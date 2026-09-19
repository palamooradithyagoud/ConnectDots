"""
Phase 5: Person Network & Key Individual Relational Models
Defines PostgreSQL tables for Person entities, Crime-Person associations,
and persisted Network Centrality analytics results.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base


class Person(Base):
    """
    Authoritative Person entity.
    Maintains stable internal ID, canonical name, aliases, source provenance,
    and confidence. Conservative identity resolution prevents premature merges.
    """
    __tablename__ = "persons"

    id = Column(String(64), primary_key=True, index=True)  # e.g., 'person:vikram_singh_4a8f' or UUID
    canonical_name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    aliases = Column(JSON, default=list)  # ["Vicky", "Vikram S."]
    identifiers = Column(JSON, default=dict)  # {"aadhaar_hash": "...", "voter_id": "..."}
    source_provenance = Column(String(100), default="FIR_NARRATIVE")  # FIR_NARRATIVE, INTERROGATION, SUBSCRIBER
    confidence = Column(Float, default=1.0)
    metadata_json = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    crime_associations = relationship(
        "CrimePersonAssociation",
        back_populates="person",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    phone_associations = relationship(
        "PersonPhoneAssociation",
        back_populates="person",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    centrality_results = relationship(
        "NetworkCentralityResult",
        back_populates="person",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class CrimePersonAssociation(Base):
    """
    Relational association linking a Person to a Crime (FIR).
    Preserves role (neutral), extraction confidence, and the exact grounded excerpt.
    """
    __tablename__ = "crime_person_associations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crime_id = Column(String(36), ForeignKey("crimes.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(String(64), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(String(50), default="PERSON_OF_INTEREST")  # SUSPECT, ACCUSED, PERSON_OF_INTEREST, WITNESS, VICTIM
    relationship_type = Column(String(50), default="MENTIONED_IN")  # MENTIONED_IN, INVOLVED_IN, ASSOCIATED_WITH
    confidence = Column(Float, default=0.9)
    evidence_excerpt = Column(Text, nullable=True)  # Grounded text passage from source narrative

    @property
    def extraction_confidence(self) -> float:
        return self.confidence

    @extraction_confidence.setter
    def extraction_confidence(self, value: float) -> None:
        self.confidence = value

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    person = relationship("Person", back_populates="crime_associations")


class NetworkCentralityResult(Base):
    """
    Persisted network centrality metrics for investigation-scoped analysis.
    Stores objective structural measurements with timestamp, scope, and algorithm metadata.
    """
    __tablename__ = "network_centrality_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = Column(String(64), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)

    scope_type = Column(String(50), nullable=False, index=True)  # all, crime, cluster, person, date_bounded
    scope_id = Column(String(64), nullable=True, index=True)      # crime_id or cluster_id when scoped

    degree_centrality = Column(Float, nullable=False, default=0.0)
    betweenness_centrality = Column(Float, nullable=False, default=0.0)
    pagerank = Column(Float, nullable=False, default=0.0)
    raw_degree = Column(Integer, nullable=False, default=0)

    connected_crimes = Column(Integer, default=0)
    connected_people = Column(Integer, default=0)
    connected_phones = Column(Integer, default=0)
    connected_vehicles = Column(Integer, default=0)
    connected_organizations = Column(Integer, default=0)

    metrics_metadata = Column(JSON, default=dict)  # Detailed structural breakdown, top bridges
    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    algorithm_version = Column(String(50), default="v1.0-gds-nx")

    person = relationship("Person", back_populates="centrality_results")
