"""
Auth Dependencies – FastAPI dependency injection for RBAC.

Usage in routes:
    @router.get("/protected")
    def protected(current_user: User = Depends(get_current_user)):
        ...

    @router.delete("/admin-only")
    def admin_only(current_user: User = Depends(get_current_admin)):
        ...
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole
from services.auth_service import decode_access_token

logger = logging.getLogger(__name__)

# OAuth2 scheme — tells Swagger where to send credentials
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode JWT token and return the authenticated user.
    Raises 401 if token is invalid or user not found.
    """
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
    """
    Ensure the current user has admin role.
    Raises 403 if not admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_current_ngo_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure the current user is either NGO or admin.
    Raises 403 otherwise.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.NGO):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NGO or Admin access required",
        )
    return current_user
