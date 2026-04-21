"""
Gamification models – Badge definitions and VolunteerBadge earned records.
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base


class BadgeCriteriaType(str, enum.Enum):
    TASKS_COMPLETED = "tasks_completed"
    AVG_RATING = "avg_rating"
    STREAK = "streak"
    FIRST_TASK = "first_task"
    SPECIAL = "special"


# Pre-defined badge catalogue (loaded via seed at startup)
BADGE_CATALOGUE = [
    {
        "code": "FIRST_RESPONDER",
        "name": "First Responder",
        "description": "Completed your very first task",
        "icon_emoji": "🚨",
        "criteria_type": "first_task",
        "threshold": 1,
    },
    {
        "code": "RISING_STAR",
        "name": "Rising Star",
        "description": "Completed 10 tasks",
        "icon_emoji": "⭐",
        "criteria_type": "tasks_completed",
        "threshold": 10,
    },
    {
        "code": "CHAMPION",
        "name": "Community Champion",
        "description": "Completed 50 tasks",
        "icon_emoji": "🏆",
        "criteria_type": "tasks_completed",
        "threshold": 50,
    },
    {
        "code": "CENTURY",
        "name": "Century Hero",
        "description": "Completed 100 tasks",
        "icon_emoji": "💯",
        "criteria_type": "tasks_completed",
        "threshold": 100,
    },
    {
        "code": "EXCELLENCE",
        "name": "Excellence Award",
        "description": "Maintained average rating of 4.5 or above",
        "icon_emoji": "🌟",
        "criteria_type": "avg_rating",
        "threshold": 4.5,
    },
    {
        "code": "STREAK_5",
        "name": "On a Roll",
        "description": "Completed 5 tasks in a row",
        "icon_emoji": "🔥",
        "criteria_type": "streak",
        "threshold": 5,
    },
    {
        "code": "MEDICAL_HERO",
        "name": "Medical Hero",
        "description": "Completed 10 medical category tasks",
        "icon_emoji": "🏥",
        "criteria_type": "special",
        "threshold": 10,
    },
    {
        "code": "FOOD_CHAMPION",
        "name": "Food Champion",
        "description": "Completed 10 food distribution tasks",
        "icon_emoji": "🍱",
        "criteria_type": "special",
        "threshold": 10,
    },
]


class Badge(Base):
    """Defines an available badge in the system."""

    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    icon_emoji = Column(String(10), nullable=True)
    criteria_type = Column(String(50), nullable=False)
    threshold = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Badge code={self.code} threshold={self.threshold}>"


class VolunteerBadge(Base):
    """Records which volunteer earned which badge and when."""

    __tablename__ = "volunteer_badges"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<VolunteerBadge vol={self.volunteer_id} badge={self.badge_id}>"
