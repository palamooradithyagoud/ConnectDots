"""
Phase 4 Telecommunications: Telecom & CDR Intelligence API Endpoints
Provides routes for CDR file ingestion, phone registry queries, network analytics,
and cross-case telecommunication discoveries.
"""
import math
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.db.session import get_db
from app.models.telecom import PhoneNumber, CdrRecord, CrimePhoneAssociation
from app.models.crime import Crime
from app.schemas.telecom import (
    PhoneResponse,
    PhoneListResponse,
    PhoneDetailResponse,
    CdrResponse,
    CdrListResponse,
    CdrImportResultResponse,
    CrossCaseConnectionResponse,
)
from app.services.cdr_ingestion_service import CdrIngestionService
from app.services.telecom_analytics_service import TelecomAnalyticsService
from app.services.graph_query_service import GraphQueryService
from app.services.phone_normalization_service import PhoneNormalizationService

router = APIRouter()


@router.post("/cdr/import", response_model=CdrImportResultResponse, summary="Ingest Call Detail Records")
async def import_cdr(
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="Simulate ingestion and return validation preview without committing"),
    db: Session = Depends(get_db)
):
    """
    Ingests CDR records from a CSV or JSON file.
    Performs field alias mapping, E.164 phone normalization, SHA-256 deduplication,
    and bulk transactional commit.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        raw_records, file_type = CdrIngestionService.parse_file_content(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    result = CdrIngestionService.process_data(
        db=db,
        raw_records=raw_records,
        filename=file.filename,
        file_type=file_type,
        dry_run=dry_run
    )

    return result


@router.get("/phones", response_model=PhoneListResponse, summary="List normalized phone numbers")
def list_phones(
    search: Optional[str] = Query(None, description="Search phone number (substring or exact)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Returns paginated list of canonical E.164 phone numbers with search filtering.
    """
    query = db.query(PhoneNumber)
    if search:
        s = search.strip()
        query = query.filter(
            or_(
                PhoneNumber.normalized_number.ilike(f"%{s}%"),
                PhoneNumber.national_number.ilike(f"%{s}%"),
                PhoneNumber.carrier.ilike(f"%{s}%"),
            )
        )

    total = query.count()
    items = query.order_by(desc(PhoneNumber.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PhoneListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/phones/{phone_id_or_number}", response_model=PhoneDetailResponse, summary="Get phone profile & network metrics")
def get_phone_detail(
    phone_id_or_number: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full telecom profile, call volume metrics, top contacts, and associated crime records.
    """
    profile = TelecomAnalyticsService.get_phone_profile(db, phone_id_or_number)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Phone '{phone_id_or_number}' not found.")
    return profile


@router.get("/phones/{phone_id_or_number}/neighborhood", summary="Get phone communication graph neighborhood")
def get_phone_graph_neighborhood(
    phone_id_or_number: str,
    depth: int = Query(2, ge=1, le=3),
    max_nodes: int = Query(50, ge=5, le=100),
    db: Session = Depends(get_db)
):
    """
    Traverses Neo4j communication graph starting at the given phone number up to specified depth.
    """
    # Verify phone exists in db
    norm_res = PhoneNormalizationService.normalize(phone_id_or_number)
    search_key = norm_res.normalized_number if norm_res.is_valid else phone_id_or_number

    neighborhood = GraphQueryService.get_phone_neighborhood(
        phone_number=search_key,
        depth=depth,
        max_nodes=max_nodes
    )
    return neighborhood


@router.get("/cdr", response_model=CdrListResponse, summary="List CDR records")
def list_cdr_records(
    phone: Optional[str] = Query(None, description="Filter calls involving this phone number (inbound or outbound)"),
    call_type: Optional[str] = Query(None, description="Filter by call type (VOICE, SMS, etc.)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieves paginated call detail records with optional telephone and call type filters.
    """
    query = db.query(CdrRecord)

    if phone:
        p_clean = phone.strip()
        p_match = db.query(PhoneNumber).filter(
            or_(PhoneNumber.normalized_number == p_clean, PhoneNumber.id == p_clean)
        ).first()
        if p_match:
            query = query.filter(
                or_(CdrRecord.caller_phone_id == p_match.id, CdrRecord.callee_phone_id == p_match.id)
            )
        else:
            return CdrListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=1)

    if call_type:
        query = query.filter(CdrRecord.call_type == call_type.upper().strip())

    total = query.count()
    records = query.order_by(desc(CdrRecord.call_timestamp)).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Map caller and callee numbers for client convenience
    phone_ids = set()
    for r in records:
        phone_ids.add(r.caller_phone_id)
        phone_ids.add(r.callee_phone_id)

    phones_map = {p.id: p.normalized_number for p in db.query(PhoneNumber).filter(PhoneNumber.id.in_(phone_ids)).all()}

    items = []
    for r in records:
        items.append(CdrResponse(
            id=r.id,
            caller_phone_id=r.caller_phone_id,
            callee_phone_id=r.callee_phone_id,
            caller_number=phones_map.get(r.caller_phone_id),
            callee_number=phones_map.get(r.callee_phone_id),
            call_timestamp=r.call_timestamp,
            duration_seconds=r.duration_seconds,
            call_type=r.call_type,
            location_or_tower=r.location_or_tower,
            latitude=r.latitude,
            longitude=r.longitude,
            source_reference=r.source_reference,
            fingerprint=r.fingerprint,
            created_at=r.created_at,
        ))

    return CdrListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/crimes/{crime_id}/phones", summary="Get phone numbers associated with a crime")
def get_crime_phones(
    crime_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns all telephone numbers mentioned in or linked to a specific crime incident report.
    """
    crime = db.query(Crime).filter(or_(Crime.id == crime_id, Crime.record_id == crime_id)).first()
    if not crime:
        raise HTTPException(status_code=404, detail=f"Crime '{crime_id}' not found.")

    assocs = db.query(CrimePhoneAssociation).filter(CrimePhoneAssociation.crime_id == crime.id).all()
    phone_ids = [a.phone_id for a in assocs]
    phones = {p.id: p for p in db.query(PhoneNumber).filter(PhoneNumber.id.in_(phone_ids)).all()}

    results = []
    for a in assocs:
        p = phones.get(a.phone_id)
        if p:
            results.append({
                "phone_id": p.id,
                "normalized_number": p.normalized_number,
                "country_code": p.country_code,
                "national_number": p.national_number,
                "relationship_type": a.relationship_type,
                "confidence": a.confidence,
                "confidence_type": a.confidence_type,
                "source_text": a.source_text
            })

    return {"crime_id": crime.id, "record_id": crime.record_id, "phones": results}


@router.get("/cross-case", response_model=List[CrossCaseConnectionResponse], summary="Uncover cross-case telecom links")
def get_cross_case_telecom(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Identifies multiple crime incidents linked by common telephone numbers or active CDR communication.
    """
    connections = TelecomAnalyticsService.get_cross_case_connections(db=db, limit=limit)
    return connections
