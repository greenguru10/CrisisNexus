"""
VolunteerPoolRequest model – NGO requests to borrow volunteers from another NGO or global pool.
Volunteer's primary ngo_id does NOT change; pool assignment is temporary.
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from database import Base


class PoolRequestStatus(str, enum.Enum):
    PENDING = "pending"
    PENDING_LENDERS = "pending_lenders"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    COMPLETED = "completed"


class VolunteerPoolRequest(Base):
    """ORM model for volunteer_pool_requests. NGO asks Admin to borrow volunteers."""

    __tablename__ = "volunteer_pool_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requesting_ngo_id = Column(Integer, ForeignKey("ngos.id", ondelete="CASCADE"), nullable=False, index=True)
    # source_ngo_id = NULL means borrow from any available global pool
    source_ngo_id = Column(Integer, ForeignKey("ngos.id", ondelete="CASCADE"), nullable=True, index=True,
                           comment="Which NGO to borrow from; NULL = any available")
    # Optionally link to a specific task
    need_id = Column(Integer, ForeignKey("needs.id", ondelete="SET NULL"), nullable=True, index=True,
                     comment="Task this pool request is associated with (optional)")
    # Skills required from the pool volunteers
    required_skills = Column(ARRAY(String), nullable=True, default=list)
    volunteers_needed = Column(Integer, nullable=False, default=1)
    reason = Column(Text, nullable=False)
    duration_days = Column(Integer, nullable=False, default=7, comment="How many days the borrow lasts")
    status = Column(SAEnum(PoolRequestStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=PoolRequestStatus.PENDING, index=True)
    admin_notes = Column(Text, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    pool_assignments = relationship("PoolAssignment", back_populates="pool_request", cascade="all, delete-orphan")

    @property
    def assigned_volunteer_ids(self):
        return [a.volunteer_id for a in self.pool_assignments if a.is_active]

    def __repr__(self):
        return f"<VolunteerPoolRequest id={self.id} from={self.requesting_ngo_id} status={self.status}>"


class PoolAssignment(Base):
    """Tracks which volunteers are temporarily assigned to a borrowing NGO."""

    __tablename__ = "pool_assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pool_request_id = Column(Integer, ForeignKey("volunteer_pool_requests.id", ondelete="CASCADE"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True)
    borrowing_ngo_id = Column(Integer, ForeignKey("ngos.id", ondelete="CASCADE"), nullable=False)
    lending_ngo_id = Column(Integer, ForeignKey("ngos.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="pending", comment="pending|approved|rejected")
    is_active = Column(Boolean, nullable=False, default=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    pool_request = relationship("VolunteerPoolRequest", back_populates="pool_assignments")

    def __repr__(self):
        return f"<PoolAssignment vol={self.volunteer_id} → ngo={self.borrowing_ngo_id}>"
