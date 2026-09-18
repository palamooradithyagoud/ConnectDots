"""
Phase 4: Deterministic Mock LLM Provider
Used in testing environments and offline development.
Parses the structured evidence block and synthesizes an evidence-grounded response.
"""
import json
import re
import logging
from typing import Dict, Any, List

from app.services.llm.base import LLMProvider

logger = logging.getLogger("connectdots_mock_llm")


class MockLLMProvider(LLMProvider):
    """
    Synthesizes predictable, grounded responses from structured evidence without external API calls.
    """

    async def generate(self, prompt: str, system_prompt: str) -> str:
        """
        Parses evidence from prompt and builds structured sections.
        """
        evidence_data: Dict[str, Any] = {}
        # Attempt to extract JSON from ```json ... ``` block
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", prompt, re.DOTALL)
        if json_match:
            try:
                evidence_data = json.loads(json_match.group(1))
            except Exception:
                pass

        primary_crime = evidence_data.get("primary_crime", {})
        similar_crimes = evidence_data.get("similar_crimes", [])
        graph_connections = evidence_data.get("graph_connections", [])
        supporting_patterns = evidence_data.get("supporting_patterns", [])
        question = evidence_data.get("question", "Crime Investigation Query")

        # Handle empty/insufficient evidence case
        if not primary_crime and not similar_crimes and not graph_connections:
            return (
                "### Summary\n"
                "Insufficient evidence available in the current records to address this query.\n\n"
                "### Connections\n"
                "• No verified graph connections or incident overlaps were discovered in the dataset.\n\n"
                "### Evidence\n"
                "None cited.\n\n"
                "### Uncertainty\n"
                "The available crime records do not contain matching incident IDs or statistical clusters."
            )

        # 1. Summary
        p_id = primary_crime.get("id") or primary_crime.get("record_id", "Primary Incident")
        p_cat = primary_crime.get("category", "Unspecified Category")
        p_loc = primary_crime.get("location_name", "Reported Location")

        related_ids = [c.get("crime_id") or c.get("id") for c in similar_crimes if c.get("crime_id") or c.get("id")]
        related_count = len(related_ids)

        summary_lines = [
            f"Investigation analysis for incident **{p_id}** ({p_cat} at {p_loc}).",
            f"Cross-database evidence fusion identified {related_count} semantically and relationally connected incident(s): {', '.join(related_ids[:4]) if related_ids else 'none'}."
        ]

        # 2. Connections
        conn_lines = []
        explicit_found = False
        derived_found = False

        for conn in graph_connections:
            rel = conn.get("relationship", "CONNECTED")
            c_type = conn.get("confidence_type", "derived")
            conf = conn.get("confidence", 1.0)
            other = conn.get("to") or conn.get("crime_id") or "Incident"
            inter = conn.get("intermediate_entity")

            if c_type == "explicit":
                explicit_found = True
                conn_lines.append(f"• **[Explicit Fact]** {p_id} exhibited relationship `{rel}` with {other} (Source: NLP incident extraction).")
            else:
                derived_found = True
                inter_str = f" via entity '{inter}'" if inter else ""
                conn_lines.append(f"• **[Derived Connection]** `{rel}` between {p_id} and {other}{inter_str} (Confidence: {conf:.2f}).")

        for sim in similar_crimes:
            sim_id = sim.get("crime_id")
            score = sim.get("similarity", 0.0)
            sim_cat = sim.get("category", "")
            conn_lines.append(f"• **[Semantic Similarity]** High narrative vector correlation with {sim_id} ({sim_cat}) at {score:.2f} cosine similarity.")

        for pat in supporting_patterns:
            pat_desc = pat.get("description") if isinstance(pat, dict) else str(pat)
            conn_lines.append(f"• **[ML Pattern]** Supported by Phase 3 pattern: {pat_desc}")

        if not conn_lines:
            conn_lines.append("• High categorical and geographical alignment based on PostGIS spatial proximity.")

        # 3. Evidence
        evidence_citations = set()
        if p_id:
            evidence_citations.add(p_id)
        for c in related_ids:
            evidence_citations.add(c)
        for pat in supporting_patterns:
            pid = pat.get("id") if isinstance(pat, dict) else str(pat)
            evidence_citations.add(f"PATTERN-{pid}")

        evidence_lines = [f"• {item}" for item in sorted(list(evidence_citations))]

        # 4. Uncertainty
        uncertainty_lines = [
            "• Analytical connections in the Knowledge Graph are derived from reported patterns and similarity models; they do not establish legal proof of common perpetrator identity or coordination.",
            "• Modus Operandi and vehicle overlaps reflect analytical correlation within available reports."
        ]

        return (
            f"### Summary\n{' '.join(summary_lines)}\n\n"
            f"### Connections\n{chr(10).join(conn_lines)}\n\n"
            f"### Evidence\n{chr(10).join(evidence_lines)}\n\n"
            f"### Uncertainty\n{chr(10).join(uncertainty_lines)}"
        )
