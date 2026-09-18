import { NlpAnalysis, SemanticSearchResponse, NlpStatsResponse } from "@/types/crime";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

/**
 * Fetches the NLP analysis record for a specific crime.
 */
export async function fetchNlpAnalysis(crimeId: string): Promise<NlpAnalysis> {
  const res = await fetch(`${API_BASE_URL}/nlp/${crimeId}`, { cache: "no-store" });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to fetch NLP analysis" }));
    throw new Error(errorData.detail || `Error ${res.status}`);
  }
  return res.json();
}

/**
 * Triggers NLP processing for a single crime record.
 */
export async function processCrimeNlp(crimeId: string): Promise<NlpAnalysis> {
  const res = await fetch(`${API_BASE_URL}/nlp/process/${crimeId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "NLP processing failed" }));
    throw new Error(errorData.detail || `Error ${res.status}`);
  }
  return res.json();
}

/**
 * Triggers batch NLP processing for unanalyzed records.
 */
export async function batchProcessNlp(limit: number = 50, forceReprocess: boolean = false): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/nlp/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit, force_reprocess: forceReprocess }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Batch processing failed" }));
    throw new Error(errorData.detail || `Error ${res.status}`);
  }
  return res.json();
}

/**
 * Fetches real-time NLP and vector database statistics.
 */
export async function fetchNlpStats(): Promise<NlpStatsResponse> {
  const res = await fetch(`${API_BASE_URL}/nlp/stats`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch NLP stats: ${res.status}`);
  }
  return res.json();
}

/**
 * Retries all records that previously failed NLP processing.
 */
export async function retryFailedNlp(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/nlp/retry-failed`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to retry failed records: ${res.status}`);
  }
  return res.json();
}

/**
 * Queries the semantic similarity search engine.
 */
export async function semanticSearch(params: {
  query: string;
  category?: string;
  limit?: number;
  similarityThreshold?: number;
  location?: string;
}): Promise<SemanticSearchResponse> {
  const res = await fetch(`${API_BASE_URL}/search/similar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: params.query,
      category: params.category || null,
      limit: params.limit ?? 10,
      similarity_threshold: params.similarityThreshold ?? 0.40,
      location: params.location || null,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Search query failed" }));
    throw new Error(errorData.detail || `Search failed: ${res.status}`);
  }
  return res.json();
}
