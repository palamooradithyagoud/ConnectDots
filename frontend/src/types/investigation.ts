export interface GraphNode {
  id: string;
  label: string;
  properties: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  properties: Record<string, any>;
}

export interface Citation {
  claim: string;
  evidence: string[];
}

export interface RelatedCrime {
  crime_id: string;
  record_id?: string;
  category?: string;
  connection_type: string;
  confidence_type?: "explicit" | "derived" | string;
  confidence?: number;
  similarity?: number;
}

export interface InvestigationResult {
  answer: string;
  structured_sections: {
    summary: string;
    connections: string;
    evidence: string;
    uncertainty: string;
  };
  citations: Citation[];
  evidence: Record<string, any>;
  graph_paths: GraphEdge[];
  graph_nodes: GraphNode[];
  related_crimes: RelatedCrime[];
  confidence: number;
  meta: Record<string, any>;
}

export interface GraphStats {
  status: string;
  is_fallback: boolean;
  crime_nodes: number;
  location_nodes: number;
  vehicle_nodes: number;
  weapon_nodes: number;
  mo_nodes: number;
  person_nodes: number;
  organization_nodes: number;
  cluster_nodes: number;
  pattern_nodes: number;
  total_nodes: number;
  total_relationships: number;
  explicit_relationships: number;
  derived_relationships: number;
  last_sync?: string | null;
}
