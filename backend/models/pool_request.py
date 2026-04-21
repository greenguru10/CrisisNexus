"""
VolunteerPoolRequest model – NGO requests to borrow volunteers from another NGO or global pool.
Volunteer's primary ngo_id does NOT change; pool assignment is temporary.
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from database import Base


class PoolRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    COMPLETED = "completed"


class VolunteerPoolRequest(Base):
    """ORM model for volunteer_pool_requests. NGO asks Admin to borrow volunteers."""

    __tablename__ = "volunteer_pool_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requesting_ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=False, index=True)
    # source_ngo_id = NULL means borrow from any available global pool
    source_ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=True, index=True,
                           comment="Which NGO to borrow from; NULL = any available")
    # Skills required from the pool volunteers
    required_skills = Column(ARRAY(String), nullable=True, default=list)
    volunteers_needed = Column(Integer, nullable=False, default=1)
    # Admin populates this on approval
    assigned_volunteer_ids = Column(ARRAY(Integer), nullable=True, default=list,
                                    comment="Volunteer IDs Admin approved for pool")
    reason = Column(Text, nullable=False)
    duration_days = Column(Integer, nullable=False, default=7, comment="How many days the borrow lasts")
    status = Column(SAEnum(PoolRequestStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=PoolRequestStatus.PENDING, index=True)
    admin_notes = Column(Text, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<VolunteerPoolRequest id={self.id} from={self.requesting_ngo_id} status={self.status}>"


class PoolAssignment(Base):
    """Tracks which volunteers are temporarily assigned to a borrowing NGO."""

    __tablename__ = "pool_assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pool_request_id = Column(Integer, ForeignKey("volunteer_pool_requests.id"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"), nullable=False, index=True)
    borrowing_ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<PoolAssignment vol={self.volunteer_id} → ngo={self.borrowing_ngo_id}>"
