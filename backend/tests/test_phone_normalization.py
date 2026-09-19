"""
Phase 4 Telecommunications: Phone Normalization Unit Tests
Tests E.164 canonicalization, region inference, dummy sequence rejection,
and false-positive avoidance across formatting styles.
"""
import pytest
from app.services.phone_normalization_service import PhoneNormalizationService, PhoneNormalizationResult


def test_valid_indian_number_variations():
    """All common Indian phone representations must resolve to the identical E.164 canonical string."""
    canonical = "+919876543210"
    variations = [
        "+91 9876543210",
        "+91-9876543210",
        "919876543210",
        "09876543210",
        "9876543210",
        "+91 98765-43210",
        "098765 43210",
        "(+91) 9876543210",
    ]

    for val in variations:
        res = PhoneNormalizationService.normalize(val)
        assert res.is_valid is True, f"Failed on valid representation: {val} (error: {res.error_message})"
        assert res.normalized_number == canonical
        assert res.country_code == "91"
        assert res.national_number == "9876543210"
        assert res.number_type in ("MOBILE", "FIXED_OR_MOBILE")


def test_valid_international_numbers():
    """International numbers with explicit country codes must be accurately parsed and formatted."""
    us_res = PhoneNormalizationService.normalize("+1 650 253 0000")
    assert us_res.is_valid is True
    assert us_res.normalized_number == "+16502530000"
    assert us_res.country_code == "1"

    uk_res = PhoneNormalizationService.normalize("+44 20 7946 0958")
    assert uk_res.is_valid is True
    assert uk_res.normalized_number == "+442079460958"
    assert uk_res.country_code == "44"


def test_malformed_and_dummy_numbers_rejected():
    """Short numbers, letters, and dummy sequences must be safely rejected."""
    invalid_inputs = [
        "",
        None,
        "   ",
        "123",
        "12345",
        "abcdefghij",
        "0000000000",
        "1111111111",
        "9999999999",
        "++919876543210",
    ]

    for inv in invalid_inputs:
        res = PhoneNormalizationService.normalize(inv)
        assert res.is_valid is False, f"Expected invalid for '{inv}', got valid: {res.normalized_number}"
        assert res.normalized_number is None
        assert res.error_message is not None


def test_false_positive_numerical_strings():
    """Dates, PIN codes, and case numbers must NOT be accepted as valid phone numbers."""
    non_phones = [
        "2026-09-19",
        "19/09/2026",
        "20260919",
        "500034",           # 6-digit Indian PIN code
        "110001",           # Delhi PIN code
        "Section 420",
        "CR-2026-014",
    ]

    for np_val in non_phones:
        res = PhoneNormalizationService.normalize(np_val)
        assert res.is_valid is False, f"Non-phone '{np_val}' should not be valid, got {res.normalized_number}"


def test_is_valid_phone_helper():
    """Convenience boolean helper method works as expected."""
    assert PhoneNormalizationService.is_valid_phone("9876543210") is True
    assert PhoneNormalizationService.is_valid_phone("00000") is False
