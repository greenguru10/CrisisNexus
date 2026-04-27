"""
Script to create an admin user in the database.
Run after database initialization: python add_admin.py
"""

import logging
import sys
from getpass import getpass
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import SessionLocal
from models.user import User, UserRole, AccountStatus
from passlib.context import CryptContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_admin():
    """Create an admin user interactively."""
    logger.info("=" * 70)
    logger.info("👤 CREATE ADMIN USER")
    logger.info("=" * 70)
    
    db = SessionLocal()
    try:
        # Get input
        email = input("\n📧 Enter admin email: ").strip().lower()
        mobile = input("📱 Enter mobile number (optional): ").strip() or None
        
        # Validate email format
        if "@" not in email:
            logger.error("❌ Invalid email format!")
            return False
        
        # Check if user already exists
        stmt = select(User).where(User.email == email)
        existing = db.execute(stmt).scalar()
        if existing:
            logger.error(f"❌ User with email {email} already exists!")
            return False
        
        # Get password
        password = getpass("🔐 Enter password: ")
        password_confirm = getpass("🔐 Confirm password: ")
        
        if password != password_confirm:
            logger.error("❌ Passwords do not match!")
            return False
        
        if len(password) < 8:
            logger.error("❌ Password must be at least 8 characters!")
            return False
        
        # Create admin user
        admin = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            mobile_number=mobile,
            account_status=AccountStatus.APPROVED,
            is_active=True,
        )
        
        db.add(admin)
        db.commit()
        
        logger.info("✅ Admin user created successfully!")
        logger.info(f"   Email: {email}")
        logger.info(f"   Role: ADMIN")
        logger.info(f"   Status: APPROVED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def list_users():
    """List all users in the database."""
    logger.info("\n📋 EXISTING USERS:")
    logger.info("-" * 70)
    
    db = SessionLocal()
    try:
        stmt = select(User).order_by(User.created_at.desc())
        users = db.execute(stmt).scalars().all()
        
        if not users:
            logger.info("   No users found.")
            return
        
        for user in users:
            status_icon = "✅" if user.is_active else "❌"
            logger.info(
                f"   {status_icon} {user.email} | Role: {user.role} | Status: {user.account_status}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    success = create_admin()
    if success:
        list_users()
    sys.exit(0 if success else 1)
