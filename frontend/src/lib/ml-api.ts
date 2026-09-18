import {
  MlStatsResponse,
  MlJobStatus,
  ClusterListResponse,
  HotspotListResponse,
  TrendListResponse,
  AnomalyListResponse,
  PatternListResponse,
} from "@/types/crime";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ─── Analysis Job ────────────────────────────────────────────────────────────

export async function triggerMlAnalysis(
  analyses?: string[]
): Promise<{ job_id: string; status: string; message: string }> {
  const res = await fetch(`${API_BASE_URL}/ml/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analyses: analyses ?? null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to trigger ML analysis");
  }
  return res.json();
}

export async function getMlJobStatus(jobId: string): Promise<MlJobStatus> {
  const res = await fetch(`${API_BASE_URL}/ml/jobs/${jobId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to get job status for ${jobId}`);
  const data = await res.json();
  return { ...data, job_id: data.job_id ?? jobId };
}

// ─── Stats ───────────────────────────────────────────────────────────────────

export async function fetchMlStats(): Promise<MlStatsResponse> {
  const res = await fetch(`${API_BASE_URL}/ml/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch ML stats");
  return res.json();
}

// ─── Clusters ────────────────────────────────────────────────────────────────

export async function fetchClusters(params?: {
  cluster_type?: string;
  category?: string;
  include_members?: boolean;
  limit?: number;
}): Promise<ClusterListResponse> {
  const url = new URL(`${API_BASE_URL}/ml/clusters`);
  if (params?.cluster_type) url.searchParams.set("cluster_type", params.cluster_type);
  if (params?.category) url.searchParams.set("category", params.category);
  if (params?.include_members) url.searchParams.set("include_members", "true");
  if (params?.limit) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch clusters");
  return res.json();
}

// ─── Hotspots ────────────────────────────────────────────────────────────────

export async function fetchHotspots(params?: {
  category?: string;
  limit?: number;
}): Promise<HotspotListResponse> {
  const url = new URL(`${API_BASE_URL}/ml/hotspots`);
  if (params?.category) url.searchParams.set("category", params.category);
  if (params?.limit) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch hotspots");
  return res.json();
}

// ─── Trends ──────────────────────────────────────────────────────────────────

export async function fetchTrends(params?: {
  period_type?: string;
  category?: string;
  limit?: number;
}): Promise<TrendListResponse> {
  const url = new URL(`${API_BASE_URL}/ml/trends`);
  if (params?.period_type) url.searchParams.set("period_type", params.period_type);
  if (params?.category) url.searchParams.set("category", params.category);
  if (params?.limit) url.searchParams.set("limit", String(params.limit ?? 200));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch trends");
  return res.json();
}

// ─── Anomalies ───────────────────────────────────────────────────────────────

export async function fetchAnomalies(params?: {
  anomaly_type?: string;
  category?: string;
  limit?: number;
}): Promise<AnomalyListResponse> {
  const url = new URL(`${API_BASE_URL}/ml/anomalies`);
  if (params?.anomaly_type) url.searchParams.set("anomaly_type", params.anomaly_type);
  if (params?.category) url.searchParams.set("category", params.category);
  if (params?.limit) url.searchParams.set("limit", String(params.limit ?? 50));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch anomalies");
  return res.json();
}

// ─── Patterns ────────────────────────────────────────────────────────────────

export async function fetchPatterns(params?: {
  pattern_type?: string;
  category?: string;
  limit?: number;
}): Promise<PatternListResponse> {
  const url = new URL(`${API_BASE_URL}/ml/patterns`);
  if (params?.pattern_type) url.searchParams.set("pattern_type", params.pattern_type);
  if (params?.category) url.searchParams.set("category", params.category);
  if (params?.limit) url.searchParams.set("limit", String(params.limit ?? 50));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch patterns");
  return res.json();
}
