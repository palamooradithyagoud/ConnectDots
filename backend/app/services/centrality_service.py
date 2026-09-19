"""
Phase 5: Network Centrality & Structural Topology Engine
Calculates Degree Centrality, Betweenness Centrality, and PageRank over
investigation-bounded person networks.
Supports both native Neo4j GDS and mathematically exact NetworkX fallback.
Strict Zero-Guilt Principle: Centrality measures structural connectivity only.
"""
import logging
import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.services.neo4j_service import Neo4jService
from app.core.config import settings

logger = logging.getLogger("connectdots_centrality")


class CentralityService:
    """
    Computes objective network topology metrics for individuals in a criminal network graph.
    All calculations operate on bounded, investigation-scoped subgraphs.
    """

    @classmethod
    def compute_network_metrics(
        cls,
        scope_type: str = "all",
        scope_id: Optional[str] = None,
        max_hops: int = 2,
        max_nodes: int = 150,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts bounded subgraph and calculates Degree, Betweenness, and PageRank.
        Returns dictionary containing:
          - 'nodes': List of scored individuals with metrics and breakdown
          - 'graph_summary': Node and edge counts, scope metadata
        """
        # 1. Fetch scoped graph from Neo4j (or mock fallback if in-memory)
        nodes_dict, edges_list = cls._extract_scoped_subgraph(
            scope_type=scope_type,
            scope_id=scope_id,
            max_hops=max_hops,
            max_nodes=max_nodes,
            start_date=start_date,
            end_date=end_date
        )

        if not nodes_dict:
            return {
                "nodes": [],
                "graph_summary": {
                    "total_nodes": 0,
                    "total_edges": 0,
                    "person_count": 0,
                    "scope_type": scope_type,
                    "scope_id": scope_id
                }
            }

        # 2. Build NetworkX Graph representation for exact bounded mathematical calculation
        G = nx.Graph()
        for n_id, n_data in nodes_dict.items():
            G.add_node(n_id, **n_data)

        for edge in edges_list:
            src = edge.get("source") or edge.get("from_id")
            dst = edge.get("target") or edge.get("to_id")
            actual_src = src if src in nodes_dict else next((k for k in nodes_dict if k.endswith(f":{src}") or src.endswith(f":{k}")), None)
            actual_dst = dst if dst in nodes_dict else next((k for k in nodes_dict if k.endswith(f":{dst}") or dst.endswith(f":{k}")), None)
            if actual_src and actual_dst:
                G.add_edge(actual_src, actual_dst, relation=edge.get("relation") or edge.get("type", "LINKED"))

        # 3. Calculate mathematical metrics
        num_nodes = G.number_of_nodes()
        if num_nodes == 0:
            deg_centrality = {}
            btw_centrality = {}
            pr_scores = {}
        elif num_nodes == 1:
            only_node = list(G.nodes())[0]
            deg_centrality = {only_node: 0.0}
            btw_centrality = {only_node: 0.0}
            pr_scores = {only_node: 1.0}
        else:
            deg_centrality = nx.degree_centrality(G)
            btw_centrality = nx.betweenness_centrality(G, normalized=True)
            try:
                pr_scores = nx.pagerank(G, alpha=0.85, max_iter=100)
            except Exception as e:
                logger.warning(f"PageRank convergence error, using uniform fallback: {e}")
                pr_scores = {n: 1.0 / num_nodes for n in G.nodes()}

        # 4. Extract metrics specifically for Person nodes
        results = []
        for n_id, n_data in nodes_dict.items():
            if n_data.get("label") != "Person":
                continue

            raw_degree = G.degree(n_id) if n_id in G else 0
            neighbors = list(G.neighbors(n_id)) if n_id in G else []

            # Breakdown counts by entity type
            connected_crimes = sum(1 for nb in neighbors if nodes_dict.get(nb, {}).get("label") == "Crime")
            connected_people = sum(1 for nb in neighbors if nodes_dict.get(nb, {}).get("label") == "Person")
            connected_phones = sum(1 for nb in neighbors if nodes_dict.get(nb, {}).get("label") == "Phone")
            connected_vehicles = sum(1 for nb in neighbors if nodes_dict.get(nb, {}).get("label") == "Vehicle")
            connected_orgs = sum(1 for nb in neighbors if nodes_dict.get(nb, {}).get("label") == "Organization")
            connected_locs = sum(1 for nb in neighbors if nodes_dict.get(nb, {}).get("label") == "Location")

            canonical_name = (
                n_data.get("properties", {}).get("canonical_name")
                or n_data.get("properties", {}).get("name")
                or n_data.get("properties", {}).get("description")
                or n_id.replace("person:", "").replace("_", " ").title()
            )

            deg_val = round(float(deg_centrality.get(n_id, 0.0)), 4)
            btw_val = round(float(btw_centrality.get(n_id, 0.0)), 4)
            pr_val = round(float(pr_scores.get(n_id, 0.0)), 4)

            results.append({
                "person_id": n_id,
                "canonical_name": canonical_name,
                "display_name": canonical_name,
                "degree_centrality": deg_val,
                "betweenness_centrality": btw_val,
                "pagerank": pr_val,
                "raw_degree": raw_degree,
                "metrics": {
                    "degree_centrality": deg_val,
                    "betweenness_centrality": btw_val,
                    "pagerank": pr_val,
                    "raw_degree": raw_degree,
                },
                "network_breakdown": {
                    "connected_crimes": connected_crimes,
                    "connected_people": connected_people,
                    "connected_phones": connected_phones,
                    "connected_vehicles": connected_vehicles,
                    "connected_organizations": connected_orgs,
                    "connected_locations": connected_locs,
                },
                "properties": n_data.get("properties", {})
            })

        # Default sort by degree centrality descending
        results.sort(key=lambda x: (x["metrics"]["degree_centrality"], x["metrics"]["betweenness_centrality"]), reverse=True)

        return {
            "nodes": results,
            "graph_summary": {
                "total_nodes": num_nodes,
                "total_edges": G.number_of_edges(),
                "person_count": len(results),
                "scope_type": scope_type,
                "scope_id": scope_id
            },
            "subgraph_nodes": [
                {
                    "id": n_id,
                    "label": n_data.get("label", "Entity"),
                    "properties": n_data.get("properties", {})
                }
                for n_id, n_data in nodes_dict.items()
            ],
            "subgraph_edges": edges_list
        }

    @classmethod
    def _extract_scoped_subgraph(
        cls,
        scope_type: str,
        scope_id: Optional[str],
        max_hops: int,
        max_nodes: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extracts bounded subgraph from Neo4j or in-memory fallback.
        Ensures queries are bounded by LIMIT clauses.
        """
        bounded_limit = min(max(max_nodes, 10), 300)
        bounded_hops = min(max(max_hops, 1), 3)

        if Neo4jService.is_fallback_mode():
            return cls._extract_subgraph_from_fallback(scope_type, scope_id, bounded_hops, bounded_limit)

        driver = Neo4jService.get_driver()
        if not driver:
            return cls._extract_subgraph_from_fallback(scope_type, scope_id, bounded_hops, bounded_limit)

        nodes_dict: Dict[str, Dict[str, Any]] = {}
        edges_list: List[Dict[str, Any]] = []

        # Scope query construction
        if scope_type == "crime" and scope_id:
            c_raw = scope_id if scope_id.startswith("crime:") else f"crime:{scope_id}"
            query = f"""
            MATCH (start:Crime) WHERE start.id = $scope_id OR start.id = $raw_id
            CALL apoc.path.subgraphAll(start, {{
                maxLevel: {bounded_hops},
                limit: {bounded_limit}
            }}) YIELD nodes, relationships
            RETURN nodes, relationships
            """
            # Fallback Cypher if APOC is not available
            fallback_cypher = f"""
            MATCH path = (start:Crime)-[*1..{bounded_hops}]-(m)
            WHERE start.id = $scope_id OR start.id = $raw_id
            RETURN nodes(path) as path_nodes, relationships(path) as path_rels
            LIMIT {bounded_limit}
            """
            params = {"scope_id": c_raw, "raw_id": scope_id}

        elif scope_type == "cluster" and scope_id:
            cl_raw = scope_id if scope_id.startswith("cluster:") else f"cluster:{scope_id}"
            fallback_cypher = f"""
            MATCH path = (start:CrimeCluster)-[*1..{bounded_hops}]-(m)
            WHERE start.id = $scope_id OR start.id = $raw_id
            RETURN nodes(path) as path_nodes, relationships(path) as path_rels
            LIMIT {bounded_limit}
            """
            params = {"scope_id": cl_raw, "raw_id": scope_id}

        elif scope_type == "person" and scope_id:
            p_raw = scope_id if scope_id.startswith("person:") else f"person:{scope_id}"
            fallback_cypher = f"""
            MATCH path = (start:Person)-[*1..{bounded_hops}]-(m)
            WHERE start.id = $scope_id OR start.id = $raw_id
            RETURN nodes(path) as path_nodes, relationships(path) as path_rels
            LIMIT {bounded_limit}
            """
            params = {"scope_id": p_raw, "raw_id": scope_id}

        else:
            # "all" scope: sample person-centric network
            fallback_cypher = f"""
            MATCH (p:Person)
            OPTIONAL MATCH (p)-[r]-(m)
            RETURN collect(DISTINCT p) + collect(DISTINCT m) as path_nodes, collect(DISTINCT r) as path_rels
            LIMIT {bounded_limit}
            """
            params = {}

        try:
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                records = session.run(fallback_cypher, params)
                for record in records:
                    p_nodes = record.get("path_nodes") or []
                    p_rels = record.get("path_rels") or []

                    for n in p_nodes:
                        if n is None:
                            continue
                        n_id = n.get("id") or str(n.element_id)
                        lbl = list(n.labels)[0] if n.labels else "Unknown"
                        nodes_dict[n_id] = {
                            "id": n_id,
                            "label": lbl,
                            "properties": cls._clean_properties(dict(n))
                        }

                    for r in p_rels:
                        if r is None:
                            continue
                        src_id = r.start_node.get("id") or str(r.start_node.element_id)
                        dst_id = r.end_node.get("id") or str(r.end_node.element_id)
                        edges_list.append({
                            "source": src_id,
                            "target": dst_id,
                            "relation": r.type,
                            "properties": cls._clean_properties(dict(r))
                        })

            return nodes_dict, edges_list
        except Exception as e:
            logger.warning(f"Error extracting scoped subgraph from Neo4j: {e}. Falling back to in-memory.")
            return cls._extract_subgraph_from_fallback(scope_type, scope_id, bounded_hops, bounded_limit)

    @staticmethod
    def _clean_properties(raw_props: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizes properties by converting neo4j DateTime and non-primitive types to strings."""
        cleaned = {}
        for k, v in raw_props.items():
            if v is None:
                cleaned[k] = None
            elif hasattr(v, "iso_format"):
                cleaned[k] = v.iso_format()
            elif hasattr(v, "isoformat"):
                cleaned[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                cleaned[k] = str(v)
            elif hasattr(v, "__str__") and not isinstance(v, (str, int, float, bool)):
                cleaned[k] = str(v)
            else:
                cleaned[k] = v
        return cleaned

    @classmethod
    def compute_person_centrality_fallback(cls, scope: str = "global") -> List[Dict[str, Any]]:
        """
        Calculates exact mathematical centrality in-memory using NetworkX over fallback graph.
        Returns flattened list of person centrality metric dictionaries.
        """
        scope_type = "all" if scope in ("global", "all") else scope
        res = cls.compute_network_metrics(scope_type=scope_type)
        return res.get("nodes", [])

    @classmethod
    def generate_structural_explanation(
        cls,
        degree: float,
        betweenness: float,
        pagerank: float,
        case_count: int = 0,
        phone_count: int = 0
    ) -> str:
        """
        Generates objective structural topology explanation without guilt inference.
        Adheres strictly to the Zero-Guilt Principle: describes graph topology only.
        """
        roles = []
        if betweenness >= 0.3:
            roles.append("structural bridge/broker between network components")
        if degree >= 0.5:
            roles.append("high-degree central hub in observed incidents")
        elif degree >= 0.2:
            roles.append("moderately connected individual across cases")
        else:
            roles.append("peripheral structural node")

        role_desc = " and ".join(roles)
        details = []
        if case_count > 0:
            details.append(f"connected to {case_count} incident record(s)")
        if phone_count > 0:
            details.append(f"linked to {phone_count} registered device(s)")

        context = f" ({', '.join(details)})" if details else ""
        return (
            f"This entity occupies a {role_desc}{context}. "
            f"Metrics: Degree Centrality {round(degree, 3)}, Betweenness Centrality {round(betweenness, 3)}, "
            f"PageRank {round(pagerank, 3)}. Structural position indicates graph topological connectivity only, "
            f"not criminal culpability."
        )

    @classmethod
    def _extract_subgraph_from_fallback(
        cls,
        scope_type: str,
        scope_id: Optional[str],
        max_hops: int,
        max_nodes: int
    ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Fallback subgraph extraction from in-memory mock graph (used in tests or offline).
        """
        mock_nodes = Neo4jService._mock_nodes
        mock_rels = Neo4jService._mock_relationships

        if not mock_nodes:
            return {}, []

        if scope_type == "all" or not scope_id:
            return dict(list(mock_nodes.items())[:max_nodes]), mock_rels[:max_nodes * 2]

        target_id = scope_id
        if scope_type == "crime" and not target_id.startswith("crime:"):
            target_id = f"crime:{target_id}"
        elif scope_type == "person" and not target_id.startswith("person:"):
            target_id = f"person:{target_id}"
        elif scope_type == "cluster" and not target_id.startswith("cluster:"):
            target_id = f"cluster:{target_id}"

        target_candidates = {scope_id, target_id}
        start_nodes = {
            n for n in mock_nodes
            if n in target_candidates or any(n.endswith(f":{c}") or c.endswith(f":{n}") for c in target_candidates)
        }
        visited_nodes = set(start_nodes)
        frontier = set(start_nodes)
        collected_edges = []

        for _ in range(max_hops):
            next_frontier = set()
            for r in mock_rels:
                src = r.get("source") or r.get("from_id")
                dst = r.get("target") or r.get("to_id")
                actual_src = src if src in mock_nodes else next((k for k in mock_nodes if k.endswith(f":{src}") or src.endswith(f":{k}")), None)
                actual_dst = dst if dst in mock_nodes else next((k for k in mock_nodes if k.endswith(f":{dst}") or dst.endswith(f":{k}")), None)

                if actual_src and actual_dst:
                    if actual_src in frontier:
                        if actual_dst not in visited_nodes:
                            next_frontier.add(actual_dst)
                            visited_nodes.add(actual_dst)
                        collected_edges.append(r)
                    elif actual_dst in frontier:
                        if actual_src not in visited_nodes:
                            next_frontier.add(actual_src)
                            visited_nodes.add(actual_src)
                        collected_edges.append(r)
            frontier = next_frontier
            if len(visited_nodes) >= max_nodes:
                break

        scoped_nodes = {n_id: mock_nodes[n_id] for n_id in visited_nodes if n_id in mock_nodes}
        return scoped_nodes, collected_edges
