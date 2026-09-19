"""
Phase 8: Unified Investigation Command Center Service
Aggregates and synchronizes Case Context, Unified Chronological Timeline,
Global Categorized Search, and Structured Investigation Dossiers across
PostgreSQL, Neo4j, Telecom, Centrality, and Human Review engines.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.crime import Crime
from app.models.person import Person, CrimePersonAssociation
from app.models.telecom import PhoneNumber, CrimePhoneAssociation, CdrRecord
from app.models.nlp_analysis import NlpAnalysis
from app.models.review import InvestigationRelationshipReview, InvestigationReviewHistory, ReviewStatus
from app.models.ml_models import CrimeCluster, CrimePattern, CrimeAnomaly
from app.services.key_individual_service import KeyIndividualService
from app.services.telecom_analytics_service import TelecomAnalyticsService
from app.schemas.investigation import (
    CaseContextResponse,
    ExtractedEntitySummary,
    ConnectedCaseSummary,
    KeyIndividualSummary,
    TimelineEvent,
    CaseTimelineResponse,
    SearchItem,
    GlobalSearchResponse,
    InvestigationReportResponse
)

logger = logging.getLogger("connectdots_command_center")


class InvestigationCommandService:
    """
    Central orchestration service powering the Phase 8 Unified Command Center.
    """

    @classmethod
    def get_case_context(cls, db: Session, case_id: str) -> Optional[CaseContextResponse]:
        """
        Retrieves complete, bounded case dossier and surrounding entity topology.
        """
        crime = db.query(Crime).filter(
            or_(Crime.id == case_id, Crime.record_id == case_id)
        ).first()
        if not crime:
            return None

        # 1. Extracted People
        person_assocs = db.query(CrimePersonAssociation).filter(
            CrimePersonAssociation.crime_id == crime.id
        ).all()
        extracted_people: List[ExtractedEntitySummary] = []
        for pa in person_assocs:
            person = db.query(Person).filter(Person.id == pa.person_id).first()
            p_name = person.canonical_name if person else (pa.person_id or "Unknown Person")
            extracted_people.append(ExtractedEntitySummary(
                id=pa.person_id or pa.id,
                type="Person",
                label=p_name,
                role=pa.role or "ASSOCIATED",
                confidence=pa.confidence if pa.confidence is not None else 1.0,
                validation_status="VALIDATED" if getattr(pa, "relationship_type", None) == "INVOLVED_IN" else "AI_DERIVED"
            ))

        # 2. Extracted Phones
        phone_assocs = db.query(CrimePhoneAssociation).filter(
            CrimePhoneAssociation.crime_id == crime.id
        ).all()
        extracted_phones: List[ExtractedEntitySummary] = []
        for ph_a in phone_assocs:
            phone = db.query(PhoneNumber).filter(PhoneNumber.id == ph_a.phone_id).first()
            ph_num = phone.normalized_number if phone else ph_a.phone_id
            extracted_phones.append(ExtractedEntitySummary(
                id=ph_a.phone_id or ph_a.id,
                type="Phone",
                label=ph_num,
                role=ph_a.relationship_type or "PHONE_CONTACT",
                confidence=ph_a.confidence if ph_a.confidence is not None else 1.0,
                validation_status="VALIDATED" if ph_a.confidence_type == "explicit" else "AI_DERIVED"
            ))

        # 3. Extracted Vehicles and Weapons from NLP Analysis
        extracted_vehicles: List[ExtractedEntitySummary] = []
        extracted_weapons: List[ExtractedEntitySummary] = []
        nlp = db.query(NlpAnalysis).filter(NlpAnalysis.crime_id == crime.id).first()
        if nlp and isinstance(nlp.entities, dict):
            for v in nlp.entities.get("vehicles", []):
                v_label = v.get("text") or v.get("name") or "Suspect Vehicle"
                extracted_vehicles.append(ExtractedEntitySummary(
                    id=f"veh-{len(extracted_vehicles)+1}",
                    type="Vehicle",
                    label=v_label,
                    role="GETAWAY_VEHICLE",
                    confidence=v.get("confidence", 0.9),
                    validation_status="AI_DERIVED"
                ))
            for w in nlp.entities.get("weapons", []):
                w_label = w.get("text") or w.get("name") or "Weapon"
                extracted_weapons.append(ExtractedEntitySummary(
                    id=f"wpn-{len(extracted_weapons)+1}",
                    type="Weapon",
                    label=w_label,
                    role="WEAPON_USED",
                    confidence=w.get("confidence", 0.9),
                    validation_status="AI_DERIVED"
                ))

        # 4. Connected Cases via Telecom and Graph
        all_conns = TelecomAnalyticsService.get_cross_case_connections(db, limit=20)
        connected_cases: List[ConnectedCaseSummary] = []
        seen_case_ids = set()

        for conn in all_conns:
            c1 = conn.get("crime_1", {})
            c2 = conn.get("crime_2", {})
            other = None
            if c1.get("id") == crime.id or c1.get("record_id") == crime.record_id:
                other = c2
            elif c2.get("id") == crime.id or c2.get("record_id") == crime.record_id:
                other = c1

            if other and other.get("id") and other.get("id") not in seen_case_ids:
                seen_case_ids.add(other.get("id"))
                connected_cases.append(ConnectedCaseSummary(
                    crime_id=other.get("id"),
                    record_id=other.get("record_id", "Unknown"),
                    category=other.get("category", "General Crime"),
                    location_name=other.get("location_name", "Unknown Location"),
                    connection_type=conn.get("connection_type", "SHARED_PHONE"),
                    confidence=conn.get("confidence", 0.9),
                    evidence=conn.get("evidence", "Shared telecommunications contact")
                ))

        # 5. Key Individuals around Crime
        key_ind_res = KeyIndividualService.get_key_individuals(
            db=db, scope_type="crime", scope_id=crime.id, limit=5
        )
        key_individuals: List[KeyIndividualSummary] = []
        for ki in key_ind_res.get("items", []):
            metrics = ki.get("metrics", {})
            key_individuals.append(KeyIndividualSummary(
                person_id=ki.get("person_id", ""),
                name=ki.get("display_name") or ki.get("canonical_name") or "Individual",
                degree_centrality=metrics.get("degree_centrality", 0.0),
                betweenness_centrality=metrics.get("betweenness_centrality", 0.0),
                pagerank=metrics.get("pagerank", 0.0),
                structural_explanation=ki.get("structural_explanation")
            ))

        # 6. Validation Review Summary
        reviews = db.query(InvestigationRelationshipReview).filter(
            or_(
                InvestigationRelationshipReview.source_entity_id == crime.id,
                InvestigationRelationshipReview.target_entity_id == crime.id,
                InvestigationRelationshipReview.source_entity_id == crime.record_id,
                InvestigationRelationshipReview.target_entity_id == crime.record_id
            )
        ).all()

        val_counts = {"validated": 0, "under_review": 0, "rejected": 0, "modified": 0}
        for r in reviews:
            st = (r.status or "").upper()
            if st == "VALIDATED":
                val_counts["validated"] += 1
            elif st in ("UNDER_REVIEW", "PENDING"):
                val_counts["under_review"] += 1
            elif st == "REJECTED":
                val_counts["rejected"] += 1
            elif st == "MODIFIED":
                val_counts["modified"] += 1

        total_evidence = (
            1 + len(person_assocs) + len(phone_assocs) +
            len(extracted_vehicles) + len(extracted_weapons) + len(reviews)
        )

        return CaseContextResponse(
            case_id=crime.id,
            record_id=crime.record_id,
            category=crime.category or "General",
            crime_type=crime.crime_type or crime.category or "Unknown",
            description=crime.description or "",
            location_name=crime.location_name or "Unknown Location",
            latitude=crime.latitude,
            longitude=crime.longitude,
            occurred_at=crime.occurred_at.isoformat() if crime.occurred_at else None,
            source=crime.source or "FIR_REPORT",
            extracted_people=extracted_people,
            extracted_phones=extracted_phones,
            extracted_vehicles=extracted_vehicles,
            extracted_weapons=extracted_weapons,
            connected_cases=connected_cases[:10],
            key_individuals=key_individuals,
            validation_summary=val_counts,
            total_evidence_count=total_evidence
        )

    @classmethod
    def get_case_timeline(
        cls,
        db: Session,
        case_id: str,
        entity_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> CaseTimelineResponse:
        """
        Builds a unified, chronologically ordered investigation timeline.
        Aggregates FIR occurrences, CDR communications, relationship discoveries,
        and investigator validation decisions.
        """
        crime = db.query(Crime).filter(
            or_(Crime.id == case_id, Crime.record_id == case_id)
        ).first()
        if not crime:
            return CaseTimelineResponse(case_id=case_id, events=[], total_events=0)

        events: List[TimelineEvent] = []

        # 1. Primary Crime Incident
        if crime.occurred_at:
            events.append(TimelineEvent(
                id=f"evt-crime-{crime.id[:8]}",
                timestamp=crime.occurred_at.isoformat(),
                event_type="CRIME_INCIDENT",
                source="POSTGRESQL",
                title=f"Incident Occurred: Case {crime.record_id}",
                description=f"{crime.category or 'Crime'} reported at {crime.location_name or 'scene'}. {crime.description[:120] if crime.description else ''}",
                entity_id=crime.id,
                entity_name=f"Case {crime.record_id}",
                entity_type="Crime",
                validation_status="VALIDATED",
                citation=f"FIR-{crime.record_id}",
                metadata={"category": crime.category, "location": crime.location_name}
            ))

        # 2. Associated Phone CDR Events
        phone_assocs = db.query(CrimePhoneAssociation).filter(
            CrimePhoneAssociation.crime_id == crime.id
        ).all()
        phone_ids = [pa.phone_id for pa in phone_assocs]

        if phone_ids:
            cdrs = db.query(CdrRecord).filter(
                or_(
                    CdrRecord.caller_phone_id.in_(phone_ids),
                    CdrRecord.callee_phone_id.in_(phone_ids)
                )
            ).order_by(CdrRecord.call_timestamp.desc()).limit(30).all()

            for cdr in cdrs:
                if not cdr.call_timestamp:
                    continue
                caller = db.query(PhoneNumber).filter(PhoneNumber.id == cdr.caller_phone_id).first()
                callee = db.query(PhoneNumber).filter(PhoneNumber.id == cdr.callee_phone_id).first()
                caller_num = caller.normalized_number if caller else cdr.caller_phone_id
                callee_num = callee.normalized_number if callee else cdr.callee_phone_id

                events.append(TimelineEvent(
                    id=f"evt-cdr-{cdr.id[:8]}",
                    timestamp=cdr.call_timestamp.isoformat(),
                    event_type="CDR_COMMUNICATION",
                    source="CDR",
                    title=f"Telecommunication Call: {caller_num} → {callee_num}",
                    description=f"Call duration: {cdr.duration_seconds or 0}s. Telecommunication activity recorded in surveillance window.",
                    entity_id=cdr.caller_phone_id,
                    entity_name=caller_num,
                    entity_type="Phone",
                    validation_status="VALIDATED",
                    citation=f"CDR-{cdr.id[:8]}",
                    metadata={"duration_sec": cdr.duration_seconds, "callee": callee_num}
                ))

        # 3. Investigator Validation History
        reviews = db.query(InvestigationRelationshipReview).filter(
            or_(
                InvestigationRelationshipReview.source_entity_id == crime.id,
                InvestigationRelationshipReview.target_entity_id == crime.id,
                InvestigationRelationshipReview.source_entity_id == crime.record_id,
                InvestigationRelationshipReview.target_entity_id == crime.record_id
            )
        ).all()

        review_ids = [r.id for r in reviews]
        if review_ids:
            histories = db.query(InvestigationReviewHistory).filter(
                InvestigationReviewHistory.review_id.in_(review_ids)
            ).order_by(InvestigationReviewHistory.created_at.desc()).limit(20).all()

            for h in histories:
                if not h.created_at:
                    continue
                events.append(TimelineEvent(
                    id=f"evt-rev-{h.id[:8]}",
                    timestamp=h.created_at.isoformat(),
                    event_type="INVESTIGATOR_DECISION",
                    source="REVIEW_QUEUE",
                    title=f"Investigator Validation Action: {h.action}",
                    description=f"Relationship reviewed to status '{h.to_status}' by {h.reviewer_display_name or 'Investigator'}. Note: {h.note or 'No notes provided'}",
                    entity_id=h.review_id,
                    entity_name=h.action,
                    entity_type="Review",
                    validation_status=h.to_status,
                    citation=f"Audit-{h.id[:8]}",
                    metadata={"action": h.action, "to_status": h.to_status}
                ))

        # 4. Connected Cases Occurrences
        connected_crimes = db.query(Crime).filter(
            Crime.id.in_(
                db.query(CrimePhoneAssociation.crime_id).filter(
                    CrimePhoneAssociation.phone_id.in_(phone_ids),
                    CrimePhoneAssociation.crime_id != crime.id
                )
            )
        ).limit(10).all()

        for cc in connected_crimes:
            if cc.occurred_at:
                events.append(TimelineEvent(
                    id=f"evt-conn-{cc.id[:8]}",
                    timestamp=cc.occurred_at.isoformat(),
                    event_type="CRIME_INCIDENT",
                    source="POSTGRESQL",
                    title=f"Correlated Case Occurrence: Case {cc.record_id}",
                    description=f"Connected case ({cc.category or 'Crime'}) occurred at {cc.location_name or 'Scene'}.",
                    entity_id=cc.id,
                    entity_name=f"Case {cc.record_id}",
                    entity_type="Crime",
                    validation_status="AI_DERIVED",
                    citation=f"FIR-{cc.record_id}",
                    metadata={"category": cc.category}
                ))

        # Entity filtering
        if entity_id:
            events = [
                e for e in events
                if e.entity_id == entity_id or (e.metadata and entity_id in str(e.metadata))
            ]

        # Event type filtering
        if event_type:
            events = [e for e in events if e.event_type.upper() == event_type.upper()]

        # Sort chronologically (earliest to latest)
        events.sort(key=lambda x: x.timestamp)

        return CaseTimelineResponse(
            case_id=crime.id,
            events=events[:limit],
            total_events=len(events)
        )

    @classmethod
    def global_investigation_search(
        cls,
        db: Session,
        query: str,
        limit: int = 15
    ) -> GlobalSearchResponse:
        """
        Fast cross-entity search returning categorized hits across Crimes, People, Phones, and Reviews.
        """
        q_term = query.strip()
        if not q_term:
            return GlobalSearchResponse(query=query, total_results=0)

        wildcard = f"%{q_term}%"

        # 1. Crimes
        crimes = db.query(Crime).filter(
            or_(
                Crime.record_id.ilike(wildcard),
                Crime.description.ilike(wildcard),
                Crime.category.ilike(wildcard),
                Crime.location_name.ilike(wildcard)
            )
        ).limit(limit).all()

        crime_items = [
            SearchItem(
                id=c.id,
                entity_type="CRIME",
                title=f"Case {c.record_id}",
                subtitle=f"{c.category or 'Incident'} • {c.location_name or 'Unknown'}",
                category=c.category,
                detail=c.description[:100] if c.description else None,
                metadata={"record_id": c.record_id, "occurred_at": c.occurred_at.isoformat() if c.occurred_at else None}
            )
            for c in crimes
        ]

        # 2. People
        people = db.query(Person).filter(
            or_(
                Person.canonical_name.ilike(wildcard),
                Person.normalized_name.ilike(wildcard)
            )
        ).limit(limit).all()

        person_items = [
            SearchItem(
                id=p.id,
                entity_type="PERSON",
                title=p.canonical_name,
                subtitle=f"Aliases: {', '.join(p.aliases) if p.aliases else 'None'}",
                category="Person",
                detail=f"Known aliases: {p.aliases}",
                metadata={"aliases": p.aliases}
            )
            for p in people
        ]

        # 3. Phones
        phones = db.query(PhoneNumber).filter(
            or_(
                PhoneNumber.normalized_number.ilike(wildcard),
                PhoneNumber.national_number.ilike(wildcard)
            )
        ).limit(limit).all()

        phone_items = [
            SearchItem(
                id=ph.id,
                entity_type="PHONE",
                title=ph.normalized_number,
                subtitle=f"Carrier: {ph.carrier or 'Unknown'} • {ph.circle or 'National'}",
                category="Phone",
                detail=f"Line Type: {ph.line_type or 'Mobile'}",
                metadata={"carrier": ph.carrier}
            )
            for ph in phones
        ]

        # 4. Reviews
        reviews = db.query(InvestigationRelationshipReview).filter(
            or_(
                InvestigationRelationshipReview.relationship_ref.ilike(wildcard),
                InvestigationRelationshipReview.id.ilike(wildcard)
            )
        ).limit(limit).all()

        review_items = [
            SearchItem(
                id=r.id,
                entity_type="REVIEW",
                title=f"Review: {r.relationship_type}",
                subtitle=f"Status: {r.status} • Ref: {r.relationship_ref[:30]}…",
                category=r.status,
                detail=r.investigator_note,
                metadata={"status": r.status}
            )
            for r in reviews
        ]

        total = len(crime_items) + len(person_items) + len(phone_items) + len(review_items)

        return GlobalSearchResponse(
            query=q_term,
            crimes=crime_items,
            people=person_items,
            phones=phone_items,
            reviews=review_items,
            total_results=total
        )

    @classmethod
    def generate_investigation_report(
        cls,
        db: Session,
        case_id: str
    ) -> Optional[InvestigationReportResponse]:
        """
        Compiles an authoritative 13-section investigation report strictly adhering to
        Section 21 of Phase 8 requirements and the Zero-Guilt Inference Principle.
        """
        crime = db.query(Crime).filter(
            or_(Crime.id == case_id, Crime.record_id == case_id)
        ).first()
        if not crime:
            return None

        ctx = cls.get_case_context(db, crime.id)
        timeline = cls.get_case_timeline(db, crime.id, limit=30)

        # 1. Investigation Scope
        scope = {
            "case_id": crime.id,
            "record_id": crime.record_id,
            "category": crime.category or "General Crime",
            "jurisdiction": crime.location_name or "National Capital Region",
            "date_reported": crime.occurred_at.strftime("%Y-%m-%d %H:%M") if crime.occurred_at else "N/A",
            "reporting_source": crime.source or "FIRST_INFORMATION_REPORT",
            "investigator_unit": "Special Investigation Command Unit / SIH-26189"
        }

        # 2. Executive Summary (evidence grounded)
        summary = (
            f"Investigation report for Case {crime.record_id} ({crime.category or 'Crime'}), "
            f"reported at {crime.location_name or 'the scene'} on "
            f"{crime.occurred_at.strftime('%Y-%m-%d') if crime.occurred_at else 'the recorded date'}. "
            f"Analysis of cross-database records identified {len(ctx.connected_cases)} correlated incidents, "
            f"{len(ctx.extracted_people)} associated individuals, and {len(ctx.extracted_phones)} verified telecommunications lines. "
            f"All findings distinguish between human-validated evidence and AI-derived investigative hypotheses."
        )

        # 3. People Findings (Neutral structural connectivity only)
        people_findings = []
        for ki in ctx.key_individuals:
            people_findings.append({
                "person_id": ki.person_id,
                "name": ki.name,
                "centrality_metrics": {
                    "degree": ki.degree_centrality,
                    "betweenness": ki.betweenness_centrality,
                    "pagerank": ki.pagerank
                },
                "structural_role": ki.structural_explanation or "Node exhibits elevated topological connectivity within observed network.",
                "neutrality_disclaimer": "Centrality quantifies structural network position only; it does not constitute an inference of culpability or guilt."
            })

        # 4. Telecom Findings
        telecom_findings = []
        for ph in ctx.extracted_phones:
            telecom_findings.append({
                "phone_id": ph.id,
                "normalized_number": ph.label,
                "relationship": ph.role,
                "validation_status": ph.validation_status,
                "citation": f"PHONE-{ph.label}"
            })

        # 5. Network Findings
        network_findings = [
            {
                "topology": "Bipartite Person-Crime-Phone Multigraph",
                "connected_incidents_count": len(ctx.connected_cases),
                "isolated_clusters": 1,
                "highest_betweenness_bridge": ctx.key_individuals[0].name if ctx.key_individuals else "None identified"
            }
        ]

        # 6. Geographic Findings
        geographic_findings = []
        if crime.latitude and crime.longitude:
            geographic_findings.append({
                "incident_coordinates": [crime.latitude, crime.longitude],
                "location_name": crime.location_name or "Scene",
                "spatial_corridor": f"Corridor surrounding {crime.location_name} within 5.0km radius"
            })

        # 7. Evidence Inventory
        evidence_inventory = [
            {
                "citation": f"FIR-{crime.record_id}",
                "evidence_type": "PRIMARY_POLICE_REPORT",
                "source": "State Police FIR Repository",
                "summary": f"Incident narrative for Case {crime.record_id} at {crime.location_name}.",
                "validation_status": "VALIDATED"
            }
        ]
        for cc in ctx.connected_cases:
            evidence_inventory.append({
                "citation": f"LINK-{crime.record_id[:4]}-{cc.record_id[:4]}",
                "evidence_type": "CROSS_CASE_LINK",
                "source": "Telecom CDR Analytics",
                "summary": cc.evidence,
                "validation_status": "AI_DERIVED"
            })

        # 8. Uncertainties & Data Gaps
        uncertainties = [
            "Subscriber identities for non-standard SIM registrations remain subject to carrier verification.",
            "Temporal gaps between CDR logging windows and physical FIR filing times require corroborating field evidence.",
            "AI-derived linkages require human investigator review prior to formal judicial presentation."
        ]

        # 9. Methodology & Tool Provenance
        methodology = [
            "Spatial proximity calculations executed via PostGIS geography types.",
            "Semantic similarity computed via Sentence Transformers (384-dimensional embeddings) and Qdrant vector index.",
            "Graph centrality evaluated via Neo4j Graph Data Science (GDS) algorithms and NetworkX.",
            "Telecommunications correlation derived from E.164 normalized CDR exchange records.",
            "AI investigation planning orchestrated by Domain AI Agent with strict 16 read-only tool boundaries."
        ]

        # 10. Statutory Limitations
        statutory_limitations = [
            "Section 65B Bharatiya Sakshya Adhiniyam (BSA) 2023: Electronic records and machine-generated outputs require an accompanying Certificate signed by the authorized system officer for admissibility in judicial proceedings.",
            "Section 43A Information Technology Act 2000: Personal identifiable information (PII) and telecommunication records must be stored and processed strictly within designated law enforcement access controls.",
            "Human-in-the-Loop Validation Mandate: Centrality metrics (Degree, Betweenness, PageRank) strictly quantify structural connectivity within observed data and must not be construed as culpability assessments, criminal hierarchy ratings, or legal culpability."
        ]

        return InvestigationReportResponse(
            case_id=crime.id,
            record_id=crime.record_id,
            title=f"Comprehensive Criminal Network Investigation Report — Case {crime.record_id}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            scope=scope,
            executive_summary=summary,
            connected_cases=ctx.connected_cases,
            people_findings=people_findings,
            telecom_findings=telecom_findings,
            network_findings=network_findings,
            timeline=timeline.events,
            geographic_findings=geographic_findings,
            evidence_inventory=evidence_inventory,
            validation_breakdown=ctx.validation_summary,
            uncertainties=uncertainties,
            methodology=methodology,
            statutory_limitations=statutory_limitations
        )
