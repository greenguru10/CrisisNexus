"""
NGO model – represents an NGO organisation and its coordinator.
Each NGO must be approved by Admin before it becomes active.
"""

import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base


class NgoType(str, enum.Enum):
    DISASTER_RELIEF = "disaster_relief"
    MEDICAL = "medical"
    FOOD_DISTRIBUTION = "food_distribution"
    EDUCATION = "education"
    LOGISTICS = "logistics"
    SHELTER = "shelter"
    REHABILITATION = "rehabilitation"
    WATER_SANITATION = "water_sanitation"
    CHILD_WELFARE = "child_welfare"
    OTHERS = "others"


class NgoStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


# Human-readable labels for the frontend dropdown
NGO_TYPE_LABELS = {
    NgoType.DISASTER_RELIEF: "Disaster Relief",
    NgoType.MEDICAL: "Medical & Health",
    NgoType.FOOD_DISTRIBUTION: "Food Distribution",
    NgoType.EDUCATION: "Education",
    NgoType.LOGISTICS: "Logistics & Transport",
    NgoType.SHELTER: "Shelter & Housing",
    NgoType.REHABILITATION: "Rehabilitation",
    NgoType.WATER_SANITATION: "Water & Sanitation",
    NgoType.CHILD_WELFARE: "Child Welfare",
    NgoType.OTHERS: "Others",
}


class NGO(Base):
    """ORM model for the ngos table."""

    __tablename__ = "ngos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    ngo_type = Column(SAEnum(NgoType, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=NgoType.OTHERS)
    registration_number = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    status = Column(
        SAEnum(NgoStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=NgoStatus.PENDING,
        index=True,
        comment="pending|approved|rejected|suspended — Admin controls this",
    )
    # The user_id of the NGO coordinator account
    coordinator_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    admin_notes = Column(Text, nullable=True, comment="Admin rejection/approval notes")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NGO id={self.id} name={self.name} status={self.status}>"
