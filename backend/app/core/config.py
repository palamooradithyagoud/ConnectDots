from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ConnectDots - AI Crime Analysis System"
    VERSION: str = "4.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:CHANGE_ME@localhost:5432/crime_db"
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Ingestion Constraints
    MAX_UPLOAD_SIZE_MB: int = 50
    BATCH_SIZE: int = 1000

    # Phase 2: NLP & Qdrant Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    QDRANT_URL: Union[str, None] = None
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Union[str, None] = None
    QDRANT_COLLECTION_NAME: str = "connectdots_crimes"
    QDRANT_STORAGE_PATH: str = "./qdrant_storage"
    NLP_CONFIDENCE_THRESHOLD: float = 0.60
    NLP_BATCH_SIZE: int = 50

    # Phase 3: ML & Crime Pattern Analysis
    ML_DBSCAN_EPS_KM: float = 1.0            # Spatial DBSCAN epsilon in kilometres
    ML_DBSCAN_MIN_SAMPLES: int = 2           # Minimum cluster size (lowered for small datasets)
    ML_SEMANTIC_DBSCAN_EPS: float = 0.5     # Semantic clustering epsilon (cosine-normalized)
    ML_ANOMALY_CONTAMINATION: float = 0.15  # Isolation Forest contamination rate
    ML_ROLLING_WINDOW_WEEKS: int = 4        # Rolling average window in periods

    # Phase 4: Knowledge Graph (Neo4j Aura) & LLM Investigation Intelligence
    # Set these in your .env file — do NOT hardcode real credentials here.
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_USERNAME: Union[str, None] = None
    NEO4J_PASSWORD: str = "CHANGE_ME"
    NEO4J_DATABASE: str = "neo4j"
    AURA_INSTANCEID: Union[str, None] = None
    AURA_INSTANCENAME: Union[str, None] = None

    @field_validator("NEO4J_USER", mode="after")
    @classmethod
    def resolve_neo4j_user(cls, v: str) -> str:
        return v

    def model_post_init(self, __context):
        if self.NEO4J_USERNAME and (not self.NEO4J_USER or self.NEO4J_USER == "neo4j"):
            self.NEO4J_USER = self.NEO4J_USERNAME

    # LLM Provider Abstraction
    LLM_PROVIDER: str = "groq"              # "groq" | "openai" | "mock"
    LLM_MODEL: str = "openai/gpt-oss-120b"
    LLM_API_KEY: Union[str, None] = None
    GROQ_API_KEY: Union[str, None] = None
    LLM_BASE_URL: Union[str, None] = None
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1500

    # Graph RAG & Investigation
    GRAPH_TRAVERSAL_MAX_DEPTH: int = 2
    GRAPH_RAG_TOP_K_SEMANTIC: int = 5
    GRAPH_RAG_SIMILARITY_THRESHOLD: float = 0.60
    GRAPH_AUTO_SYNC_ON_STARTUP: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
