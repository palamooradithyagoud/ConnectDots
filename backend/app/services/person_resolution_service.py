"""
Phase 5: Conservative Person Identity Resolution Service
Implements safe entity deduplication, name normalization, and provenance tracking.
Strict Non-Assumption Principle: Disconnected or ambiguous individuals are NEVER
merged without explicit evidence.
"""
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.person import Person, CrimePersonAssociation
from app.models.telecom import PersonPhoneAssociation, PhoneNumber

logger = logging.getLogger("connectdots_person_resolution")


class PersonResolutionService:
    """
    Handles canonicalization, conservative identity resolution, and database persistence
    for Person entities.
    """

    HONORIFICS_PATTERN = re.compile(
        r"^(?:mr\.?|mrs\.?|ms\.?|dr\.?|shri|smt\.?|mohd\.?|md\.?|adv\.?|capt\.?|constable|inspector|sub-inspector|late|s/o|w/o|d/o)\s+",
        re.IGNORECASE
    )

    @classmethod
    def normalize_name(cls, raw_name: str) -> str:
        """
        Cleans and normalizes a person's display name:
        1. Strips leading honorifics / titles
        2. Normalizes internal whitespace
        3. Title-cases name parts
        """
        if not raw_name:
            return ""
        name = raw_name.strip()
        name = cls.HONORIFICS_PATTERN.sub("", name).strip()
        # Collapse multiple spaces
        name = re.sub(r"\s+", " ", name)
        # Title case tokens while preserving initials
        tokens = [t.capitalize() if len(t) > 1 else t.upper() for t in name.split()]
        return " ".join(tokens)

    @classmethod
    def generate_person_id(cls, canonical_name: str, discriminator: Optional[str] = None) -> str:
        """
        Generates a stable, deterministic internal ID for a person.
        e.g. 'person:vikram_singh' or 'person:vikram_singh_a1b2' if discriminator provided.
        """
        norm = cls.normalize_name(canonical_name).lower()
        slug = re.sub(r"[^a-z0-9]+", "_", norm).strip("_")
        if not slug:
            slug = "unknown_person"

        if discriminator:
            disc_hash = hashlib.sha256(discriminator.encode("utf-8")).hexdigest()[:6]
            return f"person:{slug}_{disc_hash}"
        return f"person:{slug}"

    @classmethod
    def resolve_or_create_person(
        cls,
        db: Session,
        name: str = "",
        raw_name: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        source_provenance: str = "FIR_NARRATIVE",
        confidence: float = 1.0,
        discriminator: Optional[str] = None
    ) -> Person:
        """
        Conservatively resolves or persists a Person entity in PostgreSQL.
        Prevents aggressive identity merges.
        """
        target_name = raw_name if raw_name is not None else name
        canonical = cls.normalize_name(target_name)
        if not canonical:
            canonical = "Unknown Individual"

        normalized = canonical.lower()
        clean_aliases = [cls.normalize_name(a) for a in (aliases or []) if a.strip()]

        # 1. Exact match on canonical_name
        existing = db.query(Person).filter(Person.normalized_name == normalized).first()
        if existing:
            # Safely merge aliases
            current_aliases = set(existing.aliases or [])
            current_aliases.update(clean_aliases)
            existing.aliases = list(current_aliases)
            return existing

        # 2. Check if this candidate name is an explicit alias of an existing person
        # (Only if name is distinct and non-generic)
        if len(normalized.split()) >= 2:
            all_persons = db.query(Person).all()
            for p in all_persons:
                p_aliases = [cls.normalize_name(a).lower() for a in (p.aliases or [])]
                if normalized in p_aliases:
                    return p

        # 3. If not resolvable, create new Person with stable ID
        person_id = cls.generate_person_id(canonical, discriminator=discriminator)
        # Ensure unique ID
        counter = 1
        base_id = person_id
        while db.query(Person).filter(Person.id == person_id).first():
            person_id = f"{base_id}_{counter}"
            counter += 1

        new_person = Person(
            id=person_id,
            canonical_name=canonical,
            normalized_name=normalized,
            aliases=clean_aliases,
            source_provenance=source_provenance,
            confidence=confidence,
            metadata_json={"resolved_by": "conservative_heuristic"}
        )
        db.add(new_person)
        db.flush()
        logger.info(f"Created new Person record: {new_person.id} ({new_person.canonical_name})")
        return new_person

    @classmethod
    def link_person_to_crime(
        cls,
        db: Session,
        crime_id: str,
        person_id: str,
        role: str = "PERSON_OF_INTEREST",
        relationship_type: str = "MENTIONED_IN",
        confidence: float = 0.9,
        extraction_confidence: Optional[float] = None,
        evidence_excerpt: Optional[str] = None
    ) -> CrimePersonAssociation:
        """
        Creates or updates a grounded association between a Crime and a Person.
        """
        conf = confidence if extraction_confidence is None else extraction_confidence
        existing = db.query(CrimePersonAssociation).filter(
            CrimePersonAssociation.crime_id == crime_id,
            CrimePersonAssociation.person_id == person_id
        ).first()

        if existing:
            if role and existing.role != role:
                existing.role = role
            if evidence_excerpt and not existing.evidence_excerpt:
                existing.evidence_excerpt = evidence_excerpt
            if conf:
                existing.confidence = conf
            return existing

        assoc = CrimePersonAssociation(
            crime_id=crime_id,
            person_id=person_id,
            role=role,
            relationship_type=relationship_type,
            confidence=conf,
            evidence_excerpt=evidence_excerpt
        )
        db.add(assoc)
        db.flush()
        return assoc

    @classmethod
    def associate_crime_person(
        cls,
        db: Session,
        crime_id: str,
        raw_name: Optional[str] = None,
        name: Optional[str] = None,
        role: str = "PERSON_OF_INTEREST",
        excerpt: Optional[str] = None,
        evidence_excerpt: Optional[str] = None,
        confidence: float = 0.9,
        relationship_type: str = "MENTIONED_IN"
    ) -> CrimePersonAssociation:
        """
        Resolves or creates a Person entity and binds them with grounded excerpt to a Crime.
        """
        target_name = raw_name if raw_name is not None else (name or "")
        person = cls.resolve_or_create_person(
            db=db,
            name=target_name,
            source_provenance="FIR_NARRATIVE",
            confidence=confidence
        )
        target_excerpt = excerpt if excerpt is not None else evidence_excerpt
        return cls.link_person_to_crime(
            db=db,
            crime_id=crime_id,
            person_id=person.id,
            role=role,
            relationship_type=relationship_type,
            confidence=confidence,
            evidence_excerpt=target_excerpt
        )

    @classmethod
    def link_person_to_phone(
        cls,
        db: Session,
        person_id: str,
        phone_id: str,
        person_name: str,
        crime_id: Optional[str] = None,
        role: str = "SUSPECT",
        confidence: float = 0.8,
        confidence_type: str = "derived",
        source: Optional[str] = None
    ) -> PersonPhoneAssociation:
        """
        Creates or updates an association between a Person and a Phone Number.
        """
        existing = db.query(PersonPhoneAssociation).filter(
            PersonPhoneAssociation.phone_id == phone_id,
            (PersonPhoneAssociation.person_id == person_id) | (PersonPhoneAssociation.person_name == person_name)
        ).first()

        if existing:
            if not existing.person_id:
                existing.person_id = person_id
            return existing

        assoc = PersonPhoneAssociation(
            person_id=person_id,
            person_name=person_name,
            phone_id=phone_id,
            crime_id=crime_id,
            role=role,
            confidence=confidence,
            confidence_type=confidence_type,
            source=source
        )
        db.add(assoc)
        db.flush()
        return assoc
