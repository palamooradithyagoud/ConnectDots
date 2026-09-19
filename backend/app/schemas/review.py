"""
Phase 6: Investigator Validation & Review Schemas
Pydantic schemas for review queue items, detailed dossiers, actions, and audit trail entries.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ReviewHistoryItem(BaseModel):
    id: str
    review_id: str
    action: str
    from_status: Optional[str] = None
    to_status: str
    reviewer_id: str
    reviewer_display_name: Optional[str] = None
    note: Optional[str] = None
    reason: Optional[str] = None
    metadata_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewItem(BaseModel):
    id: str
    relationship_ref: str
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    relationship_type: str
    original_relationship_type: str
    final_relationship_type: Optional[str] = None
    original_confidence: float
    provenance: str
    discovery_method: Optional[str] = None
    status: str
    reviewer_id: Optional[str] = None
    reviewer_display_name: Optional[str] = None
    investigator_note: Optional[str] = None
    rejection_reason: Optional[str] = None
    evidence_count: int = 0
    version: int = 1
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewDetailResponse(BaseModel):
    id: str
    relationship_ref: str
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    relationship_type: str
    original_relationship_type: str
    final_relationship_type: Optional[str] = None
    original_confidence: float
    provenance: str
    discovery_method: Optional[str] = None
    status: str
    reviewer_id: Optional[str] = None
    reviewer_display_name: Optional[str] = None
    investigator_note: Optional[str] = None
    rejection_reason: Optional[str] = None
    evidence_snapshot: List[Any] = Field(default_factory=list)
    version: int = 1
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    updated_at: datetime
    history_entries: List[ReviewHistoryItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[ReviewItem]


class ValidateActionRequest(BaseModel):
    reviewer_id: Optional[str] = Field("investigator:lead", description="Investigator identifier")
    reviewer_display_name: Optional[str] = Field("Lead Investigator", description="Display name")
    note: Optional[str] = Field(None, description="Investigator rationale or corroboration notes")
    expected_version: Optional[int] = Field(None, description="Expected concurrency version for conflict detection")


class RejectActionRequest(BaseModel):
    reason: str = Field(..., description="Mandatory rationale for rejection")
    reviewer_id: Optional[str] = Field("investigator:lead", description="Investigator identifier")
    reviewer_display_name: Optional[str] = Field("Lead Investigator", description="Display name")
    note: Optional[str] = Field(None, description="Detailed explanation or context")
    expected_version: Optional[int] = Field(None, description="Expected concurrency version for conflict detection")


class ModifyActionRequest(BaseModel):
    new_relationship_type: str = Field(..., description="Supported alternative relationship type")
    reviewer_id: Optional[str] = Field("investigator:lead", description="Investigator identifier")
    reviewer_display_name: Optional[str] = Field("Lead Investigator", description="Display name")
    note: Optional[str] = Field(None, description="Explanation for modification")
    expected_version: Optional[int] = Field(None, description="Expected concurrency version for conflict detection")


class ReopenActionRequest(BaseModel):
    reason: Optional[str] = Field("New investigative evidence surfaced", description="Reason for reopening review")
    reviewer_id: Optional[str] = Field("investigator:lead", description="Investigator identifier")
    reviewer_display_name: Optional[str] = Field("Lead Investigator", description="Display name")


class AddNoteRequest(BaseModel):
    note: str = Field(..., description="Investigator note content")
    reviewer_id: Optional[str] = Field("investigator:lead", description="Investigator identifier")
    reviewer_display_name: Optional[str] = Field("Lead Investigator", description="Display name")


class ReviewStatsResponse(BaseModel):
    total: int
    pending: int
    under_review: int
    validated: int
    rejected: int
    modified: int
