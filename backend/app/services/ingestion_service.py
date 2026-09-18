import io
import json
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from geoalchemy2.elements import WKTElement

from app.models.crime import Crime, ImportBatch, CrimeRejection
from app.schemas.crime import ImportResultResponse, RejectionDetail, CrimeBase
from app.services.cleaning_service import CleaningService


class IngestionService:
    """Manages CSV/JSON parsing, deduplication, batch creation, and database persistence."""

    @classmethod
    def parse_file_content(cls, content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], str]:
        """Parses CSV or JSON file bytes into a list of row dictionaries."""
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            file_type = "CSV"
            # Read CSV using pandas with string preservation
            df = pd.read_csv(io.BytesIO(content), dtype=str)
            # Replace NaN with None
            df = df.where(pd.notnull(df), None)
            records = df.to_dict(orient="records")
        elif filename_lower.endswith(".json"):
            file_type = "JSON"
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and "records" in data:
                records = data["records"]
            elif isinstance(data, dict):
                records = [data]
            else:
                raise ValueError("Unsupported JSON structure: expected list or object with 'records' key")
        else:
            raise ValueError(f"Unsupported file format '{filename}'. Please upload a CSV or JSON file.")

        return records, file_type

    @classmethod
    def process_data(
        cls,
        db: Session,
        raw_records: List[Dict[str, Any]],
        filename: str,
        file_type: str,
        dry_run: bool = False
    ) -> ImportResultResponse:
        """
        Executes the validation, deduplication, and ingestion pipeline.
        Supports dry-run preview and persistent transactional commit.
        """
        total_rows = len(raw_records)
        valid_records: List[Dict[str, Any]] = []
        rejections: List[RejectionDetail] = []
        seen_batch_record_ids = set()

        # Step 1: Collect record_ids to check for duplicates in DB in a single bulk query
        candidate_ids = []
        for r in raw_records:
            rid = r.get("record_id") or r.get("id") or r.get("crime_id")
            if rid:
                candidate_ids.append(CleaningService.clean_string(rid))

        existing_db_ids = set()
        if candidate_ids:
            existing_query = db.execute(
                select(Crime.record_id).where(Crime.record_id.in_(candidate_ids))
            ).scalars().all()
            existing_db_ids = set(existing_query)

        # Step 2: Validate and clean each record
        for idx, raw_record in enumerate(raw_records, start=1):
            # Check required fields, formats, coordinates, and types
            is_valid, cleaned, error_info = CleaningService.validate_and_clean_record(raw_record, row_num=idx)
            
            if not is_valid:
                rejections.append(RejectionDetail(
                    row_number=idx,
                    raw_data=raw_record,
                    error_category=error_info["error_category"],
                    error_message=error_info["error_message"]
                ))
                continue

            record_id = cleaned["record_id"]

            # Intra-batch duplicate check
            if record_id in seen_batch_record_ids:
                rejections.append(RejectionDetail(
                    row_number=idx,
                    raw_data=raw_record,
                    error_category="DUPLICATE_RECORD",
                    error_message=f"Duplicate record_id '{record_id}' detected within the same upload file"
                ))
                continue

            # Existing DB duplicate check
            if record_id in existing_db_ids:
                rejections.append(RejectionDetail(
                    row_number=idx,
                    raw_data=raw_record,
                    error_category="DUPLICATE_RECORD",
                    error_message=f"Record with ID '{record_id}' already exists in database"
                ))
                continue

            seen_batch_record_ids.add(record_id)
            valid_records.append(cleaned)

        valid_count = len(valid_records)
        rejected_count = len(rejections)

        # Step 3: Handle Dry Run mode (Return diagnostics without DB insertion)
        if dry_run:
            preview_items = [
                CrimeBase(
                    record_id=r["record_id"],
                    crime_type=r["crime_type"],
                    category=r["category"],
                    location_name=r["location_name"],
                    occurred_at=r["occurred_at"],
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    description=r["description"],
                    source=r["source"],
                    status=r["status"]
                )
                for r in valid_records[:10]  # Preview up to first 10
            ]
            return ImportResultResponse(
                batch_id=None,
                dry_run=True,
                filename=filename,
                total_rows=total_rows,
                valid_count=valid_count,
                rejected_count=rejected_count,
                preview_valid=preview_items,
                rejections=rejections,
                message=f"Dry run complete: {valid_count} valid, {rejected_count} rejected out of {total_rows} records."
            )

        # Step 4: Transactional Commit Mode
        batch = ImportBatch(
            filename=filename,
            file_type=file_type,
            total_rows=total_rows,
            valid_count=valid_count,
            rejected_count=rejected_count,
            status="COMPLETED" if valid_count > 0 or total_rows == 0 else "FAILED"
        )
        db.add(batch)
        db.flush()  # Generate batch.id

        # Insert Valid Crimes with PostGIS Geography points
        is_sqlite = db.bind and db.bind.dialect.name == "sqlite"
        for r in valid_records:
            point_wkt = f"POINT({r['longitude']} {r['latitude']})"
            geom_val = None if is_sqlite else WKTElement(point_wkt, srid=4326)
            crime_obj = Crime(
                record_id=r["record_id"],
                crime_type=r["crime_type"],
                category=r["category"],
                location_name=r["location_name"],
                occurred_at=r["occurred_at"],
                latitude=r["latitude"],
                longitude=r["longitude"],
                geom=geom_val,
                description=r["description"],
                source=r["source"],
                status=r["status"],
                import_batch_id=batch.id,
                extra_metadata=r.get("extra_metadata")
            )
            db.add(crime_obj)

        # Insert Rejected Records for Auditing
        for rej in rejections:
            rejection_obj = CrimeRejection(
                import_batch_id=batch.id,
                row_number=rej.row_number,
                raw_data=rej.raw_data,
                error_category=rej.error_category,
                error_message=rej.error_message
            )
            db.add(rejection_obj)

        db.commit()

        preview_items = [
            CrimeBase(
                record_id=r["record_id"],
                crime_type=r["crime_type"],
                category=r["category"],
                location_name=r["location_name"],
                occurred_at=r["occurred_at"],
                latitude=r["latitude"],
                longitude=r["longitude"],
                description=r["description"],
                source=r["source"],
                status=r["status"]
            )
            for r in valid_records[:10]
        ]

        return ImportResultResponse(
            batch_id=batch.id,
            dry_run=False,
            filename=filename,
            total_rows=total_rows,
            valid_count=valid_count,
            rejected_count=rejected_count,
            preview_valid=preview_items,
            rejections=rejections,
            message=f"Successfully imported {valid_count} records into PostgreSQL/PostGIS. Logged {rejected_count} rejections."
        )
