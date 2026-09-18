"""
Phase 3 — ML & Pattern Analysis API Endpoints
All ML analyses run as BackgroundTasks to avoid blocking the API.
Job status can be polled via GET /api/v1/ml/jobs/{job_id}.
"""
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.models.ml_models import (
    MlAnalysisJob, CrimeCluster, CrimeClusterMember,
    CrimeHotspot, CrimeAnomaly, CrimePattern, CrimeTrend
)
from app.schemas.ml import (
    AnalyzeRequest, AnalyzeResponse, JobStatusResponse,
    ClusterResponse, ClusterListResponse,
    HotspotResponse, HotspotListResponse,
    TrendResponse, TrendListResponse,
    AnomalyResponse, AnomalyListResponse,
    PatternResponse, PatternListResponse,
    MlStatsResponse,
)
from app.services.ml.orchestrator import MLAnalysisService

router = APIRouter()
logger = logging.getLogger("connectdots_ml_api")


def _serialize_cluster(cluster: CrimeCluster, db: Session, include_members: bool = False) -> dict:
    members = []
    if include_members:
        members = [m.crime_id for m in db.query(CrimeClusterMember.crime_id).filter(
            CrimeClusterMember.cluster_id == cluster.id
        ).all()]
    return {
        "id": cluster.id,
        "cluster_type": cluster.cluster_type,
        "cluster_label": cluster.cluster_label,
        "crime_count": cluster.crime_count,
        "centroid_lat": cluster.centroid_lat,
        "centroid_lon": cluster.centroid_lon,
        "metadata": cluster.metadata_,
        "crime_ids": members if include_members else None,
        "created_at": cluster.created_at,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Trigger Analysis
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Phase 3 ML analysis pipeline",
)
def trigger_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Starts the Phase 3 ML analysis pipeline as a background job.
    Returns a job_id that can be polled for status.
    Optionally specify which analyses to run via the 'analyses' list.
    """
    job_id = MLAnalysisService.create_job(db, analyses=request.analyses)

    def _run_in_background():
        MLAnalysisService.run_job(job_id, db_factory=SessionLocal)

    background_tasks.add_task(_run_in_background)
    return AnalyzeResponse(
        job_id=job_id,
        status="PENDING",
        message=f"ML analysis job {job_id} queued. Poll GET /api/v1/ml/jobs/{job_id} for status."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Job Status
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get ML analysis job status",
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Poll the status of a submitted ML analysis job."""
    job = db.query(MlAnalysisJob).filter(MlAnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"ML Job '{job_id}' not found.")
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        analyses=job.analyses,
        result_summary=job.result_summary,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=MlStatsResponse,
    summary="Phase 3 ML analysis summary statistics",
)
def get_ml_stats(db: Session = Depends(get_db)):
    """Returns aggregate counts of clusters, hotspots, anomalies, and patterns."""
    stats = MLAnalysisService.get_stats(db)
    return MlStatsResponse(**stats)


