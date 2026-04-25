"""
migrate_task_states.py
─────────────────────
Safe migration script to add the 3-layer task state machine columns.

Changes applied:
  1. need_volunteer_assignments:
     - status         VARCHAR (ASSIGNED / ACCEPTED / IN_PROGRESS / COMPLETED)
     - accepted_at    TIMESTAMPTZ
     - started_at     TIMESTAMPTZ
     - completed_at   TIMESTAMPTZ

  2. need_ngo_assignments:
     - Adds new enum values: in_progress, completed  (to ngoas_signstatus)
     - started_at     TIMESTAMPTZ
     - completed_at   TIMESTAMPTZ  (replaces the old boolean is_completed for logic)
     - is_completed   stays as a column for backward compat

All statements use IF NOT EXISTS / DO NOTHING so the script is idempotent.

Usage:
    cd backend
    python scripts/migrate_task_states.py
"""

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


MIGRATION_STEPS = [
    # ── 1. Create the VolunteerTaskStatus enum type (idempotent) ─────────────
    """
    DO $$ BEGIN
        CREATE TYPE volunteertaskstatus AS ENUM (
            'assigned', 'accepted', 'in_progress', 'completed'
        );
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """,

    # ── 2. Add 'status' column to need_volunteer_assignments ─────────────────
    """
    ALTER TABLE need_volunteer_assignments
        ADD COLUMN IF NOT EXISTS status volunteertaskstatus
            NOT NULL DEFAULT 'assigned';
    """,

    # ── 3. Backfill status for rows where is_active = false (completed tasks) ─
    """
    UPDATE need_volunteer_assignments
        SET status = 'completed'
    WHERE is_active = false AND status = 'assigned';
    """,

    # ── 4. Add timestamp columns to need_volunteer_assignments ───────────────
    """
    ALTER TABLE need_volunteer_assignments
        ADD COLUMN IF NOT EXISTS accepted_at  TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS started_at   TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
    """,

    # ── 5. Add new enum values to NgoAssignStatus ────────────────────────────
    #    PostgreSQL requires separate ALTER TYPE statements per value.
    """
    DO $$ BEGIN
        ALTER TYPE ngoassignstatus ADD VALUE IF NOT EXISTS 'in_progress';
    EXCEPTION WHEN others THEN NULL;
    END $$;
    """,
    """
    DO $$ BEGIN
        ALTER TYPE ngoassignstatus ADD VALUE IF NOT EXISTS 'completed';
    EXCEPTION WHEN others THEN NULL;
    END $$;
    """,

    # ── 6. Add timestamp columns to need_ngo_assignments ────────────────────
    """
    ALTER TABLE need_ngo_assignments
        ADD COLUMN IF NOT EXISTS started_at   TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
    """,

    # ── 7. Backfill ngo_assignments: is_completed=True → status='completed' ──
    """
    UPDATE need_ngo_assignments
        SET status = 'completed'
    WHERE is_completed = true AND status != 'completed';
    """,
]


def run_migration():
    logger.info("Starting CommunitySync task-state migration...")
    with engine.connect() as conn:
        for i, sql in enumerate(MIGRATION_STEPS, start=1):
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info("Step %d/%d ✅", i, len(MIGRATION_STEPS))
            except Exception as exc:
                logger.error("Step %d FAILED: %s", i, exc)
                logger.error("SQL was: %s", sql.strip())
                raise

    logger.info("Migration complete! All task-state columns are in place.")
    print("\n" + "="*55)
    print("MIGRATION COMPLETE")
    print("="*55)
    print("New columns added:")
    print("  need_volunteer_assignments.status        (ASSIGNED→COMPLETED)")
    print("  need_volunteer_assignments.accepted_at")
    print("  need_volunteer_assignments.started_at")
    print("  need_volunteer_assignments.completed_at")
    print("  need_ngo_assignments.started_at")
    print("  need_ngo_assignments.completed_at")
    print("  NgoAssignStatus enum: +in_progress, +completed")
    print("="*55)
    print("Next: restart uvicorn (uvicorn main:app --reload)")


if __name__ == "__main__":
    run_migration()
