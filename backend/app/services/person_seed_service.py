"""
Phase 5: Person & Network Seeding Service
Populates grounded Person entities, Crime-Person associations, and Person-Phone links
for existing database crimes to enable live network analysis and knowledge graph verification.
"""
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.crime import Crime
from app.models.telecom import PhoneNumber
from app.services.person_resolution_service import PersonResolutionService

logger = logging.getLogger("connectdots_person_seed")


class PersonSeedService:
    """
    Seeds initial realistic person investigation entities linked to existing FIR crimes.
    """

    @classmethod
    def seed_initial_network(cls, db: Session) -> Dict[str, Any]:
        """
        Idempotently seeds key individuals and associations for existing crimes.
        """
        crimes = db.query(Crime).all()
        if not crimes:
            return {"status": "skipped", "reason": "No crimes in database"}

        crime_by_rec = {c.record_id: c for c in crimes}

        # 1. Individuals to register
        people_specs = [
            {
                "name": "Vikram Singh",
                "aliases": ["Vicky", "Vikram S."],
                "provenance": "FIR_NARRATIVE",
                "confidence": 0.95,
                "cases": [
                    {"record_id": "CR-2026-001", "role": "SUSPECT", "excerpt": "Accused Vikram Singh alias Vicky fled scene on two-wheeler"},
                    {"record_id": "CR-2026-004", "role": "SUSPECT", "excerpt": "Suspect Vikram Singh identified from CCTV footage at robbery site"},
                    {"record_id": "CR-2026-002", "role": "PERSON_OF_INTEREST", "excerpt": "Vikram Singh observed in proximity of retail showroom"}
                ],
                "phone_number": "+919876543210"
            },
            {
                "name": "Sunil Sharma",
                "aliases": ["Sunny"],
                "provenance": "INVESTIGATIVE_REPORT",
                "confidence": 0.90,
                "cases": [
                    {"record_id": "CR-2026-001", "role": "ASSOCIATE", "excerpt": "Accomplice Sunil Sharma aided in transport of stolen electronics"},
                    {"record_id": "CR-2026-002", "role": "SUSPECT", "excerpt": "Sunil Sharma apprehended with break-in tools outside store"}
                ],
                "phone_number": "+919811122233"
            },
            {
                "name": "Rajesh Verma",
                "aliases": ["Raju", "Verma Ji"],
                "provenance": "STATEMENT",
                "confidence": 0.88,
                "cases": [
                    {"record_id": "CR-2026-002", "role": "CONSPIRATOR", "excerpt": "Rajesh Verma alias Raju facilitated fencing of stolen goods"},
                    {"record_id": "CR-2026-004", "role": "ASSOCIATE", "excerpt": "Communicated with Vikram Singh prior to convenience store robbery"}
                ],
                "phone_number": None
            },
            {
                "name": "Ramesh Rao",
                "aliases": [],
                "provenance": "WITNESS_STATEMENT",
                "confidence": 0.85,
                "cases": [
                    {"record_id": "CR-2026-003", "role": "WITNESS", "excerpt": "Eyewitness Ramesh Rao reported altercation outside restaurant"}
                ],
                "phone_number": "+919700011122"
            },
            {
                "name": "Amit Patel",
                "aliases": ["Bunty"],
                "provenance": "FIR_NARRATIVE",
                "confidence": 0.92,
                "cases": [
                    {"record_id": "CR-2026-005", "role": "ACCUSED", "excerpt": "Accused Amit Patel operated skimming device at ATM kiosk"}
                ],
                "phone_number": None
            }
        ]

        persons_created = 0
        assocs_created = 0
        phone_links_created = 0

        for spec in people_specs:
            person = PersonResolutionService.resolve_or_create_person(
                db=db,
                name=spec["name"],
                aliases=spec["aliases"],
                source_provenance=spec["provenance"],
                confidence=spec["confidence"]
            )
            persons_created += 1

            # Link to crimes
            for case_info in spec["cases"]:
                rec_id = case_info["record_id"]
                target_crime = crime_by_rec.get(rec_id)
                if target_crime:
                    PersonResolutionService.link_person_to_crime(
                        db=db,
                        crime_id=target_crime.id,
                        person_id=person.id,
                        role=case_info["role"],
                        relationship_type="INVOLVED_IN" if case_info["role"] in ("SUSPECT", "ACCUSED") else "MENTIONED_IN",
                        extraction_confidence=spec["confidence"],
                        evidence_excerpt=case_info["excerpt"]
                    )
                    assocs_created += 1

            # Link to phone if phone exists
            ph_num = spec.get("phone_number")
            if ph_num:
                ph_obj = db.query(PhoneNumber).filter(PhoneNumber.normalized_number == ph_num).first()
                if ph_obj:
                    PersonResolutionService.link_person_to_phone(
                        db=db,
                        person_id=person.id,
                        phone_id=ph_obj.id,
                        person_name=person.canonical_name,
                        role=spec["cases"][0]["role"] if spec["cases"] else "SUSPECT",
                        confidence=spec["confidence"],
                        confidence_type="explicit",
                        source=spec["provenance"]
                    )
                    phone_links_created += 1

        db.commit()
        logger.info(
            f"Seeded person network: {persons_created} people, {assocs_created} crime associations, {phone_links_created} phone links."
        )

        return {
            "status": "completed",
            "persons_seeded": persons_created,
            "crime_associations": assocs_created,
            "phone_links": phone_links_created
        }
