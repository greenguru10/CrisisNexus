"""
Pool routes – NGOs request volunteer pool lending; Admin approves/rejects.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.ngo import NGO, NgoStatus
from models.volunteer import Volunteer
from models.pool_request import VolunteerPoolRequest, PoolAssignment, PoolRequestStatus
from schemas.pool_schema import (
    PoolRequestCreate, PoolRequestApprove, PoolRequestReject, PoolRequestResponse,
)
from dependencies.auth_dependency import get_current_admin, get_current_ngo_coordinator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pool", tags=["Volunteer Pool"])


@router.post("/request", response_model=PoolRequestResponse, status_code=201)
def create_pool_request(
    payload: PoolRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] Request to borrow volunteers from the global pool or another NGO."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    # Optional: validate the linked need exists and is assigned to this NGO
    if payload.need_id:
        from models.need import Need
        from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus
        need = db.query(Need).filter(Need.id == payload.need_id).first()
        if not need:
            raise HTTPException(status_code=404, detail=f"Need id={payload.need_id} not found")
        ngo_assign = db.query(NeedNGOAssignment).filter_by(
            need_id=payload.need_id, ngo_id=ngo.id, status=NgoAssignStatus.ACCEPTED
        ).first()
        if not ngo_assign:
            raise HTTPException(
                status_code=403,
                detail="This task is not assigned to your NGO — cannot link pool request to it",
            )

    pool_req = VolunteerPoolRequest(
        requesting_ngo_id=ngo.id,
        source_ngo_id=payload.source_ngo_id,
        need_id=payload.need_id,
        required_skills=payload.required_skills or [],
        volunteers_needed=payload.volunteers_needed,
        reason=payload.reason,
        duration_days=payload.duration_days,
    )
    db.add(pool_req)
    db.commit()
    db.refresh(pool_req)
    logger.info("NGO %s created pool request id=%d (need_id=%s)", ngo.name, pool_req.id, payload.need_id)
    return pool_req


@router.get("/my-requests", response_model=List[PoolRequestResponse])
def my_pool_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] View own pool requests and their statuses."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    return db.query(VolunteerPoolRequest).filter(
        VolunteerPoolRequest.requesting_ngo_id == ngo.id
    ).order_by(VolunteerPoolRequest.created_at.desc()).all()


@router.get("/requests", response_model=List[PoolRequestResponse])
def list_pool_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] View all pool requests."""
    query = db.query(VolunteerPoolRequest)
    if status_filter:
        query = query.filter(VolunteerPoolRequest.status == status_filter)
    return query.order_by(VolunteerPoolRequest.created_at.desc()).all()


