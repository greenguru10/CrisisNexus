"""
Volunteer routes – Add, list, update, and delete volunteers.
Updated: NGO coordinators can approve/reject their own NGO's volunteers,
add volunteers directly to their NGO, and view only their NGO's pool.
"""

import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole, AccountStatus
from models.volunteer import Volunteer, VolunteerApprovalStatus
from models.ngo import NGO, NgoStatus
from schemas.volunteer_schema import (
    VolunteerCreate, VolunteerUpdate, VolunteerResponse, AdminVolunteerCreate,
    VolunteerApprovalRequest, VolunteerRejectionRequest,
)
from dependencies.auth_dependency import get_current_user, get_current_admin, get_current_admin_or_ngo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Volunteers"])


# ── Helper: enrich volunteer with account_status from User table ──

def _enrich_volunteer_response(volunteer: Volunteer, db: Session) -> dict:
    """
    Build a VolunteerResponse-compatible dict by merging the volunteer
    record with its linked User's account_status and approval details.
    """
    vol_dict = {
        "id": volunteer.id,
        "name": volunteer.name,
        "email": volunteer.email,
        "mobile_number": volunteer.mobile_number,
        "skills": volunteer.skills or [],
        "location": volunteer.location,
        "latitude": volunteer.latitude,
        "longitude": volunteer.longitude,
        "availability": volunteer.availability,
        "rating": volunteer.rating,
        "ngo_id": volunteer.ngo_id,
        "tasks_completed": volunteer.tasks_completed,
        "created_at": volunteer.created_at,
        "updated_at": volunteer.updated_at,
        "account_status": None,
        "approval_status": volunteer.approval_status.value if volunteer.approval_status else None,
        "approval_notes": volunteer.approval_notes,
        "approved_at": volunteer.approved_at,
    }
    if volunteer.email:
        user = db.query(User).filter(User.email == volunteer.email).first()
        if user:
            vol_dict["account_status"] = user.account_status.value
    return vol_dict


