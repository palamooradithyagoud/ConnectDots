"""
Phase 4: Investigation Intelligence & Graph RAG Tests
Tests LLMProvider abstraction, GraphRAGService hybrid retrieval, citation parsing, and APIs.
"""
import pytest
import asyncio
import sqlite3
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.models.crime import Crime
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.factory import get_llm_provider
from app.services.neo4j_service import Neo4jService
from app.services.graph_rag_service import GraphRAGService


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


from app.services.llm.groq_provider import GroqProvider


def test_llm_provider_abstraction():
    """Tests that MockLLMProvider synthesizes structured sections from evidence."""
    provider = get_llm_provider(force_mock=True)
    assert isinstance(provider, MockLLMProvider)


    mock_evidence = {
        "primary_crime": {
            "id": "crime-014",
            "record_id": "CR-2026-014",
            "category": "ROBBERY",
            "location_name": "7-Eleven Mart"
        },
        "similar_crimes": [
            {
                "crime_id": "crime-021",
                "similarity": 0.88,
                "category": "ROBBERY"
            }
        ],
        "graph_connections": [
            {
                "relationship": "SHARES_MO",
                "confidence_type": "derived",
                "confidence": 0.95,
                "to": "crime-021"
            }
        ],
        "supporting_patterns": [
            {"id": "pat-01", "description": "Serial convenience store robberies"}
        ]
    }

    import json
    prompt = f"```json\n{json.dumps(mock_evidence)}\n```"
    response = asyncio.run(provider.generate(prompt=prompt, system_prompt="System instructions"))

    assert "### Summary" in response
    assert "### Connections" in response
    assert "### Evidence" in response
    assert "### Uncertainty" in response
    assert "crime-014" in response or "CR-2026-014" in response
    assert "crime-021" in response


def test_groq_provider_initialization():
    """Tests that GroqProvider initializes when configured in settings."""
    provider = get_llm_provider()
    assert isinstance(provider, GroqProvider)
    assert provider.model == "openai/gpt-oss-120b"


def test_graph_rag_service_with_evidence(test_db):
    """Tests end-to-end Graph RAG execution when a matching crime exists in the database."""
    now = datetime.now(timezone.utc)
    crime = Crime(
        id="c-rag-14",
        record_id="CR-2026-014",
        crime_type="Armed Robbery",
        category="ROBBERY",
        location_name="Downtown Gas Station",
        occurred_at=now,
        latitude=37.77,
        longitude=-122.41,
        description="Armed suspects in masks demanded cash from register and fled.",
        source="cad_feed",
        status="VALID"
    )
    test_db.add(crime)
    test_db.commit()

    # Pre-populate graph
    Neo4jService.upsert_crime({
        "id": crime.id,
        "record_id": crime.record_id,
        "category": crime.category,
        "location_name": crime.location_name
    })

    result = asyncio.run(GraphRAGService.query(
        db=test_db,
        question="Find crimes similar to CR-2026-014 and explain the connections between them."
    ))

    assert "answer" in result
    assert "structured_sections" in result
    assert result["structured_sections"]["summary"] != ""
    assert "citations" in result
    assert "meta" in result
    assert result["meta"]["target_crime_id"] == crime.id


def test_graph_rag_insufficient_evidence(test_db):
    """Verifies that an unrecognizable query returns graceful insufficient evidence without hallucinating."""
    result = asyncio.run(GraphRAGService.query(
        db=test_db,
        question="What happened on Mars with alien space pirates?"
    ))

    assert "Insufficient evidence" in result["answer"]
    assert result["confidence"] == 0.0
    assert len(result["citations"]) == 0


def test_investigation_and_graph_apis(client, test_db):
    """Tests FastAPI endpoints for graph and investigation services."""
    # 1. Stats endpoint
    stats_res = client.get("/api/v1/graph/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert "total_nodes" in stats_data
    assert "total_relationships" in stats_data

    # 2. Examples endpoint
    examples_res = client.get("/api/v1/investigation/examples")
    assert examples_res.status_code == 200
    examples = examples_res.json().get("examples", [])
    assert len(examples) >= 3

    # 3. Investigation query endpoint
    query_payload = {"question": "Find crimes similar to CR-2026-014"}
    query_res = client.post("/api/v1/investigation/query", json=query_payload)
    assert query_res.status_code == 200
    res_data = query_res.json()
    assert "answer" in res_data
    assert "structured_sections" in res_data
    assert "citations" in res_data

    # 4. Graph sync endpoint
    sync_res = client.post("/api/v1/graph/sync")
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "completed"
