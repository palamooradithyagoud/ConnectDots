"""
Phase 7: Domain AI Investigation Agent — Tool Registry & Executor Tests
Verifies that all 16 tools are registered, schemas are strictly enforced,
limits are clamped, and tool execution produces normalized evidence.
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
from app.models.review import InvestigationRelationshipReview, ReviewStatus
from app.services.agent.tool_registry import ToolRegistry
from app.services.agent.tool_executor import SafeToolExecutor
from app.services.agent.models import ToolCall
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


def test_tool_registry_contains_16_approved_tools():
    """Verify exactly the 16 approved domain investigation tools are registered."""
    tools = ToolRegistry.list_tools()
    assert len(tools) == 16
    expected_tools = {
        "crime_search", "crime_detail", "semantic_search", "graph_connections",
        "graph_paths", "phone_lookup", "phone_connections", "cdr_analysis",
        "cross_case_analysis", "key_individual_analysis", "network_subgraph",
        "pattern_analysis", "anomaly_analysis", "cluster_analysis",
        "evidence_lookup", "review_status"
    }
    actual_names = {t.name for t in tools}
    assert actual_names == expected_tools


def test_tool_registry_rejects_unauthorized_tools():
    """Verify unauthorized or dangerous tool calls are strictly rejected."""
    dangerous = ["execute_sql", "execute_cypher", "run_bash", "delete_records", "modify_graph", "drop_table"]
    for t in dangerous:
        assert not ToolRegistry.is_tool_allowed(t)
        with pytest.raises(ValueError, match="Unknown or unauthorized tool"):
            ToolRegistry.validate_tool_arguments(t, {})


def test_tool_registry_argument_validation_and_clamping():
    """Verify tool argument validation clamps bounds and enforces data types."""
    valid_args = ToolRegistry.validate_tool_arguments("crime_search", {"query": "robbery", "limit": 25})
    assert valid_args["limit"] == 25
    assert valid_args["query"] == "robbery"

    # Excessive limit clamped / rejected by schema
    with pytest.raises(ValueError):
        ToolRegistry.validate_tool_arguments("crime_search", {"limit": 500})  # max 50

    # Max hops clamped / rejected
    with pytest.raises(ValueError):
        ToolRegistry.validate_tool_arguments("graph_connections", {"crime_id": "1042", "max_hops": 10})  # max 3


def test_tool_executor_crime_search_and_detail(test_db):
    """Test execution of crime_search and crime_detail tools."""
    c = Crime(
        id="crime-test-1042",
        record_id="1042",
        crime_type="Armed Robbery",
        category="Armed Robbery",
        location_name="Connaught Place, Delhi",
        latitude=28.6315,
        longitude=77.2167,
        occurred_at=datetime(2026, 8, 15, tzinfo=timezone.utc),
        source="FIR_REPORT",
        description="Armed robbery at financial institution using getaway bike."
    )
    test_db.add(c)
    test_db.commit()

    executor = SafeToolExecutor(test_db)

    # 1. Test crime_search
    res, ev = asyncio.run(executor.execute_tool(ToolCall(
        tool="crime_search",
        arguments={"query": "robbery", "limit": 10}
    )))
    assert res.success is True
    assert res.evidence_count >= 1
    assert any(e.source_record_id == c.id for e in ev)
    assert ev[0].validation_status == "VALIDATED"

    # 2. Test crime_detail
    res_d, ev_d = asyncio.run(executor.execute_tool(ToolCall(
        tool="crime_detail",
        arguments={"crime_id": "1042"}
    )))
    assert res_d.success is True
    assert res_d.data["crime"]["category"] == "Armed Robbery"
    assert len(ev_d) == 1
    assert ev_d[0].source_entity == "1042"


def test_tool_executor_phone_lookup_and_connections(test_db):
    """Test execution of phone_lookup and phone_connections tools."""
    p = PhoneNumber(
        id="phone-uuid-1",
        normalized_number="+919876543210",
        national_number="9876543210",
        carrier="Airtel",
        circle="Delhi",
        line_type="MOBILE",
        is_valid=True
    )
    test_db.add(p)
    test_db.commit()

    executor = SafeToolExecutor(test_db)

    res, ev = asyncio.run(executor.execute_tool(ToolCall(
        tool="phone_lookup",
        arguments={"phone_number": "9876543210"}
    )))
    assert res.success is True
    assert res.data["phone"]["carrier"] == "Airtel"
    assert len(ev) == 1
    assert ev[0].evidence_type == "PHONE"


def test_tool_executor_review_status(test_db):
    """Test execution of review_status tool."""
    rev = InvestigationRelationshipReview(
        id="rev-test-1",
        relationship_ref="Person:P1->ASSOCIATED_WITH->Crime:C1",
        source_entity_type="Person",
        source_entity_id="P1",
        relationship_type="ASSOCIATED_WITH",
        original_relationship_type="ASSOCIATED_WITH",
        target_entity_type="Crime",
        target_entity_id="C1",
        original_confidence=0.88,
        provenance="NLP_EXTRACTED",
        status=ReviewStatus.VALIDATED.value
    )
    test_db.add(rev)
    test_db.commit()

    executor = SafeToolExecutor(test_db)

    res, ev = asyncio.run(executor.execute_tool(ToolCall(
        tool="review_status",
        arguments={"status": "VALIDATED"}
    )))
    assert res.success is True
    assert res.data["total_reviews"] >= 1
    assert any(e.validation_status == "VALIDATED" for e in ev)


def test_tool_executor_unauthorized_tool_fails_safely(test_db):
    """Verify tool executor safely fails if an unallowlisted tool is requested."""
    executor = SafeToolExecutor(test_db)
    res, ev = asyncio.run(executor.execute_tool(ToolCall(
        tool="malicious_shell_exec",
        arguments={"cmd": "whoami"}
    )))
    assert res.success is False
    assert "not authorized" in res.error
    assert len(ev) == 0
