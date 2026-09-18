"""
Phase 4: Knowledge Graph API Endpoints
Provides graph synchronization, graph metrics, crime neighborhood retrieval, and path traversal.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.graph_sync_service import GraphSyncService
from app.services.graph_query_service import GraphQueryService
from app.services.neo4j_service import Neo4jService
from app.schemas.graph import (
    GraphSubgraphResponse,
    GraphStatsResponse,
    GraphSyncResponse,
    ConnectedCrimeItem
)

router = APIRouter()
logger = logging.getLogger("connectdots_graph_api")


@router.post("/sync", response_model=GraphSyncResponse, summary="Synchronize Postgres, NLP & ML to Neo4j")
def sync_graph(db: Session = Depends(get_db)):
    """
    Executes an idempotent synchronization of:
      1. PostgreSQL Crime records
      2. Phase 2 NLP entities & explicit relationships
      3. Phase 3 ML clusters & patterns
      4. Derived cross-incident relationships (shared entities, clusters, semantics)
    """
    try:
        result = GraphSyncService.sync_all(db)
        return result
    except Exception as e:
        logger.error(f"Graph sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Graph sync error: {str(e)}")


@router.get("/stats", response_model=GraphStatsResponse, summary="Get Knowledge Graph Statistics")
def get_graph_stats():
    """
    Returns current node counts, relationship totals, and breakdown by explicit/derived types.
    """
    return Neo4jService.get_stats()


@router.get("/crimes/{crime_id}", response_model=GraphSubgraphResponse, summary="Get Crime Subgraph Neighborhood")
def get_crime_subgraph(
    crime_id: str,
    depth: int = Query(2, ge=1, le=3, description="Graph traversal depth"),
    max_nodes: int = Query(50, ge=5, le=100, description="Maximum nodes to return")
):
    """
    Returns the connected graph neighborhood (entities, weapons, vehicles, locations, patterns)
    around a specified crime record.
    """
    subgraph = GraphQueryService.get_crime_neighborhood(crime_id=crime_id, depth=depth, max_nodes=max_nodes)
    return subgraph


@router.get("/crimes/{crime_id}/connections", response_model=List[ConnectedCrimeItem], summary="Find Connected Crimes")
def get_connected_crimes(crime_id: str):
    """
    Returns other crime incidents connected to the specified crime via explicit or derived relationships.
    """
    connections = GraphQueryService.find_connected_crimes(crime_id=crime_id)
    return connections


@router.get("/patterns/{pattern_id}", summary="Get Pattern Subgraph")
def get_pattern_subgraph(pattern_id: str):
    """
    Returns the subgraph for a Phase 3 pattern, its supporting crimes, and common entities.
    """
    return GraphQueryService.get_pattern_subgraph(pattern_id=pattern_id)


@router.get("/paths", summary="Find Shortest Paths Between Crimes")
def find_paths_between_crimes(
    crime_a: str = Query(..., description="First crime ID"),
    crime_b: str = Query(..., description="Second crime ID"),
    max_depth: int = Query(3, ge=1, le=4)
):
    """
    Finds connecting paths and intermediate entities between two crime incidents.
    """
    paths = GraphQueryService.find_paths_between_crimes(crime_a=crime_a, crime_b=crime_b, max_depth=max_depth)
    return {"crime_a": crime_a, "crime_b": crime_b, "paths": paths}
