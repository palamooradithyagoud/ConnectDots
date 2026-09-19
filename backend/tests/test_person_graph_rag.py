"""
Phase 5 Person Network: Graph RAG Grounding & Zero-Guilt System Prompt Tests
Tests GraphRAGService integration with Person Network, Key Individuals context injection,
and strict Zero-Guilt limitation disclosures.
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
    """Ensures graph state is clean before each test and runs in in-memory fallback."""
    Neo4jService._force_fallback = True
    Neo4jService.reset_graph()
    yield
    Neo4jService.reset_graph()
    Neo4jService._force_fallback = False


def test_system_prompt_zero_guilt_limitation():
    """Verifies that the investigation system prompt explicitly mandates the Zero-Guilt limitation disclosure."""
    prompt = GraphRAGService.INVESTIGATION_SYSTEM_PROMPT
    assert "CENTRALITY & PERSON NETWORK LIMITATION" in prompt
    assert "DO NOT indicate guilt" in prompt
    assert "network topology" in prompt
    assert "bridge/broker position" in prompt


def test_format_context_includes_key_individuals():
    """Verifies that _format_context renders Key Individuals and structural centrality metrics."""
    mock_evidence = {
        "primary_crime": {
            "id": "c-rag-1",
            "record_id": "FIR-2026-RAG",
            "category": "EXTORTION",
            "location_name": "Delhi Market"
        },
        "similar_crimes": [],
        "graph_connections": [],
        "telecom_intelligence": [],
        "key_individuals": [
            {
                "person_id": "person:vikram_singh",
                "canonical_name": "Vikram Singh",
                "role": "ACCUSED",
                "degree_centrality": 0.85,
                "betweenness_centrality": 0.62,
                "pagerank": 0.18,
                "structural_role": "High Degree Hub / Bridge",
                "associated_cases": 3,
                "associated_phones": ["+919876543210"],
                "structural_notes": "High degree connectivity across multiple cases."
            }
        ]
    }

    formatted = GraphRAGService._format_context(mock_evidence)
    assert "### KEY INDIVIDUALS & PERSON NETWORK (CENTRALITY INTELLIGENCE)" in formatted
    assert "Vikram Singh (ID: person:vikram_singh)" in formatted
    assert "Degree Centrality: 0.85" in formatted
    assert "Betweenness Centrality: 0.62" in formatted
    assert "PageRank: 0.18" in formatted
    assert "+919876543210" in formatted


def test_graph_rag_investigate_with_person_intelligence(test_db):
    """Verifies end-to-end GraphRAGService.investigate_crime collects and utilizes person intelligence."""
    now = datetime.now(timezone.utc)
    crime = Crime(
        id="c-rag-person",
        record_id="FIR-2026-RAG-P",
        crime_type="Armed Extortion",
        category="EXTORTION",
        location_name="Chandni Chowk",
        occurred_at=now,
        latitude=28.6505,
        longitude=77.2303,
        description="Armed extortion operation led by Vikram Singh.",
        source="fir_cad",
        status="VALID"
    )
    test_db.add(crime)

    person = Person(
        id="person:vikram_singh",
        canonical_name="Vikram Singh",
        normalized_name="vikram singh",
        aliases=["Vicky"]
    )
    test_db.add(person)

    assoc = CrimePersonAssociation(
        crime_id=crime.id,
        person_id=person.id,
        role="ACCUSED",
        evidence_excerpt="Armed extortion operation led by Vikram Singh.",
        confidence=0.95
    )
    test_db.add(assoc)

    phone = PhoneNumber(
        id="phone:+919876543210",
        raw_number="9876543210",
        normalized_number="+919876543210",
        is_valid=True
    )
    test_db.add(phone)

    ppa = PersonPhoneAssociation(
        phone_id=phone.id,
        person_id=person.id,
        person_name=person.canonical_name,
        confidence=0.9
    )
    test_db.add(ppa)
    test_db.commit()

    # Graph nodes
    Neo4jService.upsert_crime({"id": crime.id, "record_id": crime.record_id, "category": crime.category})
    Neo4jService.upsert_person({"id": person.id, "canonical_name": person.canonical_name})
    Neo4jService.create_relationship(crime.id, "MENTIONS_PERSON", person.id, confidence_type="explicit")
    Neo4jService.create_relationship(person.id, "USES_PHONE", phone.id, confidence_type="explicit")

    # Run investigation with mock LLM provider
    result = GraphRAGService.investigate_crime(crime_id=crime.id, db=test_db, force_mock=True)

    assert result["crime_id"] == crime.id
    assert "evidence_used" in result
    key_inds = result["evidence_used"].get("key_individuals", [])
    assert len(key_inds) >= 1
    assert key_inds[0]["person_id"] == "person:vikram_singh"
    assert "synthesis" in result
    assert result["synthesis"] != ""


def test_graph_rag_graceful_when_no_persons(test_db):
    """Verifies GraphRAGService executes gracefully without error when no persons exist for a crime."""
    now = datetime.now(timezone.utc)
    crime = Crime(
        id="c-rag-empty",
        record_id="FIR-2026-EMPTY",
        crime_type="Vandalism",
        category="VANDALISM",
        location_name="Public Park",
        occurred_at=now,
        latitude=28.6,
        longitude=77.2,
        description="Public bench spray painted overnight.",
        source="fir_cad",
        status="VALID"
    )
    test_db.add(crime)
    test_db.commit()

    Neo4jService.upsert_crime({"id": crime.id, "record_id": crime.record_id, "category": crime.category})

    result = GraphRAGService.investigate_crime(crime_id=crime.id, db=test_db, force_mock=True)
    assert result["crime_id"] == crime.id
    assert result["evidence_used"]["key_individuals"] == []
