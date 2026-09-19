"""
Phase 4 Telecommunications: Phone Normalization Service
Uses Google's libphonenumber (via python phonenumbers) to reliably parse, validate,
and normalize phone numbers into E.164 canonical format.
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberType, PhoneNumberFormat

logger = logging.getLogger("connectdots_phone_norm")


@dataclass
class PhoneNormalizationResult:
    is_valid: bool
    raw_input: str
    normalized_number: Optional[str] = None     # Canonical E.164, e.g. +919876543210
    country_code: Optional[str] = None          # e.g. "91"
    national_number: Optional[str] = None      # e.g. "9876543210"
    number_type: Optional[str] = None          # MOBILE, FIXED_LINE, VOIP, etc.
    carrier: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "raw_input": self.raw_input,
            "normalized_number": self.normalized_number,
            "country_code": self.country_code,
            "national_number": self.national_number,
            "number_type": self.number_type,
            "error_message": self.error_message,
        }


class PhoneNormalizationService:
    """
    Production-grade telephone number parser and canonicalizer.
    Extensible across international regions, default: 'IN' (India).
    """
    DEFAULT_REGION = "IN"

    TYPE_MAPPING = {
        PhoneNumberType.FIXED_LINE: "FIXED_LINE",
        PhoneNumberType.MOBILE: "MOBILE",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_OR_MOBILE",
        PhoneNumberType.TOLL_FREE: "TOLL_FREE",
        PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
        PhoneNumberType.SHARED_COST: "SHARED_COST",
        PhoneNumberType.VOIP: "VOIP",
        PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
        PhoneNumberType.PAGER: "PAGER",
        PhoneNumberType.UAN: "UAN",
        PhoneNumberType.VOICEMAIL: "VOICEMAIL",
        PhoneNumberType.UNKNOWN: "UNKNOWN",
    }

    @classmethod
    def normalize(cls, raw_input: Any, default_region: Optional[str] = None) -> PhoneNormalizationResult:
        """
        Parses and standardizes any raw phone input string.
        Guarantees:
        - Never silently turns an invalid number into a valid one.
        - Preserves country code and E.164 standard formatting.
        - Filters dummy / repeated / implausible sequences.
        """
        if raw_input is None:
            return PhoneNormalizationResult(
                is_valid=False,
                raw_input="",
                error_message="Phone number value is empty or null"
            )

        raw_str = str(raw_input).strip()
        if not raw_str:
            return PhoneNormalizationResult(
                is_valid=False,
                raw_input="",
                error_message="Phone number string is empty"
            )

        region = (default_region or cls.DEFAULT_REGION).upper().strip()

        # Reject malformed '+' usage (e.g. multiple '+' or '+' not at start)
        if raw_str.count("+") > 1 or ("+" in raw_str and not raw_str.lstrip(" (").startswith("+")):
            return PhoneNormalizationResult(
                is_valid=False,
                raw_input=raw_str,
                error_message=f"Malformed plus '+' symbol in phone number '{raw_str}'"
            )

        # Clean non-digit / non-plus characters
        cleaned = re.sub(r"[^\d+]", "", raw_str)
        if not cleaned:
            return PhoneNormalizationResult(
                is_valid=False,
                raw_input=raw_str,
                error_message="No numeric digits found in input"
            )

        # Pre-process Indian 12-digit format without '+' (e.g. 919876543210 -> +919876543210)
        parseable_str = cleaned
        if not parseable_str.startswith("+") and len(parseable_str) == 12 and parseable_str.startswith("91"):
            parseable_str = "+" + parseable_str

        # Reject obvious dummy repetitive sequences like 0000000000, 9999999999, 1234567890
        digits_only = re.sub(r"\D", "", cleaned)
        if len(digits_only) >= 8 and len(set(digits_only)) == 1:
            return PhoneNormalizationResult(
                is_valid=False,
                raw_input=raw_str,
                error_message=f"Rejected repetitive dummy number sequence '{raw_str}'"
            )

        try:
            parsed = phonenumbers.parse(parseable_str, region)
        except NumberParseException as e:
            return PhoneNormalizationResult(
                is_valid=False,
                raw_input=raw_str,
                error_message=f"Parse error: {e}"
            )

        if not phonenumbers.is_possible_number(parsed):
            return PhoneNormalizationResult(
                is_valid=False,
                raw_input=raw_str,
                error_message="Number length or structure is implausible"
            )

        if not phonenumbers.is_valid_number(parsed):
            return PhoneNormalizationResult(
                is_valid=False,
                raw_input=raw_str,
                error_message="Number is not a valid recognized telephone number for its region"
            )

        # Retrieve E.164 canonical representation
        e164_str = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        c_code = str(parsed.country_code)
        nat_num = str(parsed.national_number)
        num_type_enum = phonenumbers.number_type(parsed)
        num_type = cls.TYPE_MAPPING.get(num_type_enum, "UNKNOWN")

        return PhoneNormalizationResult(
            is_valid=True,
            raw_input=raw_str,
            normalized_number=e164_str,
            country_code=c_code,
            national_number=nat_num,
            number_type=num_type,
            error_message=None
        )

    @classmethod
    def is_valid_phone(cls, raw_input: Any, default_region: Optional[str] = None) -> bool:
        """Quick boolean test."""
        return cls.normalize(raw_input, default_region).is_valid
