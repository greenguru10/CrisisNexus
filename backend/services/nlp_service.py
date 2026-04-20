"""
NLP Service – Complete Hybrid Pipeline for CommunitySync.

Pipeline:
  1. Preprocess:     lowercase, strip noise, expand slang/multilingual
  2. Length handling: summarize long text (top sentences or LLM)
  3. Rule-based:     category, urgency, people count, location extraction
  4. Groq LLM:       COMPULSORY structured extraction (async)
  5. Location:       LLM location → spaCy NER → city-list fallback
  6. Geocoding:      OpenCage API → static city lookup
  7. Merge:          LLM (preferred) + rule-based (fallback)
  8. Confidence:     LLM success → high, rule-only → medium
  9. Fallback:       sensible defaults for any missing field
  10. Output:        final structured JSON
"""

import re
import logging
from typing import Optional, List

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


# ═══════════════════════════════════════════════════════════════════
# 1. SLANG / MIXED-LANGUAGE EXPANSION MAP
# ═══════════════════════════════════════════════════════════════════

SLANG_MAP: list[tuple[str, str]] = [
    # Numbers / quantity
    (r'\bppl\b',            'people'),
    (r'\bprsns?\b',         'persons'),
    (r'\bpax\b',            'people'),

    # Food-related (Hindi/Urdu)
    (r'\bkhana\b',          'food'),
    (r'\bbhojan\b',         'food'),
    (r'\bkhane\b',          'food'),
    (r'\bkhaana\b',         'food'),
    (r'\banaj\b',           'grain'),
    (r'\baata\b',           'flour'),
    (r'\bchawal\b',         'rice'),

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
    (r'\bbimaari\b',        'disease'),
    (r'\bbukhaar\b',        'fever'),
    (r'\brug?na?\b',        'patient'),
    (r'\baspatal\b',        'hospital'),

    # Clothing
    (r'\bkapde\b',          'clothes'),
    (r'\bkapdein\b',        'clothes'),
    (r'\bkambal\b',         'blanket'),

    # Shelter
    (r'\bmakaan\b',         'house'),
    (r'\bghar\b',           'home'),
    (r'\bjhopdpatti\b',     'slum'),

    # Urgency shorthand
    (r'\burgo\b',           'urgent'),
    (r'\burgt\b',           'urgent'),
    (r'\basap\b',           'immediately'),
    (r'\bplz\b',            'please'),
    (r'\bpls\b',            'please'),
    (r'\bv\.?urgent\b',     'very urgent'),
    (r'\bsos\b',            'emergency'),
    (r'\bjaldi\b',          'quickly'),
    (r'\bturant\b',         'immediately'),
    (r'\bmadat\b',          'help'),
    (r'\bmadad\b',          'help'),
    (r'\bbachao\b',         'save'),

    # Common abbreviations
    (r'\bapprox\.?\b',      'approximately'),
    (r'\bw/\b',             'with'),
    (r'\b&\b',              'and'),
    (r'\bvol\b',            'volunteer'),
    (r'\brel\s*camp\b',     'relief camp'),
    (r'\bgovt\b',           'government'),
    (r'\bngo\b',            'organization'),
    (r'\bfam(?:ilies)?\b',  'families'),
]


# ═══════════════════════════════════════════════════════════════════
# 2. CATEGORY KEYWORD DICTIONARY
# ═══════════════════════════════════════════════════════════════════

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food": [
        "food", "hunger", "hungry", "meal", "meals", "ration", "rations",
        "nutrition", "starvation", "starving", "feed", "feeding", "grain",
        "rice", "wheat", "dal", "groceries", "provisions", "supplies",
        "biscuit", "biscuits", "relief food", "dry food", "flour",
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
        "patient", "patients",
    ],
    "shelter": [
        "shelter", "housing", "homeless", "tent", "tarp", "tarpaulin",
        "roof", "displaced", "evacuation", "camp", "accommodation",
        "house", "home", "relief camp", "temporary shelter", "flood victims",
        "slum",
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
    "quickly", "immediately", "save",
]

