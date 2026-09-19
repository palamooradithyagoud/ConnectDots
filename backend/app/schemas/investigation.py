"""
Phase 4 & Phase 8: Investigation Intelligence Pydantic Schemas
Provides data contracts for Graph RAG, Unified Case Context, Multi-Source Timeline,
Global Search, and Comprehensive Investigation Reports.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Phase 4 Schemas: Grounded Graph RAG
# ---------------------------------------------------------------------------
class InvestigationQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Natural-language crime investigation question")


class Citation(BaseModel):
    claim: str
    evidence: List[str] = Field(default_factory=list, description="Authoritative Crime IDs supporting this claim")


class RelatedCrime(BaseModel):
    crime_id: str
    record_id: Optional[str] = None
    category: Optional[str] = None
    connection_type: str
    confidence_type: Optional[str] = "derived"
    confidence: Optional[float] = None
    similarity: Optional[float] = None


class InvestigationQueryResponse(BaseModel):
    answer: str
    structured_sections: Dict[str, str] = Field(
        default_factory=dict,
        description="Structured sections: summary, connections, evidence, uncertainty"
    )
    citations: List[Citation] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    graph_paths: List[Dict[str, Any]] = Field(default_factory=list)
    graph_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    related_crimes: List[RelatedCrime] = Field(default_factory=list)
    confidence: float = 0.85
    meta: Dict[str, Any] = Field(default_factory=dict)


class InvestigationExamplesResponse(BaseModel):
    examples: List[str]


# ---------------------------------------------------------------------------
# Phase 8 Schemas: Unified Investigation Command Center
# ---------------------------------------------------------------------------
class ExtractedEntitySummary(BaseModel):
    id: str
    type: str  # "Person", "Phone", "Vehicle", "Weapon", "Organization", "Location"
    label: str
    role: Optional[str] = None
    confidence: float = 1.0
    validation_status: str = "AI_DERIVED"


class ConnectedCaseSummary(BaseModel):
    crime_id: str
    record_id: str
    category: str
    location_name: str
    connection_type: str
    confidence: float
    evidence: str


class KeyIndividualSummary(BaseModel):
    person_id: str
    name: str
    degree_centrality: float
    betweenness_centrality: float
    pagerank: float
    structural_explanation: Optional[str] = None


class CaseContextResponse(BaseModel):
    case_id: str
    record_id: str
    category: str
    crime_type: str
    description: str
    location_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    occurred_at: Optional[str] = None
    source: str
    extracted_people: List[ExtractedEntitySummary] = Field(default_factory=list)
    extracted_phones: List[ExtractedEntitySummary] = Field(default_factory=list)
    extracted_vehicles: List[ExtractedEntitySummary] = Field(default_factory=list)
    extracted_weapons: List[ExtractedEntitySummary] = Field(default_factory=list)
    connected_cases: List[ConnectedCaseSummary] = Field(default_factory=list)
    key_individuals: List[KeyIndividualSummary] = Field(default_factory=list)
    validation_summary: Dict[str, int] = Field(
        default_factory=lambda: {"validated": 0, "under_review": 0, "rejected": 0, "modified": 0}
    )
    total_evidence_count: int = 0


class TimelineEvent(BaseModel):
    id: str
    timestamp: str  # ISO-8601 format
    event_type: str  # "CRIME_INCIDENT", "CDR_COMMUNICATION", "INVESTIGATOR_DECISION", "RELATIONSHIP_DISCOVERED", "AGENT_FINDING"
    source: str      # "POSTGRESQL", "CDR", "REVIEW_QUEUE", "AI_AGENT"
    title: str
    description: str
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None  # "Crime", "Person", "Phone"
    validation_status: Optional[str] = None  # "VALIDATED", "AI_DERIVED", "REJECTED", "MODIFIED"
    citation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CaseTimelineResponse(BaseModel):
    case_id: str
    events: List[TimelineEvent] = Field(default_factory=list)
    total_events: int = 0


class SearchItem(BaseModel):
    id: str
    entity_type: str  # "CRIME", "PERSON", "PHONE", "REVIEW"
    title: str
    subtitle: str
    category: Optional[str] = None
    detail: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GlobalSearchResponse(BaseModel):
    query: str
    crimes: List[SearchItem] = Field(default_factory=list)
    people: List[SearchItem] = Field(default_factory=list)
    phones: List[SearchItem] = Field(default_factory=list)
    reviews: List[SearchItem] = Field(default_factory=list)
    total_results: int = 0


class InvestigationReportResponse(BaseModel):
    case_id: str
    record_id: str
    title: str
    generated_at: str
    scope: Dict[str, Any]
    executive_summary: str
    connected_cases: List[ConnectedCaseSummary] = Field(default_factory=list)
    people_findings: List[Dict[str, Any]] = Field(default_factory=list)
    telecom_findings: List[Dict[str, Any]] = Field(default_factory=list)
    network_findings: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    geographic_findings: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_inventory: List[Dict[str, Any]] = Field(default_factory=list)
    validation_breakdown: Dict[str, int] = Field(default_factory=dict)
    uncertainties: List[str] = Field(default_factory=list)
    methodology: List[str] = Field(default_factory=list)
    statutory_limitations: List[str] = Field(default_factory=list)
