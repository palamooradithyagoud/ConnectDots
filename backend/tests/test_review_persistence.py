"""
Phase 6: Investigator Validation Review Persistence Tests
Tests database persistence for InvestigationRelationshipReview and InvestigationReviewHistory.
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
    RelationshipProvenance,
    InvestigationRelationshipReview,
    InvestigationReviewHistory,
)
from app.services.review_service import ReviewService


@pytest.fixture(scope="function")
def test_db():
    """In-memory SQLite engine for test isolation with Geo functions registered."""
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
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_review_model_persistence(test_db):
    """Verifies creation and persistence of InvestigationRelationshipReview."""
    review = InvestigationRelationshipReview(
        relationship_ref="Person:person:vikram_singh--SHARES_PHONE--Person:person:sunil_sharma",
        source_entity_type="Person",
        source_entity_id="person:vikram_singh",
        target_entity_type="Person",
        target_entity_id="person:sunil_sharma",
        relationship_type="SHARES_PHONE",
        original_relationship_type="SHARES_PHONE",
        original_confidence=0.92,
        provenance=RelationshipProvenance.CDR_DERIVED.value,
        discovery_method="shared_telecom_subscriber_analysis",
        status=ReviewStatus.PENDING.value,
        evidence_snapshot=[
            {"type": "Phone", "number": "+919876543210", "note": "Used by both individuals"}
        ],
        version=1
    )
    test_db.add(review)
    test_db.commit()

    saved = test_db.query(InvestigationRelationshipReview).filter(
        InvestigationRelationshipReview.relationship_ref == "Person:person:vikram_singh--SHARES_PHONE--Person:person:sunil_sharma"
    ).first()

    assert saved is not None
    assert saved.status == "PENDING"
    assert saved.original_confidence == 0.92
    assert saved.version == 1
    assert len(saved.evidence_snapshot) == 1


def test_deterministic_relationship_ref_generation():
    """Verifies symmetric relationships generate canonical sorted references regardless of order."""
    ref1 = ReviewService.generate_relationship_ref(
        source_type="Person",
        source_id="person:vikram_singh",
        relationship_type="SHARES_PHONE",
        target_type="Person",
        target_id="person:sunil_sharma"
    )
    ref2 = ReviewService.generate_relationship_ref(
        source_type="Person",
        source_id="person:sunil_sharma",
        relationship_type="SHARES_PHONE",
        target_type="Person",
        target_id="person:vikram_singh"
    )
    # Symmetric relationship: must be identical
    assert ref1 == ref2
    assert "SHARES_PHONE" in ref1

    # Directed relationship: must preserve direction
    dir1 = ReviewService.generate_relationship_ref("Person", "person:vikram", "USES_PHONE", "Phone", "phone:98765")
    dir2 = ReviewService.generate_relationship_ref("Phone", "phone:98765", "USES_PHONE", "Person", "person:vikram")
    assert dir1 != dir2


def test_review_service_ingest_idempotency(test_db):
    """Verifies ingesting the same derived relationship does not duplicate review records."""
    r1 = ReviewService.ingest_derived_relationship(
        db=test_db,
        source_type="Crime",
        source_id="crime:CR-001",
        relationship_type="COMMUNICATION_LINKED",
        target_type="Crime",
        target_id="crime:CR-002",
        confidence=0.88,
        provenance="CDR_DERIVED",
        discovery_method="cdr_calls",
        evidence_items=[{"call_id": "CALL-101"}]
    )
    test_db.commit()

    # Second ingestion with additional evidence
    r2 = ReviewService.ingest_derived_relationship(
        db=test_db,
        source_type="Crime",
        source_id="crime:CR-002",  # Reverse order
        relationship_type="COMMUNICATION_LINKED",
        target_type="Crime",
        target_id="crime:CR-001",
        confidence=0.88,
        provenance="CDR_DERIVED",
        discovery_method="cdr_calls",
        evidence_items=[{"call_id": "CALL-102"}]
    )
    test_db.commit()

    assert r1.id == r2.id
    total_reviews = test_db.query(InvestigationRelationshipReview).count()
    assert total_reviews == 1

    saved = test_db.query(InvestigationRelationshipReview).first()
    assert len(saved.evidence_snapshot) == 2


def test_review_history_audit_trail(test_db):
    """Verifies that review state changes append history records with full provenance."""
    review = ReviewService.ingest_derived_relationship(
        db=test_db,
        source_type="Person",
        source_id="person:p1",
        relationship_type="CO_OCCURS_WITH",
        target_type="Person",
        target_id="person:p2",
        confidence=0.8
    )
    test_db.commit()

    # Ingestion creates first history record
    histories = test_db.query(InvestigationReviewHistory).filter(
        InvestigationReviewHistory.review_id == review.id
    ).all()
    assert len(histories) == 1
    assert histories[0].action == "CREATED"
    assert histories[0].to_status == "PENDING"
