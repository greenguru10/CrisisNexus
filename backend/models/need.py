"""
Need model – represents an NGO survey report converted into a structured need.
"""

from sqlalchemy import Column, Integer, String, Float, Text, Enum as SAEnum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
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
    feedback_rating = Column(Float, nullable=True, comment="Optional post-completion rating 0-5")
    feedback_comments = Column(Text, nullable=True, comment="Optional post-completion comments")
    assigned_by_admin = Column(Boolean, nullable=False, default=False,
                               comment="True when Admin pushed this task to the NGO")
    ngo_accepted = Column(Boolean, nullable=True,
                          comment="None=pending, True=accepted, False=rejected by NGO coordinator")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships for junction tables
    volunteer_assignments = relationship("NeedVolunteerAssignment", back_populates="need", cascade="all, delete-orphan")
    ngo_assignments = relationship("NeedNGOAssignment", back_populates="need", cascade="all, delete-orphan")

    @property
    def assigned_volunteer_id(self):
        # Look for active assignment first
        active = [a for a in self.volunteer_assignments if a.is_active]
        if active:
            return active[0].volunteer_id
        
        # If none active but task is completed, return the last one assigned
        if self.status == NeedStatus.COMPLETED and self.volunteer_assignments:
            # Sort by assigned_at desc
            sorted_vols = sorted(self.volunteer_assignments, key=lambda x: x.assigned_at, reverse=True)
            return sorted_vols[0].volunteer_id
            
        return None

    @property
    def ngo_id(self):
        # Return the first assigned NGO for legacy compatibility
        return self.ngo_assignments[0].ngo_id if self.ngo_assignments else None

    def __repr__(self):
        return f"<Need id={self.id} category={self.category} urgency={self.urgency} score={self.priority_score}>"
