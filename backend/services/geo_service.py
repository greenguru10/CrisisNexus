"""
Geo Service – OpenCage geocoding with in-memory cache.

Converts location names to (latitude, longitude) coordinates using
the OpenCage Geocoding API, with a fallback to a static city lookup.
"""

import logging
import asyncio
from typing import Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── LRU cache for geocoding results (avoids repeated API calls) ──

@lru_cache(maxsize=256)
def _cached_opencage_lookup(location: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Cached synchronous OpenCage API call.
    LRU cache ensures the same location string is only geocoded once.
    """
    try:
        from config import settings
        if not settings.OPENCAGE_API_KEY or settings.OPENCAGE_API_KEY.startswith("your_"):
            logger.debug("OpenCage API key not configured – skipping geocode for '%s'", location)
            return None, None

        import urllib.request
        import urllib.parse
        import json

        encoded = urllib.parse.quote(location)
        url = (
            f"https://api.opencagedata.com/geocode/v1/json"
            f"?q={encoded}&key={settings.OPENCAGE_API_KEY}&limit=1&no_annotations=1"
        )

        req = urllib.request.Request(url, headers={"User-Agent": "CommunitySync/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        if data.get("results"):
            geo = data["results"][0]["geometry"]
            lat, lng = geo["lat"], geo["lng"]
            logger.info("OpenCage geocoded '%s' -> (%.4f, %.4f)", location, lat, lng)
            return lat, lng

        logger.debug("OpenCage returned no results for '%s'", location)
        return None, None

    except Exception as e:
        logger.warning("OpenCage geocoding failed for '%s': %s", location, e)
        return None, None


# ── Static city fallback ─────────────────────────────────────────

from utils.location_utils import CITY_COORDS


def _static_city_lookup(location: str) -> Tuple[Optional[float], Optional[float]]:
    """Fallback: match against known city coordinates."""
    name_lower = location.lower().strip()
    for city, (lat, lon) in CITY_COORDS.items():
        if city in name_lower:
            logger.debug("Static city match: '%s' -> %s (%.4f, %.4f)", location, city, lat, lon)
            return lat, lon
    return None, None


# ── Public API ───────────────────────────────────────────────────

async def get_coordinates(location: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode a location string to (latitude, longitude).

    Pipeline:
      1. OpenCage API (cached)
      2. Static city fallback

    Args:
        location: Human-readable location name (e.g. "Mumbai", "Kathmandu Valley")

    Returns:
        Tuple of (latitude, longitude), or (None, None) if geocoding fails.
    """
    if not location or not location.strip():
        return None, None

    location = location.strip()

    # Try OpenCage API (runs in executor to stay async, result is cached)
    try:
        lat, lon = await asyncio.get_event_loop().run_in_executor(
            None, _cached_opencage_lookup, location
        )
        if lat is not None and lon is not None:
            return lat, lon
    except Exception as e:
        logger.debug("OpenCage executor call failed: %s", e)

    # Fallback to static city lookup
    lat, lon = _static_city_lookup(location)
    return lat, lon


def get_coordinates_sync(location: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Synchronous version of get_coordinates for use in non-async contexts.
    """
    if not location or not location.strip():
        return None, None

    location = location.strip()

    # Try OpenCage
    lat, lon = _cached_opencage_lookup(location)
    if lat is not None and lon is not None:
        return lat, lon

    # Fallback
    return _static_city_lookup(location)
