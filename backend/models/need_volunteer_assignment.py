import enum
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class VolunteerTaskStatus(str, enum.Enum):
    """
    Per-volunteer task lifecycle.
    State machine: ASSIGNED → ACCEPTED → IN_PROGRESS → COMPLETED
    No skipping states is enforced at the route layer.
    """
    ASSIGNED   = "assigned"
    ACCEPTED   = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED  = "completed"


class NeedVolunteerAssignment(Base):
    """
    Tracks which volunteers are assigned to a need by an NGO.
    Each row holds a per-volunteer status so that acceptance, start, and
    completion are tracked independently per volunteer.

    State machine (enforced in task_routes.py):
        ASSIGNED → ACCEPTED → IN_PROGRESS → COMPLETED
    """
    __tablename__ = "need_volunteer_assignments"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    need_id        = Column(Integer, ForeignKey("needs.id",       ondelete="CASCADE"), nullable=False, index=True)
    volunteer_id   = Column(Integer, ForeignKey("volunteers.id",  ondelete="CASCADE"), nullable=False, index=True)
    ngo_id         = Column(Integer, ForeignKey("ngos.id",        ondelete="CASCADE"), nullable=True, index=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id",       ondelete="SET NULL"), nullable=True)

    # ── Per-volunteer state machine ───────────────────────────────────────────
    status = Column(
        SAEnum(VolunteerTaskStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=VolunteerTaskStatus.ASSIGNED,
        index=True,
        comment="ASSIGNED → ACCEPTED → IN_PROGRESS → COMPLETED",
    )

    # ── Backward-compat flag (deprecated; use status instead) ────────────────
    is_active      = Column(Boolean, nullable=False, default=True,
                            comment="Deprecated: use status != COMPLETED instead")

    # ── Timestamps ────────────────────────────────────────────────────────────
    assigned_at    = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at    = Column(DateTime(timezone=True), nullable=True)
    started_at     = Column(DateTime(timezone=True), nullable=True)
    completed_at   = Column(DateTime(timezone=True), nullable=True)

    need = relationship("Need", back_populates="volunteer_assignments")
