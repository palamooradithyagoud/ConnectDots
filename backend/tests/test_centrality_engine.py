"""
Phase 5 Person Network: Centrality Engine & Structural Metrics Tests
Tests deterministic synthetic graphs (Star, Chain, Bridge-node, Disconnected),
exact NetworkX mathematical fallbacks, PageRank, and Zero-Guilt structural explanations.
"""
import pytest
import networkx as nx
from datetime import datetime, timezone

from app.services.centrality_service import CentralityService
from app.services.neo4j_service import Neo4jService
from app.models.person import Person, CrimePersonAssociation


@pytest.fixture(autouse=True)
def reset_graph_state():
    """Ensures graph state is clean before each test and runs in in-memory fallback."""
    Neo4jService._force_fallback = True
    Neo4jService.reset_graph()
    yield
    Neo4jService.reset_graph()
    Neo4jService._force_fallback = False


def test_star_graph_centrality():
    """
    In a Star graph with center H and 4 leaves (L1, L2, L3, L4):
    - Center H must have degree centrality = 1.0 (highest).
    - Center H must have betweenness centrality = 1.0 (highest).
    - Leaves must have betweenness centrality = 0.0.
    """
    # 1. Setup in Neo4j in-memory store
    Neo4jService.upsert_person({"id": "person:hub", "canonical_name": "Hub Center"})
    for i in range(1, 5):
        Neo4jService.upsert_person({"id": f"person:leaf_{i}", "canonical_name": f"Leaf {i}"})
        Neo4jService.create_relationship(
            from_id="person:hub",
            rel_type="CO_OCCURS_WITH",
            to_id=f"person:leaf_{i}",
            properties={"weight": 1.0},
            confidence_type="derived"
        )

    # 2. Extract and compute centrality
    metrics = CentralityService.compute_person_centrality_fallback(scope="global")
    assert len(metrics) == 5

    hub_metric = next(m for m in metrics if m["person_id"] == "person:hub")
    leaf_metrics = [m for m in metrics if m["person_id"] != "person:hub"]

    # Hub has maximum degree centrality
    assert hub_metric["degree_centrality"] == pytest.approx(1.0, abs=1e-3)
    # Hub has maximum betweenness centrality
    assert hub_metric["betweenness_centrality"] == pytest.approx(1.0, abs=1e-3)
    # Leaves have zero betweenness centrality
    for lm in leaf_metrics:
        assert lm["betweenness_centrality"] == pytest.approx(0.0, abs=1e-3)
        assert lm["degree_centrality"] < hub_metric["degree_centrality"]


def test_chain_graph_centrality():
    """
    In a Chain graph A - B - C - D - E:
    - Middle node C must have the strictly highest betweenness centrality.
    - Endpoints A and E have betweenness = 0.0 and minimum degree centrality.
    """
    nodes = ["person:A", "person:B", "person:C", "person:D", "person:E"]
    for n in nodes:
        Neo4jService.upsert_person({"id": n, "canonical_name": n.replace("person:", "Person ")})

    edges = [
        ("person:A", "person:B"),
        ("person:B", "person:C"),
        ("person:C", "person:D"),
        ("person:D", "person:E"),
    ]
    for u, v in edges:
        Neo4jService.create_relationship(
            from_id=u, rel_type="CO_OCCURS_WITH", to_id=v,
            properties={"weight": 1.0}, confidence_type="derived"
        )

    metrics = CentralityService.compute_person_centrality_fallback(scope="global")
    by_id = {m["person_id"]: m for m in metrics}

    # Center C has highest betweenness
    assert by_id["person:C"]["betweenness_centrality"] > by_id["person:B"]["betweenness_centrality"]
    assert by_id["person:C"]["betweenness_centrality"] > by_id["person:D"]["betweenness_centrality"]

    # Endpoints A and E have 0 betweenness
    assert by_id["person:A"]["betweenness_centrality"] == pytest.approx(0.0, abs=1e-4)
    assert by_id["person:E"]["betweenness_centrality"] == pytest.approx(0.0, abs=1e-4)


