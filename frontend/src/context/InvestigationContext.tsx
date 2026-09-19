"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import {
  GraphNode,
  GraphEdge,
  CaseContextBundle,
  TimelineEventItem,
  AgentInvestigationResponse,
  AgentNormalizedEvidence,
  InvestigationReportData,
} from "@/types/investigation";

interface InvestigationContextType {
  // Case Scope State
  selectedCaseId: string;
  caseContext: CaseContextBundle | null;
  loadingCase: boolean;
  caseError: string | null;

  // Graph Selection State
  selectedNodeId: string | null;
  selectedEdge: GraphEdge | null;
  selectedPersonId: string | null;
  selectedPhoneId: string | null;
  selectedCrimeId: string | null;
  highlightedNodeIds: Set<string>;
  highlightedEdgeIds: Set<string>;

  // Graph Data State
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  loadingGraph: boolean;

  // Agent State
  activeAgentResult: AgentInvestigationResponse | null;
  runningAgent: boolean;
  agentError: string | null;

  // Timeline State
  timelineEvents: TimelineEventItem[];
  loadingTimeline: boolean;
  timelineFilter: { eventType?: string; entityId?: string };

  // Evidence & Review State
  selectedEvidence: AgentNormalizedEvidence | null;
  activeReviewId: string | null;
  isAuditHistoryOpen: boolean;

  // Modals
  isReportModalOpen: boolean;
  isSearchModalOpen: boolean;
  activeReport: InvestigationReportData | null;
  generatingReport: boolean;

  // Actions
  loadCase: (caseId: string) => Promise<void>;
  selectNode: (node: GraphNode | null) => void;
  selectEdge: (edge: GraphEdge | null) => void;
  selectPerson: (personId: string) => void;
  selectPhone: (phoneId: string) => void;
  selectCrime: (crimeId: string) => void;
  selectEvidence: (ev: AgentNormalizedEvidence | null) => void;
  applyAgentResult: (result: AgentInvestigationResponse) => void;
  clearHighlights: () => void;
  setTimelineFilter: (filter: { eventType?: string; entityId?: string }) => void;
  runAgentInvestigation: (question: string) => Promise<void>;
  generateReport: () => Promise<void>;
  openReportModal: () => void;
  closeReportModal: () => void;
  openSearchModal: () => void;
  closeSearchModal: () => void;
  openAuditHistory: (reviewId: string) => void;
  closeAuditHistory: () => void;
  refreshWorkspace: () => Promise<void>;
}

const InvestigationContext = createContext<InvestigationContextType | undefined>(undefined);

