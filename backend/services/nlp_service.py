"""
NLP Service – Extracts structured data from raw NGO survey report text.

Pipeline:
  1. Preprocess: lowercase, strip extra spaces, expand slang/mixed-language
  2. Category:   keyword scoring → top match + secondary mention list
  3. Description: first 1–2 meaningful sentences from original text
  4. Urgency:    tiered keyword detection (high → medium → low)
  5. People:     regex extraction from preprocessed text → fallback = 5
  6. Location:   spaCy NER → city-list fallback
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Try loading spaCy model; fall back to rule-based only ─────────

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


# ── Slang / mixed-language expansion map ─────────────────────────

SLANG_MAP: list[tuple[str, str]] = [
    # Numbers / quantity
    (r'\bppl\b',            'people'),
    (r'\bprsns?\b',         'persons'),
    (r'\bpax\b',            'people'),

    # Food-related
    (r'\bkhana\b',          'food'),
    (r'\bbhojan\b',         'food'),
    (r'\bkhane\b',          'food'),
    (r'\bkhaana\b',         'food'),
    (r'\anaj\b',            'grain'),

    # Water-related
    (r'\bpaani\b',          'water'),
    (r'\bpani\b',           'water'),
    (r'\bjal\b',            'water'),
    (r'\bneer\b',           'water'),

    # Medical-related
    (r'\bdawa\b',           'medicine'),
    (r'\bdawai\b',          'medicine'),
    (r'\bdawaee\b',         'medicine'),
    (r'\bbimaar\b',         'sick'),
    (r'\bbukhaar\b',        'fever'),

    # Clothing
    (r'\bkapde\b',          'clothes'),
    (r'\bkapdein\b',        'clothes'),

    # Urgency shorthand
    (r'\burgo\b',           'urgent'),
    (r'\burgt\b',           'urgent'),
    (r'\basap\b',           'immediately'),
    (r'\bplz\b',            'please'),
    (r'\bpls\b',            'please'),
    (r'\bv\.?urgent\b',     'very urgent'),
    (r'\bsos\b',            'emergency'),

    # Common abbreviations
    (r'\bapprox\.?\b',      'approximately'),
    (r'\bw/\b',             'with'),
    (r'\b&\b',              'and'),
    (r'\bno\.?\b',          'number'),
    (r'\bvol\b',            'volunteer'),
    (r'\brel\s*camp\b',     'relief camp'),
]


# ── Category keyword dictionary ───────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food": [
        "food", "hunger", "hungry", "meal", "meals", "ration", "rations",
        "nutrition", "starvation", "starving", "feed", "feeding", "grain",
        "rice", "wheat", "dal", "groceries", "provisions", "supplies",
        "biscuit", "biscuits", "relief food", "dry food",
    ],
    "water": [
        "water", "drinking water", "clean water", "safe water", "thirst",
        "dehydration", "purification", "well", "borewell", "pipeline",
        "tanker", "waterborne", "contaminated water", "flood water",
    ],
    "medical": [
        "medical", "medicine", "medicines", "health", "doctor", "hospital",
        "injury", "injured", "disease", "epidemic", "vaccine", "vaccination",
        "clinic", "ambulance", "first aid", "surgical", "infection",
        "fever", "ill", "illness", "pain", "sick", "cholera", "malaria",
        "diarrhea", "wound", "wounds", "treatment", "nurse", "icu", "oxygen",
    ],
    "shelter": [
        "shelter", "housing", "homeless", "tent", "tarp", "tarpaulin",
        "roof", "displaced", "evacuation", "camp", "accommodation",
        "house", "home", "relief camp", "temporary shelter", "flood victims",
    ],
    "clothing": [
        "clothing", "clothes", "blanket", "blankets", "warm", "winter wear",
        "garments", "jacket", "jackets", "socks", "shoes", "saree", "dhoti",
    ],
    "sanitation": [
        "sanitation", "hygiene", "toilet", "latrine", "sewage", "waste",
        "disinfectant", "soap", "sanitizer", "open defecation", "flush",
        "drainage", "garbage", "trash",
    ],
    "education": [
        "education", "school", "children school", "books", "stationery",
        "teacher", "learning", "classroom", "students", "tuition",
    ],
    "logistics": [
        "transport", "transportation", "vehicle", "truck", "road",
        "delivery", "boat", "helicopter", "access", "route", "bridge",
        "distribution",
    ],
}

URGENCY_HIGH_KEYWORDS = [
    "urgent", "urgently", "emergency", "critical", "immediately",
    "asap", "right now", "life threatening", "life-threatening",
    "dire", "desperate", "severe", "crisis", "catastrophe",
    "catastrophic", "devastating", "acute", "sos", "no time",
    "very urgent", "extremely urgent", "mass casualty",
]

URGENCY_MEDIUM_KEYWORDS = [
    "soon", "needed", "necessary", "required", "important", "moderate",
    "significant", "concern", "growing", "worsening", "rising",
    "deteriorating", "increasing", "shortage", "need",
]


# ── Public API ────────────────────────────────────────────────────

def _preprocess_text(raw_text: str) -> str:
    """
    Standardize messy field text:
      - lowercase
      - collapse multiple whitespace / newlines to single space
      - expand slang and mixed-language terms
    """
    text = raw_text.lower()
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()

    for pattern, replacement in SLANG_MAP:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def extract_from_text(raw_text: str) -> dict:
    """
    Process raw survey text and return structured fields.

    Returns:
        dict with keys: category, urgency, people_affected, location
    """
    if not raw_text or not raw_text.strip():
        logger.warning("Empty input text received – returning defaults.")
        return {
            "category": "general",
            "urgency": "medium",
            "people_affected": 5,
            "location": None,
        }

    preprocessed = _preprocess_text(raw_text)

    category        = _detect_category(preprocessed)
    urgency         = _detect_urgency(preprocessed)
    people_affected = _extract_people_count(preprocessed)
    location        = _extract_location(raw_text)

    result = {
        "category":        category,
        "urgency":         urgency,
        "people_affected": people_affected,
        "location":        location,
    }

    logger.info("NLP extraction → %s", result)
    return result


# ── Private helpers ───────────────────────────────────────────────

def _detect_category(preprocessed: str) -> str:
    """
    Score each category by counting matched keywords.
    Returns the highest-scoring category, defaulting to 'general'.
    """
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        # Use word-boundary matching for short keywords to avoid false positives
        score = 0
        for kw in keywords:
            # Multi-word keywords use simple substring; single words use \b
            if ' ' in kw:
                score += preprocessed.count(kw)
            else:
                score += len(re.findall(rf'\b{re.escape(kw)}\b', preprocessed))
        if score > 0:
            scores[category] = score

    if not scores:
        return "general"

    best = max(scores, key=scores.get)   # type: ignore[arg-type]
    logger.debug("Category scores: %s → picked '%s'", scores, best)
    return best


def _detect_urgency(preprocessed: str) -> str:
    """
    Classify urgency as high / medium / low.
    Checks high-urgency keywords first; falls back to medium.
    """
    for phrase in URGENCY_HIGH_KEYWORDS:
        if re.search(rf'\b{re.escape(phrase)}\b', preprocessed):
            return "high"

    for phrase in URGENCY_MEDIUM_KEYWORDS:
        if re.search(rf'\b{re.escape(phrase)}\b', preprocessed):
            return "medium"

    # Rational default: unknown field reports lean medium, not low
    return "medium"


def _extract_people_count(preprocessed: str) -> int:
    """
    Extract the number of people affected.

    Priority:
      1. Number followed by a people-word  (e.g. "200 families", "1,500 people")
      2. People-word followed by number    (e.g. "people affected: 300")
      3. Any standalone number ≥ 10
      4. Hard fallback → 5
    """
    people_words = (
        r"(?:people|persons|individuals|families|children|villagers|"
        r"residents|victims|affected|refugees|inhabitants|survivors|"
        r"households|patients|workers|displaced)"
    )

    # Pattern 1: number BEFORE the people word
    m = re.search(rf"(\d[\d,]*)\s*(?:\+\s*)?{people_words}", preprocessed, re.IGNORECASE)
    if m:
        return max(1, int(m.group(1).replace(",", "")))

    # Pattern 2: people word BEFORE the number (e.g. "affected: 300")
    m = re.search(rf"{people_words}[:\s]+(\d[\d,]*)", preprocessed, re.IGNORECASE)
    if m:
        return max(1, int(m.group(1).replace(",", "")))

    # Pattern 3: any large standalone number ≥ 10
    numbers = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", preprocessed)]
    large = [n for n in numbers if n >= 10]
    if large:
        return max(large)

    return 5   # sensible minimum for unknown-scale incidents


def _extract_location(raw_text: str) -> Optional[str]:
    """
    Extract location using spaCy NER (GPE/LOC entities).
    Falls back to rule-based matching against known city coordinates.
    """
    if SPACY_AVAILABLE and nlp is not None:
        doc = nlp(raw_text)
        locations = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
        if locations:
            return locations[0]

    # Rule-based fallback
    from utils.location_utils import CITY_COORDS

    text_lower = raw_text.lower()
    for city in CITY_COORDS:
        if city in text_lower:
            return city.title()

    return None
