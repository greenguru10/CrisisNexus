import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
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
