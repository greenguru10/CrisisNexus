from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class NeedVolunteerAssignment(Base):
    """
    Tracks which volunteers are assigned to a need by an NGO.
    Supports team assignment (multiple volunteers, same need).
    Completion by any one volunteer = task complete for all on that need for that NGO.
    """
    __tablename__ = "need_volunteer_assignments"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    need_id        = Column(Integer, ForeignKey("needs.id",       ondelete="CASCADE"), nullable=False, index=True)
    volunteer_id   = Column(Integer, ForeignKey("volunteers.id",  ondelete="CASCADE"), nullable=False, index=True)
    ngo_id         = Column(Integer, ForeignKey("ngos.id",        ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id",       ondelete="SET NULL"), nullable=True)
    is_active      = Column(Boolean, nullable=False, default=True)  # False = removed/unassigned
    assigned_at    = Column(DateTime(timezone=True), server_default=func.now())
