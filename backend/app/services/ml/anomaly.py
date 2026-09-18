"""
Phase 3 — Anomaly Detection Service
Identifies unusual crime incidents or temporal periods using:
  - Isolation Forest on per-incident feature vectors (statistical/spatial anomaly)
  - Statistical baseline comparison for temporal anomalies (observed vs historical average)

Every anomaly gets a human-readable explanation.
anomaly_type: 'statistical' | 'spatial' | 'temporal'

IMPORTANT: Anomalies are flagged at the INCIDENT or PERIOD level — not individual persons.
This does not constitute predictive policing or individual risk scoring.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.models.ml_models import CrimeAnomaly, CrimeTrend
from app.core.config import settings

logger = logging.getLogger("connectdots_ml_anomaly")

# Canonical categories for encoding
CATEGORIES = [
    "THEFT", "BURGLARY", "ROBBERY", "ASSAULT", "HOMICIDE",
    "VEHICLE_THEFT", "FRAUD", "CYBERCRIME", "NARCOTICS", "VANDALISM",
]


class AnomalyDetectionService:
    """
    Detects anomalous crime incidents and temporal periods.
    Results are stored as CrimeAnomaly records with mandatory human-readable explanations.
    """

    @classmethod
    def run(cls, db: Session) -> Dict[str, Any]:
        """Main entry point — runs statistical + temporal anomaly detection."""
        crimes = db.query(
            Crime.id,
            Crime.record_id,
            Crime.latitude,
            Crime.longitude,
            Crime.category,
            Crime.occurred_at,
        ).filter(
            Crime.status == "VALID",
            Crime.latitude.isnot(None),
            Crime.longitude.isnot(None),
            Crime.occurred_at.isnot(None),
        ).all()

        if len(crimes) < 5:
            logger.info(f"Anomaly detection: insufficient data ({len(crimes)} records, need >= 5).")
            return {
                "status": "insufficient_data",
                "crime_count": len(crimes),
                "anomalies_found": 0,
                "message": f"Only {len(crimes)} valid crime record(s). Need at least 5 for anomaly detection."
            }

        # Remove old anomaly records
        db.query(CrimeAnomaly).delete()
        db.flush()

        stat_anomalies = cls._run_isolation_forest(db, crimes)
        temp_anomalies = cls._run_temporal_anomalies(db)

        db.commit()
        total = stat_anomalies + temp_anomalies
        logger.info(f"Anomaly detection committed: {total} anomalies ({stat_anomalies} statistical, {temp_anomalies} temporal).")

        return {
            "status": "completed",
            "crime_count": len(crimes),
            "anomalies_found": total,
            "statistical_anomalies": stat_anomalies,
            "temporal_anomalies": temp_anomalies,
        }

    @classmethod
    def _run_isolation_forest(cls, db: Session, crimes: list) -> int:
        """
        Isolation Forest on feature vector: [hour, day_of_week, lat, lon, category_encoded].
        Flags incidents that are outliers in the combined feature space.
        """
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            logger.error("scikit-learn not installed. Cannot run Isolation Forest.")
            return 0

        cat_index = {cat: i for i, cat in enumerate(CATEGORIES)}

        features = []
        for c in crimes:
            hour = c.occurred_at.hour if c.occurred_at else 12
            dow = c.occurred_at.weekday() if c.occurred_at else 0
            lat = float(c.latitude) if c.latitude else 0.0
            lon = float(c.longitude) if c.longitude else 0.0
            cat_enc = cat_index.get(str(c.category).upper(), len(CATEGORIES))
            features.append([hour, dow, lat, lon, cat_enc])

        X = np.array(features, dtype=float)

        contamination = min(settings.ML_ANOMALY_CONTAMINATION, 0.5)
        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        preds = model.fit_predict(X)           # -1 = anomaly, 1 = normal
        scores = model.decision_function(X)    # lower = more anomalous

        anomaly_count = 0
        for i, (crime, pred, score) in enumerate(zip(crimes, preds, scores)):
            if pred == -1:
                # Determine spatial vs statistical anomaly type
                hour = features[i][0]
                lat, lon = features[i][2], features[i][3]

                # Compute local density for context
                lats = [f[2] for f in features]
                lons = [f[3] for f in features]
                avg_lat = np.mean(lats)
                avg_lon = np.mean(lons)
                dist_from_center = (
                    (lat - avg_lat) ** 2 + (lon - avg_lon) ** 2
                ) ** 0.5

                if dist_from_center > np.std(lats) * 2:
                    anomaly_type = "spatial"
                    explanation = (
                        f"This incident at {crime.record_id} was flagged because its geographic location "
                        f"is significantly farther from the main crime concentration area than typical incidents."
                    )
                else:
                    anomaly_type = "statistical"
                    explanation = (
                        f"Incident {crime.record_id} was flagged as statistically unusual based on its "
                        f"combination of crime category ({crime.category}), time of occurrence "
                        f"({hour:02d}:00), and geographic location relative to the overall dataset distribution."
                    )

                anomaly = CrimeAnomaly(
                    crime_id=crime.id,
                    anomaly_type=anomaly_type,
                    anomaly_score=round(float(score), 6),
                    explanation=explanation,
                    category=crime.category,
                    metadata_={
                        "record_id": crime.record_id,
                        "isolation_forest_score": round(float(score), 6),
                        "hour": int(hour),
                        "day_of_week": int(features[i][1]),
                        "latitude": lat,
                        "longitude": lon,
                    }
                )
                db.add(anomaly)
                anomaly_count += 1

        db.flush()
        return anomaly_count

    @classmethod
    def _run_temporal_anomalies(cls, db: Session) -> int:
        """
        Compares observed weekly crime volume against historical rolling baseline.
        Flags weeks that are more than 2 standard deviations above the mean.
        """
        is_postgres = "postgresql" in str(db.bind.url) if db.bind else False

        if is_postgres:
            rows = db.execute(text("""
                SELECT
                    TO_CHAR(date_trunc('week', occurred_at), 'YYYY-"W"IW') AS week,
                    COUNT(*) AS cnt
                FROM crimes
                WHERE status = 'VALID' AND occurred_at IS NOT NULL
                GROUP BY 1
                ORDER BY 1
            """)).fetchall()
        else:
            rows = db.execute(text("""
                SELECT
                    strftime('%Y-W%W', occurred_at) AS week,
                    COUNT(*) AS cnt
                FROM crimes
                WHERE status = 'VALID' AND occurred_at IS NOT NULL
                GROUP BY 1
                ORDER BY 1
            """)).fetchall()

        if len(rows) < 3:
            return 0

        weeks = [r[0] for r in rows]
        counts = [int(r[1]) for r in rows]

        mean_count = np.mean(counts)
        std_count = np.std(counts)
        threshold = mean_count + (2.0 * std_count) if std_count > 0 else mean_count * 1.5

        anomaly_count = 0
        for week, count in zip(weeks, counts):
            if count > threshold and std_count > 0:
                explanation = (
                    f"Crime volume during week {week} was unusually high compared with the historical baseline. "
                    f"Observed: {count} incidents. Historical average: {mean_count:.1f} incidents/week "
                    f"(threshold: {threshold:.1f}). "
                    f"This period was flagged because observed crime volume exceeded the established baseline "
                    f"by more than 2 standard deviations."
                )
                anomaly = CrimeAnomaly(
                    crime_id=None,
                    anomaly_type="temporal",
                    anomaly_score=round((count - mean_count) / (std_count + 1e-9), 4),
                    baseline_value=round(float(mean_count), 2),
                    observed_value=float(count),
                    period=week,
                    explanation=explanation,
                    metadata_={
                        "week": week,
                        "crime_count": count,
                        "historical_mean": round(float(mean_count), 2),
                        "historical_std": round(float(std_count), 2),
                        "threshold": round(float(threshold), 2),
                    }
                )
                db.add(anomaly)
                anomaly_count += 1

        db.flush()
        return anomaly_count
