import re
import unicodedata
from typing import Optional


class TextPreprocessor:
    """
    Dedicated NLP text preprocessing service for crime narratives.
    Prepares text for entity extraction, classification, and embeddings.
    CRITICAL RULE: Never mutates the original source description.
    """

    # Common police log / dispatch boilerplates to clean
    BOILERPLATE_PATTERNS = [
        re.compile(r"^\s*(?:incident\s+report|police\s+log|dispatch\s+note|case\s+summary)\s*:\s*", re.IGNORECASE),
        re.compile(r"\s*(?:investigation\s+underway|fir\s+registered|report\s+filed|pending\s+investigation)\.?\s*$", re.IGNORECASE),
    ]

    @classmethod
    def clean(cls, text: Optional[str]) -> str:
        """
        Cleans and normalizes crime narrative text.
        Returns a clean string, or empty string if input is null/empty.
        """
        if not text:
            return ""

        # 1. Unicode Normalization: decompose and strip combining diacritical marks
        normalized = unicodedata.normalize("NFKD", text)
        cleaned = "".join(
            ch for ch in normalized
            if not unicodedata.combining(ch) and (unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t", " "))
        )

        # 3. Strip boilerplate headers/trailers
        for pattern in cls.BOILERPLATE_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        # 4. Standardize dashes, quotes, and bullet points
        cleaned = re.sub(r"[‘’‚‛`]", "'", cleaned)
        cleaned = re.sub(r"[“”„‟]", '"', cleaned)
        cleaned = re.sub(r"[—–−]", "-", cleaned)

        # 5. Normalize repeated spaces, tabs, and newlines
        cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)

        # 6. Normalize punctuation spacing (e.g., "knife , and" -> "knife, and")
        cleaned = re.sub(r"\s+([,.:;?!])", r"\1", cleaned)

        # 7. Strip surrounding whitespace
        cleaned = cleaned.strip()

        return cleaned

    @classmethod
    def normalize_for_matching(cls, text: Optional[str]) -> str:
        """Lowercased and punctuation-trimmed version for exact token/lemma matches."""
        cleaned = cls.clean(text)
        return cleaned.lower()
