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
  Link2,
  Maximize2,
  Minimize2,
  ExternalLink,
  Tag,
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";
import AgenticBall from "@/components/ui/agentic-ball";

interface AgentConsoleProps {
  onSelectEntity?: (id: string, type: string) => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export const AgentConsole: React.FC<AgentConsoleProps> = ({
  onSelectEntity,
  isExpanded,
  onToggleExpand,
}) => {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentInvestigationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const [traceExpanded, setTraceExpanded] = useState(false);
  const [examples, setExamples] = useState<AgentExampleItem[]>([]);

  let investigationCtx: any = null;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    investigationCtx = useInvestigation();
  } catch {
    // Isolated rendering without provider
  }

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

  // Synchronize with context investigation result
  useEffect(() => {
    if (investigationCtx?.activeAgentResult) {
      setResult(investigationCtx.activeAgentResult);
    }
  }, [investigationCtx?.activeAgentResult]);

  useEffect(() => {
    if (investigationCtx?.runningAgent !== undefined) {
      setLoading(investigationCtx.runningAgent);
    }
  }, [investigationCtx?.runningAgent]);

  useEffect(() => {
    if (investigationCtx?.agentError) {
      setError(investigationCtx.agentError);
    }
  }, [investigationCtx?.agentError]);

  const handleInvestigate = async (qToRun?: string) => {
    const activeQ = (qToRun || question).trim();
    if (!activeQ) return;

    setLoading(true);
    setError(null);

    try {
      const scopePayload = investigationCtx
        ? {
            crime_id: investigationCtx.selectedCrimeId || investigationCtx.selectedCaseId,
            person_id: investigationCtx.selectedPersonId,
            phone_number: investigationCtx.selectedPhoneId,
          }
        : undefined;

      const res = await fetch(`${apiUrl}/agent/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: activeQ,
          scope: scopePayload,
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
    const s = (status || "").toUpperCase();
    if (s === "VALIDATED") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.65rem] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 whitespace-nowrap">
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          VALIDATED
        </span>
      );
    }
    if (s === "REJECTED") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.65rem] font-semibold bg-red-500/15 text-red-400 border border-red-500/30 whitespace-nowrap">
          <AlertTriangle className="w-3 h-3 text-red-400" />
          REJECTED
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.65rem] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30 whitespace-nowrap">
        <Sparkles className="w-3 h-3 text-amber-400" />
        AI-DERIVED
      </span>
    );
  };

  return (
    <div className="flex flex-col space-y-4 min-w-0 w-full font-sans">
      {/* Header & Controls */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-[#0e0e1a] via-[#101024] to-[#15102a] border border-purple-500/25 p-3.5 sm:p-4 shadow-xl">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="p-1.5 rounded-lg bg-purple-950/60 border border-purple-500/40 shadow-inner shrink-0">
              <AgenticBall width={22} height={22} speed={0.4} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <h3 className="text-xs sm:text-sm font-bold text-white tracking-wide truncate">
                  Domain AI Agent
                </h3>
                <span className="px-1.5 py-0.2 rounded text-[0.6rem] font-mono uppercase bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  Orchestrator
                </span>
              </div>
              <p className="text-[0.68rem] text-white/50 truncate">
                Multi-tool investigation over SQL, Neo4j &amp; Telecom
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.62rem] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              16 Tools
            </span>

            {onToggleExpand && (
              <button
                type="button"
                onClick={onToggleExpand}
                title={isExpanded ? "Collapse View" : "Expand Full View"}
                className="p-1 rounded-lg border border-white/10 bg-white/[0.04] text-white/70 hover:text-white hover:bg-white/[0.08] transition-colors"
              >
                {isExpanded ? (
                  <Minimize2 className="h-3.5 w-3.5" />
                ) : (
                  <Maximize2 className="h-3.5 w-3.5" />
                )}
              </button>
            )}
          </div>
        </div>

        {/* Responsive Input Box */}
        <div className="mt-3 relative">
          <div className="flex items-center bg-black/60 border border-purple-500/30 rounded-xl shadow-inner focus-within:border-purple-400 transition-all p-1">
            <Search className="w-4 h-4 text-purple-400 ml-2.5 shrink-0" />
            <input
              type="text"
              className="w-full bg-transparent px-2.5 py-1.5 text-xs text-white placeholder-white/40 focus:outline-none min-w-0"
              placeholder="Ask AI about case, phones, suspects..."
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
              className="px-3 py-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-bold rounded-lg shadow-md transition-all shrink-0 flex items-center gap-1 cursor-pointer"
            >
              {loading ? (
                <>
                  <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                  <span className="hidden sm:inline">Running...</span>
                </>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Analyze</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Scenario Chips */}
        {examples.length > 0 && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            <span className="text-[0.62rem] font-mono uppercase text-white/40 mr-0.5">
              Scenarios:
            </span>
            {examples.map((ex, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuestion(ex.question);
                  handleInvestigate(ex.question);
                }}
                className="text-[0.65rem] bg-white/[0.04] hover:bg-purple-900/30 text-white/70 hover:text-purple-200 border border-white/[0.08] hover:border-purple-500/40 px-2 py-0.5 rounded-full transition-all flex items-center gap-1 cursor-pointer"
              >
                <span className="text-purple-400 font-bold">{ex.scenario.replace("Scenario ", "S")}:</span>
                <span className="truncate max-w-[140px] sm:max-w-none">{ex.title}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Error Message Display */}
      {error && (
        <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-200 text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div className="min-w-0">
            <div className="font-bold text-red-300">Investigation Error</div>
            <div className="text-[0.68rem] text-red-300/80 mt-0.5 break-words">{error}</div>
          </div>
        </div>
      )}

      {/* Result Container */}
      {result && (
        <div className="space-y-3.5">
          {/* Status & Timing Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-xl bg-[#0c0c16] border border-white/[0.08] text-xs">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-md text-[0.62rem] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                {result.status}
              </span>
              <span className="text-[0.68rem] text-white/50 font-mono">
                {result.investigation_id}
              </span>
            </div>

            <div className="flex items-center gap-2 text-[0.65rem] font-mono text-white/50">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-purple-400" />
                {result.total_duration_ms} ms
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Layers className="w-3 h-3 text-purple-400" />
                {result.tool_trace.length} tools
              </span>
              <button
                type="button"
                onClick={() => setResult(null)}
                title="Reset Agent View"
                className="text-white/40 hover:text-white ml-1 p-0.5 rounded"
              >
                <RotateCcw className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* Investigation Summary */}
          <div className="p-3.5 sm:p-4 rounded-xl bg-[#0c0c16] border border-white/[0.08] space-y-2">
            <div className="flex items-center gap-1.5 text-purple-400 font-bold text-xs">
              <FileText className="w-3.5 h-3.5" />
              <span>Grounded Investigation Synthesis</span>
            </div>
            <div className="text-slate-200 text-xs leading-relaxed whitespace-pre-wrap break-words">
              {result.summary}
            </div>
          </div>

          {/* Structurally Central Individuals */}
          {result.key_individuals && result.key_individuals.length > 0 && (
            <div className="p-3.5 sm:p-4 rounded-xl bg-[#0c0c16] border border-white/[0.08] space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-amber-400 font-bold text-xs">
                  <Users className="w-3.5 h-3.5" />
                  <span>Structurally Central Individuals ({result.key_individuals.length})</span>
                </div>
                <span className="text-[0.6rem] text-white/40 font-mono">
                  Network Prominence
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {result.key_individuals.map((ki, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-black/40 border border-white/[0.06] hover:border-purple-500/40 transition-all"
                  >
                    <div className="flex items-start justify-between gap-1.5">
                      <div className="min-w-0">
                        <div className="font-bold text-white text-xs truncate">{ki.display_name}</div>
                        <div className="text-[0.6rem] text-white/40 font-mono truncate">{ki.person_id}</div>
                      </div>
                      {getValidationBadge(ki.validation_status)}
                    </div>

                    <div className="grid grid-cols-3 gap-1.5 mt-2 pt-2 border-t border-white/[0.06] text-center">
                      <div className="p-1 rounded bg-white/[0.02]">
                        <div className="text-[0.55rem] text-white/40 uppercase">Degree</div>
                        <div className="text-[0.68rem] font-bold text-white font-mono">{ki.degree_centrality}</div>
                      </div>
                      <div className="p-1 rounded bg-white/[0.02]">
                        <div className="text-[0.55rem] text-white/40 uppercase">Between</div>
                        <div className="text-[0.68rem] font-bold text-white font-mono">{ki.betweenness_centrality}</div>
                      </div>
                      <div className="p-1 rounded bg-white/[0.02]">
                        <div className="text-[0.55rem] text-white/40 uppercase">PageRank</div>
                        <div className="text-[0.68rem] font-bold text-white font-mono">{ki.pagerank}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Findings List */}
          {result.findings && result.findings.length > 0 && (
            <div className="p-3.5 sm:p-4 rounded-xl bg-[#0c0c16] border border-white/[0.08] space-y-2.5">
              <div className="flex items-center gap-1.5 text-purple-400 font-bold text-xs">
                <Network className="w-3.5 h-3.5" />
                <span>Investigation Findings ({result.findings.length})</span>
              </div>

              <div className="flex flex-col gap-2 max-h-72 overflow-y-auto pr-1">
                {result.findings.map((f, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-black/40 border border-white/[0.06] space-y-1"
                  >
                    <div className="flex items-start justify-between gap-1.5">
                      <h4 className="font-bold text-white text-xs">{f.title}</h4>
                      {getValidationBadge(f.validation_status)}
                    </div>
                    <p className="text-[0.7rem] text-white/60 leading-relaxed break-words">{f.details}</p>
                    {f.supporting_evidence_ids && f.supporting_evidence_ids.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {f.supporting_evidence_ids.map((evId, eIdx) => (
                          <span
                            key={eIdx}
                            className="px-1.5 py-0.2 rounded bg-purple-500/10 text-[0.6rem] font-mono text-purple-300 border border-purple-500/20"
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

          {/* Tool Execution Trace (Expandable) */}
          <div className="rounded-xl bg-[#0c0c16] border border-white/[0.08] overflow-hidden">
            <button
              onClick={() => setTraceExpanded(!traceExpanded)}
              className="w-full px-3.5 py-2.5 flex items-center justify-between bg-black/30 hover:bg-black/50 transition-all text-left cursor-pointer"
            >
              <div className="flex items-center gap-1.5 text-xs text-white/70">
                <Layers className="w-3.5 h-3.5 text-purple-400" />
                <span className="font-semibold">Tool Execution Trace</span>
                <span className="text-[0.65rem] text-white/40">({result.tool_trace.length} steps)</span>
              </div>
              {traceExpanded ? (
                <ChevronUp className="w-3.5 h-3.5 text-white/40" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-white/40" />
              )}
            </button>

            {traceExpanded && (
              <div className="p-3 divide-y divide-white/[0.06] font-mono text-xs max-h-56 overflow-y-auto">
                {result.tool_trace.map((t: AgentToolTraceItem, idx: number) => (
                  <div key={idx} className="py-2 flex items-center justify-between gap-2 text-[0.68rem]">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-white/40">{t.step}.</span>
                      <span className="text-purple-300 font-bold">{t.tool}</span>
                      <span className="text-white/40 truncate hidden sm:inline">{t.purpose}</span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-white/40">{t.duration_ms}ms</span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[0.6rem] font-bold ${
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

          {/* Citations & Limitations */}
          {result.citations && result.citations.length > 0 && (
            <div className="p-2.5 rounded-lg bg-black/40 border border-white/[0.06] text-xs flex flex-wrap items-center gap-1.5">
              <span className="text-[0.62rem] font-mono text-white/40 uppercase">Citations:</span>
              {result.citations.map((c, idx) => (
                <span
                  key={idx}
                  className="px-1.5 py-0.2 rounded text-[0.6rem] font-mono bg-purple-950/60 text-purple-300 border border-purple-500/30"
                >
                  {c}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
