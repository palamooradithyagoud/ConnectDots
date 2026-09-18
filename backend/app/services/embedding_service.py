import logging
from typing import List, Optional
import numpy as np
from app.core.config import settings

logger = logging.getLogger("connectdots_embeddings")


class EmbeddingService:
    """
    Dedicated Sentence Transformers embedding service.
    Reuses a cached singleton model instance to maximize inference performance.
    Configurable via EMBEDDING_MODEL environment setting.
    """

    _model_instance = None
    _model_name: Optional[str] = None

    @classmethod
    def get_model(cls):
        """Lazy-loads and caches the SentenceTransformer model."""
        target_model = settings.EMBEDDING_MODEL

        if cls._model_instance is None or cls._model_name != target_model:
            logger.info(f"Loading SentenceTransformer embedding model: {target_model}")
            try:
                from sentence_transformers import SentenceTransformer
                cls._model_instance = SentenceTransformer(target_model)
                cls._model_name = target_model
                logger.info(f"Embedding model '{target_model}' loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer model '{target_model}': {e}")
                raise RuntimeError(f"Embedding model initialization failed: {e}")

        return cls._model_instance

    @classmethod
    def generate_embedding(cls, text: Optional[str]) -> List[float]:
        """
        Generates a normalized float vector embedding for input text.
        Handles empty/null strings safely.
        """
        if not text or not text.strip():
            # Return zero vector of appropriate dimension for empty text
            return [0.0] * settings.EMBEDDING_DIMENSION

        model = cls.get_model()
        # normalize_embeddings=True ensures cosine similarity is directly dot product
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    @classmethod
    def generate_batch_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """
        Generates normalized embeddings for a list of texts in a single forward pass.
        """
        if not texts:
            return []

        # Replace empty items with single space so tokenizer doesn't error
        processed_texts = [t if (t and t.strip()) else " " for t in texts]

        model = cls.get_model()
        embeddings = model.encode(processed_texts, batch_size=32, normalize_embeddings=True)
        return embeddings.tolist()
