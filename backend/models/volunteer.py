"""
Volunteer model – represents a volunteer who can be matched to needs.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from database import Base


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Volunteer id={self.id} name={self.name} available={self.availability}>"

