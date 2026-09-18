"""
Phase 3 — Hotspot Service
Converts spatial clusters into geographic crime hotspots with density scoring.
Uses convex hull of cluster crime points as the hotspot boundary polygon (PostGIS-compatible WKT).
"""
import logging
import math
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from app.models.crime import Crime
from app.models.ml_models import CrimeCluster, CrimeClusterMember, CrimeHotspot

logger = logging.getLogger("connectdots_ml_hotspot")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _approximate_area_km2(lats: List[float], lons: List[float]) -> float:
    """Rough bounding-box area in km² for density calculation."""
    if len(lats) < 2:
        return 1.0  # 1 km² minimum to avoid division by zero
    height_km = _haversine_km(min(lats), min(lons), max(lats), min(lons))
    width_km = _haversine_km(min(lats), min(lons), min(lats), max(lons))
    area = max(height_km * width_km, 0.01)
    return area


def _convex_hull_wkt(points: List[tuple]) -> Optional[str]:
    """
    Computes convex hull of (lat, lon) points and returns WKT POLYGON.
    Uses Shapely if available; falls back to bounding-box rectangle.
    Note: WKT uses (lon lat) order per WKS84/GeoJSON convention.
    """
    if len(points) < 3:
        # Use a small bounding box for 1-2 points
        lats = [p[0] for p in points]
        lons = [p[1] for p in points]
        pad = 0.005  # ~500m padding
        wkt = (
            f"POLYGON(("
            f"{min(lons)-pad} {min(lats)-pad}, "
            f"{max(lons)+pad} {min(lats)-pad}, "
            f"{max(lons)+pad} {max(lats)+pad}, "
            f"{min(lons)-pad} {max(lats)+pad}, "
            f"{min(lons)-pad} {min(lats)-pad}"
            f"))"
        )
        return wkt

    try:
        from shapely.geometry import MultiPoint
        mp = MultiPoint([(lon, lat) for lat, lon in points])  # Shapely: (x=lon, y=lat)
        hull = mp.convex_hull
        return hull.wkt
    except Exception as e:
        logger.warning(f"Shapely convex hull failed: {e} — using bounding box.")

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    pad = 0.005
    wkt = (
        f"POLYGON(("
        f"{min(lons)-pad} {min(lats)-pad}, "
        f"{max(lons)+pad} {min(lats)-pad}, "
        f"{max(lons)+pad} {max(lats)+pad}, "
        f"{min(lons)-pad} {max(lats)+pad}, "
        f"{min(lons)-pad} {min(lats)-pad}"
        f"))"
    )
    return wkt


class HotspotService:
    """
    Creates CrimeHotspot records from spatial clusters.
    Hotspot density = crimes per km² (measurable, not just visual density).
    """

    @classmethod
    def run(cls, db: Session) -> Dict[str, Any]:
        """Main entry point — converts spatial clusters to hotspot records."""
        spatial_clusters = db.query(CrimeCluster).filter(
            CrimeCluster.cluster_type == "spatial",
            CrimeCluster.crime_count >= 1,
        ).all()

        if not spatial_clusters:
            return {
                "status": "no_spatial_clusters",
                "hotspots_created": 0,
                "message": "No spatial clusters found. Run spatial analysis first."
            }

        # Remove previous hotspots
        db.query(CrimeHotspot).delete()
        db.flush()

        hotspots_created = 0
        for cluster in spatial_clusters:
            # Get crime coordinates for this cluster
            member_crimes = db.query(
                Crime.latitude,
                Crime.longitude,
                Crime.category,
                Crime.occurred_at,
            ).join(
                CrimeClusterMember, Crime.id == CrimeClusterMember.crime_id
            ).filter(
                CrimeClusterMember.cluster_id == cluster.id,
                Crime.latitude.isnot(None),
                Crime.longitude.isnot(None),
            ).all()

            if not member_crimes:
                continue

            points = [(c.latitude, c.longitude) for c in member_crimes]
            lats = [p[0] for p in points]
            lons = [p[1] for p in points]
            area_km2 = _approximate_area_km2(lats, lons)
            density_score = round(len(member_crimes) / area_km2, 4)

            # Dominant category
            meta = cluster.metadata_ or {}
            primary_category = meta.get("dominant_category")

            # Time range
            timestamps = [c.occurred_at for c in member_crimes if c.occurred_at]
            date_range_start = min(timestamps) if timestamps else None
            date_range_end = max(timestamps) if timestamps else None

            # Convex hull polygon for PostGIS
            hull_wkt = _convex_hull_wkt(points)

            # Only store WKT in metadata if PostgreSQL is not available for geography column
            is_postgres = "postgresql" in (db.bind.url.drivername if db.bind else "")

            hotspot = CrimeHotspot(
                crime_count=len(member_crimes),
                density_score=density_score,
                primary_category=primary_category,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                source_cluster_id=cluster.id,
                centroid_lat=cluster.centroid_lat,
                centroid_lon=cluster.centroid_lon,
                metadata_={
                    "cluster_label": cluster.cluster_label,
                    "area_km2": round(area_km2, 4),
                    "density_score": density_score,
                    "bounding_box": meta.get("bounding_box"),
                    "locations": meta.get("locations", []),
                    "convex_hull_wkt": hull_wkt,  # Keep WKT in metadata for frontend use
                }
            )

            # Set PostGIS geometry column if on PostgreSQL
            if is_postgres and hull_wkt:
                try:
                    from geoalchemy2.elements import WKTElement
                    hotspot.geom = WKTElement(hull_wkt, srid=4326)
                except Exception as e:
                    logger.warning(f"Could not set PostGIS geometry on hotspot: {e}")

            db.add(hotspot)
            hotspots_created += 1

        db.commit()
        logger.info(f"Hotspot detection committed: {hotspots_created} hotspots.")
        return {
            "status": "completed",
            "spatial_clusters_processed": len(spatial_clusters),
            "hotspots_created": hotspots_created,
        }
