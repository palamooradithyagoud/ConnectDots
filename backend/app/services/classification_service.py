import re
import math
from typing import Dict, Any, Tuple, Optional
from app.core.config import settings


class ClassificationService:
    """
    Classifies incident descriptions into the 10 canonical crime categories.
    Computes confidence score and flags cases needing human review.
    Preserves original classification without mutation.
    """

    CATEGORIES = [
        "THEFT",
        "BURGLARY",
        "ROBBERY",
        "ASSAULT",
        "HOMICIDE",
        "VEHICLE_THEFT",
        "FRAUD",
        "CYBERCRIME",
        "NARCOTICS",
        "VANDALISM",
    ]

    # Keyword / feature indicators for each canonical category with importance weights
    CATEGORY_INDICATORS = {
        "HOMICIDE": {
            "patterns": [r"\bfatal\b", r"\bmurder\b", r"\bhomicide\b", r"\bkilled\b", r"\bdead\b", r"\bstabbed\s+to\s+death\b", r"\bcorpse\b", r"\bloss\s+of\s+life\b"],
            "weight": 3.0
        },
        "ROBBERY": {
            "patterns": [r"\brobbed\b", r"\brobbery\b", r"\bgunpoint\b", r"\bweapon\s+threat\b", r"\bknife\s+threat\b", r"\bheld\s+up\b", r"\bmugged\b", r"\bsnatching\s+with\s+weapon\b", r"\bextortion\b", r"\barmed\b"],
            "weight": 2.5
        },
        "BURGLARY": {
            "patterns": [r"\bbreak-in\b", r"\bbreaking\s+in\b", r"\bforced\s+entry\b", r"\bbroke\s+open\b", r"\bovernight\b", r"\bburglary\b", r"\bburglar\b", r"\bintruder\b", r"\btampered\s+lock\b", r"\balarm\s+triggered\b"],
            "weight": 2.2
        },
        "VEHICLE_THEFT": {
            "patterns": [r"\bmotorcycle\s+stolen\b", r"\bbike\s+stolen\b", r"\bvehicle\s+theft\b", r"\bcar\s+stolen\b", r"\bauto\s+theft\b", r"\bstolen\s+from\s+driveway\b", r"\bstolen\s+from\s+parking\b", r"\bstolen\s+(?:car|scooter|bike|motorcycle|suv)\b"],
            "weight": 2.5
        },
        "ASSAULT": {
            "patterns": [r"\bassault\b", r"\bphysical\s+altercation\b", r"\bfight\b", r"\bpunched\b", r"\battacked\b", r"\bbeaten\b", r"\binjuries\b", r"\bbattered\b", r"\bhospitalized\b", r"\bbrawl\b"],
            "weight": 2.2
        },
        "CYBERCRIME": {
            "patterns": [r"\bphishing\b", r"\bmalware\b", r"\bransomware\b", r"\bhacked\b", r"\bcyber\b", r"\botp\s+theft\b", r"\bdata\s+breach\b", r"\bserver\b", r"\bonline\s+fraud\b", r"\bidentity\s+theft\b", r"\bsocial\s+engineering\b"],
            "weight": 2.5
        },
        "FRAUD": {
            "patterns": [r"\bskimming\b", r"\bcredit\s+card\b", r"\bdebit\s+card\b", r"\bunauthorized\s+atm\b", r"\bforgery\b", r"\bponzi\b", r"\bcheated\b", r"\bembezzlement\b", r"\bcounterfeit\b", r"\bfraud\b"],
            "weight": 2.2
        },
        "NARCOTICS": {
            "patterns": [r"\bnarcotics\b", r"\bdrugs\b", r"\bcontraband\b", r"\bsynthetic\s+substances\b", r"\bpossession\s+of\s+illicit\b", r"\bganja\b", r"\bcocaine\b", r"\bheroin\b", r"\bpeddling\b", r"\bmeth\b"],
            "weight": 2.8
        },
        "VANDALISM": {
            "patterns": [r"\bvandalism\b", r"\bvandalized\b", r"\bdefaced\b", r"\bgraffiti\b", r"\bshattered\s+glass\b", r"\bdamage\s+to\s+public\b", r"\bproperty\s+damage\b", r"\bbroken\s+shelter\b", r"\bbroken\s+signage\b"],
            "weight": 2.2
        },
        "THEFT": {
            "patterns": [r"\btheft\b", r"\bstolen\b", r"\bstealing\b", r"\bpickpocket\b", r"\bshoplifting\b", r"\bsnatched\b", r"\blarceny\b", r"\btook\b", r"\bmissing\b", r"\bpurloined\b"],
            "weight": 1.5
        },
    }

    @classmethod
    def classify(
        cls,
        text: Optional[str],
        original_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predicts canonical category and returns confidence score.
        Never mutates the original_category.
        """
        if not text or not text.strip():
            # If no text description is provided, fall back to existing category if valid, else review
            fallback = original_category.upper() if original_category in cls.CATEGORIES else "THEFT"
            return {
                "predicted_category": fallback,
                "confidence": 0.50,
                "needs_review": True,
                "scores": {c: 0.1 for c in cls.CATEGORIES}
            }

        scores: Dict[str, float] = {cat: 0.05 for cat in cls.CATEGORIES}
        lower_text = text.lower()

        # Score based on indicator matches
        for cat, config in cls.CATEGORY_INDICATORS.items():
            cat_weight = config["weight"]
            for pattern_str in config["patterns"]:
                if re.search(pattern_str, lower_text):
                    scores[cat] += cat_weight

        # Softmax normalization to derive calibrated probabilities
        max_score = max(scores.values())
        exp_scores = {k: math.exp(v - max_score) for k, v in scores.items()}
        sum_exp = sum(exp_scores.values())
        probabilities = {k: round(v / sum_exp, 4) for k, v in exp_scores.items()}

        best_category = max(probabilities, key=probabilities.get)
        confidence = probabilities[best_category]

        # Prioritize high-signal category matches
        # If confidence is below threshold, flag needs_review
        needs_review = confidence < settings.NLP_CONFIDENCE_THRESHOLD

        return {
            "predicted_category": best_category,
            "confidence": float(confidence),
            "needs_review": needs_review,
            "probabilities": probabilities,
        }
