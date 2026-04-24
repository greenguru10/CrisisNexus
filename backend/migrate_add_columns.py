"""
Migration: add new columns to support CrisisNexus feature upgrades.

Tables altered:
  1. need_ngo_assignments  → add is_completed, completed_at, completed_by_volunteer_id
  2. needs                 → add FK constraint to assigned_volunteer_id  (volunteers.id)
  3. volunteer_pool_requests → add need_id FK column

Run from the backend/ directory:
    python migrate_add_columns.py

Safe to re-run (uses IF NOT EXISTS / exception handling).
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import engine
from sqlalchemy import text

MIGRATIONS = [
    # ── need_ngo_assignments ──────────────────────────────────────────────────
    """
    ALTER TABLE need_ngo_assignments
        ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS completed_by_volunteer_id INTEGER
            REFERENCES volunteers(id) ON DELETE SET NULL;
    """,
    "CREATE INDEX IF NOT EXISTS ix_need_ngo_assignments_is_completed ON need_ngo_assignments(is_completed);",

    # ── needs: make assigned_volunteer_id a proper FK ─────────────────────────
    # Only add the FK if it doesn't already exist (idempotent).
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'fk_needs_assigned_volunteer'
        ) THEN
            ALTER TABLE needs
                ADD CONSTRAINT fk_needs_assigned_volunteer
                FOREIGN KEY (assigned_volunteer_id)
                REFERENCES volunteers(id)
                ON DELETE SET NULL;
        END IF;
    END $$;
    """,
    "CREATE INDEX IF NOT EXISTS ix_needs_assigned_volunteer_id ON needs(assigned_volunteer_id);",

    # ── volunteer_pool_requests: add need_id ──────────────────────────────────
    """
    ALTER TABLE volunteer_pool_requests
        ADD COLUMN IF NOT EXISTS need_id INTEGER
            REFERENCES needs(id) ON DELETE SET NULL;
    """,
    "CREATE INDEX IF NOT EXISTS ix_volunteer_pool_requests_need_id ON volunteer_pool_requests(need_id);",
]


def run():
    with engine.connect() as conn:
        for i, sql in enumerate(MIGRATIONS, 1):
            try:
                conn.execute(text(sql.strip()))
                conn.commit()
                print(f"[{i}/{len(MIGRATIONS)}] OK")
            except Exception as e:
                conn.rollback()
                print(f"[{i}/{len(MIGRATIONS)}] WARN — {e}")
    print("\n✅ Migration complete.")


if __name__ == "__main__":
    run()
