"""
Phase 7: Domain AI Investigation Agent — REST API Schemas
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.agent.models import (
    AgentInvestigationResponse,
    InvestigationFinding,
    KeyIndividualFinding,
    NormalizedEvidence,
    ToolTraceItem,
    ToolDefinition,
    InvestigationPlan,
)


class AgentInvestigateRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Natural-language criminal investigation question")
    scope: Optional[Dict[str, Any]] = Field(default=None, description="Optional scope overrides such as crime_id, phone_number, max_hops")
    investigation_id: Optional[str] = Field(default=None, description="Optional client-assigned investigation UUID")


class AgentToolInfoResponse(BaseModel):
    tools: List[ToolDefinition]
    total: int


class AgentExampleItem(BaseModel):
    title: str
    scenario: str
    question: str


class AgentExamplesResponse(BaseModel):
    examples: List[AgentExampleItem]
