"""
Phase 4: Graph RAG (Retrieval-Augmented Generation) Service
Implements Hybrid Evidence Retrieval (PostgreSQL + Qdrant + Neo4j), Evidence Fusion,
Hallucination Safeguards, Strict Grounding, and Structured Citation Generation.
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.models.ml_models import CrimePattern, CrimeCluster
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.graph_query_service import GraphQueryService
from app.services.neo4j_service import Neo4jService
from app.services.llm.factory import get_llm_provider
from app.core.config import settings

logger = logging.getLogger("connectdots_graph_rag")

SYSTEM_GROUNDING_PROMPT = """You are an evidence-grounded crime analysis assistant for the ConnectDots system.

CRITICAL OPERATIONAL RULES:
1. Use ONLY the evidence supplied in the structured context JSON.
2. Do NOT invent crimes, people, vehicles, weapons, locations, relationships, dates, motives, or identities.
3. If the retrieved evidence is insufficient to address the question, clearly state: "Insufficient evidence available in the current records."
4. Clearly distinguish:
   a) Directly stated / explicit facts (from source incident reports)
   b) NLP-extracted entities (locations, weapons, vehicles, M.O.)
   c) ML-derived patterns and clusters (statistical groupings)
   d) Graph-derived relationships (shared entity overlaps)
   e) Analytical uncertainty
5. Never treat statistical similarity, shared modus operandi, or geographic proximity as proof of common perpetrator identity, intent, coordination, or legal causation.
6. Always cite the exact crime IDs (e.g. CR-2026-014) that support each statement.
7. Format your response into four distinct markdown sections:
   ### Summary
   ### Connections
   ### Evidence
   ### Uncertainty
"""


class GraphRAGService:
    """
    Coordinates multi-database evidence retrieval, fusion, and grounded LLM synthesis.
    """

    @classmethod
    async def query(cls, db: Session, question: str) -> Dict[str, Any]:
        """
        Main Graph RAG pipeline:
        1. Parse question for entity hints or crime IDs
        2. Hybrid retrieval (Postgres + Qdrant + Neo4j)
        3. Evidence fusion into structured EvidenceObject
        4. Guardrails / Safeguards check
        5. Grounded synthesis via LLMProvider
        6. Citation & graph path extraction
        """
        clean_question = question.strip()
        if not clean_question:
            return cls._empty_response("No question was provided for investigation.")

        # 1. Question Understanding / Target Crime Resolution
        target_crime = cls._extract_or_match_target_crime(db, clean_question)

        # 2. Hybrid Retrieval
        # A. Semantic Search via Qdrant
        similar_crimes_data = []
        try:
            query_vector = EmbeddingService.generate_embedding(clean_question)
            semantic_matches = QdrantService.search_similar_crimes(
                query_vector=query_vector,
                limit=settings.GRAPH_RAG_TOP_K_SEMANTIC,
                score_threshold=settings.GRAPH_RAG_SIMILARITY_THRESHOLD
            )
            for sm in semantic_matches:
                cid = sm.get("crime_id")
                score = sm.get("score", 0.0)
                # Verify existence in Postgres
                p_crime = db.query(Crime).filter(Crime.id == cid).first()
                if p_crime:
                    similar_crimes_data.append({
                        "crime_id": p_crime.id,
                        "record_id": p_crime.record_id,
                        "category": p_crime.category,
                        "location_name": p_crime.location_name,
                        "occurred_at": p_crime.occurred_at.isoformat() if p_crime.occurred_at else None,
                        "similarity": round(float(score), 4)
                    })
        except Exception as e:
            logger.warning(f"Qdrant semantic retrieval error in Graph RAG: {e}")

        # If target crime was not directly named in prompt, use top semantic match if high confidence
        if not target_crime and similar_crimes_data:
            top_candidate_id = similar_crimes_data[0]["crime_id"]
            target_crime = db.query(Crime).filter(Crime.id == top_candidate_id).first()

        # B. Graph Traversal via Neo4j
        graph_connections = []
        graph_subgraph = {"nodes": [], "edges": []}

        if target_crime:
            try:
                # Get 2-hop neighborhood
                graph_subgraph = GraphQueryService.get_crime_neighborhood(
                    crime_id=target_crime.id,
                    depth=settings.GRAPH_TRAVERSAL_MAX_DEPTH,
                    max_nodes=40
                )
                # Get direct and derived crime connections
                graph_connections = GraphQueryService.find_connected_crimes(target_crime.id)
            except Exception as e:
                logger.warning(f"Graph traversal error: {e}")

        # C. Pattern Evidence from Phase 3 ML
        supporting_patterns = []
        if target_crime:
            # Query patterns that include target_crime.id or any similar crime ID in their evidence list
            all_incident_ids = {target_crime.id} | {s["crime_id"] for s in similar_crimes_data}
            patterns = db.query(CrimePattern).all()
            for p in patterns:
                ev_list = p.evidence if isinstance(p.evidence, list) else []
                overlap = set(ev_list).intersection(all_incident_ids)
                if overlap:
                    supporting_patterns.append({
                        "id": p.id,
                        "pattern_type": p.pattern_type,
                        "category": p.category,
                        "description": p.description,
                        "confidence": p.confidence,
                        "matching_crimes": list(overlap)
                    })

        # 3. Safeguard: Check if any evidence exists
        if not target_crime and not similar_crimes_data and not graph_connections:
            return cls._empty_response(
                "Insufficient evidence available in the current database records. "
                "No incident matches or statistical clusters were found for this query."
            )

        # 4. Evidence Fusion into Structured Object
        evidence_object = {
            "query": clean_question,
            "primary_crime": {
                "id": target_crime.id if target_crime else None,
                "record_id": target_crime.record_id if target_crime else None,
                "category": target_crime.category if target_crime else None,
                "location_name": target_crime.location_name if target_crime else None,
                "occurred_at": target_crime.occurred_at.isoformat() if target_crime and target_crime.occurred_at else None,
                "description": target_crime.description if target_crime else None,
            } if target_crime else None,
            "similar_crimes": similar_crimes_data,
            "graph_connections": graph_connections,
            "supporting_patterns": supporting_patterns,
        }

        # 5. Build Grounded Prompt
        user_prompt = f"""Investigator Query:
