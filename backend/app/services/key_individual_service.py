"""
Phase 5: Key Individual Intelligence & Evidence Synthesis Service
Orchestrates structural key-individual identification, evidence retrieval,
telecom analytics fusion, and neutral structural explanations.
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.person import Person, CrimePersonAssociation, NetworkCentralityResult
from app.models.crime import Crime
from app.models.telecom import PhoneNumber, CdrRecord, PersonPhoneAssociation
from app.services.centrality_service import CentralityService
from app.services.telecom_analytics_service import TelecomAnalyticsService
from app.services.neo4j_service import Neo4jService
from app.core.config import settings

logger = logging.getLogger("connectdots_key_individual")


class KeyIndividualService:
    """
    Synthesizes structural network metrics with grounded multi-source evidence
    to explain key individual positions without legal guilt inference.
    """

    @classmethod
    def get_key_individuals(
        cls,
        db: Session,
        scope_type: str = "all",
        scope_id: Optional[str] = None,
        sort_by: str = "degree_centrality",
        limit: int = 20,
        offset: int = 0,
        scope_crime_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Computes or retrieves ranked key individuals with contextual network breakdown.
        """
        if scope_crime_id and not scope_id:
            scope_id = scope_crime_id
            scope_type = "crime"

        # 1. Run Centrality Engine on scoped graph
        analysis_res = CentralityService.compute_network_metrics(
            scope_type=scope_type,
            scope_id=scope_id
        )

        nodes = analysis_res.get("nodes", [])

        # 2. Sort by requested metric
        valid_sort_keys = {
            "degree_centrality": lambda x: x["metrics"]["degree_centrality"],
            "betweenness_centrality": lambda x: x["metrics"]["betweenness_centrality"],
            "pagerank": lambda x: x["metrics"]["pagerank"],
            "raw_degree": lambda x: x["metrics"]["raw_degree"]
        }
        sort_func = valid_sort_keys.get(sort_by, valid_sort_keys["degree_centrality"])
        nodes.sort(key=sort_func, reverse=True)

        total_count = len(nodes)
        paginated_nodes = nodes[offset: offset + limit]

        # 3. Enrich each individual with database evidence & explanation
        enriched_individuals = []
        for item in paginated_nodes:
            p_id = item["person_id"]
            explanation = cls._generate_structural_explanation(item)
            item["structural_explanation"] = explanation

            # Check DB person
            db_person = db.query(Person).filter(Person.id == p_id).first()
            if db_person:
                item["aliases"] = db_person.aliases or []
                item["source_provenance"] = db_person.source_provenance

            # Optional: Persist snapshot of centrality metrics
            cls._persist_centrality_snapshot(db, item, scope_type, scope_id)

            enriched_individuals.append(item)

        db.commit()

        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "sort_by": sort_by,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "items": enriched_individuals,
            "graph_summary": analysis_res.get("graph_summary", {})
        }

    @classmethod
    def get_person_detail(cls, db: Session, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns full intelligence dossier for a single individual.
        Includes metrics, connected crimes, phone associations, and CDR stats.
        """
        # Ensure person exists
        person = db.query(Person).filter(Person.id == person_id).first()
        raw_id = person_id.replace("person:", "")
        if not person:
            person = db.query(Person).filter(Person.normalized_name == raw_id.replace("_", " ")).first()

        mock_nodes = Neo4jService._mock_nodes
        exists_in_graph = (person_id in mock_nodes) or (f"person:{raw_id}" in mock_nodes) or (raw_id in mock_nodes)
        if not exists_in_graph and not Neo4jService.is_fallback_mode():
            driver = Neo4jService.get_driver()
            if driver:
                try:
                    with driver.session(database=settings.NEO4J_DATABASE) as session:
                        rec = session.run("MATCH (p:Person) WHERE p.id = $pid OR p.id = $raw_id RETURN p.id LIMIT 1", {"pid": person_id, "raw_id": f"person:{raw_id}"}).single()
                        if rec:
                            exists_in_graph = True
                except Exception:
                    pass

        if not person and not exists_in_graph:
            return None

        # Compute person-scoped centrality
        centrality_res = CentralityService.compute_network_metrics(
            scope_type="person",
            scope_id=person_id,
            max_hops=2
        )
        target_metrics = None
        for n in centrality_res.get("nodes", []):
            if n["person_id"] == person_id or (person and n["person_id"] == person.id):
                target_metrics = n
                break

        if not target_metrics:
            target_metrics = {
                "person_id": person_id,
                "display_name": person.canonical_name if person else raw_id.title(),
                "degree_centrality": 0.0,
                "betweenness_centrality": 0.0,
                "pagerank": 0.0,
                "raw_degree": 0,
                "metrics": {"degree_centrality": 0.0, "betweenness_centrality": 0.0, "pagerank": 0.0, "raw_degree": 0},
                "network_breakdown": {"connected_crimes": 0, "connected_people": 0, "connected_phones": 0, "connected_vehicles": 0, "connected_organizations": 0, "connected_locations": 0}
            }

        # Retrieve associated crimes from PostgreSQL
        actual_pid = person.id if person else person_id
        crime_assocs = db.query(CrimePersonAssociation).filter(CrimePersonAssociation.person_id == actual_pid).all()
        crimes_data = []
        for ca in crime_assocs:
            c = db.query(Crime).filter(Crime.id == ca.crime_id).first()
            if c:
                crimes_data.append({
                    "crime_id": c.id,
                    "record_id": c.record_id,
                    "category": c.category,
                    "occurred_at": c.occurred_at.isoformat() if c.occurred_at else None,
                    "role": ca.role,
                    "relationship_type": ca.relationship_type,
                    "evidence_excerpt": ca.evidence_excerpt
                })

        # Retrieve associated phones
        phone_assocs = db.query(PersonPhoneAssociation).filter(
            (PersonPhoneAssociation.person_id == actual_pid) |
            (PersonPhoneAssociation.person_name == (person.canonical_name if person else raw_id.title()))
        ).all()

        phones_data = []
        telecom_summary = {
            "total_phones": len(phone_assocs),
            "total_calls": 0,
            "total_airtime_seconds": 0,
            "top_contacts": []
        }

        for pa in phone_assocs:
            ph = db.query(PhoneNumber).filter(PhoneNumber.id == pa.phone_id).first()
            if ph:
                # Get phone metrics
                p_metrics = TelecomAnalyticsService.get_phone_profile(db, ph.id) or {}
                phones_data.append({
                    "phone_id": ph.id,
                    "normalized_number": ph.normalized_number,
                    "carrier": ph.carrier,
                    "role": pa.role,
                    "confidence": pa.confidence,
                    "metrics": p_metrics.get("call_summary")
                })
                call_sum = p_metrics.get("call_summary", {})
                telecom_summary["total_calls"] += call_sum.get("total_calls", 0)
                telecom_summary["total_airtime_seconds"] += call_sum.get("total_duration_seconds", 0)
                for contact in p_metrics.get("top_contacts", [])[:3]:
                    telecom_summary["top_contacts"].append(contact)

        explanation = cls._generate_structural_explanation(target_metrics)

        tm_metrics = target_metrics.get("metrics") or {}
        return {
            "person_id": actual_pid,
            "canonical_name": person.canonical_name if person else target_metrics.get("canonical_name", raw_id.title()),
            "aliases": person.aliases if person else [],
            "source_provenance": person.source_provenance if person else "GRAPH_EXTRACT",
            "confidence": person.confidence if person else 1.0,
            "degree_centrality": target_metrics.get("degree_centrality", tm_metrics.get("degree_centrality", 0.0)),
            "betweenness_centrality": target_metrics.get("betweenness_centrality", tm_metrics.get("betweenness_centrality", 0.0)),
            "pagerank": target_metrics.get("pagerank", tm_metrics.get("pagerank", 0.0)),
            "raw_degree": target_metrics.get("raw_degree", tm_metrics.get("raw_degree", 0)),
            "metrics": tm_metrics,
            "network_breakdown": target_metrics.get("network_breakdown"),
            "structural_explanation": explanation,
            "crimes": crimes_data,
            "associated_crimes": crimes_data,
            "phones": phones_data,
            "associated_phones": phones_data,
            "telecom_summary": telecom_summary,
            "subgraph": {
                "nodes": centrality_res.get("subgraph_nodes", []),
                "edges": centrality_res.get("subgraph_edges", [])
            }
        }

    @classmethod
    def get_person_evidence(cls, db: Session, person_id: str) -> List[Dict[str, Any]]:
        """
        Returns granular evidence items grounding this individual's presence in the system.
        """
        evidence_items = []
        person = db.query(Person).filter(Person.id == person_id).first()
        actual_pid = person.id if person else person_id

        # 1. Crime mentions
        crime_assocs = db.query(CrimePersonAssociation).filter(CrimePersonAssociation.person_id == actual_pid).all()
        for ca in crime_assocs:
            c = db.query(Crime).filter(Crime.id == ca.crime_id).first()
            evidence_items.append({
                "evidence_type": "CRIME_MENTION",
                "reference_id": c.record_id if c else ca.crime_id,
                "role": ca.role,
                "relationship": ca.relationship_type,
                "confidence": ca.extraction_confidence,
                "excerpt": ca.evidence_excerpt,
                "provenance": "FIR_NARRATIVE"
            })

        # 2. Phone associations
        phone_assocs = db.query(PersonPhoneAssociation).filter(
            (PersonPhoneAssociation.person_id == actual_pid) |
            (PersonPhoneAssociation.person_name == (person.canonical_name if person else ""))
        ).all()
        for pa in phone_assocs:
            ph = db.query(PhoneNumber).filter(PhoneNumber.id == pa.phone_id).first()
            if ph:
                evidence_items.append({
                    "evidence_type": "PHONE_LINKAGE",
                    "reference_id": ph.normalized_number,
                    "role": pa.role,
                    "relationship": "USES_PHONE",
                    "confidence": pa.confidence,
                    "excerpt": f"Associated with telephone {ph.normalized_number} ({ph.carrier})",
                    "provenance": pa.source or "TELECOM_REGISTRY"
                })

        return evidence_items

    @classmethod
    def _generate_structural_explanation(cls, item: Dict[str, Any]) -> str:
        """
        Generates an objective, non-accusatory explanation of why this node has high structural centrality.
        """
        m = item.get("metrics", {})
        nb = item.get("network_breakdown", {})
        deg = m.get("degree_centrality", 0.0)
        btw = m.get("betweenness_centrality", 0.0)
        pr = m.get("pagerank", 0.0)
        name = item.get("canonical_name") or item.get("display_name", "Individual")

        parts = []
        if btw >= 0.25:
            parts.append(
                f"{name} acts as a structural bridge (betweenness: {btw}) connecting otherwise distinct groups or cases."
            )
        if deg >= 0.2:
            parts.append(
                f"Exhibits elevated direct connectivity (degree: {deg}) with links to {nb.get('connected_crimes', 0)} incidents and {nb.get('connected_people', 0)} individuals."
            )
        if pr >= 0.15:
            parts.append(
                f"Has a prominent PageRank score ({pr}), indicating direct linkages to other structurally connected nodes in the graph."
            )

        if not parts:
            parts.append(
                f"{name} has observed links to {nb.get('connected_crimes', 0)} incident(s) and {nb.get('connected_phones', 0)} phone number(s) within the scoped network."
            )

        parts.append(
            "Note: Network centrality describes structural connectivity in the available data and does not establish legal guilt or criminal responsibility."
        )
        return " ".join(parts)

    @classmethod
    def _persist_centrality_snapshot(
        cls,
        db: Session,
        item: Dict[str, Any],
        scope_type: str,
        scope_id: Optional[str]
    ):
        """
        Idempotently persists or updates a centrality record for auditability.
        """
        p_id = item["person_id"]
        m = item["metrics"]
        nb = item.get("network_breakdown", {})

        existing = db.query(NetworkCentralityResult).filter(
            NetworkCentralityResult.person_id == p_id,
            NetworkCentralityResult.scope_type == scope_type,
            NetworkCentralityResult.scope_id == scope_id
        ).first()

        if existing:
            existing.degree_centrality = m["degree_centrality"]
            existing.betweenness_centrality = m["betweenness_centrality"]
            existing.pagerank = m["pagerank"]
            existing.raw_degree = m.get("raw_degree", 0)
            existing.connected_crimes = nb.get("connected_crimes", 0)
            existing.connected_people = nb.get("connected_people", 0)
            existing.connected_phones = nb.get("connected_phones", 0)
            existing.connected_vehicles = nb.get("connected_vehicles", 0)
            existing.connected_organizations = nb.get("connected_organizations", 0)
            existing.calculated_at = datetime.now(timezone.utc)
        else:
            rec = NetworkCentralityResult(
                person_id=p_id,
                scope_type=scope_type,
                scope_id=scope_id,
                degree_centrality=m["degree_centrality"],
                betweenness_centrality=m["betweenness_centrality"],
                pagerank=m["pagerank"],
                raw_degree=m.get("raw_degree", 0),
                connected_crimes=nb.get("connected_crimes", 0),
                connected_people=nb.get("connected_people", 0),
                connected_phones=nb.get("connected_phones", 0),
                connected_vehicles=nb.get("connected_vehicles", 0),
                connected_organizations=nb.get("connected_organizations", 0),
                calculated_at=datetime.now(timezone.utc)
            )
            db.add(rec)