export function InvestigationProvider({ children }: { children: ReactNode }) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // Case State
  const [selectedCaseId, setSelectedCaseId] = useState<string>("1042");
  const [caseContext, setCaseContext] = useState<CaseContextBundle | null>(null);
  const [loadingCase, setLoadingCase] = useState<boolean>(false);
  const [caseError, setCaseError] = useState<string | null>(null);

  // Graph Selection
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null);
  const [selectedPhoneId, setSelectedPhoneId] = useState<string | null>(null);
  const [selectedCrimeId, setSelectedCrimeId] = useState<string | null>(null);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState<Set<string>>(new Set());
  const [highlightedEdgeIds, setHighlightedEdgeIds] = useState<Set<string>>(new Set());

  // Graph Canvas Data
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [loadingGraph, setLoadingGraph] = useState<boolean>(false);

  // Agent State
  const [activeAgentResult, setActiveAgentResult] = useState<AgentInvestigationResponse | null>(null);
  const [runningAgent, setRunningAgent] = useState<boolean>(false);
  const [agentError, setAgentError] = useState<string | null>(null);

  // Timeline State
  const [timelineEvents, setTimelineEvents] = useState<TimelineEventItem[]>([]);
  const [loadingTimeline, setLoadingTimeline] = useState<boolean>(false);
  const [timelineFilter, setTimelineFilterState] = useState<{ eventType?: string; entityId?: string }>({});

  // Evidence & Review
  const [selectedEvidence, setSelectedEvidence] = useState<AgentNormalizedEvidence | null>(null);
  const [activeReviewId, setActiveReviewId] = useState<string | null>(null);
  const [isAuditHistoryOpen, setIsAuditHistoryOpen] = useState<boolean>(false);

  // Modals & Reports
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);
  const [isSearchModalOpen, setIsSearchModalOpen] = useState<boolean>(false);
  const [activeReport, setActiveReport] = useState<InvestigationReportData | null>(null);
  const [generatingReport, setGeneratingReport] = useState<boolean>(false);

  // Load Graph Subgraph for Crime
  const fetchGraphData = useCallback(async (caseId: string) => {
    setLoadingGraph(true);
    try {
      const res = await fetch(`${apiUrl}/graph/crimes/${caseId}?depth=2&max_nodes=50`);
      if (res.ok) {
        const data = await res.json();
        setGraphNodes(data.nodes || []);
        setGraphEdges(data.edges || []);
      } else {
        // Fallback to person network subgraph if crime graph is empty
        const netRes = await fetch(`${apiUrl}/network/crimes/${caseId}/subgraph?max_hops=2&max_nodes=50`);
        if (netRes.ok) {
          const netData = await netRes.json();
          setGraphNodes(netData.nodes || []);
          setGraphEdges(netData.edges || []);
        }
      }
    } catch (err) {
      console.warn("Could not fetch graph neighborhood:", err);
    } finally {
      setLoadingGraph(false);
    }
  }, [apiUrl]);

  // Load Timeline for Case
  const fetchTimeline = useCallback(async (caseId: string, filter?: { eventType?: string; entityId?: string }) => {
    setLoadingTimeline(true);
    try {
      const params = new URLSearchParams();
      if (filter?.eventType) params.append("event_type", filter.eventType);
      if (filter?.entityId) params.append("entity_id", filter.entityId);
      params.append("limit", "50");

      const res = await fetch(`${apiUrl}/investigation/case/${caseId}/timeline?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setTimelineEvents(data.events || []);
      }
    } catch (err) {
      console.warn("Could not fetch timeline:", err);
    } finally {
      setLoadingTimeline(false);
    }
  }, [apiUrl]);

  // Load Complete Case Context
  const loadCase = useCallback(async (caseId: string) => {
    if (!caseId) return;
    setLoadingCase(true);
    setCaseError(null);
    setSelectedCaseId(caseId);
    setSelectedNodeId(null);
    setSelectedEdge(null);
    setSelectedPersonId(null);
    setSelectedPhoneId(null);
    setSelectedCrimeId(null);
    setHighlightedNodeIds(new Set());
    setHighlightedEdgeIds(new Set());

    try {
      const res = await fetch(`${apiUrl}/investigation/case/${caseId}/context`);
      if (!res.ok) {
        // If not found by custom ID, try searching first crime in database
        throw new Error(`Case '${caseId}' context could not be loaded.`);
      }
      const data: CaseContextBundle = await res.json();
      setCaseContext(data);

      // Concurrently load Graph & Timeline
      await Promise.all([
        fetchGraphData(data.case_id || caseId),
        fetchTimeline(data.case_id || caseId, timelineFilter),
      ]);
    } catch (err: any) {
      setCaseError(err.message || "Failed to load case context.");
      // Still attempt to load timeline and graph
      fetchTimeline(caseId, timelineFilter);
      fetchGraphData(caseId);
    } finally {
      setLoadingCase(false);
    }
  }, [apiUrl, fetchGraphData, fetchTimeline, timelineFilter]);

  // Initialize with Default Case on mount
  useEffect(() => {
    loadCase(selectedCaseId);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Node Selection Handlers
  const selectNode = useCallback((node: GraphNode | null) => {
    if (!node) {
      setSelectedNodeId(null);
      setSelectedPersonId(null);
      setSelectedPhoneId(null);
      setSelectedCrimeId(null);
      return;
    }
    setSelectedNodeId(node.id);
    setSelectedEdge(null);

    if (node.label === "Crime") {
      const cId = node.properties?.record_id || node.id.replace("crime:", "");
      setSelectedCrimeId(cId);
      setSelectedPersonId(null);
      setSelectedPhoneId(null);
    } else if (node.label === "Person") {
      setSelectedPersonId(node.id.replace("person:", ""));
      setSelectedCrimeId(null);
      setSelectedPhoneId(null);
    } else if (node.label === "Phone") {
      setSelectedPhoneId(node.id.replace("phone:", ""));
      setSelectedCrimeId(null);
      setSelectedPersonId(null);
    }
  }, []);

  const selectEdge = useCallback((edge: GraphEdge | null) => {
    setSelectedEdge(edge);
    if (edge) {
      setSelectedNodeId(null);
    }
  }, []);

  const selectPerson = useCallback((personId: string) => {
    setSelectedPersonId(personId);
    setSelectedNodeId(personId.startsWith("person:") ? personId : `person:${personId}`);
    setSelectedEdge(null);
  }, []);

  const selectPhone = useCallback((phoneId: string) => {
    setSelectedPhoneId(phoneId);
    setSelectedNodeId(phoneId.startsWith("phone:") ? phoneId : `phone:${phoneId}`);
    setSelectedEdge(null);
  }, []);

  const selectCrime = useCallback((crimeId: string) => {
    setSelectedCrimeId(crimeId);
    setSelectedNodeId(crimeId.startsWith("crime:") ? crimeId : `crime:${crimeId}`);
    setSelectedEdge(null);
  }, []);

  const selectEvidence = useCallback((ev: AgentNormalizedEvidence | null) => {
    setSelectedEvidence(ev);
  }, []);

  // Agent Investigation Orchestration
  const applyAgentResult = useCallback((result: AgentInvestigationResponse) => {
    setActiveAgentResult(result);

    // Extract all returned entity IDs to highlight on the graph canvas
    const highlightedNodes = new Set<string>();
    const highlightedEdges = new Set<string>();

    if (result.evidence) {
      result.evidence.forEach((ev) => {
        if (ev.source_entity) highlightedNodes.add(ev.source_entity);
        if (ev.target_entity) highlightedNodes.add(ev.target_entity);
        if (ev.source_record_id) highlightedNodes.add(ev.source_record_id);
      });
    }

    if (result.key_individuals) {
      result.key_individuals.forEach((ki) => {
        highlightedNodes.add(ki.person_id);
        if (ki.connected_crimes) {
          ki.connected_crimes.forEach((c) => highlightedNodes.add(c));
        }
        if (ki.connected_phones) {
          ki.connected_phones.forEach((p) => highlightedNodes.add(p));
        }
      });
    }

    if (result.graph_data?.nodes) {
      result.graph_data.nodes.forEach((n) => highlightedNodes.add(n.id));
    }
    if (result.graph_data?.links) {
      result.graph_data.links.forEach((l) => {
        highlightedNodes.add(l.source);
        highlightedNodes.add(l.target);
        highlightedEdges.add(`${l.source}->${l.relationship}->${l.target}`);
      });
    }

    setHighlightedNodeIds(highlightedNodes);
    setHighlightedEdgeIds(highlightedEdges);

    // Inject agent finding events into current timeline
    const agentTimelineEvents: TimelineEventItem[] = (result.findings || []).map((f, idx) => ({
      id: `agent-find-${idx}`,
      timestamp: new Date().toISOString(),
      event_type: "AGENT_FINDING",
      source: "AI_AGENT",
      title: `AI Finding: ${f.title}`,
      description: f.details,
      validation_status: f.validation_status,
      citation: f.supporting_evidence_ids[0] || "AI-DERIVED",
    }));

    setTimelineEvents((prev) => [...agentTimelineEvents, ...prev]);
  }, []);

  const clearHighlights = useCallback(() => {
    setHighlightedNodeIds(new Set());
    setHighlightedEdgeIds(new Set());
  }, []);

  const setTimelineFilter = useCallback((filter: { eventType?: string; entityId?: string }) => {
    setTimelineFilterState(filter);
    fetchTimeline(selectedCaseId, filter);
  }, [fetchTimeline, selectedCaseId]);

  const runAgentInvestigation = useCallback(async (question: string) => {
    if (!question.trim()) return;
    setRunningAgent(true);
    setAgentError(null);

    try {
      const res = await fetch(`${apiUrl}/agent/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          scope: {
            crime_id: selectedCrimeId || selectedCaseId,
            person_id: selectedPersonId,
            phone_number: selectedPhoneId,
          },
        }),
      });

      if (!res.ok) {
        throw new Error("Domain AI agent investigation request failed.");
      }

      const data: AgentInvestigationResponse = await res.json();
      applyAgentResult(data);
    } catch (err: any) {
      setAgentError(err.message || "Failed to execute agent investigation.");
    } finally {
      setRunningAgent(false);
    }
  }, [apiUrl, selectedCrimeId, selectedCaseId, selectedPersonId, selectedPhoneId, applyAgentResult]);

  // Report Generation
  const generateReport = useCallback(async () => {
    setGeneratingReport(true);
    try {
      const res = await fetch(`${apiUrl}/investigation/case/${selectedCaseId}/report`);
      if (res.ok) {
        const data: InvestigationReportData = await res.json();
        setActiveReport(data);
        setIsReportModalOpen(true);
      }
    } catch (err) {
      console.warn("Could not generate report:", err);
    } finally {
      setGeneratingReport(false);
    }
  }, [apiUrl, selectedCaseId]);

  const refreshWorkspace = useCallback(async () => {
    await loadCase(selectedCaseId);
  }, [loadCase, selectedCaseId]);

  return (
    <InvestigationContext.Provider
      value={{
        selectedCaseId,
        caseContext,
        loadingCase,
        caseError,
        selectedNodeId,
        selectedEdge,
        selectedPersonId,
        selectedPhoneId,
        selectedCrimeId,
        highlightedNodeIds,
        highlightedEdgeIds,
        graphNodes,
        graphEdges,
        loadingGraph,
        activeAgentResult,
        runningAgent,
        agentError,
        timelineEvents,
        loadingTimeline,
        timelineFilter,
        selectedEvidence,
        activeReviewId,
        isAuditHistoryOpen,
        isReportModalOpen,
        isSearchModalOpen,
        activeReport,
        generatingReport,
        loadCase,
        selectNode,
        selectEdge,
        selectPerson,
        selectPhone,
        selectCrime,
        selectEvidence,
        applyAgentResult,
        clearHighlights,
        setTimelineFilter,
        runAgentInvestigation,
        generateReport,
        openReportModal: () => setIsReportModalOpen(true),
        closeReportModal: () => setIsReportModalOpen(false),
        openSearchModal: () => setIsSearchModalOpen(true),
        closeSearchModal: () => setIsSearchModalOpen(false),
        openAuditHistory: (reviewId: string) => {
          setActiveReviewId(reviewId);
          setIsAuditHistoryOpen(true);
        },
        closeAuditHistory: () => {
          setActiveReviewId(null);
          setIsAuditHistoryOpen(false);
        },
        refreshWorkspace,
      }}
    >
      {children}
    </InvestigationContext.Provider>
  );
}

export function useInvestigation() {
  const context = useContext(InvestigationContext);
  if (!context) {
    throw new Error("useInvestigation must be used within an InvestigationProvider");
  }
  return context;
}
