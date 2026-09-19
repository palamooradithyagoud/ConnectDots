"""
Phase 7: Domain AI Investigation Agent — REST Endpoints
Provides endpoints for executing agentic investigations, inspecting tool contracts, and retrieving scenario examples.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.agent.agent_service import DomainAgentService
from app.services.agent.tool_registry import ToolRegistry
from app.schemas.agent import (
    AgentInvestigateRequest,
    AgentInvestigationResponse,
    AgentToolInfoResponse,
    AgentExamplesResponse,
    AgentExampleItem
)

router = APIRouter()
logger = logging.getLogger("connectdots_agent_api")


@router.post("/investigate", response_model=AgentInvestigationResponse, summary="Execute Domain AI Investigation")
async def investigate(
    payload: AgentInvestigateRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a bounded, domain-specific AI investigation:
    1. Question understanding & classification
    2. Dynamic planning across 16 allowlisted investigation tools
    3. Safe tool execution across PostgreSQL, Neo4j, Qdrant, and ML engines
    4. Evidence fusion, deduplication, and validation status filtering
    5. Grounded Groq synthesis with verifiable citations and uncertainty tracking
    """
    try:
        service = DomainAgentService(db=db)
        result = await service.investigate(
            question=payload.question,
            user_scope=payload.scope,
            investigation_id=payload.investigation_id
        )
        return result
    except Exception as e:
        logger.error(f"Agent investigation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent investigation error: {str(e)}")


@router.get("/tools", response_model=AgentToolInfoResponse, summary="List Approved Investigation Tools")
def list_tools():
    """
    Returns the allowlist of 16 approved investigation tools with their schemas and limits.
    """
    tools = ToolRegistry.list_tools()
    return {
        "tools": tools,
        "total": len(tools)
    }


@router.get("/examples", response_model=AgentExamplesResponse, summary="Get Investigation Scenarios")
def get_investigation_examples():
    """
    Returns verified domain investigation scenarios corresponding to law enforcement questions.
    """
    examples = [
        AgentExampleItem(
            title="Cross-Case Phone Linkage",
            scenario="Scenario 1",
            question="Find cases connected to Case 1042 through phones."
        ),
        AgentExampleItem(
            title="Structural Centrality",
            scenario="Scenario 2",
            question="Who are the structurally central individuals around Case 1042?"
        ),
        AgentExampleItem(
            title="Human Validation Audit",
            scenario="Scenario 3",
            question="Which connections around Case 1042 have been investigator validated?"
        ),
        AgentExampleItem(
            title="Anomaly & Pattern Detection",
            scenario="Scenario 4",
            question="Find unusual activity around Case 1042."
        ),
        AgentExampleItem(
            title="Entity Path & Corroboration",
            scenario="Scenario 5",
            question="Explain the relationship between Person A and Person B."
        ),
    ]
    return {"examples": examples}
