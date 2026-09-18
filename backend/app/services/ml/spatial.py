"""
Phase 3 — Spatial Analysis Service
Uses DBSCAN (sklearn) on crime lat/lon pairs to discover geographically concentrated clusters.
DBSCAN is preferred because:
  - Crime clusters are not necessarily spherical
  - The number of clusters need not be predetermined
  - Noise/outlier points are handled natively (label = -1)
"""
import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.models.ml_models import CrimeCluster, CrimeClusterMember
from app.core.config import settings

logger = logging.getLogger("connectdots_ml_spatial")

# Earth radius in km
EARTH_RADIUS_KM = 6371.0


class SpatialAnalysisService:
    """
    Discovers geographically concentrated crime clusters using DBSCAN.
    All results are persisted as CrimeCluster + CrimeClusterMember records.
    Original crime data is never modified.
    """

    @classmethod
    def run(cls, db: Session, eps_km: Optional[float] = None, min_samples: Optional[int] = None) -> Dict[str, Any]:
        """
        Main entry point. Loads crime coordinates, runs DBSCAN, persists results.
        Returns a summary dict with cluster counts and metadata.
        """
        eps_km = eps_km or settings.ML_DBSCAN_EPS_KM
        min_samples = min_samples or settings.ML_DBSCAN_MIN_SAMPLES

        # Load crimes with valid coordinates
        crimes = db.query(
            Crime.id,
            Crime.record_id,
            Crime.latitude,
            Crime.longitude,
            Crime.category,
            Crime.occurred_at,
            Crime.location_name,
        ).filter(
            Crime.latitude.isnot(None),
            Crime.longitude.isnot(None),
            Crime.status == "VALID",
        ).all()

        if len(crimes) < 2:
            logger.info("Spatial clustering: insufficient data (need >= 2 valid records).")
            return {
                "status": "insufficient_data",
                "crime_count": len(crimes),
                "clusters_found": 0,
                "noise_points": 0,
                "message": f"Only {len(crimes)} valid crime record(s) available. Need at least 2 for spatial clustering."
            }

        crime_ids = [c.id for c in crimes]
        coords = np.array([[c.latitude, c.longitude] for c in crimes], dtype=float)

        # DBSCAN with haversine metric requires radians input
        coords_rad = np.radians(coords)
        eps_radians = eps_km / EARTH_RADIUS_KM

        try:
            from sklearn.cluster import DBSCAN
            db_model = DBSCAN(
                eps=eps_radians,
                min_samples=min_samples,
                algorithm="ball_tree",
                metric="haversine",
            )
            labels = db_model.fit_predict(coords_rad)
        except Exception as e:
            logger.error(f"DBSCAN failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

        unique_labels = set(labels)
        cluster_labels = [lbl for lbl in unique_labels if lbl != -1]
        noise_count = int(np.sum(labels == -1))

        logger.info(f"Spatial DBSCAN: {len(crimes)} crimes → {len(cluster_labels)} clusters, {noise_count} noise points")

        # Delete previous spatial clusters to avoid duplicates on re-run
        old_clusters = db.query(CrimeCluster).filter(CrimeCluster.cluster_type == "spatial").all()
        for oc in old_clusters:
            db.delete(oc)
        db.flush()

        clusters_created = 0
        for lbl in cluster_labels:
            mask = labels == lbl
            member_indices = np.where(mask)[0]
            member_crime_ids = [crime_ids[i] for i in member_indices]
            member_crimes = [crimes[i] for i in member_indices]

            # Centroid
            centroid_lat = float(np.mean([crimes[i].latitude for i in member_indices]))
            centroid_lon = float(np.mean([crimes[i].longitude for i in member_indices]))

            # Category distribution
            cat_counts: Dict[str, int] = {}
            for c in member_crimes:
                cat_counts[c.category] = cat_counts.get(c.category, 0) + 1
            dominant_category = max(cat_counts, key=cat_counts.get)

            # Time range
            timestamps = [c.occurred_at for c in member_crimes if c.occurred_at]
            time_range_start = min(timestamps).isoformat() if timestamps else None
            time_range_end = max(timestamps).isoformat() if timestamps else None

            # Bounding box
            lats = [crimes[i].latitude for i in member_indices]
            lons = [crimes[i].longitude for i in member_indices]
            bbox = {
                "min_lat": float(min(lats)),
                "max_lat": float(max(lats)),
                "min_lon": float(min(lons)),
                "max_lon": float(max(lons)),
            }

            cluster = CrimeCluster(
                cluster_type="spatial",
                cluster_label=int(lbl),
                crime_count=len(member_crime_ids),
                centroid_lat=centroid_lat,
                centroid_lon=centroid_lon,
                metadata_={
                    "dominant_category": dominant_category,
                    "category_distribution": cat_counts,
                    "time_range_start": time_range_start,
                    "time_range_end": time_range_end,
                    "bounding_box": bbox,
                    "eps_km": eps_km,
                    "min_samples": min_samples,
                    "locations": list({c.location_name for c in member_crimes if c.location_name})[:10],
                }
            )
            db.add(cluster)
            db.flush()

            # Create member associations
            for crime_id in member_crime_ids:
                db.add(CrimeClusterMember(cluster_id=cluster.id, crime_id=crime_id))

            clusters_created += 1

        db.commit()
        logger.info(f"Spatial clustering committed: {clusters_created} clusters.")

        return {
            "status": "completed",
            "crime_count": len(crimes),
            "clusters_found": clusters_created,
            "noise_points": noise_count,
            "eps_km": eps_km,
            "min_samples": min_samples,
        }

    @classmethod
    def get_cluster_detail(cls, db: Session, cluster_id: str) -> Optional[Dict[str, Any]]:
        """Returns detailed info for a single spatial cluster including member crime IDs."""
        cluster = db.query(CrimeCluster).filter(CrimeCluster.id == cluster_id).first()
        if not cluster:
            return None
        members = db.query(CrimeClusterMember.crime_id).filter(
            CrimeClusterMember.cluster_id == cluster_id
        ).all()
        return {
            "id": cluster.id,
            "cluster_type": cluster.cluster_type,
            "cluster_label": cluster.cluster_label,
            "crime_count": cluster.crime_count,
            "centroid_lat": cluster.centroid_lat,
            "centroid_lon": cluster.centroid_lon,
            "metadata": cluster.metadata_,
            "crime_ids": [m.crime_id for m in members],
            "created_at": cluster.created_at.isoformat(),
        }
