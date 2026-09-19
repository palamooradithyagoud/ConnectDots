"""
Phase 4 Telecommunications: CDR Ingestion & Deduplication Service
Handles CSV and JSON CDR record ingestion, tolerant alias mapping, E.164 phone normalization,
SHA-256 deterministic deduplication, and transactional persistence.
"""
import io
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional, Set

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.crime import ImportBatch, CrimeRejection
from app.models.telecom import PhoneNumber, CdrRecord
from app.services.phone_normalization_service import PhoneNormalizationService
from app.services.cleaning_service import CleaningService

logger = logging.getLogger("connectdots_cdr_ingestion")


class CdrIngestionService:
    """
    Manages parsing, field resolution, phone canonicalization, deduplication,
    and bulk transactional ingestion for Call Detail Records (CDRs).
    """

    CALLER_ALIASES = [
        "caller_phone", "caller", "originating_number", "source_number",
        "calling_number", "from", "calling_no", "msisdn_a", "ani", "source_phone"
    ]

    CALLEE_ALIASES = [
        "callee_phone", "callee", "destination_number", "dialed_number",
        "called_number", "to", "called_no", "msisdn_b", "dnis", "target_phone"
    ]

    TIMESTAMP_ALIASES = [
        "call_timestamp", "timestamp", "call_time", "datetime", "time",
        "date_time", "start_time", "call_date", "occurred_at"
    ]

    DURATION_ALIASES = [
        "duration_seconds", "duration", "call_duration", "dur_sec",
        "call_duration_seconds", "sec", "length_seconds"
    ]

    CALL_TYPE_ALIASES = [
        "call_type", "type", "service_type", "call_direction", "direction"
    ]

    LOCATION_ALIASES = [
        "location_or_tower", "location", "tower", "cell_id", "tower_location",
        "site", "bts", "cell_tower", "location_name"
    ]

    SOURCE_REF_ALIASES = [
        "source_reference", "source_record_id", "reference", "record_id",
        "cdr_id", "id", "ticket_id"
    ]

    LATITUDE_ALIASES = ["latitude", "lat", "tower_lat"]
    LONGITUDE_ALIASES = ["longitude", "lon", "lng", "tower_lon", "tower_lng"]

    @classmethod
    def parse_file_content(cls, content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], str]:
        """Parses CSV or JSON file bytes into row dictionaries."""
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            file_type = "CSV"
            df = pd.read_csv(io.BytesIO(content), dtype=str)
            df = df.where(pd.notnull(df), None)
            records = df.to_dict(orient="records")
        elif filename_lower.endswith(".json"):
            file_type = "JSON"
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and "records" in data:
                records = data["records"]
            elif isinstance(data, dict) and "cdrs" in data:
                records = data["cdrs"]
            elif isinstance(data, dict):
                records = [data]
            else:
                raise ValueError("Unsupported JSON structure: expected list or object with 'records'/'cdrs' key")
        else:
            raise ValueError(f"Unsupported file format '{filename}'. Please upload a CSV or JSON file.")

        return records, file_type

    @classmethod
    def _resolve_field(cls, record: Dict[str, Any], aliases: List[str]) -> Optional[Any]:
        """Case-insensitively resolves a field value against alias candidates."""
        rec_lower = {k.lower().strip(): v for k, v in record.items()}
        for alias in aliases:
            if alias in rec_lower:
                val = rec_lower[alias]
                if val is not None:
                    s_val = str(val).strip()
                    if s_val and s_val.lower() != "nan":
                        return s_val
        return None

    @classmethod
    def compute_fingerprint(
        cls,
        caller: str,
        callee: str,
        timestamp_iso: str,
        duration: int,
        call_type: str,
        source_ref: Optional[str] = None
    ) -> str:
        """
        Generates a deterministic SHA-256 fingerprint for CDR deduplication.
        """
        raw_key = f"{caller}|{callee}|{timestamp_iso}|{duration}|{call_type}|{source_ref or ''}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def process_data(
        cls,
        db: Session,
        raw_records: List[Dict[str, Any]],
        filename: str,
        file_type: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes validation, phone normalization, fingerprinting, deduplication,
        and transactional persistence.
        """
        total_rows = len(raw_records)
        valid_cleaned_records: List[Dict[str, Any]] = []
        rejections: List[Dict[str, Any]] = []
        seen_batch_fingerprints: Set[str] = set()

        # Step 1: Pre-process and validate each raw record
        for idx, raw in enumerate(raw_records, start=1):
            caller_raw = cls._resolve_field(raw, cls.CALLER_ALIASES)
            callee_raw = cls._resolve_field(raw, cls.CALLEE_ALIASES)
            time_raw = cls._resolve_field(raw, cls.TIMESTAMP_ALIASES)
            dur_raw = cls._resolve_field(raw, cls.DURATION_ALIASES)
            type_raw = cls._resolve_field(raw, cls.CALL_TYPE_ALIASES) or "VOICE"
            loc_raw = cls._resolve_field(raw, cls.LOCATION_ALIASES)
            ref_raw = cls._resolve_field(raw, cls.SOURCE_REF_ALIASES)
            lat_raw = cls._resolve_field(raw, cls.LATITUDE_ALIASES)
            lon_raw = cls._resolve_field(raw, cls.LONGITUDE_ALIASES)

            # Check required caller
            if not caller_raw:
                rejections.append({
                    "row_number": idx,
                    "raw_data": raw,
                    "error_category": "MISSING_CALLER",
                    "error_message": "Caller phone number (originating number) is missing or blank"
                })
                continue

            # Check required callee
            if not callee_raw:
                rejections.append({
                    "row_number": idx,
                    "raw_data": raw,
                    "error_category": "MISSING_CALLEE",
                    "error_message": "Callee phone number (destination number) is missing or blank"
                })
                continue

            # Normalize Caller
            caller_norm = PhoneNormalizationService.normalize(caller_raw)
            if not caller_norm.is_valid:
                rejections.append({
                    "row_number": idx,
                    "raw_data": raw,
                    "error_category": "INVALID_CALLER_PHONE",
                    "error_message": f"Caller '{caller_raw}' invalid: {caller_norm.error_message}"
                })
                continue

            # Normalize Callee
            callee_norm = PhoneNormalizationService.normalize(callee_raw)
            if not callee_norm.is_valid:
                rejections.append({
                    "row_number": idx,
                    "raw_data": raw,
                    "error_category": "INVALID_CALLEE_PHONE",
                    "error_message": f"Callee '{callee_raw}' invalid: {callee_norm.error_message}"
                })
                continue

            # Parse Timestamp
            if not time_raw:
                rejections.append({
                    "row_number": idx,
                    "raw_data": raw,
                    "error_category": "MISSING_TIMESTAMP",
                    "error_message": "Call timestamp is missing"
                })
                continue

            parsed_dt = CleaningService.parse_datetime(time_raw)
            if not parsed_dt:
                rejections.append({
                    "row_number": idx,
                    "raw_data": raw,
                    "error_category": "INVALID_TIMESTAMP",
                    "error_message": f"Unable to parse timestamp '{time_raw}'"
                })
                continue

            # Parse Duration
            duration_sec = 0
            if dur_raw is not None:
                try:
                    duration_sec = int(float(dur_raw))
                    if duration_sec < 0:
                        rejections.append({
                            "row_number": idx,
                            "raw_data": raw,
                            "error_category": "INVALID_DURATION",
                            "error_message": f"Duration cannot be negative: {duration_sec}"
                        })
                        continue
                except (ValueError, TypeError):
                    rejections.append({
                        "row_number": idx,
                        "raw_data": raw,
                        "error_category": "INVALID_DURATION",
                        "error_message": f"Duration '{dur_raw}' is not a valid integer"
                    })
                    continue

            # Coordinates if present
            latitude = None
            longitude = None
            if lat_raw and lon_raw:
                is_coord_valid, lat, lon = CleaningService.validate_coordinates(lat_raw, lon_raw)
                if is_coord_valid:
                    latitude = lat
                    longitude = lon

            # Compute Fingerprint
            fingerprint = cls.compute_fingerprint(
                caller=caller_norm.normalized_number,
                callee=callee_norm.normalized_number,
                timestamp_iso=parsed_dt.isoformat(),
                duration=duration_sec,
                call_type=type_raw.upper(),
                source_ref=ref_raw
            )

            # Intra-batch deduplication
            if fingerprint in seen_batch_fingerprints:
                rejections.append({
                    "row_number": idx,
                    "raw_data": raw,
                    "error_category": "DUPLICATE_CDR",
                    "error_message": "Duplicate CDR entry detected within upload batch"
                })
                continue

            seen_batch_fingerprints.add(fingerprint)

            valid_cleaned_records.append({
                "row_number": idx,
                "caller_norm": caller_norm,
                "callee_norm": callee_norm,
                "call_timestamp": parsed_dt,
                "duration_seconds": duration_sec,
                "call_type": type_raw.upper(),
                "location_or_tower": loc_raw,
                "latitude": latitude,
                "longitude": longitude,
                "source_reference": ref_raw,
                "fingerprint": fingerprint,
            })

        # Step 2: Bulk Database Deduplication
        final_to_insert: List[Dict[str, Any]] = []
        if valid_cleaned_records:
            all_fps = [r["fingerprint"] for r in valid_cleaned_records]
            existing_fps = set(
                db.execute(select(CdrRecord.fingerprint).where(CdrRecord.fingerprint.in_(all_fps))).scalars().all()
            )

            for rec in valid_cleaned_records:
                if rec["fingerprint"] in existing_fps:
                    rejections.append({
                        "row_number": rec["row_number"],
                        "raw_data": {"caller": rec["caller_norm"].normalized_number, "callee": rec["callee_norm"].normalized_number},
                        "error_category": "DUPLICATE_CDR_DATABASE",
                        "error_message": f"CDR fingerprint already exists in database (fingerprint: {rec['fingerprint'][:12]}...)"
                    })
                else:
                    final_to_insert.append(rec)

        # Step 3: Handle Dry Run
        if dry_run:
            return {
                "batch_id": None,
                "dry_run": True,
                "filename": filename,
                "total_rows": total_rows,
                "valid_count": len(final_to_insert),
                "rejected_count": len(rejections),
                "preview_valid": [
                    {
                        "caller": r["caller_norm"].normalized_number,
                        "callee": r["callee_norm"].normalized_number,
                        "timestamp": r["call_timestamp"].isoformat(),
                        "duration_seconds": r["duration_seconds"],
                        "call_type": r["call_type"],
                        "location": r["location_or_tower"]
                    }
                    for r in final_to_insert[:5]
                ],
                "rejections": rejections,
                "message": f"Dry-run preview: {len(final_to_insert)} valid CDRs, {len(rejections)} rejected."
            }

        # Step 4: Transactional Persistence
        batch = ImportBatch(
            filename=filename,
            file_type=file_type,
            total_rows=total_rows,
            valid_count=len(final_to_insert),
            rejected_count=len(rejections),
            status="COMPLETED" if final_to_insert else "FAILED"
        )
        db.add(batch)
        db.flush()

        # Step 4a: Collect and upsert unique PhoneNumbers in bulk
        unique_phones: Dict[str, Any] = {}
        for r in final_to_insert:
            c_norm = r["caller_norm"]
            unique_phones[c_norm.normalized_number] = c_norm
            ce_norm = r["callee_norm"]
            unique_phones[ce_norm.normalized_number] = ce_norm

        phone_id_map: Dict[str, str] = {}
        if unique_phones:
            existing_db_phones = db.execute(
                select(PhoneNumber).where(PhoneNumber.normalized_number.in_(list(unique_phones.keys())))
            ).scalars().all()

            for ep in existing_db_phones:
                phone_id_map[ep.normalized_number] = ep.id

            for norm_num, norm_obj in unique_phones.items():
                if norm_num not in phone_id_map:
                    new_phone = PhoneNumber(
                        normalized_number=norm_num,
                        country_code=norm_obj.country_code,
                        national_number=norm_obj.national_number,
                        number_type=norm_obj.number_type,
                    )
                    db.add(new_phone)
                    db.flush()
                    phone_id_map[norm_num] = new_phone.id

        # Step 4b: Insert CdrRecords
        for rec in final_to_insert:
            c_id = phone_id_map[rec["caller_norm"].normalized_number]
            ce_id = phone_id_map[rec["callee_norm"].normalized_number]

            cdr_entry = CdrRecord(
                caller_phone_id=c_id,
                callee_phone_id=ce_id,
                call_timestamp=rec["call_timestamp"],
                duration_seconds=rec["duration_seconds"],
                call_type=rec["call_type"],
                location_or_tower=rec["location_or_tower"],
                latitude=rec["latitude"],
                longitude=rec["longitude"],
                source_reference=rec["source_reference"],
                source_batch_id=batch.id,
                fingerprint=rec["fingerprint"],
            )
            db.add(cdr_entry)

        # Step 4c: Record rejections for audit
        for rej in rejections:
            rejection_entry = CrimeRejection(
                import_batch_id=batch.id,
                row_number=rej.get("row_number"),
                raw_data=rej.get("raw_data", {}),
                error_category=rej.get("error_category", "UNKNOWN"),
                error_message=rej.get("error_message", "Rejected"),
            )
            db.add(rejection_entry)

        db.commit()
        logger.info(f"Committed CDR batch {batch.id}: {len(final_to_insert)} records saved.")

        return {
            "batch_id": batch.id,
            "dry_run": False,
            "filename": filename,
            "total_rows": total_rows,
            "valid_count": len(final_to_insert),
            "rejected_count": len(rejections),
            "preview_valid": [],
            "rejections": rejections,
            "message": f"Successfully ingested {len(final_to_insert)} CDR records into batch {batch.id}."
        }
