"""
Phase 3: ML & Crime Pattern Analysis — SQLAlchemy Models
All models here are DERIVED ARTIFACTS. They never mutate the original crimes table.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Text,
    Integer,
    Boolean,
    ForeignKey,
    JSON,
    Index,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geography
from app.db.session import Base


# Allow SQLite to compile Geography columns as BLOB for testing
@compiles(Geography, "sqlite")
def compile_geography_sqlite(type_, compiler, **kw):
    return "BLOB"


def generate_uuid():
    return str(uuid.uuid4())


class MlAnalysisJob(Base):
    """
    Tracks async ML analysis pipeline executions.
    Enables non-blocking job submission and status polling.
    """
    __tablename__ = "ml_analysis_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    # PENDING | RUNNING | COMPLETED | FAILED
    analyses = Column(JSON, nullable=True)          # e.g. ["spatial","temporal","semantic","anomaly","patterns"]
    result_summary = Column(JSON, nullable=True)   # High-level counts per analysis type
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_ml_jobs_status", "status"),
    )


class CrimeCluster(Base):
    """
    A discovered cluster of geographically or semantically similar crime incidents.
    cluster_type: 'spatial' (DBSCAN lat/lon) | 'semantic' (embedding DBSCAN/K-Means)
    """
    __tablename__ = "crime_clusters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    cluster_type = Column(String(50), nullable=False, index=True)   # 'spatial' | 'semantic'
    cluster_label = Column(Integer, nullable=False)                  # DBSCAN cluster number (-1 = noise)
    crime_count = Column(Integer, default=0, nullable=False)

    # Centroid (applicable mainly to spatial clusters)
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)

    # Flexible metadata: bounding_box, categories, time_range, dominant_category, etc.
    metadata_ = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    members = relationship("CrimeClusterMember", back_populates="cluster", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_clusters_type_created", "cluster_type", "created_at"),
    )


class CrimeClusterMember(Base):
    """Join table mapping individual crime records to their discovered cluster."""
    __tablename__ = "crime_cluster_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    cluster_id = Column(String(36), ForeignKey("crime_clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    crime_id = Column(String(36), ForeignKey("crimes.id", ondelete="CASCADE"), nullable=False, index=True)

    cluster = relationship("CrimeCluster", back_populates="members")

    __table_args__ = (
        Index("idx_cluster_members_crime", "crime_id"),
    )


class CrimeHotspot(Base):
    """
    Geographic crime hotspot derived from spatial cluster density.
    Uses a PostGIS GEOGRAPHY(POLYGON) to store the hotspot boundary (convex hull of cluster).
    """
    __tablename__ = "crime_hotspots"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # PostGIS polygon boundary (WKT convex hull of cluster points)
    geom = Column(
        Geography(geometry_type="POLYGON", srid=4326, spatial_index=False),
        nullable=True
    )

    crime_count = Column(Integer, default=0, nullable=False)
    density_score = Column(Float, nullable=True)    # crimes per km²
    primary_category = Column(String(100), nullable=True, index=True)
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)

    # Reference back to the originating spatial cluster
    source_cluster_id = Column(String(36), ForeignKey("crime_clusters.id", ondelete="SET NULL"), nullable=True)

    # Centroid for map marker display
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)

    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_hotspots_category_created", "primary_category", "created_at"),
        Index("idx_hotspots_geom_gist", "geom", postgresql_using="gist"),
    )


class CrimeAnomaly(Base):
    """
    Flagged anomaly at the incident level (crime_id set) or temporal period level (crime_id null).
    anomaly_type: 'statistical' | 'spatial' | 'temporal'
    Every anomaly must have a human-readable explanation.
    """
    __tablename__ = "crime_anomalies"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # crime_id is nullable — temporal period anomalies do not reference a single crime
    crime_id = Column(String(36), ForeignKey("crimes.id", ondelete="CASCADE"), nullable=True, index=True)

    anomaly_type = Column(String(50), nullable=False, index=True)  # statistical | spatial | temporal
    anomaly_score = Column(Float, nullable=True)                    # Isolation Forest score (lower = more anomalous)
    baseline_value = Column(Float, nullable=True)                   # Historical baseline (e.g., avg weekly count)
    observed_value = Column(Float, nullable=True)                   # Observed value
    period = Column(String(100), nullable=True)                     # e.g. "2026-W33" for temporal anomalies
    explanation = Column(Text, nullable=False)                      # Human-readable explanation — MANDATORY

    category = Column(String(100), nullable=True, index=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_anomalies_type_created", "anomaly_type", "created_at"),
        Index("idx_anomalies_category", "category"),
    )


class CrimePattern(Base):
    """
    A discovered multi-dimensional crime pattern combining spatial, temporal, semantic, and M.O. signals.
    evidence: list of crime IDs that produced this pattern (mandatory for Phase 4 graph construction).
    """
    __tablename__ = "crime_patterns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    pattern_type = Column(String(100), nullable=False, index=True)  # e.g. 'spatial_temporal', 'semantic_mo'
    category = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)     # 0.0 – 1.0

    # JSONB array of crime IDs — critical for Phase 4 Neo4j graph construction
    evidence = Column(JSON, nullable=False)        # List[str] of crime IDs

    # Structured metadata: location_cluster_id, time_window, dominant_mo, etc.
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_patterns_type_created", "pattern_type", "created_at"),
        Index("idx_patterns_category", "category"),
    )


class CrimeTrend(Base):
    """
    Time-series aggregation for crime volume by period and category.
    period_type: 'hourly' | 'daily' | 'weekly' | 'monthly'
    period: ISO string — e.g. '2026-08' (monthly), '2026-W33' (weekly), 'MON' (daily), '18:00' (hourly)
    """
    __tablename__ = "crime_trends"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    period = Column(String(50), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)    # hourly | daily | weekly | monthly
    category = Column(String(100), nullable=True, index=True)       # NULL means "ALL" categories combined
    crime_count = Column(Integer, default=0, nullable=False)
    rolling_average = Column(Float, nullable=True)                  # N-period rolling mean
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_trends_period_type_cat", "period_type", "category", "period"),
    )
