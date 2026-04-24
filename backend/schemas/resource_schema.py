"""
Resource schemas – Pydantic models for resource inventory and requests.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Resource Inventory ────────────────────────────────────────────────────

class ResourceCreate(BaseModel):
    resource_type: str
    name: str
    quantity: float = Field(..., gt=0)
    unit: str = "units"
    location: Optional[str] = None
    notes: Optional[str] = None


class ResourceUpdate(BaseModel):
    resource_type: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ResourceResponse(BaseModel):
    id: int
    resource_type: str
    name: str
    quantity: float
    unit: str
    location: Optional[str]
    status: str
    allocated_to_ngo_id: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Resource Requests ─────────────────────────────────────────────────────

class ResourceRequestCreate(BaseModel):
    resource_inventory_id: int
    resource_type: str
    quantity_requested: float = Field(..., gt=0)
    unit: str = "units"
    reason: str = Field(..., min_length=3)
    urgency: str = "medium"
    need_id: Optional[int] = None


class ResourceRequestApprove(BaseModel):
    resource_inventory_id: int
    quantity_allocated: float
    admin_notes: Optional[str] = None


class ResourceRequestReject(BaseModel):
    admin_notes: str


class ResourceRequestResponse(BaseModel):
    id: int
    requesting_ngo_id: int
    resource_type: str
    quantity_requested: float
    unit: str
    reason: str
    urgency: str
    status: str
    requested_inventory_id: Optional[int] = None
    admin_notes: Optional[str]
    allocated_resource_id: Optional[int]
    quantity_allocated: Optional[float]
    created_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}
