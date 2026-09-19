"""
Phase 4: Neo4j Knowledge Graph Service
Manages Neo4j driver connection, constraints, and idempotent graph upserts.
Provides a resilient fallback mode when Neo4j is offline/unreachable in local test environments.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from neo4j import GraphDatabase, Driver, Session as Neo4jDriverSession
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError

from app.core.config import settings

logger = logging.getLogger("connectdots_neo4j")


class Neo4jService:
    """
    Singleton-style management of Neo4j driver and parameterized Cypher executions.
    Guarantees idempotency via MERGE operations and uniqueness constraints.
    """
    _driver: Optional[Driver] = None
    _in_memory_fallback: bool = False
    _force_fallback: bool = False
    # In-memory graph representation used when Neo4j is unavailable (e.g. during offline unit tests)
    _mock_nodes: Dict[str, Dict[str, Any]] = {}
    _mock_relationships: List[Dict[str, Any]] = []
    _store: Dict[str, Any] = {
        "nodes": _mock_nodes,
        "relationships": _mock_relationships
    }

    @classmethod
    def get_driver(cls) -> Optional[Driver]:
        """Returns active Neo4j driver or initializes one if possible."""
        if cls._force_fallback:
            cls._in_memory_fallback = True
            return None

        if cls._driver is not None:
            return cls._driver

        user = settings.NEO4J_USERNAME or settings.NEO4J_USER
        pwd = settings.NEO4J_PASSWORD
        uri = settings.NEO4J_URI

        uris_to_try = [uri]
        if "+s://" in uri and "+ssc://" not in uri:
            uris_to_try.append(uri.replace("+s://", "+ssc://"))
            if uri.startswith("neo4j+s://"):
                uris_to_try.append(uri.replace("neo4j+s://", "bolt+ssc://"))

        last_error = None
        for target_uri in uris_to_try:
            try:
                driver = GraphDatabase.driver(
                    target_uri,
                    auth=(user, pwd),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=8.0
                )
                driver.verify_connectivity()
                cls._driver = driver
                cls._in_memory_fallback = False
                logger.info(f"Connected to Neo4j successfully at {target_uri} (user: {user})")
                return cls._driver
            except Exception as e:
                last_error = e
                logger.debug(f"Attempt with {target_uri} failed: {e}")

        logger.warning(
            f"Neo4j is not reachable at {uri} ({last_error}). "
            "Operating in resilient in-memory graph fallback mode."
        )
        cls._driver = None
        cls._in_memory_fallback = True
        return None

    @classmethod
    def is_connected(cls) -> bool:
        """Checks if a live connection to Neo4j is established."""
        try:
            driver = cls.get_driver()
            if driver:
                driver.verify_connectivity()
                return True
        except Exception:
            pass
        return False

    @classmethod
    def is_fallback_mode(cls) -> bool:
        """Returns true if currently operating in in-memory fallback mode."""
        if cls._force_fallback:
            return True
        if cls._driver is None and not cls._in_memory_fallback:
            cls.get_driver()
        return cls._in_memory_fallback or (cls._driver is None)

    @classmethod
    def close(cls):
        """Closes the Neo4j driver pool."""
        if cls._driver is not None:
            try:
                cls._driver.close()
            except Exception:
                pass
            cls._driver = None

    @classmethod
    def init_schema(cls) -> bool:
        """
        Creates uniqueness constraints for all primary graph node types.
        Idempotent: uses 'IF NOT EXISTS'.
        """
        constraints = [
            "CREATE CONSTRAINT crime_id_unique IF NOT EXISTS FOR (c:Crime) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT org_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT vehicle_id_unique IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT weapon_id_unique IF NOT EXISTS FOR (w:Weapon) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT mo_id_unique IF NOT EXISTS FOR (m:ModusOperandi) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (cl:CrimeCluster) REQUIRE cl.id IS UNIQUE",
            "CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS FOR (pat:Pattern) REQUIRE pat.id IS UNIQUE",
            "CREATE CONSTRAINT phone_id_unique IF NOT EXISTS FOR (p:Phone) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT phone_number_unique IF NOT EXISTS FOR (p:Phone) REQUIRE p.number IS UNIQUE",
        ]

        driver = cls.get_driver()
        if not driver:
            logger.info("Schema initialized in resilient in-memory fallback.")
            return True

        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                for stmt in constraints:
                    session.run(stmt)
            logger.info("Neo4j uniqueness constraints verified.")
            return True
        except Exception as e:
            logger.warning(f"Could not initialize Neo4j constraints: {e}")
            return False

    @classmethod
    def upsert_crime(cls, crime_data: Dict[str, Any]) -> bool:
        """
        Idempotently creates or updates a Crime node.
        """
        node_id = f"crime:{crime_data.get('id')}"
        props = {
            "id": crime_data.get("id"),
            "record_id": crime_data.get("record_id", ""),
            "category": crime_data.get("category", "UNKNOWN"),
            "occurred_at": str(crime_data.get("occurred_at", "")),
            "location_name": crime_data.get("location_name", ""),
            "description": crime_data.get("description", "") or "",
            "source": crime_data.get("source", "UNKNOWN"),
            "latitude": float(crime_data.get("latitude", 0.0)) if crime_data.get("latitude") is not None else None,
            "longitude": float(crime_data.get("longitude", 0.0)) if crime_data.get("longitude") is not None else None,
        }

        if cls.is_fallback_mode():
            cls._mock_nodes[node_id] = {
                "id": node_id,
                "label": "Crime",
                "properties": props
            }
            return True

        driver = cls.get_driver()
        query = """
        MERGE (c:Crime {id: $id})
        SET c.record_id = $record_id,
            c.category = $category,
            c.occurred_at = $occurred_at,
            c.location_name = $location_name,
            c.description = $description,
            c.source = $source,
            c.latitude = $latitude,
            c.longitude = $longitude,
            c.updated_at = datetime()
        RETURN c.id as id
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                session.run(query, props)
            return True
        except Exception as e:
            logger.error(f"Error upserting Crime {crime_data.get('id')} to Neo4j: {e}")
            return False

    @classmethod
    def upsert_entity(cls, label: str, entity_id: str, properties: Dict[str, Any]) -> bool:
        """
        Idempotently creates or updates an entity node (Location, Vehicle, Weapon, etc.).
        """
        clean_label = label.strip()
        # Whitelist safe node labels
        allowed_labels = {"Location", "Person", "Organization", "Vehicle", "Weapon", "ModusOperandi", "CrimeCluster", "Pattern", "Phone"}
        if clean_label not in allowed_labels:
            logger.warning(f"Rejected unsafe node label: {clean_label}")
            return False

        if cls.is_fallback_mode():
            cls._mock_nodes[entity_id] = {
                "id": entity_id,
                "label": clean_label,
                "properties": properties
            }
            return True

        driver = cls.get_driver()
        query = f"""
        MERGE (e:{clean_label} {{id: $id}})
        SET e += $properties,
            e.updated_at = datetime()
        RETURN e.id as id
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                session.run(query, {"id": entity_id, "properties": properties})
            return True
        except Exception as e:
            logger.error(f"Error upserting entity {entity_id} ({clean_label}): {e}")
            return False

    @classmethod
    def upsert_person(cls, person_data: Dict[str, Any]) -> bool:
        """
        Idempotently creates or updates a Person node.
        """
        raw_id = person_data.get("id", "")
        person_id = f"person:{raw_id}" if not raw_id.startswith("person:") else raw_id
        props = {
            "id": person_id,
            "canonical_name": person_data.get("canonical_name") or person_data.get("name", "Unknown"),
            "name": person_data.get("canonical_name") or person_data.get("name", "Unknown"),
            "aliases": person_data.get("aliases", []),
            "source_provenance": person_data.get("source_provenance", "FIR_NARRATIVE"),
            "confidence": float(person_data.get("confidence", 1.0)),
        }
        return cls.upsert_entity(label="Person", entity_id=person_id, properties=props)

    @classmethod
    def create_relationship(
        cls,
        source_id: str = "",
        rel_type: str = "",
        target_id: str = "",
        properties: Optional[Dict[str, Any]] = None,
        confidence_type: str = "explicit",
        from_id: Optional[str] = None,
        to_id: Optional[str] = None
    ) -> bool:
        """
        Idempotently creates a directed relationship between two nodes.
        confidence_type: 'explicit' (direct facts from NLP) or 'derived' (analytical).
        """
        s_id = from_id if from_id is not None else source_id
        t_id = to_id if to_id is not None else target_id

        # Whitelist allowed relationship types to prevent Cypher injection
        allowed_rels = {
            "OCCURRED_AT", "INVOLVES_PERSON", "MENTIONS_PERSON", "INVOLVED_IN",
            "CO_OCCURS_WITH", "ASSOCIATED_WITH", "AFFILIATED_WITH",
            "INVOLVES_ORGANIZATION", "USED_VEHICLE", "USED_WEAPON", "EXHIBITS_MO",
            "BELONGS_TO", "SUPPORTS",
            "SEMANTICALLY_SIMILAR", "SHARES_VEHICLE", "SHARES_WEAPON",
            "SHARES_MO", "SAME_LOCATION", "SAME_CLUSTER",
            "MENTIONS_PHONE", "USES_PHONE", "CALLS", "SHARES_PHONE", "COMMUNICATION_LINKED"
        }
        if rel_type not in allowed_rels:
            logger.warning(f"Rejected unsafe relationship type: {rel_type}")
            return False

        props = properties.copy() if properties else {}
        props["confidence_type"] = confidence_type
        if "status" not in props:
            props["status"] = "EXPLICIT" if confidence_type == "explicit" else "AI_DERIVED"
        props["created_at"] = props.get("created_at", datetime.now(timezone.utc).isoformat())

        if cls.is_fallback_mode():
            # Deduplicate in fallback
            for r in cls._mock_relationships:
                r_src = r.get("source") or r.get("from_id")
                r_tgt = r.get("target") or r.get("to_id")
                r_rel = r.get("relation") or r.get("type")
                if r_src == s_id and r_rel == rel_type and r_tgt == t_id:
                    r["properties"].update(props)
                    return True
            cls._mock_relationships.append({
                "source": s_id,
                "from_id": s_id,
                "relation": rel_type,
                "type": rel_type,
                "target": t_id,
                "to_id": t_id,
                "properties": props
            })
            return True

        driver = cls.get_driver()
        src_raw = s_id.split(":", 1)[1] if ":" in s_id else s_id
        tgt_raw = t_id.split(":", 1)[1] if ":" in t_id else t_id

        query = f"""
        MATCH (a) WHERE a.id = $source_id OR a.id = $src_raw
        MATCH (b) WHERE b.id = $target_id OR b.id = $tgt_raw
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $props,
            r.updated_at = datetime()
        RETURN type(r) as rel
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                session.run(
                    query,
                    {
                        "source_id": s_id,
                        "src_raw": src_raw,
                        "target_id": t_id,
                        "tgt_raw": tgt_raw,
                        "props": props
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Error creating relationship {s_id} -[:{rel_type}]-> {t_id}: {e}")
            return False

    @classmethod
    def update_relationship_status(
        cls,
        source_id: str,
        rel_type: str,
        target_id: str,
        status: str,
        reviewer_id: Optional[str] = None,
        review_id: Optional[str] = None,
        new_rel_type: Optional[str] = None
    ) -> bool:
        """
        Updates the review validation status of a relationship in Neo4j.
        Supports both in-memory fallback and live Neo4j.
        """
        s_id = source_id.strip()
        t_id = target_id.strip()
        r_type = rel_type.strip()
        target_status = status.strip().upper()

        if cls.is_fallback_mode():
            matched = False
            for r in cls._mock_relationships:
                r_src = r.get("source") or r.get("from_id") or ""
                r_tgt = r.get("target") or r.get("to_id") or ""
                r_rel = r.get("relation") or r.get("type") or ""

                is_match = (
                    (r_src == s_id or r_src.endswith(f":{s_id}") or s_id.endswith(f":{r_src}")) and
                    (r_tgt == t_id or r_tgt.endswith(f":{t_id}") or t_id.endswith(f":{r_tgt}")) and
                    (r_rel == r_type)
                )
                # Also check reverse match if bidirectional
                if not is_match:
                    is_match = (
                        (r_src == t_id or r_src.endswith(f":{t_id}") or t_id.endswith(f":{r_src}")) and
                        (r_tgt == s_id or r_tgt.endswith(f":{s_id}") or s_id.endswith(f":{r_tgt}")) and
                        (r_rel == r_type)
                    )

                if is_match:
                    if "properties" not in r:
                        r["properties"] = {}
                    r["properties"]["status"] = target_status
                    r["properties"]["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                    if reviewer_id:
                        r["properties"]["reviewer_id"] = reviewer_id
                    if review_id:
                        r["properties"]["review_id"] = review_id
                    if new_rel_type:
                        r["relation"] = new_rel_type
                        r["type"] = new_rel_type
                        r["properties"]["original_relationship_type"] = r_type
                    matched = True

            return matched

        driver = cls.get_driver()
        if not driver:
            return False

        src_raw = s_id.split(":", 1)[1] if ":" in s_id else s_id
        tgt_raw = t_id.split(":", 1)[1] if ":" in t_id else t_id

        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                if new_rel_type:
                    # Update relationship type: delete old and merge new
                    query = f"""
                    MATCH (a)-[r:{r_type}]->(b)
                    WHERE (a.id = $source_id OR a.id = $src_raw) AND (b.id = $target_id OR b.id = $tgt_raw)
                    WITH a, b, r, properties(r) as old_props
                    DELETE r
                    MERGE (a)-[new_r:{new_rel_type}]->(b)
                    SET new_r += old_props,
                        new_r.status = $status,
                        new_r.original_type = $r_type,
                        new_r.reviewer_id = $reviewer_id,
                        new_r.review_id = $review_id,
                        new_r.reviewed_at = datetime()
                    RETURN type(new_r) as rel
                    """
                else:
                    query = f"""
                    MATCH (a)-[r:{r_type}]->(b)
                    WHERE (a.id = $source_id OR a.id = $src_raw) AND (b.id = $target_id OR b.id = $tgt_raw)
                    SET r.status = $status,
                        r.reviewer_id = $reviewer_id,
                        r.review_id = $review_id,
                        r.reviewed_at = datetime()
                    RETURN count(r) as updated
                    """

                session.run(
                    query,
                    {
                        "source_id": s_id,
                        "src_raw": src_raw,
                        "target_id": t_id,
                        "tgt_raw": tgt_raw,
                        "status": target_status,
                        "r_type": r_type,
                        "reviewer_id": reviewer_id,
                        "review_id": review_id,
                    }
                )
            return True
        except Exception as e:
            logger.error(f"Error updating relationship status {s_id} -[:{r_type}]-> {t_id}: {e}")
            return False

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        Returns graph node counts, relationship totals, and breakdown by explicit/derived.
        """
        if cls.is_fallback_mode():
            node_counts: Dict[str, int] = {}
            for n in cls._mock_nodes.values():
                lbl = n.get("label", "Unknown")
                node_counts[lbl] = node_counts.get(lbl, 0) + 1

            explicit_rels = sum(1 for r in cls._mock_relationships if r.get("properties", {}).get("confidence_type") == "explicit")
            derived_rels = sum(1 for r in cls._mock_relationships if r.get("properties", {}).get("confidence_type") == "derived")

            return {
                "status": "connected_in_memory",
                "is_fallback": True,
                "crime_nodes": node_counts.get("Crime", 0),
                "location_nodes": node_counts.get("Location", 0),
                "vehicle_nodes": node_counts.get("Vehicle", 0),
                "weapon_nodes": node_counts.get("Weapon", 0),
                "mo_nodes": node_counts.get("ModusOperandi", 0),
                "person_nodes": node_counts.get("Person", 0),
                "organization_nodes": node_counts.get("Organization", 0),
                "cluster_nodes": node_counts.get("CrimeCluster", 0),
                "pattern_nodes": node_counts.get("Pattern", 0),
                "total_nodes": len(cls._mock_nodes),
                "total_relationships": len(cls._mock_relationships),
                "explicit_relationships": explicit_rels,
                "derived_relationships": derived_rels,
                "last_sync": datetime.now(timezone.utc).isoformat()
            }

        driver = cls.get_driver()
        query = """
        CALL () {
            MATCH (c:Crime) RETURN count(c) as crimes
        }
        CALL () {
            MATCH (l:Location) RETURN count(l) as locations
        }
        CALL () {
            MATCH (v:Vehicle) RETURN count(v) as vehicles
        }
        CALL () {
            MATCH (w:Weapon) RETURN count(w) as weapons
        }
        CALL () {
            MATCH (m:ModusOperandi) RETURN count(m) as mos
        }
        CALL () {
            MATCH (p:Person) RETURN count(p) as persons
        }
        CALL () {
            MATCH (o:Organization) RETURN count(o) as orgs
        }
        CALL () {
            MATCH (cl:CrimeCluster) RETURN count(cl) as clusters
        }
        CALL () {
            MATCH (pat:Pattern) RETURN count(pat) as patterns
        }
        CALL () {
            MATCH ()-[r]->() RETURN count(r) as total_rels
        }
        CALL () {
            MATCH ()-[r]->() WHERE r.confidence_type = 'explicit' RETURN count(r) as explicit_rels
        }
        CALL () {
            MATCH ()-[r]->() WHERE r.confidence_type = 'derived' RETURN count(r) as derived_rels
        }
        RETURN crimes, locations, vehicles, weapons, mos, persons, orgs, clusters, patterns, total_rels, explicit_rels, derived_rels
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run(query).single()
                if result:
                    total_n = (
                        result["crimes"] + result["locations"] + result["vehicles"] +
                        result["weapons"] + result["mos"] + result["persons"] +
                        result["orgs"] + result["clusters"] + result["patterns"]
                    )
                    return {
                        "status": "connected_neo4j",
                        "is_fallback": False,
                        "crime_nodes": result["crimes"],
                        "location_nodes": result["locations"],
                        "vehicle_nodes": result["vehicles"],
                        "weapon_nodes": result["weapons"],
                        "mo_nodes": result["mos"],
                        "person_nodes": result["persons"],
                        "organization_nodes": result["orgs"],
                        "cluster_nodes": result["clusters"],
                        "pattern_nodes": result["patterns"],
                        "total_nodes": total_n,
                        "total_relationships": result["total_rels"],
                        "explicit_relationships": result["explicit_rels"],
                        "derived_relationships": result["derived_rels"],
                        "last_sync": datetime.now(timezone.utc).isoformat()
                    }
        except Exception as e:
            logger.error(f"Error fetching Neo4j stats: {e}")

        return {
            "status": "error",
            "is_fallback": False,
            "total_nodes": 0,
            "total_relationships": 0,
            "last_sync": None
        }

    @classmethod
    def reset_graph(cls):
        """Clears all nodes and relationships (used primarily in test suites)."""
        cls._mock_nodes.clear()
        cls._mock_relationships.clear()
        if not cls.is_fallback_mode():
            driver = cls.get_driver()
            if driver:
                try:
                    with driver.session(database=settings.NEO4J_DATABASE) as session:
                        session.run("MATCH (n) DETACH DELETE n")
                except Exception as e:
                    logger.warning(f"Error resetting Neo4j graph: {e}")
