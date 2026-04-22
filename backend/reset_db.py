"""
Master Database Reset Script.
This script drops all existing tables and creates a fresh database schema from scratch using the ORM models.
It guarantees zero schema mismatch issues.

Run this script ONCE after setting up the environment.
WARNING: THIS WILL DELETE ALL EXISTING DATA!
"""

import logging
import sys
from database import engine, Base

import models.user
import models.ngo
import models.need
import models.volunteer
import models.resource
import models.task_trail
import models.pool_request
import models.gamification
import models.need_ngo_assignment
import models.need_volunteer_assignment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s"
)
logger = logging.getLogger(__name__)

def reset_database():
    logger.info("=" * 60)
    logger.info("🧨 DATABASE RESET AND INITIALIZATION")
    logger.info("=" * 60)
    
    try:
        logger.info("Dropping all existing tables to start fresh...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped successfully.")
        
        logger.info("\nCreating all tables from current ORM models...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully!")
        
        logger.info("=" * 60)
        logger.info("🎉 Database successfully recreated from scratch with ZERO issues!")
        logger.info("📌 Next Steps:")
        logger.info("   1. Create an admin user: python add_admin.py")
        logger.info("   2. Run the application: uvicorn main:app --reload")
        return True
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)
