"""
Phase 4: Knowledge Graph Unit & Integration Tests
Tests Neo4jService, GraphSyncService idempotence, and GraphQueryService traversals.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.models.ml_models import CrimeCluster, CrimeClusterMember, CrimePattern
from app.services.neo4j_service import Neo4jService
from app.services.graph_sync_service import GraphSyncService
from app.services.graph_query_service import GraphQueryService


@pytest.fixture(scope="function")
def test_db():
    """In-memory SQLite engine for test isolation."""
    import sqlite3
    from sqlalchemy import event

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


def test_neo4j_service_in_memory_upsert_and_constraints():
    """Verifies schema constraint execution, node creation, and relationship tracking."""
    assert Neo4jService.init_schema() is True

    # 1. Upsert Crime
    crime_data = {
        "id": "c-001",
        "record_id": "CR-2026-001",
        "category": "ROBBERY",
        "occurred_at": "2026-03-15T22:30:00Z",
        "location_name": "Downtown Convenience Store",
        "description": "Two armed suspects fled in a black sedan.",
        "source": "police_cad",
        "latitude": 37.7749,
        "longitude": -122.4194
    }
    assert Neo4jService.upsert_crime(crime_data) is True

    # 2. Upsert Entities
    assert Neo4jService.upsert_entity("Location", "location:downtown", {"name": "Downtown"}) is True
    assert Neo4jService.upsert_entity("Vehicle", "vehicle:black_sedan", {"name": "black sedan"}) is True
    assert Neo4jService.upsert_entity("Weapon", "weapon:handgun", {"name": "handgun"}) is True
    assert Neo4jService.upsert_entity("ModusOperandi", "mo:convenience_robbery", {"pattern": "convenience robbery"}) is True

    # 3. Create Explicit Relationships
    assert Neo4jService.create_relationship("crime:c-001", "OCCURRED_AT", "location:downtown", confidence_type="explicit") is True
    assert Neo4jService.create_relationship("crime:c-001", "USED_VEHICLE", "vehicle:black_sedan", confidence_type="explicit") is True
    assert Neo4jService.create_relationship("crime:c-001", "USED_WEAPON", "weapon:handgun", confidence_type="explicit") is True
    assert Neo4jService.create_relationship("crime:c-001", "EXHIBITS_MO", "mo:convenience_robbery", confidence_type="explicit") is True

    stats = Neo4jService.get_stats()
    assert stats["crime_nodes"] == 1
    assert stats["location_nodes"] == 1
    assert stats["vehicle_nodes"] == 1
    assert stats["weapon_nodes"] == 1
    assert stats["mo_nodes"] == 1
    assert stats["explicit_relationships"] == 4


def test_graph_sync_service_idempotence(test_db):
    """
    Tests that GraphSyncService imports PostgreSQL records, NLP entities,
    Phase 3 clusters and patterns, and generates derived relationships idempotently.
    """
    # Create 2 crimes in test DB
    now = datetime.now(timezone.utc)
    c1 = Crime(
        id="crime-101",
        record_id="CR-2026-101",
        crime_type="Armed Robbery",
        category="ROBBERY",
        location_name="Bank of West",
        occurred_at=now,
        latitude=37.77,
        longitude=-122.41,
        description="Suspects brandished handguns and fled in a silver van.",
        source="cad_feed",
        status="VALID"
    )
    c2 = Crime(
        id="crime-102",
        record_id="CR-2026-102",
        crime_type="Commercial Robbery",
        category="ROBBERY",
        location_name="Westside Jewelry",
        occurred_at=now,
        latitude=37.78,
        longitude=-122.42,
        description="Armed robbery with handguns and getaway in a silver van.",
        source="cad_feed",
        status="VALID"
    )
    test_db.add_all([c1, c2])
    test_db.flush()

    # Create NLP analysis records with shared vehicle and weapon
    nlp1 = NlpAnalysis(
        crime_id=c1.id,
        status="COMPLETED",
        extracted_weapons=["handgun"],
        extracted_vehicles=["silver van"],
        extracted_locations=["Bank of West"],
        extracted_persons=["male suspect"],
        modus_operandi=[{"pattern": "armed commercial robbery", "certainty": "explicitly_stated"}]
    )
    nlp2 = NlpAnalysis(
        crime_id=c2.id,
        status="COMPLETED",
        extracted_weapons=["handgun"],
        extracted_vehicles=["silver van"],
        extracted_locations=["Westside Jewelry"],
        extracted_persons=["male suspect"],
        modus_operandi=[{"pattern": "armed commercial robbery", "certainty": "explicitly_stated"}]
    )
    test_db.add_all([nlp1, nlp2])

    # Create a Phase 3 Cluster
    cluster = CrimeCluster(
        id="cluster-999",
        cluster_type="spatial",
        cluster_label=1,
        crime_count=2,
        centroid_lat=37.775,
        centroid_lon=-122.415
    )
    test_db.add(cluster)
    test_db.flush()

    m1 = CrimeClusterMember(cluster_id=cluster.id, crime_id=c1.id)
    m2 = CrimeClusterMember(cluster_id=cluster.id, crime_id=c2.id)
    test_db.add_all([m1, m2])

    # Create a Phase 3 Pattern
    pattern = CrimePattern(
        id="pattern-777",
        pattern_type="spatial_temporal",
        category="ROBBERY",
        description="Repeated armed robberies targeting commercial stores.",
        confidence=0.92,
        evidence=[c1.id, c2.id]
    )
    test_db.add(pattern)
    test_db.commit()

    # First sync run
    result1 = GraphSyncService.sync_all(test_db)
    assert result1["status"] == "completed"
    assert result1["crimes_synced"] == 2
    assert result1["explicit_relationships_created"] > 0
    assert result1["derived_relationships_created"] > 0

    stats1 = Neo4jService.get_stats()
    total_nodes_1 = stats1["total_nodes"]
    total_rels_1 = stats1["total_relationships"]

    # Second sync run (Idempotency check)
    result2 = GraphSyncService.sync_all(test_db)
    assert result2["status"] == "completed"

    stats2 = Neo4jService.get_stats()
    assert stats2["total_nodes"] == total_nodes_1, "Node count should remain identical after second sync"
    assert stats2["total_relationships"] == total_rels_1, "Relationship count should remain identical after second sync"


def test_graph_query_service_neighborhood_and_connections(test_db):
    """Verifies graph neighborhood traversal and connected crime discovery."""
    # Set up nodes and connections in in-memory store
    c1_data = {"id": "c-alpha", "record_id": "CR-ALPHA", "category": "BURGLARY", "location_name": "Midtown"}
    c2_data = {"id": "c-beta", "record_id": "CR-BETA", "category": "BURGLARY", "location_name": "Midtown"}
    Neo4jService.upsert_crime(c1_data)
    Neo4jService.upsert_crime(c2_data)

    Neo4jService.upsert_entity("Vehicle", "vehicle:blue_truck", {"name": "blue truck"})
    Neo4jService.create_relationship("crime:c-alpha", "USED_VEHICLE", "vehicle:blue_truck", confidence_type="explicit")
    Neo4jService.create_relationship("crime:c-beta", "USED_VEHICLE", "vehicle:blue_truck", confidence_type="explicit")

    # Derived cross-edge
    Neo4jService.create_relationship(
        "crime:c-alpha", "SHARES_VEHICLE", "crime:c-beta",
        properties={"confidence": 1.0, "entity_name": "blue truck", "source": "shared_vehicle"},
        confidence_type="derived"
    )

    # 1. Neighborhood query
    subgraph = GraphQueryService.get_crime_neighborhood(crime_id="c-alpha", depth=2)
    assert subgraph["total_nodes"] >= 2
    assert any(n["id"] == "vehicle:blue_truck" for n in subgraph["nodes"])

    # 2. Connected crimes query
    connections = GraphQueryService.find_connected_crimes(crime_id="c-alpha")
    assert len(connections) >= 1
    assert connections[0]["crime_id"] == "c-beta"
    assert connections[0]["relationship"] == "SHARES_VEHICLE"
    assert connections[0]["confidence_type"] == "derived"

    # 3. Path finding
    paths = GraphQueryService.find_paths_between_crimes("c-alpha", "c-beta")
    assert len(paths) >= 1
