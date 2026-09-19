"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  CheckCircle2,
  AlertOctagon,
  Layers,
  MapPin,
  UploadCloud,
  ArrowRight,
  Database,
  RefreshCw,
  Sparkles,
  Cpu,
  BrainCircuit,
  Search,
} from "lucide-react";
import StatCard from "@/components/StatCard";
import { fetchStats, fetchImportBatches } from "@/lib/api";
import { fetchNlpStats, batchProcessNlp } from "@/lib/nlp-api";
import { StatsResponse, ImportBatch, NlpStatsResponse } from "@/types/crime";

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [nlpStats, setNlpStats] = useState<NlpStatsResponse | null>(null);
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingNlp, setProcessingNlp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nlpMessage, setNlpMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, batchesData, nlpStatsData] = await Promise.all([
        fetchStats(),
        fetchImportBatches().catch(() => []),
        fetchNlpStats().catch(() => null),
      ]);
      setStats(statsData);
      setBatches(batchesData);
      setNlpStats(nlpStatsData);
    } catch (err: any) {
      setError(err.message || "Failed to connect to backend service");
    } finally {
      setLoading(false);
    }
  };

  const handleBatchNlp = async () => {
    setProcessingNlp(true);
    setNlpMessage(null);
    try {
      const res = await batchProcessNlp(50, true);
      setNlpMessage(`Successfully processed ${res.processed_count} records through NLP & indexed in Qdrant!`);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Batch NLP processing failed");
    } finally {
      setProcessingNlp(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalIncidents = stats?.total_crimes ?? 0;
  const validCount = stats?.total_valid ?? 0;
  const rejectedCount = stats?.total_rejected ?? 0;
  const totalProcessed = validCount + rejectedCount;
  const validityRate = totalProcessed > 0 ? ((validCount / totalProcessed) * 100).toFixed(1) : "100.0";

  return (
    <div className="space-y-8">
      {/* Hero Welcome Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand/10 px-2.5 py-0.5 text-[0.65rem] font-bold tracking-[0.2em] uppercase text-brand-300">
              ConnectDots Core · Phases 1 & 2
            </span>
            <span className="text-[0.65rem] font-semibold text-white/40 uppercase tracking-widest">
              Data Pipeline & NLP Intelligence
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black uppercase tracking-tight text-white font-mono">
            Crime Data & NLP Understanding
          </h1>
          <p className="mt-1 text-sm text-white/60 max-w-2xl">
            Real-time ingestion metrics, PostGIS spatial indexing, and Qdrant semantic vector intelligence.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3.5 py-2 text-xs font-bold uppercase tracking-wider text-white/80 hover:bg-white/[0.08] hover:text-white transition-all active:scale-95"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-brand-300" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={handleBatchNlp}
            disabled={processingNlp || loading}
            className="inline-flex items-center gap-2 rounded-lg border border-brand/40 bg-brand/10 px-3.5 py-2 text-xs font-bold uppercase tracking-wider text-brand-200 hover:bg-brand/20 transition-all shadow-sm active:scale-95"
          >
            <Cpu className={`h-3.5 w-3.5 text-brand-300 ${processingNlp ? "animate-spin" : ""}`} />
            <span>{processingNlp ? "Processing..." : "Run Batch NLP"}</span>
          </button>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 rounded-lg border border-white/15 bg-white/[0.08] px-3.5 py-2 text-xs font-bold uppercase tracking-wider text-white hover:bg-white/[0.14] transition-all active:scale-95"
          >
            <Sparkles className="h-3.5 w-3.5 text-brand-300" />
            <span>Semantic Search</span>
          </Link>
          <Link
            href="/import"
            className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-xs font-bold uppercase tracking-wider text-white hover:bg-brand-600 transition-all shadow-brand-glow active:scale-95"
          >
            <UploadCloud className="h-4 w-4" />
            <span>Ingest Dataset</span>
          </Link>
        </div>
      </div>

      {nlpMessage && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-300 flex items-center justify-between shadow-lg shadow-emerald-950/20">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider">
            <CheckCircle2 className="h-4 w-4 shrink-0" /> {nlpMessage}
          </div>
          <button onClick={() => setNlpMessage(null)} className="text-white/50 hover:text-white transition">
            ✕
          </button>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 shadow-lg shadow-rose-950/20">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider">
            <AlertOctagon className="h-4 w-4 shrink-0" /> Connection Notice
          </div>
          <p className="mt-1">{error}. Ensure the FastAPI backend is running on port 8000.</p>
        </div>
      )}

      {/* Phase 2: NLP Intelligence & Vector Indexing KPIs */}
      <div>
        <div className="flex items-center justify-between mb-3.5">
          <span className="text-xs font-bold uppercase tracking-wider text-white/60 flex items-center gap-2">
            <Cpu className="h-3.5 w-3.5 text-brand-300" /> Phase 2 · NLP Understanding & Vector Retrieval
          </span>
          <Link
            href="/search"
            className="text-[0.7rem] font-bold uppercase text-brand-300 hover:text-brand-200 flex items-center gap-1 transition"
          >
            Open Semantic Search <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="NLP Understood"
            value={loading ? "..." : `${nlpStats?.nlp_processed ?? 0} / ${totalIncidents}`}
            subtitle="Analyzed crime descriptions"
            icon={Cpu}
            badgeText="spaCy / Rules"
            badgeType="brand"
          />
          <StatCard
            label="Qdrant Vectors"
            value={loading ? "..." : `${nlpStats?.qdrant_indexed_vectors ?? 0}`}
            subtitle="384-dim dense embeddings"
            icon={BrainCircuit}
            badgeText="all-MiniLM-L6"
            badgeType="brand"
          />
          <StatCard
            label="Avg NLP Confidence"
            value={loading ? "..." : `${Math.round((nlpStats?.average_confidence ?? 0) * 100)}%`}
            subtitle="Canonical taxonomy score"
            icon={Sparkles}
            badgeText="Calibrated"
            badgeType="success"
          />
          <StatCard
            label="Human Review Flags"
            value={loading ? "..." : nlpStats?.needs_review_count ?? 0}
            subtitle="Confidence below 60% threshold"
            icon={AlertOctagon}
            badgeText={nlpStats?.needs_review_count ? "Flagged" : "Clear"}
            badgeType={nlpStats?.needs_review_count ? "warning" : "success"}
          />
        </div>
      </div>

      {/* Phase 1: Spatial & Ingestion Pipeline KPIs */}
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-white/60 block mb-3.5">
          Phase 1 · Data Collection & Spatial Normalization
        </span>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Total Incidents"
            value={loading ? "..." : totalIncidents.toLocaleString()}
            subtitle="Validated records in PostgreSQL"
            icon={Database}
            badgeText="Active PostGIS"
            badgeType="brand"
          />
          <StatCard
            label="Pipeline Ingestion"
            value={loading ? "..." : stats?.total_batches ?? 0}
            subtitle="Import batches recorded"
            icon={Layers}
            badgeText="Audited"
            badgeType="brand"
          />
          <StatCard
            label="Data Quality Pass"
            value={loading ? "..." : `${validityRate}%`}
            subtitle={`${validCount} valid / ${rejectedCount} rejected`}
            icon={CheckCircle2}
            badgeText="Standardized"
            badgeType="success"
          />
          <StatCard
            label="Rejected Records"
            value={loading ? "..." : rejectedCount}
            subtitle="Non-destructive error logs"
            icon={AlertOctagon}
            badgeText={rejectedCount > 0 ? "Flagged" : "Clean"}
            badgeType={rejectedCount > 0 ? "warning" : "success"}
          />
        </div>
      </div>

      {/* Category Breakdown & Geographic Coverage Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Category Breakdown (2 Cols) */}
        <div className="glass-panel p-6 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                Incidents by Canonical Category
              </h2>
              <p className="text-xs text-white/50">Normalized categorization across all ingestion sources</p>
            </div>
            <Link
              href="/crimes"
              className="inline-flex items-center gap-1 text-xs font-bold uppercase text-brand-300 hover:text-brand-200 transition"
            >
              View Table <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {stats?.by_category && Object.keys(stats.by_category).length > 0 ? (
            <div className="space-y-3 pt-2">
              {Object.entries(stats.by_category).map(([category, count]) => {
                const percentage = totalIncidents > 0 ? Math.round((count / totalIncidents) * 100) : 0;
                return (
                  <div key={category} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="font-bold text-white uppercase">{category}</span>
                      <span className="text-white/60">
                        {count} ({percentage}%)
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-brand to-brand-300 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-white/40">
              No crime category distribution recorded yet. Ingest a dataset to view distribution.
            </div>
          )}
        </div>

        {/* Geographic Coverage Summary (1 Col) */}
        <div className="glass-panel p-6 flex flex-col justify-between space-y-4">
          <div>
            <div className="border-b border-white/10 pb-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                Geographic Coverage
              </h2>
              <p className="text-xs text-white/50">PostGIS spatial bounding envelope</p>
            </div>

            <div className="mt-4 space-y-3">
              <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3.5">
                <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40">
                  Latitude Bounds
                </span>
                <p className="mt-1 text-xs font-mono text-white font-semibold">
                  {stats?.geo_coverage?.min_latitude !== undefined && stats?.geo_coverage?.min_latitude !== null
                    ? `${stats.geo_coverage.min_latitude.toFixed(4)}° to ${stats.geo_coverage.max_latitude?.toFixed(4)}° N`
                    : "No spatial bounds"}
                </p>
              </div>

              <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3.5">
                <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40">
                  Longitude Bounds
                </span>
                <p className="mt-1 text-xs font-mono text-white font-semibold">
                  {stats?.geo_coverage?.min_longitude !== undefined && stats?.geo_coverage?.min_longitude !== null
                    ? `${stats.geo_coverage.min_longitude.toFixed(4)}° to ${stats.geo_coverage.max_longitude?.toFixed(4)}° E`
                    : "No spatial bounds"}
                </p>
              </div>

              <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3.5">
                <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40">
                  Spatial Reference System
                </span>
                <p className="mt-1 text-xs font-mono text-brand-300 font-bold">
                  EPSG:4326 (WGS84 Geodetic)
                </p>
              </div>
            </div>
          </div>

          <Link
            href="/map"
            className="inline-flex items-center justify-center gap-2 w-full rounded-lg border border-brand/40 bg-brand/10 hover:bg-brand/20 text-brand-200 py-2.5 text-xs font-bold uppercase tracking-wider transition-all mt-4"
          >
            <MapPin className="h-3.5 w-3.5 text-brand-300" />
            Open Spatial Map
          </Link>
        </div>
      </div>

      {/* Recent Import Batches Audit */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-white">
              Recent Ingestion Audits
            </h2>
            <p className="text-xs text-white/50">Tracking runs, valid records committed, and logged rejections</p>
          </div>
          <Link
            href="/import"
            className="text-xs font-bold uppercase text-brand-300 hover:text-brand-200 transition"
          >
            New Import
          </Link>
        </div>

        {batches.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-white/10">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/10 bg-white/[0.02] text-[0.68rem] font-bold uppercase tracking-wider text-white/40">
                <tr>
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Format</th>
                  <th className="py-3 px-4">Total Rows</th>
                  <th className="py-3 px-4">Valid</th>
                  <th className="py-3 px-4">Rejected</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono">
                {batches.slice(0, 5).map((b) => (
                  <tr key={b.id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-3 px-4 font-medium text-white">{b.filename}</td>
                    <td className="py-3 px-4 text-white/60">{b.file_type}</td>
                    <td className="py-3 px-4 text-white/80">{b.total_rows}</td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">{b.valid_count}</td>
                    <td className="py-3 px-4 text-rose-400 font-bold">{b.rejected_count}</td>
                    <td className="py-3 px-4">
                      <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[0.65rem] text-emerald-400 uppercase font-semibold">
                        {b.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-white/40">
                      {new Date(b.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="py-8 text-center text-xs text-white/40">
            No ingestion batches logged yet. Upload sample CSV or JSON in the Ingestion Pipeline.
          </p>
        )}
      </div>
    </div>
  );
}
