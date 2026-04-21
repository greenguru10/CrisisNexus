"""
Gamification service – checks and awards badges after task completions.
Called from task_routes.py upon task completion.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.volunteer import Volunteer
from models.need import Need, NeedStatus
from models.gamification import Badge, VolunteerBadge

logger = logging.getLogger(__name__)


def _already_has_badge(db: Session, volunteer_id: int, badge_id: int) -> bool:
    return db.query(VolunteerBadge).filter(
        VolunteerBadge.volunteer_id == volunteer_id,
        VolunteerBadge.badge_id == badge_id,
    ).first() is not None


def _award(db: Session, volunteer_id: int, badge: Badge):
    if not _already_has_badge(db, volunteer_id, badge.id):
        db.add(VolunteerBadge(volunteer_id=volunteer_id, badge_id=badge.id))
        logger.info("🏅 Awarded badge '%s' to volunteer id=%d", badge.code, volunteer_id)


def check_and_award_badges(volunteer_id: int, db: Session):
    """
    Run after every task completion. Checks all badge criteria
    and awards any newly earned badges to the volunteer.
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        return

    badges = db.query(Badge).all()
    total = volunteer.tasks_completed
    streak = volunteer.consecutive_completions
    avg_rating = volunteer.rating or 0.0

    # Count by category for special badges
    medical_count = db.query(func.count(Need.id)).filter(
        Need.assigned_volunteer_id == volunteer_id,
        Need.status == NeedStatus.COMPLETED,
        Need.category.ilike("%medical%"),
    ).scalar() or 0

    food_count = db.query(func.count(Need.id)).filter(
        Need.assigned_volunteer_id == volunteer_id,
        Need.status == NeedStatus.COMPLETED,
        Need.category.ilike("%food%"),
    ).scalar() or 0

    for badge in badges:
        ct = badge.criteria_type
        th = badge.threshold

        if ct == "first_task" and total >= 1:
            _award(db, volunteer_id, badge)
        elif ct == "tasks_completed" and total >= th:
            _award(db, volunteer_id, badge)
        elif ct == "avg_rating" and total >= 5 and avg_rating >= th:
            # Require at least 5 tasks before excellence badge
            _award(db, volunteer_id, badge)
        elif ct == "streak" and streak >= th:
            _award(db, volunteer_id, badge)
        elif ct == "special":
            if badge.code == "MEDICAL_HERO" and medical_count >= th:
                _award(db, volunteer_id, badge)
            elif badge.code == "FOOD_CHAMPION" and food_count >= th:
                _award(db, volunteer_id, badge)

    db.commit()


def update_volunteer_stats_on_completion(volunteer_id: int, rating: float | None, db: Session):
    """
    Called when a task is marked completed.
    Updates tasks_completed, streak, and rolling average rating.
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        return

    volunteer.tasks_completed = (volunteer.tasks_completed or 0) + 1
    volunteer.consecutive_completions = (volunteer.consecutive_completions or 0) + 1

    # Update rolling average rating
    if rating is not None and rating > 0:
        old_rating = volunteer.rating or 0.0
        old_count = volunteer.tasks_completed - 1  # before this task
        if old_count <= 0:
            volunteer.rating = rating
        else:
            volunteer.rating = round(
                (old_rating * old_count + rating) / volunteer.tasks_completed, 2
            )

    db.commit()
    check_and_award_badges(volunteer_id, db)
