import os
from sqlalchemy import text
from database import engine

def run_migration():
    print("Starting database schema fixes migration...")
    with engine.begin() as conn:
        # Phase 1: Fix Missing ON DELETE Constraints
        print("Fixing ON DELETE constraints...")
        
        # volunteers.ngo_id
        conn.execute(text("ALTER TABLE volunteers DROP CONSTRAINT IF EXISTS volunteers_ngo_id_fkey;"))
        conn.execute(text("ALTER TABLE volunteers ADD CONSTRAINT volunteers_ngo_id_fkey FOREIGN KEY (ngo_id) REFERENCES ngos(id) ON DELETE SET NULL;"))
        
        # volunteer_pool_requests.requesting_ngo_id
        conn.execute(text("ALTER TABLE volunteer_pool_requests DROP CONSTRAINT IF EXISTS volunteer_pool_requests_requesting_ngo_id_fkey;"))
        conn.execute(text("ALTER TABLE volunteer_pool_requests ADD CONSTRAINT volunteer_pool_requests_requesting_ngo_id_fkey FOREIGN KEY (requesting_ngo_id) REFERENCES ngos(id) ON DELETE CASCADE;"))
        
        # volunteer_pool_requests.need_id
        conn.execute(text("ALTER TABLE volunteer_pool_requests DROP CONSTRAINT IF EXISTS volunteer_pool_requests_need_id_fkey;"))
        conn.execute(text("ALTER TABLE volunteer_pool_requests ADD CONSTRAINT volunteer_pool_requests_need_id_fkey FOREIGN KEY (need_id) REFERENCES needs(id) ON DELETE SET NULL;"))
        
        # pool_assignments.pool_request_id
        conn.execute(text("ALTER TABLE pool_assignments DROP CONSTRAINT IF EXISTS pool_assignments_pool_request_id_fkey;"))
        conn.execute(text("ALTER TABLE pool_assignments ADD CONSTRAINT pool_assignments_pool_request_id_fkey FOREIGN KEY (pool_request_id) REFERENCES volunteer_pool_requests(id) ON DELETE CASCADE;"))
        
        # pool_assignments.borrowing_ngo_id
        conn.execute(text("ALTER TABLE pool_assignments DROP CONSTRAINT IF EXISTS pool_assignments_borrowing_ngo_id_fkey;"))
        conn.execute(text("ALTER TABLE pool_assignments ADD CONSTRAINT pool_assignments_borrowing_ngo_id_fkey FOREIGN KEY (borrowing_ngo_id) REFERENCES ngos(id) ON DELETE CASCADE;"))
        
        # pool_assignments.lending_ngo_id
        conn.execute(text("ALTER TABLE pool_assignments DROP CONSTRAINT IF EXISTS pool_assignments_lending_ngo_id_fkey;"))
        conn.execute(text("ALTER TABLE pool_assignments ADD CONSTRAINT pool_assignments_lending_ngo_id_fkey FOREIGN KEY (lending_ngo_id) REFERENCES ngos(id) ON DELETE SET NULL;"))
        
        # resource_requests.need_id
        conn.execute(text("ALTER TABLE resource_requests DROP CONSTRAINT IF EXISTS resource_requests_need_id_fkey;"))
        conn.execute(text("ALTER TABLE resource_requests ADD CONSTRAINT resource_requests_need_id_fkey FOREIGN KEY (need_id) REFERENCES needs(id) ON DELETE SET NULL;"))
        
        # resource_inventory.allocated_to_ngo_id
        conn.execute(text("ALTER TABLE resource_inventory DROP CONSTRAINT IF EXISTS resource_inventory_allocated_to_ngo_id_fkey;"))
        conn.execute(text("ALTER TABLE resource_inventory ADD CONSTRAINT resource_inventory_allocated_to_ngo_id_fkey FOREIGN KEY (allocated_to_ngo_id) REFERENCES ngos(id) ON DELETE SET NULL;"))
        
        # volunteer_badges.volunteer_id
        conn.execute(text("ALTER TABLE volunteer_badges DROP CONSTRAINT IF EXISTS volunteer_badges_volunteer_id_fkey;"))
        conn.execute(text("ALTER TABLE volunteer_badges ADD CONSTRAINT volunteer_badges_volunteer_id_fkey FOREIGN KEY (volunteer_id) REFERENCES volunteers(id) ON DELETE CASCADE;"))
        
        # Phase 2: Add Missing Indexes
        print("Adding missing indexes...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pool_assignments_pool_request_id ON pool_assignments(pool_request_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pool_assignments_borrowing_ngo_id ON pool_assignments(borrowing_ngo_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_volunteer_badges_badge_id ON volunteer_badges(badge_id);"))
        
        # Phase 3: Data Migration
        print("Migrating data to junction tables...")
        conn.execute(text("ALTER TABLE need_volunteer_assignments ALTER COLUMN ngo_id DROP NOT NULL;"))
        # 3.1 Migrating needs.ngo_id to need_ngo_assignments
        conn.execute(text("""
            INSERT INTO need_ngo_assignments (need_id, ngo_id, status, assigned_at)
            SELECT id, ngo_id, 'accepted', NOW()
            FROM needs
            WHERE ngo_id IS NOT NULL
            ON CONFLICT DO NOTHING;
        """))
        
        # 3.2 Migrating needs.assigned_volunteer_id to need_volunteer_assignments
        conn.execute(text("""
            INSERT INTO need_volunteer_assignments (need_id, volunteer_id, ngo_id, assigned_at, is_active)
            SELECT n.id, n.assigned_volunteer_id, COALESCE(n.ngo_id, v.ngo_id), NOW(), true
            FROM needs n
            JOIN volunteers v ON n.assigned_volunteer_id = v.id
            WHERE n.assigned_volunteer_id IS NOT NULL
            ON CONFLICT DO NOTHING;
        """))
        
        # 3.3 Migrating volunteer_pool_requests.assigned_volunteer_ids to pool_assignments
        # Using PostgreSQL unnest to expand array into rows
        conn.execute(text("""
            INSERT INTO pool_assignments (pool_request_id, volunteer_id, borrowing_ngo_id, status, is_active, assigned_at)
            SELECT pr.id, unnest(pr.assigned_volunteer_ids), pr.requesting_ngo_id, 'approved', true, NOW()
            FROM volunteer_pool_requests pr
            WHERE pr.assigned_volunteer_ids IS NOT NULL AND array_length(pr.assigned_volunteer_ids, 1) > 0
            ON CONFLICT DO NOTHING;
        """))
        
        # Phase 4: Drop Redundant Columns & Make Junction columns nullable
        print("Dropping redundant columns...")
        conn.execute(text("ALTER TABLE needs DROP COLUMN IF EXISTS ngo_id;"))
        conn.execute(text("ALTER TABLE needs DROP COLUMN IF EXISTS assigned_volunteer_id;"))
        conn.execute(text("ALTER TABLE volunteer_pool_requests DROP COLUMN IF EXISTS assigned_volunteer_ids;"))
        
        print("Migration complete!")

if __name__ == "__main__":
    run_migration()
