import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class NgoAssignStatus(str, enum.Enum):
    """
    Per-NGO allocation status.
    State machine: PENDING → ACCEPTED → IN_PROGRESS → COMPLETED
    REJECTED = NGO refused or was removed by Admin.
    """
    PENDING     = "pending"
    ACCEPTED    = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    REJECTED    = "rejected"


class NeedNGOAssignment(Base):
    """
    Junction table: Admin assigns a Need to one or more NGOs.
    Each row = one NGO's independent allocation for that need.

    State machine (enforced in task_routes.py):
        PENDING → ACCEPTED → IN_PROGRESS → COMPLETED

    Global need becomes COMPLETED only when ALL non-rejected NGO
    allocations reach COMPLETED status.
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
    resolved_at = Column(DateTime(timezone=True), nullable=True)   # when accepted / rejected

    # ── Timestamps for lifecycle stages ───────────────────────────────────────
    started_at    = Column(DateTime(timezone=True), nullable=True)
    completed_at  = Column(DateTime(timezone=True), nullable=True)
    completed_by_volunteer_id = Column(
        Integer,
        ForeignKey("volunteers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Which volunteer from this NGO triggered completion",
    )

    # ── Backward-compat: is_completed boolean ────────────────────────────────
    # Legacy code may still read this; keep it in sync via the property below.
    # The authoritative state is now `status == COMPLETED`.
    _is_completed_col = Column(
        "is_completed", Boolean, nullable=False, default=False, index=True,
        comment="Deprecated: use status == COMPLETED instead",
    )

    @property
    def is_completed(self) -> bool:
        return self.status == NgoAssignStatus.COMPLETED

    @is_completed.setter
    def is_completed(self, value: bool):
        """Legacy setter – kept so old code that does `ngo_assignment.is_completed = True` still works."""
        if value:
            self.status = NgoAssignStatus.COMPLETED
        # Setting False has no safe meaning in the state machine; ignore silently.

    need = relationship("Need", back_populates="ngo_assignments")
