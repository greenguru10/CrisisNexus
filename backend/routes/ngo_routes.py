"""
NGO routes – Registration, approval workflow, and coordinator management.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.user import User, UserRole, AccountStatus
from models.ngo import NGO, NgoStatus, NgoType, NGO_TYPE_LABELS
from models.volunteer import Volunteer
from models.need import Need
from schemas.ngo_schema import NgoRegister, NgoUpdate, NgoResponse, NgoSummary, NgoTypeOption, NgoApproveReject
from dependencies.auth_dependency import get_current_admin, get_current_ngo_coordinator, get_current_user
from services.auth_service import hash_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ngo", tags=["NGO Management"])


# ── Public: Get NGO type options (for dropdown) ──────────────────────────
@router.get("/types", response_model=List[NgoTypeOption])
def get_ngo_types():
    """Return all available NGO types for the registration dropdown."""
    return [
        NgoTypeOption(value=k, label=v)
        for k, v in NGO_TYPE_LABELS.items()
    ]


# ── Public: Get list of approved NGO names (for volunteer signup) ────────
@router.get("/names", response_model=List[dict])
def get_approved_ngo_names(db: Session = Depends(get_db)):
    """Return names and IDs of all approved NGOs (used in volunteer signup dropdown)."""
    ngos = db.query(NGO.id, NGO.name).filter(NGO.status == NgoStatus.APPROVED).order_by(NGO.name).all()
    return [{"id": n.id, "name": n.name} for n in ngos]


# ── Admin: List all NGOs ─────────────────────────────────────────────────
@router.get("", response_model=List[NgoSummary])
def list_ngos(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] List all NGOs with optional status filter."""
    query = db.query(NGO)
    if status_filter:
        query = query.filter(NGO.status == status_filter)
    ngos = query.order_by(NGO.created_at.desc()).all()

    result = []
    for ngo in ngos:
        vol_count = db.query(func.count(Volunteer.id)).filter(Volunteer.ngo_id == ngo.id).scalar() or 0
        need_count = db.query(func.count(Need.id)).filter(Need.ngo_id == ngo.id).scalar() or 0
        summary = NgoSummary(
            id=ngo.id, name=ngo.name, ngo_type=ngo.ngo_type.value,
            status=ngo.status.value, location=ngo.location,
            volunteer_count=vol_count, need_count=need_count,
        )
        result.append(summary)
    return result


# ── Admin: List pending NGOs ─────────────────────────────────────────────
@router.get("/pending", response_model=List[NgoResponse])
def list_pending_ngos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] List all NGOs awaiting approval."""
    ngos = db.query(NGO).filter(NGO.status == NgoStatus.PENDING).order_by(NGO.created_at.desc()).all()
    return ngos


# ── Admin: Get single NGO ────────────────────────────────────────────────
@router.get("/{ngo_id}", response_model=NgoResponse)
def get_ngo(
    ngo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single NGO by ID. Admin sees all; NGO coordinator sees own."""
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    if current_user.role == UserRole.NGO and ngo.coordinator_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return ngo


# ── Admin: Approve NGO ───────────────────────────────────────────────────
@router.post("/{ngo_id}/approve")
def approve_ngo(
    ngo_id: int,
    payload: NgoApproveReject = NgoApproveReject(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Approve a pending NGO registration."""
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    if ngo.status == NgoStatus.APPROVED:
        raise HTTPException(status_code=400, detail="NGO is already approved")

    ngo.status = NgoStatus.APPROVED
    if payload.admin_notes:
        ngo.admin_notes = payload.admin_notes

    # Also activate coordinator user account
    if ngo.coordinator_user_id:
        coord_user = db.query(User).filter(User.id == ngo.coordinator_user_id).first()
        if coord_user:
            coord_user.account_status = AccountStatus.APPROVED

    db.commit()
    logger.info("Admin %s approved NGO id=%d (%s)", current_user.email, ngo_id, ngo.name)

    # Send welcome email to coordinator
    if ngo.coordinator_user_id:
        coord = db.query(User).filter(User.id == ngo.coordinator_user_id).first()
        if coord:
            from services.email_service import send_welcome_email
            background_tasks.add_task(send_welcome_email, coord.email, "ngo")

    return {"message": f"NGO '{ngo.name}' has been approved.", "ngo_id": ngo_id}


# ── Admin: Reject NGO ────────────────────────────────────────────────────
@router.post("/{ngo_id}/reject")
def reject_ngo(
    ngo_id: int,
    payload: NgoApproveReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Reject a pending NGO registration."""
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    ngo.status = NgoStatus.REJECTED
    ngo.admin_notes = payload.admin_notes

    if ngo.coordinator_user_id:
        coord_user = db.query(User).filter(User.id == ngo.coordinator_user_id).first()
        if coord_user:
            coord_user.account_status = AccountStatus.REJECTED

    db.commit()
    logger.info("Admin %s rejected NGO id=%d (%s)", current_user.email, ngo_id, ngo.name)
    return {"message": f"NGO '{ngo.name}' has been rejected."}


# ── Admin: Update NGO ────────────────────────────────────────────────────
@router.put("/{ngo_id}", response_model=NgoResponse)
def update_ngo(
    ngo_id: int,
    payload: NgoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Update NGO details."""
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "ngo_type" and value:
            value = NgoType(value)
        setattr(ngo, field, value)

    db.commit()
    db.refresh(ngo)
    return ngo


# ── Admin: Delete NGO ────────────────────────────────────────────────────
@router.delete("/{ngo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ngo(
    ngo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Delete an NGO and disassociate volunteers/needs."""
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    # Disassociate volunteers (set ngo_id → NULL)
    db.query(Volunteer).filter(Volunteer.ngo_id == ngo_id).update({"ngo_id": None})
    db.query(Need).filter(Need.ngo_id == ngo_id).update({"ngo_id": None})

    db.delete(ngo)
    db.commit()
    logger.info("Admin %s deleted NGO id=%d", current_user.email, ngo_id)


# ── NGO Coordinator: Get my NGO ──────────────────────────────────────────
@router.get("/me/details", response_model=NgoResponse)
def get_my_ngo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] Get own NGO details."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found for this coordinator")
    return ngo


# ── NGO Coordinator: Update my NGO ───────────────────────────────────────
@router.put("/me/details", response_model=NgoResponse)
def update_my_ngo(
    payload: NgoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] Update own NGO details (editable fields only)."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found for this coordinator")

    # Coordinators can update these fields:
    # - name, ngo_type, registration_number, description, location, contact_email, contact_phone
    # They cannot change: status, coordinator_user_id, admin_notes
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "ngo_type" and value:
            value = NgoType(value)
        setattr(ngo, field, value)

    db.commit()
    db.refresh(ngo)
    logger.info("NGO coordinator %s updated their NGO id=%d (%s)", current_user.email, ngo.id, ngo.name)
    return ngo
