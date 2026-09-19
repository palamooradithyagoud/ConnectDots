"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Edit3,
  RotateCcw,
  MessageSquare,
  FileText,
  PhoneCall,
  Users,
  Search,
  Filter,
  RefreshCw,
  Info,
  Clock,
  Sparkles,
  ChevronRight,
  Shield,
  Layers,
  ArrowRight
} from "lucide-react";
import {
  ReviewItem,
  ReviewDetail,
  ReviewHistoryItem,
  ReviewStats,
  ReviewStatus
} from "@/types/investigation";

interface InvestigatorReviewQueueProps {
  onFocusGraph?: (sourceId: string, targetId: string) => void;
}

export default function InvestigatorReviewQueue({ onFocusGraph }: InvestigatorReviewQueueProps) {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [conflictError, setConflictError] = useState<string | null>(null);

  // Filters
  const [selectedStatus, setSelectedStatus] = useState<string>("PENDING");
  const [selectedRelType, setSelectedRelType] = useState<string>("ALL");
  const [minConfidence, setMinConfidence] = useState<number>(0.0);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);

  // Selected Detail Modal / Drawer
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);
  const [reviewDetail, setReviewDetail] = useState<ReviewDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  // Action Dialog States
  const [actionModal, setActionModal] = useState<"validate" | "reject" | "modify" | "note" | null>(null);
  const [actionNote, setActionNote] = useState<string>("");
  const [rejectReason, setRejectReason] = useState<string>("Coincidental overlap");
  const [newRelType, setNewRelType] = useState<string>("CO_OCCURS_WITH");
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  // Whitelist of supported relationship types
  const [supportedTypes, setSupportedTypes] = useState<string[]>([
    "CO_OCCURS_WITH",
    "ASSOCIATED_WITH",
    "AFFILIATED_WITH",
    "SHARES_PHONE",
    "SHARES_VEHICLE",
    "SHARES_WEAPON",
    "SHARES_MO",
    "SAME_LOCATION",
    "SAME_CLUSTER",
    "COMMUNICATION_LINKED",
    "INVOLVED_IN",
    "MENTIONS_PERSON",
    "USES_PHONE"
  ]);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // 1. Fetch Review Stats
  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/reviews/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.warn("Could not fetch review stats:", err);
    }
  }, [apiUrl]);

  // 2. Fetch Review Items
  const fetchReviews = useCallback(async () => {
    setLoading(true);
    setError(null);
    setConflictError(null);
    try {
      const params = new URLSearchParams();
      if (selectedStatus !== "ALL") params.append("status", selectedStatus);
      if (selectedRelType !== "ALL") params.append("relationship_type", selectedRelType);
      if (minConfidence > 0) params.append("min_confidence", minConfidence.toString());
      if (searchQuery.trim()) params.append("search", searchQuery.trim());
      params.append("page", page.toString());
      params.append("page_size", "15");

      const res = await fetch(`${apiUrl}/reviews?${params.toString()}`);
      if (!res.ok) throw new Error(`Failed to load reviews (${res.status})`);
      const data = await res.json();
      setReviews(data.items || []);
      setTotalPages(data.total_pages || 1);
    } catch (err: any) {
      setError(err.message || "Could not retrieve review queue.");
    } finally {
      setLoading(false);
    }
  }, [apiUrl, selectedStatus, selectedRelType, minConfidence, searchQuery, page]);

  useEffect(() => {
    fetchStats();
    fetchReviews();
  }, [fetchStats, fetchReviews]);

  // 3. Fetch Supported Types once
  useEffect(() => {
    async function loadTypes() {
      try {
        const res = await fetch(`${apiUrl}/reviews/supported-types`);
        if (res.ok) {
          const data = await res.json();
          if (data.supported_types) setSupportedTypes(data.supported_types);
        }
      } catch (err) {
        console.warn("Could not fetch supported types:", err);
      }
    }
    loadTypes();
  }, [apiUrl]);

  // 4. Fetch Review Detail
  const fetchDetail = useCallback(async (id: string) => {
    setDetailLoading(true);
    setConflictError(null);
    try {
      const res = await fetch(`${apiUrl}/reviews/${encodeURIComponent(id)}`);
      if (res.ok) {
        const data = await res.json();
        setReviewDetail(data);
      }
    } catch (err) {
      console.warn("Could not load review detail:", err);
    } finally {
      setDetailLoading(false);
    }
  }, [apiUrl]);

  const handleOpenDetail = (id: string) => {
    setSelectedReviewId(id);
    fetchDetail(id);
  };

  // 5. Populate Queue from Graph
  const handlePopulateQueue = async () => {
    setSyncing(true);
    try {
      const res = await fetch(`${apiUrl}/reviews/populate`, { method: "POST" });
      if (res.ok) {
        await fetchStats();
        await fetchReviews();
      }
    } catch (err) {
      console.warn("Could not populate queue:", err);
    } finally {
      setSyncing(false);
    }
  };

  // 6. Action Handlers (Validate, Reject, Modify, Reopen, Note)
  const handleValidate = async () => {
    if (!reviewDetail) return;
    setActionLoading(true);
    setConflictError(null);
    try {
      const res = await fetch(`${apiUrl}/reviews/${reviewDetail.id}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_id: "investigator:lead",
          reviewer_display_name: "Lead Investigator",
          note: actionNote.trim() || undefined,
          expected_version: reviewDetail.version
        })
      });

      if (res.status === 409) {
        const data = await res.json();
        setConflictError(data.detail || "Review was modified by another investigator.");
        await fetchDetail(reviewDetail.id);
        return;
      }

      if (!res.ok) throw new Error("Validation action failed.");
      const updated = await res.json();
      setReviewDetail(updated);
      setActionModal(null);
      setActionNote("");
      await fetchStats();
      await fetchReviews();
    } catch (err: any) {
      setError(err.message || "Failed to validate relationship.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!reviewDetail) return;
    setActionLoading(true);
    setConflictError(null);
    try {
      const res = await fetch(`${apiUrl}/reviews/${reviewDetail.id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_id: "investigator:lead",
          reviewer_display_name: "Lead Investigator",
          reason: rejectReason,
          note: actionNote.trim() || undefined,
          expected_version: reviewDetail.version
        })
      });

      if (res.status === 409) {
        const data = await res.json();
        setConflictError(data.detail || "Review was modified by another investigator.");
        await fetchDetail(reviewDetail.id);
        return;
      }

      if (!res.ok) throw new Error("Rejection action failed.");
      const updated = await res.json();
      setReviewDetail(updated);
      setActionModal(null);
      setActionNote("");
      await fetchStats();
      await fetchReviews();
    } catch (err: any) {
      setError(err.message || "Failed to reject relationship.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleModify = async () => {
    if (!reviewDetail) return;
    setActionLoading(true);
    setConflictError(null);
    try {
      const res = await fetch(`${apiUrl}/reviews/${reviewDetail.id}/modify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          new_relationship_type: newRelType,
          reviewer_id: "investigator:lead",
          reviewer_display_name: "Lead Investigator",
          note: actionNote.trim() || undefined,
          expected_version: reviewDetail.version
        })
      });

      if (res.status === 409) {
        const data = await res.json();
        setConflictError(data.detail || "Review was modified by another investigator.");
        await fetchDetail(reviewDetail.id);
        return;
      }

      if (!res.ok) throw new Error("Modification action failed.");
      const updated = await res.json();
      setReviewDetail(updated);
      setActionModal(null);
      setActionNote("");
      await fetchStats();
      await fetchReviews();
    } catch (err: any) {
      setError(err.message || "Failed to modify relationship.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReopen = async () => {
    if (!reviewDetail) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${apiUrl}/reviews/${reviewDetail.id}/reopen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_id: "investigator:lead",
          reviewer_display_name: "Lead Investigator",
          reason: "Reopened for reassessment"
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setReviewDetail(updated);
        await fetchStats();
        await fetchReviews();
      }
    } catch (err) {
      console.warn("Could not reopen review:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddNote = async () => {
    if (!reviewDetail || !actionNote.trim()) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${apiUrl}/reviews/${reviewDetail.id}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_id: "investigator:lead",
          reviewer_display_name: "Lead Investigator",
          note: actionNote.trim()
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setReviewDetail(updated);
        setActionModal(null);
        setActionNote("");
        await fetchReviews();
      }
    } catch (err) {
      console.warn("Could not add note:", err);
    } finally {
      setActionLoading(false);
    }
  };

  // Helper badge renderers
  const getStatusBadge = (st: string) => {
    switch (st) {
      case "VALIDATED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
            <CheckCircle2 className="h-3 w-3" /> Validated
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-400 border border-rose-800/60">
            <XCircle className="h-3 w-3" /> Rejected
          </span>
        );
      case "MODIFIED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-950/80 text-indigo-400 border border-indigo-800/60">
            <Edit3 className="h-3 w-3" /> Modified
          </span>
        );
      case "UNDER_REVIEW":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
            <Clock className="h-3 w-3 animate-spin" /> In Review
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800/60">
            <AlertCircle className="h-3 w-3" /> Pending Review
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Principle Banner */}
      <div className="p-4 rounded-xl border border-indigo-500/20 bg-indigo-950/20 flex items-start justify-between gap-4 text-sm text-indigo-200">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-white">Human-in-the-Loop Governance Principle:</span>{" "}
            AI discoveries and graph inferences are investigative hypotheses, never self-authoritative facts.
            Investigators inspect grounded evidence (FIR excerpts, CDR logs, co-occurrences) to affirmatively
            validate, reject, or modify relationships. Every action is immutably audited.
          </div>
        </div>

        <button
          onClick={handlePopulateQueue}
          disabled={syncing}
          className="shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${syncing ? "animate-spin" : ""}`} />
          {syncing ? "Scanning Graph..." : "Scan & Seed AI Links"}
        </button>
      </div>

      {/* Summary Counters */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div
            onClick={() => setSelectedStatus("ALL")}
            className={`p-3.5 rounded-xl border cursor-pointer transition ${
              selectedStatus === "ALL"
                ? "bg-slate-800/90 border-indigo-500 ring-1 ring-indigo-500/40"
                : "bg-slate-900/60 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <div className="text-[11px] text-slate-400 font-medium">Total AI Links</div>
            <div className="text-xl font-bold text-white mt-0.5 font-mono">{stats.total}</div>
          </div>

          <div
            onClick={() => setSelectedStatus("PENDING")}
            className={`p-3.5 rounded-xl border cursor-pointer transition ${
              selectedStatus === "PENDING"
                ? "bg-amber-950/40 border-amber-500 ring-1 ring-amber-500/40"
                : "bg-slate-900/60 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <div className="text-[11px] text-amber-300 font-medium flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" /> Pending Review
            </div>
            <div className="text-xl font-bold text-amber-400 mt-0.5 font-mono">{stats.pending}</div>
          </div>

          <div
            onClick={() => setSelectedStatus("VALIDATED")}
            className={`p-3.5 rounded-xl border cursor-pointer transition ${
              selectedStatus === "VALIDATED"
                ? "bg-emerald-950/40 border-emerald-500 ring-1 ring-emerald-500/40"
                : "bg-slate-900/60 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <div className="text-[11px] text-emerald-300 font-medium flex items-center gap-1.5">
              <CheckCircle2 className="h-3 w-3" /> Validated
            </div>
            <div className="text-xl font-bold text-emerald-400 mt-0.5 font-mono">{stats.validated}</div>
          </div>

          <div
            onClick={() => setSelectedStatus("REJECTED")}
            className={`p-3.5 rounded-xl border cursor-pointer transition ${
              selectedStatus === "REJECTED"
                ? "bg-rose-950/40 border-rose-500 ring-1 ring-rose-500/40"
                : "bg-slate-900/60 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <div className="text-[11px] text-rose-300 font-medium flex items-center gap-1.5">
              <XCircle className="h-3 w-3" /> Rejected
            </div>
            <div className="text-xl font-bold text-rose-400 mt-0.5 font-mono">{stats.rejected}</div>
          </div>

          <div
            onClick={() => setSelectedStatus("MODIFIED")}
            className={`p-3.5 rounded-xl border cursor-pointer transition ${
              selectedStatus === "MODIFIED"
                ? "bg-indigo-950/40 border-indigo-500 ring-1 ring-indigo-500/40"
                : "bg-slate-900/60 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <div className="text-[11px] text-indigo-300 font-medium flex items-center gap-1.5">
              <Edit3 className="h-3 w-3" /> Modified
            </div>
            <div className="text-xl font-bold text-indigo-400 mt-0.5 font-mono">{stats.modified}</div>
          </div>
        </div>
      )}

      {/* Control / Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by entity or note..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono w-56"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={selectedRelType}
              onChange={(e) => {
                setSelectedRelType(e.target.value);
                setPage(1);
              }}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Relationship Types</option>
              {supportedTypes.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>Min Confidence:</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={minConfidence}
              onChange={(e) => {
                setMinConfidence(parseFloat(e.target.value));
                setPage(1);
              }}
              className="w-20 accent-indigo-500"
            />
            <span className="font-mono text-slate-300">{Math.round(minConfidence * 100)}%</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchReviews()}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh review items"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Main Review Queue Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-12 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" /> Loading investigator queue...
            </div>
          ) : error ? (
            <div className="p-8 text-center text-red-400 text-sm">{error}</div>
          ) : reviews.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-sm space-y-2">
              <ShieldCheck className="h-8 w-8 text-slate-600 mx-auto" />
              <div>No relationships matching the current filter.</div>
              <div className="text-xs text-slate-600">
                Click "Scan & Seed AI Links" to discover links from knowledge graph records.
              </div>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
                  <th className="p-3 font-medium">Source Entity</th>
                  <th className="p-3 font-medium text-center">Proposed Relationship</th>
                  <th className="p-3 font-medium">Target Entity</th>
                  <th className="p-3 font-medium text-center">Confidence</th>
                  <th className="p-3 font-medium text-center">Status</th>
                  <th className="p-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {reviews.map((rev) => (
                  <tr
                    key={rev.id}
                    className="hover:bg-slate-800/40 transition cursor-pointer"
                    onClick={() => handleOpenDetail(rev.id)}
                  >
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          {rev.source_entity_type}
                        </span>
                        <span className="font-semibold text-slate-200 font-mono">
                          {rev.source_entity_id.split(":").pop()}
                        </span>
                      </div>
                    </td>

                    <td className="p-3 text-center">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950 border border-slate-800">
                        <span className="font-bold text-indigo-300 font-mono text-[11px]">
                          {rev.relationship_type}
                        </span>
                        <span className="text-[9px] text-slate-500 uppercase px-1 rounded bg-slate-800/80">
                          {rev.provenance.replace("_DERIVED", "")}
                        </span>
                      </div>
                    </td>

                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          {rev.target_entity_type}
                        </span>
                        <span className="font-semibold text-slate-200 font-mono">
                          {rev.target_entity_id.split(":").pop()}
                        </span>
                      </div>
                    </td>

                    <td className="p-3 text-center font-mono">
                      <span className="text-amber-300 font-semibold">
                        {Math.round(rev.original_confidence * 100)}%
                      </span>
                    </td>

                    <td className="p-3 text-center">
                      {getStatusBadge(rev.status)}
                    </td>

                    <td className="p-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDetail(rev.id);
                        }}
                        className="px-3 py-1 rounded-md bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition"
                      >
                        Inspect & Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-3 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
            <span>Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Evidence Review Modal / Drawer */}
      {selectedReviewId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="relative w-full max-w-3xl max-h-[90vh] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-indigo-400" />
                <h3 className="font-bold text-white text-sm">Investigator Evidence Dossier</h3>
                {reviewDetail && getStatusBadge(reviewDetail.status)}
              </div>
              <button
                onClick={() => {
                  setSelectedReviewId(null);
                  setReviewDetail(null);
                  setActionModal(null);
                }}
                className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
              {detailLoading || !reviewDetail ? (
                <div className="p-12 text-center text-slate-400 flex items-center justify-center gap-2">
                  <RefreshCw className="h-4 w-4 animate-spin" /> Loading complete evidence package...
                </div>
              ) : (
                <>
                  {/* Concurrency Conflict Banner */}
                  {conflictError && (
                    <div className="p-3 rounded-lg border border-amber-500/40 bg-amber-950/30 text-amber-300 flex items-center gap-2 text-xs">
                      <AlertCircle className="h-4 w-4 shrink-0 text-amber-400" />
                      <span>{conflictError}</span>
                    </div>
                  )}

                  {/* Relationship Overview Card */}
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="text-center sm:text-left">
                        <div className="text-[10px] text-slate-500 uppercase">{reviewDetail.source_entity_type}</div>
                        <div className="font-bold text-white text-sm font-mono mt-0.5">
                          {reviewDetail.source_entity_id.split(":").pop()}
                        </div>
                      </div>

                      <div className="flex flex-col items-center px-4">
                        <span className="text-[10px] font-bold text-indigo-400 uppercase font-mono px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-800/40">
                          {reviewDetail.relationship_type}
                        </span>
                        <ArrowRight className="h-4 w-4 text-slate-600 mt-1" />
                      </div>

                      <div className="text-center sm:text-left">
                        <div className="text-[10px] text-slate-500 uppercase">{reviewDetail.target_entity_type}</div>
                        <div className="font-bold text-white text-sm font-mono mt-0.5">
                          {reviewDetail.target_entity_id.split(":").pop()}
                        </div>
                      </div>
                    </div>

                    <div className="text-right border-t sm:border-t-0 sm:border-l border-slate-800 pt-2 sm:pt-0 sm:pl-4">
                      <div className="text-[10px] text-slate-500 uppercase">AI Discovery Confidence</div>
                      <div className="text-base font-bold text-amber-400 font-mono">
                        {Math.round(reviewDetail.original_confidence * 100)}%
                      </div>
                      <div className="text-[9px] text-slate-500">{reviewDetail.discovery_method}</div>
                    </div>
                  </div>

                  {/* Supporting Evidence Snapshot */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-200 mb-2 flex items-center gap-1.5">
                      <FileText className="h-3.5 w-3.5 text-indigo-400" /> Corroborating Records & Evidence ({reviewDetail.evidence_snapshot.length})
                    </h4>
                    {reviewDetail.evidence_snapshot.length === 0 ? (
                      <div className="p-4 rounded-lg bg-slate-950/40 border border-slate-800 text-slate-500 italic">
                        No specific record snapshot attached. Proposed via topology co-occurrence.
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                        {reviewDetail.evidence_snapshot.map((ev, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-lg bg-slate-950/40 border border-slate-800 space-y-1"
                          >
                            <div className="flex items-center justify-between text-slate-300">
                              <span className="font-semibold text-white">
                                {ev.type || "Evidence"}: {ev.id || ev.number || ev.call_id || "Record"}
                              </span>
                              {ev.note && <span className="text-[10px] text-slate-400">{ev.note}</span>}
                            </div>
                            {ev.excerpt && (
                              <div className="text-[11px] text-slate-400 italic">"{ev.excerpt}"</div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Investigator Notes */}
                  {reviewDetail.investigator_note && (
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="font-semibold text-slate-200 mb-1 flex items-center gap-1.5">
                        <MessageSquare className="h-3.5 w-3.5 text-cyan-400" /> Investigator Notes
                      </div>
                      <div className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                        {reviewDetail.investigator_note}
                      </div>
                    </div>
                  )}

                  {/* Rejection Reason if applicable */}
                  {reviewDetail.rejection_reason && (
                    <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-800/40 text-rose-300">
                      <span className="font-semibold text-rose-200">Rejection Rationale:</span> {reviewDetail.rejection_reason}
                    </div>
                  )}

                  {/* Audit History Log */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-200 mb-2 flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-slate-400" /> Audit Trail ({reviewDetail.history_entries.length} events)
                    </h4>
                    <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
                      {reviewDetail.history_entries.map((h) => (
                        <div
                          key={h.id}
                          className="p-2 rounded-lg bg-slate-950/30 border border-slate-800 text-[11px] flex items-start justify-between gap-2"
                        >
                          <div>
                            <span className="font-bold text-slate-200 font-mono">[{h.action}]</span>{" "}
                            <span className="text-slate-400">by {h.reviewer_display_name || h.reviewer_id}</span>
                            {h.note && <div className="text-slate-500 italic mt-0.5">"{h.note}"</div>}
                            {h.reason && <div className="text-rose-400/80 mt-0.5">Reason: {h.reason}</div>}
                          </div>
                          <span className="text-[10px] text-slate-500 shrink-0">
                            {new Date(h.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Modal Actions Footer */}
            {reviewDetail && (
              <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setActionModal("note")}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition"
                  >
                    <MessageSquare className="h-3.5 w-3.5" /> Add Note
                  </button>

                  {reviewDetail.status !== "PENDING" && reviewDetail.status !== "UNDER_REVIEW" && (
                    <button
                      onClick={handleReopen}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs transition"
                    >
                      <RotateCcw className="h-3.5 w-3.5" /> Reopen Review
                    </button>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {reviewDetail.status !== "VALIDATED" && (
                    <button
                      onClick={() => setActionModal("validate")}
                      className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" /> Validate Link
                    </button>
                  )}

                  {reviewDetail.status !== "REJECTED" && (
                    <button
                      onClick={() => setActionModal("reject")}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 text-xs font-medium transition"
                    >
                      <XCircle className="h-3.5 w-3.5" /> Reject
                    </button>
                  )}

                  <button
                    onClick={() => setActionModal("modify")}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition"
                  >
                    <Edit3 className="h-3.5 w-3.5" /> Modify Type
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sub-Modal: Validate Confirmation */}
      {actionModal === "validate" && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/80">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-4 shadow-2xl">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Confirm Relationship Validation
            </h4>
            <p className="text-xs text-slate-300">
              You are certifying that the evidence supports this relationship. The link will be upgraded to
              investigator-validated evidence in the Knowledge Graph and Graph RAG.
            </p>
            <div>
              <label className="text-xs text-slate-400 font-medium">Investigator Corroboration Note (Optional):</label>
              <textarea
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                placeholder="e.g. Verified through CDR subscriber registration records..."
                className="w-full mt-1.5 p-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                rows={3}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setActionModal(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleValidate}
                disabled={actionLoading}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? "Validating..." : "Confirm Validation"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sub-Modal: Reject with Rationale */}
      {actionModal === "reject" && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/80">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-4 shadow-2xl">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <XCircle className="h-4 w-4 text-rose-400" /> Reject Proposed Relationship
            </h4>
            <p className="text-xs text-slate-300">
              The relationship will be marked as REJECTED in the Knowledge Graph and suppressed from active investigative queries.
              Original evidence will remain preserved for auditability.
            </p>
            <div>
              <label className="text-xs text-slate-400 font-medium">Rejection Rationale (Mandatory):</label>
              <select
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="w-full mt-1.5 p-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="Coincidental overlap">Coincidental overlap (no conspiratorial intent)</option>
                <option value="Shared public/burner phone">Shared public phone / non-exclusive number</option>
                <option value="False identity resolution match">False identity resolution match</option>
                <option value="Insufficient evidence to substantiate">Insufficient evidence to substantiate</option>
                <option value="Contradicted by witness testimony">Contradicted by witness testimony</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 font-medium">Detailed Explanation (Optional):</label>
              <textarea
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                placeholder="Explain the specific reasons for discarding this link..."
                className="w-full mt-1.5 p-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                rows={3}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setActionModal(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={actionLoading}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? "Rejecting..." : "Confirm Rejection"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sub-Modal: Modify Relationship Type */}
      {actionModal === "modify" && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/80">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-4 shadow-2xl">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <Edit3 className="h-4 w-4 text-indigo-400" /> Correct Relationship Type
            </h4>
            <p className="text-xs text-slate-300">
              Select a more accurate domain relationship type from the controlled schema.
            </p>
            <div>
              <label className="text-xs text-slate-400 font-medium">New Relationship Type:</label>
              <select
                value={newRelType}
                onChange={(e) => setNewRelType(e.target.value)}
                className="w-full mt-1.5 p-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              >
                {supportedTypes.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 font-medium">Modification Note:</label>
              <textarea
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                placeholder="Explain why this relationship type was selected..."
                className="w-full mt-1.5 p-2 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                rows={3}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setActionModal(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleModify}
                disabled={actionLoading}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? "Saving..." : "Apply Modification"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sub-Modal: Add Note */}
      {actionModal === "note" && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/80">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-4 shadow-2xl">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-cyan-400" /> Add Investigator Note
            </h4>
            <div>
              <textarea
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                placeholder="Enter note or corroborating findings..."
                className="w-full p-2.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                rows={4}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setActionModal(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleAddNote}
                disabled={actionLoading || !actionNote.trim()}
                className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold disabled:opacity-50"
              >
                {actionLoading ? "Saving..." : "Save Note"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
