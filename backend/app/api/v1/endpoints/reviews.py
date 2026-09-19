"""
Phase 6: Human-in-the-Loop Investigator Review Endpoints
Provides REST APIs for inspecting, validating, rejecting, modifying, and auditing
AI-derived relationships.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.review import InvestigationRelationshipReview, InvestigationReviewHistory
from app.services.review_service import ReviewService, ConcurrencyConflictError
from app.schemas.review import (
    ReviewItem,
    ReviewDetailResponse,
    ReviewListResponse,
    ValidateActionRequest,
    RejectActionRequest,
    ModifyActionRequest,
    ReopenActionRequest,
    AddNoteRequest,
    ReviewHistoryItem,
    ReviewStatsResponse,
)

router = APIRouter()
logger = logging.getLogger("connectdots_reviews_api")


def _to_review_item(r: InvestigationRelationshipReview) -> ReviewItem:
    evidence = r.evidence_snapshot if isinstance(r.evidence_snapshot, list) else []
    return ReviewItem(
        id=r.id,
        relationship_ref=r.relationship_ref,
        source_entity_type=r.source_entity_type,
        source_entity_id=r.source_entity_id,
        target_entity_type=r.target_entity_type,
        target_entity_id=r.target_entity_id,
        relationship_type=r.relationship_type,
        original_relationship_type=r.original_relationship_type,
        final_relationship_type=r.final_relationship_type,
        original_confidence=r.original_confidence,
        provenance=r.provenance,
        discovery_method=r.discovery_method,
        status=r.status,
        reviewer_id=r.reviewer_id,
        reviewer_display_name=r.reviewer_display_name,
        investigator_note=r.investigator_note,
        rejection_reason=r.rejection_reason,
        evidence_count=len(evidence),
        version=r.version,
        created_at=r.created_at,
        reviewed_at=r.reviewed_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=ReviewListResponse, summary="List Review Queue Items")
def list_reviews(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, UNDER_REVIEW, VALIDATED, REJECTED, MODIFIED, or ALL"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type (e.g. SHARES_PHONE)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum original AI confidence"),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum original AI confidence"),
    search: Optional[str] = Query(None, description="Search by entity identifier or note keywords"),
    sort_by: str = Query("created_at", description="Sort field: created_at, original_confidence, updated_at"),
    sort_desc: bool = Query(True, description="Sort descending if true"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of AI-derived relationships requiring human investigator review.
    """
    res = ReviewService.get_reviews(
        db=db,
        status=status,
        relationship_type=relationship_type,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc,
        page=page,
        page_size=page_size
    )

    items = [_to_review_item(r) for r in res["items"]]
    return ReviewListResponse(
        total=res["total"],
        page=res["page"],
        page_size=res["page_size"],
        total_pages=res["total_pages"],
        items=items
    )


@router.get("/stats", response_model=ReviewStatsResponse, summary="Get Review Queue Statistics")
def get_review_stats(db: Session = Depends(get_db)):
    """
    Returns status counts across the investigator validation lifecycle.
    """
    stats = ReviewService.get_review_stats(db)
    return ReviewStatsResponse(
        total=stats.get("total", 0),
        pending=stats.get("pending", 0),
        under_review=stats.get("under_review", 0),
        validated=stats.get("validated", 0),
        rejected=stats.get("rejected", 0),
        modified=stats.get("modified", 0),
    )


@router.get("/supported-types", summary="Get Supported Modification Relationship Types")
def get_supported_types():
    """
    Returns the whitelist of valid domain relationship types for investigator modifications.
    """
    return {
        "supported_types": sorted(list(ReviewService.ALLOWED_RELATIONSHIP_TYPES)),
        "symmetric_types": sorted(list(ReviewService.SYMMETRIC_RELATIONSHIPS))
    }


@router.post("/populate", summary="Populate Queue From Graph Relationships")
def populate_queue_from_graph(db: Session = Depends(get_db)):
    """
    Scans derived relationships in the knowledge graph and seeds pending items into the review queue.
    """
    return ReviewService.populate_queue_from_graph(db)


@router.get("/{review_id}", response_model=ReviewDetailResponse, summary="Get Review Dossier")
def get_review_detail(review_id: str, db: Session = Depends(get_db)):
    """
    Returns complete details of a review item including full evidence snapshot and audit history.
    """
    review = db.query(InvestigationRelationshipReview).filter(
        InvestigationRelationshipReview.id == review_id
    ).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review '{review_id}' not found.")

    item_base = _to_review_item(review)
    history = [
        ReviewHistoryItem(
            id=h.id,
            review_id=h.review_id,
            action=h.action,
            from_status=h.from_status,
            to_status=h.to_status,
            reviewer_id=h.reviewer_id,
            reviewer_display_name=h.reviewer_display_name,
            note=h.note,
            reason=h.reason,
            metadata_snapshot=h.metadata_snapshot or {},
            created_at=h.created_at
        ) for h in review.history_entries
    ]

    return ReviewDetailResponse(
        **item_base.model_dump(),
        evidence_snapshot=review.evidence_snapshot or [],
        history_entries=history
    )


