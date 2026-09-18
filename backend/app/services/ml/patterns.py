"""
Phase 3 — Pattern Analysis Service
Discovers multi-dimensional crime patterns by cross-joining:
  - Spatial clusters (which crimes cluster geographically?)
  - Temporal windows (when do those cluster members occur?)
  - Crime categories (what type?)
  - Modus Operandi (how were crimes committed?)

Every discovered pattern maintains mandatory evidence (crime IDs) for Phase 4 Neo4j graph construction.
"""
import logging
from collections import defaultdict
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from app.models.crime import Crime
from app.models.nlp_analysis import NlpAnalysis
from app.models.ml_models import CrimeCluster, CrimeClusterMember, CrimePattern

logger = logging.getLogger("connectdots_ml_patterns")


class PatternAnalysisService:
    """
    Synthesizes multi-signal crime patterns. Patterns are observational analyses
    of the available data — not predictions about future crimes or specific individuals.
    """

    @classmethod
    def run(cls, db: Session) -> Dict[str, Any]:
        """Main entry point — generates all pattern types."""
        # Remove previous patterns
        db.query(CrimePattern).delete()
        db.flush()

        patterns_created = 0
        patterns_created += cls._spatial_temporal_patterns(db)
        patterns_created += cls._semantic_mo_patterns(db)
        patterns_created += cls._category_concentration_patterns(db)

        db.commit()
        logger.info(f"Pattern analysis committed: {patterns_created} patterns.")
        return {
            "status": "completed",
            "patterns_found": patterns_created,
        }

    @classmethod
    def _spatial_temporal_patterns(cls, db: Session) -> int:
        """
        Identifies spatial clusters where crimes concentrate in specific time windows.
        Pattern: cluster C has N crimes, M% occurring between hours X-Y.
        """
        spatial_clusters = db.query(CrimeCluster).filter(
            CrimeCluster.cluster_type == "spatial",
            CrimeCluster.crime_count >= 2,
        ).all()

        patterns_created = 0
        for cluster in spatial_clusters:
            # Get member crimes with occurred_at
            member_rows = db.query(
                Crime.id,
                Crime.record_id,
                Crime.category,
                Crime.occurred_at,
            ).join(
                CrimeClusterMember, Crime.id == CrimeClusterMember.crime_id
            ).filter(
                CrimeClusterMember.cluster_id == cluster.id,
                Crime.occurred_at.isnot(None),
            ).all()

            if len(member_rows) < 2:
                continue

            # Time-window bucketing (6-hour buckets: night/morning/afternoon/evening)
            time_buckets: Dict[str, List[str]] = defaultdict(list)
            for crime in member_rows:
                hour = crime.occurred_at.hour
                if 0 <= hour < 6:
                    bucket = "00:00-06:00 (Night)"
                elif 6 <= hour < 12:
                    bucket = "06:00-12:00 (Morning)"
                elif 12 <= hour < 18:
                    bucket = "12:00-18:00 (Afternoon)"
                else:
                    bucket = "18:00-00:00 (Evening)"
                time_buckets[bucket].append(crime.id)

            # Find dominant time window (at least 50% of crimes)
            total = len(member_rows)
            for time_window, crime_ids in time_buckets.items():
                ratio = len(crime_ids) / total
                if ratio >= 0.5 and len(crime_ids) >= 2:
                    meta = cluster.metadata_ or {}
                    dominant_category = meta.get("dominant_category", "UNKNOWN")
                    confidence = round(ratio, 4)

                    description = (
                        f"{len(crime_ids)} out of {total} incidents in Spatial Cluster #{cluster.cluster_label} "
                        f"occurred during {time_window}. "
                        f"Primary crime category: {dominant_category}. "
                        f"This temporal concentration pattern was detected across {len(crime_ids)} crime records."
                    )

                    pattern = CrimePattern(
                        pattern_type="spatial_temporal",
                        category=dominant_category,
                        description=description,
                        confidence=confidence,
                        evidence=crime_ids,
                        metadata_={
                            "location_cluster_id": cluster.id,
                            "cluster_label": cluster.cluster_label,
                            "time_window": time_window,
                            "incident_count": len(crime_ids),
                            "total_cluster_size": total,
                            "centroid_lat": cluster.centroid_lat,
                            "centroid_lon": cluster.centroid_lon,
                        }
                    )
                    db.add(pattern)
                    patterns_created += 1
                    break  # One pattern per cluster

        db.flush()
        return patterns_created

    @classmethod
    def _semantic_mo_patterns(cls, db: Session) -> int:
        """
        Identifies recurring Modus Operandi patterns within semantic clusters.
        Pattern: semantic cluster S has crimes sharing M.O. pattern X.
        """
        semantic_clusters = db.query(CrimeCluster).filter(
            CrimeCluster.cluster_type == "semantic",
            CrimeCluster.crime_count >= 2,
        ).all()

        patterns_created = 0
        for cluster in semantic_clusters:
            member_crime_ids = [
                m.crime_id for m in db.query(CrimeClusterMember.crime_id).filter(
                    CrimeClusterMember.cluster_id == cluster.id
                ).all()
            ]

            if len(member_crime_ids) < 2:
                continue

            # Collect M.O. patterns from NLP analyses
            mo_counts: Dict[str, List[str]] = defaultdict(list)  # pattern → [crime_id]
            for crime_id in member_crime_ids:
                nlp = db.query(NlpAnalysis).filter(
                    NlpAnalysis.crime_id == crime_id,
                    NlpAnalysis.status == "COMPLETED",
                ).first()
                if nlp and nlp.modus_operandi:
                    for mo in nlp.modus_operandi:
                        if isinstance(mo, dict):
                            pattern_name = mo.get("pattern", "")
                            if pattern_name:
                                mo_counts[pattern_name].append(crime_id)

            for mo_pattern, crime_ids in mo_counts.items():
                if len(crime_ids) >= 2:
                    meta = cluster.metadata_ or {}
                    dominant_category = meta.get("dominant_category", "UNKNOWN")
                    confidence = round(len(crime_ids) / len(member_crime_ids), 4)

                    description = (
                        f"Modus Operandi pattern '{mo_pattern}' was identified in {len(crime_ids)} out of "
                        f"{len(member_crime_ids)} semantically similar crime descriptions. "
                        f"This M.O. recurrence was detected within Semantic Cluster #{cluster.cluster_label} "
                        f"(dominant category: {dominant_category}). "
                        f"Note: M.O. similarity indicates similar methods in the analyzed data — "
                        f"it does not imply a shared perpetrator."
                    )

                    pattern = CrimePattern(
                        pattern_type="semantic_mo",
                        category=dominant_category,
                        description=description,
                        confidence=confidence,
                        evidence=crime_ids,
                        metadata_={
                            "semantic_cluster_id": cluster.id,
                            "cluster_label": cluster.cluster_label,
                            "mo_pattern": mo_pattern,
                            "occurrence_count": len(crime_ids),
                            "cluster_size": len(member_crime_ids),
                        }
                    )
                    db.add(pattern)
                    patterns_created += 1

        db.flush()
        return patterns_created

    @classmethod
    def _category_concentration_patterns(cls, db: Session) -> int:
        """
        Identifies categories that are significantly more concentrated in specific locations.
        Pattern: category X has N crimes concentrated in location cluster Y.
        """
        spatial_clusters = db.query(CrimeCluster).filter(
            CrimeCluster.cluster_type == "spatial",
            CrimeCluster.crime_count >= 3,
        ).all()

        patterns_created = 0
        for cluster in spatial_clusters:
            meta = cluster.metadata_ or {}
            cat_dist = meta.get("category_distribution", {})

            if not cat_dist:
                continue

            total = sum(cat_dist.values())
            for category, count in cat_dist.items():
                ratio = count / total if total > 0 else 0
                if ratio >= 0.6 and count >= 2:
                    # Fetch crime IDs for this category in this cluster
                    crime_ids = [
                        m.crime_id for m in db.query(CrimeClusterMember).filter(
                            CrimeClusterMember.cluster_id == cluster.id
                        ).all()
                    ]

                    # Filter to this category
                    cat_crimes = db.query(Crime.id).filter(
                        Crime.id.in_(crime_ids),
                        Crime.category == category,
                    ).all()
                    cat_crime_ids = [c.id for c in cat_crimes]

                    if len(cat_crime_ids) < 2:
                        continue

                    confidence = round(ratio, 4)
                    description = (
                        f"{count} out of {total} crimes in Spatial Cluster #{cluster.cluster_label} "
                        f"({ratio*100:.0f}%) are categorized as {category}. "
                        f"This geographic concentration of a single crime category was detected "
                        f"across {count} crime records in the cluster area."
                    )

                    pattern = CrimePattern(
                        pattern_type="category_concentration",
                        category=category,
                        description=description,
                        confidence=confidence,
                        evidence=cat_crime_ids,
                        metadata_={
                            "cluster_id": cluster.id,
                            "cluster_label": cluster.cluster_label,
                            "category_ratio": ratio,
                            "category_count": count,
                            "total_cluster_count": total,
                            "centroid_lat": cluster.centroid_lat,
                            "centroid_lon": cluster.centroid_lon,
                        }
                    )
                    db.add(pattern)
                    patterns_created += 1

        db.flush()
        return patterns_created
