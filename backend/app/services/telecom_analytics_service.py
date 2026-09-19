"""
Phase 4 Telecommunications: Telecom Network Analytics Service
Computes objective telecommunication network metrics, call activity patterns,
and cross-case intelligence links.
Strict principle: Network centrality measures are descriptive, never accusatory.
"""
import logging
from collections import defaultdict
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_, func, select

from app.models.telecom import PhoneNumber, CdrRecord, CrimePhoneAssociation, PersonPhoneAssociation
from app.models.crime import Crime

logger = logging.getLogger("connectdots_telecom_analytics")


class TelecomAnalyticsService:
    """
    Analyzes CDR communication records and phone associations to extract
    investigative network intelligence without subjective bias.
    """

    @classmethod
    def get_phone_profile(cls, db: Session, phone_id_or_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves complete telecommunications profile, call volumes, contact breakdown,
        and linked criminal cases for a phone identity.
        """
        clean_input = phone_id_or_number.strip()
        # Find phone by ID or by normalized number
        phone = db.query(PhoneNumber).filter(
            or_(PhoneNumber.id == clean_input, PhoneNumber.normalized_number == clean_input)
        ).first()

        if not phone:
            return None

        # Outbound calls
        outbound = db.query(CdrRecord).filter(CdrRecord.caller_phone_id == phone.id).all()
        # Inbound calls
        inbound = db.query(CdrRecord).filter(CdrRecord.callee_phone_id == phone.id).all()

        total_calls = len(outbound) + len(inbound)
        outbound_duration = sum(c.duration_seconds for c in outbound)
        inbound_duration = sum(c.duration_seconds for c in inbound)
        total_duration = outbound_duration + inbound_duration

        # Unique contacts
        unique_contact_ids: Set[str] = set()
        for c in outbound:
            unique_contact_ids.add(c.callee_phone_id)
        for c in inbound:
            unique_contact_ids.add(c.caller_phone_id)

        # Timestamps
        all_timestamps = [c.call_timestamp for c in outbound if c.call_timestamp] + \
                         [c.call_timestamp for c in inbound if c.call_timestamp]
        first_activity = min(all_timestamps).isoformat() if all_timestamps else None
        last_activity = max(all_timestamps).isoformat() if all_timestamps else None

        # Hourly activity breakdown
        hourly_counts: Dict[int, int] = {h: 0 for h in range(24)}
        for ts in all_timestamps:
            hourly_counts[ts.hour] += 1

        # Associated Crimes
        crime_assocs = db.query(CrimePhoneAssociation).filter(
            CrimePhoneAssociation.phone_id == phone.id
        ).all()
        associated_crimes = []
        for ca in crime_assocs:
            c = db.query(Crime).filter(Crime.id == ca.crime_id).first()
            if c:
                associated_crimes.append({
                    "crime_id": c.id,
                    "record_id": c.record_id,
                    "category": c.category,
                    "crime_type": c.crime_type,
                    "location_name": c.location_name,
                    "occurred_at": c.occurred_at.isoformat() if c.occurred_at else None,
                    "relationship_type": ca.relationship_type,
                    "confidence": ca.confidence,
                    "confidence_type": ca.confidence_type,
                    "source_text": ca.source_text
                })

        # Associated Persons
        person_assocs = db.query(PersonPhoneAssociation).filter(
            PersonPhoneAssociation.phone_id == phone.id
        ).all()
        associated_persons = [
            {
                "person_name": pa.person_name,
                "role": pa.role,
                "confidence": pa.confidence,
                "confidence_type": pa.confidence_type,
                "source": pa.source
            }
            for pa in person_assocs
        ]

        # Top Contact phone numbers
        contact_frequency: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "duration": 0})
        for c in outbound:
            contact_frequency[c.callee_phone_id]["count"] += 1
            contact_frequency[c.callee_phone_id]["duration"] += c.duration_seconds
        for c in inbound:
            contact_frequency[c.caller_phone_id]["count"] += 1
            contact_frequency[c.caller_phone_id]["duration"] += c.duration_seconds

        top_contacts = []
        for c_id, stats in sorted(contact_frequency.items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
            c_phone = db.query(PhoneNumber).filter(PhoneNumber.id == c_id).first()
            if c_phone:
                top_contacts.append({
                    "phone_id": c_phone.id,
                    "normalized_number": c_phone.normalized_number,
                    "call_count": stats["count"],
                    "total_duration": stats["duration"],
                })

        return {
            "id": phone.id,
            "normalized_number": phone.normalized_number,
            "country_code": phone.country_code,
            "national_number": phone.national_number,
            "number_type": phone.number_type,
            "carrier": phone.carrier,
            "created_at": phone.created_at.isoformat() if phone.created_at else None,
            "metrics": {
                "total_calls": total_calls,
                "outbound_calls": len(outbound),
                "inbound_calls": len(inbound),
                "total_duration_seconds": total_duration,
                "outbound_duration_seconds": outbound_duration,
                "inbound_duration_seconds": inbound_duration,
                "unique_contacts_count": len(unique_contact_ids),
                "first_activity": first_activity,
                "last_activity": last_activity,
                "hourly_distribution": hourly_counts,
            },
            "associated_crimes": associated_crimes,
            "associated_persons": associated_persons,
            "top_contacts": top_contacts,
        }

    @classmethod
    def get_cross_case_connections(cls, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Uncovers multi-crime connections established through shared phones and direct CDR communication.
        Returns:
            List of cross-case linkages with evidence citations and confidence metrics.
        """
        connections: List[Dict[str, Any]] = []
        seen_pairs = set()

        # 1. Direct Shared Phone Number: Crime A mentions Phone X AND Crime B mentions Phone X
        all_crime_assocs = db.query(CrimePhoneAssociation).all()
        phone_to_crimes: Dict[str, List[CrimePhoneAssociation]] = defaultdict(list)
        for ca in all_crime_assocs:
            phone_to_crimes[ca.phone_id].append(ca)

        for phone_id, assocs in phone_to_crimes.items():
            if len(assocs) < 2:
                continue
            phone = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
            if not phone:
                continue

            for i in range(len(assocs)):
                for j in range(i + 1, len(assocs)):
                    ca1, ca2 = assocs[i], assocs[j]
                    if ca1.crime_id == ca2.crime_id:
                        continue
                    pair = tuple(sorted([ca1.crime_id, ca2.crime_id]))
                    pair_key = (pair[0], pair[1], "SHARED_PHONE")
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    c1 = db.query(Crime).filter(Crime.id == pair[0]).first()
                    c2 = db.query(Crime).filter(Crime.id == pair[1]).first()
                    if c1 and c2:
                        connections.append({
                            "connection_type": "SHARED_PHONE",
                            "crime_1": {
                                "id": c1.id,
                                "record_id": c1.record_id,
                                "category": c1.category,
                                "location_name": c1.location_name
                            },
                            "crime_2": {
                                "id": c2.id,
                                "record_id": c2.record_id,
                                "category": c2.category,
                                "location_name": c2.location_name
                            },
                            "shared_phone": phone.normalized_number,
                            "evidence": f"Both incidents reference identical phone number {phone.normalized_number}.",
                            "confidence": 0.95,
                            "confidence_type": "derived"
                        })

        # 2. CDR Communication Link: Crime A mentions Phone X, Crime B mentions Phone Y, and Phone X called Phone Y
        # Aggregate CDRs by phone pair
        cdrs = db.query(CdrRecord).all()
        call_pair_map: Dict[Tuple[str, str], int] = defaultdict(int)
        for cdr in cdrs:
            p_tuple = tuple(sorted([cdr.caller_phone_id, cdr.callee_phone_id]))
            call_pair_map[p_tuple] += 1

        for (pid1, pid2), call_count in call_pair_map.items():
            crimes_1 = phone_to_crimes.get(pid1, [])
            crimes_2 = phone_to_crimes.get(pid2, [])

            if not crimes_1 or not crimes_2:
                continue

            phone1 = db.query(PhoneNumber).filter(PhoneNumber.id == pid1).first()
            phone2 = db.query(PhoneNumber).filter(PhoneNumber.id == pid2).first()
            if not phone1 or not phone2:
                continue

            for ca1 in crimes_1:
                for ca2 in crimes_2:
                    if ca1.crime_id == ca2.crime_id:
                        continue
                    pair = tuple(sorted([ca1.crime_id, ca2.crime_id]))
                    pair_key = (pair[0], pair[1], "CDR_COMMUNICATION")
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    c1 = db.query(Crime).filter(Crime.id == pair[0]).first()
                    c2 = db.query(Crime).filter(Crime.id == pair[1]).first()
                    if c1 and c2:
                        connections.append({
                            "connection_type": "CDR_COMMUNICATION",
                            "crime_1": {
                                "id": c1.id,
                                "record_id": c1.record_id,
                                "category": c1.category,
                                "location_name": c1.location_name
                            },
                            "crime_2": {
                                "id": c2.id,
                                "record_id": c2.record_id,
                                "category": c2.category,
                                "location_name": c2.location_name
                            },
                            "phone_1": phone1.normalized_number,
                            "phone_2": phone2.normalized_number,
                            "call_count": call_count,
                            "evidence": (
                                f"Incident {c1.record_id} mentions {phone1.normalized_number} and "
                                f"Incident {c2.record_id} mentions {phone2.normalized_number}. "
                                f"CDR records verify {call_count} telecommunications between these numbers."
                            ),
                            "confidence": 0.88,
                            "confidence_type": "derived"
                        })

        return connections[:limit]
