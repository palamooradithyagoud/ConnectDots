"""
Phase 4: Graph Query Service
Provides safe, parameterized Cypher queries and graph traversals.
Guarantees bounded depth, limited node returns, and zero arbitrary user Cypher execution.
Supports both live Neo4j driver and the resilient in-memory graph fallback.
"""
import logging
from typing import Dict, Any, List, Optional, Set
from app.services.neo4j_service import Neo4jService
from app.core.config import settings

logger = logging.getLogger("connectdots_graph_query")


class GraphQueryService:
    """
    Executes bounded graph queries for investigation workflows.
    """

    @staticmethod
    def _clean_properties(raw_props: Any) -> Any:
        """Sanitizes properties by converting neo4j DateTime, Date, and non-primitive types to strings."""
        if not isinstance(raw_props, dict):
            return raw_props
        cleaned = {}
        for k, v in raw_props.items():
            if v is None:
                cleaned[k] = None
            elif hasattr(v, "iso_format"):
                cleaned[k] = v.iso_format()
            elif hasattr(v, "isoformat"):
                cleaned[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                cleaned[k] = v
            elif hasattr(v, "__str__") and not isinstance(v, (str, int, float, bool)):
                cleaned[k] = str(v)
            else:
                cleaned[k] = v
        return cleaned

    @classmethod
    def get_crime_neighborhood(
        cls,
        crime_id: str,
        depth: int = 2,
        max_nodes: int = 50,
        include_rejected: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves the connected neighborhood for a given crime ID up to specified depth.
        By default, suppresses REJECTED relationships unless include_rejected is True.
        Returns:
            {"nodes": [...], "edges": [...], "center_node_id": "crime:..."}
        """
        clean_crime_id = crime_id.strip()
        crime_node_id = f"crime:{clean_crime_id}" if not clean_crime_id.startswith("crime:") else clean_crime_id
        depth = min(max(1, depth), settings.GRAPH_TRAVERSAL_MAX_DEPTH)

        if Neo4jService.is_fallback_mode():
            # Traverse in-memory mock store
            visited_nodes: Dict[str, Dict[str, Any]] = {}
            visited_edges: List[Dict[str, Any]] = []
            queue = [(crime_node_id, 0)]
            seen = {crime_node_id}

            if crime_node_id in Neo4jService._mock_nodes:
                visited_nodes[crime_node_id] = Neo4jService._mock_nodes[crime_node_id]

            while queue and len(visited_nodes) < max_nodes:
                curr_id, d = queue.pop(0)
                if d >= depth:
                    continue

                for rel in Neo4jService._mock_relationships:
                    # Filter rejected edges unless in audit mode
                    rel_status = rel.get("properties", {}).get("status")
                    if rel_status == "REJECTED" and not include_rejected:
                        continue

                    src = rel["source"]
                    tgt = rel["target"]
                    if src == curr_id or tgt == curr_id:
                        other = tgt if src == curr_id else src
                        visited_edges.append(rel)

                        if other not in seen and len(visited_nodes) < max_nodes:
                            seen.add(other)
                            if other in Neo4jService._mock_nodes:
                                visited_nodes[other] = Neo4jService._mock_nodes[other]
                            queue.append((other, d + 1))

            return {
                "center_node_id": crime_node_id,
                "nodes": list(visited_nodes.values()),
                "edges": visited_edges,
                "total_nodes": len(visited_nodes),
                "total_edges": len(visited_edges)
            }

        driver = Neo4jService.get_driver()
        raw_id = clean_crime_id.replace("crime:", "")
        prefixed_id = f"crime:{raw_id}"

        rejection_filter = "" if include_rejected else "WHERE ALL(x IN relationships(path) WHERE coalesce(x.status, '') <> 'REJECTED')"
        match_start_query = """
        MATCH (start:Crime)
        WHERE (start.id = $raw_id OR start.id = $prefixed_id OR start.record_id = $raw_id OR start.record_id = $prefixed_id)
        RETURN start
        LIMIT 1
        """
        paths_query = f"""
        MATCH (start:Crime)
        WHERE (start.id = $raw_id OR start.id = $prefixed_id OR start.record_id = $raw_id OR start.record_id = $prefixed_id)
        MATCH path = (start)-[r*1..{depth}]-(neighbor)
        {rejection_filter}
        RETURN path
        LIMIT {max_nodes}
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                params = {"raw_id": raw_id, "prefixed_id": prefixed_id}
                start_rec = session.run(match_start_query, params).single()
                if start_rec and start_rec["start"]:
                    start_node = start_rec["start"]
                    center_id = start_node.get("id") or prefixed_id
                    nodes_map = {
                        center_id: {
                            "id": center_id,
                            "label": list(start_node.labels)[0] if start_node.labels else "Crime",
                            "properties": cls._clean_properties(dict(start_node))
                        }
                    }
                    edges_list = []
                    seen_edges = set()

                    paths_result = session.run(paths_query, params)
                    for record in paths_result:
                        path = record["path"]
                        for n in path.nodes:
                            nid = n.get("id") or str(n.id)
                            if nid not in nodes_map:
                                nodes_map[nid] = {
                                    "id": nid,
                                    "label": list(n.labels)[0] if n.labels else "Entity",
                                    "properties": cls._clean_properties(dict(n))
                                }
                        for rel in path.relationships:
                            src_id = rel.start_node.get("id") or str(rel.start_node.id)
                            tgt_id = rel.end_node.get("id") or str(rel.end_node.id)
                            edge_key = (src_id, tgt_id, rel.type)
                            if edge_key not in seen_edges:
                                seen_edges.add(edge_key)
                                edges_list.append({
                                    "source": src_id,
                                    "target": tgt_id,
                                    "relation": rel.type,
                                    "properties": cls._clean_properties(dict(rel))
                                })

                    return {
                        "center_node_id": center_id,
                        "nodes": list(nodes_map.values()),
                        "edges": edges_list,
                        "total_nodes": len(nodes_map),
                        "total_edges": len(edges_list)
                    }
        except Exception as e:
            logger.error(f"Error executing get_crime_neighborhood in Neo4j: {e}", exc_info=True)

        return {
            "center_node_id": crime_node_id,
            "nodes": [],
            "edges": [],
            "total_nodes": 0,
            "total_edges": 0
        }

    @classmethod
    def find_connected_crimes(cls, crime_id: str, max_hops: int = 1, limit: int = 25, **kwargs) -> List[Dict[str, Any]]:
        """
        Returns all other Crime nodes connected to this crime (direct or via 1 entity).
        Provides reason, relationship type, confidence, and explicit vs derived distinction.
        """
        clean_id = crime_id.strip().replace("crime:", "")
        crime_node_id = f"crime:{clean_id}"

        if Neo4jService.is_fallback_mode():
            connections: List[Dict[str, Any]] = []
            # Check direct crime-to-crime edges bidirectionally
            seen_crimes = set()
            for rel in Neo4jService._mock_relationships:
                src, tgt = rel["source"], rel["target"]
                other = None
                if (src == crime_node_id or src == clean_id) and (tgt != crime_node_id and tgt != clean_id):
                    other = tgt
                elif (tgt == crime_node_id or tgt == clean_id) and (src != crime_node_id and src != clean_id):
                    other = src

                is_crime = False
                if other:
                    if other.startswith("crime:"):
                        is_crime = True
                    elif other in Neo4jService._mock_nodes:
                        is_crime = (Neo4jService._mock_nodes[other].get("label") == "Crime")

                if is_crime:
                    other_clean = other.replace("crime:", "")
                    if other_clean not in seen_crimes:
                        seen_crimes.add(other_clean)
                        props = rel.get("properties", {})
                        connections.append({
                            "crime_id": other_clean,
                            "relationship": rel.get("relation"),
                            "confidence": props.get("confidence", 1.0),
                            "confidence_type": props.get("confidence_type", "derived"),
                            "source": props.get("source", "knowledge_graph"),
                            "intermediate_entity": props.get("entity_name") or props.get("cluster_id")
                        })
            return connections

        driver = Neo4jService.get_driver()
        raw_id = clean_id
        prefixed_id = f"crime:{raw_id}"
        query = f"""
        MATCH (c1:Crime)-[r]-(c2:Crime)
        WHERE (c1.id = $raw_id OR c1.id = $prefixed_id OR c1.record_id = $raw_id OR c1.record_id = $prefixed_id) AND c1.id <> c2.id
        RETURN DISTINCT c2.id as other_id, c2.record_id as other_record_id,
               c2.category as other_category, type(r) as relation,
               r.confidence as confidence, r.confidence_type as confidence_type,
               r.source as source, r.entity_name as entity_name
        LIMIT {limit}
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                results = session.run(query, {"raw_id": raw_id, "prefixed_id": prefixed_id}).data()
                return [
                    {
                        "crime_id": r["other_id"],
                        "record_id": r.get("other_record_id"),
                        "category": r.get("other_category"),
                        "relationship": r["relation"],
                        "confidence": float(r.get("confidence") or 1.0),
                        "confidence_type": r.get("confidence_type", "derived"),
                        "source": r.get("source", "graph"),
                        "intermediate_entity": r.get("entity_name")
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"Error finding connected crimes in Neo4j: {e}")
            return []

    @classmethod
    def get_pattern_subgraph(cls, pattern_id: str) -> Dict[str, Any]:
        """
        Returns the pattern node, all supporting crimes, and their connected entities.
        """
        clean_pat_id = pattern_id.strip()
        pat_node_id = f"pattern:{clean_pat_id}" if not clean_pat_id.startswith("pattern:") else clean_pat_id

        if Neo4jService.is_fallback_mode():
            pat_node = Neo4jService._mock_nodes.get(pat_node_id) or Neo4jService._mock_nodes.get(clean_pat_id)
            nodes = [pat_node] if pat_node else []
            edges = []
            for r in Neo4jService._mock_relationships:
                if (r["target"] == pat_node_id or r["target"] == clean_pat_id) and r["relation"] == "SUPPORTS":
                    edges.append(r)
                    c_node = Neo4jService._mock_nodes.get(r["source"])
                    if c_node and c_node not in nodes:
                        nodes.append(c_node)

            return {
                "pattern_id": clean_pat_id,
                "nodes": nodes,
                "edges": edges,
                "total_supporting_crimes": len(edges)
            }

        driver = Neo4jService.get_driver()
        raw_id = clean_pat_id.replace("pattern:", "")
        prefixed_id = f"pattern:{raw_id}"
        query = """
        MATCH (pat:Pattern)<-[r:SUPPORTS]-(c:Crime)
        WHERE pat.id = $raw_id OR pat.id = $prefixed_id
        RETURN pat, collect(c) as crimes, collect(r) as relationships
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                rec = session.run(query, {"raw_id": raw_id, "prefixed_id": prefixed_id}).single()
                if rec:
                    pat = rec["pat"]
                    crimes = rec["crimes"]
                    nodes = [{
                        "id": f"pattern:{pat['id']}",
                        "label": "Pattern",
                        "properties": cls._clean_properties(dict(pat))
                    }]
                    edges = []
                    for c in crimes:
                        c_id = f"crime:{c['id']}"
                        nodes.append({
                            "id": c_id,
                            "label": "Crime",
                            "properties": cls._clean_properties(dict(c))
                        })
                        edges.append({
                            "source": c_id,
                            "target": f"pattern:{pat['id']}",
                            "relation": "SUPPORTS",
                            "properties": {"confidence_type": "derived"}
                        })
                    return {
                        "pattern_id": raw_id,
                        "nodes": nodes,
                        "edges": edges,
                        "total_supporting_crimes": len(crimes)
                    }
        except Exception as e:
            logger.error(f"Error fetching pattern subgraph: {e}")

        return {"pattern_id": clean_pat_id, "nodes": [], "edges": [], "total_supporting_crimes": 0}

    @classmethod
    def find_paths_between_crimes(
        cls,
        crime_a: str,
        crime_b: str,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Finds connecting paths between two crime records.
        """
        clean_a = crime_a.strip().replace("crime:", "")
        clean_b = crime_b.strip().replace("crime:", "")

        if Neo4jService.is_fallback_mode():
            # In fallback mode, check direct connection or 1-hop intermediary
            paths: List[Dict[str, Any]] = []
            node_a = f"crime:{clean_a}"
            node_b = f"crime:{clean_b}"

            for r in Neo4jService._mock_relationships:
                if (r["source"] == node_a and r["target"] == node_b) or (r["source"] == node_b and r["target"] == node_a):
                    paths.append({
                        "length": 1,
                        "path": [node_a, r["relation"], node_b],
                        "details": cls._clean_properties(r.get("properties", {}))
                    })

            # Check 2-hop
            for r1 in Neo4jService._mock_relationships:
                if r1["source"] == node_a or r1["target"] == node_a:
                    inter = r1["target"] if r1["source"] == node_a else r1["source"]
                    for r2 in Neo4jService._mock_relationships:
                        if (r2["source"] == inter and r2["target"] == node_b) or (r2["target"] == inter and r2["source"] == node_b):
                            paths.append({
                                "length": 2,
                                "path": [node_a, r1["relation"], inter, r2["relation"], node_b],
                                "intermediate_node": inter
                            })
            return paths

        driver = Neo4jService.get_driver()
        raw_a = clean_a
        prefixed_a = f"crime:{raw_a}"
        raw_b = clean_b
        prefixed_b = f"crime:{raw_b}"
        query = f"""
        MATCH (c1:Crime), (c2:Crime)
        WHERE (c1.id = $raw_a OR c1.id = $prefixed_a OR c1.record_id = $raw_a OR c1.record_id = $prefixed_a)
          AND (c2.id = $raw_b OR c2.id = $prefixed_b OR c2.record_id = $raw_b OR c2.record_id = $prefixed_b)
        MATCH p = allShortestPaths((c1)-[*..{max_depth}]-(c2))
        RETURN [n in nodes(p) | {{id: n.id, label: labels(n)[0]}}] as nodes,
               [r in relationships(p) | {{type: type(r), props: properties(r)}}] as rels,
               length(p) as length
        LIMIT 5
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                results = session.run(query, {
                    "raw_a": raw_a,
                    "prefixed_a": prefixed_a,
                    "raw_b": raw_b,
                    "prefixed_b": prefixed_b
                }).data()
                return [
                    {
                        "length": r["length"],
                        "nodes": r["nodes"],
                        "relationships": [
                            {"type": rel["type"], "props": cls._clean_properties(rel.get("props", {}))}
                            for rel in r.get("rels", [])
                        ]
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"Error finding paths between crimes: {e}")
            return []

    @classmethod
    def get_phone_neighborhood(
        cls,
        phone_number: str,
        depth: int = 2,
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """
        Retrieves the connected neighborhood for a given phone number up to specified depth.
        Includes connected Phones (via CALLS), Crimes (via MENTIONS_PHONE), and Persons (via USES_PHONE).
        """
        clean_num = phone_number.strip()
        phone_node_id = f"phone:{clean_num}" if not clean_num.startswith("phone:") else clean_num
        depth = min(max(1, depth), settings.GRAPH_TRAVERSAL_MAX_DEPTH)

        if Neo4jService.is_fallback_mode():
            visited_nodes: Dict[str, Dict[str, Any]] = {}
            visited_edges: List[Dict[str, Any]] = []
            queue = [(phone_node_id, 0)]
            seen = {phone_node_id}

            if phone_node_id in Neo4jService._mock_nodes:
                visited_nodes[phone_node_id] = Neo4jService._mock_nodes[phone_node_id]

            while queue and len(visited_nodes) < max_nodes:
                curr_id, d = queue.pop(0)
                if d >= depth:
                    continue

                for rel in Neo4jService._mock_relationships:
                    src = rel["source"]
                    tgt = rel["target"]
                    if src == curr_id or tgt == curr_id:
                        other = tgt if src == curr_id else src
                        visited_edges.append(rel)

                        if other not in seen and len(visited_nodes) < max_nodes:
                            seen.add(other)
                            if other in Neo4jService._mock_nodes:
                                visited_nodes[other] = Neo4jService._mock_nodes[other]
                            queue.append((other, d + 1))

            return {
                "center_node_id": phone_node_id,
                "nodes": list(visited_nodes.values()),
                "edges": visited_edges,
                "total_nodes": len(visited_nodes),
                "total_edges": len(visited_edges)
            }

        driver = Neo4jService.get_driver()
        num_clean = clean_num.replace("phone:", "")
        prefixed_id = f"phone:{num_clean}"

        match_start_query = """
        MATCH (start:Phone)
        WHERE start.number = $num_clean OR start.id = $prefixed_id OR start.id = $num_clean
        RETURN start
        LIMIT 1
        """
        paths_query = f"""
        MATCH (start:Phone)
        WHERE start.number = $num_clean OR start.id = $prefixed_id OR start.id = $num_clean
        MATCH path = (start)-[r*1..{depth}]-(neighbor)
        RETURN path
        LIMIT {max_nodes}
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                params = {"num_clean": num_clean, "prefixed_id": prefixed_id}
                start_rec = session.run(match_start_query, params).single()
                if start_rec and start_rec["start"]:
                    start_node = start_rec["start"]
                    center_id = start_node.get("id") or prefixed_id
                    nodes_map = {
                        center_id: {
                            "id": center_id,
                            "label": list(start_node.labels)[0] if start_node.labels else "Phone",
                            "properties": cls._clean_properties(dict(start_node))
                        }
                    }
                    edges_list = []
                    seen_edges = set()

                    paths_result = session.run(paths_query, params)
                    for record in paths_result:
                        path = record["path"]
                        for n in path.nodes:
                            nid = n.get("id") or str(n.id)
                            if nid not in nodes_map:
                                nodes_map[nid] = {
                                    "id": nid,
                                    "label": list(n.labels)[0] if n.labels else "Entity",
                                    "properties": cls._clean_properties(dict(n))
                                }
                        for rel in path.relationships:
                            src_id = rel.start_node.get("id") or str(rel.start_node.id)
                            tgt_id = rel.end_node.get("id") or str(rel.end_node.id)
                            edge_key = (src_id, tgt_id, rel.type)
                            if edge_key not in seen_edges:
                                seen_edges.add(edge_key)
                                edges_list.append({
                                    "source": src_id,
                                    "target": tgt_id,
                                    "relation": rel.type,
                                    "properties": cls._clean_properties(dict(rel))
                                })

                    return {
                        "center_node_id": center_id,
                        "nodes": list(nodes_map.values()),
                        "edges": edges_list,
                        "total_nodes": len(nodes_map),
                        "total_edges": len(edges_list)
                    }
        except Exception as e:
            logger.error(f"Error executing get_phone_neighborhood: {e}", exc_info=True)

        return {
            "center_node_id": phone_node_id,
            "nodes": [],
            "edges": [],
            "total_nodes": 0,
            "total_edges": 0
        }

    @classmethod
    def find_crimes_by_phone(cls, phone_number: str) -> List[Dict[str, Any]]:
        """
        Finds all crime incidents connected to a given phone number.
        """
        clean_num = phone_number.strip().replace("phone:", "")
        phone_node_id = f"phone:{clean_num}"

        if Neo4jService.is_fallback_mode():
            linked_crimes = []
            for rel in Neo4jService._mock_relationships:
                if rel.get("relation") == "MENTIONS_PHONE":
                    if rel.get("target") == phone_node_id:
                        c_id = rel.get("source")
                        c_node = Neo4jService._mock_nodes.get(c_id)
                        if c_node:
                            linked_crimes.append(cls._clean_properties(c_node.get("properties", {})))
            return linked_crimes

        driver = Neo4jService.get_driver()
        query = """
        MATCH (c:Crime)-[r:MENTIONS_PHONE]->(p:Phone)
        WHERE p.number = $num OR p.id = $prefixed_id OR p.id = $num
        RETURN properties(c) as crime, properties(r) as relationship
        LIMIT 50
        """
        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                results = session.run(query, {"num": clean_num, "prefixed_id": phone_node_id}).data()
                return [
                    {
                        "crime": cls._clean_properties(r.get("crime", {})),
                        "relationship": cls._clean_properties(r.get("relationship", {}))
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"Error finding crimes by phone: {e}")
            return []

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Returns knowledge graph statistics."""
        return Neo4jService.get_stats()
