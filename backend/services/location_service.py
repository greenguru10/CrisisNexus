"""
Location Service – Enrichment & Validation (NO standalone LLM call).

Receives pre-extracted location_area / location_city from the unified
LLM call in llm_service.py, then enriches via spaCy fallback and
OpenCage geocoding.  Only ONE Groq API call is made per report.
"""

import logging
import asyncio
import re
import json
import urllib.request
import urllib.parse
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# --- Try loading spaCy ---
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    nlp = None
    logger.warning("spaCy not available. Fallback extraction will be degraded.")


# ═══════════════════════════════════════════════════════════════════
# NOISE / INVALID TERMS (not real places)
# ═══════════════════════════════════════════════════════════════════

# Words that the LLM or spaCy might return as "locations" but are NOT places
NOISE_LOCATION_TERMS = {
    # Generic noise
    "location", "area", "slum", "slum area", "settlement", "informal settlement",
    "region", "zone", "place", "locality", "nearby", "near", "maybe",
    "side", "around", "close", "unknown", "not mentioned", "n/a", "none", "null",
    # Medical terms spaCy sometimes misidentifies as GPE/LOC
    "fever", "cholera", "malaria", "diarrhea", "illness", "disease",
    "infection", "pain", "weakness", "oxygen", "icu",
    # Other common false positives
    "daily", "wage", "yesterday", "evening", "morning", "today",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
}

# ═══════════════════════════════════════════════════════════════════
# MAJOR CITIES FALLBACK (If LLM/spaCy fails to extract city)
# ═══════════════════════════════════════════════════════════════════

MAJOR_CITIES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "kolkata", 
    "hyderabad", "pune", "ahmedabad", "surat", "jaipur", "lucknow", 
    "kanpur", "nagpur", "indore", "thane", "bhopal", "patna", "vadodara"
}

def fallback_city_extraction(text: str) -> str:
    """Extract known major cities using regex if missing."""
    text_lower = text.lower()
    for city in MAJOR_CITIES:
        if re.search(rf'\b{city}\b', text_lower):
            return city.title()
    return ""


def _is_valid_location(text: str) -> bool:
    """Check if a string is a plausible location (not noise/medical term)."""
    if not text or not text.strip():
        return False
    cleaned = text.strip().lower()
    # Reject if it's a known noise term
    if cleaned in NOISE_LOCATION_TERMS:
        return False
    # Reject if too short (single char) or too long (likely a sentence)
    if len(cleaned) < 2 or len(cleaned) > 80:
        return False
    # Reject if it's purely numeric
    if cleaned.replace(" ", "").isdigit():
        return False
    return True


# ═══════════════════════════════════════════════════════════════════
# 1. PREPROCESSING
# ═══════════════════════════════════════════════════════════════════

