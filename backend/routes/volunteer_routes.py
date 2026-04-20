"""
Volunteer routes – Add, list, update, and delete volunteers.
Includes admin-only endpoints for update, delete, and approval workflow.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole, AccountStatus
from models.volunteer import Volunteer
from schemas.volunteer_schema import (
    VolunteerCreate, VolunteerUpdate, VolunteerResponse, AdminVolunteerCreate,
)
from dependencies.auth_dependency import get_current_user, get_current_admin

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
    available: Optional[bool] = Query(None, description="Filter by availability"),
    skill: Optional[str] = Query(None, description="Filter by skill (partial match)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List all **approved** volunteers with optional filters.
    Only returns volunteers whose linked User account has account_status = 'approved'.
    """
    # Join Volunteer with User on email, filter by approved status
    query = (
        db.query(Volunteer)
        .join(User, User.email == Volunteer.email)
        .filter(User.role == UserRole.VOLUNTEER)
        .filter(User.account_status == AccountStatus.APPROVED)
    )

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
    current_user: User = Depends(get_current_admin),
):
    """
    **[ADMIN ONLY]** List all volunteers with account_status = 'pending'.
    Used by the admin dashboard to review and approve new signups.
    """
    pending_volunteers = (
        db.query(Volunteer)
        .join(User, User.email == Volunteer.email)
        .filter(User.role == UserRole.VOLUNTEER)
        .filter(User.account_status == AccountStatus.PENDING)
        .order_by(Volunteer.created_at.desc())
        .all()
    )
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
    current_user: User = Depends(get_current_admin),
):
    """
    **[ADMIN ONLY]** Approve a pending volunteer.
    Sets account_status to 'approved' and triggers two background emails:
    1. WhatsApp onboarding email (with join instructions)
    2. Welcome email (confirming active status)
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer with id {volunteer_id} not found")

    # Find linked user
    user = db.query(User).filter(User.email == volunteer.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No linked user account found for this volunteer")

    if user.account_status == AccountStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Volunteer is already approved")

    # Update status
    user.account_status = AccountStatus.APPROVED
    db.commit()

    logger.info("Admin %s approved volunteer id=%d (%s)", current_user.email, volunteer_id, volunteer.email)

    # Send WhatsApp onboarding email
    from services.email_service import send_onboarding_email
    background_tasks.add_task(send_onboarding_email, volunteer.name, volunteer.email)

    # Send welcome email
    from services.email_service import send_volunteer_welcome_email
    background_tasks.add_task(send_volunteer_welcome_email, volunteer.name, volunteer.email)

    return {
        "message": f"Volunteer {volunteer.name} has been approved",
        "account_status": "approved",
    }


@router.post("/volunteer/{volunteer_id}/reject")
def reject_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    **[ADMIN ONLY]** Reject a pending volunteer.
    Sets account_status to 'rejected'.
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer with id {volunteer_id} not found")

    user = db.query(User).filter(User.email == volunteer.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No linked user account found for this volunteer")

    if user.account_status == AccountStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Volunteer is already rejected")

    user.account_status = AccountStatus.REJECTED
    db.commit()

    logger.info("Admin %s rejected volunteer id=%d (%s)", current_user.email, volunteer_id, volunteer.email)

    return {
        "message": f"Volunteer {volunteer.name} has been rejected",
        "account_status": "rejected",
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
    current_user: User = Depends(get_current_admin),
):
    """
    **[ADMIN ONLY]** Create a new volunteer with email and skills.
    Generates a secure password and emails the volunteer.
    Also sends WhatsApp onboarding instructions.
    Admin-created volunteers are auto-approved (no approval required).
    """
    # 1. Check if email exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Generate random password
    temp_password = secrets.token_urlsafe(12)

    # 3. Create User — auto-approved since admin is creating
    new_user = User(
        email=payload.email,
        password_hash=hash_password(temp_password),
        role=UserRole.VOLUNTEER,
        is_active=True,
        account_status=AccountStatus.APPROVED,
    )
    db.add(new_user)
    db.flush()

    # 4. Create Volunteer profile linked by email
    volunteer = Volunteer(
        name=payload.email.split('@')[0],  # Generic name initially
        email=payload.email,
        mobile_number=payload.mobile_number,
        skills=payload.skills,
        availability=True,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)

    logger.info("Admin %s created volunteer %s (auto-approved)", current_user.email, volunteer.email)

    # 5. Send Welcome Email (with temp password)
    background_tasks.add_task(send_admin_created_volunteer_email, volunteer.email, temp_password)

    # 6. Send WhatsApp Onboarding Email (with join instructions)
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
