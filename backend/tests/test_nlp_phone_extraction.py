"""
Phase 4 Telecommunications: NLP Phone Entity Extraction Tests
Tests extraction of phone numbers from unstructured FIR and police incident narratives,
false-positive avoidance, and graph-ready payload formatting.
"""
import pytest
from app.services.entity_extraction_service import EntityExtractionService
from app.services.graph_ready_service import GraphReadyService


def test_extract_single_phone_from_narrative():
    """Extracts Indian mobile number from police narrative and normalizes to E.164."""
    text = "Victim stated that the suspect contacted 9876543210 demanding ransom before fleeing."
    extracted = EntityExtractionService.extract_entities(text)
    assert "phones" in extracted
    assert len(extracted["phones"]) == 1
    assert "+919876543210" in extracted["phones"]


def test_extract_multiple_phones_with_prefixes():
    """Extracts multiple phone numbers with formatting and prefixes."""
    text = (
        "Complainant reported receiving threatening calls from mobile: +91 9876543210 and "
        "another accomplice on 09123456789. Caller demanded cash transfer."
    )
    extracted = EntityExtractionService.extract_entities(text)
    assert len(extracted["phones"]) == 2
    assert "+919876543210" in extracted["phones"]
    assert "+919123456789" in extracted["phones"]


def test_nlp_phone_false_positive_rejection():
    """
    Guarantees non-hallucination and rejects numeric false positives:
    - Dates (2026-09-19)
    - FIR numbers (CR-2026-014, FIR 101/2026)
    - Vehicle registration plates (TS09AB1234, DL1CAB1234)
    - PIN codes (500034)
    - Penal codes (Section 420, IPC 302)
    - Currency figures (Rs. 50,000)
    """
    text = (
        "Incident occurred on 2026-09-19 as per FIR 101/2026 under Section 420 and IPC 302. "
        "Suspects escaped in vehicle TS09AB1234 near Banjara Hills PIN 500034 after stealing Rs. 50,000 in cash. "
        "No call was made."
    )
    extracted = EntityExtractionService.extract_entities(text)
    assert extracted["phones"] == []


def test_graph_ready_payload_includes_phone_nodes_and_relationships():
    """GraphReadyService must output Phone nodes and MENTIONS_PHONE edges for knowledge graph sync."""
    entities = {
        "locations": ["Downtown Mart"],
        "weapons": ["Iron rod"],
        "vehicles": ["Black motorcycle"],
        "persons": ["Two masked suspects"],
        "organizations": [],
        "phones": ["+919876543210"]
    }
    payload = GraphReadyService.generate_graph_payload(
        crime_id="crime-test-101",
        record_id="CR-2026-101",
        category="ROBBERY",
        occurred_at="2026-09-19T10:00:00Z",
        entities=entities,
        modus_operandi=[]
    )

    nodes = payload["nodes"]
    relationships = payload["relationships"]

    # Verify Phone node
    phone_nodes = [n for n in nodes if n["label"] == "Phone"]
    assert len(phone_nodes) == 1
    assert phone_nodes[0]["id"] == "phone:+919876543210"
    assert phone_nodes[0]["properties"]["number"] == "+919876543210"

    # Verify MENTIONS_PHONE edge
    mention_edges = [r for r in relationships if r["relation"] == "MENTIONS_PHONE"]
    assert len(mention_edges) == 1
    assert mention_edges[0]["source"] == "crime:CR-2026-101"
    assert mention_edges[0]["target"] == "phone:+919876543210"
