"""
Location utilities – Haversine distance calculation.
"""

import math
from typing import Optional, Tuple


def haversine_distance(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float],
) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1, lon1: Latitude/longitude of point 1 (degrees).
        lat2, lon2: Latitude/longitude of point 2 (degrees).

    Returns:
        Distance in kilometers. Returns float('inf') if coordinates are missing.
    """
    if any(v is None for v in (lat1, lon1, lat2, lon2)):
        return float("inf")

    R = 6371.0  # Earth's mean radius in km

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ── Well-known city coordinates (fallback geocoding) ────────────

CITY_COORDS: dict[str, Tuple[float, float]] = {
    "mumbai": (19.076, 72.8777),
    "delhi": (28.7041, 77.1025),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.385, 78.4867),
    "pune": (18.5204, 73.8567),
    "kathmandu": (27.7172, 85.324),
    "dhaka": (23.8103, 90.4125),
    "colombo": (6.9271, 79.8612),
    "new york": (40.7128, -74.006),
    "london": (51.5074, -0.1278),
    "tokyo": (35.6762, 139.6503),
    "nairobi": (1.2921, 36.8219),
    "cairo": (30.0444, 31.2357),
    "lagos": (6.5244, 3.3792),
    "sao paulo": (-23.5505, -46.6333),
    "jakarta": (-6.2088, 106.8456),
    "manila": (14.5995, 120.9842),
    "karachi": (24.8607, 67.0011),
}


def geocode_location(location_name: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Simple geocode lookup by matching city names.
    Returns (latitude, longitude) or (None, None) if not found.
    """
    if not location_name:
        return None, None

    name_lower = location_name.lower().strip()
    for city, (lat, lon) in CITY_COORDS.items():
        if city in name_lower:
            return lat, lon

    return None, None
