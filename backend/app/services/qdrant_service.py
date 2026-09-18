import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.core.config import settings

logger = logging.getLogger("connectdots_qdrant")


class QdrantService:
    """
    Manages vector indexing, collection lifecycle, and similarity searches in Qdrant.
    Features resilient connection fallback to ensure zero API crashes if Qdrant daemon is warming up.
    """

    _client_instance: Optional[QdrantClient] = None
    _collection_initialized: bool = False

    @classmethod
    def get_client(cls) -> QdrantClient:
        """Returns active Qdrant client singleton, initializing connection if needed."""
        if cls._client_instance is not None:
            return cls._client_instance

        # 1. Try URL connection if configured
        if settings.QDRANT_URL:
            try:
                logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
                cls._client_instance = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=5.0
                )
                cls._client_instance.get_collections()
                logger.info("Connected to remote Qdrant successfully.")
                cls._ensure_collection()
                return cls._client_instance
            except Exception as e:
                logger.warning(f"Could not connect to QDRANT_URL ({settings.QDRANT_URL}): {e}")

        # 2. Try default localhost:6333
        try:
            target_host = settings.QDRANT_HOST
            target_port = settings.QDRANT_PORT
            logger.info(f"Attempting connection to Qdrant at {target_host}:{target_port}...")
            client = QdrantClient(host=target_host, port=target_port, timeout=3.0)
            client.get_collections()
            cls._client_instance = client
            logger.info(f"Connected to Qdrant at {target_host}:{target_port} successfully.")
            cls._ensure_collection()
            return cls._client_instance
        except Exception as e:
            logger.warning(f"Local Qdrant daemon at {settings.QDRANT_HOST}:{settings.QDRANT_PORT} unavailable: {e}")

        # 3. Fallback to resilient in-memory embedded vector store for local testing/dev
        logger.info("Falling back to local in-memory Qdrant instance for seamless continuity.")
        cls._client_instance = QdrantClient(location=":memory:")
        cls._ensure_collection()
        return cls._client_instance

    @classmethod
    def _ensure_collection(cls):
        """Ensures the crime vector collection exists with appropriate dimensions."""
        if cls._client_instance is None:
            return

        collection_name = settings.QDRANT_COLLECTION_NAME
        try:
            collections = cls._client_instance.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            if not exists:
                logger.info(f"Creating Qdrant collection '{collection_name}' (dim={settings.EMBEDDING_DIMENSION})...")
                cls._client_instance.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{collection_name}' created successfully.")
            cls._collection_initialized = True
        except Exception as e:
            logger.error(f"Error checking/creating Qdrant collection: {e}")

    @classmethod
    def upsert_crime_vector(
        cls,
        crime_id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> str:
        """
        Idempotently upserts a crime vector and its metadata payload into Qdrant.
        Returns point_id (deterministic UUID based on crime_id).
        """
        client = cls.get_client()
        cls._ensure_collection()

        # Generate deterministic UUID for idempotency
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"connectdots-crime-{crime_id}"))

        point = PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "crime_id": crime_id,
                "record_id": payload.get("record_id"),
                "category": payload.get("category"),
                "location": payload.get("location"),
                "occurred_at": str(payload.get("occurred_at")),
                "source": payload.get("source"),
            }
        )

        client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[point]
        )
        return point_id

    @classmethod
    def search_similar_crimes(
        cls,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.50,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches Qdrant for crime vectors semantically closest to query_vector.
        Returns matched point IDs, similarity scores, and payloads.
        """
        client = cls.get_client()
        cls._ensure_collection()

        # Optional metadata filter
        query_filter = None
        if category:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category.upper())
                    )
                ]
            )

        # Qdrant client query_points method
        try:
            results = client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            ).points
        except AttributeError:
            # Fallback for older client search API
            results = client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            )

        formatted_results = []
        for res in results:
            formatted_results.append({
                "point_id": str(res.id),
                "score": float(res.score),
                "payload": res.payload or {}
            })

        return formatted_results

    @classmethod
    def count_indexed_vectors(cls) -> int:
        """Returns the number of vectors stored in the Qdrant collection."""
        try:
            client = cls.get_client()
            col = client.get_collection(settings.QDRANT_COLLECTION_NAME)
            return col.points_count or 0
        except Exception as e:
            logger.debug(f"Could not read vector count from Qdrant: {e}")
            return 0
