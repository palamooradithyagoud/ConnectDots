"""
Phase 4 & Phase 8: Investigation Intelligence API Endpoints
Provides natural-language investigation queries powered by Graph RAG and LLM explanation,
as well as Phase 8 Unified Command Center services (Case Context, Timeline, Global Search, Report).
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.graph_rag_service import GraphRAGService
from app.services.investigation_command_service import InvestigationCommandService
from app.schemas.investigation import (
    InvestigationQueryRequest,
    InvestigationQueryResponse,
    InvestigationExamplesResponse,
    CaseContextResponse,
    CaseTimelineResponse,
    GlobalSearchResponse,
    InvestigationReportResponse
)

router = APIRouter()
logger = logging.getLogger("connectdots_investigation_api")


# ---------------------------------------------------------------------------
# Phase 4: Grounded Graph RAG
# ---------------------------------------------------------------------------
@router.post("/query", response_model=InvestigationQueryResponse, summary="Execute Grounded Investigation Query")
async def query_investigation(
    payload: InvestigationQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a multi-database Graph RAG pipeline:
      1. Parses question for crime IDs or entities
      2. Retrieves authoritative facts (PostgreSQL), semantic similarity (Qdrant), and relationships (Neo4j)
      3. Constructs a bounded EvidenceObject
      4. Synthesizes an evidence-grounded response with verifiable citations
    """
    try:
        result = await GraphRAGService.query(db=db, question=payload.question)
        return result
    except Exception as e:
        logger.error(f"Investigation query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Investigation query error: {str(e)}")


@router.get("/examples", response_model=InvestigationExamplesResponse, summary="Get Suggested Investigation Questions")
def get_example_questions():
    """
    Returns suggested queries designed for investigators.
    """
    examples = [
        "Find crimes similar to CR-2026-014 and explain the connections between them.",
        "Which incidents share the same vehicle or getaway vehicle?",
        "What crimes have a similar modus operandi?",
        "Show connections and evidence between commercial robbery incidents.",
        "What patterns are associated with armed convenience store robberies?"
    ]
    return {"examples": examples}


# ---------------------------------------------------------------------------
# Phase 8: Unified Investigation Command Center Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/case/{case_id}/context",
    response_model=CaseContextResponse,
    summary="Get Unified Case Context & Entity Topology"
)
def get_case_context(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns a unified case context dossier containing FIR details, extracted entities
    (people, phones, vehicles, weapons), connected cases, key individuals, and validation status counts.
    """
    context = InvestigationCommandService.get_case_context(db=db, case_id=case_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case incident with identifier '{case_id}' was not found."
        )
    return context


@router.get(
    "/case/{case_id}/timeline",
    response_model=CaseTimelineResponse,
    summary="Get Chronological Multi-Source Investigation Timeline"
)
def get_case_timeline(
    case_id: str,
    entity_id: Optional[str] = Query(None, description="Optional entity ID filter (person_id or phone_id)"),
    event_type: Optional[str] = Query(None, description="Filter by event type (CRIME_INCIDENT, CDR_COMMUNICATION, INVESTIGATOR_DECISION)"),
    limit: int = Query(50, ge=1, le=150, description="Max timeline events"),
    db: Session = Depends(get_db)
):
    """
    Returns a unified chronological sequence of case-related events: FIR filings,
    CDR call exchanges, relationship discoveries, and investigator review actions.
    """
    timeline = InvestigationCommandService.get_case_timeline(
        db=db,
        case_id=case_id,
        entity_id=entity_id,
        event_type=event_type,
        limit=limit
    )
    return timeline


@router.get(
    "/search",
    response_model=GlobalSearchResponse,
    summary="Global Multi-Entity Investigation Search"
)
def global_search(
    q: str = Query(..., min_length=1, max_length=100, description="Search query term"),
    limit: int = Query(15, ge=1, le=50, description="Max results per category"),
    db: Session = Depends(get_db)
):
    """
    Performs fast cross-table lookup across Crimes, Persons, Phone Numbers, and Review Records.
    Returns categorized search results.
    """
    return InvestigationCommandService.global_investigation_search(
        db=db,
        query=q,
        limit=limit
    )


@router.get(
    "/case/{case_id}/report",
    response_model=InvestigationReportResponse,
    summary="Generate Comprehensive Structured Investigation Report"
)
def generate_report(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Assembles an authoritative 13-section investigation report covering scope, executive summary,
    connected cases, people centrality, telecom intelligence, timeline, geographic corridor,
    evidence inventory, uncertainties, methodology, and statutory limitations.
    """
    report = InvestigationCommandService.generate_investigation_report(db=db, case_id=case_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case incident '{case_id}' not found for report generation."
        )
    return report
