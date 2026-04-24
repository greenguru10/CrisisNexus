"""
Pydantic schemas for Volunteer – request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Request Schemas ──────────────────────────────────────────────

class VolunteerCreate(BaseModel):
    """Schema for registering a new volunteer."""
    name: str = Field(..., min_length=2, max_length=150, description="Volunteer full name")
    email: Optional[str] = Field(None, description="Volunteer email for notifications")
    mobile_number: Optional[str] = Field(None, description="Mobile number for WhatsApp (e.g. +919876543210)")
    skills: List[str] = Field(
        ...,
        min_length=1,
        description="List of skill tags (e.g. ['medical', 'logistics', 'cooking'])",
    )
    location: Optional[str] = Field(None, description="Human-readable location")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    availability: bool = Field(True, description="Whether the volunteer is currently available")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Performance rating 0-5")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Priya Sharma",
                "email": "priya@example.com",
                "mobile_number": "+919876543210",
                "skills": ["medical", "first_aid", "logistics"],
                "location": "Mumbai, India",
                "latitude": 19.076,
                "longitude": 72.8777,
                "availability": True,
                "rating": 4.5,
            }
        }


class AdminVolunteerCreate(BaseModel):
    """Schema for admin creating a volunteer with just email and skills."""
    email: str = Field(..., description="Volunteer email for login and notifications")
    name: Optional[str] = Field(None, description="Full name (optional, defaults to email prefix)")
    mobile_number: Optional[str] = Field(None, description="Mobile number for WhatsApp (e.g. +919876543210)")
    skills: List[str] = Field(..., min_length=1)
    ngo_id: Optional[int] = Field(None, description="NGO ID to assign the volunteer to")

class VolunteerUpdate(BaseModel):
    """Schema for admin to update a volunteer. All fields optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[str] = Field(None)
    mobile_number: Optional[str] = Field(None)
    skills: Optional[List[str]] = Field(None, min_length=1)
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    availability: Optional[bool] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    ngo_id: Optional[int] = None


# ── Response Schemas ─────────────────────────────────────────────

class VolunteerBase(BaseModel):
    """Shared attributes for Volunteer responses."""
    id: int
    name: str
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    skills: List[str]
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability: bool
    rating: Optional[float] = None
    ngo_id: Optional[int] = None
    ngo_name: Optional[str] = None
    account_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VolunteerResponse(VolunteerBase):
    """Full volunteer response returned by endpoints."""
    pass


class MatchResult(BaseModel):
    """Result of a volunteer-need matching operation."""
    need_id: int
    volunteer_id: int
    volunteer_name: str
    match_score: float = Field(..., description="Composite match score (higher is better)")
    distance_km: float = Field(..., description="Distance between volunteer and need in km")
    skill_match: float = Field(..., description="Skill similarity score 0-1")
    message: str

