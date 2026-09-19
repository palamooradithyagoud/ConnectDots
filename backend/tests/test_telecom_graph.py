"""
Phase 4 Telecommunications: Telecom Knowledge Graph Tests
Tests Neo4j Phone nodes, CALLS relationships, idempotent graph sync,
and cross-case telecommunications traversal.
"""
import pytest
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.crime import Crime, ImportBatch
from app.models.telecom import PhoneNumber, CdrRecord, CrimePhoneAssociation, PersonPhoneAssociation
from app.services.neo4j_service import Neo4jService
from app.services.graph_sync_service import GraphSyncService
from app.services.graph_query_service import GraphQueryService


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


def test_neo4j_phone_upsert_and_call_edge():
    """Verifies that Phone nodes and CALLS relationships are registered idempotently in the graph."""
    # 1. Upsert phones
    Neo4jService.upsert_entity(
        label="Phone",
        entity_id="phone:+919876543210",
        properties={"number": "+919876543210", "carrier": "Airtel"}
    )
    Neo4jService.upsert_entity(
        label="Phone",
        entity_id="phone:+919123456789",
        properties={"number": "+919123456789", "carrier": "Jio"}
    )

    assert "phone:+919876543210" in Neo4jService._mock_nodes
    assert "phone:+919123456789" in Neo4jService._mock_nodes

    # 2. Create CALLS edge
    Neo4jService.create_relationship(
        source_id="phone:+919876543210",
        rel_type="CALLS",
        target_id="phone:+919123456789",
        properties={"call_count": 5, "total_duration": 450},
        confidence_type="explicit"
    )

    # 3. Repeat to test idempotency
    Neo4jService.create_relationship(
        source_id="phone:+919876543210",
        rel_type="CALLS",
        target_id="phone:+919123456789",
        properties={"call_count": 5, "total_duration": 450},
        confidence_type="explicit"
    )

    call_rels = [r for r in Neo4jService._mock_relationships if r["relation"] == "CALLS"]
    assert len(call_rels) == 1
    assert call_rels[0]["source"] == "phone:+919876543210"
    assert call_rels[0]["target"] == "phone:+919123456789"


def test_graph_sync_telecom_and_cross_case_linkage(test_db):
    """
    End-to-end GraphSync:
    Crime 1 mentions Phone A.
    Crime 2 mentions Phone B.
    Phone A calls Phone B (CDR).
    GraphSync must derive: (:Crime 1)-[:COMMUNICATION_LINKED]->(:Crime 2).
    """
    now = datetime.now(timezone.utc)

    # Crime 1
    c1 = Crime(
        id="c-001",
        record_id="CR-2026-001",
        crime_type="Armed Robbery",
        category="ROBBERY",
        location_name="Banjara Hills",
        occurred_at=now,
        latitude=17.41,
        longitude=78.44,
        description="Armed robbery at jewelry store.",
        source="police_log",
        status="VALID"
    )
    # Crime 2
    c2 = Crime(
        id="c-002",
        record_id="CR-2026-002",
        crime_type="Commercial Burglary",
        category="BURGLARY",
        location_name="Jubilee Hills",
        occurred_at=now,
        latitude=17.43,
        longitude=78.40,
        description="Overnight break-in at electronics warehouse.",
        source="police_log",
        status="VALID"
    )
    test_db.add_all([c1, c2])

    # Phone A and B
    p_a = PhoneNumber(id="p-001", normalized_number="+919876543210")
    p_b = PhoneNumber(id="p-002", normalized_number="+919123456789")
    test_db.add_all([p_a, p_b])

    # Associations
    assoc1 = CrimePhoneAssociation(
        id="cpa-001",
        crime_id=c1.id,
        phone_id=p_a.id,
        relationship_type="MENTIONED_IN_REPORT",
        confidence=1.0,
        confidence_type="explicit"
    )
    assoc2 = CrimePhoneAssociation(
        id="cpa-002",
        crime_id=c2.id,
        phone_id=p_b.id,
        relationship_type="MENTIONED_IN_REPORT",
        confidence=1.0,
        confidence_type="explicit"
    )
    test_db.add_all([assoc1, assoc2])

    # CDR communication between A and B
    cdr = CdrRecord(
        id="cdr-001",
        caller_phone_id=p_a.id,
        callee_phone_id=p_b.id,
        call_timestamp=now,
        duration_seconds=180,
        call_type="VOICE",
        fingerprint="fp_hash_001",
        source_reference="AIRTEL_CDR"
    )
    test_db.add(cdr)
    test_db.commit()

    # Run GraphSync
    result = GraphSyncService.sync_all(test_db)
    assert result["status"] == "completed"
    assert result["phones_synced"] == 2
    assert result["call_relationships_synced"] == 1

    # Verify COMMUNICATION_LINKED derived relationship was created
    comm_links = [
        r for r in Neo4jService._mock_relationships
        if r["relation"] == "COMMUNICATION_LINKED"
    ]
    assert len(comm_links) >= 1
    assert comm_links[0]["source"] == f"crime:{c1.id}"
    assert comm_links[0]["target"] == f"crime:{c2.id}"
    assert comm_links[0]["properties"]["caller_phone"] == "+919876543210"
    assert comm_links[0]["properties"]["callee_phone"] == "+919123456789"


def test_graph_query_phone_neighborhood():
    """GraphQueryService retrieves 2-hop graph neighborhood for a phone."""
    phone_id = "phone:+919876543210"
    callee_id = "phone:+919123456789"
    crime_id = "crime:c-001"

    Neo4jService.upsert_entity("Phone", phone_id, {"number": "+919876543210"})
    Neo4jService.upsert_entity("Phone", callee_id, {"number": "+919123456789"})
    Neo4jService.upsert_crime({"id": "c-001", "record_id": "CR-001"})

    Neo4jService.create_relationship(phone_id, "CALLS", callee_id, {"call_count": 3})
    Neo4jService.create_relationship(crime_id, "MENTIONS_PHONE", phone_id, {})

    neighborhood = GraphQueryService.get_phone_neighborhood("+919876543210", depth=2)
    assert neighborhood["total_nodes"] >= 2
    assert neighborhood["total_edges"] >= 1
    assert any(n["id"] == phone_id for n in neighborhood["nodes"])
