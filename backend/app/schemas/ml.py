"""
Phase 3 — Pydantic v2 Schemas for ML Analysis API
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ──────────────────────────────────────────────────────────────────────────────
# Analysis Job
# ──────────────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    analyses: Optional[List[str]] = Field(
        default=None,
        description="Options: spatial, temporal, semantic, anomaly, hotspot, patterns. Defaults to all."
    )


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str
    analyses: Optional[List[str]] = None
    result_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class AnalyzeResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ──────────────────────────────────────────────────────────────────────────────
# Clusters
# ──────────────────────────────────────────────────────────────────────────────

class ClusterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cluster_type: str
    cluster_label: int
    crime_count: int
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    crime_ids: Optional[List[str]] = None
    created_at: datetime


class ClusterListResponse(BaseModel):
    total: int
    items: List[ClusterResponse]


# ──────────────────────────────────────────────────────────────────────────────
# Hotspots
# ──────────────────────────────────────────────────────────────────────────────

class HotspotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    crime_count: int
    density_score: Optional[float] = None
    primary_category: Optional[str] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    source_cluster_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class HotspotListResponse(BaseModel):
    total: int
    items: List[HotspotResponse]


# ──────────────────────────────────────────────────────────────────────────────
# Trends
# ──────────────────────────────────────────────────────────────────────────────

class TrendResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    period: str
    period_type: str
    category: Optional[str] = None
    crime_count: int
    rolling_average: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class TrendListResponse(BaseModel):
    total: int
    period_type: Optional[str] = None
    items: List[TrendResponse]


# ──────────────────────────────────────────────────────────────────────────────
# Anomalies
# ──────────────────────────────────────────────────────────────────────────────

class AnomalyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    crime_id: Optional[str] = None
    anomaly_type: str
    anomaly_score: Optional[float] = None
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    period: Optional[str] = None
    explanation: str
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class AnomalyListResponse(BaseModel):
    total: int
    items: List[AnomalyResponse]


# ──────────────────────────────────────────────────────────────────────────────
# Patterns
# ──────────────────────────────────────────────────────────────────────────────

class PatternResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pattern_type: str
    category: Optional[str] = None
    description: str
    confidence: Optional[float] = None
    evidence: List[str] = Field(description="Crime IDs supporting this pattern")
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class PatternListResponse(BaseModel):
    total: int
    items: List[PatternResponse]


# ──────────────────────────────────────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────────────────────────────────────

class MlStatsResponse(BaseModel):
    total_crimes_analyzed: int
    total_clusters: int
    spatial_clusters: int
    semantic_clusters: int
    total_hotspots: int
    total_anomalies: int
    total_patterns: int
    trend_records: int
    last_analysis_at: Optional[str] = None
    last_job_id: Optional[str] = None
