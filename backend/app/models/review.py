"""
Phase 6: Human-in-the-Loop Investigator Validation Models
Defines PostgreSQL tables for managing the review lifecycle of AI-derived relationships,
audit trail logging, and optimistic concurrency versioning.
"""
import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class ReviewStatus(str, enum.Enum):
    """Strongly typed review state machine status."""
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class RelationshipProvenance(str, enum.Enum):
    """Categorization of how the relationship was originally discovered."""
    EXPLICIT = "EXPLICIT"
    NLP_DERIVED = "NLP_DERIVED"
    CDR_DERIVED = "CDR_DERIVED"
    GRAPH_DERIVED = "GRAPH_DERIVED"
    ML_DERIVED = "ML_DERIVED"
    SEMANTIC_DERIVED = "SEMANTIC_DERIVED"
    LLM_DERIVED = "LLM_DERIVED"


class InvestigationRelationshipReview(Base):
    """
    Authoritative review record for an AI-derived entity relationship.
    Stores the proposed relationship, discovery provenance, supporting evidence snapshot,
    current review status, and optimistic concurrency version.
    """
    __tablename__ = "investigation_relationship_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Deterministic identity reference (e.g. "Person:person:vikram->SHARES_PHONE->Person:person:sunil")
    relationship_ref = Column(String(255), unique=True, nullable=False, index=True)

    source_entity_type = Column(String(50), nullable=False, index=True)   # Person, Crime, Phone, Location, Vehicle
    source_entity_id = Column(String(100), nullable=False, index=True)
    target_entity_type = Column(String(50), nullable=False, index=True)
    target_entity_id = Column(String(100), nullable=False, index=True)

    relationship_type = Column(String(50), nullable=False, index=True)          # Current active relationship type
    original_relationship_type = Column(String(50), nullable=False)            # Originally proposed AI relationship type
    final_relationship_type = Column(String(50), nullable=True)                # Set if modified by investigator

    original_confidence = Column(Float, nullable=False, default=0.8)
    provenance = Column(String(50), nullable=False, default="GRAPH_DERIVED")   # RelationshipProvenance
    discovery_method = Column(String(100), nullable=True)                      # e.g., "shared_phone_analysis", "cdr_call_linkage"

    status = Column(String(30), nullable=False, default=ReviewStatus.PENDING.value, index=True)

    reviewer_id = Column(String(100), nullable=True, index=True)               # e.g., "investigator:lead" or future user UUID
    reviewer_display_name = Column(String(255), nullable=True)
    investigator_note = Column(Text, nullable=True)
    rejection_reason = Column(String(255), nullable=True)

    # Snapshot of corroborating records (FIR record IDs, CDR call IDs, verbatim excerpts)
    evidence_snapshot = Column(JSON, default=list)

    # Optimistic concurrency versioning (detects simultaneous reviews)
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    history_entries = relationship(
        "InvestigationReviewHistory",
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="InvestigationReviewHistory.created_at.asc()"
    )

    __table_args__ = (
        Index("idx_review_source_target", "source_entity_id", "target_entity_id"),
        Index("idx_review_status_conf", "status", "original_confidence"),
    )


class InvestigationReviewHistory(Base):
    """
    Append-only audit log for all investigator decisions, state changes, and notes
    associated with an InvestigationRelationshipReview.
    """
    __tablename__ = "investigation_review_histories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String(36), ForeignKey("investigation_relationship_reviews.id", ondelete="CASCADE"), nullable=False, index=True)

    action = Column(String(50), nullable=False)  # CREATED, VALIDATE, REJECT, MODIFY, REOPEN, NOTE_ADDED
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)

    reviewer_id = Column(String(100), nullable=False)
    reviewer_display_name = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    reason = Column(String(255), nullable=True)

    metadata_snapshot = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    review = relationship("InvestigationRelationshipReview", back_populates="history_entries")
