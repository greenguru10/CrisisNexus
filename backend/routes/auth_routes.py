"""
Auth routes – Register, login, and user profile endpoints.
Updated: NGO registration creates NGO entity; volunteer signup links to NGO by name.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole, AccountStatus
from models.volunteer import Volunteer
from models.ngo import NGO, NgoStatus, NgoType
from schemas import auth_schema
from schemas.auth_schema import UserRegister, UserLogin, TokenResponse, UserResponse
from services.auth_service import (
    hash_password, create_access_token, authenticate_user, get_user_by_email,
)
from dependencies.auth_dependency import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    payload: UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    - **volunteer**: Creates volunteer profile; must supply `ngo_name` (NGO to join).
      Account starts as `pending` — NGO coordinator must approve.
    - **ngo**: Creates NGO entity (status: pending) + coordinator account.
      Must supply `ngo_type`. Admin approval required before login.
    - **admin**: Immediately approved (internal use).
    """
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # ── VOLUNTEER REGISTRATION ──────────────────────────────────────────
    if payload.role == UserRole.VOLUNTEER:
        if not payload.ngo_name:
            raise HTTPException(
                status_code=400,
                detail="Volunteers must specify the NGO they want to join (ngo_name)",
            )
        # Resolve NGO — must be approved
        ngo = db.query(NGO).filter(NGO.name.ilike(payload.ngo_name.strip())).first()
        if not ngo:
            raise HTTPException(
                status_code=404,
                detail=f"NGO '{payload.ngo_name}' not found. Check the name or contact your NGO coordinator.",
            )
        if ngo.status != NgoStatus.APPROVED:
            raise HTTPException(
                status_code=400,
                detail=f"NGO '{ngo.name}' is not yet active (status: {ngo.status.value})",
            )

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=UserRole.VOLUNTEER,
            is_active=True,
            account_status=AccountStatus.PENDING,
        )
        db.add(user)
        db.flush()

        volunteer = Volunteer(
            name=payload.volunteer_name or payload.email.split("@")[0],
            email=payload.email,
            skills=payload.skills or [],
            availability=True,
            ngo_id=ngo.id,
        )
        db.add(volunteer)
        db.commit()
        db.refresh(user)
        logger.info("Volunteer registered: %s → NGO '%s' (pending coordinator approval)", payload.email, ngo.name)
        return user

    # ── NGO COORDINATOR REGISTRATION ───────────────────────────────────
    elif payload.role == UserRole.NGO:
        if not payload.ngo_type:
            raise HTTPException(status_code=400, detail="NGO coordinators must specify ngo_type")
        ngo_name = (payload.ngo_name or "").strip()
        if not ngo_name:
            raise HTTPException(status_code=400, detail="NGO coordinators must specify ngo_name")

        # Check NGO name uniqueness
        existing_ngo = db.query(NGO).filter(NGO.name.ilike(ngo_name)).first()
        if existing_ngo:
            raise HTTPException(status_code=400, detail=f"An NGO named '{ngo_name}' already exists")

        try:
            ngo_type_enum = NgoType(payload.ngo_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid ngo_type: '{payload.ngo_type}'")

        # Create coordinator user — pending until Admin approves NGO
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=UserRole.NGO,
            is_active=True,
            account_status=AccountStatus.PENDING,
        )
        db.add(user)
        db.flush()

        # Create NGO entity in pending state
        ngo = NGO(
            name=ngo_name,
            ngo_type=ngo_type_enum,
            coordinator_user_id=user.id,
            status=NgoStatus.PENDING,
            contact_email=payload.email,
        )
        db.add(ngo)
        db.commit()
        db.refresh(user)
        logger.info("NGO coordinator registered: %s → NGO '%s' (pending Admin approval)", payload.email, ngo_name)
        return user

    # ── ADMIN REGISTRATION ──────────────────────────────────────────────
    else:
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=UserRole(payload.role.value),
            is_active=True,
            account_status=AccountStatus.APPROVED,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        from services.email_service import send_welcome_email
        background_tasks.add_task(send_welcome_email, user.email, user.role.value)
        return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    - Volunteers: blocked if account_status != approved.
    - NGO coordinators: blocked if NGO is not approved yet.
    """
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Gate: block unapproved volunteers or NGO coordinators
    if user.role == UserRole.VOLUNTEER and user.account_status != AccountStatus.APPROVED:
        msgs = {
            AccountStatus.PENDING: "Account pending NGO coordinator approval",
            AccountStatus.REJECTED: "Account has been rejected by the NGO coordinator",
        }
        raise HTTPException(status_code=403, detail=msgs.get(user.account_status, "Account not approved"))

    if user.role == UserRole.NGO and user.account_status != AccountStatus.APPROVED:
        raise HTTPException(
            status_code=403,
            detail="Your NGO registration is pending Admin approval. You will be notified once approved.",
        )

    # Resolve NGO context for the token response
    ngo_id = None
    ngo_name = None
    ngo_status_val = None
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == user.id).first()
    if ngo:
        ngo_id = ngo.id
        ngo_name = ngo.name
        ngo_status_val = ngo.status.value

    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    logger.info("User logged in: %s (role=%s)", user.email, user.role.value)

    return TokenResponse(
        access_token=access_token,
        role=user.role.value,
        account_status=user.account_status.value,
        ngo_id=ngo_id,
        ngo_name=ngo_name,
        ngo_status=ngo_status_val,
    )


@router.get("/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    user_resp = UserResponse.model_validate(current_user)
    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if volunteer:
        user_resp.location = volunteer.location
        user_resp.skills = volunteer.skills
        if not user_resp.mobile_number and volunteer.mobile_number:
            user_resp.mobile_number = volunteer.mobile_number

    # Attach NGO info
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if ngo:
        user_resp.ngo_id = ngo.id
        user_resp.ngo_name = ngo.name
    elif volunteer and volunteer.ngo_id:
        ngo = db.query(NGO).filter(NGO.id == volunteer.ngo_id).first()
        if ngo:
            user_resp.ngo_id = ngo.id
            user_resp.ngo_name = ngo.name

    return user_resp


@router.put("/me", response_model=UserResponse)
def update_me(
    payload: auth_schema.UserUpdateProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update profile."""
    if payload.email:
        existing = get_user_by_email(db, payload.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already taken")

    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()

    if payload.email:
        current_user.email = payload.email
        if volunteer:
            volunteer.email = payload.email
    if payload.password:
        current_user.password_hash = hash_password(payload.password)
    if payload.mobile_number is not None:
        current_user.mobile_number = payload.mobile_number
        if volunteer:
            volunteer.mobile_number = payload.mobile_number
    if payload.location is not None and volunteer:
        volunteer.location = payload.location
    if payload.skills is not None and volunteer:
        volunteer.skills = payload.skills

    db.commit()
    db.refresh(current_user)
    return get_me(db=db, current_user=current_user)


@router.post("/forgot-password")
async def forgot_password(
    payload: auth_schema.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Request a password reset link."""
    user = get_user_by_email(db, payload.email)
    if not user:
        return {"message": "If an account exists, a reset link has been sent."}

    from services.auth_service import generate_reset_token
    token = generate_reset_token(db, user)

    from services.email_service import send_password_reset_email
    background_tasks.add_task(send_password_reset_email, user.email, token)
    return {"message": "If an account exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: auth_schema.ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token."""
    from services.auth_service import verify_reset_token
    user = verify_reset_token(db, payload.token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")

    user.password_hash = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
    return {"message": "Password successfully reset."}
