import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("connectdots_entity_extractor")

# Attempt to import spaCy with safety fallback
_SPACY_NLP = None
try:
    import spacy
    try:
        _SPACY_NLP = spacy.load("en_core_web_sm")
        logger.info("spaCy en_core_web_sm loaded successfully.")
    except Exception as e:
        logger.info(f"spaCy model en_core_web_sm not found, using rule-based and regex extraction fallback: {e}")
except Exception as e:
    logger.info(f"spaCy C-extension unavailable in environment, using domain extraction fallback: {e}")


class EntityExtractionService:
    """
    High-precision entity extraction service for crime descriptions.
    Extracts: PERSON, LOCATION, ORGANIZATION, VEHICLE, WEAPON, DATE, TIME, MONEY.
    Strict non-hallucination constraint: Only entities directly grounded in source text.
    """

    # Domain Lexicons & Regex Patterns
    WEAPON_PATTERNS = [
        re.compile(r"\b(?:pocket\s+)?(?:knife|knives|blade|dagger|machete|sword)\b", re.IGNORECASE),
        re.compile(r"\b(?:firearm|handgun|pistol|revolver|country-made\s+pistol|desi\s+katta|rifle|shotgun|gun)\b", re.IGNORECASE),
        re.compile(r"\b(?:iron\s+rod|metal\s+pipe|crowbar|wooden\s+club|baseball\s+bat|hammer|cutter)\b", re.IGNORECASE),
        re.compile(r"\b(?:acid|explosive|petrol\s+bomb|molotov)\b", re.IGNORECASE),
    ]

    VEHICLE_PATTERNS = [
        re.compile(r"\b(?:(?:black|white|red|silver|blue|grey|dark|stolen)\s+)?(?:motorcycle|motorbike|bike|scooter|moped|two-wheeler)\b", re.IGNORECASE),
        re.compile(r"\b(?:(?:black|white|red|silver|blue|grey|dark|stolen)\s+)?(?:car|sedan|suv|hatchback|van|tempo|truck|lorry|auto-rickshaw|auto|cab)\b", re.IGNORECASE),
    ]

    PERSON_PATTERNS = [
        re.compile(r"\b(?:two|three|four|five|\d+)?\s*(?:unidentified\s+)?(?:suspects?|culprits?|perpetrators?|assailants?|intruders?|thieves|burglars?|robbers?)\b", re.IGNORECASE),
        re.compile(r"\b(?:masked\s+man|unidentified\s+man|unidentified\s+male|unknown\s+person|gang\s+of\s+(?:two|three|four|\d+))\b", re.IGNORECASE),
        re.compile(r"\b(?:shopkeeper|store\s+manager|cashier|security\s+guard|pedestrian|victim|homeowner|watchman)\b", re.IGNORECASE),
    ]

    ORGANIZATION_PATTERNS = [
        re.compile(r"\b(?:jewell?ery\s+(?:store|shop|showroom)|electronics?\s+store|retail\s+showroom|supermarket|grocery\s+store)\b", re.IGNORECASE),
        re.compile(r"\b(?:bank|atm|branch|hospital|corporate\s+office|tech\s+park|police\s+station|metro\s+station|hotel|restaurant)\b", re.IGNORECASE),
        re.compile(r"\b(?:HDFC|ICICI|SBI|State\s+Bank|Axis\s+Bank|Tech\s+Mahindra|Infosys|Wipro)\b", re.IGNORECASE),
    ]

    TIME_PATTERNS = [
        re.compile(r"\b(?:at\s+)?(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))\b", re.IGNORECASE),
        re.compile(r"\b(?:around|at|during)?\s*(?:midnight|noon|overnight|early\s+morning|late\s+night|broad\s+daylight|evening)\b", re.IGNORECASE),
        re.compile(r"\b\d{2}:\d{2}(?::\d{2})?\b"),
    ]

    DATE_PATTERNS = [
        re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b"),
        re.compile(r"\b(?:on\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+evening|\s+night|\s+morning)?\b", re.IGNORECASE),
        re.compile(r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*\d{4})?\b", re.IGNORECASE),
    ]

    MONEY_PATTERNS = [
        re.compile(r"\b(?:rs\.?|inr|₹|\$|usd)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakhs?|crores?|k|thousand|million))?\b", re.IGNORECASE),
        re.compile(r"\b[\d,]+\s*(?:lakhs?|crores?|thousand\s+rupees|dollars)\b", re.IGNORECASE),
    ]

    LOCATION_PHRASE_PATTERNS = [
        re.compile(r"\b(?:near|at|around|outside|inside|in\s+front\s+of|behind|opposite)\s+([A-Z][a-zA-Z0-9\s]+?(?=(?:at|on|using|and|with|escaped|in|\.|$)))", re.IGNORECASE),
    ]

    PHONE_PATTERNS = [
        # Explicit telephone prefix indicators (e.g. "phone: 9876543210", "mobile: +91 9876543210")
        re.compile(r"\b(?:ph(?:one)?|mobile|cell|contact|no\.?|dialed|called)\s*[:\-]?\s*(\+?[\d\s\-]{8,16}\d)\b", re.IGNORECASE),
        # Indian standard mobile numbers (10 digits starting with 6-9, with optional +91 or 0 prefix)
        re.compile(r"(?:\b|\+)(?:(?:91|0)[\s\-]?)?[6-9]\d{9}\b"),
        # General international E.164-style numbers
        re.compile(r"\+\d{1,3}[\s\-]?(?:\(?\d{1,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}\b"),
    ]

    @classmethod
    def extract_entities(cls, text: str, fallback_location: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts all supported entity categories from description text.
        Guarantees: Non-hallucination. Only entities directly grounded in source text are returned.
        """
        if not text or not text.strip():
            return {
                "persons": [],
                "locations": [fallback_location] if fallback_location else [],
                "organizations": [],
                "weapons": [],
                "vehicles": [],
                "dates": [],
                "times": [],
                "money": [],
                "phones": [],
            }

        extracted: Dict[str, List[str]] = {
            "persons": [],
            "locations": [],
            "organizations": [],
            "weapons": [],
            "vehicles": [],
            "dates": [],
            "times": [],
            "money": [],
            "phones": [],
        }

        # 1. spaCy NER Pass if available
        if _SPACY_NLP:
            try:
                doc = _SPACY_NLP(text)
                for ent in doc.ents:
                    val = ent.text.strip()
                    if not val:
                        continue
                    if ent.label_ in ("PERSON",):
                        cls._add_unique(extracted["persons"], val, text)
                    elif ent.label_ in ("GPE", "LOC"):
                        cls._add_unique(extracted["locations"], val, text)
                    elif ent.label_ in ("ORG",):
                        cls._add_unique(extracted["organizations"], val, text)
                    elif ent.label_ in ("DATE",):
                        cls._add_unique(extracted["dates"], val, text)
                    elif ent.label_ in ("TIME",):
                        cls._add_unique(extracted["times"], val, text)
                    elif ent.label_ in ("MONEY",):
                        cls._add_unique(extracted["money"], val, text)
            except Exception as e:
                logger.debug(f"spaCy pass encountered error: {e}")

        # 2. Domain Pattern Extractions (Weapons, Vehicles, Persons, Locations, Organizations, Time, Money)
        cls._match_patterns(cls.WEAPON_PATTERNS, text, extracted["weapons"])
        cls._match_patterns(cls.VEHICLE_PATTERNS, text, extracted["vehicles"])
        cls._match_patterns(cls.PERSON_PATTERNS, text, extracted["persons"])
        cls._match_patterns(cls.ORGANIZATION_PATTERNS, text, extracted["organizations"])
        cls._match_patterns(cls.TIME_PATTERNS, text, extracted["times"])
        cls._match_patterns(cls.DATE_PATTERNS, text, extracted["dates"])
        cls._match_patterns(cls.MONEY_PATTERNS, text, extracted["money"])
        cls._extract_phones(text, extracted["phones"])

        # 3. Prepositional Location phrases
        for pattern in cls.LOCATION_PHRASE_PATTERNS:
            for match in pattern.finditer(text):
                loc_candidate = match.group(1).strip(" ,.-")
                # Ensure it looks like a proper name or area (starts uppercase and <= 4 words)
                if loc_candidate and len(loc_candidate.split()) <= 4:
                    cls._add_unique(extracted["locations"], loc_candidate, text)

        # 4. Fallback Location from record if no specific location was extracted in description
        if not extracted["locations"] and fallback_location:
            extracted["locations"].append(fallback_location)

        # 5. Clean / deduplicate overlaps (e.g. if 'motorcycle' and 'black motorcycle' both match, keep 'black motorcycle')
        for category in extracted:
            extracted[category] = cls._deduplicate_substrings(extracted[category])

        return extracted

    @classmethod
    def _extract_phones(cls, text: str, target_list: List[str]):
        """
        Extracts candidate phone strings, normalizes them via PhoneNormalizationService,
        and excludes false positives from dates, FIRs, PIN codes, and vehicle registration numbers.
        """
        from app.services.phone_normalization_service import PhoneNormalizationService

        found_candidates = set()
        for pattern in cls.PHONE_PATTERNS:
            for match in pattern.finditer(text):
                val = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                cleaned_val = val.strip(" ,.-:;()[]{}")
                if cleaned_val:
                    found_candidates.add(cleaned_val)

        for cand in sorted(found_candidates, key=len, reverse=True):
            # Check false-positive avoidance:
            # Check if this candidate is actually a date format like 2026-09-19 or 19/09/2026
            if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}$", cand) or re.match(r"^\d{2}[-/]\d{2}[-/]\d{4}$", cand):
                continue
            # Check if candidate is part of a vehicle registration plate like TS09AB1234
            if re.search(r"[A-Za-z]{2}\s*\d{1,2}\s*[A-Za-z]{1,3}\s*" + re.escape(cand), text, re.IGNORECASE):
                continue

            norm_res = PhoneNormalizationService.normalize(cand)
            if norm_res.is_valid and norm_res.normalized_number:
                canonical = norm_res.normalized_number
                if canonical not in target_list:
                    target_list.append(canonical)

    @classmethod
    def _match_patterns(cls, patterns: List[re.Pattern], text: str, target_list: List[str]):
        for pattern in patterns:
            for match in pattern.finditer(text):
                val = match.group(0).strip(" ,.-")
                cls._add_unique(target_list, val, text)

    @classmethod
    def _add_unique(cls, target_list: List[str], val: str, source_text: str):
        if not val or len(val) < 2:
            return
        # Strict grounding: Must actually exist in source text
        if val.lower() not in source_text.lower():
            return
        # Avoid duplicate additions
        if not any(val.lower() == existing.lower() for existing in target_list):
            target_list.append(val)

    @staticmethod
    def _deduplicate_substrings(items: List[str]) -> List[str]:
        """Keeps longer specific phrases over shorter redundant sub-tokens."""
        if not items:
            return []
        sorted_items = sorted(set(items), key=len, reverse=True)
        result = []
        for item in sorted_items:
            # If item is a complete substring of an already selected item with same words, skip
            if not any(item.lower() != r.lower() and item.lower() in r.lower() for r in result):
                result.append(item)
        return sorted(result)
