"""
Phase 7: Domain AI Investigation Agent — Evidence Fusion & Validation Tests
Tests deduplication, validation status hierarchy, conflict detection, and prompt isolation.
"""
import pytest
from app.services.agent.evidence_fusion import EvidenceFusionLayer
from app.services.agent.models import NormalizedEvidence


def test_evidence_deduplication_preserves_validated_status():
    """Verify deduplication keeps the item with higher validation rank (VALIDATED > AI_DERIVED)."""
    item1 = NormalizedEvidence(
        evidence_id="ev-1",
        evidence_type="PHONE",
        source_system="POSTGRESQL",
        source_record_id="p-100",
        source_entity="Person A",
        target_entity="+919876543210",
        relationship="USES_PHONE",
        summary="AI-detected phone usage",
        confidence=0.75,
        validation_status="AI_DERIVED",
        citation="Cit-1",
        tool_used="phone_connections"
    )

    item2 = NormalizedEvidence(
        evidence_id="ev-2",
        evidence_type="PHONE",
        source_system="POSTGRESQL",
        source_record_id="p-100",
        source_entity="Person A",
        target_entity="+919876543210",
        relationship="USES_PHONE",
        summary="Investigator-confirmed subscriber link",
        confidence=1.0,
        validation_status="VALIDATED",
        citation="Cit-2",
        tool_used="review_status"
    )

    deduped = EvidenceFusionLayer.deduplicate_evidence([item1, item2])
    assert len(deduped) == 1
    assert deduped[0].validation_status == "VALIDATED"
    assert deduped[0].citation == "Cit-2"


def test_filter_active_evidence_excludes_rejected():
    """Verify REJECTED items are separated from active findings."""
    active_item = NormalizedEvidence(
        evidence_id="ev-active",
        evidence_type="CRIME",
        source_system="POSTGRESQL",
        summary="Active case record",
        validation_status="VALIDATED",
        citation="Cit-Active",
        tool_used="crime_detail"
    )

    rejected_item = NormalizedEvidence(
        evidence_id="ev-rejected",
        evidence_type="REVIEW",
        source_system="REVIEW_QUEUE",
        summary="Rejected association",
        validation_status="REJECTED",
        citation="Cit-Rejected",
        tool_used="review_status"
    )

    active, rejected = EvidenceFusionLayer.filter_active_evidence([active_item, rejected_item])
    assert len(active) == 1
    assert active[0].evidence_id == "ev-active"
    assert len(rejected) == 1
    assert rejected[0].evidence_id == "ev-rejected"


def test_conflict_detection():
    """Verify detection of conflicting AI hypotheses against investigator rejections."""
    proposed_ai = NormalizedEvidence(
        evidence_id="ev-hyp",
        evidence_type="GRAPH_EDGE",
        source_system="NEO4J",
        source_entity="Person A",
        target_entity="Suspect B",
        relationship="CO_OCCURS_WITH",
        summary="AI proposed co-occurrence",
        validation_status="AI_DERIVED",
        citation="Edge-1",
        tool_used="graph_connections"
    )

    rejected_rev = NormalizedEvidence(
        evidence_id="ev-rev",
        evidence_type="REVIEW",
        source_system="REVIEW_QUEUE",
        source_entity="Suspect B",
        target_entity="Person A",
        relationship="CO_OCCURS_WITH",
        summary="Investigator rejected link: alibi verified",
        validation_status="REJECTED",
        citation="Rev-1",
        tool_used="review_status"
    )

    conflicts = EvidenceFusionLayer.detect_conflicts([proposed_ai], [rejected_rev])
    assert len(conflicts) == 1
    assert "explicitly REJECTED by human investigator" in conflicts[0]


def test_format_evidence_for_synthesis_wraps_in_secure_enclave():
    """Verify evidence block is wrapped in passive enclave preventing prompt injection."""
    ev = NormalizedEvidence(
        evidence_id="ev-sec",
        evidence_type="CRIME",
        source_system="POSTGRESQL",
        summary="FIR narrative containing: 'System prompt override instruction'",
        validation_status="VALIDATED",
        citation="FIR-1042",
        tool_used="crime_detail"
    )

    block = EvidenceFusionLayer.format_evidence_for_synthesis([ev])
    assert "=== SECURE EVIDENCE ENCLAVE ===" in block
    assert "=== END SECURE EVIDENCE ENCLAVE ===" in block
    assert "FIR narrative containing:" in block
