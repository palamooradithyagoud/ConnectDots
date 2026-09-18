"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import {
  BarChart as RBarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from "recharts";
import {
  TrendingUp,
  MapPin,
  AlertTriangle,
  Layers,
  GitBranch,
  Play,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ShieldAlert,
  Network,
  BarChart3,
} from "lucide-react";

import {
  triggerMlAnalysis,
  getMlJobStatus,
  fetchMlStats,
  fetchClusters,
  fetchHotspots,
  fetchTrends,
  fetchAnomalies,
  fetchPatterns,
} from "@/lib/ml-api";
import {
  MlStatsResponse,
  MlJobStatus,
  ClusterRecord,
  HotspotRecord,
  TrendRecord,
  AnomalyRecord,
  PatternRecord,
} from "@/types/crime";

// ─── Colour palette (Innovators Conclave brand) ───────────────────────────────
const CATEGORY_COLORS: Record<string, string> = {
  THEFT: "#5227ff",
  ROBBERY: "#B19EEF",
  BURGLARY: "#7c3aed",
  ASSAULT: "#f59e0b",
  HOMICIDE: "#ef4444",
  VEHICLE_THEFT: "#10b981",
  FRAUD: "#06b6d4",
  CYBERCRIME: "#8b5cf6",
  NARCOTICS: "#f97316",
  VANDALISM: "#64748b",
  UNKNOWN: "#334155",
};
const CHART_VIOLET = "#5227ff";
const CHART_LILAC = "#B19EEF";

const ANOMALY_TYPE_BADGE: Record<string, string> = {
  statistical: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  spatial: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  temporal: "bg-red-500/20 text-red-400 border-red-500/30",
};

const PATTERN_TYPE_LABEL: Record<string, string> = {
  spatial_temporal: "Spatial–Temporal",
  semantic_mo: "Semantic M.O.",
  category_concentration: "Category Concentration",
};

