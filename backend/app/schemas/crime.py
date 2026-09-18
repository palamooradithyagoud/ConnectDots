from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CrimeBase(BaseModel):
    record_id: str = Field(..., description="Unique external incident tracking code")
    crime_type: str = Field(..., description="Normalized or raw crime type")
    category: str = Field(..., description="Standardized canonical crime category")
    location_name: str = Field(..., description="Cleaned location or neighborhood name")
    occurred_at: datetime = Field(..., description="Incident timestamp with timezone")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude coordinate")
    description: Optional[str] = Field(None, description="Detailed incident narrative")
    source: str = Field(..., description="Reporting police station or data source")
    status: str = Field("VALID", description="Verification state of incident")
    extra_metadata: Optional[Dict[str, Any]] = None


class CrimeCreate(CrimeBase):
    pass


class CrimeResponse(CrimeBase):
    id: str
    import_batch_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CrimeListResponse(BaseModel):
    items: List[CrimeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# GeoJSON Schemas for Mapping
class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


# Rejection & Ingestion Schemas
class RejectionDetail(BaseModel):
    row_number: Optional[int] = None
    raw_data: Dict[str, Any]
    error_category: str
    error_message: str


class ImportBatchResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    total_rows: int
    valid_count: int
    rejected_count: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImportResultResponse(BaseModel):
    batch_id: Optional[str] = None
    dry_run: bool
    filename: str
    total_rows: int
    valid_count: int
    rejected_count: int
    preview_valid: List[CrimeBase] = []
    rejections: List[RejectionDetail] = []
    message: str


# Stats & KPIs
class StatsResponse(BaseModel):
    total_crimes: int
    total_batches: int
    total_valid: int
    total_rejected: int
    by_category: Dict[str, int]
    by_source: Dict[str, int]
    geo_coverage: Optional[Dict[str, Optional[float]]] = None
