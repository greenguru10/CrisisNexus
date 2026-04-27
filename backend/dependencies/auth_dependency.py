"""
Auth Dependencies – FastAPI dependency injection for RBAC.
Extended to support NGO Coordinator scoping.
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole
from models.ngo import NGO, NgoStatus
from services.auth_service import decode_access_token

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode JWT token and return the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_email: str = payload.get("sub")
    if user_email is None:
        raise credentials_exception
    user = db.query(User).filter(User.email == user_email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_current_ngo_coordinator(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Ensure current user is an approved NGO coordinator.
    Attaches `current_user.ngo` to the returned user object for convenience.
    """
    if current_user.role != UserRole.NGO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NGO Coordinator access required",
        )
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No approved NGO found for this coordinator",
        )
    if ngo.status != NgoStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"NGO is not yet approved (status: {ngo.status.value})",
        )
    # Attach NGO to user object for downstream use
    current_user._ngo = ngo
    return current_user


def get_current_admin_or_ngo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Allow both Admin and approved NGO Coordinator."""
    if current_user.role == UserRole.ADMIN:
        return current_user
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if ngo and ngo.status == NgoStatus.APPROVED:
            current_user._ngo = ngo
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NGO is not yet approved",
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="NGO Coordinator or Admin access required",
    )


def get_ngo_id_for_user(current_user: User, db: Session) -> int | None:
    """
    Helper: resolve the NGO id for the current user.
    Returns None if admin (global scope), NGO id if coordinator.
    """
    if current_user.role == UserRole.ADMIN:
        return None
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    return ngo.id if ngo else None


def get_current_ngo_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Legacy alias kept for backward compatibility."""
    if current_user.role not in (UserRole.ADMIN, UserRole.NGO):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NGO or Admin access required",
        )
    return current_user
