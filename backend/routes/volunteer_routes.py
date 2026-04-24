"""
Volunteer routes – Add, list, update, and delete volunteers.
Updated: NGO coordinators can approve/reject their own NGO's volunteers,
add volunteers directly to their NGO, and view only their NGO's pool.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole, AccountStatus
from models.volunteer import Volunteer
from models.ngo import NGO, NgoStatus
from schemas.volunteer_schema import (
    VolunteerCreate, VolunteerUpdate, VolunteerResponse, AdminVolunteerCreate,
)
from dependencies.auth_dependency import get_current_user, get_current_admin, get_current_admin_or_ngo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Volunteers"])


# ── Helper: enrich volunteer with account_status from User table ──

def _enrich_volunteer_response(volunteer: Volunteer, db: Session) -> dict:
    """
    Build a VolunteerResponse-compatible dict by merging the volunteer
    record with its linked User's account_status.
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
    List approved volunteers.
    - Admin: all approved volunteers; can filter by ngo_id.
    - NGO Coordinator: only their own NGO's volunteers.
    """
    query = (
        db.query(Volunteer)
        .join(User, func.lower(User.email) == func.lower(Volunteer.email))
        .filter(User.role == UserRole.VOLUNTEER)
        .filter(User.account_status == AccountStatus.APPROVED)
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
    """
    query = (
        db.query(Volunteer)
        .join(User, func.lower(User.email) == func.lower(Volunteer.email))
        .filter(User.role == UserRole.VOLUNTEER)
        .filter(User.account_status == AccountStatus.PENDING)
    )
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        scope_id = ngo.id if ngo else -1
        query = query.filter(Volunteer.ngo_id == scope_id)
    elif current_user.role == UserRole.ADMIN:
        # Admin only sees volunteers who are NOT assigned to any NGO
        query = query.filter(Volunteer.ngo_id == None)

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
    ngo_id_val = payload.ngo_id
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo:
            raise HTTPException(status_code=403, detail="No NGO associated with your account")
        ngo_id_val = ngo.id

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
    volunteer_name = payload.name if payload.name else payload.email.split('@')[0]
    volunteer = Volunteer(
        name=volunteer_name,
        email=payload.email,
        mobile_number=payload.mobile_number,
        skills=payload.skills,
        availability=True,
        ngo_id=ngo_id_val,
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
