"""
User model – represents an authenticated user with role-based access.
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from database import Base


class UserRole(str, enum.Enum):
    """User role for RBAC."""
    ADMIN = "admin"
    VOLUNTEER = "volunteer"
    NGO = "ngo"


class AccountStatus(str, enum.Enum):
    """Account approval status for volunteer onboarding workflow."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    """ORM model for the users table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.VOLUNTEER, index=True)
    mobile_number = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    account_status = Column(
        SAEnum(AccountStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False,
        default=AccountStatus.APPROVED, index=True,
        comment="pending|approved|rejected — volunteers start as pending on self-signup",
    )
    reset_token = Column(String(255), nullable=True, index=True)
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
