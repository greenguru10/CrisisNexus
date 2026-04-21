import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class TrailAction(str, enum.Enum):
    CREATED            = "created"
    SUBMITTED_BY_NGO   = "submitted_by_ngo"
    APPROVED_BY_ADMIN  = "approved_by_admin"
    ASSIGNED_TO_NGO    = "assigned_to_ngo"
    NGO_ACCEPTED       = "ngo_accepted"
    NGO_REJECTED       = "ngo_rejected"
    VOLUNTEER_ASSIGNED = "volunteer_assigned"
    STATUS_CHANGED     = "status_changed"
    COMPLETED          = "completed"
    RESOURCE_REQUESTED = "resource_requested"


class TaskTrail(Base):
    """Append-only audit log for every action taken on a Need."""
    __tablename__ = "task_trail"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    need_id     = Column(Integer, ForeignKey("needs.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role  = Column(String(20), nullable=False)   # 'admin' | 'ngo' | 'volunteer' | 'system'
    actor_name  = Column(String(255), nullable=True)   # denormalized for display
    action      = Column(
        SAEnum(TrailAction, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
    )
    # Flexible JSON payload: {ngo_ids, ngo_names, volunteer_ids, volunteer_names, note, old_status, new_status}
    detail_json = Column(JSONB, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