@router.get("/{review_id}/evidence", summary="Get Review Evidence Snapshot")
def get_review_evidence(review_id: str, db: Session = Depends(get_db)):
    """
    Returns supporting evidence citations (case files, CDR logs, co-occurrences) for a relationship.
    """
    review = db.query(InvestigationRelationshipReview).filter(
        InvestigationRelationshipReview.id == review_id
    ).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review '{review_id}' not found.")

    return {
        "review_id": review.id,
        "relationship_ref": review.relationship_ref,
        "provenance": review.provenance,
        "discovery_method": review.discovery_method,
        "confidence": review.original_confidence,
        "evidence": review.evidence_snapshot or []
    }


@router.get("/{review_id}/history", response_model=List[ReviewHistoryItem], summary="Get Review Audit History")
def get_review_history(review_id: str, db: Session = Depends(get_db)):
    """
    Returns the append-only audit trail for this relationship review.
    """
    histories = db.query(InvestigationReviewHistory).filter(
        InvestigationReviewHistory.review_id == review_id
    ).order_by(InvestigationReviewHistory.created_at.asc()).all()

    return [
        ReviewHistoryItem(
            id=h.id,
            review_id=h.review_id,
            action=h.action,
            from_status=h.from_status,
            to_status=h.to_status,
            reviewer_id=h.reviewer_id,
            reviewer_display_name=h.reviewer_display_name,
            note=h.note,
            reason=h.reason,
            metadata_snapshot=h.metadata_snapshot or {},
            created_at=h.created_at
        ) for h in histories
    ]


@router.post("/{review_id}/validate", response_model=ReviewDetailResponse, summary="Validate Relationship")
def validate_relationship(
    review_id: str,
    body: ValidateActionRequest,
    db: Session = Depends(get_db)
):
    """
    Validates an AI-derived relationship after investigator inspection.
    Transactionally marks status as VALIDATED and updates knowledge graph.
    """
    try:
        updated = ReviewService.validate_relationship(
            db=db,
            review_id=review_id,
            reviewer_id=body.reviewer_id or "investigator:lead",
            reviewer_display_name=body.reviewer_display_name or "Lead Investigator",
            note=body.note,
            expected_version=body.expected_version
        )
        return get_review_detail(review_id=updated.id, db=db)
    except ConcurrencyConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{review_id}/reject", response_model=ReviewDetailResponse, summary="Reject Relationship")
def reject_relationship(
    review_id: str,
    body: RejectActionRequest,
    db: Session = Depends(get_db)
):
    """
    Rejects an AI-derived relationship with required rationale.
    Preserves audit history and marks status as REJECTED in graph.
    """
    try:
        updated = ReviewService.reject_relationship(
            db=db,
            review_id=review_id,
            reviewer_id=body.reviewer_id or "investigator:lead",
            reviewer_display_name=body.reviewer_display_name or "Lead Investigator",
            reason=body.reason,
            note=body.note,
            expected_version=body.expected_version
        )
        return get_review_detail(review_id=updated.id, db=db)
    except ConcurrencyConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{review_id}/modify", response_model=ReviewDetailResponse, summary="Modify Relationship Type")
def modify_relationship(
    review_id: str,
    body: ModifyActionRequest,
    db: Session = Depends(get_db)
):
    """
    Corrects an AI-derived relationship to a supported domain relationship type.
    """
    try:
        updated = ReviewService.modify_relationship(
            db=db,
            review_id=review_id,
            new_relationship_type=body.new_relationship_type,
            reviewer_id=body.reviewer_id or "investigator:lead",
            reviewer_display_name=body.reviewer_display_name or "Lead Investigator",
            note=body.note,
            expected_version=body.expected_version
        )
        return get_review_detail(review_id=updated.id, db=db)
    except ConcurrencyConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        # Invalid relationship type or not found
        msg = str(e)
        code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg)


@router.post("/{review_id}/reopen", response_model=ReviewDetailResponse, summary="Reopen Review")
def reopen_review(
    review_id: str,
    body: ReopenActionRequest,
    db: Session = Depends(get_db)
):
    """
    Reopens a previously reviewed or rejected relationship when new evidence surfaces.
    """
    try:
        updated = ReviewService.reopen_review(
            db=db,
            review_id=review_id,
            reviewer_id=body.reviewer_id or "investigator:lead",
            reviewer_display_name=body.reviewer_display_name or "Lead Investigator",
            reason=body.reason or "Reopened for reassessment"
        )
        return get_review_detail(review_id=updated.id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{review_id}/notes", response_model=ReviewDetailResponse, summary="Add Investigator Note")
def add_review_note(
    review_id: str,
    body: AddNoteRequest,
    db: Session = Depends(get_db)
):
    """
    Appends an investigator note to the review dossier and records an audit log event.
    """
    try:
        updated = ReviewService.add_note(
            db=db,
            review_id=review_id,
            reviewer_id=body.reviewer_id or "investigator:lead",
            reviewer_display_name=body.reviewer_display_name or "Lead Investigator",
            note=body.note
        )
        return get_review_detail(review_id=updated.id, db=db)
    except ValueError as e:
        msg = str(e)
        code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg)
