from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EntityExtractionResult(BaseModel):
    persons: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    weapons: List[str] = Field(default_factory=list)
    vehicles: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    times: List[str] = Field(default_factory=list)
    money: List[str] = Field(default_factory=list)


class ModusOperandiResult(BaseModel):
    pattern: str
    certainty: str  # explicitly_stated, inferred
    matched_text: Optional[str] = None


class NlpAnalysisResponse(BaseModel):
    id: str
    crime_id: str
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    processed_text: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    extracted_weapons: Optional[List[str]] = Field(default_factory=list)
    extracted_vehicles: Optional[List[str]] = Field(default_factory=list)
    extracted_locations: Optional[List[str]] = Field(default_factory=list)
    extracted_persons: Optional[List[str]] = Field(default_factory=list)
    modus_operandi: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    predicted_category: Optional[str] = None
    classification_confidence: Optional[float] = None
    needs_review: bool = False
    embedding_model: Optional[str] = None
    qdrant_point_id: Optional[str] = None
    graph_ready_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NlpBatchProcessRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=500)
    force_reprocess: bool = False


class NlpBatchProcessResponse(BaseModel):
    total_requested: int
    processed_count: int
    failed_count: int
    items: List[Dict[str, Any]]


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language search query")
    category: Optional[str] = Field(None, description="Optional canonical category filter")
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.40, ge=0.0, le=1.0)
    location: Optional[str] = Field(None, description="Optional location filter")


class SemanticSearchResult(BaseModel):
    crime_id: str
    record_id: str
    category: str
    predicted_category: Optional[str] = None
    similarity_score: float
    location: str
    occurred_at: Optional[str] = None
    description: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    weapons: Optional[List[str]] = Field(default_factory=list)
    vehicles: Optional[List[str]] = Field(default_factory=list)
    modus_operandi: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class SemanticSearchResponse(BaseModel):
    query: str
    total_results: int
    similarity_threshold: float
    results: List[SemanticSearchResult]


class NlpStatsResponse(BaseModel):
    total_crimes: int
    nlp_processed: int
    nlp_pending: int
    nlp_failed: int
    needs_review_count: int
    average_confidence: float
    qdrant_indexed_vectors: int
    predicted_category_distribution: Dict[str, int]
    embedding_model: str
