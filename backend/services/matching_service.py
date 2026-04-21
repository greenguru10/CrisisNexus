"""
Matching Engine – Finds the best volunteer for a given need.

Composite match score (higher is better):
  match_score = (skill_score * 0.50) + (distance_score * 0.35) + (rating_score * 0.15)

Where:
  - skill_score:    Jaccard-like similarity between need category and volunteer skills
  - distance_score: Inverse distance penalty (closer = higher)
  - rating_score:   Normalised volunteer rating (0-5 → 0-1)
"""

import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from models.need import Need
from models.volunteer import Volunteer
from utils.location_utils import haversine_distance

logger = logging.getLogger(__name__)

# ── Category ↔ Skill mapping ────────────────────────────────────

CATEGORY_SKILL_MAP: dict[str, list[str]] = {
    "food": ["cooking", "food", "nutrition", "logistics", "distribution"],
    "water": ["water", "plumbing", "purification", "logistics", "engineering"],
    "medical": ["medical", "first_aid", "nursing", "pharmacy", "doctor", "health"],
    "shelter": ["construction", "shelter", "carpentry", "engineering", "logistics"],
    "clothing": ["clothing", "textiles", "distribution", "logistics"],
    "sanitation": ["sanitation", "hygiene", "cleaning", "plumbing", "health"],
    "education": ["education", "teaching", "mentoring", "counseling"],
    "general": ["logistics", "coordination", "general", "driving"],
}


def find_best_volunteer(
    need: Need,
    volunteers: List[Volunteer],
    workloads: Optional[Dict[int, int]] = None
) -> Optional[Dict]:
    """
    Score all available volunteers against a need and return the best match.

    Returns:
        dict with volunteer_id, volunteer_name, match_score, distance_km, skill_match
        or None if no suitable volunteer found.
    """
    if workloads is None:
        workloads = {}
    if not volunteers:
        return None

    best: Optional[Dict] = None
    best_score = -1.0

    need_cats = [c.strip() for c in need.category.split(",")]
    relevant_skills = set()
    for cat in need_cats:
        relevant_skills.update(CATEGORY_SKILL_MAP.get(cat, CATEGORY_SKILL_MAP["general"]))

    for vol in volunteers:
        # Availability Score: 1.0 if available, 0.2 if busy (but still considered)
        availability_score = 1.0 if vol.availability else 0.2

        # Workload Score: Inverse scaling based on active tasks (maxed out penalty at 5 tasks)
        active_tasks = workloads.get(vol.id, 0)
        workload_score = max(0.0, 1.0 - (active_tasks * 0.2))

        # Skill similarity (Jaccard-like)
        vol_skills = set(s.lower().strip() for s in (vol.skills or []))
        if vol_skills and relevant_skills:
            intersection = vol_skills & relevant_skills
            union = vol_skills | relevant_skills
            skill_score = len(intersection) / len(union) if union else 0.0
        else:
            skill_score = 0.0

        # Distance score (inverse, max 500 km range considered)
        dist_km = haversine_distance(
            need.latitude, need.longitude,
            vol.latitude, vol.longitude,
        )
        if dist_km == float("inf"):
            distance_score = 0.3  # unknown location gets a neutral score
        else:
            distance_score = max(0.0, 1.0 - (dist_km / 500.0))

        # Rating score (0-5 → 0-1)
        rating_score = (vol.rating or 0.0) / 5.0

        # Composite score
        # skill (40%), distance (20%), rating (10%), availability (15%), workload (15%)
        composite = (skill_score * 0.40) + (distance_score * 0.20) + (rating_score * 0.10) + (availability_score * 0.15) + (workload_score * 0.15)

        if composite > best_score:
            best_score = composite
            best = {
                "volunteer_id": vol.id,
                "volunteer_name": vol.name,
                "match_score": round(composite, 4),
                "distance_km": round(dist_km, 2) if dist_km != float("inf") else -1,
                "skill_match": round(skill_score, 4),
            }

    if best:
        logger.info("Best match for need %d: volunteer %s (score=%.4f)", need.id, best["volunteer_name"], best["match_score"])
    else:
        logger.warning("No suitable volunteer found for need %d", need.id)

    return best
