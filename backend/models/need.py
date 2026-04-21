"""
Need model – represents an NGO survey report converted into a structured need.
"""

from sqlalchemy import Column, Integer, String, Float, Text, Enum as SAEnum, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base
import enum


class UrgencyLevel(str, enum.Enum):
    """Urgency classification for needs."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NeedStatus(str, enum.Enum):
    """Status lifecycle of a need."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    ASSIGNED = "assigned"
    COMPLETED = "completed"


class Need(Base):
    """ORM model for the needs table."""

    __tablename__ = "needs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raw_text = Column(Text, nullable=False, comment="Original unstructured survey report text")
    category = Column(String(255), nullable=False, index=True, comment="E.g. food, medical, water, shelter")
    urgency = Column(SAEnum(UrgencyLevel), nullable=False, default=UrgencyLevel.MEDIUM, index=True)
    people_affected = Column(Integer, nullable=False, default=0)
    location = Column(String(255), nullable=True, comment="Human-readable location name")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    priority_score = Column(Float, nullable=False, default=0.0, index=True, comment="Computed 0-100 score")
    status = Column(SAEnum(NeedStatus), nullable=False, default=NeedStatus.PENDING, index=True)
    assigned_volunteer_id = Column(Integer, nullable=True, comment="FK to volunteer who was matched")
    feedback_rating = Column(Float, nullable=True, comment="Optional post-completion rating 0-5")
    feedback_comments = Column(Text, nullable=True, comment="Optional post-completion comments")
    # ── Multi-NGO federation fields ───────────────────────────────
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=True, index=True,
                    comment="Which NGO owns/manages this need")
    assigned_by_admin = Column(Boolean, nullable=False, default=False,
                               comment="True when Admin pushed this task to the NGO")
    ngo_accepted = Column(Boolean, nullable=True,
                          comment="None=pending, True=accepted, False=rejected by NGO coordinator")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Need id={self.id} category={self.category} urgency={self.urgency} score={self.priority_score}>"
