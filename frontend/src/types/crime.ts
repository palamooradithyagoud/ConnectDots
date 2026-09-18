export interface CrimeRecord {
  id: string;
  record_id: string;
  crime_type: string;
  category: string;
  location_name: string;
  occurred_at: string;
  latitude: number;
  longitude: number;
  description: string | null;
  source: string;
  status: string;
  import_batch_id?: string | null;
  extra_metadata?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface CrimeListResponse {
  items: CrimeRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RejectionDetail {
  row_number: number | null;
  raw_data: Record<string, any>;
  error_category: string;
  error_message: string;
}

export interface ImportResultResponse {
  batch_id: string | null;
  dry_run: boolean;
  filename: string;
  total_rows: number;
  valid_count: number;
  rejected_count: number;
  preview_valid: any[];
  rejections: RejectionDetail[];
  message: string;
}

export interface StatsResponse {
  total_crimes: number;
  total_batches: number;
  total_valid: number;
  total_rejected: number;
  by_category: Record<string, number>;
  by_source: Record<string, number>;
  geo_coverage?: {
    min_latitude: number;
    max_latitude: number;
    min_longitude: number;
    max_longitude: number;
  } | null;
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number]; // [lon, lat]
  };
  properties: {
    id: string;
    record_id: string;
    crime_type: string;
    category: string;
    location: string;
    occurred_at: string | null;
    description: string | null;
    source: string;
  };
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}

export interface ImportBatch {
  id: string;
  filename: string;
  file_type: string;
  total_rows: number;
  valid_count: number;
  rejected_count: number;
  status: string;
  created_at: string;
}

// Phase 2: NLP & Semantic Intelligence Interfaces

export interface ModusOperandi {
  pattern: string;
  certainty: string;
  matched_text?: string | null;
}

export interface NlpAnalysis {
  id: string;
  crime_id: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  processed_text?: string | null;
  entities?: {
    persons?: string[];
    locations?: string[];
    organizations?: string[];
    weapons?: string[];
    vehicles?: string[];
    dates?: string[];
    times?: string[];
    money?: string[];
  } | null;
  extracted_weapons?: string[];
  extracted_vehicles?: string[];
  extracted_locations?: string[];
  extracted_persons?: string[];
  modus_operandi?: ModusOperandi[];
  predicted_category?: string | null;
  classification_confidence?: number | null;
  needs_review: boolean;
  embedding_model?: string | null;
  qdrant_point_id?: string | null;
  graph_ready_payload?: {
    crime_id: string;
    record_id: string;
    nodes: Array<{ id: string; label: string; properties: Record<string, any> }>;
    relationships: Array<{ source: string; relation: string; target: string }>;
  } | null;
  error_message?: string | null;
  processed_at?: string | null;
}

export interface SemanticSearchResult {
  crime_id: string;
  record_id: string;
  category: string;
  predicted_category?: string | null;
  similarity_score: number;
  location: string;
  occurred_at?: string | null;
  description?: string | null;
  entities?: Record<string, any> | null;
  weapons?: string[];
  vehicles?: string[];
  modus_operandi?: ModusOperandi[];
}

export interface SemanticSearchResponse {
  query: string;
  total_results: number;
  similarity_threshold: number;
  results: SemanticSearchResult[];
}

export interface NlpStatsResponse {
  total_crimes: number;
  nlp_processed: number;
  nlp_pending: number;
  nlp_failed: number;
  needs_review_count: number;
  average_confidence: number;
  qdrant_indexed_vectors: number;
  predicted_category_distribution: Record<string, number>;
  embedding_model: string;
}

