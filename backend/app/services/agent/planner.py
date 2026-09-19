"""
Phase 7: Domain AI Investigation Agent — Investigation Planner
Converts natural language investigation inquiries into structured, allowlisted tool execution plans.
Provides dynamic LLM planning with deterministic domain fallback.
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from app.services.agent.models import (
    InvestigationPlan,
    InvestigationScope,
    ToolCall,
    QueryCategory
)
from app.services.agent.tool_registry import ToolRegistry
from app.services.agent.prompts import AGENT_PLANNER_SYSTEM_PROMPT
from app.services.llm.factory import get_llm_provider
from app.services.phone_normalization_service import PhoneNormalizationService

logger = logging.getLogger("connectdots_planner")


class InvestigationPlanner:
    """
    Constructs bounded investigation plans from natural language queries.
    Uses Groq LLM when available, and falls back to a deterministic domain planner.
    """

    PHONE_REGEX = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}")
    FIR_REGEX = re.compile(r"(?:FIR[-\s]?)?(\b\d{3,6}\b|C\d{3,6}|Case[-\s]?\d{3,6})", re.IGNORECASE)

    @classmethod
    def extract_scope_heuristics(cls, question: str) -> InvestigationScope:
        """
        Extracts anchor entities (phone numbers, crime/FIR identifiers) using robust heuristics.
        """
        phone_match = cls.PHONE_REGEX.search(question)
        phone = phone_match.group(0) if phone_match else None

        fir_match = re.search(r"(?:Case|FIR)[-\s]?(\d{3,6})", question, re.IGNORECASE)
        crime_id = fir_match.group(1) if fir_match else None

        if not crime_id:
            # Check for general 4-digit number like "1042"
            num_match = re.search(r"\b(10\d{2}|11\d{2}|20\d{2})\b", question)
            if num_match:
                crime_id = num_match.group(1)

        # Check for person identifiers like "Person A", "Palamoor"
        person_match = re.search(r"(?:Person\s+[A-Z]|Suspect\s+[A-Z])", question, re.IGNORECASE)
        entity_id = person_match.group(0) if person_match else None

        return InvestigationScope(
            crime_id=crime_id,
            entity_id=entity_id,
            phone_number=phone,
            max_hops=2
        )

    @classmethod
    def classify_question(cls, question: str) -> QueryCategory:
        """
        Classifies the investigation intent into domain categories.
        """
        q = question.lower()
        if any(w in q for w in ["central", "centrality", "pagerank", "betweenness", "key individual", "mastermind", "leader"]):
            return QueryCategory.KEY_INDIVIDUAL
        if any(w in q for w in ["phone", "call", "cdr", "telecom", "subscriber", "burner"]):
            return QueryCategory.TELECOM
        if any(w in q for w in ["connected", "link", "across cases", "cross-case", "shared"]):
            return QueryCategory.CROSS_CASE
        if any(w in q for w in ["path", "shortest path", "between", "how are"]):
            return QueryCategory.NETWORK
        if any(w in q for w in ["similar", "resembles", "semantic"]):
            return QueryCategory.SEMANTIC
        if any(w in q for w in ["unusual", "anomaly", "anomalies", "spike", "outlier"]):
            return QueryCategory.ANOMALY
        if any(w in q for w in ["pattern", "series", "m.o.", "modus operandi", "trend"]):
            return QueryCategory.PATTERN
        if any(w in q for w in ["validated", "rejected", "review status", "pending review", "investigator"]):
            return QueryCategory.EVIDENCE

        return QueryCategory.MIXED_INVESTIGATION

    @classmethod
    def deterministic_plan(cls, question: str, scope: InvestigationScope, category: QueryCategory) -> InvestigationPlan:
        """
        Constructs a high-precision deterministic plan when LLM is offline or in mock mode.
        """
        steps: List[ToolCall] = []

        if category == QueryCategory.TELECOM:
            target_phone = scope.phone_number or "9876543210"
            steps.append(ToolCall(tool="phone_lookup", arguments={"phone_number": target_phone}, purpose="Lookup phone subscriber and carrier details"))
            steps.append(ToolCall(tool="phone_connections", arguments={"phone_number": target_phone, "limit": 20}, purpose="Find crimes and suspects associated with phone"))
            steps.append(ToolCall(tool="cross_case_analysis", arguments={"phone_number": target_phone, "limit": 20}, purpose="Check cross-jurisdictional case linkages via phone"))
            steps.append(ToolCall(tool="cdr_analysis", arguments={"phone_number": target_phone, "days_window": 30}, purpose="Analyze call detail frequency and contacts"))

        elif category == QueryCategory.KEY_INDIVIDUAL:
            cid = scope.crime_id or "1042"
            steps.append(ToolCall(tool="crime_detail", arguments={"crime_id": cid}, purpose="Retrieve anchor crime context"))
            steps.append(ToolCall(tool="network_subgraph", arguments={"crime_id": cid, "depth": 2}, purpose="Explore local graph neighborhood"))
            steps.append(ToolCall(tool="key_individual_analysis", arguments={"scope_crime_id": cid, "limit": 10}, purpose="Calculate Degree, Betweenness, and PageRank metrics"))
            steps.append(ToolCall(tool="evidence_lookup", arguments={"crime_id": cid}, purpose="Gather corroborating documentary evidence"))

        elif category == QueryCategory.CROSS_CASE:
            cid = scope.crime_id or "1042"
            steps.append(ToolCall(tool="crime_detail", arguments={"crime_id": cid}, purpose="Retrieve primary case narrative"))
            steps.append(ToolCall(tool="graph_connections", arguments={"crime_id": cid, "max_hops": 2}, purpose="Traverse knowledge graph for shared entities"))
            steps.append(ToolCall(tool="cross_case_analysis", arguments={"crime_id": cid}, purpose="Identify cross-case linkages via shared phones"))
            steps.append(ToolCall(tool="review_status", arguments={"crime_id": cid}, purpose="Check investigator validation status of links"))

        elif category == QueryCategory.ANOMALY:
            cid = scope.crime_id
            steps.append(ToolCall(tool="anomaly_analysis", arguments={"crime_id": cid, "limit": 15}, purpose="Retrieve statistical and temporal crime anomalies"))
            steps.append(ToolCall(tool="pattern_analysis", arguments={"crime_id": cid, "limit": 10}, purpose="Check for matching modus operandi patterns"))

        elif category == QueryCategory.PATTERN:
            cid = scope.crime_id
            steps.append(ToolCall(tool="pattern_analysis", arguments={"crime_id": cid, "limit": 15}, purpose="Retrieve ML-discovered crime patterns"))
            steps.append(ToolCall(tool="cluster_analysis", arguments={"limit": 10}, purpose="Check spatial and semantic crime clusters"))

        elif category == QueryCategory.SEMANTIC:
            steps.append(ToolCall(tool="semantic_search", arguments={"query": question, "limit": 10, "threshold": 0.5}, purpose="Perform vector similarity search for modus operandi"))
            steps.append(ToolCall(tool="cluster_analysis", arguments={"cluster_type": "semantic", "limit": 10}, purpose="Check semantic clusters"))

        elif category == QueryCategory.EVIDENCE:
            cid = scope.crime_id
            steps.append(ToolCall(tool="review_status", arguments={"crime_id": cid, "limit": 20}, purpose="Query human investigator validation queue"))
            if cid:
                steps.append(ToolCall(tool="crime_detail", arguments={"crime_id": cid}, purpose="Retrieve anchor incident details"))

        elif category == QueryCategory.NETWORK:
            source = scope.entity_id or "Person A"
            target = "Person B"
            steps.append(ToolCall(tool="graph_paths", arguments={"source_id": source, "target_id": target, "max_depth": 3}, purpose="Find shortest path in knowledge graph"))
            steps.append(ToolCall(tool="evidence_lookup", arguments={"person_id": source}, purpose="Retrieve ground truth evidence for entities"))
            steps.append(ToolCall(tool="review_status", arguments={}, purpose="Verify status of connecting relationships"))

        else:  # MIXED_INVESTIGATION or default
            cid = scope.crime_id or "1042"
            steps.append(ToolCall(tool="crime_detail", arguments={"crime_id": cid}, purpose="Retrieve anchor case details"))
            steps.append(ToolCall(tool="graph_connections", arguments={"crime_id": cid, "max_hops": 2}, purpose="Traverse knowledge graph for connections"))
            steps.append(ToolCall(tool="phone_connections", arguments={"crime_id": cid}, purpose="Identify phone linkages"))
            steps.append(ToolCall(tool="cross_case_analysis", arguments={"crime_id": cid}, purpose="Identify cross-case connections"))
            steps.append(ToolCall(tool="key_individual_analysis", arguments={"scope_crime_id": cid, "limit": 5}, purpose="Identify structurally central people"))
            steps.append(ToolCall(tool="review_status", arguments={"crime_id": cid}, purpose="Verify investigator validation states"))

        return InvestigationPlan(
            goal=f"Investigate question: {question[:120]}",
            category=category,
            scope=scope,
            steps=steps,
            rationale="Deterministic domain investigation plan generated based on query classification and entity scope."
        )

    @classmethod
    async def create_plan(cls, question: str, user_scope: Optional[Dict[str, Any]] = None) -> InvestigationPlan:
        """
        Creates an investigation plan. Attempts LLM generation first, falling back to deterministic plan.
        """
        scope = cls.extract_scope_heuristics(question)
        if user_scope:
            if user_scope.get("crime_id"):
                scope.crime_id = user_scope["crime_id"]
            if user_scope.get("phone_number"):
                scope.phone_number = user_scope["phone_number"]
            if user_scope.get("max_hops"):
                scope.max_hops = min(int(user_scope["max_hops"]), 3)

        category = cls.classify_question(question)
        llm = get_llm_provider()

        # If LLM is Mock or offline, use deterministic domain planner
        from app.services.llm.mock_provider import MockLLMProvider
        if isinstance(llm, MockLLMProvider):
            return cls.deterministic_plan(question, scope, category)

        try:
            prompt = f"User Investigation Question:\n{question}\n\nExtracted Scope:\n{scope.model_dump_json()}"
            raw_response = await llm.generate(prompt=prompt, system_prompt=AGENT_PLANNER_SYSTEM_PROMPT)

            # Strip markdown fences if present
            clean_json = raw_response.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```(?:json)?\n?", "", clean_json)
                clean_json = re.sub(r"\n?```$", "", clean_json)

            data = json.loads(clean_json.strip())

            # Validate tools against allowlist
            validated_steps = []
            for step_data in data.get("steps", []):
                t_name = step_data.get("tool", "").strip().lower()
                if ToolRegistry.is_tool_allowed(t_name):
                    try:
                        valid_args = ToolRegistry.validate_tool_arguments(t_name, step_data.get("arguments", {}))
                        validated_steps.append(ToolCall(
                            tool=t_name,
                            arguments=valid_args,
                            purpose=step_data.get("purpose", "")
                        ))
                    except Exception as val_err:
                        logger.warning(f"Skipping invalid tool call {t_name}: {val_err}")

            if validated_steps:
                return InvestigationPlan(
                    goal=data.get("goal", question),
                    category=category,
                    scope=scope,
                    steps=validated_steps,
                    rationale=data.get("rationale", "LLM-generated plan with allowlist validation.")
                )

        except Exception as e:
            logger.warning(f"LLM planning failed ({e}), falling back to deterministic plan.")

        return cls.deterministic_plan(question, scope, category)
