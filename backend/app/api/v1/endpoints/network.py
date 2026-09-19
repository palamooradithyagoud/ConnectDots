"""
Phase 5: Person Network & Key Individual Intelligence REST Endpoints
Provides endpoints for key individual discovery, centrality analysis,
person dossiers, grounded evidence, and investigation scopes.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.crime import Crime
from app.models.ml_models import CrimeCluster
from app.services.key_individual_service import KeyIndividualService
from app.services.centrality_service import CentralityService
from app.schemas.network import (
    KeyIndividualsListResponse,
    PersonDetailResponse,
    PersonEvidenceItem,
    ScopeItem
)

router = APIRouter()
logger = logging.getLogger("connectdots_network_api")


@router.get("/key-individuals", response_model=KeyIndividualsListResponse, summary="List Ranked Key Individuals")
def get_key_individuals(
    scope_type: Optional[str] = Query(None, description="Scope type: all, crime, cluster, person"),
    scope: Optional[str] = Query(None, description="Alias for scope_type (e.g. global, crime)"),
    scope_id: Optional[str] = Query(None, description="Scope identifier (crime_id or cluster_id)"),
    sort_by: str = Query("degree_centrality", description="Metric to sort by: degree_centrality, betweenness_centrality, pagerank, raw_degree"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Page limit"),
    offset: Optional[int] = Query(None, ge=0, description="Offset for pagination"),
    page: Optional[int] = Query(None, ge=1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Returns ranked key individuals within the specified network scope based on objective
    centrality metrics (Degree, Betweenness, PageRank).
    """
    target_scope = "all"
    if scope:
        target_scope = "all" if scope in ("global", "all") else scope
    elif scope_type:
        target_scope = "all" if scope_type in ("global", "all") else scope_type

    if page is not None and page_size is not None:
        eff_limit = page_size
        eff_offset = (page - 1) * page_size
    else:
        eff_limit = limit if limit is not None else (page_size or 20)
        eff_offset = offset if offset is not None else 0

    try:
        res = KeyIndividualService.get_key_individuals(
            db=db,
            scope_type=target_scope,
            scope_id=scope_id,
            sort_by=sort_by,
            limit=eff_limit,
            offset=eff_offset
        )
        return res
    except Exception as e:
        logger.error(f"Error fetching key individuals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate key individuals: {str(e)}")


@router.get("/key-individuals/{person_id}", response_model=PersonDetailResponse, summary="Get Key Individual Detail")
@router.get("/person/{person_id}", response_model=PersonDetailResponse, summary="Get Person Profile & Network Dossier")
def get_person_profile(
    person_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves complete structural and evidentiary profile for a single person:
    metrics, associated crimes, phone numbers, CDR communication stats, and local graph.
    """
    profile = KeyIndividualService.get_person_detail(db=db, person_id=person_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Person '{person_id}' not found.")
    return profile


@router.get("/crimes/{crime_id}/key-individuals", summary="Get Crime-Scoped Key Individuals")
def get_crime_key_individuals(
    crime_id: str,
    sort_by: str = Query("degree_centrality"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Calculates and returns key individuals scoped to a specific crime's connected graph neighborhood.
    """
    # Verify crime exists
    crime = db.query(Crime).filter((Crime.id == crime_id) | (Crime.record_id == crime_id)).first()
    if not crime:
        raise HTTPException(status_code=404, detail=f"Crime '{crime_id}' not found.")

    res = KeyIndividualService.get_key_individuals(
        db=db,
        scope_type="crime",
        scope_id=crime.id,
        sort_by=sort_by,
        limit=limit,
        offset=0
    )
    return res.get("items", [])


@router.get("/crimes/{crime_id}/subgraph", summary="Get Crime-Scoped Person Subgraph")
def get_crime_person_subgraph(
    crime_id: str,
    depth: Optional[int] = Query(None, ge=1, le=3),
    max_hops: Optional[int] = Query(2, ge=1, le=3),
    max_nodes: int = Query(50, ge=5, le=150)
):
    """
    Returns nodes and edges for visualizing the person network surrounding a crime.
    """
    hops = depth if depth is not None else (max_hops or 2)
    res = CentralityService.compute_network_metrics(
        scope_type="crime",
        scope_id=crime_id,
        max_hops=hops,
        max_nodes=max_nodes
    )
    nodes = res.get("subgraph_nodes", [])
    edges = res.get("subgraph_edges", [])
    summary = res.get("graph_summary", {})
    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": summary.get("total_nodes", len(nodes)),
        "total_edges": summary.get("total_edges", len(edges)),
        "summary": summary
    }


@router.get("/person/{person_id}/evidence", summary="Get Grounded Person Evidence")
def get_person_evidence(
    person_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns verifiable source citations grounding this individual's presence in police reports and telecom logs.
    """
    evidence = KeyIndividualService.get_person_evidence(db=db, person_id=person_id)
    return {
        "person_id": person_id,
        "evidence": evidence
    }


@router.get("/scopes", summary="Get Available Investigation Scopes")
def get_scopes(db: Session = Depends(get_db)):
    """
    Returns available scopes for investigation filtering (all network, specific crimes, clusters).
    """
    scopes = [
        ScopeItem(
            scope_type="all",
            scope_id="all",
            display_label="Entire Observed Network",
            detail="All connected entities across all cases"
        )
    ]

    crimes = db.query(Crime).order_by(Crime.occurred_at.desc()).limit(15).all()
    for c in crimes:
        scopes.append(ScopeItem(
            scope_type="crime",
            scope_id=c.id,
            display_label=f"Case {c.record_id} ({c.category})",
            detail=c.location_name or "Unknown location"
        ))

    clusters = db.query(CrimeCluster).limit(10).all()
    for cl in clusters:
        scopes.append(ScopeItem(
            scope_type="cluster",
            scope_id=cl.id,
            display_label=f"Cluster: {cl.cluster_label}",
            detail=f"{cl.crime_count} incidents"
        ))

    return {
        "scopes": ["global", "crime", "cluster", "person"],
        "scope_options": scopes,
        "items": scopes
    }
