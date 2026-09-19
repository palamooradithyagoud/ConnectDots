"""
Phase 7: Domain AI Investigation Agent — Data Contracts & Models
Defines typed contracts for tool definitions, tool executions, investigation plans,
normalized evidence, validation tracking, and final investigation reports.
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class QueryCategory(str, Enum):
    CASE_LOOKUP = "CASE_LOOKUP"
    ENTITY_LOOKUP = "ENTITY_LOOKUP"
    CROSS_CASE = "CROSS_CASE"
    TELECOM = "TELECOM"
    NETWORK = "NETWORK"
    KEY_INDIVIDUAL = "KEY_INDIVIDUAL"
    PATTERN = "PATTERN"
    ANOMALY = "ANOMALY"
    CLUSTER = "CLUSTER"
    SEMANTIC = "SEMANTIC"
    EVIDENCE = "EVIDENCE"
    TIMELINE = "TIMELINE"
    MIXED_INVESTIGATION = "MIXED_INVESTIGATION"


class InvestigationScope(BaseModel):
    crime_id: Optional[str] = None
    entity_id: Optional[str] = None
    phone_number: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    max_hops: int = Field(default=2, ge=1, le=3)


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    permission: str = "READ_ONLY"
    timeout_seconds: float = 10.0
    max_results: int = 50
    provenance_type: str = "SYSTEM"


class ToolCall(BaseModel):
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""


class ToolResult(BaseModel):
    tool: str
    success: bool
    data: Any = None
    evidence_count: int = 0
    duration_ms: float = 0.0
    error: Optional[str] = None
    truncated: bool = False
    provenance: List[str] = Field(default_factory=list)


class NormalizedEvidence(BaseModel):
    evidence_id: str
    evidence_type: str  # CRIME, PERSON, PHONE, CDR, GRAPH_EDGE, PATTERN, ANOMALY, CLUSTER, REVIEW
    source_system: str  # POSTGRESQL, NEO4J, QDRANT, ML_ENGINE, REVIEW_QUEUE
    source_record_id: Optional[str] = None
    source_entity: Optional[str] = None
    target_entity: Optional[str] = None
    relationship: Optional[str] = None
    summary: str
    confidence: float = 1.0
    validation_status: str = "AI_DERIVED"  # VALIDATED, AI_DERIVED, UNDER_REVIEW, REJECTED
    citation: str
    tool_used: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = None


class InvestigationPlan(BaseModel):
    goal: str
    category: QueryCategory = QueryCategory.MIXED_INVESTIGATION
    scope: InvestigationScope = Field(default_factory=InvestigationScope)
    steps: List[ToolCall] = Field(default_factory=list)
    rationale: str = ""


class InvestigationFinding(BaseModel):
    title: str
    details: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    validation_status: str = "AI_DERIVED"
    confidence: Optional[float] = None


class KeyIndividualFinding(BaseModel):
    person_id: str
    display_name: str
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
    pagerank: float = 0.0
    connected_crimes: List[str] = Field(default_factory=list)
    connected_phones: List[str] = Field(default_factory=list)
    validation_status: str = "AI_DERIVED"


class ToolTraceItem(BaseModel):
    step: int
    tool: str
    purpose: str
    status: str  # SUCCESS, FAILED, SKIPPED
    duration_ms: float
    result_count: int
    error: Optional[str] = None


class AgentInvestigationResponse(BaseModel):
    investigation_id: str
    question: str
    status: str = "COMPLETED"  # COMPLETED, FAILED, TIMEOUT, PARTIAL
    summary: str
    findings: List[InvestigationFinding] = Field(default_factory=list)
    key_individuals: List[KeyIndividualFinding] = Field(default_factory=list)
    evidence: List[NormalizedEvidence] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    tool_trace: List[ToolTraceItem] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    graph_data: Optional[Dict[str, Any]] = None
    iterations_count: int = 1
    total_duration_ms: float = 0.0
