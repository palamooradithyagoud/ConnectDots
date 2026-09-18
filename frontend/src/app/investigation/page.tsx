"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Brain,
  Search,
  RefreshCw,
  Layers,
  ShieldAlert,
  Sparkles,
  Link as LinkIcon,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  Database,
  ArrowUpRight,
  Fingerprint,
  FileText
} from "lucide-react";
import InteractiveGraph from "@/components/investigation/InteractiveGraph";
import EvidencePanel from "@/components/investigation/EvidencePanel";
import {
  InvestigationResult,
  GraphStats,
  GraphNode,
  GraphEdge
} from "@/types/investigation";

export default function InvestigationPage() {
  const [question, setQuestion] = useState<string>(
    "Find crimes similar to CR-2026-014 and explain the connections between them."
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Graph Selection State
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // Fetch initial graph stats
  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/graph/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.warn("Could not fetch graph stats:", err);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // Execute Graph Sync
  const handleSyncGraph = async () => {
    setSyncing(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/graph/sync`, { method: "POST" });
      if (res.ok) {
        await fetchStats();
      } else {
        setError("Failed to complete Knowledge Graph synchronization.");
      }
    } catch (err) {
      setError("Network error while synchronizing Knowledge Graph.");
    } finally {
      setSyncing(false);
    }
  };

  // Execute Investigation Query
  const handleInvestigate = async (overrideQuery?: string) => {
    const q = (overrideQuery || question).trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setSelectedEdge(null);

    try {
      const res = await fetch(`${apiUrl}/investigation/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data: InvestigationResult = await res.json();
      setResult(data);
      await fetchStats();
    } catch (err: any) {
      setError(err.message || "Failed to execute investigation query.");
    } finally {
      setLoading(false);
    }
  };

  const exampleChips = [
    "Find crimes similar to CR-2026-014 and explain the connections between them.",
    "Which incidents share the same vehicle or getaway car?",
    "What crimes have a similar modus operandi?",
    "Show connections and evidence between commercial robbery incidents.",
  ];

  return (
    <div className="flex flex-col gap-8 pb-16">
      {/* Top Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold tracking-[0.2em] text-brand uppercase mb-1">
            <Brain className="h-4 w-4" />
            Phase 4 Intelligence Layer
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white uppercase font-mono">
            Investigation <span className="text-brand">Intelligence</span>
          </h1>
          <p className="mt-1 text-sm text-white/60 max-w-2xl">
            Multi-database hybrid retrieval (PostgreSQL + Qdrant + Neo4j). Databases provide the evidence; Graph RAG retrieves the subgraph; the LLM explains the connections with strict citations.
          </p>
        </div>

        {/* Sync & Health Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-black/40 px-3 py-1.5 text-xs font-mono text-white/80">
            <span
              className={`h-2 w-2 rounded-full ${
                stats?.is_fallback ? "bg-amber-400" : "bg-emerald-400"
              } animate-pulse`}
            />
            <span>{stats?.is_fallback ? "In-Memory Resilient" : "Neo4j Active"}</span>
            <span className="text-white/20">|</span>
            <span className="text-white/50">{stats?.total_nodes ?? 0} Nodes</span>
          </div>

          <button
            onClick={handleSyncGraph}
            disabled={syncing}
            className="btn-metallic inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-bold uppercase tracking-wider text-white shadow-md disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${syncing ? "animate-spin text-brand" : ""}`} />
            {syncing ? "Syncing Graph..." : "Sync Graph"}
          </button>
        </div>
      </div>

      {/* Query Bar with Suggestion Chips */}
      <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-midnight/80 p-5 backdrop-blur-xl shadow-2xl">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleInvestigate();
          }}
          className="flex flex-col sm:flex-row items-center gap-3"
        >
          <div className="relative w-full flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask an investigation question (e.g. Find crimes similar to CR-2026-014)..."
              className="w-full rounded-xl border border-white/10 bg-white/[0.03] pl-11 pr-4 py-3 text-sm text-white placeholder-white/30 focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="btn-metallic w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-xs font-black uppercase tracking-wider text-white shadow-lg disabled:opacity-50 min-w-[140px]"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin text-brand" />
                Reasoning...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 text-brand" />
                Investigate
              </>
            )}
          </button>
        </form>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[0.68rem] font-mono font-bold uppercase tracking-wider text-white/40 mr-1">
            Quick Inquiries:
          </span>
          {exampleChips.map((chip, i) => (
            <button
              key={i}
              onClick={() => {
                setQuestion(chip);
                handleInvestigate(chip);
              }}
              className="rounded-full border border-white/10 bg-white/[0.02] px-3 py-1 text-[0.7rem] font-mono text-white/60 hover:border-brand/50 hover:bg-brand/10 hover:text-white transition-all text-left"
            >
              {chip.length > 55 ? `${chip.slice(0, 52)}…` : chip}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 font-mono">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Investigation Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: AI Grounded Analysis & Citations (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* Grounding Confidence Meter */}
          {result && (
            <div className="flex items-center justify-between rounded-xl border border-white/10 bg-midnight/90 p-4 backdrop-blur-md shadow-lg">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-brand/40 bg-brand/10 text-brand">
                  <Fingerprint className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-white">
                    Evidence Grounding
                  </h4>
                  <span className="text-[0.7rem] text-white/50">
                    Source: PostgreSQL & Knowledge Graph
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-base font-black font-mono text-emerald-400">
                  {((result.confidence || 0.88) * 100).toFixed(0)}%
                </span>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[0.65rem] font-mono font-bold text-emerald-400 border border-emerald-500/30">
                  Strict
                </span>
              </div>
            </div>
          )}

          {/* Structured Analysis Sections */}
          {result ? (
            <div className="flex flex-col gap-4">
              {/* 1. Summary Card */}
              <div className="rounded-xl border border-white/10 bg-midnight/90 p-5 backdrop-blur-md shadow-xl">
                <div className="flex items-center gap-2 border-b border-white/10 pb-3 mb-3">
                  <FileText className="h-4 w-4 text-brand" />
                  <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-white">
                    Investigation Summary
                  </h3>
                </div>
                <p className="text-xs text-white/80 leading-relaxed font-sans whitespace-pre-wrap">
                  {result.structured_sections?.summary || result.answer}
                </p>
              </div>

              {/* 2. Connections Card */}
              <div className="rounded-xl border border-white/10 bg-midnight/90 p-5 backdrop-blur-md shadow-xl">
                <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-3">
                  <div className="flex items-center gap-2">
                    <LinkIcon className="h-4 w-4 text-cyan-400" />
                    <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-white">
                      Relational Connections
                    </h3>
                  </div>
                  <span className="text-[0.65rem] font-mono text-cyan-400">
                    {result.related_crimes?.length || 0} Incident Links
                  </span>
                </div>
                <div className="text-xs text-white/80 leading-relaxed font-sans whitespace-pre-wrap space-y-1">
                  {result.structured_sections?.connections || "No verified connections detected."}
                </div>
              </div>

              {/* 3. Evidence Card with Clickable Crime Badges */}
              <div className="rounded-xl border border-white/10 bg-midnight/90 p-5 backdrop-blur-md shadow-xl">
                <div className="flex items-center gap-2 border-b border-white/10 pb-3 mb-3">
                  <Database className="h-4 w-4 text-emerald-400" />
                  <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-white">
                    Supporting Incidents & Evidence
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2 mb-3">
                  {result.related_crimes?.map((rc, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        const targetNode = result.graph_nodes?.find(
                          n => n.id === rc.crime_id || n.id === `crime:${rc.crime_id}`
                        );
                        if (targetNode) setSelectedNode(targetNode);
                      }}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 text-[0.7rem] font-mono font-bold text-purple-300 hover:border-purple-400 hover:bg-purple-500/20 transition-all"
                    >
                      <span>{rc.record_id || rc.crime_id}</span>
                      <ArrowUpRight className="h-3 w-3 text-purple-400" />
                    </button>
                  ))}
                </div>
                <div className="text-xs text-white/70 leading-relaxed font-mono text-[0.72rem] whitespace-pre-wrap">
                  {result.structured_sections?.evidence}
                </div>
              </div>

              {/* 4. Uncertainty & Analytical Boundaries */}
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5 backdrop-blur-md shadow-xl">
                <div className="flex items-center gap-2 border-b border-amber-500/20 pb-3 mb-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-amber-300">
                    Analytical Boundaries & Uncertainty
                  </h3>
                </div>
                <div className="text-[0.72rem] text-amber-200/70 leading-relaxed font-sans whitespace-pre-wrap">
                  {result.structured_sections?.uncertainty ||
                    "Statistical similarity and graph connections do not establish legal proof of common perpetrator identity."}
                </div>
              </div>

              {/* 5. Citations Breakdown */}
              {result.citations && result.citations.length > 0 && (
                <div className="rounded-xl border border-white/10 bg-midnight/90 p-5 backdrop-blur-md shadow-xl">
                  <div className="flex items-center gap-2 border-b border-white/10 pb-3 mb-3">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-white">
                      Verified Citations ({result.citations.length})
                    </h3>
                  </div>
                  <div className="space-y-3">
                    {result.citations.map((cite, i) => (
                      <div
                        key={i}
                        className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5 text-xs"
                      >
                        <p className="text-white/80 font-sans italic">"{cite.claim}"</p>
                        <div className="mt-2 flex flex-wrap items-center gap-1.5">
                          <span className="text-[0.65rem] font-mono text-white/40">Evidence:</span>
                          {cite.evidence.map((evId, j) => (
                            <span
                              key={j}
                              className="rounded bg-brand/20 px-2 py-0.5 font-mono text-[0.65rem] font-bold text-brand-glow"
                            >
                              {evId}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-midnight/60 p-8 text-center backdrop-blur-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-brand mb-3">
                <Brain className="h-6 w-6" />
              </div>
              <h4 className="text-sm font-bold text-white uppercase font-mono">
                No Query Executed Yet
              </h4>
              <p className="mt-1 text-xs text-white/40 max-w-sm">
                Submit an inquiry above to initiate hybrid database retrieval, Knowledge Graph traversal, and grounded explanation.
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Interactive Knowledge Graph & Inspector (7 Cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          {/* Interactive Graph Visualization */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-brand" />
                <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-white">
                  Evidence Graph Visualization
                </h3>
              </div>
              <span className="text-[0.7rem] font-mono text-white/40">
                Interactive Force Canvas
              </span>
            </div>

            <InteractiveGraph
              nodes={result?.graph_nodes || []}
              edges={result?.graph_paths || []}
              selectedNodeId={selectedNode?.id || null}
              selectedEdge={selectedEdge}
              onSelectNode={setSelectedNode}
              onSelectEdge={setSelectedEdge}
              onDrillDownCrime={(crimeId) => {
                setQuestion(`Find crimes similar to ${crimeId} and explain the connections.`);
                handleInvestigate(`Find crimes similar to ${crimeId} and explain the connections.`);
              }}
            />
          </div>

          {/* Evidence Inspector Panel */}
          <EvidencePanel
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            onDrillDownCrime={(crimeId) => {
              setQuestion(`Find crimes similar to ${crimeId} and explain the connections.`);
              handleInvestigate(`Find crimes similar to ${crimeId} and explain the connections.`);
            }}
            onClose={() => {
              setSelectedNode(null);
              setSelectedEdge(null);
            }}
          />
        </div>
      </div>
    </div>
  );
}
