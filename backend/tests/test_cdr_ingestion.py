"""
Phase 4 Telecommunications: CDR Ingestion & Deduplication Tests
Tests CSV/JSON parsing, alias mapping, fingerprint deduplication, dry run, and persistence.
"""
import pytest
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.crime import ImportBatch, CrimeRejection
from app.models.telecom import PhoneNumber, CdrRecord
from app.services.cdr_ingestion_service import CdrIngestionService


@pytest.fixture(scope="function")
def test_db():
    """In-memory SQLite engine for test isolation."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def add_geo_functions(dbapi_conn, connection_record):
        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.create_function("ST_GeogFromText", 1, lambda v: v)
            dbapi_conn.create_function("ST_AsGeoJSON", 1, lambda v: "{}")
            dbapi_conn.create_function("AsBinary", 1, lambda v: v)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_cdr_csv_parsing_and_alias_mapping(test_db):
    """Verifies that diverse column aliases are properly recognized and normalized."""
    csv_content = b"""originating_number,destination_number,call_time,call_duration,call_type,cell_id
9876543210,9123456789,2026-09-19 14:30:00,120,VOICE,TOWER_HYD_01
+91 9988776655,9876543210,2026-09-19 15:45:00,45,SMS,TOWER_HYD_02
"""
    records, file_type = CdrIngestionService.parse_file_content(csv_content, "cdr_telco_export.csv")
    assert file_type == "CSV"
    assert len(records) == 2

    res = CdrIngestionService.process_data(
        db=test_db,
        raw_records=records,
        filename="cdr_telco_export.csv",
        file_type="CSV",
        dry_run=False
    )

    assert res["valid_count"] == 2
    assert res["rejected_count"] == 0
    assert res["batch_id"] is not None

    # Check database persistence
    phones = test_db.query(PhoneNumber).all()
    assert len(phones) == 3  # 9876543210, 9123456789, 9988776655
    norm_set = {p.normalized_number for p in phones}
    assert "+919876543210" in norm_set
    assert "+919123456789" in norm_set
    assert "+919988776655" in norm_set

    cdrs = test_db.query(CdrRecord).all()
    assert len(cdrs) == 2


def test_cdr_json_parsing(test_db):
    """Verifies JSON format parsing and ingestion."""
    json_bytes = b"""{
        "records": [
            {
                "caller_phone": "+91 9876543210",
                "callee_phone": "+91 9123456789",
                "timestamp": "2026-09-19T10:00:00Z",
                "duration_seconds": 95,
                "call_type": "VOICE",
                "location": "Banjara Hills Tower 4"
            }
        ]
    }"""
    records, file_type = CdrIngestionService.parse_file_content(json_bytes, "calls.json")
    assert file_type == "JSON"
    assert len(records) == 1

    res = CdrIngestionService.process_data(
        db=test_db,
        raw_records=records,
        filename="calls.json",
        file_type="JSON",
        dry_run=False
    )
    assert res["valid_count"] == 1
    assert res["rejected_count"] == 0


def test_cdr_deduplication_intra_batch_and_db(test_db):
    """Verifies deterministic deduplication rejects identical records both intra-batch and against DB."""
    raw_records = [
        {
            "caller": "9876543210",
            "callee": "9123456789",
            "timestamp": "2026-09-19 12:00:00",
            "duration": 60,
            "call_type": "VOICE",
            "source_reference": "REC-001"
        },
        # Exact duplicate in same batch
        {
            "caller": "+91 9876543210",
            "callee": "+91 9123456789",
            "timestamp": "2026-09-19 12:00:00",
            "duration": 60,
            "call_type": "VOICE",
            "source_reference": "REC-001"
        }
    ]

    res = CdrIngestionService.process_data(
        db=test_db,
        raw_records=raw_records,
        filename="batch1.csv",
        file_type="CSV",
        dry_run=False
    )
    assert res["valid_count"] == 1
    assert res["rejected_count"] == 1
    assert res["rejections"][0]["error_category"] == "DUPLICATE_CDR"

    # Second batch ingestion attempt with the same record -> database duplicate detection
    res2 = CdrIngestionService.process_data(
        db=test_db,
        raw_records=[raw_records[0]],
        filename="batch2.csv",
        file_type="CSV",
        dry_run=False
    )
    assert res2["valid_count"] == 0
    assert res2["rejected_count"] == 1
    assert res2["rejections"][0]["error_category"] == "DUPLICATE_CDR_DATABASE"


def test_cdr_validation_rejections(test_db):
    """Invalid caller, missing callee, or negative duration are safely rejected with audit logs."""
    malformed = [
        {"caller": "", "callee": "9876543210", "timestamp": "2026-09-19 12:00:00", "duration": 10},
        {"caller": "9876543210", "callee": "", "timestamp": "2026-09-19 12:00:00", "duration": 10},
        {"caller": "123", "callee": "9876543210", "timestamp": "2026-09-19 12:00:00", "duration": 10},
        {"caller": "9876543210", "callee": "9123456789", "timestamp": "not-a-date", "duration": 10},
        {"caller": "9876543210", "callee": "9123456789", "timestamp": "2026-09-19 12:00:00", "duration": -50},
    ]

    res = CdrIngestionService.process_data(
        db=test_db,
        raw_records=malformed,
        filename="bad_records.csv",
        file_type="CSV",
        dry_run=False
    )
    assert res["valid_count"] == 0
    assert res["rejected_count"] == 5
    categories = [r["error_category"] for r in res["rejections"]]
    assert "MISSING_CALLER" in categories
    assert "MISSING_CALLEE" in categories
    assert "INVALID_CALLER_PHONE" in categories
    assert "INVALID_TIMESTAMP" in categories
    assert "INVALID_DURATION" in categories


def test_cdr_dry_run_does_not_mutate_db(test_db):
    """Dry run should return validation preview without committing anything to DB."""
    records = [
        {"caller": "9876543210", "callee": "9123456789", "timestamp": "2026-09-19 12:00:00", "duration": 30}
    ]

    res = CdrIngestionService.process_data(
        db=test_db,
        raw_records=records,
        filename="preview.csv",
        file_type="CSV",
        dry_run=True
    )
    assert res["dry_run"] is True
    assert res["valid_count"] == 1
    assert res["batch_id"] is None

    # Verify nothing was committed
    assert test_db.query(CdrRecord).count() == 0
    assert test_db.query(PhoneNumber).count() == 0
    assert test_db.query(ImportBatch).count() == 0
