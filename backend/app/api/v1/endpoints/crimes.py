import json
import math
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.crime import (
    CrimeResponse,
    CrimeListResponse,
    ImportResultResponse,
    StatsResponse,
    GeoJSONFeatureCollection,
    ImportBatchResponse,
    RejectionDetail
)
from app.repositories.crime_repository import CrimeRepository
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check verifying FastAPI runtime and database connectivity."""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    from datetime import timezone
    return {
        "status": "online",
        "service": "AI Crime Analysis System - Phase 1 API",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post(
    "/crimes/import",
    response_model=ImportResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Import crime incidents from CSV, JSON, or direct API payload",
    tags=["Crimes Ingestion"]
)
async def import_crimes(
    file: Optional[UploadFile] = File(None),
    raw_json: Optional[List[Dict[str, Any]]] = Body(None),
    dry_run: bool = Query(
        False,
        description="When True, validates and returns rejected diagnostics without saving to database"
    ),
    db: Session = Depends(get_db)
):
    """
    Ingests and validates crime incidents.
    Supports CSV or JSON file uploads, or a direct JSON array payload.
    Provides diagnostic error reporting for duplicate or invalid records.
    """
    if not file and not raw_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either a CSV/JSON file upload or a JSON body payload."
        )

    filename = "direct_api_payload.json"
    file_type = "JSON"

    if file:
        filename = file.filename or "upload"
        content = await file.read()
        try:
            raw_records, file_type = IngestionService.parse_file_content(content, filename)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse upload: {str(e)}"
            )
    else:
        raw_records = raw_json

    if not raw_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The provided dataset contains zero records."
        )

    result = IngestionService.process_data(
        db=db,
        raw_records=raw_records,
        filename=filename,
        file_type=file_type,
        dry_run=dry_run
    )

    return result


@router.get(
    "/crimes",
    response_model=CrimeListResponse,
    summary="Query paginated crimes with multi-parameter filtering and search",
    tags=["Crimes"]
)
def list_crimes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search across record ID, crime type, location, and description"),
    crime_type: Optional[str] = Query(None, description="Filter by crime type"),
    category: Optional[str] = Query(None, description="Filter by canonical category (e.g. THEFT, BURGLARY, ASSAULT)"),
    location: Optional[str] = Query(None, description="Filter by location name"),
    start_date: Optional[datetime] = Query(None, description="Filter incidents starting from this timestamp"),
    end_date: Optional[datetime] = Query(None, description="Filter incidents up to this timestamp"),
    source: Optional[str] = Query(None, description="Filter by reporting station or source"),
    status: Optional[str] = Query(None, description="Filter by verification status"),
    sort_by: str = Query("occurred_at", description="Field to sort by (occurred_at, record_id, category, location_name)"),
    order: str = Query("desc", description="Sort direction ('asc' or 'desc')"),
    db: Session = Depends(get_db)
):
    items, total = CrimeRepository.list_crimes(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        crime_type=crime_type,
        category=category,
        location=location,
        start_date=start_date,
        end_date=end_date,
        source=source,
        status=status,
        sort_by=sort_by,
        order=order
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return CrimeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/crimes/stats",
    response_model=StatsResponse,
    summary="Retrieve high-level crime metrics, category breakdowns, and geographic coverage",
    tags=["Crimes Analytics"]
)
def get_stats(db: Session = Depends(get_db)):
    stats = CrimeRepository.get_statistics(db)
    return stats


@router.get(
    "/crimes/locations",
    response_model=GeoJSONFeatureCollection,
    summary="Get valid spatial records as a GeoJSON FeatureCollection for map rendering",
    tags=["Crimes Spatial"]
)
def get_locations(
    category: Optional[str] = Query(None, description="Filter spatial pins by crime category"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(1000, ge=1, le=5000, description="Max coordinates to return"),
    db: Session = Depends(get_db)
):
    geojson = CrimeRepository.get_locations_geojson(
        db=db,
        category=category,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return geojson


@router.get(
    "/crimes/batches",
    response_model=List[ImportBatchResponse],
    summary="List all import batches and ingestion runs",
    tags=["Crimes Ingestion"]
)
def list_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return CrimeRepository.list_batches(db=db, skip=skip, limit=limit)


@router.get(
    "/crimes/batches/{batch_id}/rejections",
    response_model=List[RejectionDetail],
    summary="Get detailed rejected records for a specific import batch",
    tags=["Crimes Ingestion"]
)
def get_batch_rejections(
    batch_id: str,
    db: Session = Depends(get_db)
):
    rejections = CrimeRepository.get_batch_rejections(db=db, batch_id=batch_id)
    return [
        RejectionDetail(
            row_number=r.row_number,
            raw_data=r.raw_data,
            error_category=r.error_category,
            error_message=r.error_message
        )
        for r in rejections
    ]


@router.get(
    "/crimes/{crime_id}",
    response_model=CrimeResponse,
    summary="Get single crime record by ID or unique record code",
    tags=["Crimes"]
)
def get_crime(crime_id: str, db: Session = Depends(get_db)):
    crime = CrimeRepository.get_by_id(db, crime_id)
    if not crime:
        crime = CrimeRepository.get_by_record_id(db, crime_id)
    if not crime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crime incident with ID or record code '{crime_id}' not found."
        )
    return crime


@router.delete(
    "/crimes/{crime_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a crime incident",
    tags=["Crimes"]
)
def delete_crime(crime_id: str, db: Session = Depends(get_db)):
    crime = CrimeRepository.get_by_id(db, crime_id)
    if not crime:
        crime = CrimeRepository.get_by_record_id(db, crime_id)
    if not crime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crime incident '{crime_id}' not found."
        )
    CrimeRepository.delete(db, crime)
    return {"message": f"Crime incident '{crime_id}' successfully deleted."}