# ──────────────────────────────────────────────────────────────────────────────
# Clusters
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/clusters",
    response_model=ClusterListResponse,
    summary="List discovered crime clusters",
)
def list_clusters(
    cluster_type: Optional[str] = Query(None, description="Filter by 'spatial' or 'semantic'"),
    category: Optional[str] = Query(None, description="Filter by dominant category"),
    include_members: bool = Query(False, description="Include member crime IDs in response"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(CrimeCluster)
    if cluster_type:
        query = query.filter(CrimeCluster.cluster_type == cluster_type.lower())

    total = query.count()
    clusters = query.order_by(CrimeCluster.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for cluster in clusters:
        data = _serialize_cluster(cluster, db, include_members=include_members)
        # Category filter on metadata (post-filter since it's in JSON)
        if category:
            meta = cluster.metadata_ or {}
            dom_cat = meta.get("dominant_category", "")
            if dom_cat.upper() != category.upper():
                continue
        items.append(ClusterResponse(**data))

    return ClusterListResponse(total=total, items=items)


@router.get(
    "/clusters/{cluster_id}",
    response_model=ClusterResponse,
    summary="Get cluster detail with member crime IDs",
)
def get_cluster(cluster_id: str, db: Session = Depends(get_db)):
    from app.services.ml.spatial import SpatialAnalysisService
    detail = SpatialAnalysisService.get_cluster_detail(db, cluster_id)
    if not detail:
        # Try without assuming spatial type
        cluster = db.query(CrimeCluster).filter(CrimeCluster.id == cluster_id).first()
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found.")
        data = _serialize_cluster(cluster, db, include_members=True)
        detail = data
    return ClusterResponse(**detail)


# ──────────────────────────────────────────────────────────────────────────────
# Hotspots
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/hotspots",
    response_model=HotspotListResponse,
    summary="List crime hotspots",
)
def list_hotspots(
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(CrimeHotspot)
    if category:
        query = query.filter(CrimeHotspot.primary_category == category.upper())

    total = query.count()
    hotspots = query.order_by(CrimeHotspot.density_score.desc()).offset(offset).limit(limit).all()
    items = [HotspotResponse(
        id=h.id,
        crime_count=h.crime_count,
        density_score=h.density_score,
        primary_category=h.primary_category,
        date_range_start=h.date_range_start,
        date_range_end=h.date_range_end,
        centroid_lat=h.centroid_lat,
        centroid_lon=h.centroid_lon,
        source_cluster_id=h.source_cluster_id,
        metadata=h.metadata_,
        created_at=h.created_at,
    ) for h in hotspots]
    return HotspotListResponse(total=total, items=items)


# ──────────────────────────────────────────────────────────────────────────────
# Trends
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/trends",
    response_model=TrendListResponse,
    summary="Crime trends over time",
)
def list_trends(
    period_type: Optional[str] = Query(None, description="hourly | daily | weekly | monthly"),
    category: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(CrimeTrend)
    if period_type:
        query = query.filter(CrimeTrend.period_type == period_type.lower())
    if category:
        query = query.filter(CrimeTrend.category == category.upper())
    else:
        query = query.filter(CrimeTrend.category.is_(None))

    total = query.count()
    trends = query.order_by(CrimeTrend.period_type, CrimeTrend.period).limit(limit).all()
    items = [TrendResponse(
        id=t.id,
        period=t.period,
        period_type=t.period_type,
        category=t.category,
        crime_count=t.crime_count,
        rolling_average=t.rolling_average,
        metadata=t.metadata_,
        created_at=t.created_at,
    ) for t in trends]
    return TrendListResponse(total=total, period_type=period_type, items=items)


# ──────────────────────────────────────────────────────────────────────────────
# Anomalies
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/anomalies",
    response_model=AnomalyListResponse,
    summary="List detected crime anomalies",
)
def list_anomalies(
    anomaly_type: Optional[str] = Query(None, description="statistical | spatial | temporal"),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(CrimeAnomaly)
    if anomaly_type:
        query = query.filter(CrimeAnomaly.anomaly_type == anomaly_type.lower())
    if category:
        query = query.filter(CrimeAnomaly.category == category.upper())

    total = query.count()
    anomalies = query.order_by(CrimeAnomaly.anomaly_score).offset(offset).limit(limit).all()
    items = [AnomalyResponse(
        id=a.id,
        crime_id=a.crime_id,
        anomaly_type=a.anomaly_type,
        anomaly_score=a.anomaly_score,
        baseline_value=a.baseline_value,
        observed_value=a.observed_value,
        period=a.period,
        explanation=a.explanation,
        category=a.category,
        metadata=a.metadata_,
        created_at=a.created_at,
    ) for a in anomalies]
    return AnomalyListResponse(total=total, items=items)


# ──────────────────────────────────────────────────────────────────────────────
# Patterns
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/patterns",
    response_model=PatternListResponse,
    summary="List discovered crime patterns with evidence crime IDs",
)
def list_patterns(
    pattern_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(CrimePattern)
    if pattern_type:
        query = query.filter(CrimePattern.pattern_type == pattern_type.lower())
    if category:
        query = query.filter(CrimePattern.category == category.upper())

    total = query.count()
    patterns = query.order_by(CrimePattern.confidence.desc()).offset(offset).limit(limit).all()
    items = [PatternResponse(
        id=p.id,
        pattern_type=p.pattern_type,
        category=p.category,
        description=p.description,
        confidence=p.confidence,
        evidence=p.evidence or [],
        metadata=p.metadata_,
        created_at=p.created_at,
    ) for p in patterns]
    return PatternListResponse(total=total, items=items)
