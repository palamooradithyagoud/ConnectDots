"""
Phase 5 Person Network: Person Knowledge Graph Tests
Tests Neo4j Person nodes, MENTIONS_PERSON, USES_PHONE, CO_OCCURS_WITH,
SHARES_PHONE relationships, and idempotent graph synchronization.
"""
import pytest
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.crime import Crime
from app.models.person import Person, CrimePersonAssociation
from app.models.telecom import PhoneNumber, PersonPhoneAssociation
from app.services.neo4j_service import Neo4jService
from app.services.graph_sync_service import GraphSyncService


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


def test_neo4j_person_upsert_and_relationships():
    """Verifies that Person nodes and explicit/derived edges are registered correctly in the graph."""
    # 1. Upsert Crime
    Neo4jService.upsert_crime({
        "id": "c-test-01",
        "record_id": "CR-2026-001",
        "category": "EXTORTION",
        "location_name": "Delhi Central",
        "description": "Extortion call racket",
        "occurred_at": "2026-03-01T10:00:00Z"
    })

    # 2. Upsert Person
    assert Neo4jService.upsert_person({
        "id": "person:vikram_singh",
        "canonical_name": "Vikram Singh",
        "aliases": ["Vicky"]
    }) is True

    # 3. Create MENTIONS_PERSON explicit edge
    assert Neo4jService.create_relationship(
        from_id="crime:c-test-01",
        rel_type="MENTIONS_PERSON",
        to_id="person:vikram_singh",
        properties={"role": "ACCUSED", "confidence": 0.95},
        confidence_type="explicit"
    ) is True

    # 4. Upsert Phone & USES_PHONE edge
    Neo4jService.upsert_entity("Phone", "phone:+919876543210", {
        "raw_number": "9876543210",
        "normalized_number": "+919876543210"
    })
    assert Neo4jService.create_relationship(
        from_id="person:vikram_singh",
        rel_type="USES_PHONE",
        to_id="phone:+919876543210",
        properties={"confidence": 0.9, "source": "cdr_registration"},
        confidence_type="explicit"
    ) is True

    stats = Neo4jService.get_stats()
    assert stats["crime_nodes"] == 1
    assert stats["explicit_relationships"] >= 2


def test_graph_sync_person_network_and_cross_person_edges(test_db):
    """
    Tests that GraphSyncService synchronizes Person records, establishes MENTIONS_PERSON,
    USES_PHONE, and accurately derives CO_OCCURS_WITH and SHARES_PHONE cross-person relationships.
    """
    now = datetime.now(timezone.utc)

    # 1. Relational Crime
    c1 = Crime(
        id="c-sync-1",
        record_id="CR-SYNC-01",
        crime_type="Armed Robbery",
        category="ROBBERY",
        location_name="Karol Bagh",
        occurred_at=now,
        latitude=28.65,
        longitude=77.19,
        description="Jewelry store robbery executed by Vikram Singh and Sunil Sharma.",
        source="cad_feed",
        status="VALID"
    )
    test_db.add(c1)

    # 2. Relational Persons
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

    # 3. Associations to same crime (Trigger for CO_OCCURS_WITH)
    assoc1 = CrimePersonAssociation(
        crime_id=c1.id,
        person_id=p1.id,
        role="ACCUSED",
        evidence_excerpt="executed by Vikram Singh",
        confidence=0.95
    )
    assoc2 = CrimePersonAssociation(
        crime_id=c1.id,
        person_id=p2.id,
        role="ACCOMPLICE",
        evidence_excerpt="and Sunil Sharma",
        confidence=0.9
    )
    test_db.add_all([assoc1, assoc2])

    # 4. Phone shared by both persons (Trigger for SHARES_PHONE)
    phone = PhoneNumber(
        id="phone:+919876543210",
        raw_number="9876543210",
        normalized_number="+919876543210",
        country_code="+91",
        is_valid=True
    )
    test_db.add(phone)

    ppa1 = PersonPhoneAssociation(
        phone_id=phone.id,
        person_id=p1.id,
        person_name=p1.canonical_name,
        confidence=0.85
    )
    ppa2 = PersonPhoneAssociation(
        phone_id=phone.id,
        person_id=p2.id,
        person_name=p2.canonical_name,
        confidence=0.85
    )
    test_db.add_all([ppa1, ppa2])
    test_db.commit()

    # Initial Sync
    res1 = GraphSyncService.sync_all(test_db)
    assert res1["status"] == "completed"
    assert res1.get("persons_synced", 0) == 2

    # Check store for Person nodes and relationships
    store = Neo4jService._store
    assert "person:vikram_singh" in store["nodes"]
    assert "person:sunil_sharma" in store["nodes"]

    # Verify MENTIONS_PERSON edges
    mentions = [r for r in store["relationships"] if r["type"] == "MENTIONS_PERSON"]
    assert len(mentions) >= 2

    # Verify USES_PHONE edges
    uses_phone = [r for r in store["relationships"] if r["type"] == "USES_PHONE"]
    assert len(uses_phone) >= 2

    # Verify derived CO_OCCURS_WITH edge between p1 and p2
    co_occurs = [r for r in store["relationships"] if r["type"] == "CO_OCCURS_WITH"]
    assert len(co_occurs) >= 1
    co_pair = {(r["from_id"], r["to_id"]) for r in co_occurs}
    assert ("person:vikram_singh", "person:sunil_sharma") in co_pair or ("person:sunil_sharma", "person:vikram_singh") in co_pair

    # Verify derived SHARES_PHONE edge between p1 and p2
    shares_phone = [r for r in store["relationships"] if r["type"] == "SHARES_PHONE"]
    assert len(shares_phone) >= 1

    # Idempotency check: Second sync produces identical counts
    total_nodes_before = len(store["nodes"])
    total_rels_before = len(store["relationships"])

    res2 = GraphSyncService.sync_all(test_db)
    assert res2["status"] == "completed"

    assert len(store["nodes"]) == total_nodes_before
    assert len(store["relationships"]) == total_rels_before
