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

    pool_req = VolunteerPoolRequest(
        requesting_ngo_id=ngo.id,
        source_ngo_id=payload.source_ngo_id,
        required_skills=payload.required_skills or [],
        volunteers_needed=payload.volunteers_needed,
        reason=payload.reason,
        duration_days=payload.duration_days,
    )
    db.add(pool_req)
    db.commit()
    db.refresh(pool_req)
    logger.info("NGO %s created pool request id=%d", ngo.name, pool_req.id)
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
    """[ADMIN] Approve a pool request and assign specific volunteers."""
    req = db.query(VolunteerPoolRequest).filter(VolunteerPoolRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Pool request not found")
    if req.status != PoolRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

    # Validate volunteers exist and are approved
    for vol_id in payload.volunteer_ids:
        vol = db.query(Volunteer).filter(Volunteer.id == vol_id).first()
        if not vol:
            raise HTTPException(status_code=404, detail=f"Volunteer id={vol_id} not found")

    now = datetime.now(timezone.utc)
    ends = now + timedelta(days=req.duration_days)

    req.status = PoolRequestStatus.APPROVED
    req.assigned_volunteer_ids = payload.volunteer_ids
    req.admin_notes = payload.admin_notes
    req.starts_at = now
    req.ends_at = ends
    req.resolved_at = now

    # Create PoolAssignment records for each volunteer
    for vol_id in payload.volunteer_ids:
        assignment = PoolAssignment(
            pool_request_id=req.id,
            volunteer_id=vol_id,
            borrowing_ngo_id=req.requesting_ngo_id,
            is_active=True,
            expires_at=ends,
        )
        db.add(assignment)

    db.commit()
    db.refresh(req)
    logger.info("Admin %s approved pool request id=%d — assigned %d volunteers",
                current_user.email, request_id, len(payload.volunteer_ids))
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
