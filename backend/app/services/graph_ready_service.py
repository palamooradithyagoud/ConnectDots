from typing import Dict, List, Any


class GraphReadyService:
    """
    Constructs Graph-Ready nodes and relationships from extracted NLP entities and metadata.
    Enables zero-friction ingestion into Neo4j in Phase 4 without introducing Neo4j in Phase 2.
    """

    @classmethod
    def generate_graph_payload(
        cls,
        crime_id: str,
        record_id: str,
        category: str,
        occurred_at: str,
        entities: Dict[str, List[str]],
        modus_operandi: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Builds graph-ready node and edge structures for downstream Knowledge Graph ingestion.
        """
        crime_node_id = f"crime:{record_id}"

        nodes: List[Dict[str, Any]] = [
            {
                "id": crime_node_id,
                "label": "Crime",
                "properties": {
                    "crime_id": crime_id,
                    "record_id": record_id,
                    "category": category,
                    "occurred_at": occurred_at,
                }
            }
        ]

        relationships: List[Dict[str, Any]] = []

        # 1. Locations
        for loc in entities.get("locations", []):
            loc_id = f"location:{loc.strip().replace(' ', '_').lower()}"
            nodes.append({
                "id": loc_id,
                "label": "Location",
                "properties": {"name": loc.strip()}
            })
            relationships.append({
                "source": crime_node_id,
                "relation": "OCCURRED_AT",
                "target": loc_id
            })

        # 2. Weapons
        for wpn in entities.get("weapons", []):
            wpn_id = f"weapon:{wpn.strip().replace(' ', '_').lower()}"
            nodes.append({
                "id": wpn_id,
                "label": "Weapon",
                "properties": {"name": wpn.strip()}
            })
            relationships.append({
                "source": crime_node_id,
                "relation": "USED_WEAPON",
                "target": wpn_id
            })

        # 3. Vehicles
        for veh in entities.get("vehicles", []):
            veh_id = f"vehicle:{veh.strip().replace(' ', '_').lower()}"
            nodes.append({
                "id": veh_id,
                "label": "Vehicle",
                "properties": {"name": veh.strip()}
            })
            relationships.append({
                "source": crime_node_id,
                "relation": "USED_VEHICLE",
                "target": veh_id
            })

        # 4. Modus Operandi
        for mo in modus_operandi:
            mo_pattern = mo.get("pattern", "")
            if mo_pattern:
                mo_id = f"mo:{mo_pattern.strip().replace(' ', '_').lower()}"
                nodes.append({
                    "id": mo_id,
                    "label": "ModusOperandi",
                    "properties": {
                        "pattern": mo_pattern,
                        "certainty": mo.get("certainty", "explicitly_stated")
                    }
                })
                relationships.append({
                    "source": crime_node_id,
                    "relation": "EXHIBITS_MO",
                    "target": mo_id
                })

        # 5. Organizations / Establishments
        for org in entities.get("organizations", []):
            org_id = f"organization:{org.strip().replace(' ', '_').lower()}"
            nodes.append({
                "id": org_id,
                "label": "Organization",
                "properties": {"name": org.strip()}
            })
            relationships.append({
                "source": crime_node_id,
                "relation": "TARGETED_ESTABLISHMENT",
                "target": org_id
            })

        # 6. Persons / Suspects
        for p in entities.get("persons", []):
            p_id = f"person:{p.strip().replace(' ', '_').lower()}"
            nodes.append({
                "id": p_id,
                "label": "PersonOfInterest",
                "properties": {"description": p.strip()}
            })
            relationships.append({
                "source": crime_node_id,
                "relation": "INVOLVES_PERSON",
                "target": p_id
            })

        # 7. Phone Numbers
        for ph in entities.get("phones", []):
            clean_ph = ph.strip()
            ph_id = f"phone:{clean_ph}"
            nodes.append({
                "id": ph_id,
                "label": "Phone",
                "properties": {"number": clean_ph}
            })
            relationships.append({
                "source": crime_node_id,
                "relation": "MENTIONS_PHONE",
                "target": ph_id
            })

        # Deduplicate nodes by id
        unique_nodes = {n["id"]: n for n in nodes}

        return {
            "crime_id": crime_id,
            "record_id": record_id,
            "nodes": list(unique_nodes.values()),
            "relationships": relationships
        }