URGENCY_MEDIUM_KEYWORDS = [
    "soon", "needed", "necessary", "required", "important", "moderate",
    "significant", "concern", "growing", "worsening", "rising",
    "deteriorating", "increasing", "shortage", "need", "help",
]


# ═══════════════════════════════════════════════════════════════════
# 3. PREPROCESSING
# ═══════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════
# 4. LENGTH HANDLING / SUMMARIZATION
# ═══════════════════════════════════════════════════════════════════

def _summarize_long_text(text: str, max_sentences: int = 4) -> str:
    """
    For long texts, extract the top 2-4 most meaningful sentences.
    Scores sentences by keyword density (disaster-related terms).
    """
    # If short enough, return as-is
    if len(text) < 500:
        return text

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) <= max_sentences:
        return text

    # Score each sentence by disaster keyword density
    disaster_keywords = set()
    for kw_list in CATEGORY_KEYWORDS.values():
        disaster_keywords.update(kw_list)
    disaster_keywords.update(URGENCY_HIGH_KEYWORDS)
    disaster_keywords.update(URGENCY_MEDIUM_KEYWORDS)

    scored = []
    for s in sentences:
        words = s.lower().split()
        score = sum(1 for w in words if w in disaster_keywords)
        # Bonus for sentences with numbers (likely people counts)
        if re.search(r'\d+', s):
            score += 2
        scored.append((score, s))

    # Sort by score descending, pick top sentences
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:max_sentences]]

    summarized = ' '.join(top)
    logger.debug("Summarized %d sentences -> %d (input: %d chars -> %d chars)",
                 len(sentences), len(top), len(text), len(summarized))
    return summarized


# ═══════════════════════════════════════════════════════════════════
# 5. RULE-BASED EXTRACTION
# ═══════════════════════════════════════════════════════════════════

def _detect_categories(preprocessed: str) -> list[str]:
    """
    Score each category by keyword matches.
    Returns ALL categories that scored > 0, sorted by score descending.
    Falls back to ['general'] if nothing matched.
    """
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if ' ' in kw:
                score += preprocessed.count(kw)
            else:
                score += len(re.findall(rf'\b{re.escape(kw)}\b', preprocessed))
        if score > 0:
            scores[category] = score

    if not scores:
        return ["general"]

    # Return all matched categories sorted by score
    sorted_cats = sorted(scores, key=scores.get, reverse=True)  # type: ignore
    logger.debug("Category scores: %s -> %s", scores, sorted_cats)
    return sorted_cats


def _detect_urgency(preprocessed: str) -> str:
    """Classify urgency as high / medium / low."""
    for phrase in URGENCY_HIGH_KEYWORDS:
        if re.search(rf'\b{re.escape(phrase)}\b', preprocessed):
            return "high"

    for phrase in URGENCY_MEDIUM_KEYWORDS:
        if re.search(rf'\b{re.escape(phrase)}\b', preprocessed):
            return "medium"

    return "medium"


def _extract_people_count(preprocessed: str) -> int:
    """
    Extract the number of people affected.
    Priority: number+people-word > people-word+number > large standalone > fallback 5.
    """
    people_words = (
        r"(?:people|persons|individuals|families|children|villagers|"
        r"residents|victims|affected|refugees|inhabitants|survivors|"
        r"households|patients|workers|displaced)"
    )

    m = re.search(rf"(\d[\d,]*)\s*(?:\+\s*)?{people_words}", preprocessed, re.IGNORECASE)
    if m:
        return max(1, int(m.group(1).replace(",", "")))

    m = re.search(rf"{people_words}[:\s]+(\d[\d,]*)", preprocessed, re.IGNORECASE)
    if m:
        return max(1, int(m.group(1).replace(",", "")))

    numbers = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", preprocessed)]
    large = [n for n in numbers if n >= 10]
    if large:
        return max(large)

    return 5


