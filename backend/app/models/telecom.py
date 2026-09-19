"""
Production Relational Models for Telecommunications & CDR Intelligence.
Includes:
- PhoneNumber (Normalized unique telephone identities)
- CdrRecord (Deterministic deduplicated Call Detail Records)
- CrimePhoneAssociation (Grounding Crime-Phone relationships with provenance)
- PersonPhoneAssociation (Grounding Person-Phone relationships with provenance)
"""
import uuid
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Text,
    Integer,
    ForeignKey,
    JSON,
    Index,
    CheckConstraint,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid():
    return str(uuid.uuid4())


class PhoneNumber(Base):
    """
    Normalized, deduplicated phone entity.
    Maintains a single canonical E.164 record for every unique phone number observed.
    """
    __tablename__ = "phone_numbers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    normalized_number = Column(String(32), unique=True, index=True, nullable=False)  # E.164 (e.g. +919876543210)
    country_code = Column(String(8), nullable=True, index=True)                     # e.g. "91"
    national_number = Column(String(20), nullable=True, index=True)                 # e.g. "9876543210"
    number_type = Column(String(50), nullable=True)                                 # MOBILE, FIXED_LINE, VOIP, etc.
    carrier = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    outbound_calls = relationship(
        "CdrRecord",
        foreign_keys="CdrRecord.caller_phone_id",
        back_populates="caller_phone",
        cascade="all, delete-orphan"
    )
    inbound_calls = relationship(
        "CdrRecord",
        foreign_keys="CdrRecord.callee_phone_id",
        back_populates="callee_phone",
        cascade="all, delete-orphan"
    )
    crime_associations = relationship(
        "CrimePhoneAssociation",
        back_populates="phone",
        cascade="all, delete-orphan"
    )
    person_associations = relationship(
        "PersonPhoneAssociation",
        back_populates="phone",
        cascade="all, delete-orphan"
    )


class CdrRecord(Base):
    """
    Call Detail Record (CDR) capturing point-in-time telecommunications activity.
    Uses deterministic fingerprint hashing to guarantee idempotent deduplication across ingestion runs.
    """
    __tablename__ = "cdr_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    caller_phone_id = Column(String(36), ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False, index=True)
    callee_phone_id = Column(String(36), ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False, index=True)
    call_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=False, default=0)
    call_type = Column(String(50), nullable=False, default="VOICE", index=True)     # VOICE, SMS, DATA, ROAMING
    location_or_tower = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source_reference = Column(String(255), nullable=True)                           # External record ID / batch file ref
    source_batch_id = Column(String(36), ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Deterministic deduplication hash: sha256(caller + callee + timestamp + duration + type + source_ref)
    fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    caller_phone = relationship("PhoneNumber", foreign_keys=[caller_phone_id], back_populates="outbound_calls")
    callee_phone = relationship("PhoneNumber", foreign_keys=[callee_phone_id], back_populates="inbound_calls")
    batch = relationship("ImportBatch")

    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="chk_cdr_duration_positive"),
        Index("idx_cdr_caller_time", "caller_phone_id", "call_timestamp"),
        Index("idx_cdr_callee_time", "callee_phone_id", "call_timestamp"),
        Index("idx_cdr_call_pair", "caller_phone_id", "callee_phone_id"),
    )


class CrimePhoneAssociation(Base):
    """
    Associates a Crime incident with a Phone Number.
    Preserves provenance (explicit mention from police text vs derived cross-reference).
    """
    __tablename__ = "crime_phone_associations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    crime_id = Column(String(36), ForeignKey("crimes.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_id = Column(String(36), ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), default="MENTIONED_IN_REPORT", nullable=False, index=True) # MENTIONED_IN_REPORT, SUSPECT_PHONE, VICTIM_PHONE
    confidence = Column(Float, default=1.0, nullable=False)
    confidence_type = Column(String(50), default="explicit", nullable=False)                            # explicit, derived, investigator_validated
    source_text = Column(Text, nullable=True)                                                          # Text excerpt where phone was referenced
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    crime = relationship("Crime")
    phone = relationship("PhoneNumber", back_populates="crime_associations")

    __table_args__ = (
        UniqueConstraint("crime_id", "phone_id", "relationship_type", name="uq_crime_phone_rel"),
    )


class PersonPhoneAssociation(Base):
    """
    Associates a Person of Interest with a Phone Number.
    Strict non-hallucination constraint: only recorded when supported by investigative records or user validation.
    """
    __tablename__ = "person_phone_associations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    person_name = Column(String(255), nullable=False, index=True)
    phone_id = Column(String(36), ForeignKey("phone_numbers.id", ondelete="CASCADE"), nullable=False, index=True)
    crime_id = Column(String(36), ForeignKey("crimes.id", ondelete="SET NULL"), nullable=True, index=True)
    role = Column(String(50), default="SUSPECT", nullable=False)                                        # SUSPECT, ASSOCIATE, VICTIM, WITNESS
    confidence = Column(Float, default=0.8, nullable=False)
    confidence_type = Column(String(50), default="derived", nullable=False)                            # explicit, derived, investigator_validated
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    phone = relationship("PhoneNumber", back_populates="person_associations")
    crime = relationship("Crime")

    __table_args__ = (
        UniqueConstraint("person_name", "phone_id", name="uq_person_phone_rel"),
    )
