import math
import re
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
from dateutil import parser as date_parser


class CleaningService:
    """Provides validation, cleaning, and normalization logic for raw crime records."""

    # Canonical crime categories taxonomy (ordered with specific categories prioritized)
    CATEGORY_MAPPING = {
        "CYBERCRIME": ["CYBERCRIME", "CYBER FRAUD", "PHISHING", "HACKING", "DATA BREACH", "IDENTITY THEFT"],
        "FRAUD": ["FINANCIAL FRAUD", "FORGERY", "EMBEZZLEMENT", "SKIMMING", "FRAUD", "SCAM"],
        "THEFT": ["PETTY LARCENY", "PETTY THEFT", "SHOPLIFTING", "PICKPOCKETING", "THEFT", "LARCENY", "STEALING"],
        "BURGLARY": ["BREAKING AND ENTERING", "HOUSEBREAKING", "BREAK-IN", "BURGLARY", "B&E"],
        "ROBBERY": ["ARMED ROBBERY", "MUGGING", "HEIST", "SNATCHING", "ROBBERY"],
        "ASSAULT": ["PHYSICAL ASSAULT", "AGGRAVATED ASSAULT", "BATTERY", "ASSAULT", "FIGHT"],
        "HOMICIDE": ["HOMICIDE", "MURDER", "MANSLAUGHTER"],
        "VEHICLE_THEFT": ["VEHICLE THEFT", "AUTO THEFT", "MOTORCYCLE THEFT", "GRAND THEFT AUTO", "CARJACKING", "BIKE THEFT"],
        "NARCOTICS": ["NARCOTICS", "DRUGS", "SUBSTANCE ABUSE", "ILLICIT SUBSTANCES", "DRUG POSSESSION"],
        "VANDALISM": ["VANDALISM", "GRAFFITI", "PROPERTY DAMAGE", "MISCHIEF"],
    }

    @classmethod
    def clean_string(cls, val: Any) -> str:
        """Sanitizes text fields, stripping excess whitespace and whitespace characters."""
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return ""
        s = str(val).strip()
        s = re.sub(r"\s+", " ", s)
        return s

    @classmethod
    def normalize_crime_type(cls, raw_type: str) -> Tuple[str, str]:
        """
        Normalizes crime type string and resolves its canonical category.
        Returns: (standardized_crime_type, canonical_category)
        """
        cleaned = cls.clean_string(raw_type).upper()
        if not cleaned:
            return "", "OTHER"

        for canonical_cat, aliases in cls.CATEGORY_MAPPING.items():
            for alias in aliases:
                # Check exact match or word containment
                if alias == cleaned or alias in cleaned:
                    return cleaned, canonical_cat

        return cleaned, "OTHER"

    @classmethod
    def normalize_location(cls, raw_location: str) -> str:
        """Standardizes location name to clean Title Case format."""
        cleaned = cls.clean_string(raw_location)
        if not cleaned:
            return ""
        # Convert to title case but preserve abbreviations like MG, BTM, HSR, ORR, JNTU
        parts = cleaned.split(" ")
        normalized_parts = []
        acronyms = {"MG", "BTM", "HSR", "ORR", "JNTU", "JNTUA", "ATM", "HQ", "US", "UK"}
        for p in parts:
            if p.upper() in acronyms:
                normalized_parts.append(p.upper())
            else:
                normalized_parts.append(p.capitalize())
        return " ".join(normalized_parts)

    @classmethod
    def parse_datetime(cls, date_val: Any, time_val: Any = None) -> Optional[datetime]:
        """
        Parses mixed-format dates and times into a timezone-aware UTC datetime.
        Rejects unparseable strings, missing dates, or implausible future/past dates.
        """
        date_str = cls.clean_string(date_val)
        time_str = cls.clean_string(time_val)

        if not date_str:
            return None

        combo_str = f"{date_str} {time_str}".strip()

        try:
            parsed = date_parser.parse(combo_str, fuzzy=False)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            
            # Boundary checks: between year 1990 and 2035
            if parsed.year < 1990 or parsed.year > 2035:
                return None

            return parsed
        except Exception:
            return None

    @classmethod
    def validate_coordinates(cls, lat_val: Any, lon_val: Any) -> Tuple[bool, Optional[float], Optional[float], str]:
        """
        Validates latitude and longitude coordinates.
        Ensures proper bounds and rejects Null Island (0.0, 0.0) placeholder anomalies.
        Returns: (is_valid, latitude, longitude, error_message)
        """
        if lat_val is None or lon_val is None:
            return False, None, None, "Coordinates cannot be null or empty"

        try:
            lat = float(lat_val)
            lon = float(lon_val)
        except (ValueError, TypeError):
            return False, None, None, f"Coordinates must be numeric (received lat={lat_val}, lon={lon_val})"

        if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
            return False, None, None, "Coordinates cannot be NaN or infinite"

        if lat < -90.0 or lat > 90.0:
            return False, None, None, f"Latitude {lat} is out of valid bounds [-90.0, 90.0]"

        if lon < -180.0 or lon > 180.0:
            return False, None, None, f"Longitude {lon} is out of valid bounds [-180.0, 180.0]"

        # Check for Null Island placeholder coords
        if abs(lat) < 0.0001 and abs(lon) < 0.0001:
            return False, None, None, "Coordinates (0.0, 0.0) indicate an unmapped placeholder / Null Island"

        return True, round(lat, 6), round(lon, 6), ""

    @classmethod
    def validate_and_clean_record(cls, raw: Dict[str, Any], row_num: Optional[int] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, str]]]:
        """
        Full validation and cleaning pass on a single dictionary record.
        Returns: (is_valid, cleaned_dict, error_info_dict)
        """
        # 1. Check Record ID
        raw_record_id = raw.get("record_id") or raw.get("id") or raw.get("crime_id")
        record_id = cls.clean_string(raw_record_id)
        if not record_id:
            return False, None, {
                "error_category": "MISSING_FIELD",
                "error_message": "Missing required field 'record_id'"
            }

        # 2. Check Crime Type & Canonical Category
        raw_type = raw.get("crime_type") or raw.get("type") or raw.get("offense")
        crime_type, category = cls.normalize_crime_type(raw_type)
        if not crime_type:
            return False, None, {
                "error_category": "MISSING_FIELD",
                "error_message": "Missing required field 'crime_type'"
            }

        # 3. Check Location Name
        raw_loc = raw.get("location") or raw.get("location_name") or raw.get("address")
        location_name = cls.normalize_location(raw_loc)
        if not location_name:
            return False, None, {
                "error_category": "MISSING_FIELD",
                "error_message": "Missing required field 'location'"
            }

        # 4. Check Date & Time
        date_val = raw.get("date") or raw.get("occurred_at") or raw.get("incident_date")
        time_val = raw.get("time") or raw.get("incident_time")
        occurred_at = cls.parse_datetime(date_val, time_val)
        if occurred_at is None:
            return False, None, {
                "error_category": "INVALID_DATE",
                "error_message": f"Invalid or unparseable date/time format: date='{date_val}', time='{time_val}'"
            }

        # 5. Check Coordinates
        lat_val = raw.get("latitude") or raw.get("lat")
        lon_val = raw.get("longitude") or raw.get("lon") or raw.get("lng")
        coords_valid, lat, lon, coord_err = cls.validate_coordinates(lat_val, lon_val)
        if not coords_valid:
            return False, None, {
                "error_category": "INVALID_COORDINATES",
                "error_message": coord_err
            }

        # 6. Source and Description
        source = cls.clean_string(raw.get("source")) or "Unknown Source"
        description = cls.clean_string(raw.get("description")) or None

        cleaned_record = {
            "record_id": record_id,
            "crime_type": crime_type,
            "category": category,
            "location_name": location_name,
            "occurred_at": occurred_at,
            "latitude": lat,
            "longitude": lon,
            "description": description,
            "source": source,
            "status": "VALID",
            "extra_metadata": {k: v for k, v in raw.items() if k not in {
                "record_id", "id", "crime_id", "crime_type", "type", "offense",
                "location", "location_name", "address", "date", "occurred_at",
                "incident_date", "time", "incident_time", "latitude", "lat",
                "longitude", "lon", "lng", "description", "source"
            }}
        }

        return True, cleaned_record, None
