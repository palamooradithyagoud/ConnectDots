import pytest
from datetime import datetime
from app.services.cleaning_service import CleaningService
from app.services.ingestion_service import IngestionService


def test_coordinate_validation_valid():
    """Verify that legitimate WGS84 coordinates are accepted and rounded."""
    is_valid, lat, lon, err = CleaningService.validate_coordinates(12.9715987, 77.594562)
    assert is_valid is True
    assert lat == 12.971599
    assert lon == 77.594562
    assert err == ""


def test_coordinate_validation_out_of_bounds():
    """Verify that out-of-range coordinates are rejected with descriptive messages."""
    # Latitude out of bounds
    is_valid, lat, lon, err = CleaningService.validate_coordinates(999.0, 77.5)
    assert is_valid is False
    assert "Latitude 999.0 is out of valid bounds" in err

    # Longitude out of bounds
    is_valid, lat, lon, err = CleaningService.validate_coordinates(12.5, -200.0)
    assert is_valid is False
    assert "Longitude -200.0 is out of valid bounds" in err


def test_coordinate_validation_null_island_and_strings():
    """Verify that Null Island (0,0) and invalid non-numeric strings are rejected."""
    # Null island
    is_valid, lat, lon, err = CleaningService.validate_coordinates(0.0, 0.0)
    assert is_valid is False
    assert "Null Island" in err

    # String non-numeric
    is_valid, lat, lon, err = CleaningService.validate_coordinates("not_a_num", 77.5)
    assert is_valid is False
    assert "must be numeric" in err


def test_date_parsing_various_formats():
    """Verify parsing of ISO, US, and combined dates."""
    dt1 = CleaningService.parse_datetime("2026-03-01", "14:30:00")
    assert dt1 is not None
    assert dt1.year == 2026
    assert dt1.month == 3
    assert dt1.day == 1
    assert dt1.hour == 14
    assert dt1.minute == 30

    dt2 = CleaningService.parse_datetime("03/06/2026", "10:15 PM")
    assert dt2 is not None
    assert dt2.year == 2026
    assert dt2.month == 3
    assert dt2.day == 6
    assert dt2.hour == 22
    assert dt2.minute == 15

    # Invalid date
    dt_err = CleaningService.parse_datetime("INVALID-DATE")
    assert dt_err is None


def test_crime_canonicalization():
    """Verify canonical mapping for various aliases."""
    c_type, cat = CleaningService.normalize_crime_type("PETTY LARCENY")
    assert cat == "THEFT"

    c_type, cat = CleaningService.normalize_crime_type("Breaking and Entering")
    assert cat == "BURGLARY"

    c_type, cat = CleaningService.normalize_crime_type("Aggravated Assault")
    assert cat == "ASSAULT"

    c_type, cat = CleaningService.normalize_crime_type("Phishing Scam")
    assert cat == "CYBERCRIME"


def test_full_record_validation():
    """Verify validate_and_clean_record on valid and broken records."""
    valid_raw = {
        "record_id": "CR-TEST-001",
        "crime_type": "THEFT",
        "location": "commercial street",
        "date": "2026-03-01",
        "time": "14:30:00",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "description": "Phone theft",
        "source": "City Police"
    }

    is_valid, cleaned, err = CleaningService.validate_and_clean_record(valid_raw)
    assert is_valid is True
    assert cleaned["record_id"] == "CR-TEST-001"
    assert cleaned["category"] == "THEFT"
    assert cleaned["location_name"] == "Commercial Street"
    assert cleaned["latitude"] == 12.9716
    assert err is None

    # Missing record_id
    broken_raw = valid_raw.copy()
    broken_raw["record_id"] = ""
    is_valid, cleaned, err = CleaningService.validate_and_clean_record(broken_raw)
    assert is_valid is False
    assert err["error_category"] == "MISSING_FIELD"
