"""
Phase 3 — Temporal Analysis Service
Analyzes crime occurrence patterns across time dimensions:
  - Hourly distribution (24 buckets)
  - Day-of-week distribution (7 buckets)
  - Monthly trends with rolling average

Uses PostgreSQL aggregation to avoid loading large datasets into memory.
Persists results as CrimeTrend records.
"""
import logging
from collections import defaultdict
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, text

from app.models.crime import Crime
from app.models.ml_models import CrimeTrend
from app.core.config import settings

logger = logging.getLogger("connectdots_ml_temporal")

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class TemporalAnalysisService:
    """
    Aggregates crime events across time dimensions using PostgreSQL group-by queries.
    All results are stored as CrimeTrend records.
    Original crime data is never modified.
    """

    @classmethod
    def run(cls, db: Session) -> Dict[str, Any]:
        """Main entry point — runs all temporal analyses and persists results."""
        crimes_exist = db.query(Crime.id).filter(Crime.status == "VALID").first()
        if not crimes_exist:
            return {
                "status": "insufficient_data",
                "message": "No valid crime records found for temporal analysis."
            }

        # Delete previous trend records to avoid duplicates
        db.query(CrimeTrend).delete()
        db.flush()

        hourly = cls._run_hourly(db)
        daily = cls._run_daily(db)
        monthly = cls._run_monthly(db)

        db.commit()
        logger.info("Temporal analysis committed to database.")

        return {
            "status": "completed",
            "hourly_buckets": len(hourly),
            "daily_buckets": len(daily),
            "monthly_buckets": len(monthly),
            "peak_hour": cls._find_peak(hourly, "period"),
            "peak_day": cls._find_peak(daily, "period"),
        }

    @classmethod
    def _run_hourly(cls, db: Session) -> List[Dict]:
        """Aggregates crime counts by hour of day (0-23) across all categories."""
        is_postgres = "postgresql" in str(db.bind.url) if db.bind else False

        if is_postgres:
            rows = db.execute(text("""
                SELECT
                    EXTRACT(HOUR FROM occurred_at)::int AS hour,
                    category,
                    COUNT(*) AS cnt
                FROM crimes
                WHERE status = 'VALID' AND occurred_at IS NOT NULL
                GROUP BY 1, 2
                ORDER BY 1
            """)).fetchall()
        else:
            # SQLite fallback
            rows = db.execute(text("""
                SELECT
                    CAST(strftime('%H', occurred_at) AS INTEGER) AS hour,
                    category,
                    COUNT(*) AS cnt
                FROM crimes
                WHERE status = 'VALID' AND occurred_at IS NOT NULL
                GROUP BY 1, 2
                ORDER BY 1
            """)).fetchall()

        records = []
        for row in rows:
            hour, category, cnt = row
            period_str = f"{int(hour):02d}:00"
            trend = CrimeTrend(
                period=period_str,
                period_type="hourly",
                category=category,
                crime_count=int(cnt),
            )
            db.add(trend)
            records.append({"period": period_str, "category": category, "count": int(cnt)})

        # Also create "ALL" category totals
        hour_totals: Dict[str, int] = defaultdict(int)
        for r in records:
            hour_totals[r["period"]] += r["count"]
        for period_str, total in hour_totals.items():
            db.add(CrimeTrend(period=period_str, period_type="hourly", category=None, crime_count=total))

        db.flush()
        return records

    @classmethod
    def _run_daily(cls, db: Session) -> List[Dict]:
        """Aggregates crime counts by day of week."""
        is_postgres = "postgresql" in str(db.bind.url) if db.bind else False

        if is_postgres:
            # PostgreSQL: DOW 0=Sunday...6=Saturday — remap to 0=Monday...6=Sunday
            rows = db.execute(text("""
                SELECT
                    EXTRACT(DOW FROM occurred_at)::int AS dow,
                    category,
                    COUNT(*) AS cnt
                FROM crimes
                WHERE status = 'VALID' AND occurred_at IS NOT NULL
                GROUP BY 1, 2
                ORDER BY 1
            """)).fetchall()
            # PG DOW: 0=Sun, 1=Mon...6=Sat → remap to Monday-first
            dow_to_name = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
                           5: "Friday", 6: "Saturday", 0: "Sunday"}
        else:
            rows = db.execute(text("""
                SELECT
                    CAST(strftime('%w', occurred_at) AS INTEGER) AS dow,
                    category,
                    COUNT(*) AS cnt
                FROM crimes
                WHERE status = 'VALID' AND occurred_at IS NOT NULL
                GROUP BY 1, 2
                ORDER BY 1
            """)).fetchall()
            # SQLite strftime %w: 0=Sunday...6=Saturday
            dow_to_name = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
                           5: "Friday", 6: "Saturday", 0: "Sunday"}

        records = []
        for row in rows:
            dow, category, cnt = row
            day_name = dow_to_name.get(int(dow), f"Day{dow}")
            trend = CrimeTrend(
                period=day_name,
                period_type="daily",
                category=category,
                crime_count=int(cnt),
            )
            db.add(trend)
            records.append({"period": day_name, "category": category, "count": int(cnt)})

        # ALL totals
        day_totals: Dict[str, int] = defaultdict(int)
        for r in records:
            day_totals[r["period"]] += r["count"]
        for day_name, total in day_totals.items():
            db.add(CrimeTrend(period=day_name, period_type="daily", category=None, crime_count=total))

        db.flush()
        return records

    @classmethod
    def _run_monthly(cls, db: Session) -> List[Dict]:
        """Aggregates crime counts by month and calculates rolling 4-week average."""
        is_postgres = "postgresql" in str(db.bind.url) if db.bind else False

        if is_postgres:
            rows = db.execute(text("""
                SELECT
                    TO_CHAR(occurred_at, 'YYYY-MM') AS month,
                    category,
                    COUNT(*) AS cnt
                FROM crimes
                WHERE status = 'VALID' AND occurred_at IS NOT NULL
                GROUP BY 1, 2
                ORDER BY 1
            """)).fetchall()
        else:
            rows = db.execute(text("""
                SELECT
                    strftime('%Y-%m', occurred_at) AS month,
                    category,
                    COUNT(*) AS cnt
                FROM crimes
                WHERE status = 'VALID' AND occurred_at IS NOT NULL
                GROUP BY 1, 2
                ORDER BY 1
            """)).fetchall()

        # Collect totals by month for rolling average
        month_totals: Dict[str, int] = defaultdict(int)
        records = []
        for row in rows:
            month, category, cnt = row
            month_totals[month] += int(cnt)
            records.append({"period": month, "category": category, "count": int(cnt)})

        # Compute rolling N-period average on monthly totals
        window = settings.ML_ROLLING_WINDOW_WEEKS
        sorted_months = sorted(month_totals.keys())
        rolling: Dict[str, float] = {}
        for i, m in enumerate(sorted_months):
            window_vals = [month_totals[sorted_months[j]] for j in range(max(0, i - window + 1), i + 1)]
            rolling[m] = round(sum(window_vals) / len(window_vals), 2)

        # Persist
        for row in records:
            month, category, cnt = row["period"], row["category"], row["count"]
            trend = CrimeTrend(
                period=month,
                period_type="monthly",
                category=category,
                crime_count=cnt,
                rolling_average=rolling.get(month),
            )
            db.add(trend)

        # ALL totals
        for month in sorted_months:
            db.add(CrimeTrend(
                period=month,
                period_type="monthly",
                category=None,
                crime_count=month_totals[month],
                rolling_average=rolling.get(month),
            ))

        db.flush()
        return records

    @staticmethod
    def _find_peak(records: List[Dict], key: str) -> Optional[str]:
        """Returns the period with the highest crime count."""
        if not records:
            return None
        totals: Dict[str, int] = defaultdict(int)
        for r in records:
            totals[r[key]] += r["count"]
        return max(totals, key=totals.get) if totals else None

    @classmethod
    def get_hourly_distribution(cls, db: Session, category: Optional[str] = None) -> List[Dict]:
        """Returns hourly crime distribution (all hours 0-23), optionally filtered by category."""
        query = db.query(CrimeTrend).filter(CrimeTrend.period_type == "hourly")
        if category:
            query = query.filter(CrimeTrend.category == category.upper())
        else:
            query = query.filter(CrimeTrend.category.is_(None))
        trends = query.order_by(CrimeTrend.period).all()
        return [{"period": t.period, "crime_count": t.crime_count} for t in trends]

    @classmethod
    def get_daily_distribution(cls, db: Session, category: Optional[str] = None) -> List[Dict]:
        """Returns daily (day-of-week) crime distribution."""
        query = db.query(CrimeTrend).filter(CrimeTrend.period_type == "daily")
        if category:
            query = query.filter(CrimeTrend.category == category.upper())
        else:
            query = query.filter(CrimeTrend.category.is_(None))
        trends = query.all()
        # Sort by day-of-week order
        day_order = {d: i for i, d in enumerate(DAY_NAMES)}
        return sorted(
            [{"period": t.period, "crime_count": t.crime_count} for t in trends],
            key=lambda x: day_order.get(x["period"], 99)
        )

    @classmethod
    def get_monthly_trends(cls, db: Session, category: Optional[str] = None) -> List[Dict]:
        """Returns monthly crime trends with rolling average."""
        query = db.query(CrimeTrend).filter(CrimeTrend.period_type == "monthly")
        if category:
            query = query.filter(CrimeTrend.category == category.upper())
        else:
            query = query.filter(CrimeTrend.category.is_(None))
        trends = query.order_by(CrimeTrend.period).all()
        return [
            {"period": t.period, "crime_count": t.crime_count, "rolling_average": t.rolling_average}
            for t in trends
        ]
