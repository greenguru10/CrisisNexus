"""
Resource routes – Admin manages global inventory; NGOs submit and track requests.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole
from models.ngo import NGO, NgoStatus
from models.resource import ResourceInventory, ResourceRequest, ResourceStatus, RequestStatus
from schemas.resource_schema import (
    ResourceCreate, ResourceUpdate, ResourceResponse,
    ResourceRequestCreate, ResourceRequestApprove, ResourceRequestReject, ResourceRequestResponse,
)
from dependencies.auth_dependency import (
    get_current_admin, get_current_ngo_coordinator, get_current_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resource", tags=["Resource Inventory"])


# ═══════════════════════════════════════════════════════════════════
# ADMIN: Inventory CRUD
# ═══════════════════════════════════════════════════════════════════

@router.post("", response_model=ResourceResponse, status_code=201)
def create_resource(
    payload: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Add a new resource to the global inventory."""
    resource = ResourceInventory(**payload.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    logger.info("Admin %s added resource: %s", current_user.email, resource.name)
    return resource


@router.get("", response_model=List[ResourceResponse])
def list_resources(
    resource_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] List all resources with optional filters."""
    query = db.query(ResourceInventory)
    if resource_type:
        query = query.filter(ResourceInventory.resource_type == resource_type)
    if status_filter:
        query = query.filter(ResourceInventory.status == status_filter)
    return query.order_by(ResourceInventory.resource_type).all()


@router.put("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Update a resource."""
    resource = db.query(ResourceInventory).filter(ResourceInventory.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)
    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Delete a resource from inventory."""
    resource = db.query(ResourceInventory).filter(ResourceInventory.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.delete(resource)
    db.commit()


# ═══════════════════════════════════════════════════════════════════
# NGO: Submit Resource Requests
# ═══════════════════════════════════════════════════════════════════

@router.post("/request", response_model=ResourceRequestResponse, status_code=201)
def create_resource_request(
    payload: ResourceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] Submit a resource request to Admin."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found for this coordinator")

    req = ResourceRequest(
        requesting_ngo_id=ngo.id,
        **payload.model_dump(),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    logger.info("NGO %s submitted resource request id=%d", ngo.name, req.id)
    return req


@router.get("/my-requests", response_model=List[ResourceRequestResponse])
def my_resource_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] View own resource requests and their statuses."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    return db.query(ResourceRequest).filter(
        ResourceRequest.requesting_ngo_id == ngo.id
    ).order_by(ResourceRequest.created_at.desc()).all()


# ═══════════════════════════════════════════════════════════════════
# ADMIN: Manage Resource Requests
# ═══════════════════════════════════════════════════════════════════

@router.get("/requests", response_model=List[ResourceRequestResponse])
def list_resource_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] View all NGO resource requests."""
    query = db.query(ResourceRequest)
    if status_filter:
        query = query.filter(ResourceRequest.status == status_filter)
    return query.order_by(ResourceRequest.created_at.desc()).all()


@router.post("/request/{request_id}/approve", response_model=ResourceRequestResponse)
def approve_resource_request(
    request_id: int,
    payload: ResourceRequestApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Approve a resource request and allocate inventory."""
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

    # Validate and update inventory item
    inventory_item = db.query(ResourceInventory).filter(
        ResourceInventory.id == payload.resource_inventory_id
    ).first()
    if not inventory_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if inventory_item.quantity < payload.quantity_allocated:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock: {inventory_item.quantity} {inventory_item.unit} available",
        )

    # Deduct from inventory
    inventory_item.quantity -= payload.quantity_allocated
    if inventory_item.quantity <= 0:
        inventory_item.status = ResourceStatus.DEPLETED
    inventory_item.allocated_to_ngo_id = req.requesting_ngo_id

    # Update request
    req.status = RequestStatus.APPROVED
    req.allocated_resource_id = payload.resource_inventory_id
    req.quantity_allocated = payload.quantity_allocated
    req.admin_notes = payload.admin_notes
    req.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(req)
    logger.info("Admin %s approved resource request id=%d", current_user.email, request_id)
    return req


@router.post("/request/{request_id}/reject", response_model=ResourceRequestResponse)
def reject_resource_request(
    request_id: int,
    payload: ResourceRequestReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Reject a resource request."""
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

    req.status = RequestStatus.REJECTED
    req.admin_notes = payload.admin_notes
    req.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    return req


# ═══════════════════════════════════════════════════════════════════
# PHASE 2 — Inventory name lookup + NGO Contributions
# ═══════════════════════════════════════════════════════════════════

from models.resource import InventoryContribution, ContributionStatus
from pydantic import BaseModel as _BM


class ContributeIn(_BM):
    resource_type: str
    name: str
    quantity: float
    unit: str = "units"
    notes: str | None = None


class ContributionNoteIn(_BM):
    admin_notes: str | None = None


# ── GET: inventory name+id list (for typeahead / dropdown) ─────
@router.get("/inventory/names")
def inventory_names(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns a lightweight id+name+quantity list for all inventory items (typeahead support)."""
    items = db.query(ResourceInventory.id, ResourceInventory.name, ResourceInventory.quantity, ResourceInventory.unit).all()
    return [{"id": i.id, "name": i.name, "quantity": i.quantity, "unit": i.unit} for i in items]


# ── NGO: submit inventory contribution ─────────────────────────
@router.post("/contribute", status_code=201)
def contribute_to_inventory(
    payload: ContributeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO] Suggest items to donate to the global inventory. Admin must approve."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    contrib = InventoryContribution(
        contributing_ngo_id=ngo.id,
        resource_type=payload.resource_type,
        name=payload.name,
        quantity=payload.quantity,
        unit=payload.unit,
        notes=payload.notes,
    )
    db.add(contrib)
    db.commit()
    db.refresh(contrib)
    logger.info("NGO %s contributed %s x%.1f", ngo.name, payload.name, payload.quantity)
    return {"message": "Contribution submitted for Admin review", "id": contrib.id}


# ── NGO: my contributions ───────────────────────────────────────
@router.get("/my-contributions")
def my_contributions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    rows = db.query(InventoryContribution).filter_by(contributing_ngo_id=ngo.id).order_by(InventoryContribution.created_at.desc()).all()
    return [_contrib_out(c, db) for c in rows]


# ── ADMIN: list pending contributions ──────────────────────────
@router.get("/contributions")
def list_contributions(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] List all pending/approved/rejected NGO inventory contributions."""
    q = db.query(InventoryContribution)
    if status_filter:
        q = q.filter(InventoryContribution.status == status_filter)
    rows = q.order_by(InventoryContribution.created_at.desc()).all()
    return [_contrib_out(c, db) for c in rows]


# ── ADMIN: approve contribution → merge qty ────────────────────
@router.post("/contributions/{contrib_id}/approve")
def approve_contribution(
    contrib_id: int,
    body: ContributionNoteIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Approve an NGO contribution. Merges quantity into existing inventory item by name."""
    contrib = db.query(InventoryContribution).filter_by(id=contrib_id).first()
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribution not found")
    if contrib.status != ContributionStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Already {contrib.status.value}")

    # Find existing item by name (case-insensitive)
    inv_item = db.query(ResourceInventory).filter(
        ResourceInventory.name.ilike(contrib.name)
    ).first()

    if inv_item:
        inv_item.quantity += contrib.quantity
        contrib.merged_into_id = inv_item.id
        logger.info("Merged %.1f %s into inventory item id=%d", contrib.quantity, contrib.name, inv_item.id)
    else:
        # Create new item if no match
        new_item = ResourceInventory(
            name=contrib.name, resource_type=contrib.resource_type,
            quantity=contrib.quantity, unit=contrib.unit,
        )
        db.add(new_item)
        db.flush()
        contrib.merged_into_id = new_item.id
        logger.info("Created new inventory item '%s' from contribution id=%d", contrib.name, contrib_id)

    contrib.status = ContributionStatus.APPROVED
    contrib.admin_notes = body.admin_notes
    contrib.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Contribution approved and merged into inventory"}


# ── ADMIN: reject contribution ─────────────────────────────────
@router.post("/contributions/{contrib_id}/reject")
def reject_contribution(
    contrib_id: int,
    body: ContributionNoteIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    contrib = db.query(InventoryContribution).filter_by(id=contrib_id).first()
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribution not found")
    contrib.status = ContributionStatus.REJECTED
    contrib.admin_notes = body.admin_notes
    contrib.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Contribution rejected"}


def _contrib_out(c: InventoryContribution, db: Session) -> dict:
    ngo = db.query(NGO).filter(NGO.id == c.contributing_ngo_id).first()
    return {
        "id": c.id,
        "ngo_name": ngo.name if ngo else "?",
        "resource_type": c.resource_type.value if hasattr(c.resource_type, "value") else c.resource_type,
        "name": c.name, "quantity": c.quantity, "unit": c.unit,
        "notes": c.notes, "status": c.status.value if hasattr(c.status, "value") else c.status,
        "admin_notes": c.admin_notes,
        "merged_into_id": c.merged_into_id,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }

