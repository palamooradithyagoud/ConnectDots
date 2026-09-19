"""
Phase 6: Human-in-the-Loop Review & Validation Service
Coordinates the review lifecycle for AI-derived relationships:
AI-DERIVED (PENDING) -> UNDER_REVIEW -> VALIDATED / REJECTED / MODIFIED.
Guarantees optimistic concurrency, audit logging, idempotency, and transactional Neo4j graph updates.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc

from app.models.review import (
    ReviewStatus,
    RelationshipProvenance,
    InvestigationRelationshipReview,
    InvestigationReviewHistory,
)
from app.services.neo4j_service import Neo4jService

logger = logging.getLogger("connectdots_review_service")


class ConcurrencyConflictError(Exception):
    """Raised when an investigator attempts an action on a stale review record."""
    pass


class ReviewService:
    """
    Core engine managing investigator validation, rejection, modification, notes,
    and audit histories for AI-derived criminal intelligence links.
    """

    # Controlled whitelist of valid domain relationship types
    ALLOWED_RELATIONSHIP_TYPES: Set[str] = {
        "CO_OCCURS_WITH",
        "ASSOCIATED_WITH",
        "AFFILIATED_WITH",
        "SHARES_PHONE",
        "SHARES_VEHICLE",
        "SHARES_WEAPON",
        "SHARES_MO",
        "SAME_LOCATION",
        "SAME_CLUSTER",
        "COMMUNICATION_LINKED",
        "INVOLVED_IN",
        "MENTIONS_PERSON",
        "USES_PHONE",
        "CALLS",
        "SEMANTICALLY_SIMILAR",
    }

    SYMMETRIC_RELATIONSHIPS: Set[str] = {
        "SHARES_PHONE",
        "CO_OCCURS_WITH",
        "ASSOCIATED_WITH",
        "COMMUNICATION_LINKED",
        "SAME_LOCATION",
        "SAME_CLUSTER",
        "SHARES_VEHICLE",
        "SHARES_WEAPON",
        "SHARES_MO",
        "SEMANTICALLY_SIMILAR",
    }

    @classmethod
    def generate_relationship_ref(
        cls,
        source_type: str,
        source_id: str,
        relationship_type: str,
        target_type: str,
        target_id: str
    ) -> str:
        """
        Generates a deterministic stable identity for a relationship.
        For symmetric relationships, canonically orders source and target to avoid duplication.
        """
        s_type = source_type.strip()
        s_id = source_id.strip()
        t_type = target_type.strip()
        t_id = target_id.strip()
        r_type = relationship_type.strip()

        if r_type in cls.SYMMETRIC_RELATIONSHIPS:
            # Canonical pair sorting
            item1 = (s_type, s_id)
            item2 = (t_type, t_id)
            if item1 > item2:
                item1, item2 = item2, item1
            return f"{item1[0]}:{item1[1]}--{r_type}--{item2[0]}:{item2[1]}"

        return f"{s_type}:{s_id}->{r_type}->{t_type}:{t_id}"

    @classmethod
    def ingest_derived_relationship(
        cls,
        db: Session,
        source_type: str,
        source_id: str,
        relationship_type: str,
        target_type: str,
        target_id: str,
        confidence: float = 0.85,
        provenance: str = "GRAPH_DERIVED",
        discovery_method: Optional[str] = None,
        evidence_items: Optional[List[Dict[str, Any]]] = None
    ) -> InvestigationRelationshipReview:
        """
        Idempotently registers an AI-derived relationship into the investigator review queue.
        If already present, appends non-duplicate evidence items without resetting status.
        """
        rel_ref = cls.generate_relationship_ref(
            source_type=source_type,
            source_id=source_id,
            relationship_type=relationship_type,
            target_type=target_type,
            target_id=target_id
        )

        existing = db.query(InvestigationRelationshipReview).filter(
            InvestigationRelationshipReview.relationship_ref == rel_ref
        ).first()

        new_evidence = evidence_items or []

        if existing:
            # Merge evidence snapshot idempotently
            import json
            current_evidence = list(existing.evidence_snapshot or [])
            current_hashes = {
                json.dumps(e, sort_keys=True) if isinstance(e, dict) else str(e) for e in current_evidence
            }
            updated = False
            for item in new_evidence:
                h = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                if h not in current_hashes:
                    current_evidence.append(item)
                    current_hashes.add(h)
                    updated = True
            if updated:
                existing.evidence_snapshot = current_evidence
                db.flush()
            return existing

        # Create new pending review
        review = InvestigationRelationshipReview(
            relationship_ref=rel_ref,
            source_entity_type=source_type,
            source_entity_id=source_id,
            target_entity_type=target_type,
            target_entity_id=target_id,
            relationship_type=relationship_type,
            original_relationship_type=relationship_type,
            final_relationship_type=None,
            original_confidence=float(confidence),
            provenance=provenance,
            discovery_method=discovery_method or provenance.lower(),
            status=ReviewStatus.PENDING.value,
            evidence_snapshot=new_evidence,
            version=1
        )
        db.add(review)
        db.flush()

        # Record initial audit entry
        initial_history = InvestigationReviewHistory(
            review_id=review.id,
            action="CREATED",
            from_status=None,
            to_status=ReviewStatus.PENDING.value,
            reviewer_id="system:ai_pipeline",
            reviewer_display_name="AI Discovery Pipeline",
            note=f"Discovered via {discovery_method or provenance} with confidence {confidence:.2f}.",
            metadata_snapshot={"confidence": confidence, "evidence_count": len(new_evidence)}
        )
        db.add(initial_history)
        db.flush()

        logger.info(f"Ingested review item: {rel_ref} (status: PENDING)")
        return review

    @classmethod
    def validate_relationship(
        cls,
        db: Session,
        review_id: str,
        reviewer_id: str = "investigator:lead",
        reviewer_display_name: Optional[str] = "Lead Investigator",
        note: Optional[str] = None,
        expected_version: Optional[int] = None
    ) -> InvestigationRelationshipReview:
        """
        Validates an AI-derived relationship.
        Applies optimistic concurrency check, records audit entry, and updates Neo4j status.
        """
        review = db.query(InvestigationRelationshipReview).filter(
            InvestigationRelationshipReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review with id '{review_id}' not found.")

        # Optimistic concurrency check
        if expected_version is not None and review.version != expected_version:
            raise ConcurrencyConflictError(
                f"Review state conflict: Expected version {expected_version} but current is {review.version}. "
                f"Another investigator may have updated this record."
            )

        # Idempotency check: if already validated and no new note
        if review.status == ReviewStatus.VALIDATED.value and not note:
            return review

        from_status = review.status
        review.status = ReviewStatus.VALIDATED.value
        review.reviewer_id = reviewer_id
        review.reviewer_display_name = reviewer_display_name
        if note:
            review.investigator_note = note
        review.reviewed_at = datetime.now(timezone.utc)
        review.version += 1

        # Audit entry
        history_entry = InvestigationReviewHistory(
            review_id=review.id,
            action="VALIDATE",
            from_status=from_status,
            to_status=ReviewStatus.VALIDATED.value,
            reviewer_id=reviewer_id,
            reviewer_display_name=reviewer_display_name,
            note=note or "Validated by investigator.",
            metadata_snapshot={"confidence": review.original_confidence}
        )
        db.add(history_entry)
        db.flush()

        # Synchronize Graph state
        active_rel = review.final_relationship_type or review.relationship_type
        Neo4jService.update_relationship_status(
            source_id=review.source_entity_id,
            rel_type=active_rel,
            target_id=review.target_entity_id,
            status=ReviewStatus.VALIDATED.value,
            reviewer_id=reviewer_id,
            review_id=review.id
        )

        db.commit()
        db.refresh(review)
        logger.info(f"Review {review.id} validated by {reviewer_id}")
        return review

    @classmethod
    def reject_relationship(
        cls,
        db: Session,
        review_id: str,
        reviewer_id: str = "investigator:lead",
        reviewer_display_name: Optional[str] = "Lead Investigator",
        reason: str = "Insufficient evidence",
        note: Optional[str] = None,
        expected_version: Optional[int] = None
    ) -> InvestigationRelationshipReview:
        """
        Rejects an AI-derived relationship.
        Preserves the fact that AI proposed the relationship and records the rationale.
        """
        review = db.query(InvestigationRelationshipReview).filter(
            InvestigationRelationshipReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review with id '{review_id}' not found.")

        if expected_version is not None and review.version != expected_version:
            raise ConcurrencyConflictError(
                f"Review state conflict: Expected version {expected_version} but current is {review.version}."
            )

        from_status = review.status
        review.status = ReviewStatus.REJECTED.value
        review.rejection_reason = reason
        review.reviewer_id = reviewer_id
        review.reviewer_display_name = reviewer_display_name
        if note:
            review.investigator_note = note
        review.reviewed_at = datetime.now(timezone.utc)
        review.version += 1

        history_entry = InvestigationReviewHistory(
            review_id=review.id,
            action="REJECT",
            from_status=from_status,
            to_status=ReviewStatus.REJECTED.value,
            reviewer_id=reviewer_id,
            reviewer_display_name=reviewer_display_name,
            reason=reason,
            note=note or f"Rejected: {reason}",
            metadata_snapshot={"reason": reason}
        )
        db.add(history_entry)
        db.flush()

        active_rel = review.final_relationship_type or review.relationship_type
        Neo4jService.update_relationship_status(
            source_id=review.source_entity_id,
            rel_type=active_rel,
            target_id=review.target_entity_id,
            status=ReviewStatus.REJECTED.value,
            reviewer_id=reviewer_id,
            review_id=review.id
        )

        db.commit()
        db.refresh(review)
        logger.info(f"Review {review.id} rejected by {reviewer_id} (reason: {reason})")
        return review

    @classmethod
    def modify_relationship(
        cls,
        db: Session,
        review_id: str,
        new_relationship_type: str,
        reviewer_id: str = "investigator:lead",
        reviewer_display_name: Optional[str] = "Lead Investigator",
        note: Optional[str] = None,
        expected_version: Optional[int] = None
    ) -> InvestigationRelationshipReview:
        """
        Modifies the relationship type to a controlled, supported alternative and validates it.
        """
        clean_rel = new_relationship_type.strip().upper()
        if clean_rel not in cls.ALLOWED_RELATIONSHIP_TYPES:
            raise ValueError(
                f"Invalid relationship type '{clean_rel}'. Must be one of: {sorted(list(cls.ALLOWED_RELATIONSHIP_TYPES))}"
            )

        review = db.query(InvestigationRelationshipReview).filter(
            InvestigationRelationshipReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review with id '{review_id}' not found.")

        if expected_version is not None and review.version != expected_version:
            raise ConcurrencyConflictError(
                f"Review state conflict: Expected version {expected_version} but current is {review.version}."
            )

        old_rel = review.relationship_type
        from_status = review.status

        review.final_relationship_type = clean_rel
        review.relationship_type = clean_rel
        review.status = ReviewStatus.MODIFIED.value
        review.reviewer_id = reviewer_id
        review.reviewer_display_name = reviewer_display_name
        if note:
            review.investigator_note = note
        review.reviewed_at = datetime.now(timezone.utc)
        review.version += 1

        history_entry = InvestigationReviewHistory(
            review_id=review.id,
            action="MODIFY",
            from_status=from_status,
            to_status=ReviewStatus.MODIFIED.value,
            reviewer_id=reviewer_id,
            reviewer_display_name=reviewer_display_name,
            note=note or f"Modified relationship from {old_rel} to {clean_rel}.",
            metadata_snapshot={"original_type": old_rel, "modified_type": clean_rel}
        )
        db.add(history_entry)
        db.flush()

        Neo4jService.update_relationship_status(
            source_id=review.source_entity_id,
            rel_type=old_rel,
            target_id=review.target_entity_id,
            status=ReviewStatus.MODIFIED.value,
            reviewer_id=reviewer_id,
            review_id=review.id,
            new_rel_type=clean_rel
        )

        db.commit()
        db.refresh(review)
        logger.info(f"Review {review.id} modified from {old_rel} to {clean_rel} by {reviewer_id}")
        return review

    @classmethod
    def reopen_review(
        cls,
        db: Session,
        review_id: str,
        reviewer_id: str = "investigator:lead",
        reviewer_display_name: Optional[str] = "Lead Investigator",
        reason: str = "New investigative evidence surfaced"
    ) -> InvestigationRelationshipReview:
        """
        Reopens a previously reviewed relationship back to UNDER_REVIEW/PENDING, preserving audit trail.
        """
        review = db.query(InvestigationRelationshipReview).filter(
            InvestigationRelationshipReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review with id '{review_id}' not found.")

        from_status = review.status
        review.status = ReviewStatus.UNDER_REVIEW.value
        review.version += 1

        history_entry = InvestigationReviewHistory(
            review_id=review.id,
            action="REOPEN",
            from_status=from_status,
            to_status=ReviewStatus.UNDER_REVIEW.value,
            reviewer_id=reviewer_id,
            reviewer_display_name=reviewer_display_name,
            reason=reason,
            note=f"Reopened review cycle: {reason}",
            metadata_snapshot={"previous_status": from_status, "reopen_reason": reason}
        )
        db.add(history_entry)
        db.flush()

        active_rel = review.final_relationship_type or review.relationship_type
        Neo4jService.update_relationship_status(
            source_id=review.source_entity_id,
            rel_type=active_rel,
            target_id=review.target_entity_id,
            status=ReviewStatus.UNDER_REVIEW.value,
            reviewer_id=reviewer_id,
            review_id=review.id
        )

        db.commit()
        db.refresh(review)
        logger.info(f"Review {review.id} reopened by {reviewer_id}")
        return review

    @classmethod
    def add_note(
        cls,
        db: Session,
        review_id: str,
        reviewer_id: str = "investigator:lead",
        reviewer_display_name: Optional[str] = "Lead Investigator",
        note: str = ""
    ) -> InvestigationRelationshipReview:
        """
        Appends an investigator note to the review and history log.
        """
        if not note.strip():
            raise ValueError("Note content cannot be empty.")

        review = db.query(InvestigationRelationshipReview).filter(
            InvestigationRelationshipReview.id == review_id
        ).first()
        if not review:
            raise ValueError(f"Review with id '{review_id}' not found.")

        existing_notes = review.investigator_note or ""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        formatted_addition = f"[{timestamp_str} - {reviewer_display_name or reviewer_id}]: {note.strip()}"
        if existing_notes:
            review.investigator_note = f"{existing_notes}\n{formatted_addition}"
        else:
            review.investigator_note = formatted_addition

        review.version += 1

        history_entry = InvestigationReviewHistory(
            review_id=review.id,
            action="NOTE_ADDED",
            from_status=review.status,
            to_status=review.status,
            reviewer_id=reviewer_id,
            reviewer_display_name=reviewer_display_name,
            note=note.strip(),
            metadata_snapshot={}
        )
        db.add(history_entry)
        db.flush()
        db.commit()
        db.refresh(review)
        return review

    @classmethod
    def get_reviews(
        cls,
        db: Session,
        status: Optional[str] = None,
        relationship_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Returns a bounded, paginated list of reviews matching filter criteria.
        """
        query = db.query(InvestigationRelationshipReview)

        if status:
            clean_status = status.strip().upper()
            if clean_status != "ALL":
                query = query.filter(InvestigationRelationshipReview.status == clean_status)

        if relationship_type:
            clean_rel = relationship_type.strip().upper()
            if clean_rel != "ALL":
                query = query.filter(InvestigationRelationshipReview.relationship_type == clean_rel)

        if min_confidence is not None:
            query = query.filter(InvestigationRelationshipReview.original_confidence >= min_confidence)

        if max_confidence is not None:
            query = query.filter(InvestigationRelationshipReview.original_confidence <= max_confidence)

        if search:
            s_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    InvestigationRelationshipReview.source_entity_id.ilike(s_term),
                    InvestigationRelationshipReview.target_entity_id.ilike(s_term),
                    InvestigationRelationshipReview.investigator_note.ilike(s_term),
                    InvestigationRelationshipReview.relationship_ref.ilike(s_term),
                )
            )

        total_count = query.count()

        # Sorting
        sort_col = getattr(InvestigationRelationshipReview, sort_by, InvestigationRelationshipReview.created_at)
        if sort_desc:
            query = query.order_by(desc(sort_col))
        else:
            query = query.order_by(asc(sort_col))

        limit = min(max(1, page_size), 100)
        offset = max(0, (page - 1) * limit)
        items = query.offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "page": page,
            "page_size": limit,
            "total_pages": (total_count + limit - 1) // limit if limit else 1,
            "items": items
        }

    @classmethod
    def get_review_stats(cls, db: Session) -> Dict[str, int]:
        """
        Returns aggregated counts for quick dashboard badges.
        """
        all_reviews = db.query(InvestigationRelationshipReview.status).all()
        counts = {
            "total": len(all_reviews),
            "pending": 0,
            "under_review": 0,
            "validated": 0,
            "rejected": 0,
            "modified": 0
        }
        for (st,) in all_reviews:
            k = st.lower()
            if k in counts:
                counts[k] += 1
        return counts

    @classmethod
    def populate_queue_from_graph(cls, db: Session) -> Dict[str, Any]:
        """
        Seeds and populates the review queue from derived graph relationships in Neo4j
        (e.g., SHARES_PHONE, CO_OCCURS_WITH, COMMUNICATION_LINKED, SAME_CLUSTER, etc.).
        """
        rels = Neo4jService._mock_relationships if Neo4jService.is_fallback_mode() else []
        if not Neo4jService.is_fallback_mode():
            driver = Neo4jService.get_driver()
            if driver:
                query = """
                MATCH (a)-[r]->(b)
                WHERE r.confidence_type = 'derived' OR r.status = 'AI_DERIVED'
                RETURN a.id as source, type(r) as rel, b.id as target, properties(r) as props
                LIMIT 200
                """
                try:
                    with driver.session() as session:
                        records = session.run(query)
                        for rec in records:
                            rels.append({
                                "source": rec["source"],
                                "relation": rec["rel"],
                                "target": rec["target"],
                                "properties": rec["props"] or {}
                            })
                except Exception as e:
                    logger.warning(f"Could not load live Neo4j edges for queue populate: {e}")

        ingested_count = 0
        for r in rels:
            src = r.get("source") or r.get("from_id") or ""
            tgt = r.get("target") or r.get("to_id") or ""
            rel = r.get("relation") or r.get("type") or ""
            props = r.get("properties") or {}

            # Exclude explicit facts
            if props.get("confidence_type") == "explicit" and not props.get("status") == "AI_DERIVED":
                continue

            src_type = "Person" if src.startswith("person:") else ("Crime" if src.startswith("crime:") else "Entity")
            tgt_type = "Person" if tgt.startswith("person:") else ("Crime" if tgt.startswith("crime:") else "Entity")

            conf = float(props.get("confidence", 0.85))
            evidence_items = []
            if "phone_id" in props:
                evidence_items.append({"type": "Phone", "id": props["phone_id"], "note": "Shared phone number link"})
            if "source_crime_id" in props:
                evidence_items.append({"type": "Crime", "id": props["source_crime_id"], "note": "FIR incident co-occurrence"})
            if "caller_phone" in props and "callee_phone" in props:
                evidence_items.append({
                    "type": "CDR",
                    "id": f"{props['caller_phone']}->{props['callee_phone']}",
                    "note": f"{props.get('call_count', 1)} calls, {props.get('total_duration', 0)}s duration"
                })

            cls.ingest_derived_relationship(
                db=db,
                source_type=src_type,
                source_id=src,
                relationship_type=rel,
                target_type=tgt_type,
                target_id=tgt,
                confidence=conf,
                provenance="CDR_DERIVED" if "call_count" in props else ("GRAPH_DERIVED" if "phone_id" in props else "NLP_DERIVED"),
                discovery_method=props.get("source", "cross_case_graph_inference"),
                evidence_items=evidence_items
            )
            ingested_count += 1

        db.commit()
        return {
            "status": "completed",
            "ingested_or_synced": ingested_count,
            "current_stats": cls.get_review_stats(db)
        }
