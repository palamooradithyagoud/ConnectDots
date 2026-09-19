"use client";

import React, { useState, useEffect } from "react";
import {
  AgentInvestigationResponse,
  AgentToolTraceItem,
  AgentExampleItem,
} from "@/types/investigation";
import {
  Bot,
  Search,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  FileText,
  HelpCircle,
  Network,
  Users,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Zap,
  Info,
  Link2
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";

interface AgentConsoleProps {
  onSelectEntity?: (id: string, type: string) => void;
}

export const AgentConsole: React.FC<AgentConsoleProps> = ({ onSelectEntity }) => {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentInvestigationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const [traceExpanded, setTraceExpanded] = useState(true);
  const [examples, setExamples] = useState<AgentExampleItem[]>([]);

  // Fetch suggested investigation scenarios
  useEffect(() => {
    async function fetchExamples() {
      try {
        const res = await fetch(`${apiUrl}/agent/examples`);
        if (res.ok) {
          const data = await res.json();
          setExamples(data.examples || []);
        }
      } catch (err) {
        console.warn("Failed to fetch agent examples:", err);
      }
    }
    fetchExamples();
  }, [apiUrl]);

  let investigationCtx: any = null;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    investigationCtx = useInvestigation();
  } catch {
    // Isolated rendering without provider
  }

  const handleInvestigate = async (qToRun?: string) => {
    const activeQ = qToRun || question;
    if (!activeQ.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const scopePayload = investigationCtx ? {
        crime_id: investigationCtx.selectedCrimeId || investigationCtx.selectedCaseId,
        person_id: investigationCtx.selectedPersonId,
        phone_number: investigationCtx.selectedPhoneId,
      } : undefined;

      const res = await fetch(`${apiUrl}/agent/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: activeQ,
          scope: scopePayload
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Agent investigation execution failed");
      }

      const data: AgentInvestigationResponse = await res.json();
      setResult(data);
      if (investigationCtx?.applyAgentResult) {
        investigationCtx.applyAgentResult(data);
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred while communicating with the agent.");
    } finally {
      setLoading(false);
    }
  };

  const getValidationBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === "VALIDATED") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          INVESTIGATOR-VALIDATED
        </span>
      );
    }
    if (s === "REJECTED") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
          <AlertTriangle className="w-3 h-3 text-red-400" />
          REJECTED BY REVIEWER
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
        <Sparkles className="w-3 h-3 text-amber-400" />
        AI-DERIVED (PENDING REVIEW)
      </span>
    );
  };

  return (
    <div className="flex flex-col space-y-6">
      {/* Header & Mission Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 border border-indigo-500/20 p-6 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-indigo-500/20 rounded-xl border border-indigo-500/30 shadow-inner">
              <Bot className="w-7 h-7 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white tracking-wide">
                  Domain AI Investigation Agent
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Phase 7 Orchestrator
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-0.5">
                Multi-database bounded orchestration across PostgreSQL, Neo4j, Qdrant &amp; Groq LPU
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-400 bg-slate-950/60 px-3 py-2 rounded-lg border border-slate-800">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>16 Tools Allowlisted</span>
            </div>
            <span className="text-slate-700">|</span>
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Strict Read-Only</span>
            </div>
          </div>
        </div>

        {/* Input Box */}
        <div className="mt-6 relative">
          <div className="flex items-center bg-slate-950/80 border border-slate-700/80 rounded-xl shadow-inner focus-within:border-indigo-500 transition-all">
            <Search className="w-5 h-5 text-slate-400 ml-4" />
            <input
              type="text"
              className="w-full bg-transparent px-4 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none"
              placeholder="Ask an investigation question (e.g., 'Find cases connected to Case 1042 through phones and show validated links')..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleInvestigate();
                }
              }}
            />
            <button
              onClick={() => handleInvestigate()}
              disabled={loading || !question.trim()}
              className="mr-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg shadow-md transition-all flex items-center gap-2"
            >
              {loading ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  <span>Orchestrating...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Analyze</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Suggested Scenario Chips */}
        {examples.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Scenarios:</span>
            {examples.map((ex, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuestion(ex.question);
                  handleInvestigate(ex.question);
                }}
                className="text-xs bg-slate-800/80 hover:bg-indigo-900/40 text-slate-300 hover:text-indigo-200 border border-slate-700/60 hover:border-indigo-500/40 px-3 py-1 rounded-full transition-all flex items-center gap-1.5"
              >
                <span className="font-semibold text-indigo-400">{ex.scenario}:</span>
                <span className="truncate max-w-xs">{ex.title}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Error Message Display */}
      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-200 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Investigation Error</div>
            <div className="text-xs text-red-300/80 mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {/* Result Container */}
      {result && (
        <div className="space-y-6 animate-fadeIn">
          {/* Status & Timing Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 rounded-lg text-xs font-semibold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {result.status}
              </span>
              <span className="text-xs text-slate-400">
                Investigation ID: <code className="text-slate-300 font-mono">{result.investigation_id}</code>
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                {result.total_duration_ms} ms
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                {result.iterations_count} iterations ({result.tool_trace.length} tools executed)
              </span>
            </div>
          </div>

          {/* Investigation Trace (Expandable Activity) */}
          <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
            <button
              onClick={() => setTraceExpanded(!traceExpanded)}
              className="w-full px-5 py-3.5 flex items-center justify-between bg-slate-900/90 hover:bg-slate-850 border-b border-slate-800 transition-all text-left"
            >
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span className="text-sm font-semibold text-slate-200">Investigation Tool Trace</span>
                <span className="text-xs text-slate-400">({result.tool_trace.length} steps)</span>
              </div>
              {traceExpanded ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>

            {traceExpanded && (
              <div className="p-4 divide-y divide-slate-800/60 font-mono text-xs">
                {result.tool_trace.map((t: AgentToolTraceItem, idx: number) => (
                  <div key={idx} className="py-2.5 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="w-5 text-slate-500 font-semibold">{t.step}.</span>
                      <span className="text-indigo-400 font-semibold">{t.tool}</span>
                      <span className="text-slate-400 truncate">{t.purpose}</span>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="text-slate-500">{t.duration_ms}ms</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300">
                        {t.result_count} items
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          t.status === "SUCCESS"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-red-500/10 text-red-400 border border-red-500/20"
                        }`}
                      >
                        {t.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Investigation Summary */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
              <FileText className="w-4 h-4" />
              <span>Grounded Investigation Synthesis</span>
            </div>
            <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">
              {result.summary}
            </div>
          </div>

          {/* Structurally Central Individuals (Zero Guilt Principle) */}
          {result.key_individuals && result.key_individuals.length > 0 && (
            <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                  <Users className="w-4 h-4" />
                  <span>Structurally Central Individuals</span>
                </div>
                <span className="text-[11px] text-slate-400">
                  Network prominence only • Neutral metrics
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.key_individuals.map((ki, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-indigo-500/40 transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-semibold text-white text-sm">{ki.display_name}</div>
                        <div className="text-[11px] text-slate-500 font-mono">{ki.person_id}</div>
                      </div>
                      {getValidationBadge(ki.validation_status)}
                    </div>

                    <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-800 text-center">
                      <div className="p-2 rounded bg-slate-900/60">
                        <div className="text-[10px] text-slate-400 uppercase">Degree</div>
                        <div className="text-xs font-bold text-white mt-0.5">{ki.degree_centrality}</div>
                      </div>
                      <div className="p-2 rounded bg-slate-900/60">
                        <div className="text-[10px] text-slate-400 uppercase">Betweenness</div>
                        <div className="text-xs font-bold text-white mt-0.5">{ki.betweenness_centrality}</div>
                      </div>
                      <div className="p-2 rounded bg-slate-900/60">
                        <div className="text-[10px] text-slate-400 uppercase">PageRank</div>
                        <div className="text-xs font-bold text-white mt-0.5">{ki.pagerank}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Findings Grid */}
          {result.findings && result.findings.length > 0 && (
            <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                <Network className="w-4 h-4" />
                <span>Corroborated Investigation Findings</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.findings.map((f, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 hover:border-slate-700 transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-semibold text-slate-200 text-sm">{f.title}</h4>
                      {getValidationBadge(f.validation_status)}
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{f.details}</p>
                    {f.supporting_evidence_ids && f.supporting_evidence_ids.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-2">
                        {f.supporting_evidence_ids.map((evId, eIdx) => (
                          <span
                            key={eIdx}
                            className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-indigo-300 border border-slate-700"
                          >
                            {evId}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Normalized Evidence Dossier */}
          {result.evidence && result.evidence.length > 0 && (
            <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                  <Link2 className="w-4 h-4" />
                  <span>Authoritative Evidence Records ({result.evidence.length})</span>
                </div>
                <div className="flex items-center gap-2">
                  {result.citations.map((c, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-950/60 text-indigo-300 border border-indigo-500/30"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {result.evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] font-semibold text-indigo-400">
                        {ev.evidence_id}
                      </span>
                      <span className="text-[10px] text-slate-500 uppercase">{ev.source_system}</span>
                    </div>
                    <div className="text-slate-300 leading-snug line-clamp-3">{ev.summary}</div>
                    <div className="pt-2 border-t border-slate-850 flex items-center justify-between text-[10px]">
                      <span className="text-slate-500">Tool: {ev.tool_used}</span>
                      {getValidationBadge(ev.validation_status)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Uncertainty & Conflict Disclosure Box */}
          {result.uncertainties && result.uncertainties.length > 0 && (
            <div className="p-5 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-2">
              <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
                <HelpCircle className="w-4 h-4" />
                <span>Uncertainty &amp; Investigator Verification Queue</span>
              </div>
              <ul className="space-y-1.5 text-xs text-amber-200/80 list-disc list-inside">
                {result.uncertainties.map((u, idx) => (
                  <li key={idx}>{u}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Statutory Limitations & Zero Guilt Disclaimer */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 flex items-start gap-3">
            <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-slate-400 space-y-1">
              <div className="font-semibold text-slate-300">Statutory Limitations &amp; Zero Guilt Policy:</div>
              {result.limitations.map((lim, idx) => (
                <p key={idx}>• {lim}</p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
