"""
Phase 6: Investigator Validation Workflow Tests
Tests validate, reject, modify, reopen, notes, idempotency, and concurrency protection.
"""
import pytest
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.review import (
    ReviewStatus,
    InvestigationRelationshipReview,
    InvestigationReviewHistory,
)
from app.services.review_service import ReviewService, ConcurrencyConflictError
from app.services.neo4j_service import Neo4jService


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def add_geo_functions(dbapi_conn, connection_record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.create_function("ST_GeogFromText", 1, lambda v: v)
            dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda v: "{}")
            dbapi_conn.create_function("AsBinary", 1, lambda v: v)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    Neo4jService.reset_graph()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        Neo4jService.reset_graph()


@pytest.fixture
def sample_review(test_db):
    review = ReviewService.ingest_derived_relationship(
        db=test_db,
        source_type="Person",
        source_id="person:vikram_singh",
        relationship_type="SHARES_PHONE",
        target_type="Person",
        target_id="person:sunil_sharma",
        confidence=0.91,
        provenance="CDR_DERIVED",
        discovery_method="shared_imei_and_msisdn",
        evidence_items=[{"type": "Phone", "number": "+919876543210"}]
    )
    test_db.commit()
    return review


def test_validate_relationship_workflow(test_db, sample_review):
    """Verifies successful validation with reviewer info, timestamp, and audit trail."""
    validated = ReviewService.validate_relationship(
        db=test_db,
        review_id=sample_review.id,
        reviewer_id="investigator:sharma",
        reviewer_display_name="Inspector Sharma",
        note="Subscribers verified via telecom KYC",
        expected_version=1
    )

    assert validated.status == ReviewStatus.VALIDATED.value
    assert validated.reviewer_id == "investigator:sharma"
    assert validated.reviewer_display_name == "Inspector Sharma"
    assert validated.investigator_note == "Subscribers verified via telecom KYC"
    assert validated.version == 2
    assert validated.reviewed_at is not None

    # Verify audit history
    histories = test_db.query(InvestigationReviewHistory).filter(
        InvestigationReviewHistory.review_id == sample_review.id
    ).all()
    assert len(histories) == 2  # CREATED + VALIDATE
    assert histories[1].action == "VALIDATE"
    assert histories[1].to_status == "VALIDATED"


def test_validate_relationship_idempotency(test_db, sample_review):
    """Verifies that validating an already validated review is safe and idempotent."""
    v1 = ReviewService.validate_relationship(
        db=test_db,
        review_id=sample_review.id,
        reviewer_id="investigator:lead"
    )
    v2 = ReviewService.validate_relationship(
        db=test_db,
        review_id=sample_review.id,
        reviewer_id="investigator:lead"
    )
    assert v1.status == "VALIDATED"
    assert v2.status == "VALIDATED"
    assert v1.version == v2.version


def test_reject_relationship_workflow(test_db, sample_review):
    """Verifies rejection records reason, note, and preserves original evidence."""
    rejected = ReviewService.reject_relationship(
        db=test_db,
        review_id=sample_review.id,
        reviewer_id="investigator:lead",
        reason="Burner phone shared in public internet cafe; not common conspirator",
        note="Insufficient evidence to associate individuals",
        expected_version=1
    )

    assert rejected.status == ReviewStatus.REJECTED.value
    assert rejected.rejection_reason == "Burner phone shared in public internet cafe; not common conspirator"
    assert rejected.version == 2

    # Original evidence must remain intact
    assert len(rejected.evidence_snapshot) == 1
    assert rejected.evidence_snapshot[0]["number"] == "+919876543210"

    histories = test_db.query(InvestigationReviewHistory).filter(
        InvestigationReviewHistory.review_id == sample_review.id
    ).all()
    assert histories[-1].action == "REJECT"
    assert histories[-1].reason is not None


def test_modify_relationship_workflow(test_db, sample_review):
    """Verifies modifying relationship type to supported alternative."""
    modified = ReviewService.modify_relationship(
        db=test_db,
        review_id=sample_review.id,
        new_relationship_type="CO_OCCURS_WITH",
        reviewer_id="investigator:lead",
        note="Modifying to co-occurrence based on FIR narrative",
        expected_version=1
    )

    assert modified.status == ReviewStatus.MODIFIED.value
    assert modified.relationship_type == "CO_OCCURS_WITH"
    assert modified.final_relationship_type == "CO_OCCURS_WITH"
    assert modified.original_relationship_type == "SHARES_PHONE"
    assert modified.version == 2


def test_modify_relationship_invalid_type_rejected(test_db, sample_review):
    """Verifies modifying to an arbitrary, unsupported relationship type raises ValueError."""
    with pytest.raises(ValueError) as exc:
        ReviewService.modify_relationship(
            db=test_db,
            review_id=sample_review.id,
            new_relationship_type="ARBITRARY_CUSTOM_UNSAFE_RELATION"
        )
    assert "Invalid relationship type" in str(exc.value)


def test_reopen_review_workflow(test_db, sample_review):
    """Verifies reopening a rejected review preserves history and restarts review cycle."""
    # First reject
    ReviewService.reject_relationship(
        db=test_db,
        review_id=sample_review.id,
        reason="Initial lack of evidence"
    )

    # Reopen
    reopened = ReviewService.reopen_review(
        db=test_db,
        review_id=sample_review.id,
        reviewer_id="investigator:lead",
        reason="New CDR records surfaced connecting both parties directly"
    )

    assert reopened.status == ReviewStatus.UNDER_REVIEW.value
    assert reopened.version == 3

    histories = test_db.query(InvestigationReviewHistory).filter(
        InvestigationReviewHistory.review_id == sample_review.id
    ).order_by(InvestigationReviewHistory.created_at.asc()).all()

    # History: CREATED -> REJECT -> REOPEN
    assert len(histories) == 3
    assert histories[0].action == "CREATED"
    assert histories[1].action == "REJECT"
    assert histories[2].action == "REOPEN"
    assert "New CDR records surfaced" in histories[2].reason


def test_add_investigator_notes(test_db, sample_review):
    """Verifies multiple notes can be appended without losing previous notes."""
    ReviewService.add_note(test_db, sample_review.id, note="First investigative check completed.")
    ReviewService.add_note(test_db, sample_review.id, note="Second witness interview verified ownership.")

    test_db.refresh(sample_review)
    assert "First investigative check" in sample_review.investigator_note
    assert "Second witness interview" in sample_review.investigator_note
    assert sample_review.version == 3


def test_concurrency_conflict_detection(test_db, sample_review):
    """Verifies that attempting an action with a stale expected_version raises ConcurrencyConflictError."""
    # Investigator A validates the review (version goes from 1 to 2)
    ReviewService.validate_relationship(
        db=test_db,
        review_id=sample_review.id,
        expected_version=1
    )

    # Investigator B attempts rejection using the stale version 1
    with pytest.raises(ConcurrencyConflictError) as exc:
        ReviewService.reject_relationship(
            db=test_db,
            review_id=sample_review.id,
            reason="Conflict test",
            expected_version=1
        )
    assert "conflict" in str(exc.value).lower()
