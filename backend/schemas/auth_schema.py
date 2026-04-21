"""
Pydantic schemas for Authentication – register, login, token, user response.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
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
    skills: Optional[List[str]] = Field(default_factory=list, description="List of skills for volunteers")
    # ── Volunteer-specific ───────────────────────────────────────
    volunteer_name: Optional[str] = Field(None, description="Full name (required for volunteers)")
    ngo_name: Optional[str] = Field(None, description="NGO name the volunteer wants to join")
    # ── NGO Coordinator-specific ─────────────────────────────────
    ngo_type: Optional[str] = Field(None, description="Type of NGO (required for ngo role)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "priya@example.com",
                "password": "securepass123",
                "role": "volunteer",
                "volunteer_name": "Priya Sharma",
                "ngo_name": "HelpIndia NGO",
                "skills": ["medical", "first_aid"]
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
    """JWT token response – now includes ngo_id and ngo_name for scoped views."""
    access_token: str
    token_type: str = "bearer"
    role: str
    account_status: Optional[str] = None
    ngo_id: Optional[int] = None
    ngo_name: Optional[str] = None
    ngo_status: Optional[str] = None
    message: str = "Login successful"


class UserResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    role: UserRole
    mobile_number: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    is_active: bool
    account_status: Optional[str] = None
    ngo_id: Optional[int] = None
    ngo_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdateProfile(BaseModel):
    """Update profile request payload."""
    email: Optional[str] = None
    password: Optional[str] = None
    mobile_number: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None


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
