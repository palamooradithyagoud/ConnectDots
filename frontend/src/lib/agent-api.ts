const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface InvestigationFinding {
  title: string;
  details: string;
  supporting_evidence_ids?: string[];
  validation_status?: string;
  confidence?: number;
}

export interface KeyIndividualFinding {
  person_id: string;
  display_name: string;
  degree_centrality?: number;
  betweenness_centrality?: number;
  pagerank?: number;
  connected_crimes?: string[];
  connected_phones?: string[];
  validation_status?: string;
}

export interface NormalizedEvidence {
  evidence_id: string;
  evidence_type: string;
  source_system: string;
  source_record_id?: string;
  source_entity?: string;
  target_entity?: string;
  relationship?: string;
  summary: string;
  confidence?: number;
  validation_status?: string;
  citation: string;
  tool_used: string;
  timestamp?: string;
}

export interface ToolTraceItem {
  step: number;
  tool: string;
  purpose: string;
  status: string;
  duration_ms: number;
  result_count: number;
  error?: string;
}

export interface AgentInvestigationResponse {
  investigation_id: string;
  question: string;
  status: "COMPLETED" | "FAILED" | "TIMEOUT" | "PARTIAL";
  summary: string;
  findings: InvestigationFinding[];
  key_individuals: KeyIndividualFinding[];
  evidence: NormalizedEvidence[];
  uncertainties: string[];
  limitations: string[];
  tool_trace: ToolTraceItem[];
  citations: string[];
  graph_data?: any;
  total_duration_ms: number;
}

export interface AgentExampleItem {
  title: string;
  scenario: string;
  question: string;
}

export interface AgentToolDefinition {
  name: string;
  description: string;
  permission: string;
  timeout_seconds: number;
  max_results: number;
}

export async function executeAgentInvestigation(
  question: string,
  scope?: Record<string, any>
): Promise<AgentInvestigationResponse> {
  const res = await fetch(`${API_BASE_URL}/agent/investigate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      scope: scope || null,
    }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Investigation request failed (${res.status}): ${errorText}`);
  }

  return res.json();
}

export async function fetchAgentExamples(): Promise<AgentExampleItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/agent/examples`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.examples || [];
  } catch (err) {
    console.warn("Failed to fetch agent examples:", err);
    return [];
  }
}

export async function fetchAgentTools(): Promise<AgentToolDefinition[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/agent/tools`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.tools || [];
  } catch (err) {
    console.warn("Failed to fetch agent tools:", err);
    return [];
  }
}
