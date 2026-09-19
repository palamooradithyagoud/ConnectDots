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

export interface KeyIndividual {
  person_id: string;
  canonical_name: string;
  display_name: string;
  aliases: string[];
  source_provenance?: string;
  metrics: {
    degree_centrality: number;
    betweenness_centrality: number;
    pagerank: number;
    raw_degree: number;
  };
  network_breakdown: {
    connected_crimes: number;
    connected_people: number;
    connected_phones: number;
    connected_vehicles: number;
    connected_organizations: number;
    connected_locations: number;
  };
  structural_explanation?: string;
}

export interface ScopeOption {
  scope_type: string;
  scope_id: string;
  display_label: string;
  detail?: string;
}

export interface PersonProfile {
  person_id: string;
  canonical_name: string;
  aliases: string[];
  source_provenance: string;
  confidence: number;
  metrics?: {
    degree_centrality: number;
    betweenness_centrality: number;
    pagerank: number;
    raw_degree: number;
  };
  network_breakdown?: {
    connected_crimes: number;
    connected_people: number;
    connected_phones: number;
    connected_vehicles: number;
    connected_organizations: number;
    connected_locations: number;
  };
  structural_explanation?: string;
  crimes: Array<{
    crime_id: string;
    record_id?: string;
    category?: string;
    occurred_at?: string;
    role: string;
    relationship_type: string;
    evidence_excerpt?: string;
  }>;
  phones: Array<{
    phone_id: string;
    normalized_number: string;
    carrier?: string;
    role: string;
    confidence: number;
    metrics?: any;
  }>;
  telecom_summary: {
    total_phones: number;
    total_calls: number;
    total_airtime_seconds: number;
    top_contacts: any[];
  };
  subgraph?: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
}

export type ReviewStatus = "PENDING" | "UNDER_REVIEW" | "VALIDATED" | "REJECTED" | "MODIFIED";

export interface ReviewHistoryItem {
  id: string;
  review_id: string;
  action: string;
  from_status?: string | null;
  to_status: string;
  reviewer_id: string;
  reviewer_display_name?: string | null;
  note?: string | null;
  reason?: string | null;
  metadata_snapshot?: Record<string, any>;
  created_at: string;
}

export interface ReviewItem {
  id: string;
  relationship_ref: string;
  source_entity_type: string;
  source_entity_id: string;
  target_entity_type: string;
  target_entity_id: string;
  relationship_type: string;
  original_relationship_type: string;
  final_relationship_type?: string | null;
  original_confidence: number;
  provenance: string;
  discovery_method?: string | null;
  status: ReviewStatus;
  reviewer_id?: string | null;
  reviewer_display_name?: string | null;
  investigator_note?: string | null;
  rejection_reason?: string | null;
  evidence_count: number;
  version: number;
  created_at: string;
  reviewed_at?: string | null;
  updated_at: string;
}

export interface ReviewDetail extends ReviewItem {
  evidence_snapshot: Array<{
    type?: string;
    id?: string;
    number?: string;
    call_id?: string;
    call_count?: number;
    total_duration?: number;
    excerpt?: string;
    note?: string;
    [key: string]: any;
  }>;
  history_entries: ReviewHistoryItem[];
}

export interface ReviewStats {
  total: number;
  pending: number;
  under_review: number;
  validated: number;
  rejected: number;
  modified: number;
}

// Phase 7: Domain AI Investigation Agent Types
export interface AgentNormalizedEvidence {
  evidence_id: string;
  evidence_type: string;
  source_system: string;
  source_record_id?: string | null;
  source_entity?: string | null;
  target_entity?: string | null;
  relationship?: string | null;
  summary: string;
  confidence: number;
  validation_status: string;
  citation: string;
  tool_used: string;
  metadata?: Record<string, any>;
  timestamp?: string | null;
}

export interface AgentFinding {
  title: string;
  details: string;
  supporting_evidence_ids: string[];
  validation_status: string;
  confidence?: number | null;
}

export interface AgentKeyIndividual {
  person_id: string;
  display_name: string;
  degree_centrality: number;
  betweenness_centrality: number;
  pagerank: number;
  connected_crimes: string[];
  connected_phones: string[];
  validation_status: string;
}

