"use client";

import React, { useState } from "react";
import {
  FileCheck,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ExternalLink,
  History,
  CheckCircle2,
  XCircle,
  Filter,
  Layers,
  Sparkles,
  Info,
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";

const STATUS_FILTERS = ["ALL", "VALIDATED", "AI_DERIVED", "UNDER_REVIEW", "REJECTED"];

export default function EvidenceWorkspace() {
  const {
    activeAgentResult,
    caseContext,
    selectedEvidence,
    selectEvidence,
    openAuditHistory,
    refreshWorkspace,
  } = useInvestigation();

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const [activeFilter, setActiveFilter] = useState<string>("ALL");
  const [rejectModalOpen, setRejectModalOpen] = useState<boolean>(false);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>("INSUFFICIENT_CORROBORATION");
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  // Consolidate evidence from Agent and Case Context
  const allEvidence = React.useMemo(() => {
    const list = [...(activeAgentResult?.evidence || [])];

    // Add case FIR narrative evidence if available
    if (caseContext) {
      list.push({
        evidence_id: `FIR-${caseContext.record_id}`,
        evidence_type: "POLICE_FIR",
        source_system: "POSTGRESQL",
        source_record_id: caseContext.case_id,
        source_entity: `Case ${caseContext.record_id}`,
        relationship: "PRIMARY_INCIDENT",
        summary: caseContext.description || `FIR Incident record for Case ${caseContext.record_id}`,
        confidence: 1.0,
        validation_status: "VALIDATED",
        citation: `FIR-${caseContext.record_id}`,
        tool_used: "search_crime_records",
      });

      // Add connected cases as evidence
      caseContext.connected_cases.forEach((cc) => {
        list.push({
          evidence_id: `LINK-${caseContext.record_id}-${cc.record_id}`,
          evidence_type: "CROSS_CASE_LINK",
          source_system: "TELECOM",
          source_record_id: cc.crime_id,
          source_entity: `Case ${caseContext.record_id}`,
          target_entity: `Case ${cc.record_id}`,
          relationship: cc.connection_type,
          summary: cc.evidence,
          confidence: cc.confidence,
          validation_status: "AI_DERIVED",
          citation: `LINK-${cc.record_id}`,
          tool_used: "cross_case_analysis",
        });
      });
    }

    return list;
  }, [activeAgentResult, caseContext]);

  const filteredEvidence = allEvidence.filter((ev) => {
    if (activeFilter === "ALL") return true;
    return ev.validation_status?.toUpperCase() === activeFilter;
  });

  const handleValidate = async (ev: any) => {
    setActionLoading(true);
    try {
      // Find or create review item for this relationship
      const res = await fetch(`${apiUrl}/reviews/${ev.evidence_id}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer_id: "inv-007", note: "Validated via Command Center" }),
      });
      if (res.ok) {
        await refreshWorkspace();
      }
    } catch (err) {
      console.warn("Could not validate evidence item:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectConfirm = async () => {
    if (!activeActionId) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${apiUrl}/reviews/${activeActionId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_id: "inv-007",
          reason: rejectionReason,
          note: "Rejected from Command Center Evidence Workspace.",
        }),
      });
      if (res.ok) {
        await refreshWorkspace();
      }
    } catch (err) {
      console.warn("Could not reject evidence item:", err);
    } finally {
      setActionLoading(false);
      setRejectModalOpen(false);
      setActiveActionId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const st = status.toUpperCase();
    if (st === "VALIDATED") {
      return (
        <span className="flex items-center gap-1 rounded bg-emerald-500/20 px-2 py-0.5 text-[0.65rem] font-bold text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="h-3 w-3" />
          VALIDATED FACT
        </span>
      );
    }
    if (st === "REJECTED") {
      return (
        <span className="flex items-center gap-1 rounded bg-rose-500/20 px-2 py-0.5 text-[0.65rem] font-bold text-rose-400 border border-rose-500/30">
          <XCircle className="h-3 w-3" />
          REJECTED LINK
        </span>
      );
    }
    if (st === "MODIFIED") {
      return (
        <span className="flex items-center gap-1 rounded bg-indigo-500/20 px-2 py-0.5 text-[0.65rem] font-bold text-indigo-400 border border-indigo-500/30">
          MODIFIED
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 rounded bg-cyan-500/20 px-2 py-0.5 text-[0.65rem] font-bold text-cyan-400 border border-cyan-500/30">
        AI HYPOTHESIS
      </span>
    );
  };

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-midnight/80 p-4 backdrop-blur-xl shadow-2xl text-xs font-mono h-[420px]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <FileCheck className="h-4 w-4 text-emerald-400" />
          <h3 className="font-bold uppercase tracking-wider text-white">Evidence & Validation Workspace</h3>
          <span className="rounded-full bg-white/10 px-2 py-0.5 text-[0.65rem] text-white/60">
            {filteredEvidence.length} items
          </span>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex flex-wrap gap-1">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setActiveFilter(s)}
              className={`rounded-lg px-2.5 py-1 text-[0.65rem] transition ${
                activeFilter === s
                  ? "bg-brand text-white font-bold"
                  : "bg-white/[0.04] text-white/60 hover:bg-white/[0.08] hover:text-white"
              }`}
            >
              {s.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Evidence Cards List */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
        {filteredEvidence.length > 0 ? (
          filteredEvidence.map((ev, idx) => {
            const isSelected = selectedEvidence?.evidence_id === ev.evidence_id;
            const isRejected = ev.validation_status?.toUpperCase() === "REJECTED";

            return (
              <div
                key={ev.evidence_id || idx}
                onClick={() => selectEvidence(ev)}
                className={`flex flex-col gap-2 rounded-xl border p-3 transition cursor-pointer ${
                  isSelected
                    ? "border-brand bg-brand/10 shadow-lg shadow-brand/10"
                    : isRejected
                    ? "border-rose-500/20 bg-rose-950/10 opacity-70"
                    : "border-white/5 bg-white/[0.02] hover:bg-white/[0.05]"
                }`}
              >
                {/* Top Badge Row */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-brand-accent">[{ev.citation || ev.evidence_id}]</span>
                    <span className="rounded bg-black/40 px-1.5 py-0.5 text-[0.6rem] text-white/50">
                      {ev.evidence_type}
                    </span>
                    <span className="text-[0.6rem] text-white/30">via {ev.source_system}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {getStatusBadge(ev.validation_status)}
                    <span className="text-[0.65rem] text-white/40">
                      {Math.round(ev.confidence * 100)}% conf
                    </span>
                  </div>
                </div>

                {/* Evidence Narrative */}
                <p className="text-[0.72rem] text-white/80 leading-relaxed">{ev.summary}</p>

                {/* Entity Relationship Tag */}
                {ev.source_entity && (
                  <div className="flex items-center gap-2 text-[0.65rem] text-white/50 border-t border-white/5 pt-1.5">
                    <span className="font-bold text-white/70">{ev.source_entity}</span>
                    {ev.relationship && (
                      <span className="rounded bg-brand/10 px-1 text-brand-accent font-semibold">
                        {ev.relationship}
                      </span>
                    )}
                    {ev.target_entity && (
                      <span className="font-bold text-white/70">{ev.target_entity}</span>
                    )}
                  </div>
                )}

                {/* Action Toolbar */}
                <div className="flex items-center justify-between border-t border-white/5 pt-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openAuditHistory(ev.evidence_id);
                    }}
                    className="flex items-center gap-1 text-[0.65rem] text-white/40 hover:text-white transition"
                  >
                    <History className="h-3 w-3" />
                    <span>Audit Trail</span>
                  </button>

                  {!isRejected && (
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleValidate(ev);
                        }}
                        disabled={actionLoading}
                        className="rounded bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[0.65rem] font-bold text-emerald-400 hover:bg-emerald-500/20 transition"
                      >
                        Validate
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveActionId(ev.evidence_id);
                          setRejectModalOpen(true);
                        }}
                        disabled={actionLoading}
                        className="rounded bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 text-[0.65rem] font-bold text-rose-400 hover:bg-rose-500/20 transition"
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="flex h-32 flex-col items-center justify-center text-center text-white/40">
            <Info className="h-6 w-6 text-white/20 mb-1" />
            <p>No evidence items matching current validation filter.</p>
          </div>
        )}
      </div>

      {/* Reject Reason Modal */}
      {rejectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-md">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-midnight p-5 shadow-2xl">
            <div className="flex items-center gap-2 text-rose-400 mb-2">
              <ShieldAlert className="h-5 w-5" />
              <h3 className="font-bold text-sm">Reject Evidence Relationship</h3>
            </div>
            <p className="text-xs text-white/60 mb-4">
              Rejected relationships are immediately suppressed from active findings and flagged in the permanent audit trail.
            </p>

            <label className="block text-xs font-bold text-white/70 mb-1">Reason for Rejection</label>
            <select
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/50 p-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-rose-500 mb-4"
            >
              <option value="INSUFFICIENT_CORROBORATION">Insufficient Corroboration</option>
              <option value="FALSE_NLP_CO_OCCURRENCE">False NLP Entity Co-occurrence</option>
              <option value="MISATTRIBUTED_SUBSCRIBER">Misattributed Subscriber / Non-Criminal Contact</option>
              <option value="CONTRADICTED_BY_ALIBI">Contradicted by Verified Field Alibi</option>
              <option value="DUPLICATE_INCIDENT_MERGE">Duplicate Incident Merge</option>
            </select>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setRejectModalOpen(false)}
                className="rounded-xl px-4 py-2 text-xs font-bold text-white/60 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectConfirm}
                className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white hover:bg-rose-500 shadow-lg shadow-rose-600/30"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