def _extract_location_rulebased(raw_text: str) -> Optional[str]:
    """
    Extract location using spaCy NER (GPE/LOC entities).
    Falls back to matching against known city coordinates.
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


# ═══════════════════════════════════════════════════════════════════
# 6. MERGE LOGIC: LLM + Rule-Based
# ═══════════════════════════════════════════════════════════════════

def _merge_results(rule_result: dict, llm_result: Optional[dict]) -> dict:
    """
    Merge LLM extraction with rule-based extraction.

    Priority:
      - LLM fields are preferred when valid
      - Rule-based fills in any gaps
      - Fallback defaults for anything still missing
    """
    merged = {}

    # ── Categories ──
    llm_cats = []
    if llm_result and llm_result.get("categories"):
        raw_cats = llm_result["categories"]
        if isinstance(raw_cats, list):
            llm_cats = [c.lower().strip() for c in raw_cats if isinstance(c, str) and c.strip()]
        elif isinstance(raw_cats, str):
            llm_cats = [raw_cats.lower().strip()]

    rule_cats = rule_result.get("categories", ["general"])

    # Prefer LLM categories if they look valid
    if llm_cats and llm_cats != ["general"]:
        merged["categories"] = llm_cats
    elif rule_cats and rule_cats != ["general"]:
        merged["categories"] = rule_cats
    else:
        merged["categories"] = llm_cats or rule_cats or ["general"]

    # Use first category as primary (for DB storage)
    merged["category"] = merged["categories"][0]

    # ── People count ──
    llm_people = None
    if llm_result and llm_result.get("people_count"):
        try:
            llm_people = int(llm_result["people_count"])
        except (ValueError, TypeError):
            pass

    rule_people = rule_result.get("people_affected", 5)

    if llm_people and llm_people > 0:
        merged["people_affected"] = llm_people
    else:
        merged["people_affected"] = rule_people

    # ── Urgency ──
    llm_urgency = None
    if llm_result and llm_result.get("urgency"):
        u = str(llm_result["urgency"]).lower().strip()
        if u in ("low", "medium", "high"):
            llm_urgency = u

    rule_urgency = rule_result.get("urgency", "medium")

    merged["urgency"] = llm_urgency or rule_urgency

    # ── Description ──
    llm_desc = None
    if llm_result and llm_result.get("description"):
        d = str(llm_result["description"]).strip()
        if len(d) > 10:
            llm_desc = d

    merged["description"] = llm_desc or ""

    # ── Location ──
    llm_location = None
    if llm_result and llm_result.get("location"):
        loc = str(llm_result["location"]).strip()
        if loc.lower() not in ("", "unknown", "not mentioned", "n/a", "none", "null"):
            llm_location = loc

    rule_location = rule_result.get("location")

    merged["location"] = llm_location or rule_location

    # ── Confidence ──
    if llm_result and llm_cats:
        merged["confidence"] = 90  # LLM success = high confidence
    elif rule_cats != ["general"]:
        merged["confidence"] = 65  # Rule-based with matches
    else:
        merged["confidence"] = 40  # Fallbacks only

    logger.info("Merged result: categories=%s, people=%d, urgency=%s, location=%s, confidence=%d",
                merged["categories"], merged["people_affected"], merged["urgency"],
                merged["location"], merged["confidence"])

    return merged


# ═══════════════════════════════════════════════════════════════════
# 7. FALLBACK DEFAULTS
# ═══════════════════════════════════════════════════════════════════

def _apply_fallbacks(result: dict) -> dict:
    """Ensure all required fields have values."""
    if not result.get("categories"):
        result["categories"] = ["general"]
    if not result.get("category"):
        result["category"] = result["categories"][0]
    if not result.get("people_affected") or result["people_affected"] <= 0:
        result["people_affected"] = 5
    if result.get("urgency") not in ("low", "medium", "high"):
        result["urgency"] = "medium"
    if not result.get("location"):
        result["location"] = None
    if not result.get("description"):
        result["description"] = ""
    if not result.get("confidence"):
        result["confidence"] = 40

    return result


# ═══════════════════════════════════════════════════════════════════
# 8. PUBLIC API — ASYNC HYBRID PIPELINE
# ═══════════════════════════════════════════════════════════════════

async def extract_from_text_async(raw_text: str) -> dict:
    """
    ASYNC hybrid NLP pipeline. Full flow:

      Raw Input → Preprocess → Summarize → Rule-based → Groq LLM
      → Location extraction → Geocoding → Merge → Fallback → Output

    Returns:
        {
            "categories": [...],
            "category": str,         # primary category for DB
            "description": str,
            "people_affected": int,
            "urgency": str,
            "location": str | None,
            "latitude": float | None,
            "longitude": float | None,
            "confidence": int        # 0-100
        }
    """
    if not raw_text or not raw_text.strip():
        logger.warning("Empty input text received – returning defaults.")
        return _apply_fallbacks({
            "categories": ["general"],
            "category": "general",
            "description": "",
            "people_affected": 5,
            "urgency": "medium",
            "location": None,
            "latitude": None,
            "longitude": None,
            "confidence": 20,
        })

    # ── Step 1: Preprocess ──
    preprocessed = _preprocess_text(raw_text)

    # ── Step 2: Summarize if long ──
    summarized = _summarize_long_text(preprocessed)

    # ── Step 3: Rule-based extraction ──
    rule_result = {
        "categories": _detect_categories(preprocessed),
        "urgency":    _detect_urgency(preprocessed),
        "people_affected": _extract_people_count(preprocessed),
        "location":   _extract_location_rulebased(raw_text),
    }
    logger.info("Rule-based extraction: %s", rule_result)

    # ── Step 4: Groq LLM extraction (COMPULSORY) ──
    llm_result = None
    try:
        from services.llm_service import llm_extract
        llm_result = await llm_extract(summarized)
        if llm_result:
            logger.info("LLM extraction succeeded.")
        else:
            logger.warning("LLM extraction returned None – using rule-based only.")
    except Exception as e:
        logger.error("LLM extraction error: %s – using rule-based only.", e)

    # ── Step 5: Merge results ──
    merged = _merge_results(rule_result, llm_result)

    # ── Step 6: Geocoding ──
    lat, lon = None, None
    if merged.get("location"):
        try:
            from services.geo_service import get_coordinates
            lat, lon = await get_coordinates(merged["location"])
        except Exception as e:
            logger.warning("Geocoding failed: %s", e)

    merged["latitude"] = lat
    merged["longitude"] = lon

    # ── Step 7: Apply fallbacks ──
    final = _apply_fallbacks(merged)

    logger.info(
        "NLP pipeline complete: categories=%s, urgency=%s, people=%d, "
        "location=%s (%.4f, %.4f), confidence=%d",
        final["categories"], final["urgency"], final["people_affected"],
        final.get("location"), final.get("latitude") or 0, final.get("longitude") or 0,
        final["confidence"],
    )

    return final


# ═══════════════════════════════════════════════════════════════════
# 9. SYNC WRAPPER (backward compatibility)
# ═══════════════════════════════════════════════════════════════════

def extract_from_text(raw_text: str) -> dict:
    """
    Synchronous fallback — uses ONLY rule-based extraction.
    Used when called from non-async contexts.

    For the full hybrid pipeline (with LLM + geocoding),
    use extract_from_text_async() instead.
    """
    if not raw_text or not raw_text.strip():
        return {
            "category": "general",
            "urgency": "medium",
            "people_affected": 5,
            "location": None,
        }

    preprocessed = _preprocess_text(raw_text)
    summarized = _summarize_long_text(preprocessed)

    categories = _detect_categories(summarized)
    urgency = _detect_urgency(summarized)
    people_affected = _extract_people_count(summarized)
    location = _extract_location_rulebased(raw_text)

    result = {
        "category":        categories[0] if categories else "general",
        "categories":      categories,
        "urgency":         urgency,
        "people_affected": people_affected,
        "location":        location,
    }

    logger.info("NLP sync extraction -> %s", result)
    return result
