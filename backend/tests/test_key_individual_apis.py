"""
Phase 5 Person Network: Key Individual REST API Integration Tests
Tests /api/v1/network endpoints for key individual ranking, dossiers, subgraphs,
evidence grounding, and pagination.
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
from app.models.crime import Crime
from app.models.person import Person, CrimePersonAssociation
from app.models.telecom import PhoneNumber, PersonPhoneAssociation
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
    """Ensures graph state is clean before each test and runs in in-memory fallback."""
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
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seed_test_network(test_db):
    """Seeds test database and graph with sample individuals and crimes."""
    now = datetime.now(timezone.utc)

    # 1. Crimes
    c1 = Crime(
        id="crime-api-1",
        record_id="FIR-API-01",
        crime_type="Extortion",
        category="EXTORTION",
        location_name="Connaught Place",
        occurred_at=now,
        latitude=28.6328,
        longitude=77.2197,
        description="Extortion syndicate operation.",
        source="fir_cad",
        status="VALID"
    )
    c2 = Crime(
        id="crime-api-2",
        record_id="FIR-API-02",
        crime_type="Armed Robbery",
        category="ROBBERY",
        location_name="Karol Bagh",
        occurred_at=now,
        latitude=28.65,
        longitude=77.19,
        description="Jewelry store heist.",
        source="fir_cad",
        status="VALID"
    )
    test_db.add_all([c1, c2])

    # 2. Persons
    p1 = Person(
        id="person:vikram_singh",
        canonical_name="Vikram Singh",
        normalized_name="vikram singh",
        aliases=["Vicky"]
    )
    p2 = Person(
        id="person:sunil_sharma",
        canonical_name="Sunil Sharma",
        normalized_name="sunil sharma",
        aliases=["Sunny"]
    )
    test_db.add_all([p1, p2])

    # 3. Associations
    a1 = CrimePersonAssociation(
        crime_id=c1.id,
        person_id=p1.id,
        role="ACCUSED",
        evidence_excerpt="Threat delivered by Vikram Singh",
        confidence=0.95
    )
    a2 = CrimePersonAssociation(
        crime_id=c2.id,
        person_id=p1.id,
        role="CONSPIRATOR",
        evidence_excerpt="Getaway coordinated by Vikram Singh",
        confidence=0.9
    )
    a3 = CrimePersonAssociation(
        crime_id=c2.id,
        person_id=p2.id,
        role="ACCOMPLICE",
        evidence_excerpt="Sunil Sharma on-site driver",
        confidence=0.88
    )
    test_db.add_all([a1, a2, a3])

    # 4. Phones
    phone = PhoneNumber(
        id="phone:+919876543210",
        raw_number="9876543210",
        normalized_number="+919876543210",
        is_valid=True
    )
    test_db.add(phone)
    ppa = PersonPhoneAssociation(
        phone_id=phone.id,
        person_id=p1.id,
        person_name=p1.canonical_name,
        confidence=0.9
    )
    test_db.add(ppa)
    test_db.commit()

    # 5. Graph entities
    Neo4jService.upsert_crime({"id": c1.id, "record_id": c1.record_id, "category": c1.category})
    Neo4jService.upsert_crime({"id": c2.id, "record_id": c2.record_id, "category": c2.category})
    Neo4jService.upsert_person({"id": p1.id, "canonical_name": p1.canonical_name, "aliases": p1.aliases})
    Neo4jService.upsert_person({"id": p2.id, "canonical_name": p2.canonical_name, "aliases": p2.aliases})

    Neo4jService.create_relationship(c1.id, "MENTIONS_PERSON", p1.id, confidence_type="explicit")
    Neo4jService.create_relationship(c2.id, "MENTIONS_PERSON", p1.id, confidence_type="explicit")
    Neo4jService.create_relationship(c2.id, "MENTIONS_PERSON", p2.id, confidence_type="explicit")
    Neo4jService.create_relationship(p1.id, "CO_OCCURS_WITH", p2.id, confidence_type="derived")
    Neo4jService.create_relationship(p1.id, "USES_PHONE", phone.id, confidence_type="explicit")


def test_get_key_individuals_api(client, seed_test_network):
    """Verifies GET /api/v1/network/key-individuals returns ranked individuals with pagination."""
    response = client.get("/api/v1/network/key-individuals?scope=global&sort_by=degree_centrality&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

    # Vikram Singh is connected to 2 crimes and 1 person -> higher degree
    first = data["items"][0]
    assert "person_id" in first
    assert "canonical_name" in first
    assert "degree_centrality" in first
    assert "betweenness_centrality" in first
    assert "pagerank" in first
    assert "structural_explanation" in first


def test_get_individual_dossier_api(client, seed_test_network):
    """Verifies GET /api/v1/network/key-individuals/{person_id} returns complete dossier."""
    response = client.get("/api/v1/network/key-individuals/person:vikram_singh")
    assert response.status_code == 200
    data = response.json()

    assert data["person_id"] == "person:vikram_singh"
    assert data["canonical_name"] == "Vikram Singh"
    assert len(data["associated_crimes"]) == 2
    assert len(data["associated_phones"]) == 1
    assert data["associated_phones"][0]["phone_id"] == "phone:+919876543210"
    assert "structural_explanation" in data


def test_get_individual_dossier_not_found(client):
    """Verifies 404 response for non-existent individual."""
    response = client.get("/api/v1/network/key-individuals/person:nonexistent_person")
    assert response.status_code == 404


def test_get_crime_key_individuals(client, seed_test_network):
    """Verifies GET /api/v1/network/crimes/{crime_id}/key-individuals returns individuals for a crime."""
    response = client.get("/api/v1/network/crimes/crime-api-2/key-individuals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    person_ids = [d["person_id"] for d in data]
    assert "person:vikram_singh" in person_ids
    assert "person:sunil_sharma" in person_ids


def test_get_crime_subgraph(client, seed_test_network):
    """Verifies GET /api/v1/network/crimes/{crime_id}/subgraph returns bounded graph components."""
    response = client.get("/api/v1/network/crimes/crime-api-2/subgraph?depth=2")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "total_nodes" in data
    assert "total_edges" in data
    assert data["total_nodes"] > 0


def test_get_person_evidence(client, seed_test_network):
    """Verifies GET /api/v1/network/person/{person_id}/evidence returns grounded excerpts."""
    response = client.get("/api/v1/network/person/person:vikram_singh/evidence")
    assert response.status_code == 200
    data = response.json()
    assert data["person_id"] == "person:vikram_singh"
    assert len(data["evidence"]) >= 2
    assert any("Threat delivered" in ev["excerpt"] for ev in data["evidence"])


def test_get_scopes(client):
    """Verifies GET /api/v1/network/scopes returns available investigative scopes."""
    response = client.get("/api/v1/network/scopes")
    assert response.status_code == 200
    data = response.json()
    assert "scopes" in data
    assert "global" in data["scopes"]
    assert "crime" in data["scopes"]
