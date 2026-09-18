"""
Phase 3 — ML & Pattern Analysis Tests
Tests all Phase 3 services using in-memory SQLite with synthetic crime data.
All 18 existing Phase 1/2 tests must continue to pass.
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all models so tables are created
from app.db.session import Base
from app.models.crime import Crime, ImportBatch
from app.models.nlp_analysis import NlpAnalysis
from app.models.ml_models import (
    CrimeCluster, CrimeClusterMember, CrimeHotspot,
    CrimeAnomaly, CrimePattern, CrimeTrend, MlAnalysisJob
)
from app.core.config import settings


# ──────────────────────────────────────────────────────────────────────────────
# Test Database Setup
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def test_db():
    """Creates in-memory SQLite database with Phase 1/2/3 schema for testing."""
    import sqlite3
    from sqlalchemy import event

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def add_geo_functions(dbapi_conn, connection_record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.create_function("ST_GeogFromText", 1, lambda v: v)
            dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda v: "{}")
            dbapi_conn.create_function("AsBinary", 1, lambda v: v)

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def _make_crime(db, record_id: str, lat: float, lon: float, category: str,
                occurred_at: datetime = None, description: str = None) -> Crime:
    """Helper: create and persist a Crime record."""
    batch_id = f"batch-{uuid.uuid4().hex[:8]}"
    # Ensure batch exists
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        batch = ImportBatch(
            id=batch_id,
            filename="test.csv",
            file_type="CSV",
            total_rows=1,
            valid_count=1,
            rejected_count=0,
        )
        db.add(batch)
        db.flush()

    crime = Crime(
        id=str(uuid.uuid4()),
        record_id=record_id,
        crime_type=category.lower(),
        category=category,
        location_name=f"Test Location {record_id}",
        latitude=lat,
        longitude=lon,
        occurred_at=occurred_at or datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc),
        description=description or f"Test crime description for {category} at location",
        source="Test Source",
        status="VALID",
        import_batch_id=batch_id,
    )
    db.add(crime)
    db.flush()
    return crime


@pytest.fixture(scope="module")
def populated_db(test_db):
    """
    Populates the test database with 15 synthetic crime records
    spread across multiple locations, times, and categories.
    """
    db = test_db

    # Bangalore area cluster 1: MG Road area (lat~12.97, lon~77.60)
    _make_crime(db, "CR-T-001", 12.972, 77.600, "THEFT",
                datetime(2026, 6, 10, 20, 30, tzinfo=timezone.utc),
                "Mobile phone snatched near MG Road metro station")
    _make_crime(db, "CR-T-002", 12.971, 77.601, "ROBBERY",
                datetime(2026, 6, 11, 21, 15, tzinfo=timezone.utc),
                "Purse snatched with knife threat near MG Road")
    _make_crime(db, "CR-T-003", 12.973, 77.599, "THEFT",
                datetime(2026, 6, 12, 19, 45, tzinfo=timezone.utc),
                "Laptop stolen from coffee shop near Brigade Road")

    # Bangalore cluster 2: Koramangala area (lat~12.93, lon~77.62)
    _make_crime(db, "CR-T-004", 12.934, 77.621, "BURGLARY",
                datetime(2026, 7, 1, 2, 0, tzinfo=timezone.utc),
                "Forced entry into flat during night hours")
    _make_crime(db, "CR-T-005", 12.935, 77.622, "BURGLARY",
                datetime(2026, 7, 2, 3, 30, tzinfo=timezone.utc),
                "Lock broken, burglar entered house via window")
    _make_crime(db, "CR-T-006", 12.933, 77.620, "VANDALISM",
                datetime(2026, 7, 3, 1, 0, tzinfo=timezone.utc),
                "Damage to shop shutters overnight")

    # Distant outlier: Mysore (~150km away)
    _make_crime(db, "CR-T-007", 12.295, 76.644, "ASSAULT",
                datetime(2026, 8, 5, 22, 0, tzinfo=timezone.utc),
                "Physical altercation in Mysore market area")

    # More central Bangalore crimes for temporal analysis
    for i in range(8, 16):
        hour = (i * 3) % 24
        _make_crime(
            db, f"CR-T-{i:03d}", 12.960 + (i * 0.002), 77.590 + (i * 0.001),
            ["THEFT", "FRAUD", "NARCOTICS"][i % 3],
            datetime(2026, 6 + (i % 3), i, hour, 0, tzinfo=timezone.utc),
            f"Crime incident number {i} - test description for pattern analysis"
        )

    db.commit()
    return db


# ──────────────────────────────────────────────────────────────────────────────
# Spatial Clustering Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_spatial_dbscan_clustering(populated_db):
    """DBSCAN should identify at least 1 cluster from Bangalore crime concentration."""
    from app.services.ml.spatial import SpatialAnalysisService

    result = SpatialAnalysisService.run(populated_db, eps_km=2.0, min_samples=2)

    assert result["status"] in ("completed", "insufficient_data")
    if result["status"] == "completed":
        assert result["clusters_found"] >= 1
        assert result["crime_count"] >= 2
        assert "eps_km" in result
    else:
        # Small dataset — still valid
        assert "message" in result


def test_spatial_empty_dataset(test_db):
    """Spatial clustering with no data should return insufficient_data gracefully."""
    from app.services.ml.spatial import SpatialAnalysisService

    # Clear crimes
    test_db.query(Crime).delete()
    test_db.commit()

    result = SpatialAnalysisService.run(test_db)
    assert result["status"] == "insufficient_data"
    assert result["crime_count"] == 0


def test_spatial_cluster_members_traceable(populated_db):
    """Spatial clusters must have traceable crime ID members."""
    from app.services.ml.spatial import SpatialAnalysisService

    result = SpatialAnalysisService.run(populated_db, eps_km=2.0, min_samples=2)
    if result["status"] != "completed" or result["clusters_found"] == 0:
        pytest.skip("Insufficient data for cluster membership test")

    clusters = populated_db.query(CrimeCluster).filter(
        CrimeCluster.cluster_type == "spatial"
    ).all()
    assert len(clusters) > 0

    for cluster in clusters:
        members = populated_db.query(CrimeClusterMember).filter(
            CrimeClusterMember.cluster_id == cluster.id
        ).all()
        assert len(members) >= 2  # DBSCAN min_samples=2
        assert cluster.crime_count == len(members)


# ──────────────────────────────────────────────────────────────────────────────
# Temporal Analysis Tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def temporal_db():
    """Dedicated DB for temporal tests with guaranteed crime records."""
    import sqlite3
    from sqlalchemy import event

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def add_geo_functions(dbapi_conn, connection_record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.create_function("ST_GeogFromText", 1, lambda v: v)
            dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda v: "{}")
            dbapi_conn.create_function("AsBinary", 1, lambda v: v)

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Create crimes at specific hours and days
    batch = ImportBatch(id="batch-temp-001", filename="temporal.csv", file_type="CSV",
                        total_rows=10, valid_count=10, rejected_count=0)
    db.add(batch)
    db.flush()

    times = [
        datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),   # Monday 08:00
        datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),  # Monday 20:00
        datetime(2026, 6, 2, 20, 0, tzinfo=timezone.utc),  # Tuesday 20:00
        datetime(2026, 6, 3, 21, 0, tzinfo=timezone.utc),  # Wednesday 21:00
        datetime(2026, 6, 8, 20, 0, tzinfo=timezone.utc),  # Monday 20:00
        datetime(2026, 7, 1, 3, 0, tzinfo=timezone.utc),   # Different month
        datetime(2026, 7, 2, 3, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 3, 20, 0, tzinfo=timezone.utc),
        datetime(2026, 8, 1, 20, 0, tzinfo=timezone.utc),
        datetime(2026, 8, 2, 20, 0, tzinfo=timezone.utc),
    ]
    for i, t in enumerate(times):
        crime = Crime(
            id=str(uuid.uuid4()),
            record_id=f"CR-TMP-{i:03d}",
            crime_type="theft",
            category="THEFT",
            location_name="Test Location",
            latitude=12.97 + i * 0.001,
            longitude=77.60 + i * 0.001,
            occurred_at=t,
            source="Test",
            status="VALID",
            import_batch_id="batch-temp-001",
        )
        db.add(crime)

    db.commit()
    yield db
    db.close()


def test_temporal_hourly_aggregation(temporal_db):
    """Hourly analysis should produce 24-bucket counts."""
    from app.services.ml.temporal import TemporalAnalysisService

    result = TemporalAnalysisService.run(temporal_db)
    assert result["status"] == "completed"
    assert result["hourly_buckets"] > 0

    hourly = TemporalAnalysisService.get_hourly_distribution(temporal_db)
    assert len(hourly) > 0
    # Most crimes above are at 20:00
    hour_map = {h["period"]: h["crime_count"] for h in hourly}
    assert "20:00" in hour_map
    assert hour_map["20:00"] >= 5  # Most crimes at 20:00


def test_temporal_daily_aggregation(temporal_db):
    """Daily analysis should produce day-of-week counts."""
    from app.services.ml.temporal import TemporalAnalysisService

    daily = TemporalAnalysisService.get_daily_distribution(temporal_db)
    assert len(daily) > 0
    day_names = [d["period"] for d in daily]
    # Should include at least one recognized day name
    recognized = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
    assert any(d in recognized for d in day_names)


def test_temporal_monthly_trend(temporal_db):
    """Monthly analysis should produce per-month aggregation."""
    from app.services.ml.temporal import TemporalAnalysisService

    monthly = TemporalAnalysisService.get_monthly_trends(temporal_db)
    assert len(monthly) >= 2  # At least June and July
    periods = [m["period"] for m in monthly]
    assert "2026-06" in periods or "2026-07" in periods


def test_temporal_rolling_average(temporal_db):
    """Rolling averages should be calculated for monthly trends."""
    from app.services.ml.temporal import TemporalAnalysisService

    monthly = TemporalAnalysisService.get_monthly_trends(temporal_db)
    # All monthly entries should have rolling_average populated
    for m in monthly:
        assert m["rolling_average"] is not None
        assert m["rolling_average"] >= 0


# ──────────────────────────────────────────────────────────────────────────────
# Semantic Clustering Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_semantic_clustering_from_vectors(populated_db):
    """Semantic clustering should handle available vectors."""
    from app.services.ml.clustering import SemanticClusteringService

    # Patch Qdrant scroll to return synthetic vectors
    mock_points = []
    crimes = populated_db.query(Crime).filter(Crime.status == "VALID").limit(10).all()
    for crime in crimes:
        pt = MagicMock()
        pt.vector = list(np.random.rand(384).astype(float))
        pt.payload = {"crime_id": crime.id, "category": crime.category}
        mock_points.append(pt)

    with patch.object(
        SemanticClusteringService, "_load_vectors",
        return_value=(
            np.array([p.vector for p in mock_points], dtype=float),
            {mock_points[i].payload["crime_id"]: i for i in range(len(mock_points))}
        )
    ):
        result = SemanticClusteringService.run(populated_db)
        assert result["status"] in ("completed", "insufficient_data")
        if result["status"] == "completed":
            assert result["vector_count"] >= 2


def test_semantic_cluster_membership(populated_db):
    """Semantic clusters must have traceable crime ID members."""
    clusters = populated_db.query(CrimeCluster).filter(
        CrimeCluster.cluster_type == "semantic"
    ).all()

    for cluster in clusters:
        members = populated_db.query(CrimeClusterMember).filter(
            CrimeClusterMember.cluster_id == cluster.id
        ).all()
        assert len(members) > 0
        # Every member must reference a valid crime
        for member in members:
            crime = populated_db.query(Crime).filter(Crime.id == member.crime_id).first()
            assert crime is not None, f"Cluster member references non-existent crime {member.crime_id}"


# ──────────────────────────────────────────────────────────────────────────────
# Anomaly Detection Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_anomaly_isolation_forest_normal_data():
    """Normal data should produce low anomaly count."""
    import sqlite3
    from sqlalchemy import event

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def add_geo(dbapi_conn, connection_record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.create_function("ST_GeogFromText", 1, lambda v: v)
            dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda v: "{}")
            dbapi_conn.create_function("AsBinary", 1, lambda v: v)

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    batch = ImportBatch(id="batch-anom-001", filename="test.csv", file_type="CSV",
                        total_rows=10, valid_count=10, rejected_count=0)
    db.add(batch)
    db.flush()

    # Uniform grid of crimes — all similar, no outliers
    for i in range(10):
        crime = Crime(
            id=str(uuid.uuid4()),
            record_id=f"CR-NORM-{i:03d}",
            crime_type="theft",
            category="THEFT",
            location_name="Normal Area",
            latitude=12.97 + i * 0.0001,
            longitude=77.60 + i * 0.0001,
            occurred_at=datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
            source="Test",
            status="VALID",
            import_batch_id="batch-anom-001",
        )
        db.add(crime)
    db.commit()

    from app.services.ml.anomaly import AnomalyDetectionService
    result = AnomalyDetectionService.run(db)

    assert result["status"] in ("completed", "insufficient_data")
    if result["status"] == "completed":
        # With contamination=0.15, at most 15% of 10 = 1-2 anomalies
        assert result["statistical_anomalies"] <= 3

    db.close()


def test_anomaly_isolation_forest_anomalous_data():
    """Clearly outlier crime should be detected as anomalous."""
    import sqlite3
    from sqlalchemy import event

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def add_geo(dbapi_conn, connection_record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.create_function("ST_GeogFromText", 1, lambda v: v)
            dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda v: "{}")
            dbapi_conn.create_function("AsBinary", 1, lambda v: v)

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    batch = ImportBatch(id="batch-anom-002", filename="test.csv", file_type="CSV",
                        total_rows=12, valid_count=12, rejected_count=0)
    db.add(batch)
    db.flush()

    # 10 uniform crimes
    for i in range(10):
        crime = Crime(
            id=str(uuid.uuid4()),
            record_id=f"CR-BASE-{i:03d}",
            crime_type="theft",
            category="THEFT",
            location_name="Cluster Area",
            latitude=12.97 + i * 0.0001,
            longitude=77.60 + i * 0.0001,
            occurred_at=datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
            source="Test",
            status="VALID",
            import_batch_id="batch-anom-002",
        )
        db.add(crime)

    # 2 clear outliers: distant location + unusual hour
    db.add(Crime(
        id=str(uuid.uuid4()),
        record_id="CR-OUTLIER-001",
        crime_type="homicide",
        category="HOMICIDE",
        location_name="Remote Area",
        latitude=28.61,   # Delhi — far from Bangalore cluster
        longitude=77.20,
        occurred_at=datetime(2026, 6, 1, 3, 0, tzinfo=timezone.utc),  # 3 AM
        source="Test",
        status="VALID",
        import_batch_id="batch-anom-002",
    ))
    db.add(Crime(
        id=str(uuid.uuid4()),
        record_id="CR-OUTLIER-002",
        crime_type="cybercrime",
        category="CYBERCRIME",
        location_name="Another Remote Area",
        latitude=19.07,   # Mumbai
        longitude=72.87,
        occurred_at=datetime(2026, 6, 1, 4, 0, tzinfo=timezone.utc),
        source="Test",
        status="VALID",
        import_batch_id="batch-anom-002",
    ))
    db.commit()

    from app.services.ml.anomaly import AnomalyDetectionService
    result = AnomalyDetectionService.run(db)

    assert result["status"] == "completed"
    assert result["anomalies_found"] >= 1

    db.close()


def test_anomaly_explanation_required(temporal_db):
    """Every anomaly must have a non-empty human-readable explanation."""
    from app.services.ml.anomaly import AnomalyDetectionService

    AnomalyDetectionService.run(temporal_db)
    anomalies = temporal_db.query(CrimeAnomaly).all()
    for anomaly in anomalies:
        assert anomaly.explanation is not None
        assert len(anomaly.explanation.strip()) > 10, (
            f"Anomaly {anomaly.id} has insufficient explanation: '{anomaly.explanation}'"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Pattern Analysis Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_pattern_generation_evidence_references(populated_db):
    """Every pattern must have a non-empty evidence list of crime IDs."""
    from app.services.ml.spatial import SpatialAnalysisService
    from app.services.ml.patterns import PatternAnalysisService

    SpatialAnalysisService.run(populated_db, eps_km=2.0, min_samples=2)
    result = PatternAnalysisService.run(populated_db)

    assert result["status"] == "completed"

    patterns = populated_db.query(CrimePattern).all()
    for pattern in patterns:
        assert pattern.evidence is not None
        assert isinstance(pattern.evidence, list)
        assert len(pattern.evidence) >= 2, f"Pattern {pattern.id} has fewer than 2 evidence crimes"
        # All evidence crime IDs must reference valid crimes
        for crime_id in pattern.evidence:
            crime = populated_db.query(Crime).filter(Crime.id == crime_id).first()
            assert crime is not None, f"Pattern evidence references non-existent crime {crime_id}"


def test_pattern_confidence_in_range(populated_db):
    """Pattern confidence must be in [0.0, 1.0]."""
    patterns = populated_db.query(CrimePattern).all()
    for pattern in patterns:
        if pattern.confidence is not None:
            assert 0.0 <= pattern.confidence <= 1.0, (
                f"Pattern {pattern.id} has out-of-range confidence: {pattern.confidence}"
            )


def test_pattern_description_not_empty(populated_db):
    """Every pattern must have a non-empty human-readable description."""
    patterns = populated_db.query(CrimePattern).all()
    for pattern in patterns:
        assert pattern.description is not None
        assert len(pattern.description.strip()) > 20


# ──────────────────────────────────────────────────────────────────────────────
# ML Stats API Test
# ──────────────────────────────────────────────────────────────────────────────

def test_ml_stats_structure(populated_db):
    """MLAnalysisService.get_stats() should return the expected key structure."""
    from app.services.ml.orchestrator import MLAnalysisService

    stats = MLAnalysisService.get_stats(populated_db)
    required_keys = [
        "total_crimes_analyzed", "total_clusters", "spatial_clusters",
        "semantic_clusters", "total_hotspots", "total_anomalies",
        "total_patterns", "trend_records",
    ]
    for key in required_keys:
        assert key in stats, f"Missing key '{key}' in ML stats response"
        assert stats[key] >= 0
