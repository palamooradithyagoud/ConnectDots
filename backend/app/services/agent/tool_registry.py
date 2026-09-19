"""
Phase 7: Domain AI Investigation Agent — Tool Registry & Contracts
Defines the strict allowlist of approved investigation tools with input validation,
bounds clamping, timeout policies, and permissions.
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field, ValidationError

from app.services.agent.models import ToolDefinition

logger = logging.getLogger("connectdots_tool_registry")


# -----------------------------------------------------------------------------
# Tool Input Schemas
# -----------------------------------------------------------------------------

class CrimeSearchInput(BaseModel):
    query: Optional[str] = Field(default=None, max_length=200)
    category: Optional[str] = Field(default=None, max_length=100)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=50)


class CrimeDetailInput(BaseModel):
    crime_id: str = Field(min_length=1, max_length=100)


class SemanticSearchInput(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class GraphConnectionsInput(BaseModel):
    crime_id: str = Field(min_length=1, max_length=100)
    max_hops: int = Field(default=2, ge=1, le=3)
    limit: int = Field(default=20, ge=1, le=50)


class GraphPathsInput(BaseModel):
    source_id: str = Field(min_length=1, max_length=100)
    target_id: str = Field(min_length=1, max_length=100)
    max_depth: int = Field(default=3, ge=1, le=4)


class PhoneLookupInput(BaseModel):
    phone_number: str = Field(min_length=5, max_length=30)


class PhoneConnectionsInput(BaseModel):
    phone_number: Optional[str] = Field(default=None, max_length=30)
    crime_id: Optional[str] = Field(default=None, max_length=100)
    person_id: Optional[str] = Field(default=None, max_length=100)
    limit: int = Field(default=30, ge=1, le=50)


class CdrAnalysisInput(BaseModel):
    phone_number: str = Field(min_length=5, max_length=30)
    days_window: int = Field(default=30, ge=1, le=90)
    limit: int = Field(default=50, ge=1, le=100)


class CrossCaseAnalysisInput(BaseModel):
    crime_id: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    limit: int = Field(default=20, ge=1, le=50)


class KeyIndividualAnalysisInput(BaseModel):
    scope_crime_id: Optional[str] = Field(default=None, max_length=100)
    limit: int = Field(default=10, ge=1, le=30)


class NetworkSubgraphInput(BaseModel):
    crime_id: str = Field(min_length=1, max_length=100)
    depth: int = Field(default=2, ge=1, le=3)
    max_nodes: int = Field(default=50, ge=5, le=50)


class PatternAnalysisInput(BaseModel):
    crime_id: Optional[str] = Field(default=None, max_length=100)
    pattern_type: Optional[str] = Field(default=None, max_length=50)
    limit: int = Field(default=10, ge=1, le=30)


class AnomalyAnalysisInput(BaseModel):
    crime_id: Optional[str] = Field(default=None, max_length=100)
    anomaly_type: Optional[str] = Field(default=None, max_length=50)
    limit: int = Field(default=10, ge=1, le=30)


class ClusterAnalysisInput(BaseModel):
    crime_id: Optional[str] = Field(default=None, max_length=100)
    cluster_type: Optional[str] = Field(default=None, max_length=50)
    limit: int = Field(default=10, ge=1, le=30)


class EvidenceLookupInput(BaseModel):
    crime_id: Optional[str] = Field(default=None, max_length=100)
    person_id: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    limit: int = Field(default=20, ge=1, le=50)


class ReviewStatusInput(BaseModel):
    relationship_ref: Optional[str] = Field(default=None, max_length=200)
    status: Optional[str] = Field(default=None, max_length=50)
    crime_id: Optional[str] = Field(default=None, max_length=100)
    limit: int = Field(default=20, ge=1, le=50)


# -----------------------------------------------------------------------------
# Registry Mapping
# -----------------------------------------------------------------------------

TOOL_INPUT_MODELS: Dict[str, type[BaseModel]] = {
    "crime_search": CrimeSearchInput,
    "crime_detail": CrimeDetailInput,
    "semantic_search": SemanticSearchInput,
    "graph_connections": GraphConnectionsInput,
    "graph_paths": GraphPathsInput,
    "phone_lookup": PhoneLookupInput,
    "phone_connections": PhoneConnectionsInput,
    "cdr_analysis": CdrAnalysisInput,
    "cross_case_analysis": CrossCaseAnalysisInput,
    "key_individual_analysis": KeyIndividualAnalysisInput,
    "network_subgraph": NetworkSubgraphInput,
    "pattern_analysis": PatternAnalysisInput,
    "anomaly_analysis": AnomalyAnalysisInput,
    "cluster_analysis": ClusterAnalysisInput,
    "evidence_lookup": EvidenceLookupInput,
    "review_status": ReviewStatusInput,
}


class ToolRegistry:
    """
    Central repository of verified domain investigation tools.
    Enforces strict read-only bounds and parameter sanitization.
    """

    _registry: Dict[str, ToolDefinition] = {
        "crime_search": ToolDefinition(
            name="crime_search",
            description="Search crime records by keywords, category, or date range in PostgreSQL.",
            input_schema=CrimeSearchInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"crimes": {"type": "array"}}},
            timeout_seconds=5.0,
            max_results=50,
        ),
        "crime_detail": ToolDefinition(
            name="crime_detail",
            description="Retrieve detailed crime incident record including narrative, location, and extracted entities.",
            input_schema=CrimeDetailInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"crime": {"type": "object"}}},
            timeout_seconds=5.0,
            max_results=1,
        ),
        "semantic_search": ToolDefinition(
            name="semantic_search",
            description="Perform vector similarity search in Qdrant against crime descriptions and Modus Operandi.",
            input_schema=SemanticSearchInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"matches": {"type": "array"}}},
            timeout_seconds=8.0,
            max_results=50,
        ),
        "graph_connections": ToolDefinition(
            name="graph_connections",
            description="Explore connected crimes, shared suspects, and co-occurrences via Neo4j knowledge graph.",
            input_schema=GraphConnectionsInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"connections": {"type": "array"}}},
            timeout_seconds=8.0,
            max_results=50,
        ),
        "graph_paths": ToolDefinition(
            name="graph_paths",
            description="Find shortest path and connection chain between two entities in the knowledge graph.",
            input_schema=GraphPathsInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"paths": {"type": "array"}}},
            timeout_seconds=8.0,
            max_results=10,
        ),
        "phone_lookup": ToolDefinition(
            name="phone_lookup",
            description="Lookup telephone number intelligence, subscriber attribution, and carrier metadata.",
            input_schema=PhoneLookupInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"phone": {"type": "object"}}},
            timeout_seconds=5.0,
            max_results=1,
        ),
        "phone_connections": ToolDefinition(
            name="phone_connections",
            description="Retrieve phone linkages across multiple cases, suspects, and CDR records.",
            input_schema=PhoneConnectionsInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"associations": {"type": "array"}}},
            timeout_seconds=5.0,
            max_results=50,
        ),
        "cdr_analysis": ToolDefinition(
            name="cdr_analysis",
            description="Retrieve Call Detail Record (CDR) statistics, top contacts, and call activity.",
            input_schema=CdrAnalysisInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"cdr_stats": {"type": "object"}}},
            timeout_seconds=8.0,
            max_results=100,
        ),
        "cross_case_analysis": ToolDefinition(
            name="cross_case_analysis",
            description="Identify cross-jurisdictional crime linkages via shared phones, vehicles, or suspects.",
            input_schema=CrossCaseAnalysisInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"linkages": {"type": "array"}}},
            timeout_seconds=8.0,
            max_results=50,
        ),
        "key_individual_analysis": ToolDefinition(
            name="key_individual_analysis",
            description="Retrieve structurally central individuals ranked by Degree, Betweenness, and PageRank.",
            input_schema=KeyIndividualAnalysisInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"key_individuals": {"type": "array"}}},
            timeout_seconds=10.0,
            max_results=30,
        ),
        "network_subgraph": ToolDefinition(
            name="network_subgraph",
            description="Retrieve the 1-2 hop neighborhood graph around a crime or entity for visualization.",
            input_schema=NetworkSubgraphInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"nodes": {"type": "array"}, "edges": {"type": "array"}}},
            timeout_seconds=8.0,
            max_results=50,
        ),
        "pattern_analysis": ToolDefinition(
            name="pattern_analysis",
            description="Retrieve ML-discovered crime patterns (spatial-temporal, modus operandi series).",
            input_schema=PatternAnalysisInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"patterns": {"type": "array"}}},
            timeout_seconds=5.0,
            max_results=30,
        ),
        "anomaly_analysis": ToolDefinition(
            name="anomaly_analysis",
            description="Retrieve statistical and temporal crime anomalies flagged by Isolation Forest.",
            input_schema=AnomalyAnalysisInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"anomalies": {"type": "array"}}},
            timeout_seconds=5.0,
            max_results=30,
        ),
        "cluster_analysis": ToolDefinition(
            name="cluster_analysis",
            description="Retrieve spatial (DBSCAN) or semantic incident clusters from database.",
            input_schema=ClusterAnalysisInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"clusters": {"type": "array"}}},
            timeout_seconds=5.0,
            max_results=30,
        ),
        "evidence_lookup": ToolDefinition(
            name="evidence_lookup",
            description="Retrieve ground truth narrative excerpts, extracted entities, and primary source records.",
            input_schema=EvidenceLookupInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"evidence_records": {"type": "array"}}},
            timeout_seconds=5.0,
            max_results=50,
        ),
        "review_status": ToolDefinition(
            name="review_status",
            description="Query investigator validation status (VALIDATED, UNDER_REVIEW, REJECTED) for relationships.",
            input_schema=ReviewStatusInput.model_json_schema(),
            output_schema={"type": "object", "properties": {"reviews": {"type": "array"}}},
            timeout_seconds=5.0,
            max_results=50,
        ),
    }

    @classmethod
    def is_tool_allowed(cls, tool_name: str) -> bool:
        """Checks if tool exists in the allowlist."""
        return tool_name.strip().lower() in cls._registry

    @classmethod
    def get_tool_definition(cls, tool_name: str) -> Optional[ToolDefinition]:
        """Retrieves tool definition metadata."""
        return cls._registry.get(tool_name.strip().lower())

    @classmethod
    def list_tools(cls) -> List[ToolDefinition]:
        """Returns all registered tool definitions."""
        return list(cls._registry.values())

    @classmethod
    def validate_tool_arguments(cls, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates arguments against the tool's Pydantic schema.
        Raises ValueError if tool is unknown or arguments violate schema.
        """
        clean_name = tool_name.strip().lower()
        if clean_name not in cls._registry:
            raise ValueError(f"Unknown or unauthorized tool '{tool_name}'. Allowed tools: {sorted(list(cls._registry.keys()))}")

        model_cls = TOOL_INPUT_MODELS.get(clean_name)
        if not model_cls:
            return arguments

        try:
            validated = model_cls(**arguments)
            return validated.model_dump(exclude_none=True)
        except ValidationError as e:
            raise ValueError(f"Invalid arguments for tool '{clean_name}': {e.errors()}")
