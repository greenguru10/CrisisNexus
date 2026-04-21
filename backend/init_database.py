"""
Master Database Initialization Script.
This script runs all database setup steps in the correct order:
1. Create all tables from ORM models
2. Add account_status column to users table (if needed)
3. Fix NeedStatus enum to include ACCEPTED and IN_PROGRESS

Run this script ONCE after setting up the environment.
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_setup():
    """Run all database setup steps."""
    logger.info("=" * 70)
    logger.info("🚀 DATABASE INITIALIZATION")
    logger.info("=" * 70)
    
    steps = []
    
    # Step 1: Create tables
    logger.info("\n📋 STEP 1: Creating database tables...")
    try:
        from database import engine, Base
        from models.need import Need
        from models.volunteer import Volunteer
        from models.user import User
        
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        logger.info("   Tables: users, volunteers, needs")
        steps.append(True)
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        steps.append(False)
    
    # Step 2: Migrate account_status column
    logger.info("\n📋 STEP 2: Adding account_status column to users...")
    try:
        from migrate_account_status import migrate_account_status
        if migrate_account_status():
            steps.append(True)
        else:
            steps.append(False)
    except Exception as e:
        logger.error(f"❌ Failed to migrate account_status: {e}")
        steps.append(False)
    
    # Step 3: Fix enum values
    logger.info("\n📋 STEP 3: Fixing NeedStatus enum values...")
    try:
        from fix_enum import fix_enum
        if fix_enum():
            steps.append(True)
        else:
            steps.append(False)
    except Exception as e:
        logger.error(f"❌ Failed to fix enum: {e}")
        steps.append(False)
    
    # Summary
    logger.info("\n" + "=" * 70)
    if all(steps):
        logger.info("✅ ALL DATABASE SETUP STEPS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info("\n🎉 Your database is ready to use!")
        logger.info("\n📌 Next steps:")
        logger.info("   1. Create an admin user: python add_admin.py")
        logger.info("   2. (Optional) Add sample data: python test_scripts/generate_dummy_data.py")
        logger.info("   3. Start the server: uvicorn main:app --reload")
        return True
    else:
        logger.info("❌ SOME SETUP STEPS FAILED!")
        logger.info("=" * 70)
        return False


if __name__ == "__main__":
    success = run_setup()
    sys.exit(0 if success else 1)
