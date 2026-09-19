"""
Phase 6: Graph RAG Investigator Validation Grounding Tests
Verifies that Graph RAG system prompts and context segregation strictly adhere to
investigator validation rules (validated vs AI-derived vs rejected).
"""
import pytest
from app.services.graph_rag_service import GraphRAGService, INVESTIGATION_SYSTEM_PROMPT


def test_system_prompt_investigator_validation_rules():
    """Verifies that the LLM system prompt enforces human validation rules."""
    prompt = INVESTIGATION_SYSTEM_PROMPT
    assert "HUMAN-IN-THE-LOOP INVESTIGATOR VALIDATION RULES" in prompt
    assert "investigator-validated" in prompt
    assert "pending review" in prompt
    assert "rejected during investigator review" in prompt
    assert "Never convert association into criminal guilt" in prompt


def test_format_context_segregates_validated_pending_rejected():
    """Verifies that _format_context groups connections by review status."""
    evidence = {
        "graph_connections": [
            {
                "source": "crime:CR-001",
                "relation": "SHARES_PHONE",
                "target": "crime:CR-002",
                "status": "VALIDATED"
            },
            {
                "source": "crime:CR-001",
                "relation": "COMMUNICATION_LINKED",
                "target": "crime:CR-003",
                "status": "AI_DERIVED",
                "confidence": 0.85
            },
            {
                "source": "crime:CR-001",
                "relation": "SAME_LOCATION",
                "target": "crime:CR-004",
                "status": "REJECTED",
                "rejection_reason": "Coincidental public bus terminal overlap"
            }
        ]
    }

    ctx = GraphRAGService._format_context(evidence)

    assert "### INVESTIGATOR-VALIDATED CONNECTIONS" in ctx
    assert "[INVESTIGATOR-VALIDATED] crime:CR-001 -[SHARES_PHONE]-> crime:CR-002" in ctx

    assert "### AI-DERIVED CONNECTIONS (PENDING REVIEW)" in ctx
    assert "[AI-DERIVED / PENDING REVIEW] crime:CR-001 -[COMMUNICATION_LINKED]-> crime:CR-003" in ctx

    assert "### REJECTED CONNECTIONS (EXCLUDED FROM ACTIVE EVIDENCE)" in ctx
    assert "[REJECTED BY INVESTIGATOR] crime:CR-001 -[SAME_LOCATION]-> crime:CR-004" in ctx
    assert "Coincidental public bus terminal overlap" in ctx


def test_format_context_empty_graph_connections():
    """Verifies graceful handling when no graph connections exist."""
    evidence = {"graph_connections": []}
    ctx = GraphRAGService._format_context(evidence)
    assert "### INVESTIGATOR-VALIDATED CONNECTIONS" not in ctx
    assert "### AI-DERIVED CONNECTIONS" not in ctx
