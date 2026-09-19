"""
Phase 4 Telecommunications: Telecom API Endpoints Integration Tests
Tests FastAPI endpoints for CDR import, phone registry, network profiles, and cross-case connections.
"""
import pytest
import sqlite3
import io
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.crime import Crime
from app.models.telecom import PhoneNumber, CdrRecord, CrimePhoneAssociation
from app.services.neo4j_service import Neo4jService


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


@pytest.fixture(autouse=True)
def reset_graph_state():
    Neo4jService._force_fallback = True
    Neo4jService.reset_graph()
    yield
    Neo4jService.reset_graph()
    Neo4jService._force_fallback = False


@pytest.fixture
def client(test_db):
    """Test client overriding the get_db dependency."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_cdr_import_api_dry_run_and_commit(client, test_db):
    """Verifies file upload via multipart/form-data with dry_run support."""
    csv_bytes = (
        b"caller,callee,timestamp,duration,call_type,location\n"
        b"9876543210,9123456789,2026-09-19 10:00:00,60,VOICE,Tower 1\n"
        b"9988776655,9876543210,2026-09-19 11:00:00,120,VOICE,Tower 2\n"
    )

    # 1. Dry run
    res_dry = client.post(
        "/api/v1/telecom/cdr/import?dry_run=true",
        files={"file": ("sample.csv", io.BytesIO(csv_bytes), "text/csv")}
    )
    assert res_dry.status_code == 200
    dry_data = res_dry.json()
    assert dry_data["dry_run"] is True
    assert dry_data["valid_count"] == 2
    assert dry_data["batch_id"] is None
    assert test_db.query(CdrRecord).count() == 0

    # 2. Real commit
    res_commit = client.post(
        "/api/v1/telecom/cdr/import?dry_run=false",
        files={"file": ("sample.csv", io.BytesIO(csv_bytes), "text/csv")}
    )
    assert res_commit.status_code == 200
    commit_data = res_commit.json()
    assert commit_data["dry_run"] is False
    assert commit_data["valid_count"] == 2
    assert commit_data["batch_id"] is not None
    assert test_db.query(CdrRecord).count() == 2
    assert test_db.query(PhoneNumber).count() == 3


def test_phones_and_profile_api(client, test_db):
    """Tests /api/v1/telecom/phones and /api/v1/telecom/phones/{id}."""
    now = datetime.now(timezone.utc)
    phone = PhoneNumber(id="ph-101", normalized_number="+919876543210", country_code="91", national_number="9876543210")
    callee = PhoneNumber(id="ph-102", normalized_number="+919123456789", country_code="91", national_number="9123456789")
    test_db.add_all([phone, callee])

    cdr = CdrRecord(
        id="cdr-01",
        caller_phone_id=phone.id,
        callee_phone_id=callee.id,
        call_timestamp=now,
        duration_seconds=75,
        call_type="VOICE",
        fingerprint="fp_api_01"
    )
    test_db.add(cdr)
    test_db.commit()

    # 1. List phones
    list_res = client.get("/api/v1/telecom/phones?search=9876543210")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(p["normalized_number"] == "+919876543210" for p in list_data["items"])

    # 2. Get profile
    detail_res = client.get(f"/api/v1/telecom/phones/{phone.id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["normalized_number"] == "+919876543210"
    assert detail_data["metrics"]["total_calls"] == 1
    assert detail_data["metrics"]["outbound_calls"] == 1
    assert detail_data["metrics"]["unique_contacts_count"] == 1


def test_cross_case_telecom_api(client, test_db):
    """Tests /api/v1/telecom/cross-case uncovering shared phone numbers."""
    now = datetime.now(timezone.utc)
    c1 = Crime(
        id="c-api-1", record_id="CR-API-1", crime_type="Robbery", category="ROBBERY",
        location_name="Banjara Hills", occurred_at=now, latitude=17.4, longitude=78.4,
        source="log", status="VALID"
    )
    c2 = Crime(
        id="c-api-2", record_id="CR-API-2", crime_type="Burglary", category="BURGLARY",
        location_name="Jubilee Hills", occurred_at=now, latitude=17.4, longitude=78.4,
        source="log", status="VALID"
    )
    phone = PhoneNumber(id="ph-shared", normalized_number="+919876543210")
    test_db.add_all([c1, c2, phone])

    assoc1 = CrimePhoneAssociation(id="a1", crime_id=c1.id, phone_id=phone.id, relationship_type="MENTIONED_IN_REPORT")
    assoc2 = CrimePhoneAssociation(id="a2", crime_id=c2.id, phone_id=phone.id, relationship_type="MENTIONED_IN_REPORT")
    test_db.add_all([assoc1, assoc2])
    test_db.commit()

    cross_res = client.get("/api/v1/telecom/cross-case")
    assert cross_res.status_code == 200
    cross_data = cross_res.json()
    assert len(cross_data) >= 1
    assert cross_data[0]["connection_type"] == "SHARED_PHONE"
    assert cross_data[0]["shared_phone"] == "+919876543210"
