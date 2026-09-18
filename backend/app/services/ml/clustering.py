"""
Phase 3 — Semantic Clustering Service
Reuses Phase 2 Qdrant embeddings (all-MiniLM-L6-v2, 384-dim) to cluster crime descriptions
by semantic similarity, without regenerating embeddings unnecessarily.

Algorithm:
  1. Retrieve vectors from Qdrant via scroll (batch, avoids full in-memory load)
  2. L2-normalize vectors for cosine equivalence
  3. Run DBSCAN (auto-cluster-count, handles noise)
  4. Fall back to K-Means if DBSCAN produces a single mega-cluster
  5. Persist CrimeCluster (type='semantic') + CrimeClusterMember records
"""
import logging
import math
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.models.ml_models import CrimeCluster, CrimeClusterMember
from app.services.qdrant_service import QdrantService
from app.core.config import settings

logger = logging.getLogger("connectdots_ml_clustering")


class SemanticClusteringService:
    """
    Groups crime incidents by semantic similarity of their descriptions.
    A cluster indicates similar language/phrasing — NOT proof of real-world criminal relationships.
    """

    @classmethod
    def run(cls, db: Session) -> Dict[str, Any]:
        """Main entry point: retrieve embeddings, cluster, persist."""
        vectors, crime_id_map = cls._load_vectors(db)

        if len(vectors) < 2:
            logger.info(f"Semantic clustering: insufficient data ({len(vectors)} vectors).")
            return {
                "status": "insufficient_data",
                "vector_count": len(vectors),
                "clusters_found": 0,
                "message": f"Only {len(vectors)} embedding vector(s) available. Need at least 2 for semantic clustering."
            }

        # L2-normalize for cosine similarity via Euclidean DBSCAN
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        norm_vectors = vectors / norms

        labels = cls._run_dbscan(norm_vectors)

        unique_labels = set(labels)
        cluster_labels = [lbl for lbl in unique_labels if lbl != -1]

        # If DBSCAN produces < 2 real clusters, fall back to K-Means
        if len(cluster_labels) < 2 and len(vectors) >= 4:
            logger.info("DBSCAN produced <2 clusters, falling back to K-Means with k=2.")
            labels = cls._run_kmeans(norm_vectors, k=min(2, len(vectors) // 2))
            unique_labels = set(labels)
            cluster_labels = [lbl for lbl in unique_labels if lbl != -1]

        noise_count = int(np.sum(np.array(labels) == -1))
        logger.info(f"Semantic clustering: {len(vectors)} vectors → {len(cluster_labels)} clusters, {noise_count} noise")

        # Delete previous semantic clusters
        old_clusters = db.query(CrimeCluster).filter(CrimeCluster.cluster_type == "semantic").all()
        for oc in old_clusters:
            db.delete(oc)
        db.flush()

        labels_array = np.array(labels)
        crime_ids_list = list(crime_id_map.keys())
        clusters_created = 0

        for lbl in cluster_labels:
            mask = labels_array == lbl
            member_indices = np.where(mask)[0]
            member_crime_ids = [crime_ids_list[i] for i in member_indices]

            # Centroid in embedding space
            centroid_vec = norm_vectors[mask].mean(axis=0)

            # Representative crimes: 3 closest to centroid
            dists = np.linalg.norm(norm_vectors[mask] - centroid_vec, axis=1)
            closest_indices = np.argsort(dists)[:3]
            representative_ids = [member_crime_ids[i] for i in closest_indices]

            # Fetch category info from DB
            cat_counts: Dict[str, int] = {}
            for cid in member_crime_ids:
                nlp = db.query(NlpAnalysis.predicted_category).filter(
                    NlpAnalysis.crime_id == cid,
                    NlpAnalysis.status == "COMPLETED"
                ).first()
                if nlp and nlp.predicted_category:
                    cat_counts[nlp.predicted_category] = cat_counts.get(nlp.predicted_category, 0) + 1
                else:
                    crime = db.query(Crime.category).filter(Crime.id == cid).first()
                    if crime:
                        cat_counts[crime.category] = cat_counts.get(crime.category, 0) + 1

            dominant_category = max(cat_counts, key=cat_counts.get) if cat_counts else "UNKNOWN"

            cluster = CrimeCluster(
                cluster_type="semantic",
                cluster_label=int(lbl),
                crime_count=len(member_crime_ids),
                centroid_lat=None,
                centroid_lon=None,
                metadata_={
                    "dominant_category": dominant_category,
                    "category_distribution": cat_counts,
                    "representative_crime_ids": representative_ids,
                    "eps": settings.ML_SEMANTIC_DBSCAN_EPS,
                    "algorithm": "dbscan_cosine" if len(cluster_labels) >= 2 else "kmeans_fallback",
                }
            )
            db.add(cluster)
            db.flush()

            for crime_id in member_crime_ids:
                db.add(CrimeClusterMember(cluster_id=cluster.id, crime_id=crime_id))

            clusters_created += 1

        db.commit()
        logger.info(f"Semantic clustering committed: {clusters_created} clusters.")

        return {
            "status": "completed",
            "vector_count": len(vectors),
            "clusters_found": clusters_created,
            "noise_points": noise_count,
        }

    @classmethod
    def _load_vectors(cls, db: Session) -> Tuple[np.ndarray, Dict[str, int]]:
        """
        Loads embedding vectors from Qdrant (via scroll) or regenerates from NLP analysis.
        Returns (vectors_array, {crime_id: index_in_array}).
        """
        vectors = []
        crime_id_map: Dict[str, int] = {}  # crime_id → index

        try:
            client = QdrantService.get_client()
            offset = None
            batch_size = 100

            while True:
                scroll_result = client.scroll(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    limit=batch_size,
                    offset=offset,
                    with_vectors=True,
                    with_payload=True,
                )
                points, next_offset = scroll_result

                for point in points:
                    if point.vector and point.payload and point.payload.get("crime_id"):
                        crime_id = point.payload["crime_id"]
                        crime_id_map[crime_id] = len(vectors)
                        vectors.append(point.vector)

                if next_offset is None:
                    break
                offset = next_offset

            if vectors:
                logger.info(f"Loaded {len(vectors)} vectors from Qdrant.")
                return np.array(vectors, dtype=float), crime_id_map

        except Exception as e:
            logger.warning(f"Qdrant scroll failed, will regenerate embeddings: {e}")

        # Fallback: regenerate from NLP analyses processed_text
        from app.services.embedding_service import EmbeddingService
        analyses = db.query(NlpAnalysis).filter(
            NlpAnalysis.status == "COMPLETED",
            NlpAnalysis.processed_text.isnot(None)
        ).all()

        for analysis in analyses:
            emb = EmbeddingService.generate_embedding(analysis.processed_text or "")
            crime_id_map[analysis.crime_id] = len(vectors)
            vectors.append(emb)

        logger.info(f"Regenerated {len(vectors)} embeddings from NLP analyses.")
        return np.array(vectors, dtype=float) if vectors else np.empty((0, 384)), crime_id_map

    @staticmethod
    def _run_dbscan(norm_vectors: np.ndarray) -> List[int]:
        from sklearn.cluster import DBSCAN
        model = DBSCAN(
            eps=settings.ML_SEMANTIC_DBSCAN_EPS,
            min_samples=max(2, len(norm_vectors) // 5),
            metric="euclidean",  # Euclidean on L2-normalized = cosine distance
        )
        return list(model.fit_predict(norm_vectors))

    @staticmethod
    def _run_kmeans(norm_vectors: np.ndarray, k: int) -> List[int]:
        from sklearn.cluster import KMeans
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        return list(model.fit_predict(norm_vectors))