function KpiCard({
  label,
  value,
  icon: Icon,
  accent = false,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  accent?: boolean;
}) {
  return (
    <div
      className={`glass-panel rounded-xl p-5 flex flex-col gap-2 ${
        accent ? "border-brand/40 shadow-[0_0_20px_rgba(82,39,255,0.15)]" : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[0.72rem] font-bold uppercase tracking-widest text-white/40">
          {label}
        </span>
        <Icon
          className={`h-4 w-4 ${accent ? "text-brand" : "text-white/30"}`}
        />
      </div>
      <span
        className={`text-3xl font-black tabular-nums ${
          accent ? "text-brand" : "text-white"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

// ─── Custom Tooltip for Charts ────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-panel rounded-lg p-3 text-sm shadow-xl border border-white/10">
        <p className="text-white/60 text-[0.72rem] mb-1">{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ color: p.color }} className="font-bold">
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
}

export default function AnalyticsPage() {
  // ─── State ────────────────────────────────────────────────────────────────
  const [stats, setStats] = useState<MlStatsResponse | null>(null);
  const [clusters, setClusters] = useState<ClusterRecord[]>([]);
  const [hotspots, setHotspots] = useState<HotspotRecord[]>([]);
  const [monthlyTrends, setMonthlyTrends] = useState<TrendRecord[]>([]);
  const [hourlyTrends, setHourlyTrends] = useState<TrendRecord[]>([]);
  const [dailyTrends, setDailyTrends] = useState<TrendRecord[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);
  const [patterns, setPatterns] = useState<PatternRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<MlJobStatus | null>(null);
  const [running, setRunning] = useState(false);
  const [expandedAnomaly, setExpandedAnomaly] = useState<string | null>(null);
  const [expandedPattern, setExpandedPattern] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"trends" | "clusters" | "anomalies" | "patterns">(
    "trends"
  );
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // ─── Data Fetching ────────────────────────────────────────────────────────
  const loadAllData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        statsData,
        clustersData,
        hotspotsData,
        monthlyData,
        hourlyData,
        dailyData,
        anomaliesData,
        patternsData,
      ] = await Promise.allSettled([
        fetchMlStats(),
        fetchClusters({ limit: 20 }),
        fetchHotspots({ limit: 20 }),
        fetchTrends({ period_type: "monthly" }),
        fetchTrends({ period_type: "hourly" }),
        fetchTrends({ period_type: "daily" }),
        fetchAnomalies({ limit: 50 }),
        fetchPatterns({ limit: 50 }),
      ]);

      if (statsData.status === "fulfilled") setStats(statsData.value);
      if (clustersData.status === "fulfilled") setClusters(clustersData.value.items);
      if (hotspotsData.status === "fulfilled") setHotspots(hotspotsData.value.items);
      if (monthlyData.status === "fulfilled") setMonthlyTrends(monthlyData.value.items);
      if (hourlyData.status === "fulfilled") setHourlyTrends(hourlyData.value.items);
      if (dailyData.status === "fulfilled") setDailyTrends(dailyData.value.items);
      if (anomaliesData.status === "fulfilled") setAnomalies(anomaliesData.value.items);
      if (patternsData.status === "fulfilled") setPatterns(patternsData.value.items);
    } catch (err: any) {
      setError(err.message || "Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // ─── Job Polling ──────────────────────────────────────────────────────────
  const startPolling = useCallback(
    (id: string) => {
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const status = await getMlJobStatus(id);
          setJobStatus(status);
          if (status.status === "COMPLETED" || status.status === "FAILED") {
            clearInterval(pollRef.current!);
            setRunning(false);
            if (status.status === "COMPLETED") {
              await loadAllData();
            }
          }
        } catch (e) {
          clearInterval(pollRef.current!);
          setRunning(false);
        }
      }, 2000);
    },
    [loadAllData]
  );

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  // ─── Trigger Analysis ─────────────────────────────────────────────────────
  const handleRunAnalysis = async () => {
    setRunning(true);
    setError(null);
    setJobStatus(null);
    try {
      const res = await triggerMlAnalysis();
      setJobId(res.job_id);
      setJobStatus({ job_id: res.job_id, status: "PENDING", created_at: new Date().toISOString() });
      startPolling(res.job_id);
    } catch (err: any) {
      setError(err.message || "Failed to start analysis");
      setRunning(false);
    }
  };

  // ─── Derived data for charts ──────────────────────────────────────────────
  const categoryData = clusters.reduce<Record<string, number>>((acc, c) => {
    const cat = c.metadata?.dominant_category || "UNKNOWN";
    acc[cat] = (acc[cat] || 0) + c.crime_count;
    return acc;
  }, {});
  const categoryChartData = Object.entries(categoryData).map(([name, value]) => ({
    name,
    value,
  }));

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-brand" />
            <span className="text-[0.72rem] font-bold uppercase tracking-[0.18em] text-brand">
              Phase 3 · ML Pattern Analysis
            </span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">
            Crime Analytics <span className="text-brand">Intelligence</span>
          </h1>
          <p className="mt-1 text-sm text-white/40">
            Spatial clusters · Temporal patterns · Semantic groupings · Anomaly detection
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            onClick={loadAllData}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-[0.76rem] font-bold text-white/60 hover:text-white hover:border-white/20 transition-all"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={handleRunAnalysis}
            disabled={running}
            className="btn-brand flex items-center gap-2 rounded-lg px-5 py-2 text-[0.76rem] font-black uppercase tracking-wider"
          >
            {running ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {running ? "Analyzing…" : "Run ML Analysis"}
          </button>
        </div>
      </div>

      {/* Job Status Banner */}
      {jobStatus && (
        <div
          className={`rounded-xl border px-5 py-3 flex items-center gap-3 text-sm ${
            jobStatus.status === "COMPLETED"
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
              : jobStatus.status === "FAILED"
              ? "border-red-500/30 bg-red-500/10 text-red-400"
              : "border-brand/30 bg-brand/10 text-brand"
          }`}
        >
          {jobStatus.status === "COMPLETED" ? (
            <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          ) : jobStatus.status === "FAILED" ? (
            <XCircle className="h-4 w-4 flex-shrink-0" />
          ) : (
            <Loader2 className="h-4 w-4 flex-shrink-0 animate-spin" />
          )}
          <span className="font-semibold">
            {jobStatus.status === "COMPLETED"
              ? "ML analysis completed successfully. All panels updated."
              : jobStatus.status === "FAILED"
              ? `Analysis failed: ${jobStatus.error_message}`
              : `Analysis running… Job #${jobStatus.job_id.slice(0, 8)}`}
          </span>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-3 text-sm text-amber-400 flex items-center gap-3">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <KpiCard
          label="Incidents"
          value={stats?.total_crimes_analyzed ?? "—"}
          icon={ShieldAlert}
          accent
        />
        <KpiCard
          label="Clusters"
          value={stats?.total_clusters ?? "—"}
          icon={Layers}
        />
        <KpiCard
          label="Hotspots"
          value={stats?.total_hotspots ?? "—"}
          icon={MapPin}
        />
        <KpiCard
          label="Anomalies"
          value={stats?.total_anomalies ?? "—"}
          icon={AlertTriangle}
        />
        <KpiCard
          label="Patterns"
          value={stats?.total_patterns ?? "—"}
          icon={GitBranch}
        />
      </div>

      {/* Last Analysis */}
      {stats?.last_analysis_at && (
        <p className="text-[0.72rem] text-white/30 flex items-center gap-1.5">
          <Clock className="h-3 w-3" />
          Last analysis: {new Date(stats.last_analysis_at).toLocaleString()}
        </p>
      )}

      {/* No data state */}
      {!loading && stats?.total_clusters === 0 && stats?.total_anomalies === 0 && (
        <div className="glass-panel rounded-2xl p-12 text-center">
          <Network className="h-12 w-12 text-white/20 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-white/60 mb-2">No ML Analysis Results Yet</h3>
          <p className="text-sm text-white/30 mb-6 max-w-md mx-auto">
            Click <strong className="text-white/60">Run ML Analysis</strong> to process Phase 1 & 2 data
            through the spatial, temporal, semantic, and anomaly detection pipeline.
          </p>
          <button
            onClick={handleRunAnalysis}
            disabled={running}
            className="btn-brand inline-flex items-center gap-2 rounded-lg px-6 py-3 text-sm font-black uppercase tracking-wider"
          >
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Start Analysis
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      {(stats?.total_clusters ?? 0) + (stats?.total_anomalies ?? 0) > 0 && (
        <>
          <div className="flex gap-1 border-b border-white/10 pb-0">
            {(["trends", "clusters", "anomalies", "patterns"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2.5 text-[0.75rem] font-bold uppercase tracking-widest transition-all border-b-2 -mb-px ${
                  activeTab === tab
                    ? "border-brand text-white"
                    : "border-transparent text-white/30 hover:text-white/60"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* TRENDS TAB */}
          {activeTab === "trends" && (
            <div className="space-y-6">
              {/* Monthly Trend Chart */}
              <div className="glass-panel rounded-xl p-6">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-brand" />
                  Crime Volume — Monthly Trend
                </h3>
                {monthlyTrends.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={monthlyTrends} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis dataKey="period" tick={{ fill: "#ffffff60", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#ffffff60", fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: "11px", color: "#ffffff60" }} />
                      <Line
                        type="monotone"
                        dataKey="crime_count"
                        stroke={CHART_VIOLET}
                        strokeWidth={2.5}
                        dot={{ fill: CHART_VIOLET, r: 4 }}
                        name="Incidents"
                      />
                      <Line
                        type="monotone"
                        dataKey="rolling_average"
                        stroke={CHART_LILAC}
                        strokeWidth={1.5}
                        strokeDasharray="5 3"
                        dot={false}
                        name="Rolling Avg"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyChart message="No monthly trend data. Run ML analysis first." />
                )}
              </div>

              {/* Hourly + Day-of-Week side by side */}
              <div className="grid md:grid-cols-2 gap-6">
                <div className="glass-panel rounded-xl p-6">
                  <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-brand" />
                    Hourly Crime Distribution
                  </h3>
                  {hourlyTrends.length > 0 ? (
                    <ResponsiveContainer width="100%" height={200}>
                      <RBarChart data={hourlyTrends} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                        <XAxis dataKey="period" tick={{ fill: "#ffffff60", fontSize: 9 }} interval={3} />
                        <YAxis tick={{ fill: "#ffffff60", fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="crime_count" fill={CHART_VIOLET} radius={[2, 2, 0, 0]} name="Incidents" />
                      </RBarChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart message="No hourly data yet." />
                  )}
                </div>

                <div className="glass-panel rounded-xl p-6">
                  <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-brand" />
                    Day-of-Week Distribution
                  </h3>
                  {dailyTrends.length > 0 ? (
                    <ResponsiveContainer width="100%" height={200}>
                      <RBarChart data={dailyTrends} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                        <XAxis
                          dataKey="period"
                          tick={{ fill: "#ffffff60", fontSize: 10 }}
                          tickFormatter={(v) => v.slice(0, 3)}
                        />
                        <YAxis tick={{ fill: "#ffffff60", fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="crime_count" radius={[2, 2, 0, 0]} name="Incidents">
                          {dailyTrends.map((_, index) => (
                            <Cell key={index} fill={index % 2 === 0 ? CHART_VIOLET : CHART_LILAC} />
                          ))}
                        </Bar>
                      </RBarChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart message="No daily data yet." />
                  )}
                </div>
              </div>

              {/* Category Distribution */}
              {categoryChartData.length > 0 && (
                <div className="glass-panel rounded-xl p-6">
                  <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                    <Layers className="h-4 w-4 text-brand" />
                    Category Distribution (from Clusters)
                  </h3>
                  <ResponsiveContainer width="100%" height={220}>
                    <RBarChart
                      data={categoryChartData}
                      layout="vertical"
                      margin={{ top: 5, right: 20, bottom: 5, left: 80 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                      <XAxis type="number" tick={{ fill: "#ffffff60", fontSize: 11 }} />
                      <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fill: "#ffffff80", fontSize: 11 }}
                        width={80}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="value" radius={[0, 2, 2, 0]} name="Incidents">
                        {categoryChartData.map((entry) => (
                          <Cell
                            key={entry.name}
                            fill={CATEGORY_COLORS[entry.name] || CHART_VIOLET}
                          />
                        ))}
                      </Bar>
                    </RBarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* CLUSTERS TAB */}
          {activeTab === "clusters" && (
            <div className="space-y-4">
              {clusters.length === 0 ? (
                <EmptyPanel message="No clusters found. Run ML analysis to discover crime clusters." />
              ) : (
                clusters.map((cluster) => (
                  <ClusterCard key={cluster.id} cluster={cluster} />
                ))
              )}
            </div>
          )}

          {/* ANOMALIES TAB */}
          {activeTab === "anomalies" && (
            <div className="space-y-3">
              {anomalies.length === 0 ? (
                <EmptyPanel message="No anomalies detected yet. Run ML analysis to identify unusual incidents or temporal spikes." />
              ) : (
                anomalies.map((anomaly) => (
                  <AnomalyCard
                    key={anomaly.id}
                    anomaly={anomaly}
                    expanded={expandedAnomaly === anomaly.id}
                    onToggle={() =>
                      setExpandedAnomaly(
                        expandedAnomaly === anomaly.id ? null : anomaly.id
                      )
                    }
                  />
                ))
              )}
            </div>
          )}

          {/* PATTERNS TAB */}
          {activeTab === "patterns" && (
            <div className="space-y-3">
              {patterns.length === 0 ? (
                <EmptyPanel message="No patterns detected yet. Patterns emerge from combined spatial, temporal, and semantic analysis." />
              ) : (
                patterns.map((pattern) => (
                  <PatternCard
                    key={pattern.id}
                    pattern={pattern}
                    expanded={expandedPattern === pattern.id}
                    onToggle={() =>
                      setExpandedPattern(
                        expandedPattern === pattern.id ? null : pattern.id
                      )
                    }
                  />
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Sub-Components ───────────────────────────────────────────────────────────

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="h-[200px] flex items-center justify-center text-white/30 text-sm">
      {message}
    </div>
  );
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="glass-panel rounded-xl p-10 text-center text-white/30 text-sm">
      {message}
    </div>
  );
}

function ClusterCard({ cluster }: { cluster: ClusterRecord }) {
  const meta = cluster.metadata || {};
  const dominantCat = meta.dominant_category || "UNKNOWN";
  const catColor = CATEGORY_COLORS[dominantCat] || CHART_VIOLET;
  const locations = meta.locations || [];
  const repCrimes = meta.representative_crime_ids || [];

  return (
    <div className="glass-panel glass-panel-hover rounded-xl p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className="h-10 w-10 rounded-lg flex items-center justify-center text-sm font-black"
            style={{ background: `${catColor}25`, color: catColor }}
          >
            {cluster.cluster_type === "spatial" ? (
              <MapPin className="h-5 w-5" />
            ) : (
              <Network className="h-5 w-5" />
            )}
          </div>
          <div>
            <p className="text-sm font-bold text-white">
              {cluster.cluster_type === "spatial" ? "Spatial" : "Semantic"} Cluster #{cluster.cluster_label}
            </p>
            <p className="text-[0.72rem] text-white/40">
              {cluster.crime_count} incidents · Dominant: {dominantCat}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="px-2.5 py-0.5 rounded-full text-[0.68rem] font-bold uppercase tracking-wider border"
            style={{
              background: `${catColor}20`,
              color: catColor,
              borderColor: `${catColor}40`,
            }}
          >
            {cluster.cluster_type}
          </span>
        </div>
      </div>

      {/* Category distribution */}
      {meta.category_distribution && Object.keys(meta.category_distribution).length > 1 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {Object.entries(meta.category_distribution).map(([cat, count]) => (
            <span
              key={cat}
              className="text-[0.65rem] font-bold px-2 py-0.5 rounded-full border"
              style={{
                background: `${CATEGORY_COLORS[cat] || CHART_VIOLET}15`,
                color: CATEGORY_COLORS[cat] || CHART_LILAC,
                borderColor: `${CATEGORY_COLORS[cat] || CHART_VIOLET}30`,
              }}
            >
              {cat}: {count as number}
            </span>
          ))}
        </div>
      )}

      {/* Locations */}
      {locations.length > 0 && (
        <p className="mt-2 text-[0.72rem] text-white/35">
          <MapPin className="inline h-3 w-3 mr-1" />
          {locations.slice(0, 3).join(", ")}
          {locations.length > 3 && ` +${locations.length - 3} more`}
        </p>
      )}

      {/* Representative crimes */}
      {repCrimes.length > 0 && (
        <div className="mt-3 pt-3 border-t border-white/8">
          <p className="text-[0.68rem] text-white/30 mb-1.5 uppercase tracking-wider">Representative Incidents</p>
          <div className="flex flex-wrap gap-1.5">
            {repCrimes.map((id: string) => (
              <Link
                key={id}
                href={`/crimes?id=${id}`}
                className="text-[0.68rem] font-mono text-brand/70 hover:text-brand border border-brand/20 hover:border-brand/40 rounded px-2 py-0.5 transition-colors flex items-center gap-1"
              >
                {id.slice(0, 8)}…
                <ExternalLink className="h-2.5 w-2.5" />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function AnomalyCard({
  anomaly,
  expanded,
  onToggle,
}: {
  anomaly: AnomalyRecord;
  expanded: boolean;
  onToggle: () => void;
}) {
  const badgeClass =
    ANOMALY_TYPE_BADGE[anomaly.anomaly_type] ||
    "bg-white/10 text-white/60 border-white/20";

  return (
    <div className="glass-panel rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-5 hover:bg-white/5 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <AlertTriangle
            className={`h-4 w-4 flex-shrink-0 ${
              anomaly.anomaly_type === "temporal"
                ? "text-red-400"
                : anomaly.anomaly_type === "spatial"
                ? "text-blue-400"
                : "text-amber-400"
            }`}
          />
          <div>
            <span
              className={`text-[0.68rem] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${badgeClass}`}
            >
              {anomaly.anomaly_type}
            </span>
            {anomaly.period && (
              <span className="ml-2 text-[0.72rem] text-white/40">
                Period: {anomaly.period}
              </span>
            )}
            {anomaly.category && (
              <span className="ml-2 text-[0.72rem] text-white/40">
                · {anomaly.category}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {anomaly.observed_value != null && anomaly.baseline_value != null && (
            <span className="text-[0.72rem] text-white/40 hidden sm:block">
              Observed: {anomaly.observed_value} · Baseline: {anomaly.baseline_value.toFixed(1)}
            </span>
          )}
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-white/30" />
          ) : (
            <ChevronDown className="h-4 w-4 text-white/30" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/8 px-5 pb-5 pt-4 space-y-3">
          <div className="glass-panel rounded-lg p-4">
            <p className="text-[0.72rem] font-bold text-white/40 uppercase tracking-wider mb-1.5">
              Why This Was Flagged
            </p>
            <p className="text-sm text-white/75 leading-relaxed">{anomaly.explanation}</p>
          </div>
          {anomaly.anomaly_score != null && (
            <p className="text-[0.72rem] text-white/30">
              Anomaly score: {anomaly.anomaly_score.toFixed(4)}
            </p>
          )}
          {anomaly.crime_id && (
            <div className="flex items-center gap-2">
              <p className="text-[0.72rem] text-white/40">Related incident:</p>
              <Link
                href={`/crimes?id=${anomaly.crime_id}`}
                className="text-[0.72rem] font-mono text-brand hover:underline flex items-center gap-1"
              >
                {anomaly.crime_id.slice(0, 8)}…
                <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PatternCard({
  pattern,
  expanded,
  onToggle,
}: {
  pattern: PatternRecord;
  expanded: boolean;
  onToggle: () => void;
}) {
  const confidence = pattern.confidence ?? 0;
  const label = PATTERN_TYPE_LABEL[pattern.pattern_type] || pattern.pattern_type;

  return (
    <div className="glass-panel rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-5 hover:bg-white/5 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <GitBranch className="h-4 w-4 text-brand flex-shrink-0" />
          <div>
            <p className="text-sm font-bold text-white">{label}</p>
            <p className="text-[0.72rem] text-white/40">
              {pattern.category && `${pattern.category} · `}
              {pattern.evidence.length} evidence records
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2">
            <div className="w-20 h-1.5 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-brand"
                style={{ width: `${(confidence * 100).toFixed(0)}%` }}
              />
            </div>
            <span className="text-[0.72rem] text-white/40">
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-white/30" />
          ) : (
            <ChevronDown className="h-4 w-4 text-white/30" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/8 px-5 pb-5 pt-4 space-y-4">
          <div className="glass-panel rounded-lg p-4">
            <p className="text-[0.72rem] font-bold text-white/40 uppercase tracking-wider mb-1.5">
              Pattern Description
            </p>
            <p className="text-sm text-white/75 leading-relaxed">{pattern.description}</p>
          </div>
          <div>
            <p className="text-[0.72rem] font-bold text-white/40 uppercase tracking-wider mb-2">
              Evidence — {pattern.evidence.length} Crime Records
            </p>
            <div className="flex flex-wrap gap-1.5">
              {pattern.evidence.map((id) => (
                <Link
                  key={id}
                  href={`/crimes?id=${id}`}
                  className="text-[0.68rem] font-mono text-brand/70 hover:text-brand border border-brand/20 hover:border-brand/40 rounded px-2 py-0.5 transition-colors flex items-center gap-1"
                >
                  {id.slice(0, 8)}…
                  <ExternalLink className="h-2.5 w-2.5" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
