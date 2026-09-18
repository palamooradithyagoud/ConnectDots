"""
Phase 4: Investigation Intelligence API Endpoints
Provides natural-language investigation queries powered by Graph RAG and LLM explanation.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.graph_rag_service import GraphRAGService
from app.schemas.investigation import (
    InvestigationQueryRequest,
    InvestigationQueryResponse,
    InvestigationExamplesResponse
)

router = APIRouter()
logger = logging.getLogger("connectdots_investigation_api")


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