"{clean_question}"

The following evidence has been retrieved from authoritative databases (PostgreSQL, Qdrant semantic vectors, and Neo4j Knowledge Graph).
Synthesize an evidence-grounded response adhering strictly to the operational rules.

Retrieved Structured Evidence:
```json
{json.dumps(evidence_object, indent=2)}
```
"""

        # 6. Call LLM Provider
        provider = get_llm_provider()
        try:
            raw_answer = await provider.generate(prompt=user_prompt, system_prompt=SYSTEM_GROUNDING_PROMPT)
        except Exception as e:
            logger.error(f"LLM Generation error: {e}")
            raw_answer = (
                "### Summary\n"
                "An error occurred while generating the synthesis, but underlying database evidence was successfully retrieved.\n\n"
                "### Connections\n"
                f"• Retrieved {len(graph_connections)} graph relationship(s) and {len(similar_crimes_data)} semantic match(es).\n\n"
                "### Evidence\n"
                + "\n".join([f"• {c['crime_id']}" for c in similar_crimes_data[:5]]) + "\n\n"
                "### Uncertainty\n"
                "Automated LLM synthesis unavailable."
            )

        # 7. Extract Citations & Structured Sections
        parsed_sections = cls._parse_markdown_sections(raw_answer)
        citations = cls._extract_citations(raw_answer, evidence_object)

        # Collect related crimes list
        related_crimes = []
        seen_rc = set()
        if target_crime:
            seen_rc.add(target_crime.id)

        for sc in similar_crimes_data:
            cid = sc["crime_id"]
            if cid not in seen_rc:
                seen_rc.add(cid)
                related_crimes.append({
                    "crime_id": cid,
                    "record_id": sc.get("record_id"),
                    "category": sc.get("category"),
                    "connection_type": "semantic_similarity",
                    "similarity": sc.get("similarity")
                })

        for gc in graph_connections:
            cid = gc.get("crime_id")
            if cid and cid not in seen_rc:
                seen_rc.add(cid)
                related_crimes.append({
                    "crime_id": cid,
                    "record_id": gc.get("record_id"),
                    "category": gc.get("category"),
                    "connection_type": gc.get("relationship"),
                    "confidence_type": gc.get("confidence_type"),
                    "confidence": gc.get("confidence")
                })

        # Calculate overall confidence score
        conf_scores = [sc.get("similarity", 0.7) for sc in similar_crimes_data] + [gc.get("confidence", 0.8) for gc in graph_connections]
        avg_confidence = round(sum(conf_scores) / len(conf_scores), 2) if conf_scores else 0.85

        return {
            "answer": raw_answer,
            "structured_sections": parsed_sections,
            "citations": citations,
            "evidence": evidence_object,
            "graph_paths": graph_subgraph.get("edges", []),
            "graph_nodes": graph_subgraph.get("nodes", []),
            "related_crimes": related_crimes,
            "confidence": avg_confidence,
            "meta": {
                "llm_provider": settings.LLM_PROVIDER,
                "model": settings.LLM_MODEL,
                "target_crime_id": target_crime.id if target_crime else None,
                "similar_count": len(similar_crimes_data),
                "graph_connection_count": len(graph_connections),
                "pattern_count": len(supporting_patterns),
            }
        }

    @classmethod
    def _extract_or_match_target_crime(cls, db: Session, query_text: str) -> Optional[Crime]:
        """
        Inspects text for explicit record IDs (e.g. CR-2026-014, CRM-102, UUID) or searches Postgres.
        """
        # 1. Match typical ID patterns (e.g. CR-2026-014, CR-001, etc.)
        id_pattern = r"(CR-[\w-]+|CRM-[\w-]+|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
        match = re.search(id_pattern, query_text, re.IGNORECASE)
        if match:
            candidate_id = match.group(1).strip()
            crime = db.query(Crime).filter(
                (Crime.record_id.ilike(candidate_id)) | (Crime.id == candidate_id)
            ).first()
            if crime:
                return crime

        # 2. If words indicate a specific category + location, query Postgres
        categories = ["ROBBERY", "BURGLARY", "THEFT", "ASSAULT", "HOMICIDE", "FRAUD", "VEHICLE_THEFT", "NARCOTICS"]
        found_category = None
        for cat in categories:
            if cat.lower() in query_text.lower():
                found_category = cat
                break

        if found_category:
            return db.query(Crime).filter(Crime.category == found_category).first()

        return None

    @classmethod
    def _parse_markdown_sections(cls, text: str) -> Dict[str, str]:
        """Splits answer text into Summary, Connections, Evidence, and Uncertainty."""
        sections = {"summary": "", "connections": "", "evidence": "", "uncertainty": ""}
        current_section = "summary"
        lines = text.split("\n")

        for line in lines:
            lower = line.strip().lower()
            if lower.startswith("### summary") or lower.startswith("## summary"):
                current_section = "summary"
                continue
            elif lower.startswith("### connection") or lower.startswith("## connection"):
                current_section = "connections"
                continue
            elif lower.startswith("### evidence") or lower.startswith("## evidence"):
                current_section = "evidence"
                continue
            elif lower.startswith("### uncertainty") or lower.startswith("## uncertainty"):
                current_section = "uncertainty"
                continue

            sections[current_section] += line + "\n"

        for k in sections:
            sections[k] = sections[k].strip()

        return sections

    @classmethod
    def _extract_citations(cls, answer: str, evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Maps claims/statements to underlying verified crime IDs found in the evidence object.
        """
        all_ids = set()
        primary = evidence.get("primary_crime") or {}
        if primary.get("id"):
            all_ids.add(primary["id"])
        if primary.get("record_id"):
            all_ids.add(primary["record_id"])

        for sc in evidence.get("similar_crimes", []):
            if sc.get("crime_id"):
                all_ids.add(sc["crime_id"])
            if sc.get("record_id"):
                all_ids.add(sc["record_id"])

        for gc in evidence.get("graph_connections", []):
            if gc.get("crime_id"):
                all_ids.add(gc["crime_id"])

        citations: List[Dict[str, Any]] = []
        for line in answer.split("\n"):
            clean_l = line.strip().lstrip("•-* ")
            if not clean_l or clean_l.startswith("#"):
                continue

            referenced = [cid for cid in all_ids if cid.lower() in clean_l.lower()]
            if referenced:
                citations.append({
                    "claim": clean_l[:140] + ("..." if len(clean_l) > 140 else ""),
                    "evidence": referenced
                })

        return citations

    @classmethod
    def _empty_response(cls, message: str) -> Dict[str, Any]:
        """Returns standard response structure when insufficient evidence is found."""
        return {
            "answer": f"### Summary\n{message}\n\n### Connections\n• None identified in database.\n\n### Evidence\nNone cited.\n\n### Uncertainty\nAvailable crime data is insufficient to establish connections.",
            "structured_sections": {
                "summary": message,
                "connections": "None identified in database.",
                "evidence": "None cited.",
                "uncertainty": "Available crime data is insufficient to establish connections."
            },
            "citations": [],
            "evidence": {},
            "graph_paths": [],
            "graph_nodes": [],
            "related_crimes": [],
            "confidence": 0.0,
            "meta": {
                "llm_provider": settings.LLM_PROVIDER,
                "model": settings.LLM_MODEL,
                "error": "INSUFFICIENT_EVIDENCE"
            }
        }
