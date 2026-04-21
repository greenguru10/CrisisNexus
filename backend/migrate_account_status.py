"""
Migration Script: Add account_status column to users table.
This script is idempotent - safe to run multiple times.
It adds the account_status column if it doesn't already exist.
"""

import logging
from sqlalchemy import text, inspect
from database import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
)
logger = logging.getLogger(__name__)


def migrate_account_status():
    """Add account_status column to users table if it doesn't exist."""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'account_status' in columns:
                logger.info("✅ account_status column already exists in users table")
                return True
            
            logger.info("🔄 Adding account_status column to users table...")
            
            # Create the enum type if it doesn't exist
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE account_status_enum AS ENUM ('pending', 'approved', 'rejected');
                EXCEPTION WHEN duplicate_object THEN
                    null;
                END $$;
            """))
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN account_status account_status_enum DEFAULT 'approved' NOT NULL;
            """))
            
            conn.commit()
            logger.info("✅ account_status column added successfully!")
            logger.info("   - New volunteers default to 'approved' for backward compatibility")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate_account_status()
    if not success:
        exit(1)
