"""
Phase 6: Neo4j Graph Synchronization & Query Safety Tests
Tests graph edge status updating and rejection filtering in query services.
"""
import pytest
from app.services.neo4j_service import Neo4jService
from app.services.graph_query_service import GraphQueryService


@pytest.fixture(autouse=True)
def clean_graph():
    Neo4jService._force_fallback = True
    Neo4jService.reset_graph()
    yield
    Neo4jService.reset_graph()
    Neo4jService._force_fallback = False


def test_neo4j_relationship_status_update():
    """Verifies that relationships maintain status and update correctly."""
    Neo4jService.upsert_crime({"id": "CR-101", "category": "ROBBERY"})
    Neo4jService.upsert_crime({"id": "CR-102", "category": "ROBBERY"})

    # Create AI-derived edge
    Neo4jService.create_relationship(
        source_id="crime:CR-101",
        rel_type="COMMUNICATION_LINKED",
        target_id="crime:CR-102",
        properties={"confidence": 0.88},
        confidence_type="derived"
    )

    # Initial status should be AI_DERIVED
    assert len(Neo4jService._mock_relationships) == 1
    edge = Neo4jService._mock_relationships[0]
    assert edge["properties"]["status"] == "AI_DERIVED"

    # Validate edge
    updated = Neo4jService.update_relationship_status(
        source_id="crime:CR-101",
        rel_type="COMMUNICATION_LINKED",
        target_id="crime:CR-102",
        status="VALIDATED",
        reviewer_id="investigator:test",
        review_id="rev-001"
    )
    assert updated is True
    assert edge["properties"]["status"] == "VALIDATED"
    assert edge["properties"]["reviewer_id"] == "investigator:test"
    assert edge["properties"]["review_id"] == "rev-001"


def test_neo4j_modify_relationship_type():
    """Verifies that modifying relationship changes type in graph."""
    Neo4jService.upsert_entity("Person", "person:p1", {"name": "Person 1"})
    Neo4jService.upsert_entity("Person", "person:p2", {"name": "Person 2"})

    Neo4jService.create_relationship(
        source_id="person:p1",
        rel_type="CO_OCCURS_WITH",
        target_id="person:p2",
        confidence_type="derived"
    )

    # Modify to ASSOCIATED_WITH
    updated = Neo4jService.update_relationship_status(
        source_id="person:p1",
        rel_type="CO_OCCURS_WITH",
        target_id="person:p2",
        status="MODIFIED",
        reviewer_id="investigator:test",
        new_rel_type="ASSOCIATED_WITH"
    )
    assert updated is True
    edge = Neo4jService._mock_relationships[0]
    assert edge["relation"] == "ASSOCIATED_WITH"
    assert edge["properties"]["status"] == "MODIFIED"
    assert edge["properties"]["original_relationship_type"] == "CO_OCCURS_WITH"


def test_graph_query_service_suppresses_rejected_edges():
    """Verifies that get_crime_neighborhood excludes REJECTED edges unless include_rejected is True."""
    Neo4jService.upsert_crime({"id": "CR-201", "category": "BURGLARY"})
    Neo4jService.upsert_crime({"id": "CR-202", "category": "BURGLARY"})
    Neo4jService.upsert_crime({"id": "CR-203", "category": "BURGLARY"})

    # Valid edge to CR-202
    Neo4jService.create_relationship(
        source_id="crime:CR-201",
        rel_type="SHARES_MO",
        target_id="crime:CR-202",
        properties={"status": "VALIDATED"},
        confidence_type="derived"
    )

    # Rejected edge to CR-203
    Neo4jService.create_relationship(
        source_id="crime:CR-201",
        rel_type="SAME_LOCATION",
        target_id="crime:CR-203",
        properties={"status": "REJECTED"},
        confidence_type="derived"
    )

    # Standard query: rejected edge must be filtered out
    nb_default = GraphQueryService.get_crime_neighborhood("CR-201", depth=1, include_rejected=False)
    edge_targets = [e["target"].replace("crime:", "") for e in nb_default["edges"]]
    assert "CR-202" in edge_targets
    assert "CR-203" not in edge_targets

    # Audit mode query: rejected edge included
    nb_audit = GraphQueryService.get_crime_neighborhood("CR-201", depth=1, include_rejected=True)
    audit_targets = [e["target"].replace("crime:", "") for e in nb_audit["edges"]]
    assert "CR-202" in audit_targets
    assert "CR-203" in audit_targets