def preprocess_location_text(raw_text: str) -> str:
    """
    Normalize text for location context: lowercase → strip noise → Title case.
    """
    text = raw_text.lower()
    noise_words = [r"\bmaybe\b", r"\bnear\b", r"\bside\b", r"\barea\b",
                   r"\bclose to\b", r"\baround\b", r"\bslum\b", r"\blocality\b",
                   r"\bregion\b", r"\bzone\b", r"\bplace\b", r"\blocation\b",
                   r"\bsettlement\b", r"\binformal\b"]
    for word in noise_words:
        text = re.sub(word, "", text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text.title()


# ═══════════════════════════════════════════════════════════════════
# 2. spaCy NER FALLBACK (no Groq call)
# ═══════════════════════════════════════════════════════════════════

def extract_location_spacy(text: str) -> Dict[str, str]:
    """
    Fallback extraction using spaCy NER (GPE / LOC entities).
    Used only when the main LLM call returned empty location fields.
    Filters out medical terms and other false positives.
    """
    if not SPACY_AVAILABLE or not nlp:
        return {"area": "", "city": ""}

    doc = nlp(text)
    raw_locations = [ent.text.strip() for ent in doc.ents if ent.label_ in ("GPE", "LOC")]

    # Filter out noise/invalid terms
    locations = [loc for loc in raw_locations if _is_valid_location(loc)]

    if not locations:
        return {"area": "", "city": ""}

    if len(locations) == 1:
        return {"area": "", "city": locations[0]}

    # Smaller locality first, larger city last
    return {"area": locations[0], "city": locations[-1]}


# ═══════════════════════════════════════════════════════════════════
# 3. OPENCAGE ENRICHMENT
# ═══════════════════════════════════════════════════════════════════

async def enrich_location_geocode(area: str, city: str) -> Dict[str, str]:
    """
    Enrich partial locations via OpenCage Forward Geocoding.
    If area exists but city is missing (or vice versa), fills the gap.
    """
    search_query = (
        f"{area}, {city}" if area and city
        else area if area
        else city
    )
    search_query = search_query.strip(" ,")

    if not search_query:
        return {"area": "", "city": ""}

    try:
        from config import settings
        if not settings.OPENCAGE_API_KEY or settings.OPENCAGE_API_KEY.startswith("your_"):
            return {"area": area, "city": city}

        encoded = urllib.parse.quote(search_query)
        url = (
            f"https://api.opencagedata.com/geocode/v1/json"
            f"?q={encoded}&key={settings.OPENCAGE_API_KEY}&limit=1&no_annotations=1"
        )

        def _fetch():
            req = urllib.request.Request(url, headers={"User-Agent": "CommunitySync/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode())

        data = await asyncio.get_running_loop().run_in_executor(None, _fetch)

        if data.get("results"):
            components = data["results"][0].get("components", {})

            # Keep original values if they exist; fill gaps from API
            enriched_city = city or (
                components.get("city") or
                components.get("town") or
                components.get("state_district") or
                components.get("county")
            )

            enriched_area = area or (
                components.get("suburb") or
                components.get("neighbourhood") or
                components.get("village")
            )

            return {
                "area": str(enriched_area).strip() if enriched_area else "",
                "city": str(enriched_city).strip() if enriched_city else ""
            }

    except Exception as e:
        logger.warning("Geocode enrichment failed for '%s': %s", search_query, e)

    return {"area": area, "city": city}


# ═══════════════════════════════════════════════════════════════════
# 4. MERGE LOGIC
# ═══════════════════════════════════════════════════════════════════

def merge_location(area: str, city: str) -> Optional[str]:
    """Merge area + city into a single formatted string, avoiding duplicates."""
    area = area.strip()
    city = city.strip()

    if area and city and area.lower() != city.lower():
        # Prevent outputs like "Govandi, Mumbai, Mumbai" if area already contains city
        if city.lower() in area.lower():
            return area.title()
        if area.lower() in city.lower():
            return city.title()
        return f"{area}, {city}".title()
    elif city:
        return city.title()
    elif area:
        return area.title()
    else:
        return None


# ═══════════════════════════════════════════════════════════════════
# 5. ORCHESTRATOR  (no LLM call – receives pre-extracted data)
# ═══════════════════════════════════════════════════════════════════

async def extract_and_enrich_location(
    raw_text: str,
    llm_area: str = "",
    llm_city: str = "",
) -> str:
    """
    Main orchestrator.  Does NOT make its own Groq call.

    Args:
        raw_text:  Original report text (used for spaCy fallback).
        llm_area:  Area string already extracted by the unified LLM call.
        llm_city:  City string already extracted by the unified LLM call.

    Returns:
        Formatted location string (e.g. "Govandi, Mumbai") or "unknown".
    """
    area = (llm_area or "").strip()
    city = (llm_city or "").strip()

    # Validate LLM outputs — reject noise terms
    if not _is_valid_location(area):
        area = ""
    if not _is_valid_location(city):
        city = ""

    # If LLM gave us nothing usable, try spaCy on cleaned text
    if not area and not city:
        clean_text = preprocess_location_text(raw_text)
        if clean_text:
            spacy_result = extract_location_spacy(clean_text)
            area = spacy_result.get("area", "")
            city = spacy_result.get("city", "")

    # Absolute fallback: if city is still missing, try regex lookup
    if not city:
        city = fallback_city_extraction(raw_text)

    # Enrich via OpenCage (fills missing area or city)
    if area or city:
        enriched = await enrich_location_geocode(area, city)
        area = enriched.get("area", area)
        city = enriched.get("city", city)

    result = merge_location(area, city)
    logger.info("Location pipeline: llm_area='%s' llm_city='%s' -> final='%s'",
                llm_area, llm_city, result or "unknown")
    return result if result else "unknown"
