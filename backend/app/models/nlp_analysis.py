import uuid
from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Index,
    func
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid():
    return str(uuid.uuid4())


class NlpAnalysis(Base):
    """Structured NLP understanding, extracted entities, modus operandi, and graph-ready payload."""
    __tablename__ = "nlp_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    crime_id = Column(String(36), ForeignKey("crimes.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, PROCESSING, COMPLETED, FAILED
    processed_text = Column(Text, nullable=True)
    
    # Structured Extracted Entities
    entities = Column(JSON, nullable=True)  # Full entity dictionary with span and confidence
    extracted_weapons = Column(JSON, nullable=True)  # List of identified weapons
    extracted_vehicles = Column(JSON, nullable=True)  # List of identified getaway / incident vehicles
    extracted_locations = Column(JSON, nullable=True)  # Named landmarks / sub-areas mentioned
    extracted_persons = Column(JSON, nullable=True)  # Suspects / victim / accomplice descriptions
    
    # Modus Operandi
    modus_operandi = Column(JSON, nullable=True)  # List of patterns with classification (explicitly_stated / inferred)
    
    # Classification & Review
    predicted_category = Column(String(100), nullable=True, index=True)
    classification_confidence = Column(Float, nullable=True)
    needs_review = Column(Boolean, default=False, nullable=False, index=True)
    
    # Vector Search & Embeddings
    embedding_model = Column(String(100), nullable=True)
    qdrant_point_id = Column(String(36), nullable=True, index=True)
    
    # Phase 4 Graph-Ready Schema (Nodes and Relationships)
    graph_ready_payload = Column(JSON, nullable=True)
    
    # Diagnostic / Error tracking
    error_message = Column(Text, nullable=True)
    
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    crime = relationship("Crime", back_populates="nlp_analysis")

    __table_args__ = (
        Index("idx_nlp_status_review", "status", "needs_review"),
        Index("idx_nlp_predicted_category", "predicted_category"),
    )
