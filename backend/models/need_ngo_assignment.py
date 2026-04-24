import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class NgoAssignStatus(str, enum.Enum):
    PENDING  = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class NeedNGOAssignment(Base):
    """
    Junction table: Admin assigns a Need to one or more NGOs.
    Each row = one NGO's assignment for that need.
    Completion requires at least one volunteer from EACH assigned NGO to mark done.
    """
    __tablename__ = "need_ngo_assignments"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    need_id     = Column(Integer, ForeignKey("needs.id", ondelete="CASCADE"), nullable=False, index=True)
    ngo_id      = Column(Integer, ForeignKey("ngos.id",  ondelete="CASCADE"), nullable=False, index=True)
    status      = Column(
        SAEnum(NgoAssignStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=NgoAssignStatus.PENDING,
        index=True,
    )
    admin_note  = Column(String(500), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # when accepted / rejected

    # ── Per-NGO completion tracking ───────────────────────────────────────────
    # When a volunteer from this NGO marks the task complete, is_completed → True.
    # The Need only transitions to COMPLETED when ALL assigned NGOs have is_completed=True.
    is_completed            = Column(Boolean, nullable=False, default=False, index=True)
    completed_at            = Column(DateTime(timezone=True), nullable=True)
    completed_by_volunteer_id = Column(
        Integer,
        ForeignKey("volunteers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Which volunteer from this NGO completed the task",
    )

    need = relationship("Need", back_populates="ngo_assignments")
