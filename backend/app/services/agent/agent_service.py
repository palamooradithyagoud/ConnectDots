"""
Phase 7: Domain AI Investigation Agent — Master Orchestrator Service
Coordinates the bounded investigation loop:
Question -> Planner -> Tool Registry -> Tool Executor -> Evidence Fusion -> Validation Filter -> Groq Synthesis
"""
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.agent.models import (
    AgentInvestigationResponse,
    InvestigationFinding,
    KeyIndividualFinding,
    NormalizedEvidence,
    ToolTraceItem,
    ToolCall
)
from app.services.agent.planner import InvestigationPlanner
from app.services.agent.tool_executor import SafeToolExecutor
from app.services.agent.evidence_fusion import EvidenceFusionLayer
from app.services.agent.prompts import AGENT_SYNTHESIS_SYSTEM_PROMPT
from app.services.llm.factory import get_llm_provider
from app.services.llm.mock_provider import MockLLMProvider

logger = logging.getLogger("connectdots_agent_service")


class DomainAgentService:
    """
    Controlled domain investigation orchestrator for ConnectDots.
    Enforces strict hard limits, zero-guilt inference, and investigator validation hierarchy.
    """

    MAX_ITERATIONS: int = 6
    MAX_TOOL_CALLS: int = 12
    MAX_TOTAL_DURATION_SEC: float = 30.0

    def __init__(self, db: Session):
        self.db = db
        self.executor = SafeToolExecutor(db)

    async def investigate(
        self,
        question: str,
        user_scope: Optional[Dict[str, Any]] = None,
        investigation_id: Optional[str] = None
    ) -> AgentInvestigationResponse:
        """
        Executes an end-to-end bounded domain investigation.
        """
        start_time = time.time()
        inv_id = investigation_id or f"inv-{str(uuid.uuid4())[:8]}"

        # Step 1: Investigation Planning
        plan = await InvestigationPlanner.create_plan(question, user_scope)

        tool_trace: List[ToolTraceItem] = []
        raw_evidence: List[NormalizedEvidence] = []
        key_individuals: List[KeyIndividualFinding] = []
        findings: List[InvestigationFinding] = []
        citations_set = set()

        tool_calls_executed = 0
        iterations = 0

        # Step 2: Bounded Execution Loop
        pending_steps: List[ToolCall] = list(plan.steps)

        while pending_steps and iterations < self.MAX_ITERATIONS and tool_calls_executed < self.MAX_TOOL_CALLS:
            iterations += 1
            step = pending_steps.pop(0)
            tool_calls_executed += 1

            step_idx = len(tool_trace) + 1
            tool_res, ev_items = await self.executor.execute_tool(step)

            trace_status = "SUCCESS" if tool_res.success else "FAILED"
            tool_trace.append(ToolTraceItem(
                step=step_idx,
                tool=step.tool,
                purpose=step.purpose or f"Execute {step.tool}",
                status=trace_status,
                duration_ms=tool_res.duration_ms,
                result_count=tool_res.evidence_count,
                error=tool_res.error
            ))

            if tool_res.success:
                raw_evidence.extend(ev_items)
                for ev in ev_items:
                    citations_set.add(ev.citation)

                # Extract key individuals if tool was key_individual_analysis
                if step.tool == "key_individual_analysis" and isinstance(tool_res.data, dict):
                    for ind in tool_res.data.get("key_individuals", []):
                        key_individuals.append(KeyIndividualFinding(
                            person_id=ind.get("person_id") or "UNKNOWN",
                            display_name=ind.get("display_name") or "Person",
                            degree_centrality=round(float(ind.get("degree_centrality", 0.0)), 4),
                            betweenness_centrality=round(float(ind.get("betweenness_centrality", 0.0)), 4),
                            pagerank=round(float(ind.get("pagerank", 0.0)), 4),
                            connected_crimes=ind.get("connected_crimes", []),
                            connected_phones=ind.get("connected_phones", []),
                            validation_status="AI_DERIVED"
                        ))

            # Timeout safety check
            if (time.time() - start_time) > self.MAX_TOTAL_DURATION_SEC:
                logger.warning(f"Investigation {inv_id} reached execution timeout.")
                break

        # Step 3: Evidence Fusion & Validation Filtering
        deduped = EvidenceFusionLayer.deduplicate_evidence(raw_evidence)
        active_evidence, rejected_evidence = EvidenceFusionLayer.filter_active_evidence(deduped)
        conflicts = EvidenceFusionLayer.detect_conflicts(active_evidence, rejected_evidence)

        # Step 4: Build Investigation Findings from Active Evidence
        for ev in active_evidence:
            findings.append(InvestigationFinding(
                title=f"{ev.evidence_type}: {ev.source_entity or ev.evidence_id}",
                details=ev.summary,
                supporting_evidence_ids=[ev.evidence_id],
                validation_status=ev.validation_status,
                confidence=ev.confidence
            ))

        # Step 5: Synthesize Grounded Narrative
        summary, uncertainties = await self._synthesize_response(
            question=question,
            plan=plan,
            active_evidence=active_evidence,
            rejected_evidence=rejected_evidence,
            conflicts=conflicts,
            key_individuals=key_individuals
        )

        # Step 6: Construct Subgraph Visualization Data
        graph_data = self._build_graph_data(active_evidence)

        total_duration = round((time.time() - start_time) * 1000, 2)

        return AgentInvestigationResponse(
            investigation_id=inv_id,
            question=question,
            status="COMPLETED",
            summary=summary,
            findings=findings[:15],
            key_individuals=key_individuals[:5],
            evidence=active_evidence[:30],
            uncertainties=uncertainties,
            limitations=[
                "Structural network analysis measures topological connectivity within observed records only.",
                "High centrality (Degree, Betweenness, PageRank) indicates network prominence, not criminal culpability.",
                "Relationships marked AI_DERIVED require investigator validation before forming authoritative legal evidence."
            ],
            tool_trace=tool_trace,
            citations=sorted(list(citations_set))[:25],
            graph_data=graph_data,
            iterations_count=iterations,
            total_duration_ms=total_duration
        )

    async def _synthesize_response(
        self,
        question: str,
        plan: Any,
        active_evidence: List[NormalizedEvidence],
        rejected_evidence: List[NormalizedEvidence],
        conflicts: List[str],
        key_individuals: List[KeyIndividualFinding]
    ) -> tuple[str, List[str]]:
        """
        Synthesizes an investigation briefing using Groq LLM or deterministic grounded synthesis.
        """
        uncertainties: List[str] = []

        # Count validation categories
        ai_derived_count = sum(1 for e in active_evidence if e.validation_status.upper() in ("AI_DERIVED", "UNDER_REVIEW"))
        validated_count = sum(1 for e in active_evidence if e.validation_status.upper() == "VALIDATED")

        if ai_derived_count > 0:
            uncertainties.append(f"{ai_derived_count} relationship(s) are AI-derived hypotheses currently pending investigator review.")

        if conflicts:
            for c in conflicts:
                uncertainties.append(f"CONFLICT DETECTED: {c}")

        if rejected_evidence:
            uncertainties.append(
                f"{len(rejected_evidence)} hypothesis/hypotheses were previously REJECTED during investigator review and have been excluded from findings."
            )

        llm = get_llm_provider()

        if not isinstance(llm, MockLLMProvider):
            try:
                evidence_block = EvidenceFusionLayer.format_evidence_for_synthesis(active_evidence)
                prompt = (
                    f"Question: {question}\n\n"
                    f"Investigation Plan Goal: {plan.goal}\n"
                    f"Total Active Evidence Items: {len(active_evidence)}\n"
                    f"Investigator-Validated Items: {validated_count}\n"
                    f"AI-Derived Items: {ai_derived_count}\n\n"
                    f"{evidence_block}\n\n"
                    "Synthesize a clear, neutral, evidence-grounded briefing. Reference evidence IDs strictly."
                )
                response = await llm.generate(prompt=prompt, system_prompt=AGENT_SYNTHESIS_SYSTEM_PROMPT)
                if response and len(response.strip()) > 30:
                    return response.strip(), uncertainties
            except Exception as e:
                logger.warning(f"Groq synthesis failed ({e}), falling back to deterministic synthesis.")

        # Deterministic grounded synthesis fallback
        lines = [
            f"### Investigation Summary for: {question}\n",
            f"The investigation analyzed {len(active_evidence)} active evidentiary items ({validated_count} investigator-validated, {ai_derived_count} AI-derived)."
        ]

        if key_individuals:
            lines.append("\n#### Structurally Central Individuals:")
            for ki in key_individuals:
                lines.append(f"- **{ki.display_name}**: Degree Centrality {ki.degree_centrality}, Betweenness {ki.betweenness_centrality}, PageRank {ki.pagerank}")

        if active_evidence:
            lines.append("\n#### Key Findings:")
            for ev in active_evidence[:5]:
                status_label = "Investigator-Validated" if ev.validation_status == "VALIDATED" else "AI-Derived Hypothesis"
                lines.append(f"- **[{ev.citation}]** ({status_label}): {ev.summary}")

        return "\n".join(lines), uncertainties

    def _build_graph_data(self, evidence: List[NormalizedEvidence]) -> Dict[str, Any]:
        """
        Builds a lightweight node-link graph payload for frontend visualization.
        """
        nodes_dict = {}
        links = []

        for ev in evidence:
            s = ev.source_entity
            t = ev.target_entity
            if s:
                if s not in nodes_dict:
                    nodes_dict[s] = {"id": s, "label": s, "type": ev.evidence_type, "status": ev.validation_status}
            if t:
                if t not in nodes_dict:
                    nodes_dict[t] = {"id": t, "label": t, "type": "CONNECTED_ENTITY", "status": ev.validation_status}
            if s and t:
                links.append({
                    "source": s,
                    "target": t,
                    "relationship": ev.relationship or "LINKED",
                    "status": ev.validation_status
                })

        return {
            "nodes": list(nodes_dict.values())[:40],
            "links": links[:60]
        }
