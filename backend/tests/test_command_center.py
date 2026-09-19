"""
Phase 8: Unified Investigation Command Center — Backend Service & Endpoint Tests
Verifies Case Context, Chronological Timeline, Global Search, and Structured Report Generation.
"""
import pytest
import sqlite3
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from geoalchemy2 import Geography
from sqlalchemy.ext.compiler import compiles

from app.main import app
from app.db.session import get_db, Base
from app.models.crime import Crime
from app.models.person import Person, CrimePersonAssociation
from app.models.telecom import PhoneNumber, CrimePhoneAssociation, CdrRecord
from app.models.review import InvestigationRelationshipReview, InvestigationReviewHistory, ReviewStatus
from app.models.nlp_analysis import NlpAnalysis


# SQLite in-memory setup
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(test_engine, "connect")
def add_sqlite_geo_functions(dbapi_conn, connection_record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        dbapi_conn.create_function("ST_GeogFromText", 1, lambda val: val)
        dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda val: "{}")
        dbapi_conn.create_function("AsBinary", 1, lambda val: val)

@compiles(Geography, "sqlite")
def compile_geography_sqlite(type_, compiler, **kw):
    return "BLOB"

Base.metadata.create_all(bind=test_engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_api_db():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seed_command_center_data():
    db = TestingSessionLocal()
    # Clean any prior test data
    db.query(InvestigationReviewHistory).delete()
    db.query(InvestigationRelationshipReview).delete()
    db.query(NlpAnalysis).delete()
    db.query(CdrRecord).delete()
    db.query(CrimePhoneAssociation).delete()
    db.query(CrimePersonAssociation).delete()
    db.query(PhoneNumber).delete()
    db.query(Person).delete()
    db.query(Crime).delete()
    db.commit()

    now = datetime(2026, 8, 15, 10, 30, tzinfo=timezone.utc)

    # 1. Crimes
    c1 = Crime(
        id="crime-cmd-1042",
        record_id="CMD-1042",
        crime_type="Commercial Robbery",
        category="ROBBERY",
        description="Armed bank robbery in Sector 18 involving getaway sedan.",
        location_name="Noida Sector 18",
        latitude=28.5700,
        longitude=77.3200,
        occurred_at=now,
        source="STATE_POLICE_FIR"
    )
    c2 = Crime(
        id="crime-cmd-1088",
        record_id="CMD-1088",
        crime_type="Commercial Robbery",
        category="ROBBERY",
        description="Commercial robbery in Lajpat Nagar with matching weapon.",
        location_name="Lajpat Nagar, Delhi",
        latitude=28.5677,
        longitude=77.2433,
        occurred_at=datetime(2026, 8, 16, 14, 0, tzinfo=timezone.utc),
        source="STATE_POLICE_FIR"
    )
    db.add_all([c1, c2])

    # 2. Person
    p1 = Person(
        id="person-cmd-1",
        canonical_name="Vikram Singh",
        normalized_name="vikram singh",
        aliases=["Vicky", "VS"]
    )
    db.add(p1)

    # 3. Phone
    ph1 = PhoneNumber(
        id="phone-cmd-1",
        normalized_number="+919811223344",
        national_number="9811223344",
        carrier="Airtel",
        circle="Delhi",
        line_type="MOBILE",
        is_valid=True
    )
    db.add(ph1)
    db.flush()

    # 4. Associations
    cpa1 = CrimePersonAssociation(
        id="cpa-cmd-1",
        crime_id=c1.id,
        person_id=p1.id,
        role="SUSPECT_DRIVER",
        relationship_type="INVOLVED_IN",
        confidence=0.95,
        evidence_excerpt="Witness identified driver as Vikram Singh."
    )
    cph1 = CrimePhoneAssociation(
        id="cph-cmd-1",
        crime_id=c1.id,
        phone_id=ph1.id,
        relationship_type="RECOVERED_HANDSET",
        confidence=1.0,
        confidence_type="explicit"
    )
    cph2 = CrimePhoneAssociation(
        id="cph-cmd-2",
        crime_id=c2.id,
        phone_id=ph1.id,
        relationship_type="COMMUNICATION_LINK",
        confidence=0.9,
        confidence_type="derived"
    )
    db.add_all([cpa1, cph1, cph2])

    # 5. CDR
    cdr1 = CdrRecord(
        id="cdr-cmd-1",
        caller_phone_id=ph1.id,
        callee_phone_id=ph1.id,
        call_timestamp=datetime(2026, 8, 15, 11, 0, tzinfo=timezone.utc),
        duration_seconds=120,
        call_type="VOICE_CALL",
        fingerprint="hash-cmd-1"
    )
    db.add(cdr1)

    # 6. NLP
    nlp1 = NlpAnalysis(
        id="nlp-cmd-1",
        crime_id=c1.id,
        entities={
            "vehicles": [{"text": "Silver Honda City", "confidence": 0.92}],
            "weapons": [{"text": "Country pistol", "confidence": 0.88}]
        }
    )
    db.add(nlp1)

    # 7. Review & History
    rev1 = InvestigationRelationshipReview(
        id="rev-cmd-1",
        relationship_ref="Crime:crime-cmd-1042->SHARES_PHONE->Crime:crime-cmd-1088",
        source_entity_type="Crime",
        source_entity_id=c1.id,
        target_entity_type="Crime",
        target_entity_id=c2.id,
        relationship_type="SHARES_PHONE",
        original_relationship_type="SHARES_PHONE",
        status=ReviewStatus.VALIDATED.value,
        original_confidence=0.95,
        provenance="CDR_DERIVED",
        reviewer_display_name="Lead Investigator",
        investigator_note="Corroborated by call records and vehicle sighting."
    )
    db.add(rev1)
    db.flush()

    hist1 = InvestigationReviewHistory(
        id="hist-cmd-1",
        review_id=rev1.id,
        action="VALIDATE",
        from_status="UNDER_REVIEW",
        to_status="VALIDATED",
        reviewer_id="inv-007",
        reviewer_display_name="Lead Investigator",
        note="Approved based on tower location and FIR statement."
    )
    db.add(hist1)
    db.commit()
    try:
        yield
    finally:
        clean_db = TestingSessionLocal()
        clean_db.query(InvestigationReviewHistory).delete()
        clean_db.query(InvestigationRelationshipReview).delete()
        clean_db.query(NlpAnalysis).delete()
        clean_db.query(CdrRecord).delete()
        clean_db.query(CrimePhoneAssociation).delete()
        clean_db.query(CrimePersonAssociation).delete()
        clean_db.query(PhoneNumber).delete()
        clean_db.query(Person).delete()
        clean_db.query(Crime).delete()
        clean_db.commit()
        clean_db.close()
        db.close()


def test_case_context_success(client, seed_command_center_data):
    """Verifies that GET /api/v1/investigation/case/{case_id}/context returns complete case dossier."""
    res = client.get("/api/v1/investigation/case/CMD-1042/context")
    assert res.status_code == 200
    data = res.json()

    assert data["record_id"] == "CMD-1042"
    assert data["category"] == "ROBBERY"
    assert data["location_name"] == "Noida Sector 18"
    assert len(data["extracted_people"]) >= 1
    assert data["extracted_people"][0]["label"] == "Vikram Singh"
    assert len(data["extracted_phones"]) >= 1
    assert data["extracted_phones"][0]["label"] == "+919811223344"
    assert len(data["extracted_vehicles"]) >= 1
    assert data["validation_summary"]["validated"] >= 1
    assert data["total_evidence_count"] > 0


def test_case_context_not_found(client):
    """Verifies that an invalid case ID returns 404."""
    res = client.get("/api/v1/investigation/case/NONEXISTENT-9999/context")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_case_timeline_chronological_ordering(client, seed_command_center_data):
    """Verifies that timeline returns chronological sequence of FIR, CDR, and review events."""
    res = client.get("/api/v1/investigation/case/CMD-1042/timeline")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == "crime-cmd-1042"
    events = data["events"]
    assert len(events) >= 2

    # Check chronological ordering
    timestamps = [e["timestamp"] for e in events]
    assert timestamps == sorted(timestamps)

    # Check event types
    types = [e["event_type"] for e in events]
    assert "CRIME_INCIDENT" in types


def test_case_timeline_filtering(client, seed_command_center_data):
    """Verifies timeline filtering by event type."""
    res = client.get("/api/v1/investigation/case/CMD-1042/timeline?event_type=CRIME_INCIDENT")
    assert res.status_code == 200
    events = res.json()["events"]
    assert len(events) >= 1
    for e in events:
        assert e["event_type"] == "CRIME_INCIDENT"


def test_global_investigation_search(client, seed_command_center_data):
    """Verifies categorized multi-entity search across Crimes, People, Phones, and Reviews."""
    res = client.get("/api/v1/investigation/search?q=Vikram")
    assert res.status_code == 200
    data = res.json()

    assert data["query"] == "Vikram"
    assert len(data["people"]) >= 1
    assert data["people"][0]["title"] == "Vikram Singh"
    assert data["people"][0]["entity_type"] == "PERSON"


def test_investigation_report_generation(client, seed_command_center_data):
    """Verifies structured 13-section report generation, zero-guilt assertions, and statutory limitations."""
    res = client.get("/api/v1/investigation/case/CMD-1042/report")
    assert res.status_code == 200
    report = res.json()

    # Scope & Executive Summary
    assert report["record_id"] == "CMD-1042"
    assert "Noida Sector 18" in report["scope"]["jurisdiction"]
    assert len(report["executive_summary"]) > 50

    # People findings & Zero-Guilt compliance
    assert len(report["people_findings"]) >= 0
    prohibited_words = ["mastermind", "kingpin", "guilty", "criminal boss"]
    full_text = str(report).lower()
    for word in prohibited_words:
        assert word not in full_text

    # Statutory limitations
    assert len(report["statutory_limitations"]) >= 3
    limitations_text = " ".join(report["statutory_limitations"])
    assert "65B" in limitations_text
    assert "43A" in limitations_text
    assert "Validation Mandate" in limitations_text