export interface AgentToolTraceItem {
  step: number;
  tool: string;
  purpose: string;
  status: "SUCCESS" | "FAILED" | "SKIPPED";
  duration_ms: number;
  result_count: number;
  error?: string | null;
}

export interface AgentInvestigationResponse {
  investigation_id: string;
  question: string;
  status: string;
  summary: string;
  findings: AgentFinding[];
  key_individuals: AgentKeyIndividual[];
  evidence: AgentNormalizedEvidence[];
  uncertainties: string[];
  limitations: string[];
  tool_trace: AgentToolTraceItem[];
  citations: string[];
  graph_data?: {
    nodes: Array<{ id: string; label: string; type: string; status: string }>;
    links: Array<{ source: string; target: string; relationship: string; status: string }>;
  } | null;
  iterations_count: number;
  total_duration_ms: number;
}

export interface AgentToolDefinition {
  name: string;
  description: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  permission: string;
  timeout_seconds: number;
  max_results: number;
  provenance_type: string;
}

export interface AgentExampleItem {
  title: string;
  scenario: string;
  question: string;
}

// ---------------------------------------------------------------------------
// Phase 8: Unified Investigation Command Center Types
// ---------------------------------------------------------------------------
export interface ExtractedEntitySummary {
  id: string;
  type: "Person" | "Phone" | "Vehicle" | "Weapon" | "Organization" | "Location" | string;
  label: string;
  role?: string | null;
  confidence: number;
  validation_status: string;
}

export interface ConnectedCaseSummary {
  crime_id: string;
  record_id: string;
  category: string;
  location_name: string;
  connection_type: string;
  confidence: number;
  evidence: string;
}

export interface KeyIndividualSummary {
  person_id: string;
  name: string;
  degree_centrality: number;
  betweenness_centrality: number;
  pagerank: number;
  structural_explanation?: string | null;
}

export interface CaseContextBundle {
  case_id: string;
  record_id: string;
  category: string;
  crime_type: string;
  description: string;
  location_name: string;
  latitude?: number | null;
  longitude?: number | null;
  occurred_at?: string | null;
  source: string;
  extracted_people: ExtractedEntitySummary[];
  extracted_phones: ExtractedEntitySummary[];
  extracted_vehicles: ExtractedEntitySummary[];
  extracted_weapons: ExtractedEntitySummary[];
  connected_cases: ConnectedCaseSummary[];
  key_individuals: KeyIndividualSummary[];
  validation_summary: {
    validated: number;
    under_review: number;
    rejected: number;
    modified: number;
  };
  total_evidence_count: number;
}

export interface TimelineEventItem {
  id: string;
  timestamp: string;
  event_type: "CRIME_INCIDENT" | "CDR_COMMUNICATION" | "INVESTIGATOR_DECISION" | "RELATIONSHIP_DISCOVERED" | "AGENT_FINDING" | string;
  source: string;
  title: string;
  description: string;
  entity_id?: string | null;
  entity_name?: string | null;
  entity_type?: string | null;
  validation_status?: string | null;
  citation?: string | null;
  metadata?: Record<string, any> | null;
}

export interface CaseTimelineData {
  case_id: string;
  events: TimelineEventItem[];
  total_events: number;
}

export interface SearchHitItem {
  id: string;
  entity_type: "CRIME" | "PERSON" | "PHONE" | "REVIEW";
  title: string;
  subtitle: string;
  category?: string | null;
  detail?: string | null;
  metadata?: Record<string, any> | null;
}

export interface GlobalSearchResult {
  query: string;
  crimes: SearchHitItem[];
  people: SearchHitItem[];
  phones: SearchHitItem[];
  reviews: SearchHitItem[];
  total_results: number;
}

export interface InvestigationReportData {
  case_id: string;
  record_id: string;
  title: string;
  generated_at: string;
  scope: Record<string, any>;
  executive_summary: string;
  connected_cases: ConnectedCaseSummary[];
  people_findings: Array<Record<string, any>>;
  telecom_findings: Array<Record<string, any>>;
  network_findings: Array<Record<string, any>>;
  timeline: TimelineEventItem[];
  geographic_findings: Array<Record<string, any>>;
  evidence_inventory: Array<Record<string, any>>;
  validation_breakdown: Record<string, number>;
  uncertainties: string[];
  methodology: string[];
  statutory_limitations: string[];
}
