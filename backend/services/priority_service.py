"""
Priority Engine – Computes a 0-100 priority score for needs.

Scoring formula:
  priority_score = (urgency_weight * 40) + (people_factor * 40) + (category_weight * 20)

Where:
  - urgency_weight: high=1.0, medium=0.6, low=0.3
  - people_factor: min(1.0, people_affected / 1000) — saturates at 1000 people
  - category_weight: life-critical categories score higher
"""

import logging

logger = logging.getLogger(__name__)

# ── Weight maps ──────────────────────────────────────────────────

URGENCY_WEIGHTS: dict[str, float] = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
}

CATEGORY_WEIGHTS: dict[str, float] = {
    "medical": 1.0,
    "water": 0.9,
    "food": 0.85,
    "shelter": 0.75,
    "sanitation": 0.65,
    "clothing": 0.5,
    "education": 0.4,
    "general": 0.3,
}


def compute_priority_score(
    urgency: str,
    people_affected: int,
    category: str,
) -> float:
    """
    Compute a priority score between 0 and 100.

    Args:
        urgency:         "high", "medium", or "low"
        people_affected: Number of people affected
        category:        Need category string

    Returns:
        Float score clamped to [0, 100], rounded to 2 decimals.
    """
    urgency_w = URGENCY_WEIGHTS.get(urgency, 0.3)
    
    cats = [c.strip() for c in category.split(",")]
    category_w = max([CATEGORY_WEIGHTS.get(c, 0.3) for c in cats]) if cats else 0.3
    
    people_factor = min(1.0, max(0, people_affected) / 1000.0)

    score = (urgency_w * 40) + (people_factor * 40) + (category_w * 20)
    score = round(min(100.0, max(0.0, score)), 2)

    logger.info(
        "Priority score: %.2f  (urgency=%s → %.1f, people=%d → %.2f, cat=%s → %.1f)",
        score, urgency, urgency_w, people_affected, people_factor, category, category_w,
    )
    return score
