import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.schemas.nlp import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult
)
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger("connectdots_search_api")
router = APIRouter()


@router.post("/similar", response_model=SemanticSearchResponse, summary="Semantic Crime Similarity Search")
def search_similar_crimes(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Executes semantic similarity search:
    1. Generates dense vector embedding for user's natural language query.
    2. Queries Qdrant vector database using Cosine similarity and optional category filter.
    3. Resolves full structured crime records and NLP intelligence from PostgreSQL.
    """
    try:
        # 1. Generate query embedding
        query_vector = EmbeddingService.generate_embedding(request.query)

        # 2. Query Qdrant for top matching vectors
        qdrant_matches = QdrantService.search_similar_crimes(
            query_vector=query_vector,
            limit=request.limit * 2,  # Fetch slightly more to allow post-filtering by location if requested
            score_threshold=request.similarity_threshold,
            category=request.category
        )

        if not qdrant_matches:
            return SemanticSearchResponse(
                query=request.query,
                total_results=0,
                similarity_threshold=request.similarity_threshold,
                results=[]
            )

        # 3. Collect crime IDs from Qdrant payloads
        crime_ids = [m["payload"].get("crime_id") for m in qdrant_matches if m["payload"].get("crime_id")]
        score_map = {m["payload"].get("crime_id"): m["score"] for m in qdrant_matches if m["payload"].get("crime_id")}

        # 4. Fetch full records from PostgreSQL (Source of Truth)
        crimes = db.query(Crime).filter(Crime.id.in_(crime_ids)).all()
        analyses = db.query(NlpAnalysis).filter(NlpAnalysis.crime_id.in_(crime_ids)).all()
        analysis_map = {a.crime_id: a for a in analyses}

        results: List[SemanticSearchResult] = []
        for crime in crimes:
            score = score_map.get(crime.id, 0.0)

            # Optional location filter
            if request.location:
                if request.location.lower() not in crime.location_name.lower():
                    continue

            analysis = analysis_map.get(crime.id)

            results.append(
                SemanticSearchResult(
                    crime_id=crime.id,
                    record_id=crime.record_id,
                    category=crime.category,
                    predicted_category=analysis.predicted_category if analysis else None,
                    similarity_score=round(score, 4),
                    location=crime.location_name,
                    occurred_at=crime.occurred_at.isoformat() if crime.occurred_at else None,
                    description=crime.description,
                    entities=analysis.entities if analysis else None,
                    weapons=analysis.extracted_weapons if analysis else [],
                    vehicles=analysis.extracted_vehicles if analysis else [],
                    modus_operandi=analysis.modus_operandi if analysis else [],
                )
            )

        # Sort descending by similarity score
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        results = results[:request.limit]

        return SemanticSearchResponse(
            query=request.query,
            total_results=len(results),
            similarity_threshold=request.similarity_threshold,
            results=results
        )

    except Exception as e:
        logger.error(f"Semantic similarity search encountered error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search query failed: {str(e)}"
        )
