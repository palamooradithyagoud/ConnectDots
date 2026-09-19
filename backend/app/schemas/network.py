"""
Phase 5: Network Intelligence & Key Individual Pydantic Schemas
Defines request and response schemas for key individuals, centrality rankings,
network evidence, and investigation scopes.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CentralityMetrics(BaseModel):
    degree_centrality: float = Field(..., description="Normalized Degree Centrality (0.0 to 1.0)")
    betweenness_centrality: float = Field(..., description="Normalized Betweenness Centrality (0.0 to 1.0)")
    pagerank: float = Field(..., description="PageRank Structural Score")
    raw_degree: int = Field(0, description="Total degree connectivity count")


class NetworkBreakdown(BaseModel):
    connected_crimes: int = 0
    connected_people: int = 0
    connected_phones: int = 0
    connected_vehicles: int = 0
    connected_organizations: int = 0
    connected_locations: int = 0


class KeyIndividualItem(BaseModel):
    person_id: str
    canonical_name: str
    display_name: str
    aliases: List[str] = []
    source_provenance: Optional[str] = "FIR_NARRATIVE"
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
    pagerank: float = 0.0
    raw_degree: int = 0
    metrics: CentralityMetrics
    network_breakdown: NetworkBreakdown
    structural_explanation: Optional[str] = None


class KeyIndividualsListResponse(BaseModel):
    scope_type: str
    scope_id: Optional[str] = None
    sort_by: str
    total: int
    limit: int
    offset: int
    items: List[KeyIndividualItem]
    graph_summary: Dict[str, Any] = {}


class PersonEvidenceItem(BaseModel):
    evidence_type: str
    reference_id: str
    role: str
    relationship: str
    confidence: float
    excerpt: Optional[str] = None
    provenance: str


class PersonEvidenceResponse(BaseModel):
    person_id: str
    evidence: List[PersonEvidenceItem] = []


class PersonCrimeLink(BaseModel):
    crime_id: str
    record_id: Optional[str] = None
    category: Optional[str] = None
    occurred_at: Optional[str] = None
    role: str
    relationship_type: str
    evidence_excerpt: Optional[str] = None


class PersonPhoneLink(BaseModel):
    phone_id: str
    normalized_number: str
    carrier: Optional[str] = None
    role: str
    confidence: float
    metrics: Optional[Dict[str, Any]] = None


class PersonDetailResponse(BaseModel):
    person_id: str
    canonical_name: str
    aliases: List[str] = []
    source_provenance: str = "FIR_NARRATIVE"
    confidence: float = 1.0
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
    pagerank: float = 0.0
    raw_degree: int = 0
    metrics: Optional[CentralityMetrics] = None
    network_breakdown: Optional[NetworkBreakdown] = None
    structural_explanation: Optional[str] = None
    crimes: List[PersonCrimeLink] = []
    associated_crimes: List[PersonCrimeLink] = []
    phones: List[PersonPhoneLink] = []
    associated_phones: List[PersonPhoneLink] = []
    telecom_summary: Dict[str, Any] = {}
    subgraph: Optional[Dict[str, Any]] = None


class ScopeItem(BaseModel):
    scope_type: str
    scope_id: str
    display_label: str
    detail: Optional[str] = None


class ScopeResponse(BaseModel):
    scopes: List[str] = ["global", "crime", "cluster", "person"]
    scope_options: List[ScopeItem] = []
    items: List[ScopeItem] = []
