from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc, and_

from app.models.crime import Crime, ImportBatch, CrimeRejection
from app.schemas.crime import GeoJSONFeatureCollection, GeoJSONFeature, GeoJSONGeometry


class CrimeRepository:
    """Encapsulates all database operations for Crime incidents and Batches."""

    @classmethod
    def get_by_id(cls, db: Session, crime_id: str) -> Optional[Crime]:
        return db.execute(select(Crime).where(Crime.id == crime_id)).scalar_one_or_none()

    @classmethod
    def get_by_record_id(cls, db: Session, record_id: str) -> Optional[Crime]:
        return db.execute(select(Crime).where(Crime.record_id == record_id)).scalar_one_or_none()

    @classmethod
    def list_crimes(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        crime_type: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "occurred_at",
        order: str = "desc"
    ) -> Tuple[List[Crime], int]:
        """Queries crimes with flexible filtering, search, pagination, and sorting."""
        stmt = select(Crime)
        count_stmt = select(func.count(Crime.id))

        conditions = []

        if search:
            search_pattern = f"%{search.strip()}%"
            conditions.append(
                (Crime.record_id.ilike(search_pattern)) |
                (Crime.crime_type.ilike(search_pattern)) |
                (Crime.location_name.ilike(search_pattern)) |
                (Crime.description.ilike(search_pattern))
            )

        if crime_type:
            conditions.append(Crime.crime_type.ilike(f"%{crime_type.strip()}%"))

        if category:
            conditions.append(Crime.category == category.strip().upper())

        if location:
            conditions.append(Crime.location_name.ilike(f"%{location.strip()}%"))

        if start_date:
            conditions.append(Crime.occurred_at >= start_date)

        if end_date:
            conditions.append(Crime.occurred_at <= end_date)

        if source:
            conditions.append(Crime.source.ilike(f"%{source.strip()}%"))

        if status:
            conditions.append(Crime.status == status.strip().upper())

        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        # Total count
        total = db.execute(count_stmt).scalar() or 0

        # Sorting
        sort_column = getattr(Crime, sort_by, Crime.occurred_at)
        if order.lower() == "asc":
            stmt = stmt.order_by(asc(sort_column))
        else:
            stmt = stmt.order_by(desc(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        items = db.execute(stmt).scalars().all()
        return list(items), total

    @classmethod
    def delete(cls, db: Session, crime: Crime) -> None:
        db.delete(crime)
        db.commit()

    @classmethod
    def get_locations_geojson(
        cls,
        db: Session,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> GeoJSONFeatureCollection:
        """Extracts valid geographic points formatted as a GeoJSON FeatureCollection."""
        stmt = select(
            Crime.id,
            Crime.record_id,
            Crime.crime_type,
            Crime.category,
            Crime.location_name,
            Crime.occurred_at,
            Crime.latitude,
            Crime.longitude,
            Crime.description,
            Crime.source
        )

        conditions = [Crime.latitude.isnot(None), Crime.longitude.isnot(None)]
        if category:
            conditions.append(Crime.category == category.strip().upper())
        if start_date:
            conditions.append(Crime.occurred_at >= start_date)
        if end_date:
            conditions.append(Crime.occurred_at <= end_date)

        stmt = stmt.where(and_(*conditions)).limit(limit)
        rows = db.execute(stmt).all()

        features = []
        for r in rows:
            feat = GeoJSONFeature(
                geometry=GeoJSONGeometry(coordinates=[r.longitude, r.latitude]),
                properties={
                    "id": r.id,
                    "record_id": r.record_id,
                    "crime_type": r.crime_type,
                    "category": r.category,
                    "location": r.location_name,
                    "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
                    "description": r.description,
                    "source": r.source
                }
            )
            features.append(feat)

        return GeoJSONFeatureCollection(features=features)

    @classmethod
    def get_statistics(cls, db: Session) -> Dict[str, Any]:
        """Calculates dashboard KPI metrics, category breakdowns, and geographic coverage."""
        total_crimes = db.execute(select(func.count(Crime.id))).scalar() or 0
        total_batches = db.execute(select(func.count(ImportBatch.id))).scalar() or 0
        total_rejected = db.execute(select(func.count(CrimeRejection.id))).scalar() or 0

        # Distribution by category
        cat_rows = db.execute(
            select(Crime.category, func.count(Crime.id))
            .group_by(Crime.category)
            .order_by(desc(func.count(Crime.id)))
        ).all()
        by_category = {r[0]: r[1] for r in cat_rows}

        # Distribution by source
        src_rows = db.execute(
            select(Crime.source, func.count(Crime.id))
            .group_by(Crime.source)
            .order_by(desc(func.count(Crime.id)))
            .limit(10)
        ).all()
        by_source = {r[0]: r[1] for r in src_rows}

        # Geographic bounding coverage
        geo_row = db.execute(
            select(
                func.min(Crime.latitude),
                func.max(Crime.latitude),
                func.min(Crime.longitude),
                func.max(Crime.longitude)
            )
        ).first()

        geo_coverage = None
        if geo_row and geo_row[0] is not None:
            geo_coverage = {
                "min_latitude": float(geo_row[0]),
                "max_latitude": float(geo_row[1]),
                "min_longitude": float(geo_row[2]),
                "max_longitude": float(geo_row[3])
            }

        return {
            "total_crimes": total_crimes,
            "total_batches": total_batches,
            "total_valid": total_crimes,
            "total_rejected": total_rejected,
            "by_category": by_category,
            "by_source": by_source,
            "geo_coverage": geo_coverage
        }

    @classmethod
    def list_batches(cls, db: Session, skip: int = 0, limit: int = 20) -> List[ImportBatch]:
        return db.execute(
            select(ImportBatch).order_by(desc(ImportBatch.created_at)).offset(skip).limit(limit)
        ).scalars().all()

    @classmethod
    def get_batch_rejections(cls, db: Session, batch_id: str) -> List[CrimeRejection]:
        return db.execute(
            select(CrimeRejection)
            .where(CrimeRejection.import_batch_id == batch_id)
            .order_by(CrimeRejection.row_number)
        ).scalars().all()
