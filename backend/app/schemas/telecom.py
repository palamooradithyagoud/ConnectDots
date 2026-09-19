"""
Phase 4 Telecommunications: Pydantic Schemas for Phone & CDR Intelligence
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PhoneBase(BaseModel):
    normalized_number: str = Field(..., description="Canonical E.164 phone number, e.g. +919876543210")
    country_code: Optional[str] = Field(None, description="Country calling code")
    national_number: Optional[str] = Field(None, description="National significant number")
    number_type: Optional[str] = Field(None, description="MOBILE, FIXED_LINE, VOIP, etc.")
    carrier: Optional[str] = Field(None, description="Service provider or network carrier")


class PhoneResponse(PhoneBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PhoneListResponse(BaseModel):
    items: List[PhoneResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PhoneMetrics(BaseModel):
    total_calls: int
    outbound_calls: int
    inbound_calls: int
    total_duration_seconds: int
    outbound_duration_seconds: int
    inbound_duration_seconds: int
    unique_contacts_count: int
    first_activity: Optional[str] = None
    last_activity: Optional[str] = None
    hourly_distribution: Dict[int, int] = {}


class TopContact(BaseModel):
    phone_id: str
    normalized_number: str
    call_count: int
    total_duration: int


class AssociatedCrime(BaseModel):
    crime_id: str
    record_id: str
    category: str
    crime_type: str
    location_name: str
    occurred_at: Optional[str] = None
    relationship_type: str
    confidence: float
    confidence_type: str
    source_text: Optional[str] = None


class AssociatedPerson(BaseModel):
    person_name: str
    role: str
    confidence: float
    confidence_type: str
    source: Optional[str] = None


class PhoneDetailResponse(PhoneBase):
    id: str
    created_at: Optional[str] = None
    metrics: PhoneMetrics
    associated_crimes: List[AssociatedCrime] = []
    associated_persons: List[AssociatedPerson] = []
    top_contacts: List[TopContact] = []


class CdrResponse(BaseModel):
    id: str
    caller_phone_id: str
    callee_phone_id: str
    caller_number: Optional[str] = None
    callee_number: Optional[str] = None
    call_timestamp: datetime
    duration_seconds: int
    call_type: str
    location_or_tower: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_reference: Optional[str] = None
    fingerprint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CdrListResponse(BaseModel):
    items: List[CdrResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CdrImportResultResponse(BaseModel):
    batch_id: Optional[str] = None
    dry_run: bool
    filename: str
    total_rows: int
    valid_count: int
    rejected_count: int
    preview_valid: List[Dict[str, Any]] = []
    rejections: List[Dict[str, Any]] = []
    message: str


class CrossCaseConnectionResponse(BaseModel):
    connection_type: str
    crime_1: Dict[str, Any]
    crime_2: Dict[str, Any]
    shared_phone: Optional[str] = None
    phone_1: Optional[str] = None
    phone_2: Optional[str] = None
    call_count: Optional[int] = None
    evidence: str
    confidence: float
    confidence_type: str
