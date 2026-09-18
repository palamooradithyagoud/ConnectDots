"""
Phase 3 — ML Analysis Orchestrator
Coordinates the full Phase 3 ML pipeline:
  1. Validate available data
  2. Spatial clustering (DBSCAN)
  3. Temporal analysis
  4. Semantic clustering (embedding reuse)
  5. Anomaly detection (Isolation Forest + temporal baseline)
  6. Hotspot mapping
  7. Pattern synthesis
  8. Persist results
  9. Return structured summary

Supports selective execution via 'analyses' list.
Uses MlAnalysisJob for async status tracking.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from app.models.ml_models import MlAnalysisJob
from app.services.ml.spatial import SpatialAnalysisService
from app.services.ml.temporal import TemporalAnalysisService
from app.services.ml.clustering import SemanticClusteringService
from app.services.ml.anomaly import AnomalyDetectionService
from app.services.ml.hotspot import HotspotService
from app.services.ml.patterns import PatternAnalysisService

logger = logging.getLogger("connectdots_ml_orchestrator")

ALL_ANALYSES = ["spatial", "temporal", "semantic", "anomaly", "hotspot", "patterns"]


class MLAnalysisService:
    """
    Master orchestrator for Phase 3 ML pipeline.
    Creates an MlAnalysisJob record and runs selected analyses in order.
    """

    @classmethod
    def create_job(cls, db: Session, analyses: Optional[List[str]] = None) -> str:
        """Creates an MlAnalysisJob record and returns its job_id."""
        selected = analyses if analyses else ALL_ANALYSES
        job = MlAnalysisJob(
            status="PENDING",
            analyses=selected,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"ML Analysis Job {job.id} created (analyses: {selected})")
        return job.id

    @classmethod
    def run_job(cls, job_id: str, db_factory) -> None:
        """
        Executes the full ML pipeline for a given job.
        Designed to run in a FastAPI BackgroundTask — creates its own DB session.
        """
        db: Session = db_factory()
        try:
            job = db.query(MlAnalysisJob).filter(MlAnalysisJob.id == job_id).first()
            if not job:
                logger.error(f"ML Job {job_id} not found.")
                return

            job.status = "RUNNING"
            job.started_at = datetime.now(timezone.utc)
            db.commit()

            analyses = job.analyses or ALL_ANALYSES
            result_summary: Dict[str, Any] = {}

            def _run(name: str, fn):
                if name in analyses:
                    logger.info(f"Running {name} analysis...")
                    try:
                        result = fn(db)
                        result_summary[name] = result
                        logger.info(f"{name} analysis complete: {result.get('status')}")
                    except Exception as e:
                        logger.error(f"{name} analysis failed: {e}", exc_info=True)
                        result_summary[name] = {"status": "failed", "error": str(e)}

            # Ordered pipeline execution
            _run("spatial", SpatialAnalysisService.run)
            _run("temporal", TemporalAnalysisService.run)
            _run("semantic", SemanticClusteringService.run)
            _run("anomaly", AnomalyDetectionService.run)
            _run("hotspot", HotspotService.run)
            _run("patterns", PatternAnalysisService.run)

            job.status = "COMPLETED"
            job.result_summary = result_summary
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"ML Analysis Job {job_id} COMPLETED.")

        except Exception as e:
            logger.error(f"ML Analysis Job {job_id} FAILED: {e}", exc_info=True)
            try:
                job = db.query(MlAnalysisJob).filter(MlAnalysisJob.id == job_id).first()
                if job:
                    job.status = "FAILED"
                    job.error_message = str(e)
                    job.completed_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    @classmethod
    def get_stats(cls, db: Session) -> Dict[str, Any]:
        """Returns a high-level summary of all Phase 3 ML results."""
        from sqlalchemy import func
        from app.models.ml_models import (
            CrimeCluster, CrimeHotspot, CrimeAnomaly, CrimePattern, CrimeTrend
        )
        from app.models.crime import Crime

        total_crimes = db.query(func.count(Crime.id)).filter(Crime.status == "VALID").scalar() or 0
        total_clusters = db.query(func.count(CrimeCluster.id)).scalar() or 0
        spatial_clusters = db.query(func.count(CrimeCluster.id)).filter(CrimeCluster.cluster_type == "spatial").scalar() or 0
        semantic_clusters = db.query(func.count(CrimeCluster.id)).filter(CrimeCluster.cluster_type == "semantic").scalar() or 0
        total_hotspots = db.query(func.count(CrimeHotspot.id)).scalar() or 0
        total_anomalies = db.query(func.count(CrimeAnomaly.id)).scalar() or 0
        total_patterns = db.query(func.count(CrimePattern.id)).scalar() or 0
        trend_records = db.query(func.count(CrimeTrend.id)).scalar() or 0

        # Last completed job
        last_job = db.query(MlAnalysisJob).filter(
            MlAnalysisJob.status == "COMPLETED"
        ).order_by(MlAnalysisJob.completed_at.desc()).first()

        return {
            "total_crimes_analyzed": total_crimes,
            "total_clusters": total_clusters,
            "spatial_clusters": spatial_clusters,
            "semantic_clusters": semantic_clusters,
            "total_hotspots": total_hotspots,
            "total_anomalies": total_anomalies,
            "total_patterns": total_patterns,
            "trend_records": trend_records,
            "last_analysis_at": last_job.completed_at.isoformat() if last_job and last_job.completed_at else None,
            "last_job_id": last_job.id if last_job else None,
        }

    @classmethod
    def run_individual(cls, analysis_name: str, db: Session) -> Dict[str, Any]:
        """Runs a single named analysis synchronously. Useful for targeted re-runs."""
        analysis_name = analysis_name.lower()
        dispatch = {
            "spatial": SpatialAnalysisService.run,
            "temporal": TemporalAnalysisService.run,
            "semantic": SemanticClusteringService.run,
            "anomaly": AnomalyDetectionService.run,
            "hotspot": HotspotService.run,
            "patterns": PatternAnalysisService.run,
        }
        fn = dispatch.get(analysis_name)
        if not fn:
            return {"status": "error", "message": f"Unknown analysis: {analysis_name}. Valid: {list(dispatch.keys())}"}
        return fn(db)
