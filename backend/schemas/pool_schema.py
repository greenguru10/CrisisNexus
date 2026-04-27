"""
Pool request schemas – Pydantic models for volunteer pool borrowing.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PoolRequestCreate(BaseModel):
    source_ngo_id: Optional[int] = None
    need_id: Optional[int] = None          # Task this pool request is for (optional)
    required_skills: Optional[List[str]] = []
    volunteers_needed: int = Field(1, ge=1)
    reason: str = Field(..., min_length=10)
    duration_days: int = Field(7, ge=1, le=90)


class PoolRequestApprove(BaseModel):
    volunteer_ids: List[int] = Field(..., min_length=1)
    admin_notes: Optional[str] = None


class PoolRequestReject(BaseModel):
    admin_notes: str


class PoolRequestResponse(BaseModel):
    id: int
    requesting_ngo_id: int
    source_ngo_id: Optional[int]
    need_id: Optional[int]
    required_skills: Optional[List[str]]
    volunteers_needed: int
    assigned_volunteer_ids: Optional[List[int]]
    reason: str
    duration_days: int
    status: str
    admin_notes: Optional[str]
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    created_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}
