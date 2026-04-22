"""
Volunteer model – represents a volunteer who can be matched to needs.
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from database import Base


class VolunteerApprovalStatus(str, enum.Enum):
    """Volunteer approval status by NGO Coordinator."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Volunteer(Base):
    """ORM model for the volunteers table."""

    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=True, index=True, comment="Volunteer email for notifications")
    mobile_number = Column(String(20), nullable=True, comment="Mobile number for WhatsApp (e.g. +919876543210)")
    skills = Column(ARRAY(String), nullable=False, default=list, comment="List of skill tags")
    location = Column(String(255), nullable=True, comment="Human-readable location name")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    availability = Column(Boolean, nullable=False, default=True, index=True)
    rating = Column(Float, nullable=True, default=0.0, comment="Volunteer performance rating 0-5")
    # ── Multi-NGO federation fields ───────────────────────────────
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=True, index=True,
                    comment="Primary NGO this volunteer belongs to")
    # ── NGO Coordinator Approval Status ───────────────────────────
    approval_status = Column(
        SAEnum(VolunteerApprovalStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=VolunteerApprovalStatus.PENDING,
        index=True,
        comment="NGO coordinator approval: pending|approved|rejected",
    )
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, 
                                 comment="User ID of coordinator who approved/rejected")
    approval_notes = Column(String(500), nullable=True, comment="Coordinator's approval/rejection notes")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="When coordinator approved/rejected")
    # ── Gamification fields ───────────────────────────────────────
    tasks_completed = Column(Integer, nullable=False, default=0, comment="Total completed task count")
    consecutive_completions = Column(Integer, nullable=False, default=0,
                                     comment="Current streak count for badge tracking")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Volunteer id={self.id} name={self.name} available={self.availability}>"