@router.post("/request/{request_id}/approve", response_model=PoolRequestResponse)
def approve_pool_request(
    request_id: int,
    payload: PoolRequestApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Select volunteers for pool request. Moves to PENDING_LENDERS for secondary NGO approval."""
    req = db.query(VolunteerPoolRequest).filter(VolunteerPoolRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Pool request not found")
    if req.status != PoolRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

    # Validate volunteers exist and are approved
    volunteers = []
    for vol_id in payload.volunteer_ids:
        vol = db.query(Volunteer).filter(Volunteer.id == vol_id).first()
        if not vol:
            raise HTTPException(status_code=404, detail=f"Volunteer id={vol_id} not found")

        if req.source_ngo_id and vol.ngo_id != req.source_ngo_id:
            raise HTTPException(
                status_code=400,
                detail=f"Volunteer id={vol_id} is not from required source NGO id={req.source_ngo_id}",
            )

        # Prevent cross-request conflicts: same volunteer cannot be in another active
        # pending/approved pool assignment at the same time.
        conflicting = db.query(PoolAssignment).filter(
            PoolAssignment.volunteer_id == vol_id,
            PoolAssignment.is_active == True,
            PoolAssignment.status.in_(["pending", "approved"]),
        ).first()
        if conflicting:
            raise HTTPException(
                status_code=409,
                detail=f"Volunteer id={vol_id} is already tied to another active pool request",
            )
        volunteers.append(vol)

    now = datetime.now(timezone.utc)
    ends = now + timedelta(days=req.duration_days)

    # Transition to PENDING_LENDERS (Multi-NGO coordination)
    req.status = PoolRequestStatus.PENDING_LENDERS
    req.admin_notes = payload.admin_notes
    req.starts_at = now
    req.ends_at = ends
    req.resolved_at = now

    # Create PoolAssignment records for each volunteer (status: pending)
    for vol in volunteers:
        assignment = PoolAssignment(
            pool_request_id=req.id,
            volunteer_id=vol.id,
            borrowing_ngo_id=req.requesting_ngo_id,
            lending_ngo_id=vol.ngo_id, # Source NGO
            status="pending",
            is_active=True,
            expires_at=ends,
        )
        db.add(assignment)

    db.commit()
    db.refresh(req)
    logger.info("Admin %s selected %d volunteers for pool request id=%d — now awaiting lender approvals",
                current_user.email, len(payload.volunteer_ids), request_id)
    return req


@router.post("/request/{request_id}/reject", response_model=PoolRequestResponse)
def reject_pool_request(
    request_id: int,
    payload: PoolRequestReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Reject a pool request."""
    req = db.query(VolunteerPoolRequest).filter(VolunteerPoolRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Pool request not found")
    if req.status != PoolRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

    req.status = PoolRequestStatus.REJECTED
    req.admin_notes = payload.admin_notes
    req.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    return req


@router.get("/lending-requests")
def list_lending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] View pool borrow requests for your NGO's volunteers."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    
    assignments = db.query(PoolAssignment).filter(
        PoolAssignment.lending_ngo_id == ngo.id,
        PoolAssignment.status == "pending"
    ).all()
    
    results = []
    for a in assignments:
        req = db.query(VolunteerPoolRequest).filter_by(id=a.pool_request_id).first()
        vol = db.query(Volunteer).filter_by(id=a.volunteer_id).first()
        borrower = db.query(NGO).filter_by(id=a.borrowing_ngo_id).first()
        results.append({
            "assignment_id": a.id,
            "volunteer_name": vol.name if vol else "Unknown",
            "borrower_name": borrower.name if borrower else "Unknown",
            "reason": req.reason if req else "",
            "ends_at": a.expires_at,
            "status": a.status
        })
    return results


@router.post("/assignment/{assignment_id}/approve")
def approve_lending(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] Approve lending a specific volunteer to the pool."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    a = db.query(PoolAssignment).filter_by(id=assignment_id, lending_ngo_id=ngo.id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Lending request not found")
    
    a.status = "approved"
    
    # Mark volunteer as unavailable immediately upon lending approval
    volunteer = db.query(Volunteer).filter_by(id=a.volunteer_id).first()
    if volunteer:
        volunteer.availability = False
    
    # Check if this was the last pending assignment for the pool request
    req = db.query(VolunteerPoolRequest).filter_by(id=a.pool_request_id).first()
    
    # Audit Trail (Log each volunteer lending approval)
    if req and req.need_id:
        from services.trail_service import add_trail_entry
        from models.task_trail import TrailAction
        add_trail_entry(
            db, need_id=req.need_id, action=TrailAction.POOL_ASSIGNED,
            actor_id=current_user.id, actor_role="ngo", actor_name=ngo.name,
            detail={
                "pool_request_id": req.id,
                "volunteer_ids": [volunteer.id],
                "volunteer_names": [volunteer.name],
                "borrowing_ngo_id": req.requesting_ngo_id,
                "lending_ngo_name": ngo.name
            },
        )

    if req:
        remaining = db.query(PoolAssignment).filter_by(
            pool_request_id=req.id, status="pending"
        ).count()
        if remaining == 0:
            req.status = PoolRequestStatus.APPROVED
            logger.info("Pool Request %d fully approved and active", req.id)
            
    db.commit()
    return {"message": "Lending approved"}


@router.post("/assignment/{assignment_id}/reject")
def reject_lending(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] Reject lending a specific volunteer."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    a = db.query(PoolAssignment).filter_by(id=assignment_id, lending_ngo_id=ngo.id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Lending request not found")
    
    a.status = "rejected"
    a.is_active = False
    
    # Optional: notify Admin or mark main request as partially fulfilled / needs attention
    db.commit()
    return {"message": "Lending rejected"}
