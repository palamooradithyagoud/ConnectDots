"""
Phase 7: Domain AI Investigation Agent — Master Service End-to-End Tests
Executes full investigations across Scenarios 1 to 5 and verifies zero guilt inference,
statutory limitations, tool traces, and validation state propagation.
"""
import pytest
import asyncio
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.crime import Crime
from app.models.telecom import PhoneNumber, CrimePhoneAssociation
from app.models.person import Person, CrimePersonAssociation
from app.models.review import InvestigationRelationshipReview, ReviewStatus
from app.services.agent.agent_service import DomainAgentService
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
def seed_scenario_data(test_db):
    """Seeds test data matching the benchmark investigation scenarios."""
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    # Crimes
    c1 = Crime(
        id="crime-1042",
        record_id="1042",
        crime_type="Armed Robbery",
        category="Armed Robbery",
        description="Bank robbery in Sector 18 involving three masked suspects.",
        location_name="Noida Sector 18",
        latitude=28.5700,
        longitude=77.3200,
        occurred_at=now,
        source="FIR_REPORT"
    )
    c2 = Crime(
        id="crime-1088",
        record_id="1088",
        crime_type="Armed Robbery",
        category="Armed Robbery",
        description="Commercial jewel robbery in Lajpat Nagar with matching getaway car.",
        location_name="Lajpat Nagar, Delhi",
        latitude=28.5677,
        longitude=77.2433,
        occurred_at=now,
        source="FIR_REPORT"
    )
    test_db.add_all([c1, c2])

    # Phone
    ph = PhoneNumber(
        id="phone-100",
        normalized_number="+919876543210",
        national_number="9876543210",
        carrier="Jio",
        circle="Delhi",
        line_type="MOBILE",
        is_valid=True
    )
    test_db.add(ph)
    test_db.flush()

    # Associations
    ca1 = CrimePhoneAssociation(id="cpa-1", crime_id=c1.id, phone_id=ph.id, relationship_type="RECOVERED_AT_SCENE")
    ca2 = CrimePhoneAssociation(id="cpa-2", crime_id=c2.id, phone_id=ph.id, relationship_type="CALLED_ACCOMPLICE")
    test_db.add_all([ca1, ca2])

    # Person
    p1 = Person(
        id="person-1",
        canonical_name="Rajesh Kumar",
        normalized_name="rajesh kumar",
        aliases=["Raju", "RK"]
    )
    test_db.add(p1)

    # Reviews (one validated, one rejected)
    r1 = InvestigationRelationshipReview(
        id="rev-valid-1",
        relationship_ref="Crime:crime-1042->SHARES_PHONE->Crime:crime-1088",
        source_entity_type="Crime",
        source_entity_id=c1.id,
        relationship_type="SHARES_PHONE",
        original_relationship_type="SHARES_PHONE",
        target_entity_type="Crime",
        target_entity_id=c2.id,
        status=ReviewStatus.VALIDATED.value
    )
    test_db.add(r1)
    test_db.commit()


def test_scenario_1_cross_case_phone_investigation(test_db, seed_scenario_data):
    """Scenario 1: Find cases connected to Case 1042 through phones."""
    agent = DomainAgentService(test_db)
    res = asyncio.run(agent.investigate(question="Find cases connected to Case 1042 through phones."))

    assert res.status == "COMPLETED"
    assert len(res.tool_trace) > 0
    assert any("phone" in t.tool or "cross_case" in t.tool or "crime" in t.tool for t in res.tool_trace)
    assert len(res.evidence) >= 1
    assert any("1042" in ev.summary or "1088" in ev.summary or "9876543210" in ev.summary for ev in res.evidence)

    # Zero guilt check
    prohibited = ["mastermind", "kingpin", "guilty", "gang boss"]
    for word in prohibited:
        assert word not in res.summary.lower()

    # Limitations check
    assert len(res.limitations) >= 2


def test_scenario_2_key_individual_analysis(test_db, seed_scenario_data):
    """Scenario 2: Who are the structurally central individuals around Case 1042?"""
    agent = DomainAgentService(test_db)
    res = asyncio.run(agent.investigate(question="Who are the structurally central individuals around Case 1042?"))

    assert res.status == "COMPLETED"
    assert any(t.tool == "key_individual_analysis" for t in res.tool_trace)
    assert "structurally central" in res.summary.lower() or "individual" in res.summary.lower() or len(res.evidence) > 0


def test_scenario_3_investigator_validated_connections(test_db, seed_scenario_data):
    """Scenario 3: Which connections around Case 1042 have been investigator validated?"""
    agent = DomainAgentService(test_db)
    res = asyncio.run(agent.investigate(question="Which connections around Case 1042 have been investigator validated?"))

    assert res.status == "COMPLETED"
    assert any(t.tool == "review_status" for t in res.tool_trace)
    assert any(ev.validation_status == "VALIDATED" for ev in res.evidence)


def test_scenario_4_unusual_activity_anomalies(test_db, seed_scenario_data):
    """Scenario 4: Find unusual activity around Case 1042."""
    agent = DomainAgentService(test_db)
    res = asyncio.run(agent.investigate(question="Find unusual activity around Case 1042."))

    assert res.status == "COMPLETED"
    assert any(t.tool in ["anomaly_analysis", "pattern_analysis"] for t in res.tool_trace)


def test_scenario_5_entity_relationship_explanation(test_db, seed_scenario_data):
    """Scenario 5: Explain the relationship between Person A and Person B."""
    agent = DomainAgentService(test_db)
    res = asyncio.run(agent.investigate(question="Explain the relationship between Person A and Person B."))

    assert res.status == "COMPLETED"
    assert any(t.tool in ["graph_paths", "evidence_lookup", "review_status"] for t in res.tool_trace)
    assert res.graph_data is not None


def test_agent_bounded_execution_limits(test_db):
    """Verify loop terminates within MAX_ITERATIONS and MAX_TOOL_CALLS."""
    agent = DomainAgentService(test_db)
    res = asyncio.run(agent.investigate(question="Comprehensive deep dive on Case 1042 across all entities and phones."))

    assert res.iterations_count <= agent.MAX_ITERATIONS
    assert len(res.tool_trace) <= agent.MAX_TOOL_CALLS
    assert res.total_duration_ms > 0
