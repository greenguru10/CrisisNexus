"""
NLP Service – Extracts structured data from raw NGO survey report text.

Uses spaCy for NER and rule-based keyword matching to identify:
  - Category (food, medical, water, shelter, clothing, sanitation, education)
  - Urgency (low, medium, high)
  - People affected (numeric extraction)
  - Location (NER + keyword fallback)
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Try loading spaCy model; fall back to rule-based only ────────

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    nlp = None
    logger.warning(
        "spaCy model not available – using rule-based NLP only. "
        "Run: python -m spacy download en_core_web_sm"
    )


# ── Keyword dictionaries ────────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food": ["food", "hunger", "hungry", "meal", "meals", "ration", "rations", "nutrition", "starvation", "feed", "feeding", "grain", "rice", "wheat"],
    "water": ["water", "drinking water", "clean water", "thirst", "dehydration", "purification", "well", "borewell", "pipeline"],
    "medical": ["medical", "medicine", "health", "doctor", "hospital", "injury", "injured", "disease", "epidemic", "vaccine", "clinic", "ambulance", "first aid", "surgical", "infection"],
    "shelter": ["shelter", "housing", "homeless", "tent", "tarp", "roof", "displaced", "evacuation", "camp", "accommodation"],
    "clothing": ["clothing", "clothes", "blanket", "blankets", "warm", "winter wear", "garments"],
    "sanitation": ["sanitation", "hygiene", "toilet", "latrine", "sewage", "waste", "disinfectant"],
    "education": ["education", "school", "books", "stationery", "teacher", "learning", "classroom"],
}

URGENCY_HIGH_KEYWORDS = [
    "urgent", "urgently", "emergency", "critical", "immediately", "asap",
    "dire", "desperate", "life-threatening", "severe", "crisis",
    "catastrophe", "catastrophic", "devastating", "acute",
]

URGENCY_MEDIUM_KEYWORDS = [
    "soon", "needed", "important", "moderate", "significant", "concern",
    "growing", "worsening", "rising",
]


# ── Public API ───────────────────────────────────────────────────

def extract_from_text(raw_text: str) -> dict:
    """
    Process raw survey text and return structured fields.

    Returns:
        dict with keys: category, urgency, people_affected, location
    """
    text_lower = raw_text.lower()

    category = _detect_category(text_lower)
    urgency = _detect_urgency(text_lower)
    people_affected = _extract_people_count(raw_text)
    location = _extract_location(raw_text)

    result = {
        "category": category,
        "urgency": urgency,
        "people_affected": people_affected,
        "location": location,
    }

    logger.info("NLP extraction result: %s", result)
    return result


# ── Private helpers ──────────────────────────────────────────────

def _detect_category(text_lower: str) -> str:
    """Detect the most relevant category via keyword scoring."""
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)  # type: ignore[arg-type]
    return "general"


def _detect_urgency(text_lower: str) -> str:
    """Classify urgency as high / medium / low based on keyword presence."""
    for word in URGENCY_HIGH_KEYWORDS:
        if word in text_lower:
            return "high"
    for word in URGENCY_MEDIUM_KEYWORDS:
        if word in text_lower:
            return "medium"
    return "low"


def _extract_people_count(text: str) -> int:
    """
    Extract the number of people affected from text.
    Looks for patterns like '200 families', '1500 people', '300 children'.
    """
    people_words = r"(?:people|persons|individuals|families|children|villagers|residents|victims|affected|refugees|inhabitants|survivors)"
    pattern = rf"(\d[\d,]*)\s*(?:\+\s*)?{people_words}"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        num_str = match.group(1).replace(",", "")
        return int(num_str)

    # Fallback: find any large number (>= 10)
    numbers = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", text)]
    large_numbers = [n for n in numbers if n >= 10]
    return max(large_numbers) if large_numbers else 0


def _extract_location(text: str) -> Optional[str]:
    """
    Extract location using spaCy NER (GPE/LOC entities).
    Falls back to rule-based matching against known city names.
    """
    if SPACY_AVAILABLE and nlp is not None:
        doc = nlp(text)
        locations = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
        if locations:
            return locations[0]

    # Rule-based fallback: check for known city names
    from utils.location_utils import CITY_COORDS

    text_lower = text.lower()
    for city in CITY_COORDS:
        if city in text_lower:
            return city.title()

    return None
