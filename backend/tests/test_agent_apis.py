"""
Phase 7: Domain AI Investigation Agent — REST API Endpoint Tests
Tests POST /api/v1/agent/investigate, GET /api/v1/agent/tools, and GET /api/v1/agent/examples.
"""
import pytest
import sqlite3
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_api_list_tools(client):
    """Verify GET /api/v1/agent/tools returns 16 registered tools."""
    res = client.get("/api/v1/agent/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 16
    assert len(data["tools"]) == 16
    names = [t["name"] for t in data["tools"]]
    assert "crime_search" in names
    assert "key_individual_analysis" in names
    assert "review_status" in names


def test_api_get_examples(client):
    """Verify GET /api/v1/agent/examples returns 5 investigation scenarios."""
    res = client.get("/api/v1/agent/examples")
    assert res.status_code == 200
    data = res.json()
    assert len(data["examples"]) == 5
    scenarios = [e["scenario"] for e in data["examples"]]
    assert "Scenario 1" in scenarios
    assert "Scenario 2" in scenarios


def test_api_post_investigate_success(client):
    """Verify POST /api/v1/agent/investigate returns structured response."""
    payload = {
        "question": "Find cases connected to Case 1042 through phones."
    }
    res = client.post("/api/v1/agent/investigate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "investigation_id" in data
    assert "summary" in data
    assert "findings" in data
    assert "tool_trace" in data
    assert "limitations" in data


def test_api_post_investigate_validation_error(client):
    """Verify POST /api/v1/agent/investigate with empty question fails 422."""
    res = client.post("/api/v1/agent/investigate", json={"question": ""})
    assert res.status_code == 422
