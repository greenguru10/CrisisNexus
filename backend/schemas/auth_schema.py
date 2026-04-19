"""
Pydantic schemas for Authentication – register, login, token, user response.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    VOLUNTEER = "volunteer"
    NGO = "ngo"


# ── Request Schemas ──────────────────────────────────────────────

class UserRegister(BaseModel):
    """Schema for user registration."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 chars)")
    role: UserRole = Field(UserRole.VOLUNTEER, description="User role: admin, volunteer, ngo")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "priya@example.com",
                "password": "securepass123",
                "role": "volunteer",
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "priya@example.com",
                "password": "securepass123",
            }
        }


# ── Response Schemas ─────────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    role: str
    message: str = "Login successful"


class UserResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    role: UserRole
    mobile_number: Optional[str] = None
    location: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdateProfile(BaseModel):
    """Update profile request payload."""
    email: Optional[str] = None
    password: Optional[str] = None
    mobile_number: Optional[str] = None
    location: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    """Forgot password request payload."""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Reset password request payload."""
    token: str
    new_password: str = Field(..., min_length=6)

class ManualMatchRequest(BaseModel):
    """Admin manual volunteer matching payload."""
    volunteer_id: int
