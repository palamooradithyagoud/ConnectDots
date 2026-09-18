"""
Phase 4: Graph Pydantic Schemas
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphSubgraphResponse(BaseModel):
    center_node_id: Optional[str] = None
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0


class GraphStatsResponse(BaseModel):
    status: str
    is_fallback: bool = False
    crime_nodes: int = 0
    location_nodes: int = 0
    vehicle_nodes: int = 0
    weapon_nodes: int = 0
    mo_nodes: int = 0
    person_nodes: int = 0
    organization_nodes: int = 0
    cluster_nodes: int = 0
    pattern_nodes: int = 0
    total_nodes: int = 0
    total_relationships: int = 0
    explicit_relationships: int = 0
    derived_relationships: int = 0
    last_sync: Optional[str] = None


class GraphSyncResponse(BaseModel):
    status: str
    crimes_synced: int = 0
    entities_synced: int = 0
    explicit_relationships_created: int = 0
    derived_relationships_created: int = 0
    graph_stats: Dict[str, Any] = Field(default_factory=dict)


class ConnectedCrimeItem(BaseModel):
    crime_id: str
    record_id: Optional[str] = None
    category: Optional[str] = None
    relationship: str
    confidence: float = 1.0
    confidence_type: str = "derived"
    source: str = "knowledge_graph"
    intermediate_entity: Optional[str] = None
