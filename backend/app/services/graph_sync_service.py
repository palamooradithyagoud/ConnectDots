"""
Phase 4: Knowledge Graph Synchronization Orchestrator
Coordinates the synchronization of:
  PostgreSQL (Authoritative Source Truth)
       ↓
  Phase 2 NLP Entities & Modus Operandi (Explicit facts)
       ↓
  Phase 3 ML Clusters & Discovered Patterns (Derived artifacts)
       ↓
  Neo4j Knowledge Graph (Relationship Layer)

Mandatory rules:
1. Relationships extracted directly from the crime text receive confidence_type = 'explicit'.
2. Relationships synthesized from analytical signals receive confidence_type = 'derived'.
3. Graph sync is completely idempotent: multiple executions will not duplicate nodes or edges.
"""
import logging
from collections import defaultdict
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.models.ml_models import CrimeCluster, CrimeClusterMember, CrimePattern
from app.models.telecom import PhoneNumber, CdrRecord, CrimePhoneAssociation, PersonPhoneAssociation
from app.models.person import Person, CrimePersonAssociation
from app.services.neo4j_service import Neo4jService
from app.services.graph_ready_service import GraphReadyService
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.core.config import settings

logger = logging.getLogger("connectdots_graph_sync")


class GraphSyncService:
    """
    Synchronizes PostgreSQL, NLP extractions, and Phase 3 ML patterns into the Neo4j Graph.
    """

    @classmethod
    def sync_all(cls, db: Session) -> Dict[str, Any]:
        """
        Main synchronization pipeline:
        1. Ensure graph schema constraints
        2. Sync Crime nodes and NLP entity subgraphs (explicit)
        3. Sync Phase 3 clusters (derived)
        4. Sync Phase 3 multi-signal patterns (derived)
        5. Generate derived crime-to-crime relationships (shared entities, clusters, semantics)
        """
        logger.info("Starting Graph Synchronization...")
        Neo4jService.init_schema()

        crimes_synced = 0
        entities_synced = 0
        explicit_rels = 0
        derived_rels = 0

        # 1. Fetch all crimes and their NLP analyses
        crimes = db.query(Crime).all()
        crime_map: Dict[str, Crime] = {c.id: c for c in crimes}

        nlp_records = db.query(NlpAnalysis).all()
        nlp_map: Dict[str, NlpAnalysis] = {n.crime_id: n for n in nlp_records}

        # Track entities for crime-to-crime overlap analysis
        entity_to_crimes: Dict[str, Set[str]] = defaultdict(set)
        entity_type_map: Dict[str, str] = {}
        entity_name_map: Dict[str, str] = {}

        # 2. Sync Crime nodes and Explicit NLP entities
        for crime in crimes:
            crime_node_data = {
                "id": crime.id,
                "record_id": crime.record_id,
                "category": crime.category,
                "occurred_at": crime.occurred_at.isoformat() if crime.occurred_at else None,
                "location_name": crime.location_name,
                "description": crime.description,
                "source": crime.source,
                "latitude": crime.latitude,
                "longitude": crime.longitude,
            }
            Neo4jService.upsert_crime(crime_node_data)
            crimes_synced += 1

            crime_node_id = f"crime:{crime.id}"
            nlp = nlp_map.get(crime.id)

            if nlp:
                # Use stored graph_ready_payload if available or generate fresh
                payload = nlp.graph_ready_payload
                if not payload or not isinstance(payload, dict) or "nodes" not in payload:
                    entities_dict = {
                        "weapons": nlp.extracted_weapons or [],
                        "vehicles": nlp.extracted_vehicles or [],
                        "locations": nlp.extracted_locations or [],
                        "persons": nlp.extracted_persons or [],
                        "organizations": [],
                    }
                    mo_list = nlp.modus_operandi or []
                    payload = GraphReadyService.generate_graph_payload(
                        crime_id=crime.id,
                        record_id=crime.record_id,
                        category=crime.category,
                        occurred_at=crime.occurred_at.isoformat() if crime.occurred_at else "",
                        entities=entities_dict,
                        modus_operandi=mo_list
                    )

                # Upsert entity nodes and explicit relationships
                for node in payload.get("nodes", []):
                    n_label = node.get("label")
                    n_id = node.get("id")
                    if n_label == "Crime" or not n_id:
                        continue

                    # Canonicalize entity label
                    if n_label == "PersonOfInterest":
                        n_label = "Person"

                    Neo4jService.upsert_entity(
                        label=n_label,
                        entity_id=n_id,
                        properties=node.get("properties", {})
                    )
                    entities_synced += 1

                    # Track for cross-crime entity sharing
                    entity_to_crimes[n_id].add(crime.id)
                    entity_type_map[n_id] = n_label
                    entity_name_map[n_id] = (
                        node.get("properties", {}).get("name")
                        or node.get("properties", {}).get("pattern")
                        or node.get("properties", {}).get("description")
                        or n_id
                    )

                for rel in payload.get("relationships", []):
                    rel_type = rel.get("relation")
                    target_id = rel.get("target")
                    if rel_type and target_id:
                        # Remap TARGETED_ESTABLISHMENT to INVOLVES_ORGANIZATION if needed
                        if rel_type == "TARGETED_ESTABLISHMENT":
                            rel_type = "INVOLVES_ORGANIZATION"

                        Neo4jService.create_relationship(
                            source_id=crime_node_id,
                            rel_type=rel_type,
                            target_id=target_id,
                            properties={"source": "nlp_extraction"},
                            confidence_type="explicit"
                        )
                        explicit_rels += 1

        # 3. Sync Phase 3 Clusters (Derived)
        clusters = db.query(CrimeCluster).all()
        cluster_members = db.query(CrimeClusterMember).all()
        cluster_membership_map: Dict[str, Set[str]] = defaultdict(set)
        for m in cluster_members:
            cluster_membership_map[m.cluster_id].add(m.crime_id)

        for cluster in clusters:
            cluster_node_id = f"cluster:{cluster.id}"
            cluster_props = {
                "id": cluster.id,
                "cluster_type": cluster.cluster_type,
                "cluster_label": cluster.cluster_label,
                "crime_count": cluster.crime_count,
                "centroid_lat": cluster.centroid_lat,
                "centroid_lon": cluster.centroid_lon,
            }
            Neo4jService.upsert_entity(
                label="CrimeCluster",
                entity_id=cluster_node_id,
                properties=cluster_props
            )
            entities_synced += 1

            member_crime_ids = cluster_membership_map.get(cluster.id, set())
            for c_id in member_crime_ids:
                Neo4jService.create_relationship(
                    source_id=f"crime:{c_id}",
                    rel_type="BELONGS_TO",
                    target_id=cluster_node_id,
                    properties={
                        "source": f"phase3_{cluster.cluster_type}_clustering",
                        "cluster_type": cluster.cluster_type
                    },
                    confidence_type="derived"
                )
                derived_rels += 1

        # 4. Sync Phase 3 Patterns (Derived)
        patterns = db.query(CrimePattern).all()
        for pat in patterns:
            pat_node_id = f"pattern:{pat.id}"
            pat_props = {
                "id": pat.id,
                "pattern_type": pat.pattern_type,
                "category": pat.category,
                "description": pat.description,
                "confidence": float(pat.confidence or 1.0),
            }
            Neo4jService.upsert_entity(
                label="Pattern",
                entity_id=pat_node_id,
                properties=pat_props
            )
            entities_synced += 1

            evidence_ids = pat.evidence if isinstance(pat.evidence, list) else []
            for c_id in evidence_ids:
                if c_id in crime_map:
                    Neo4jService.create_relationship(
                        source_id=f"crime:{c_id}",
                        rel_type="SUPPORTS",
                        target_id=pat_node_id,
                        properties={
                            "source": "phase3_pattern_synthesis",
                            "pattern_type": pat.pattern_type,
                            "confidence": float(pat.confidence or 1.0)
                        },
                        confidence_type="derived"
                    )
                    derived_rels += 1

        # 5. Build Derived Crime-to-Crime Relationships
        # A. Shared Entities: Vehicles, Weapons, M.O., Locations
        derived_pairs_seen: Set[Tuple[str, str, str]] = set()

        for entity_id, c_ids in entity_to_crimes.items():
            if len(c_ids) < 2:
                continue
            e_type = entity_type_map.get(entity_id, "")
            e_name = entity_name_map.get(entity_id, entity_id)

            rel_type = None
            if e_type == "Vehicle":
                rel_type = "SHARES_VEHICLE"
            elif e_type == "Weapon":
                rel_type = "SHARES_WEAPON"
            elif e_type == "ModusOperandi":
                rel_type = "SHARES_MO"
            elif e_type == "Location":
                rel_type = "SAME_LOCATION"
            elif e_type == "Phone":
                rel_type = "SHARES_PHONE"

            if not rel_type:
                continue

            sorted_crimes = sorted(list(c_ids))
            for i in range(len(sorted_crimes)):
                for j in range(i + 1, len(sorted_crimes)):
                    c1, c2 = sorted_crimes[i], sorted_crimes[j]
                    pair_key = (c1, c2, rel_type)
                    if pair_key in derived_pairs_seen:
                        continue
                    derived_pairs_seen.add(pair_key)

                    # Bidirectional edge creation
                    edge_props = {
                        "source": f"shared_{e_type.lower()}",
                        "entity_id": entity_id,
                        "entity_name": e_name,
                        "confidence": 1.0 if rel_type != "SHARES_MO" else 0.95
                    }
                    Neo4jService.create_relationship(
                        source_id=f"crime:{c1}",
                        rel_type=rel_type,
                        target_id=f"crime:{c2}",
                        properties=edge_props,
                        confidence_type="derived"
                    )
                    Neo4jService.create_relationship(
                        source_id=f"crime:{c2}",
                        rel_type=rel_type,
                        target_id=f"crime:{c1}",
                        properties=edge_props,
                        confidence_type="derived"
                    )
                    derived_rels += 2

        # B. Same Cluster relationships
        for cluster_id, c_ids in cluster_membership_map.items():
            if len(c_ids) < 2:
                continue
            sorted_crimes = sorted(list(c_ids))
            # Limit dense pairing if cluster is very large
            max_pairs = min(len(sorted_crimes), 10)
            for i in range(max_pairs):
                for j in range(i + 1, max_pairs):
                    c1, c2 = sorted_crimes[i], sorted_crimes[j]
                    pair_key = (c1, c2, "SAME_CLUSTER")
                    if pair_key in derived_pairs_seen:
                        continue
                    derived_pairs_seen.add(pair_key)

                    edge_props = {
                        "source": "cluster_co_membership",
                        "cluster_id": cluster_id,
                        "confidence": 0.85
                    }
                    Neo4jService.create_relationship(
                        source_id=f"crime:{c1}",
                        rel_type="SAME_CLUSTER",
                        target_id=f"crime:{c2}",
                        properties=edge_props,
                        confidence_type="derived"
                    )
                    Neo4jService.create_relationship(
                        source_id=f"crime:{c2}",
                        rel_type="SAME_CLUSTER",
                        target_id=f"crime:{c1}",
                        properties=edge_props,
                        confidence_type="derived"
                    )
                    derived_rels += 2

        # C. Semantic Similarity from Qdrant (top matches above threshold)
        try:
            for crime in crimes[:25]:  # Bounded for performance
                query_vec = EmbeddingService.generate_embedding(crime.description or crime.category)
                results = QdrantService.search_similar_crimes(
                    query_vector=query_vec,
                    limit=3,
                    score_threshold=settings.GRAPH_RAG_SIMILARITY_THRESHOLD
                )
                for res in results:
                    other_id = res.get("crime_id")
                    score = float(res.get("score", 0.0))
                    if other_id and other_id != crime.id and other_id in crime_map:
                        pair_key = (min(crime.id, other_id), max(crime.id, other_id), "SEMANTICALLY_SIMILAR")
                        if pair_key in derived_pairs_seen:
                            continue
                        derived_pairs_seen.add(pair_key)

                        edge_props = {
                            "source": "qdrant_embeddings",
                            "confidence": round(score, 4),
                            "similarity_score": round(score, 4)
                        }
                        Neo4jService.create_relationship(
                            source_id=f"crime:{crime.id}",
                            rel_type="SEMANTICALLY_SIMILAR",
                            target_id=f"crime:{other_id}",
                            properties=edge_props,
                            confidence_type="derived"
                        )
                        derived_rels += 1
        except Exception as e:
            logger.warning(f"Semantic similarity graph link skipped: {e}")

        # 6. Synchronize Telecom & CDR Intelligence
        phones_synced = 0
        call_rels_synced = 0

        # A. Sync Phone nodes
        db_phones = db.query(PhoneNumber).all()
        phone_id_to_norm: Dict[str, str] = {}
        for p in db_phones:
            phone_node_id = f"phone:{p.normalized_number}"
            phone_id_to_norm[p.id] = p.normalized_number
            Neo4jService.upsert_entity(
                label="Phone",
                entity_id=phone_node_id,
                properties={
                    "id": p.id,
                    "number": p.normalized_number,
                    "country_code": p.country_code or "",
                    "national_number": p.national_number or "",
                    "number_type": p.number_type or "UNKNOWN",
                }
            )
            entities_synced += 1
            phones_synced += 1

        # B. Sync Crime-Phone associations
        crime_phone_assocs = db.query(CrimePhoneAssociation).all()
        crime_to_phones: Dict[str, Set[str]] = defaultdict(set)
        phone_to_crimes: Dict[str, Set[str]] = defaultdict(set)

        for cpa in crime_phone_assocs:
            norm_num = phone_id_to_norm.get(cpa.phone_id)
            if not norm_num:
                continue
            phone_node_id = f"phone:{norm_num}"
            crime_node_id = f"crime:{cpa.crime_id}"

            Neo4jService.create_relationship(
                source_id=crime_node_id,
                rel_type="MENTIONS_PHONE",
                target_id=phone_node_id,
                properties={
                    "relationship_type": cpa.relationship_type,
                    "confidence": float(cpa.confidence),
                    "source_text": cpa.source_text or ""
                },
                confidence_type=cpa.confidence_type or "explicit"
            )
            explicit_rels += 1
            crime_to_phones[cpa.crime_id].add(norm_num)
            phone_to_crimes[norm_num].add(cpa.crime_id)

        # C. Sync Person Entities from Relational Database
        persons = db.query(Person).all()
        persons_synced = 0
        for person in persons:
            Neo4jService.upsert_person({
                "id": person.id,
                "canonical_name": person.canonical_name,
                "aliases": person.aliases or [],
                "source_provenance": person.source_provenance,
                "confidence": person.confidence
            })
            entities_synced += 1
            persons_synced += 1

        # D. Sync Crime-Person Associations
        crime_person_assocs = db.query(CrimePersonAssociation).all()
        crime_to_persons: Dict[str, Set[str]] = defaultdict(set)
        for cpa in crime_person_assocs:
            c_node_id = f"crime:{cpa.crime_id}"
            p_node_id = cpa.person_id if cpa.person_id.startswith("person:") else f"person:{cpa.person_id}"
            Neo4jService.create_relationship(
                source_id=c_node_id,
                rel_type="MENTIONS_PERSON",
                target_id=p_node_id,
                properties={
                    "role": cpa.role,
                    "confidence": float(cpa.extraction_confidence or 0.9),
                    "relationship_type": cpa.relationship_type,
                    "evidence_excerpt": cpa.evidence_excerpt or ""
                },
                confidence_type="explicit"
            )
            explicit_rels += 1
            crime_to_persons[cpa.crime_id].add(p_node_id)

        # Derived Cross-Person Links: Co-occurrence in same crime
        for c_id, p_set in crime_to_persons.items():
            p_list = sorted(list(p_set))
            for i in range(len(p_list)):
                for j in range(i + 1, len(p_list)):
                    pair_key = (p_list[i], p_list[j], "CO_OCCURS_WITH")
                    if pair_key not in derived_pairs_seen:
                        derived_pairs_seen.add(pair_key)
                        Neo4jService.create_relationship(
                            source_id=p_list[i],
                            rel_type="CO_OCCURS_WITH",
                            target_id=p_list[j],
                            properties={"source_crime_id": c_id, "confidence": 0.85},
                            confidence_type="derived"
                        )
                        derived_rels += 1

        # E. Sync Person-Phone associations
        person_phone_assocs = db.query(PersonPhoneAssociation).all()
        phone_to_persons: Dict[str, Set[str]] = defaultdict(set)
        for ppa in person_phone_assocs:
            norm_num = phone_id_to_norm.get(ppa.phone_id)
            if not norm_num:
                continue
            phone_node_id = f"phone:{norm_num}"
            person_node_id = ppa.person_id if (ppa.person_id and ppa.person_id.startswith("person:")) else f"person:{ppa.person_name.strip().replace(' ', '_').lower()}"
            Neo4jService.upsert_entity(
                label="Person",
                entity_id=person_node_id,
                properties={"name": ppa.person_name.strip(), "canonical_name": ppa.person_name.strip(), "description": ppa.person_name.strip()}
            )
            Neo4jService.create_relationship(
                source_id=person_node_id,
                rel_type="USES_PHONE",
                target_id=phone_node_id,
                properties={
                    "role": ppa.role,
                    "confidence": float(ppa.confidence),
                    "source": ppa.source or "investigative_record"
                },
                confidence_type=ppa.confidence_type or "derived"
            )
            explicit_rels += 1
            phone_to_persons[phone_node_id].add(person_node_id)

        # Derived Cross-Person Links: Shared Phone
        for ph_node_id, p_set in phone_to_persons.items():
            p_list = sorted(list(p_set))
            for i in range(len(p_list)):
                for j in range(i + 1, len(p_list)):
                    pair_key = (p_list[i], p_list[j], "SHARES_PHONE")
                    if pair_key not in derived_pairs_seen:
                        derived_pairs_seen.add(pair_key)
                        Neo4jService.create_relationship(
                            source_id=p_list[i],
                            rel_type="SHARES_PHONE",
                            target_id=p_list[j],
                            properties={"phone_id": ph_node_id, "confidence": 0.95},
                            confidence_type="derived"
                        )
                        derived_rels += 1

        # D. Aggregate and sync CDR CALLS relationships between Phones
        cdr_records = db.query(CdrRecord).all()
        call_aggregates: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(lambda: {
            "call_count": 0,
            "total_duration": 0,
            "first_seen": None,
            "last_seen": None
        })

        for cdr in cdr_records:
            caller_norm = phone_id_to_norm.get(cdr.caller_phone_id)
            callee_norm = phone_id_to_norm.get(cdr.callee_phone_id)
            if not caller_norm or not callee_norm:
                continue

            pair = (caller_norm, callee_norm)
            agg = call_aggregates[pair]
            agg["call_count"] += 1
            agg["total_duration"] += cdr.duration_seconds
            t_iso = cdr.call_timestamp.isoformat() if cdr.call_timestamp else ""
            if not agg["first_seen"] or (t_iso and t_iso < agg["first_seen"]):
                agg["first_seen"] = t_iso
            if not agg["last_seen"] or (t_iso and t_iso > agg["last_seen"]):
                agg["last_seen"] = t_iso

        for (caller_num, callee_num), agg in call_aggregates.items():
            caller_node_id = f"phone:{caller_num}"
            callee_node_id = f"phone:{callee_num}"
            Neo4jService.create_relationship(
                source_id=caller_node_id,
                rel_type="CALLS",
                target_id=callee_node_id,
                properties={
                    "call_count": agg["call_count"],
                    "total_duration": agg["total_duration"],
                    "first_seen": agg["first_seen"],
                    "last_seen": agg["last_seen"],
                },
                confidence_type="explicit"
            )
            explicit_rels += 1
            call_rels_synced += 1

        # E. Cross-Case Telecommunication Linkages (COMMUNICATION_LINKED)
        for (caller_num, callee_num), agg in call_aggregates.items():
            crimes_caller = phone_to_crimes.get(caller_num, set())
            crimes_callee = phone_to_crimes.get(callee_num, set())

            for c_src in crimes_caller:
                for c_dst in crimes_callee:
                    if c_src != c_dst:
                        pair_key = (c_src, c_dst, "COMMUNICATION_LINKED")
                        if pair_key in derived_pairs_seen:
                            continue
                        derived_pairs_seen.add(pair_key)

                        link_props = {
                            "source": "cdr_communication",
                            "caller_phone": caller_num,
                            "callee_phone": callee_num,
                            "call_count": agg["call_count"],
                            "total_duration": agg["total_duration"],
                            "confidence": 0.88
                        }
                        Neo4jService.create_relationship(
                            source_id=f"crime:{c_src}",
                            rel_type="COMMUNICATION_LINKED",
                            target_id=f"crime:{c_dst}",
                            properties=link_props,
                            confidence_type="derived"
                        )
                        derived_rels += 1

        stats = Neo4jService.get_stats()
        logger.info(
            f"Graph synchronization complete: {crimes_synced} crimes, "
            f"{entities_synced} entities, {explicit_rels} explicit edges, "
            f"{derived_rels} derived edges, {phones_synced} phones, {call_rels_synced} call edges."
        )

        return {
            "status": "completed",
            "crimes_synced": crimes_synced,
            "entities_synced": entities_synced,
            "persons_synced": persons_synced,
            "explicit_relationships_created": explicit_rels,
            "derived_relationships_created": derived_rels,
            "phones_synced": phones_synced,
            "call_relationships_synced": call_rels_synced,
            "graph_stats": stats
        }
