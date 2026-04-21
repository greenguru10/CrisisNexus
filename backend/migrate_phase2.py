"""
Phase 2 migration: creates new tables required for Task Trail, Multi-NGO/Multi-Volunteer
assignment, and Inventory Contribution features.

Run once:
    cd CrisisNexus/backend
    python migrate_phase2.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import engine, Base
from sqlalchemy import text

# Import all models so Base.metadata is populated
import models.user           # noqa
import models.ngo            # noqa
import models.volunteer      # noqa
import models.need           # noqa
import models.resource       # noqa
import models.pool_request   # noqa
import models.gamification   # noqa
import models.task_trail              # noqa – NEW
import models.need_ngo_assignment     # noqa – NEW
import models.need_volunteer_assignment  # noqa – NEW


def run():
    print("=== CrisisNexus Phase 2 Migration ===\n")

    with engine.connect() as conn:
        # ── 1. Create enum types (idempotent) ─────────────────────────────
        enums_to_create = [
            ("trailaction",      ["created","submitted_by_ngo","approved_by_admin","assigned_to_ngo",
                                   "ngo_accepted","ngo_rejected","volunteer_assigned",
                                   "status_changed","completed","resource_requested"]),
            ("ngoassignstatus",  ["pending","accepted","rejected"]),
            ("contributionstatus", ["pending","approved","rejected"]),
        ]
        for type_name, values in enums_to_create:
            val_str = ", ".join(f"'{v}'" for v in values)
            conn.execute(text(
                f"DO $$ BEGIN "
                f"  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN "
                f"    CREATE TYPE {type_name} AS ENUM ({val_str}); "
                f"  END IF; "
                f"END $$;"
            ))
            print(f"  [OK] enum '{type_name}' ready")

        conn.commit()

        # ── 2. ADD columns to existing tables (idempotent) ─────────────────
        alter_stmts = [
            # resource_requests: add need_id + need_description columns
            ("resource_requests", "need_id",
             "ALTER TABLE resource_requests ADD COLUMN IF NOT EXISTS need_id INTEGER REFERENCES needs(id) ON DELETE SET NULL;"),
            ("resource_requests", "need_description",
             "ALTER TABLE resource_requests ADD COLUMN IF NOT EXISTS need_description VARCHAR(255);"),
        ]
        for table, col, stmt in alter_stmts:
            conn.execute(text(stmt))
            print(f"  [OK] {table}.{col} added (or already exists)")

        conn.commit()

    # ── 3. Create new tables via SQLAlchemy metadata ─────────────────────
    new_tables = ["task_trail", "need_ngo_assignments", "need_volunteer_assignments", "inventory_contributions"]
    print("\nCreating new tables...")
    Base.metadata.create_all(engine, tables=[
        Base.metadata.tables[t] for t in new_tables if t in Base.metadata.tables
    ])
    for t in new_tables:
        if t in Base.metadata.tables:
            print(f"  [OK] table '{t}' created (or already exists)")
        else:
            print(f"  [MISS] table '{t}' NOT found in metadata — check model import")

    print("\n[OK] Phase 2 migration complete!")


if __name__ == "__main__":
    run()
