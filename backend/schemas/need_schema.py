"""
Pydantic schemas for Need – request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NeedStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"


# ── Request Schemas ──────────────────────────────────────────────

class ReportUpload(BaseModel):
    """Schema for uploading a raw NGO survey report."""
    raw_text: str = Field(
        ...,
        min_length=10,
        description="Raw unstructured text from an NGO survey report",
        json_schema_extra={
            "example": "Urgent: 200 families in Kathmandu need clean drinking water and medical supplies immediately."
        },
    )


# ── Response Schemas ─────────────────────────────────────────────

class NeedBase(BaseModel):
    """Shared attributes for Need responses."""
    id: int
    raw_text: str
    category: str
    urgency: UrgencyLevel
    people_affected: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority_score: float
    status: NeedStatus
    assigned_volunteer_id: Optional[int] = None
    assigned_volunteer_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NeedResponse(NeedBase):
    """Full need response returned by endpoints."""
    pass


class NLPExtractionResult(BaseModel):
    """Intermediate result from the NLP pipeline."""
    category: str
    urgency: UrgencyLevel
    people_affected: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
