import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.services.text_preprocessor import TextPreprocessor
from app.services.entity_extraction_service import EntityExtractionService
from app.services.classification_service import ClassificationService
from app.services.modus_operandi_service import ModusOperandiService
from app.services.graph_ready_service import GraphReadyService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.core.config import settings

logger = logging.getLogger("connectdots_nlp_service")


class NlpService:
    """
    Master orchestrator for Phase 2: NLP & Crime Understanding.
    Transforms raw crime descriptions into structured intelligence,
    generates embeddings, indexes into Qdrant, and builds graph-ready structures.
    """

    @classmethod
    def process_single_crime(cls, db: Session, crime_id: str) -> NlpAnalysis:
        """
        Processes a single crime record through the full NLP pipeline.
        Idempotent: updates existing NlpAnalysis if one exists, or creates new.
        """
        crime = db.query(Crime).filter(Crime.id == crime_id).first()
        if not crime:
            raise ValueError(f"Crime with ID '{crime_id}' not found.")

        # Find or create NlpAnalysis record
        analysis = db.query(NlpAnalysis).filter(NlpAnalysis.crime_id == crime.id).first()
        if not analysis:
            analysis = NlpAnalysis(
                crime_id=crime.id,
                status="PROCESSING"
            )
            db.add(analysis)
            db.flush()
        else:
            analysis.status = "PROCESSING"
            db.flush()

        try:
            # 1. Text Preprocessing (Never alters original crime.description)
            original_description = crime.description or ""
            processed_text = TextPreprocessor.clean(original_description)

            # 2. Entity Extraction
            entities = EntityExtractionService.extract_entities(
                processed_text,
                fallback_location=crime.location_name
            )

            # 3. Canonical Crime Classification
            classification = ClassificationService.classify(
                processed_text,
                original_category=crime.category
            )

            # 4. Modus Operandi Extraction
            modus_operandi = ModusOperandiService.extract_modus_operandi(processed_text)

            # 5. Graph-Ready Payload for Phase 4
            graph_payload = GraphReadyService.generate_graph_payload(
                crime_id=crime.id,
                record_id=crime.record_id,
                category=classification["predicted_category"],
                occurred_at=crime.occurred_at.isoformat() if crime.occurred_at else "",
                entities=entities,
                modus_operandi=modus_operandi
            )

            # 6. Sentence Transformer Embedding Generation
            # Embed combining processed narrative and identified entities
            embedding_text = processed_text if processed_text else f"{crime.category} at {crime.location_name}"
            embedding = EmbeddingService.generate_embedding(embedding_text)

            # 7. Qdrant Vector Database Upsert
            qdrant_payload = {
                "record_id": crime.record_id,
                "category": classification["predicted_category"],
                "location": crime.location_name,
                "occurred_at": crime.occurred_at.isoformat() if crime.occurred_at else "",
                "source": crime.source,
            }
            point_id = QdrantService.upsert_crime_vector(
                crime_id=crime.id,
                vector=embedding,
                payload=qdrant_payload
            )

            # 8. Persist structured results
            analysis.status = "COMPLETED"
            analysis.processed_text = processed_text
            analysis.entities = entities
            analysis.extracted_weapons = entities.get("weapons", [])
            analysis.extracted_vehicles = entities.get("vehicles", [])
            analysis.extracted_locations = entities.get("locations", [])
            analysis.extracted_persons = entities.get("persons", [])
            analysis.modus_operandi = modus_operandi
            analysis.predicted_category = classification["predicted_category"]
            analysis.classification_confidence = classification["confidence"]
            analysis.needs_review = classification["needs_review"]
            analysis.embedding_model = settings.EMBEDDING_MODEL
            analysis.qdrant_point_id = point_id
            analysis.graph_ready_payload = graph_payload
            analysis.error_message = None
            analysis.processed_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(analysis)
            logger.info(f"Successfully processed NLP for crime {crime.record_id} -> {analysis.predicted_category} (conf={analysis.classification_confidence})")
            return analysis

        except Exception as e:
            logger.error(f"Error processing NLP for crime {crime.id}: {e}", exc_info=True)
            analysis.status = "FAILED"
            analysis.error_message = str(e)
            db.commit()
            db.refresh(analysis)
            raise e

    @classmethod
    def batch_process_crimes(
        cls,
        db: Session,
        limit: int = 50,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Batch processes crimes that either have no NLP analysis or are in PENDING/FAILED status.
        """
        query = db.query(Crime)
        if not force_reprocess:
            # Only select crimes without a COMPLETED NLP analysis
            query = query.outerjoin(NlpAnalysis).filter(
                (NlpAnalysis.id == None) | (NlpAnalysis.status != "COMPLETED")
            )

        crimes_to_process = query.limit(limit).all()
        processed_count = 0
        failed_count = 0
        results = []

        for crime in crimes_to_process:
            try:
                analysis = cls.process_single_crime(db, crime.id)
                processed_count += 1
                results.append({
                    "crime_id": crime.id,
                    "record_id": crime.record_id,
                    "status": "COMPLETED",
                    "predicted_category": analysis.predicted_category,
                    "confidence": analysis.classification_confidence
                })
            except Exception as e:
                failed_count += 1
                results.append({
                    "crime_id": crime.id,
                    "record_id": crime.record_id,
                    "status": "FAILED",
                    "error": str(e)
                })

        return {
            "total_requested": len(crimes_to_process),
            "processed_count": processed_count,
            "failed_count": failed_count,
            "items": results
        }

    @classmethod
    def get_stats(cls, db: Session) -> Dict[str, Any]:
        """Aggregates real-time NLP metrics for the ConnectDots dashboard."""
        total_crimes = db.query(func.count(Crime.id)).scalar() or 0
        completed = db.query(func.count(NlpAnalysis.id)).filter(NlpAnalysis.status == "COMPLETED").scalar() or 0
        pending = db.query(func.count(NlpAnalysis.id)).filter(NlpAnalysis.status == "PENDING").scalar() or 0
        failed = db.query(func.count(NlpAnalysis.id)).filter(NlpAnalysis.status == "FAILED").scalar() or 0
        needs_review = db.query(func.count(NlpAnalysis.id)).filter(NlpAnalysis.needs_review == True).scalar() or 0

        # Average confidence of completed classifications
        avg_confidence = db.query(func.avg(NlpAnalysis.classification_confidence)).filter(
            NlpAnalysis.status == "COMPLETED"
        ).scalar() or 0.0

        # Category distribution of predicted classifications
        category_rows = db.query(
            NlpAnalysis.predicted_category,
            func.count(NlpAnalysis.id)
        ).filter(
            NlpAnalysis.status == "COMPLETED"
        ).group_by(NlpAnalysis.predicted_category).all()

        predicted_distribution = {cat: count for cat, count in category_rows if cat}

        # Vector count in Qdrant
        vector_count = QdrantService.count_indexed_vectors()

        return {
            "total_crimes": total_crimes,
            "nlp_processed": completed,
            "nlp_pending": pending + (total_crimes - completed - failed),
            "nlp_failed": failed,
            "needs_review_count": needs_review,
            "average_confidence": round(float(avg_confidence), 4),
            "qdrant_indexed_vectors": vector_count,
            "predicted_category_distribution": predicted_distribution,
            "embedding_model": settings.EMBEDDING_MODEL
        }
