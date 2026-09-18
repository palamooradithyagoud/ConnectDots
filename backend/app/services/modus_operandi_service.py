import re
from typing import List, Dict, Any, Optional


class ModusOperandiService:
    """
    Extracts Modus Operandi (M.O.) behavioral patterns from crime narratives.
    Distinguishes between 'explicitly_stated' and 'inferred' behaviors.
    Prioritizes explicit evidence to prevent investigative hallucination.
    """

    # Explicit M.O. patterns mapped directly to descriptive phrases
    MO_RULES = [
        {
            "pattern": "Armed robbery",
            "regex": re.compile(r"\b(?:armed\s+with|weapon\s+threat|held\s+at\s+gunpoint|threatened\s+with\s+(?:a\s+)?(?:knife|gun|weapon)|brandishing\s+(?:a\s+)?(?:knife|gun|weapon)|robbed\s+.*?(?:using|with)\s+(?:a\s+)?(?:knife|gun|weapon|firearm|pistol))\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Forced entry",
            "regex": re.compile(r"\b(?:forced\s+entry|broke\s+open|lock\s+broken|doors?\s+pried\s+open|grill\s+cut|tampered\s+lock)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Breaking window / glass",
            "regex": re.compile(r"\b(?:breaking\s+(?:a\s+)?window|shattered\s+glass|glass\s+cut|smashed\s+windowpane)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Escape using vehicle",
            "regex": re.compile(r"\b(?:escaped\s+(?:in|on|using|via)|fled\s+on\s+(?:a\s+)?(?:motorcycle|bike|car|vehicle)|getaway\s+vehicle|speeding\s+away)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Overnight / Night burglary",
            "regex": re.compile(r"\b(?:overnight\s+break-in|burglary\s+at\s+night|under\s+cover\s+of\s+darkness|late\s+night\s+intrusion)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Chain / Purse snatching",
            "regex": re.compile(r"\b(?:snatching\s+of|snatched\s+(?:chain|purse|bag|phone|mobile)|grabbed\s+and\s+fled)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "ATM / Card skimming",
            "regex": re.compile(r"\b(?:card\s+skimming|atm\s+(?:tampering|skimmer)|cloned\s+card|unauthorized\s+atm\s+debit)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Online phishing & impersonation",
            "regex": re.compile(r"\b(?:phishing\s+(?:email|link|scam)|fake\s+(?:website|portal|identity)|impersonating|otp\s+(?:fraud|theft))\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Threatening victim",
            "regex": re.compile(r"\b(?:threatened\s+(?:the\s+)?(?:victim|shopkeeper|clerk|cashier|pedestrian)|verbal\s+threats|hostage)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Public property defacement",
            "regex": re.compile(r"\b(?:graffiti|defaced|spray\s+paint|smashed\s+(?:signage|shelter|bench|cctv)|vandalized)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Illicit substance trafficking / possession",
            "regex": re.compile(r"\b(?:possession\s+of\s+illicit|drug\s+(?:peddling|distribution|trafficking)|synthetic\s+substances|contraband)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
        {
            "pattern": "Physical assault during encounter",
            "regex": re.compile(r"\b(?:physical\s+altercation|punched|struck|inflicted\s+injuries|beaten\s+up|assaulted\s+during)\b", re.IGNORECASE),
            "certainty": "explicitly_stated"
        },
    ]

    @classmethod
    def extract_modus_operandi(cls, text: Optional[str]) -> List[Dict[str, Any]]:
        """
        Extracts structured M.O. patterns with evidence spans and certainty levels.
        """
        if not text or not text.strip():
            return []

        results: List[Dict[str, Any]] = []
        found_patterns = set()

        for rule in cls.MO_RULES:
            match = rule["regex"].search(text)
            if match and rule["pattern"] not in found_patterns:
                results.append({
                    "pattern": rule["pattern"],
                    "certainty": rule["certainty"],
                    "matched_text": match.group(0).strip(),
                })
                found_patterns.add(rule["pattern"])

        return results