@router.post("/add-volunteer", response_model=VolunteerResponse, status_code=201)
def add_volunteer(
    payload: VolunteerCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new volunteer (public endpoint).

    **Sample request body:**
    ```json
    {
        "name": "Priya Sharma",
        "email": "priya@example.com",
        "mobile_number": "+919876543210",
        "skills": ["medical", "first_aid", "logistics"],
        "location": "Mumbai, India",
        "latitude": 19.076,
        "longitude": 72.8777,
        "availability": true,
        "rating": 4.5
    }
    ```
    """
    volunteer = Volunteer(
        name=payload.name,
        email=payload.email,
        mobile_number=payload.mobile_number,
        skills=payload.skills,
        location=payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        availability=payload.availability,
        rating=payload.rating,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)

    logger.info("Registered volunteer id=%d name=%s", volunteer.id, volunteer.name)
    return _enrich_volunteer_response(volunteer, db)


@router.get("/volunteers", response_model=List[VolunteerResponse])
def list_volunteers(
    available: Optional[bool] = Query(None),
    skill: Optional[str] = Query(None),
    ngo_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List approved volunteers (User account status = APPROVED).
    Shows volunteers whose User is approved AND volunteer approval_status is APPROVED.
    - Admin: all approved volunteers; can filter by ngo_id.
    - NGO Coordinator: only their own NGO's volunteers.
    """
    query = (
        db.query(Volunteer)
        .join(User, User.email == Volunteer.email)
        .filter(User.role == UserRole.VOLUNTEER)
        .filter(User.account_status == AccountStatus.APPROVED)
        .filter(Volunteer.approval_status == VolunteerApprovalStatus.APPROVED)
    )

    # Scope to NGO
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        scope_id = ngo.id if ngo else -1
        query = query.filter(Volunteer.ngo_id == scope_id)
    elif ngo_id is not None:
        query = query.filter(Volunteer.ngo_id == ngo_id)

    if available is not None:
        query = query.filter(Volunteer.availability == available)
    if skill:
        query = query.filter(Volunteer.skills.any(skill.lower()))

    volunteers = query.order_by(Volunteer.name).offset(skip).limit(limit).all()
    return [_enrich_volunteer_response(v, db) for v in volunteers]


# ── Approval Workflow Endpoints (Admin-Only) ─────────────────────
# NOTE: /volunteers/pending MUST be declared BEFORE /volunteers/{volunteer_id}
# so FastAPI matches the static path first.

@router.get("/volunteers/pending", response_model=List[VolunteerResponse])
def list_pending_volunteers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """
    List pending volunteers.
    - Admin: all pending volunteers system-wide.
    - NGO Coordinator: only pending volunteers for their own NGO.
    
    Note: This endpoint checks Volunteer.approval_status == PENDING (new workflow).
    """
    query = db.query(Volunteer).filter(Volunteer.approval_status == VolunteerApprovalStatus.PENDING)
    
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo:
            raise HTTPException(status_code=403, detail="No NGO associated with your account")
        query = query.filter(Volunteer.ngo_id == ngo.id)
    
    pending_volunteers = query.order_by(Volunteer.created_at.desc()).all()
    return [_enrich_volunteer_response(v, db) for v in pending_volunteers]


@router.get("/volunteers/{volunteer_id}", response_model=VolunteerResponse)
def get_volunteer(volunteer_id: int, db: Session = Depends(get_db)):
    """Get a single volunteer by ID."""
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer with id {volunteer_id} not found")
    return _enrich_volunteer_response(volunteer, db)


@router.post("/volunteer/{volunteer_id}/approve")
def approve_volunteer(
    volunteer_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """
    Approve a pending volunteer.
    - Admin: can approve any volunteer.
    - NGO Coordinator: can only approve volunteers from their own NGO.
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer {volunteer_id} not found")

    # NGO coordinator scope check
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo or volunteer.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Volunteer does not belong to your NGO")

    user = db.query(User).filter(User.email == volunteer.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No linked user account found")
    if user.account_status == AccountStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Volunteer is already approved")

    user.account_status = AccountStatus.APPROVED
    db.commit()
    logger.info("%s approved volunteer id=%d (%s)", current_user.email, volunteer_id, volunteer.email)

    from services.email_service import send_onboarding_email, send_volunteer_welcome_email
    background_tasks.add_task(send_onboarding_email, volunteer.name, volunteer.email)
    background_tasks.add_task(send_volunteer_welcome_email, volunteer.name, volunteer.email)

    return {"message": f"Volunteer {volunteer.name} approved", "account_status": "approved"}


@router.post("/volunteer/{volunteer_id}/reject")
def reject_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """
    Reject a pending volunteer.
    - Admin: any volunteer.
    - NGO Coordinator: only their NGO's volunteers.
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer {volunteer_id} not found")

    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo or volunteer.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Volunteer does not belong to your NGO")

    user = db.query(User).filter(User.email == volunteer.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No linked user account found")
    if user.account_status == AccountStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Already rejected")

    user.account_status = AccountStatus.REJECTED
    db.commit()
    logger.info("%s rejected volunteer id=%d", current_user.email, volunteer_id)
    return {"message": f"Volunteer {volunteer.name} rejected", "account_status": "rejected"}


@router.post("/ngo/{ngo_id}/volunteer/{volunteer_id}/remove", status_code=status.HTTP_200_OK)
def remove_volunteer_from_ngo(
    ngo_id: int, volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """Admin or NGO Coordinator removes a volunteer from the NGO (sets ngo_id = NULL)."""
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo or ngo.id != ngo_id:
            raise HTTPException(status_code=403, detail="Access denied")
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id, Volunteer.ngo_id == ngo_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found in this NGO")
    volunteer.ngo_id = None
    db.commit()
    return {"message": f"Volunteer {volunteer.name} removed from NGO id={ngo_id}"}


@router.delete("/ngo/{ngo_id}/volunteer/{volunteer_id}", status_code=status.HTTP_200_OK)
def ngo_delete_volunteer(
    ngo_id: int, volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """
    **[ADMIN / NGO COORDINATOR]** Delete/trash a volunteer from this NGO.
    
    - Admin: can delete any volunteer.
    - NGO Coordinator: can only delete volunteers from their own NGO.
    
    This permanently deletes the volunteer and their login account.
    The email becomes available for re-registration.
    """
    # NGO scope check
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo or ngo.id != ngo_id:
            raise HTTPException(status_code=403, detail="Access denied - not your NGO")
    
    # Find volunteer - must belong to this NGO
    volunteer = db.query(Volunteer).filter(
        Volunteer.id == volunteer_id, 
        Volunteer.ngo_id == ngo_id
    ).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found in this NGO")
    
    vol_name = volunteer.name
    vol_email = volunteer.email
    
    # Delete login account (User record) so email is freed up
    if volunteer.email:
        user_record = db.query(User).filter(User.email == volunteer.email).first()
        if user_record:
            db.delete(user_record)
            logger.info("%s deleted user account for volunteer email=%s", current_user.email, volunteer.email)
    
    # Delete volunteer profile
    db.delete(volunteer)
    db.commit()
    
    logger.info(
        "%s (role=%s) deleted volunteer id=%d (name=%s, email=%s) from NGO id=%d",
        current_user.email, current_user.role.value, volunteer_id, vol_name, vol_email, ngo_id
    )
    
    return {
        "message": f"Volunteer {vol_name} has been permanently deleted from NGO id={ngo_id}",
        "volunteer_id": volunteer_id,
        "volunteer_name": vol_name,
        "volunteer_email": vol_email,
    }


# ── Admin-Only CRUD Endpoints ───────────────────────────────────

import secrets
from services.auth_service import hash_password
from services.email_service import send_admin_created_volunteer_email, send_onboarding_email

@router.post("/volunteer", response_model=VolunteerResponse, status_code=201)
def admin_create_volunteer(
    payload: AdminVolunteerCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """
    **[ADMIN / NGO]** Create a new volunteer with email and skills.
    Generates a secure password and emails the volunteer.
    Admin-created volunteers are auto-approved (no approval required).
    NGO coordinators can only create volunteers for their own NGO.
    """
    # 1. Check if email exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Resolve ngo_id: admin uses payload, NGO coordinator auto-sets their own NGO
    ngo_id_val = getattr(payload, 'ngo_id', None)
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo:
            raise HTTPException(status_code=403, detail="No NGO associated with your account")
        ngo_id_val = ngo.id
    elif current_user.role == UserRole.ADMIN and not ngo_id_val:
        raise HTTPException(status_code=400, detail="NGO ID is required when Admin creates a volunteer")

    # 3. Generate random password
    temp_password = secrets.token_urlsafe(12)

    # 4. Create User — auto-approved since admin/ngo is creating
    new_user = User(
        email=payload.email,
        password_hash=hash_password(temp_password),
        role=UserRole.VOLUNTEER,
        is_active=True,
        account_status=AccountStatus.APPROVED,
    )
    db.add(new_user)
    db.flush()

    # 5. Create Volunteer profile linked by email
    # Auto-approved since admin/ngo is creating (not requiring coordinator approval)
    volunteer = Volunteer(
        name=payload.email.split('@')[0],  # Generic name initially
        email=payload.email,
        mobile_number=payload.mobile_number,
        skills=payload.skills,
        availability=True,
        ngo_id=ngo_id_val,
        approval_status=VolunteerApprovalStatus.APPROVED,
        approved_by_user_id=current_user.id,
        approved_at=datetime.utcnow(),
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)

    logger.info("%s created volunteer %s (auto-approved, ngo_id=%s)", current_user.email, volunteer.email, ngo_id_val)

    # 6. Send Welcome Email (with temp password)
    background_tasks.add_task(send_admin_created_volunteer_email, volunteer.email, temp_password)
    background_tasks.add_task(send_onboarding_email, volunteer.name, volunteer.email)

    return _enrich_volunteer_response(volunteer, db)


@router.put("/volunteer/{volunteer_id}", response_model=VolunteerResponse)
def update_volunteer(
    volunteer_id: int,
    payload: VolunteerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    **[ADMIN ONLY]** Update a volunteer's details.

    Only provided fields are updated; omitted fields remain unchanged.

    **Sample request:**
    ```json
    {
        "email": "new_email@example.com",
        "mobile_number": "+919876543210",
        "skills": ["medical", "logistics"],
        "availability": false
    }
    ```
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer with id {volunteer_id} not found")

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(volunteer, field, value)

    db.commit()
    db.refresh(volunteer)

    logger.info("Admin %s updated volunteer id=%d", current_user.email, volunteer_id)
    return _enrich_volunteer_response(volunteer, db)


@router.delete("/volunteer/{volunteer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    **[ADMIN ONLY]** Delete a volunteer.
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer with id {volunteer_id} not found")

    # Also delete their login account (User table) so the email is freed up
    if volunteer.email:
        user_record = db.query(User).filter(User.email == volunteer.email).first()
        if user_record:
            db.delete(user_record)

    db.delete(volunteer)
    db.commit()

    logger.info("Admin %s deleted volunteer id=%d", current_user.email, volunteer_id)
    return None


# ── NGO Coordinator Approval Endpoints ──────────────────────────────────

@router.get("/ngo/volunteers/pending-approval", response_model=List[VolunteerResponse])
def list_pending_approval_volunteers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """
    **[ADMIN / NGO COORDINATOR]** List volunteers pending approval by coordinator.
    - Admin: all pending volunteers system-wide.
    - NGO Coordinator: only volunteers in their NGO pending approval.
    """
    query = db.query(Volunteer).filter(Volunteer.approval_status == VolunteerApprovalStatus.PENDING)
    
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo:
            raise HTTPException(status_code=403, detail="No NGO associated with your account")
        query = query.filter(Volunteer.ngo_id == ngo.id)
    
    volunteers = query.order_by(Volunteer.created_at.desc()).offset(skip).limit(limit).all()
    return [_enrich_volunteer_response(v, db) for v in volunteers]


@router.post("/ngo/volunteer/{volunteer_id}/approve", status_code=status.HTTP_200_OK)
def ngo_approve_volunteer(
    volunteer_id: int,
    payload: VolunteerApprovalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """
    **[ADMIN / NGO COORDINATOR]** Approve a pending volunteer.
    
    - Admin: can approve any volunteer.
    - NGO Coordinator: can only approve volunteers in their own NGO.
    
    **Privileges:**
    - Volunteer becomes active immediately after approval
    - Volunteer can receive task assignments
    - Notifications sent to volunteer
    
    **Request body:**
    ```json
    {
        "notes": "Verified background and skills. Ready to deploy."
    }
    ```
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer {volunteer_id} not found")
    
    # NGO coordinator scope check
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo or volunteer.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Volunteer does not belong to your NGO")
    
    # Check status
    if volunteer.approval_status != VolunteerApprovalStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Volunteer is already {volunteer.approval_status}. Cannot approve."
        )
    
    # Update approval status on volunteer
    volunteer.approval_status = VolunteerApprovalStatus.APPROVED
    volunteer.approved_by_user_id = current_user.id
    volunteer.approval_notes = payload.notes or ""
    volunteer.approved_at = datetime.utcnow()
    
    # Also update User account_status to APPROVED
    user = db.query(User).filter(User.email == volunteer.email).first()
    if user:
        user.account_status = AccountStatus.APPROVED
    
    db.commit()
    
    logger.info(
        "%s (role=%s) approved volunteer id=%d. Notes: %s",
        current_user.email, current_user.role.value, volunteer_id, payload.notes
    )
    
    # Send approval email
    if volunteer.email:
        from services.email_service import send_onboarding_email
        background_tasks.add_task(send_onboarding_email, volunteer.name, volunteer.email)
    
    return {
        "message": f"Volunteer {volunteer.name} approved successfully",
        "volunteer_id": volunteer_id,
        "approval_status": VolunteerApprovalStatus.APPROVED.value,
        "approved_at": volunteer.approved_at,
    }


@router.post("/ngo/volunteer/{volunteer_id}/reject", status_code=status.HTTP_200_OK)
def ngo_reject_volunteer(
    volunteer_id: int,
    payload: VolunteerRejectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """
    **[ADMIN / NGO COORDINATOR]** Reject a pending volunteer.
    
    - Admin: can reject any volunteer.
    - NGO Coordinator: can only reject volunteers in their own NGO.
    
    **Privileges:**
    - Volunteer cannot receive task assignments
    - Rejection reason visible to volunteer
    - Volunteer can reapply after changes
    
    **Request body:**
    ```json
    {
        "notes": "Insufficient experience in required skills. Reapply after 3 months."
    }
    ```
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer {volunteer_id} not found")
    
    # NGO coordinator scope check
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo or volunteer.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Volunteer does not belong to your NGO")
    
    # Check status
    if volunteer.approval_status != VolunteerApprovalStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Volunteer is already {volunteer.approval_status}. Cannot reject."
        )
    
    # Update rejection status on volunteer
    volunteer.approval_status = VolunteerApprovalStatus.REJECTED
    volunteer.approved_by_user_id = current_user.id
    volunteer.approval_notes = payload.notes  # Rejection reason
    volunteer.approved_at = datetime.utcnow()
    
    # Also update User account_status to REJECTED
    user = db.query(User).filter(User.email == volunteer.email).first()
    if user:
        user.account_status = AccountStatus.REJECTED
    
    db.commit()
    
    logger.info(
        "%s (role=%s) rejected volunteer id=%d. Reason: %s",
        current_user.email, current_user.role.value, volunteer_id, payload.notes
    )
    
    # Send rejection email with reason
    if volunteer.email:
        from services.email_service import send_volunteer_rejection_email
        background_tasks.add_task(
            send_volunteer_rejection_email, volunteer.name, volunteer.email, payload.notes
        )
    
    return {
        "message": f"Volunteer {volunteer.name} rejected",
        "volunteer_id": volunteer_id,
        "approval_status": VolunteerApprovalStatus.REJECTED.value,
        "rejection_reason": payload.notes,
        "approved_at": volunteer.approved_at,
    }


@router.get("/ngo/volunteer/{volunteer_id}/approval-status", status_code=status.HTTP_200_OK)
def get_volunteer_approval_status(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_ngo),
):
    """
    **[ADMIN / NGO COORDINATOR]** Get volunteer approval status and history.
    
    Returns:
    - Approval status (pending/approved/rejected)
    - Approval notes/reason
    - Approved/rejected by whom and when
    - Privileges based on status
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer {volunteer_id} not found")
    
    # NGO coordinator scope check
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo or volunteer.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Volunteer does not belong to your NGO")
    
    approved_by = None
    if volunteer.approved_by_user_id:
        approver = db.query(User).filter(User.id == volunteer.approved_by_user_id).first()
        approved_by = approver.email if approver else None
    
    # Determine privileges based on status
    privileges = []
    if volunteer.approval_status == VolunteerApprovalStatus.APPROVED:
        privileges = [
            "receive_task_assignments",
            "view_needs",
            "submit_task_completion",
            "earn_badges",
        ]
    
    return {
        "volunteer_id": volunteer_id,
        "volunteer_name": volunteer.name,
        "approval_status": volunteer.approval_status.value,
        "approval_notes": volunteer.approval_notes,
        "approved_by": approved_by,
        "approved_at": volunteer.approved_at,
        "privileges": privileges,
        "ngo_id": volunteer.ngo_id,
    }
