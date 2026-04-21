"""
Migration: Add Multi-NGO Federation tables and columns.

Run this ONCE against an existing CommunitySync database:
    cd backend
    python migrate_add_ngo.py

This script is IDEMPOTENT — safe to run multiple times.
"""

import logging
from sqlalchemy import text
from database import engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.fetchone() is not None


def table_exists(conn, table: str) -> bool:
    result = conn.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name = :t"
    ), {"t": table})
    return result.fetchone() is not None


def run_migration():
    with engine.begin() as conn:

        # ── 1. Create NGO type enum ──────────────────────────────────────
        log.info("Creating ngo_type enum (if needed)...")
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ngotype') THEN
                    CREATE TYPE ngotype AS ENUM (
                        'disaster_relief','medical','food_distribution','education',
                        'logistics','shelter','rehabilitation','water_sanitation',
                        'child_welfare','others'
                    );
                END IF;
            END$$;
        """))

        # ── 2. Create NGO status enum ───────────────────────────────────
        log.info("Creating ngostatus enum (if needed)...")
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ngostatus') THEN
                    CREATE TYPE ngostatus AS ENUM ('pending','approved','rejected','suspended');
                END IF;
            END$$;
        """))

        # ── 3. Create ngos table ─────────────────────────────────────────
        if not table_exists(conn, "ngos"):
            log.info("Creating ngos table...")
            conn.execute(text("""
                CREATE TABLE ngos (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    ngo_type ngotype NOT NULL DEFAULT 'others',
                    registration_number VARCHAR(100),
                    description TEXT,
                    location VARCHAR(255),
                    contact_email VARCHAR(255),
                    contact_phone VARCHAR(20),
                    status ngostatus NOT NULL DEFAULT 'pending',
                    coordinator_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    admin_notes TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
        else:
            log.info("ngos table already exists, skipping.")

        # ── 4. Alter volunteers table ────────────────────────────────────
        log.info("Altering volunteers table...")
        if not column_exists(conn, "volunteers", "ngo_id"):
            conn.execute(text("ALTER TABLE volunteers ADD COLUMN ngo_id INTEGER REFERENCES ngos(id) ON DELETE SET NULL;"))
            log.info("  + Added volunteers.ngo_id")
        if not column_exists(conn, "volunteers", "tasks_completed"):
            conn.execute(text("ALTER TABLE volunteers ADD COLUMN tasks_completed INTEGER NOT NULL DEFAULT 0;"))
            log.info("  + Added volunteers.tasks_completed")
        if not column_exists(conn, "volunteers", "consecutive_completions"):
            conn.execute(text("ALTER TABLE volunteers ADD COLUMN consecutive_completions INTEGER NOT NULL DEFAULT 0;"))
            log.info("  + Added volunteers.consecutive_completions")

        # ── 5. Alter needs table ─────────────────────────────────────────
        log.info("Altering needs table...")
        if not column_exists(conn, "needs", "ngo_id"):
            conn.execute(text("ALTER TABLE needs ADD COLUMN ngo_id INTEGER REFERENCES ngos(id) ON DELETE SET NULL;"))
            log.info("  + Added needs.ngo_id")
        if not column_exists(conn, "needs", "assigned_by_admin"):
            conn.execute(text("ALTER TABLE needs ADD COLUMN assigned_by_admin BOOLEAN NOT NULL DEFAULT FALSE;"))
            log.info("  + Added needs.assigned_by_admin")
        if not column_exists(conn, "needs", "ngo_accepted"):
            conn.execute(text("ALTER TABLE needs ADD COLUMN ngo_accepted BOOLEAN;"))
            log.info("  + Added needs.ngo_accepted")

        # ── 6. Resource inventory enums ─────────────────────────────────
        log.info("Creating resource enums (if needed)...")
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'resourcetype') THEN
                    CREATE TYPE resourcetype AS ENUM
                        ('food','water','medical','shelter','clothing','equipment','transport','money','others');
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'resourcestatus') THEN
                    CREATE TYPE resourcestatus AS ENUM ('available','allocated','depleted','reserved');
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'requeststatus') THEN
                    CREATE TYPE requeststatus AS ENUM ('pending','approved','rejected','fulfilled');
                END IF;
            END$$;
        """))

        # ── 7. Create resource_inventory table ──────────────────────────
        if not table_exists(conn, "resource_inventory"):
            log.info("Creating resource_inventory table...")
            conn.execute(text("""
                CREATE TABLE resource_inventory (
                    id SERIAL PRIMARY KEY,
                    resource_type resourcetype NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    quantity FLOAT NOT NULL DEFAULT 0,
                    unit VARCHAR(50) NOT NULL DEFAULT 'units',
                    location VARCHAR(255),
                    status resourcestatus NOT NULL DEFAULT 'available',
                    allocated_to_ngo_id INTEGER REFERENCES ngos(id) ON DELETE SET NULL,
                    notes TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))

        # ── 8. Create resource_requests table ───────────────────────────
        if not table_exists(conn, "resource_requests"):
            log.info("Creating resource_requests table...")
            conn.execute(text("""
                CREATE TABLE resource_requests (
                    id SERIAL PRIMARY KEY,
                    requesting_ngo_id INTEGER NOT NULL REFERENCES ngos(id) ON DELETE CASCADE,
                    resource_type resourcetype NOT NULL,
                    quantity_requested FLOAT NOT NULL,
                    unit VARCHAR(50) NOT NULL DEFAULT 'units',
                    reason TEXT NOT NULL,
                    urgency VARCHAR(20) NOT NULL DEFAULT 'medium',
                    status requeststatus NOT NULL DEFAULT 'pending',
                    admin_notes TEXT,
                    allocated_resource_id INTEGER REFERENCES resource_inventory(id) ON DELETE SET NULL,
                    quantity_allocated FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    resolved_at TIMESTAMPTZ
                );
            """))

        # ── 9. Pool request enum ─────────────────────────────────────────
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'poolrequeststatus') THEN
                    CREATE TYPE poolrequeststatus AS ENUM
                        ('pending','approved','rejected','expired','completed');
                END IF;
            END$$;
        """))

        # ── 10. Create volunteer_pool_requests table ─────────────────────
        if not table_exists(conn, "volunteer_pool_requests"):
            log.info("Creating volunteer_pool_requests table...")
            conn.execute(text("""
                CREATE TABLE volunteer_pool_requests (
                    id SERIAL PRIMARY KEY,
                    requesting_ngo_id INTEGER NOT NULL REFERENCES ngos(id) ON DELETE CASCADE,
                    source_ngo_id INTEGER REFERENCES ngos(id) ON DELETE SET NULL,
                    required_skills TEXT[] DEFAULT '{}',
                    volunteers_needed INTEGER NOT NULL DEFAULT 1,
                    assigned_volunteer_ids INTEGER[] DEFAULT '{}',
                    reason TEXT NOT NULL,
                    duration_days INTEGER NOT NULL DEFAULT 7,
                    status poolrequeststatus NOT NULL DEFAULT 'pending',
                    admin_notes TEXT,
                    starts_at TIMESTAMPTZ,
                    ends_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    resolved_at TIMESTAMPTZ
                );
            """))

        # ── 11. Create pool_assignments table ────────────────────────────
        if not table_exists(conn, "pool_assignments"):
            log.info("Creating pool_assignments table...")
            conn.execute(text("""
                CREATE TABLE pool_assignments (
                    id SERIAL PRIMARY KEY,
                    pool_request_id INTEGER NOT NULL REFERENCES volunteer_pool_requests(id) ON DELETE CASCADE,
                    volunteer_id INTEGER NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
                    borrowing_ngo_id INTEGER NOT NULL REFERENCES ngos(id) ON DELETE CASCADE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    assigned_at TIMESTAMPTZ DEFAULT NOW(),
                    expires_at TIMESTAMPTZ
                );
            """))

        # ── 12. Create badges table ──────────────────────────────────────
        if not table_exists(conn, "badges"):
            log.info("Creating badges table...")
            conn.execute(text("""
                CREATE TABLE badges (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(150) NOT NULL,
                    description TEXT,
                    icon_emoji VARCHAR(10),
                    criteria_type VARCHAR(50) NOT NULL,
                    threshold FLOAT NOT NULL DEFAULT 1.0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            # Seed initial badges
            log.info("Seeding badge catalogue...")
            conn.execute(text("""
                INSERT INTO badges (code, name, description, icon_emoji, criteria_type, threshold) VALUES
                ('FIRST_RESPONDER', 'First Responder', 'Completed your very first task', '🚨', 'first_task', 1),
                ('RISING_STAR', 'Rising Star', 'Completed 10 tasks', '⭐', 'tasks_completed', 10),
                ('CHAMPION', 'Community Champion', 'Completed 50 tasks', '🏆', 'tasks_completed', 50),
                ('CENTURY', 'Century Hero', 'Completed 100 tasks', '💯', 'tasks_completed', 100),
                ('EXCELLENCE', 'Excellence Award', 'Maintained average rating of 4.5+', '🌟', 'avg_rating', 4.5),
                ('STREAK_5', 'On a Roll', 'Completed 5 tasks in a row', '🔥', 'streak', 5),
                ('MEDICAL_HERO', 'Medical Hero', 'Completed 10 medical tasks', '🏥', 'special', 10),
                ('FOOD_CHAMPION', 'Food Champion', 'Completed 10 food tasks', '🍱', 'special', 10)
                ON CONFLICT (code) DO NOTHING;
            """))

        # ── 13. Create volunteer_badges table ────────────────────────────
        if not table_exists(conn, "volunteer_badges"):
            log.info("Creating volunteer_badges table...")
            conn.execute(text("""
                CREATE TABLE volunteer_badges (
                    id SERIAL PRIMARY KEY,
                    volunteer_id INTEGER NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
                    badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
                    earned_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))

        log.info("✅ Migration complete — all NGO federation tables added successfully.")


if __name__ == "__main__":
    run_migration()
