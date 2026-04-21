"""
Migration Script: Add ACCEPTED and IN_PROGRESS to NeedStatus enum.
This script is idempotent - safe to run multiple times.
It extends the needstatus enum if these values don't already exist.
"""

import logging
from sqlalchemy import text, inspect
from database import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
)
logger = logging.getLogger(__name__)


def fix_enum():
    """Add ACCEPTED and IN_PROGRESS to needstatus enum if they don't exist."""
    try:
        with engine.connect() as conn:
            logger.info("🔄 Checking NeedStatus enum values...")
            
            # Query current enum values
            result = conn.execute(text("""
                SELECT enum_range(NULL::needstatus) as values;
            """))
            
            current_values = result.scalar()
            logger.info(f"   Current enum values: {current_values}")
            
            # Add missing values
            if 'accepted' not in str(current_values).lower():
                logger.info("🔄 Adding 'accepted' to needstatus enum...")
                conn.execute(text("""
                    ALTER TYPE needstatus ADD VALUE 'accepted';
                """))
            
            if 'in_progress' not in str(current_values).lower():
                logger.info("🔄 Adding 'in_progress' to needstatus enum...")
                conn.execute(text("""
                    ALTER TYPE needstatus ADD VALUE 'in_progress';
                """))
            
            conn.commit()
            logger.info("✅ NeedStatus enum extended successfully!")
            logger.info("   - New statuses: pending, assigned, accepted, in_progress, completed")
            return True
            
    except Exception as e:
        # Silently handle if enum already has the values
        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
            logger.info("✅ NeedStatus enum already has all required values")
            return True
        logger.error(f"❌ Enum migration failed: {e}")
        return False


if __name__ == "__main__":
    success = fix_enum()
    if not success:
        exit(1)