def test_bridge_node_betweenness_centrality():
    """
    In two cliques C1={A, B, C} and C2={X, Y, Z} connected by bridge node M:
    Clique 1 connected to M (C - M), and M connected to Clique 2 (M - X).
    Bridge node M must have the highest betweenness centrality in the entire graph.
    """
    all_nodes = [
        "person:A", "person:B", "person:C",
        "person:M",
        "person:X", "person:Y", "person:Z"
    ]
    for n in all_nodes:
        Neo4jService.upsert_person({"id": n, "canonical_name": n.replace("person:", "Person ")})

    # Clique 1 edges
    c1_edges = [("person:A", "person:B"), ("person:B", "person:C"), ("person:A", "person:C")]
    for u, v in c1_edges:
        Neo4jService.create_relationship(u, "CO_OCCURS_WITH", v, confidence_type="derived")

    # Clique 2 edges
    c2_edges = [("person:X", "person:Y"), ("person:Y", "person:Z"), ("person:X", "person:Z")]
    for u, v in c2_edges:
        Neo4jService.create_relationship(u, "CO_OCCURS_WITH", v, confidence_type="derived")

    # Bridge connections: C - M - X
    Neo4jService.create_relationship("person:C", "CO_OCCURS_WITH", "person:M", confidence_type="derived")
    Neo4jService.create_relationship("person:M", "CO_OCCURS_WITH", "person:X", confidence_type="derived")

    metrics = CentralityService.compute_person_centrality_fallback(scope="global")
    by_id = {m["person_id"]: m for m in metrics}

    bridge_metric = by_id["person:M"]
    for nid, m in by_id.items():
        if nid != "person:M":
            assert bridge_metric["betweenness_centrality"] > m["betweenness_centrality"], (
                f"Bridge node M must strictly exceed betweenness of {nid}"
            )


def test_disconnected_graph_handled_gracefully():
    """Verifies that disconnected components do not raise errors or divide-by-zero exceptions."""
    Neo4jService.upsert_person({"id": "person:comp1_a", "canonical_name": "C1 A"})
    Neo4jService.upsert_person({"id": "person:comp1_b", "canonical_name": "C1 B"})
    Neo4jService.create_relationship("person:comp1_a", "CO_OCCURS_WITH", "person:comp1_b", confidence_type="derived")

    Neo4jService.upsert_person({"id": "person:isolated", "canonical_name": "Isolated Node"})

    metrics = CentralityService.compute_person_centrality_fallback(scope="global")
    assert len(metrics) == 3

    isolated = next(m for m in metrics if m["person_id"] == "person:isolated")
    assert isolated["degree_centrality"] == 0.0
    assert isolated["betweenness_centrality"] == 0.0
    assert isolated["pagerank"] > 0.0  # PageRank distributes baseline damping factor


def test_property_cleaner_and_zero_guilt_explanation():
    """Verifies property sanitization against complex objects and Zero-Guilt neutral explanations."""
    props = {
        "name": "Test Node",
        "created_at": datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        "nested": {"key": 123, "active": True},
        "score": 0.85,
        "empty": None
    }
    cleaned = CentralityService._clean_properties(props)
    assert cleaned["name"] == "Test Node"
    assert "2026-03-01" in cleaned["created_at"]
    assert cleaned["score"] == 0.85
    assert cleaned["nested"] == "{'key': 123, 'active': True}"

    # Zero-Guilt Principle check:
    explanation = CentralityService.generate_structural_explanation(
        degree=0.8,
        betweenness=0.75,
        pagerank=0.15,
        case_count=3,
        phone_count=2
    )
    assert "guilt" not in explanation.lower()
    assert "guilty" not in explanation.lower()
    assert "danger" not in explanation.lower()
    assert "criminal score" not in explanation.lower()
    assert "structural" in explanation.lower() or "broker" in explanation.lower() or "bridge" in explanation.lower()
