"""
Complete Database Setup Script.
This script initializes the database and creates all necessary tables.
Run once after setting up the environment.
"""

import logging
from database import engine, Base
from models.need import Need
from models.volunteer import Volunteer
from models.user import User

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
)
logger = logging.getLogger(__name__)


def setup_database():
    """Initialize database tables from all ORM models."""
    try:
        logger.info("🔄 Creating database tables...")
        # Import all models to ensure they are registered with Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        logger.info("✅ Tables created:")
        logger.info("   - users (User authentication & RBAC)")
        logger.info("   - volunteers (Volunteer profiles & skills)")
        logger.info("   - needs (Crisis needs & assignments)")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        return False


if __name__ == "__main__":
    success = setup_database()
    if not success:
        exit(1)
