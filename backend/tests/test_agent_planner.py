"""
Phase 7: Domain AI Investigation Agent — Investigation Planner Tests
Tests query intent classification, entity extraction heuristics,
deterministic planning, and allowlist validation.
"""
import pytest
import asyncio
from app.services.agent.planner import InvestigationPlanner
from app.services.agent.models import QueryCategory
from app.services.agent.tool_registry import ToolRegistry


def test_planner_classify_questions():
    """Verify correct classification across diverse law enforcement queries."""
    cases = [
        ("What cases involve phone 9876543210?", QueryCategory.TELECOM),
        ("Who are the structurally central individuals around Case 1042?", QueryCategory.KEY_INDIVIDUAL),
        ("Are Cases 1042 and 1088 connected?", QueryCategory.CROSS_CASE),
        ("Find unusual activity and anomalies around Case 1042.", QueryCategory.ANOMALY),
        ("What patterns exist in armed robbery series?", QueryCategory.PATTERN),
        ("Find cases with similar modus operandi.", QueryCategory.SEMANTIC),
        ("Which connections have been investigator validated?", QueryCategory.EVIDENCE),
        ("Explain the path between Person A and Person B.", QueryCategory.NETWORK),
    ]
    for question, expected_cat in cases:
        assert InvestigationPlanner.classify_question(question) == expected_cat


def test_planner_extract_scope_heuristics():
    """Verify regex and heuristic extraction of anchor entities."""
    # Phone extraction
    scope1 = InvestigationPlanner.extract_scope_heuristics("Investigate activity for 9876543210 in Delhi.")
    assert scope1.phone_number == "9876543210"

    # Case extraction
    scope2 = InvestigationPlanner.extract_scope_heuristics("Find cases connected to Case 1042.")
    assert scope2.crime_id == "1042"

    # FIR extraction
    scope3 = InvestigationPlanner.extract_scope_heuristics("Show details for FIR-2045.")
    assert scope3.crime_id == "2045"


def test_planner_deterministic_plan_generation():
    """Verify that deterministic planning produces valid allowlisted steps."""
    q = "Who are the structurally central individuals around Case 1042?"
    plan = asyncio.run(InvestigationPlanner.create_plan(q))

    assert plan.category == QueryCategory.KEY_INDIVIDUAL
    assert plan.scope.crime_id == "1042"
    assert len(plan.steps) >= 2

    # Ensure all planned steps are in the approved tool allowlist
    for step in plan.steps:
        assert ToolRegistry.is_tool_allowed(step.tool)
        assert step.tool in ["crime_detail", "network_subgraph", "key_individual_analysis", "evidence_lookup"]


def test_planner_telecom_scenario():
    """Verify planning for telecom / CDR query."""
    q = "Analyze call patterns and connections for phone 9876543210."
    plan = asyncio.run(InvestigationPlanner.create_plan(q))

    assert plan.category == QueryCategory.TELECOM
    assert any(s.tool == "phone_lookup" for s in plan.steps)
    assert any(s.tool == "cdr_analysis" for s in plan.steps)
    assert any(s.tool == "cross_case_analysis" for s in plan.steps)
