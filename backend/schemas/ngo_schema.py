"""
NGO schemas – Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ── NGO Type & Status choices ─────────────────────────────────────────────

NGO_TYPES = [
    "disaster_relief", "medical", "food_distribution", "education",
    "logistics", "shelter", "rehabilitation", "water_sanitation",
    "child_welfare", "others"
]

NGO_TYPE_LABELS = {
    "disaster_relief": "Disaster Relief",
    "medical": "Medical & Health",
    "food_distribution": "Food Distribution",
    "education": "Education",
    "logistics": "Logistics & Transport",
    "shelter": "Shelter & Housing",
    "rehabilitation": "Rehabilitation",
    "water_sanitation": "Water & Sanitation",
    "child_welfare": "Child Welfare",
    "others": "Others",
}


# ── Request schemas ───────────────────────────────────────────────────────

class NgoRegister(BaseModel):
    """Used by public NGO coordinator registration."""
    name: str = Field(..., min_length=3, max_length=255, description="Unique NGO name")
    ngo_type: str = Field(..., description="Type of NGO from the allowed list")
    registration_number: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    # Coordinator account credentials
    coordinator_email: EmailStr
    coordinator_password: str = Field(..., min_length=6)


class NgoUpdate(BaseModel):
    """Admin/coordinator can update NGO details."""
    name: Optional[str] = None
    ngo_type: Optional[str] = None
    registration_number: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class NgoApproveReject(BaseModel):
    """Admin approval/rejection payload."""
    admin_notes: Optional[str] = None


# ── Response schemas ──────────────────────────────────────────────────────

class NgoResponse(BaseModel):
    id: int
    name: str
    ngo_type: str
    registration_number: Optional[str]
    description: Optional[str]
    location: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    status: str
    coordinator_user_id: Optional[int]
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NgoSummary(BaseModel):
    """Lightweight NGO info for lists and dropdowns."""
    id: int
    name: str
    ngo_type: str
    status: str
    location: Optional[str]
    volunteer_count: Optional[int] = 0
    need_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class NgoTypeOption(BaseModel):
    value: str
    label: str
