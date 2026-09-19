"""
Phase 6: Investigator Review REST API Integration Tests
Tests /api/v1/reviews endpoints: queue filtering, dossier retrieval, validate, reject,
modify, reopen, notes, stats, and concurrency conflict handling.
"""
import pytest
import sqlite3
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.review import (
    ReviewStatus,
    InvestigationRelationshipReview,
    InvestigationReviewHistory,
)
from app.services.review_service import ReviewService
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
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_graph_state():
    Neo4jService._force_fallback = True
    Neo4jService.reset_graph()
    yield
    Neo4jService.reset_graph()
    Neo4jService._force_fallback = False


@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seed_reviews(test_db):
    r1 = ReviewService.ingest_derived_relationship(
        db=test_db,
        source_type="Person",
        source_id="person:vikram_singh",
        relationship_type="SHARES_PHONE",
        target_type="Person",
        target_id="person:sunil_sharma",
        confidence=0.92,
        provenance="CDR_DERIVED",
        discovery_method="shared_imei",
        evidence_items=[{"type": "Phone", "number": "+919876543210"}]
    )
    r2 = ReviewService.ingest_derived_relationship(
        db=test_db,
        source_type="Crime",
        source_id="crime:CR-001",
        relationship_type="COMMUNICATION_LINKED",
        target_type="Crime",
        target_id="crime:CR-002",
        confidence=0.85,
        provenance="CDR_DERIVED",
        discovery_method="cross_case_cdr",
        evidence_items=[{"type": "CDR", "call_count": 4}]
    )
    test_db.commit()
    return [r1, r2]


def test_list_reviews_api(client, seed_reviews):
    """Verifies listing review queue items with pagination and filters."""
    res = client.get("/api/v1/reviews")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["status"] == "PENDING"

    # Filter by relationship_type
    filtered = client.get("/api/v1/reviews?relationship_type=SHARES_PHONE")
    assert filtered.status_code == 200
    fdata = filtered.json()
    assert fdata["total"] == 1
    assert fdata["items"][0]["relationship_type"] == "SHARES_PHONE"


def test_get_review_stats_api(client, seed_reviews):
    """Verifies review stats endpoint."""
    res = client.get("/api/v1/reviews/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["pending"] == 2
    assert data["validated"] == 0
    assert data["rejected"] == 0


def test_get_supported_types_api(client):
    """Verifies supported relationship types endpoint."""
    res = client.get("/api/v1/reviews/supported-types")
    assert res.status_code == 200
    data = res.json()
    assert "supported_types" in data
    assert "CO_OCCURS_WITH" in data["supported_types"]
    assert "SHARES_PHONE" in data["supported_types"]


def test_get_review_detail_api(client, seed_reviews):
    """Verifies full review dossier endpoint."""
    rev_id = seed_reviews[0].id
    res = client.get(f"/api/v1/reviews/{rev_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == rev_id
    assert len(data["evidence_snapshot"]) == 1
    assert len(data["history_entries"]) >= 1


def test_validate_review_api(client, seed_reviews):
    """Verifies validating a review via API."""
    rev_id = seed_reviews[0].id
    payload = {
        "reviewer_id": "investigator:lead",
        "reviewer_display_name": "Senior Inspector",
        "note": "Verified through CDR records.",
        "expected_version": 1
    }
    res = client.post(f"/api/v1/reviews/{rev_id}/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VALIDATED"
    assert data["reviewer_id"] == "investigator:lead"
    assert data["version"] == 2


def test_reject_review_api(client, seed_reviews):
    """Verifies rejecting a review via API with required reason."""
    rev_id = seed_reviews[1].id
    payload = {
        "reason": "Public payphone usage; coincidence only",
        "note": "No common conspiracy found.",
        "expected_version": 1
    }
    res = client.post(f"/api/v1/reviews/{rev_id}/reject", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "Public payphone usage; coincidence only"


def test_modify_review_api(client, seed_reviews):
    """Verifies modifying a relationship type via API."""
    rev_id = seed_reviews[0].id
    payload = {
        "new_relationship_type": "CO_OCCURS_WITH",
        "note": "Changing from phone to incident co-occurrence.",
        "expected_version": 1
    }
    res = client.post(f"/api/v1/reviews/{rev_id}/modify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "MODIFIED"
    assert data["relationship_type"] == "CO_OCCURS_WITH"

    # Attempting unsupported type must return 400
    invalid_payload = {
        "new_relationship_type": "UNKNOWN_CUSTOM_RELATION"
    }
    bad_res = client.post(f"/api/v1/reviews/{rev_id}/modify", json=invalid_payload)
    assert bad_res.status_code == 400


def test_concurrency_conflict_returns_409(client, seed_reviews):
    """Verifies optimistic concurrency conflict returns HTTP 409."""
    rev_id = seed_reviews[0].id
    # First action increments version to 2
    client.post(f"/api/v1/reviews/{rev_id}/validate", json={"expected_version": 1})

    # Second action specifying outdated version 1
    conflict_res = client.post(
        f"/api/v1/reviews/{rev_id}/reject",
        json={"reason": "Late rejection", "expected_version": 1}
    )
    assert conflict_res.status_code == 409
    assert "conflict" in conflict_res.json()["detail"].lower()


def test_nonexistent_review_returns_404(client):
    """Verifies 404 for invalid review IDs."""
    res = client.get("/api/v1/reviews/nonexistent-uuid-12345")
    assert res.status_code == 404
