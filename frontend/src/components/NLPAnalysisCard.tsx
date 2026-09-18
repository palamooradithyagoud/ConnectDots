"use client";

import { useState, useEffect } from "react";
import {
  Sparkles,
  ShieldAlert,
  Cpu,
  RefreshCw,
  Crosshair,
  Car,
  MapPin,
  Users,
  Clock,
  Coins,
  ChevronDown,
  ChevronUp,
  Share2,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { NlpAnalysis } from "@/types/crime";
import { fetchNlpAnalysis, processCrimeNlp } from "@/lib/nlp-api";

interface NLPAnalysisCardProps {
  crimeId: string;
  onAnalysisUpdated?: () => void;
}

export default function NLPAnalysisCard({ crimeId, onAnalysisUpdated }: NLPAnalysisCardProps) {
  const [analysis, setAnalysis] = useState<NlpAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showGraphPayload, setShowGraphPayload] = useState(false);

  const loadAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchNlpAnalysis(crimeId);
      setAnalysis(data);
    } catch (err: any) {
      // 404 means not yet analyzed
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (crimeId) {
      loadAnalysis();
    }
  }, [crimeId]);

  const handleRunNlp = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const updated = await processCrimeNlp(crimeId);
      setAnalysis(updated);
      if (onAnalysisUpdated) onAnalysisUpdated();
    } catch (err: any) {
      setError(err.message || "Failed to execute NLP analysis");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-center">
        <RefreshCw className="mx-auto h-5 w-5 animate-spin text-brand" />
        <p className="mt-2 text-xs text-white/50 font-mono">Loading NLP Intelligence...</p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="rounded-lg border border-brand/30 bg-brand/5 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand" />
              <h4 className="text-sm font-bold uppercase tracking-wider text-white">
                NLP Intelligence Pending
              </h4>
            </div>
            <p className="text-xs text-white/60">
              Run entity extraction, canonical classification, M.O. detection, and Qdrant vector indexing on this crime narrative.
            </p>
          </div>

          <button
            onClick={handleRunNlp}
            disabled={analyzing}
            className="btn-brand shrink-0 inline-flex items-center gap-1.5 rounded-xs px-3 py-1.5 text-xs font-black uppercase tracking-wider shadow-brand-glow"
          >
            <Sparkles className={`h-3.5 w-3.5 ${analyzing ? "animate-spin" : ""}`} />
            {analyzing ? "Analyzing..." : "Analyze with NLP"}
          </button>
        </div>

        {error && (
          <p className="mt-3 text-xs text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20">
            {error}
          </p>
        )}
      </div>
    );
  }

  const confidencePercent = analysis.classification_confidence
    ? Math.round(analysis.classification_confidence * 100)
    : 0;

  const weapons = analysis.extracted_weapons || [];
  const vehicles = analysis.extracted_vehicles || [];
  const locations = analysis.extracted_locations || [];
  const persons = analysis.extracted_persons || [];
  const mos = analysis.modus_operandi || [];
  const dates = analysis.entities?.dates || [];
  const times = analysis.entities?.times || [];
  const money = analysis.entities?.money || [];

  return (
    <div className="space-y-4 rounded-lg border border-brand/30 bg-midnight/90 p-5 shadow-brand-glow">
      {/* Header with Classification & Confidence */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-brand/40 bg-brand/10 text-brand">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-brand">
                NLP Classification
              </span>
              {analysis.needs_review ? (
                <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[0.62rem] font-bold text-amber-400 uppercase">
                  <AlertTriangle className="h-2.5 w-2.5" /> Needs Review
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[0.62rem] font-bold text-emerald-400 uppercase">
                  <CheckCircle2 className="h-2.5 w-2.5" /> Verified High Signal
                </span>
              )}
            </div>
            <h3 className="text-base font-black text-white uppercase font-mono tracking-wide">
              {analysis.predicted_category || "Unclassified"}
            </h3>
          </div>
        </div>

        {/* Confidence Meter */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 block">
              Confidence Score
            </span>
            <span className="text-base font-black font-mono text-white">
              {confidencePercent}%
            </span>
          </div>

          <button
            onClick={handleRunNlp}
            disabled={analyzing}
            title="Re-run NLP analysis"
            className="rounded-xs border border-white/10 bg-white/5 p-2 text-white/70 hover:bg-white/10 hover:text-white transition-all"
          >
            <RefreshCw className={`h-4 w-4 ${analyzing ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Normalized / Preprocessed Narrative */}
      {analysis.processed_text && (
        <div className="rounded-xs border border-white/5 bg-white/5 p-3">
          <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 block mb-1">
            Preprocessed Forensic Narrative (Unchanged from source)
          </span>
          <p className="text-xs text-white/80 font-mono italic">
            &ldquo;{analysis.processed_text}&rdquo;
          </p>
        </div>
      )}

      {/* Extracted Entities Grid */}
      <div className="space-y-2 pt-1">
        <span className="text-[0.68rem] font-bold uppercase tracking-wider text-white/50 block">
          Extracted Criminal Entities
        </span>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          {/* Weapons */}
          <div className="rounded-xs border border-white/5 bg-white/[0.02] p-2.5">
            <div className="flex items-center gap-1.5 text-rose-400 font-bold uppercase text-[0.65rem] mb-1.5">
              <Crosshair className="h-3 w-3" /> Weapons Identified
            </div>
            {weapons.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {weapons.map((w, idx) => (
                  <span key={idx} className="rounded-full border border-rose-500/30 bg-rose-500/10 px-2.5 py-0.5 text-[0.7rem] font-medium text-rose-300">
                    {w}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-white/30 text-[0.7rem]">None explicitly mentioned</span>
            )}
          </div>

          {/* Vehicles */}
          <div className="rounded-xs border border-white/5 bg-white/[0.02] p-2.5">
            <div className="flex items-center gap-1.5 text-amber-400 font-bold uppercase text-[0.65rem] mb-1.5">
              <Car className="h-3 w-3" /> Vehicles / Getaway
            </div>
            {vehicles.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {vehicles.map((v, idx) => (
                  <span key={idx} className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-[0.7rem] font-medium text-amber-300">
                    {v}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-white/30 text-[0.7rem]">None explicitly mentioned</span>
            )}
          </div>

          {/* Locations */}
          <div className="rounded-xs border border-white/5 bg-white/[0.02] p-2.5">
            <div className="flex items-center gap-1.5 text-emerald-400 font-bold uppercase text-[0.65rem] mb-1.5">
              <MapPin className="h-3 w-3" /> Extracted Locations
            </div>
            {locations.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {locations.map((loc, idx) => (
                  <span key={idx} className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[0.7rem] font-medium text-emerald-300">
                    {loc}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-white/30 text-[0.7rem]">None extracted</span>
            )}
          </div>

          {/* Persons / Suspects */}
          <div className="rounded-xs border border-white/5 bg-white/[0.02] p-2.5">
            <div className="flex items-center gap-1.5 text-sky-400 font-bold uppercase text-[0.65rem] mb-1.5">
              <Users className="h-3 w-3" /> Persons & Suspects
            </div>
            {persons.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {persons.map((p, idx) => (
                  <span key={idx} className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-0.5 text-[0.7rem] font-medium text-sky-300">
                    {p}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-white/30 text-[0.7rem]">None explicitly described</span>
            )}
          </div>
        </div>

        {/* Temporal & Financial Entities if present */}
        {(times.length > 0 || dates.length > 0 || money.length > 0) && (
          <div className="flex flex-wrap gap-2 pt-1">
            {times.map((t, idx) => (
              <span key={`time-${idx}`} className="inline-flex items-center gap-1 rounded-full border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-[0.68rem] text-purple-300">
                <Clock className="h-2.5 w-2.5" /> {t}
              </span>
            ))}
            {money.map((m, idx) => (
              <span key={`money-${idx}`} className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[0.68rem] text-emerald-300">
                <Coins className="h-2.5 w-2.5" /> {m}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Modus Operandi (M.O.) Section */}
      <div className="space-y-2 border-t border-white/10 pt-3">
        <span className="text-[0.68rem] font-bold uppercase tracking-wider text-white/50 block">
          Modus Operandi (Execution Patterns)
        </span>
        {mos.length > 0 ? (
          <div className="space-y-1.5">
            {mos.map((mo, idx) => (
              <div key={idx} className="flex items-center justify-between rounded-xs border border-white/5 bg-white/5 px-3 py-2 text-xs">
                <span className="font-bold text-white uppercase font-mono text-[0.72rem]">
                  {mo.pattern}
                </span>
                <span className="rounded-full border border-brand/40 bg-brand/10 px-2 py-0.5 text-[0.62rem] font-bold text-brand uppercase">
                  {mo.certainty.replace("_", " ")}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-white/40 italic">
            No distinctive M.O. behavior identified in text description.
          </p>
        )}
      </div>

      {/* Graph-Ready Schema for Phase 4 (Collapsible) */}
      {analysis.graph_ready_payload && (
        <div className="border-t border-white/10 pt-3">
          <button
            onClick={() => setShowGraphPayload(!showGraphPayload)}
            className="flex w-full items-center justify-between text-left text-xs font-bold uppercase tracking-wider text-brand hover:text-brand-300 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Share2 className="h-3.5 w-3.5" /> Phase 4 Graph-Ready Schema ({analysis.graph_ready_payload.nodes?.length || 0} Nodes, {analysis.graph_ready_payload.relationships?.length || 0} Relationships)
            </span>
            {showGraphPayload ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>

          {showGraphPayload && (
            <div className="mt-2.5 space-y-2 rounded-xs border border-white/5 bg-black/40 p-3 text-[0.7rem] font-mono overflow-x-auto max-h-48 scrollbar-thin">
              <pre className="text-white/70">
                {JSON.stringify(analysis.graph_ready_payload, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Vector DB Metadata */}
      <div className="flex items-center justify-between border-t border-white/5 pt-3 text-[0.65rem] font-mono text-white/40">
        <span>Model: {analysis.embedding_model || "all-MiniLM-L6-v2"} (384-dim)</span>
        <span>Indexed in Qdrant: {analysis.qdrant_point_id ? "Active" : "Pending"}</span>
      </div>
    </div>
  );
}
