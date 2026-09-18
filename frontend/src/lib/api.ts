import {
  CrimeListResponse,
  CrimeRecord,
  StatsResponse,
  GeoJSONFeatureCollection,
  ImportResultResponse,
  ImportBatch,
  RejectionDetail,
} from "@/types/crime";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE_URL}/crimes/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch statistics");
  return res.json();
}

export interface CrimeFilterParams {
  page?: number;
  page_size?: number;
  search?: string;
  crime_type?: string;
  category?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  source?: string;
  status?: string;
  sort_by?: string;
  order?: "asc" | "desc";
}

export async function fetchCrimes(params: CrimeFilterParams = {}): Promise<CrimeListResponse> {
  const url = new URL(`${API_BASE_URL}/crimes`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.append(key, String(value));
    }
  });

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch crime records");
  return res.json();
}

export async function fetchCrimeById(id: string): Promise<CrimeRecord> {
  const res = await fetch(`${API_BASE_URL}/crimes/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch crime with ID ${id}`);
  return res.json();
}

export async function deleteCrime(id: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE_URL}/crimes/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete crime with ID ${id}`);
  return res.json();
}

export async function fetchLocations(category?: string): Promise<GeoJSONFeatureCollection> {
  const url = new URL(`${API_BASE_URL}/crimes/locations`);
  if (category) url.searchParams.append("category", category);
  url.searchParams.append("limit", "2000");

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch location coordinates");
  return res.json();
}

export async function importCrimeFile(file: File, dryRun: boolean = false): Promise<ImportResultResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_BASE_URL}/crimes/import?dry_run=${dryRun}`;
  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "File import failed");
  }

  return res.json();
}

export async function fetchImportBatches(): Promise<ImportBatch[]> {
  const res = await fetch(`${API_BASE_URL}/crimes/batches`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch batches");
  return res.json();
}

export async function fetchBatchRejections(batchId: string): Promise<RejectionDetail[]> {
  const res = await fetch(`${API_BASE_URL}/crimes/batches/${batchId}/rejections`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch rejections for batch");
  return res.json();
}
