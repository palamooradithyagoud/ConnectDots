import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.schemas.nlp import (
    NlpAnalysisResponse,
    NlpBatchProcessRequest,
    NlpBatchProcessResponse,
    NlpStatsResponse
)
from app.services.nlp_service import NlpService

logger = logging.getLogger("connectdots_nlp_api")
router = APIRouter()


@router.post("/process/{crime_id}", response_model=NlpAnalysisResponse, summary="Process NLP on single crime record")
def process_single_crime(
    crime_id: str,
    db: Session = Depends(get_db)
):
    """
    Executes text cleaning, entity extraction, canonical classification,
    M.O. detection, graph payload generation, embedding generation, and Qdrant upsert.
    """
    try:
        analysis = NlpService.process_single_crime(db, crime_id)
        return analysis
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to process NLP for crime {crime_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NLP processing pipeline encountered error: {str(e)}"
        )


@router.post("/process", response_model=NlpBatchProcessResponse, summary="Batch process crimes through NLP pipeline")
def batch_process_crimes(
    request: NlpBatchProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Processes unanalyzed or pending crime records through the NLP pipeline.
    """
    try:
        result = NlpService.batch_process_crimes(
            db=db,
            limit=request.limit,
            force_reprocess=request.force_reprocess
        )
        return result
    except Exception as e:
        logger.error(f"Batch NLP processing encountered error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch NLP processing failed: {str(e)}"
        )


@router.get("/stats", response_model=NlpStatsResponse, summary="Get NLP and Vector Database statistics")
def get_nlp_stats(
    db: Session = Depends(get_db)
):
    """
    Returns aggregated metrics: total crimes, NLP completed, pending, failed,
    classification confidence, vector count in Qdrant, and predicted category breakdown.
    """
    try:
        stats = NlpService.get_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error fetching NLP stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch NLP stats: {str(e)}"
        )


@router.get("/{crime_id}", response_model=NlpAnalysisResponse, summary="Get NLP analysis for a crime")
def get_nlp_analysis(
    crime_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves stored NLP intelligence, extracted entities, M.O., and graph-ready payload for a crime.
    """
    analysis = db.query(NlpAnalysis).filter(NlpAnalysis.crime_id == crime_id).first()
    if not analysis:
        # Check if crime exists
        crime = db.query(Crime).filter(Crime.id == crime_id).first()
        if not crime:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crime incident not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NLP analysis not yet generated for this crime record. Run /api/v1/nlp/process/{crime_id} to analyze."
        )
    return analysis


@router.post("/retry-failed", summary="Retry all failed NLP records")
def retry_failed_records(
    db: Session = Depends(get_db)
):
    """
    Retries NLP processing for all records previously marked as FAILED.
    """
    failed_crimes = db.query(Crime.id).join(NlpAnalysis).filter(NlpAnalysis.status == "FAILED").all()
    retried = 0
    errors = 0

    for (c_id,) in failed_crimes:
        try:
            NlpService.process_single_crime(db, c_id)
            retried += 1
        except Exception:
            errors += 1

    return {
        "total_failed": len(failed_crimes),
        "successfully_retried": retried,
        "still_failing": errors
    }
