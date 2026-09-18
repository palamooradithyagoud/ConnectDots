"""
Phase 4: Investigation Intelligence Pydantic Schemas
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


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
