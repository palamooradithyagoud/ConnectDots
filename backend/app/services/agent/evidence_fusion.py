"""
Phase 7: Domain AI Investigation Agent — Evidence Fusion & Normalization
Converts disparate tool outputs into normalized evidence records, enforces
investigator validation status, resolves conflicting hypotheses, and builds citation indices.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from app.services.agent.models import NormalizedEvidence
from app.services.agent.prompts import EVIDENCE_PASSIVE_WRAPPER

logger = logging.getLogger("connectdots_evidence_fusion")


class EvidenceFusionLayer:
    """
    Normalizes, deduplicates, and enforces validation status hierarchy on all evidence items.
    """

    @classmethod
    def deduplicate_evidence(cls, evidence_list: List[NormalizedEvidence]) -> List[NormalizedEvidence]:
        """
        Deduplicates evidence records while preserving the highest validation status.
        Priority: VALIDATED > UNDER_REVIEW > AI_DERIVED > REJECTED
        """
        status_rank = {
            "VALIDATED": 4,
            "MODIFIED": 3,
            "UNDER_REVIEW": 2,
            "AI_DERIVED": 1,
            "REJECTED": 0,
        }

        unique_map: Dict[str, NormalizedEvidence] = {}

        for item in evidence_list:
            key = f"{item.evidence_type}::{item.source_system}::{item.source_record_id or item.evidence_id}::{item.relationship or ''}::{item.target_entity or ''}"
            if key not in unique_map:
                unique_map[key] = item
            else:
                existing = unique_map[key]
                existing_rank = status_rank.get(existing.validation_status.upper(), 1)
                new_rank = status_rank.get(item.validation_status.upper(), 1)
                if new_rank > existing_rank:
                    unique_map[key] = item

        return list(unique_map.values())

    @classmethod
    def filter_active_evidence(
        cls, evidence_list: List[NormalizedEvidence]
    ) -> Tuple[List[NormalizedEvidence], List[NormalizedEvidence]]:
        """
        Separates evidence into active evidence (VALIDATED, AI_DERIVED, UNDER_REVIEW)
        and rejected evidence (REJECTED).
        Rejected evidence is returned separately so the agent can explain conflicts.
        """
        active: List[NormalizedEvidence] = []
        rejected: List[NormalizedEvidence] = []

        for item in evidence_list:
            if item.validation_status.upper() == "REJECTED":
                rejected.append(item)
            else:
                active.append(item)

        return active, rejected

    @classmethod
    def detect_conflicts(
        cls, active_evidence: List[NormalizedEvidence], rejected_evidence: List[NormalizedEvidence]
    ) -> List[str]:
        """
        Detects conflicts between AI hypotheses and investigator rejections.
        """
        conflicts: List[str] = []
        rejected_pairs: Set[Tuple[str, str]] = set()

        for r in rejected_evidence:
            if r.source_entity and r.target_entity:
                pair = tuple(sorted([r.source_entity, r.target_entity]))
                rejected_pairs.add(pair)

        for a in active_evidence:
            if a.source_entity and a.target_entity:
                pair = tuple(sorted([a.source_entity, a.target_entity]))
                if pair in rejected_pairs:
                    conflicts.append(
                        f"Relationship between '{a.source_entity}' and '{a.target_entity}' was proposed by AI "
                        f"but explicitly REJECTED by human investigator."
                    )

        return list(set(conflicts))

    @classmethod
    def format_evidence_for_synthesis(cls, active_evidence: List[NormalizedEvidence]) -> str:
        """
        Formats normalized evidence records inside the secure passive evidence wrapper for LLM consumption.
        """
        lines: List[str] = []
        for i, ev in enumerate(active_evidence, start=1):
            val_label = ev.validation_status.upper()
            if val_label == "VALIDATED":
                status_desc = "INVESTIGATOR-VALIDATED (CONFIRMED)"
            elif val_label in ("AI_DERIVED", "UNDER_REVIEW"):
                status_desc = "AI-DERIVED (HYPOTHESIS - PENDING REVIEW)"
            else:
                status_desc = val_label

            lines.append(f"[{ev.citation}] Type: {ev.evidence_type} | Source: {ev.source_system} | Status: {status_desc}")
            lines.append(f"Summary: {ev.summary}")
            if ev.relationship:
                lines.append(f"Relation: {ev.source_entity or 'N/A'} -> {ev.relationship} -> {ev.target_entity or 'N/A'}")
            lines.append("---")

        raw_block = "\n".join(lines) if lines else "No evidence retrieved."
        return EVIDENCE_PASSIVE_WRAPPER.format(evidence_content=raw_block)
