"""
Auth routes – Register, login, and user profile endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole
from schemas import auth_schema
from schemas.auth_schema import UserRegister, UserLogin, TokenResponse, UserResponse
from services.auth_service import (
    hash_password,
    create_access_token,
    authenticate_user,
    get_user_by_email,
)
from services.email_service import send_welcome_email
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

    **Sample request:**
    ```json
    {
        "email": "priya@example.com",
        "password": "securepass123",
        "role": "volunteer"
    }
    ```
    """
    # Check if email already exists
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole(payload.role.value),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("Registered user id=%d email=%s role=%s", user.id, user.email, user.role.value)

    # Send welcome email in background
    background_tasks.add_task(send_welcome_email, user.email, user.role.value)

    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    **Sample request:**
    ```json
    {
        "email": "priya@example.com",
        "password": "securepass123"
    }
    ```

    **Sample response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "role": "volunteer",
        "message": "Login successful"
    }
    ```
    """
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )

    logger.info("User logged in: %s (role=%s)", user.email, user.role.value)

    return TokenResponse(
        access_token=access_token,
        role=user.role.value,
    )


from models.volunteer import Volunteer

@router.get("/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    """
    user_resp = UserResponse.model_validate(current_user)
    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if volunteer:
        user_resp.location = volunteer.location
    return user_resp

@router.put("/me", response_model=UserResponse)
def update_me(
    payload: auth_schema.UserUpdateProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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

    db.commit()
    db.refresh(current_user)
    
    # Return matched layout
    return get_me(db=db, current_user=current_user)

@router.post("/forgot-password")
async def forgot_password(
    payload: auth_schema.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request a password reset link."""
    user = get_user_by_email(db, payload.email)
    if not user:
        # Prevent email enumeration by returning a generic success message
        return {"message": "If an account exists, a reset link has been sent."}

    from services.auth_service import generate_reset_token
    token = generate_reset_token(db, user)

    from services.email_service import send_password_reset_email
    background_tasks.add_task(send_password_reset_email, user.email, token)

    return {"message": "If an account exists, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(
    payload: auth_schema.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
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
