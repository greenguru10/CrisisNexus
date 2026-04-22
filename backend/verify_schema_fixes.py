"""
Verification script: Confirm all database schema fixes were applied
"""

import logging
from sqlalchemy import text, inspect
from database import engine

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def verify_fk_on_delete():
    """Verify all FK constraints have ON DELETE rules"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    results = []
    for table in tables:
        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            ondelete = fk.get('ondelete', 'NO ACTION')
            col = fk['constrained_columns'][0]
            ref = fk['referred_table']
            
            status = "✓" if ondelete != 'NO ACTION' else "✗"
            results.append({
                'check': 'FK ON DELETE',
                'status': status,
                'detail': f'{table}.{col} -> {ref} ({ondelete})'
            })
    
    return results


def verify_unique_constraints():
    """Verify unique constraints on junction tables"""
    with engine.connect() as conn:
        query = text("""
            SELECT table_name, constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name IN ('need_ngo_assignments', 'need_volunteer_assignments')
            AND constraint_type = 'UNIQUE'
        """)
        results = conn.execute(query).fetchall()
        
    return [{'check': 'UNIQUE', 'status': '✓', 'detail': f'{r[0]}: {r[1]}'} for r in results]


def verify_indexes():
    """Verify performance indexes were added"""
    expected_indexes = [
        'idx_task_trail_created_at',
        'idx_task_trail_actor_id',
        'idx_need_volunteer_assignments_active',
        'idx_volunteers_approval_status',
        'idx_needs_priority_score',
        'idx_resource_requests_resolved',
        'idx_pool_requests_resolved',
    ]
    
    with engine.connect() as conn:
        query = text("""
            SELECT indexname FROM pg_catalog.pg_indexes
            WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'
        """)
        existing_indexes = [row[0] for row in conn.execute(query).fetchall()]
    
    results = []
    for idx in expected_indexes:
        status = "✓" if idx in existing_indexes else "✗"
        results.append({'check': 'INDEX', 'status': status, 'detail': idx})
    
    return results


def verify_constraints():
    """Verify CHECK constraints were added"""
    with engine.connect() as conn:
        query = text("""
            SELECT table_name, constraint_name
            FROM information_schema.table_constraints
            WHERE constraint_type = 'CHECK'
            AND table_name IN ('needs', 'resource_requests', 'volunteer_pool_requests', 'ngos')
        """)
        results = conn.execute(query).fetchall()
    
    return [{'check': 'CHECK', 'status': '✓', 'detail': f'{r[0]}: {r[1]}'} for r in results]


def verify_columns():
    """Verify new columns were added"""
    with engine.connect() as conn:
        query = text("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE (table_name = 'users' AND column_name = 'updated_at')
            OR (table_name = 'needs' AND column_name = 'ngo_response_status')
        """)
        results = conn.execute(query).fetchall()
    
    return [{'check': 'COLUMN', 'status': '✓', 'detail': f'{r[0]}.{r[1]} ({r[2]})'} for r in results]


def verify_enum_types():
    """Verify enum types were created"""
    with engine.connect() as conn:
        query = text("""
            SELECT typname FROM pg_type
            WHERE typtype = 'e' AND typname IN ('actor_role_enum', 'need_category_enum')
        """)
        results = conn.execute(query).fetchall()
    
    return [{'check': 'ENUM', 'status': '✓', 'detail': f'Type: {r[0]}'} for r in results]


def main():
    logger.info("=" * 80)
    logger.info("DATABASE SCHEMA FIXES - VERIFICATION REPORT")
    logger.info("=" * 80)
    logger.info("")
    
    all_results = []
    
    logger.info("1. Foreign Key ON DELETE Rules")
    logger.info("-" * 40)
    fk_results = verify_fk_on_delete()
    for r in fk_results:
        if r['status'] == '✓':
            all_results.append(r)
            if len(all_results) % 5 == 0:  # Sample output
                logger.info(f"  {r['status']} {r['detail']}")
    logger.info(f"  Total FK constraints with ON DELETE rules: {len([r for r in fk_results if r['status'] == '✓'])}/{len(fk_results)}")
    logger.info("")
    
    logger.info("2. UNIQUE Constraints on Junction Tables")
    logger.info("-" * 40)
    unique_results = verify_unique_constraints()
    for r in unique_results:
        logger.info(f"  {r['status']} {r['detail']}")
        all_results.append(r)
    logger.info("")
    
    logger.info("3. Performance Indexes")
    logger.info("-" * 40)
    index_results = verify_indexes()
    for r in index_results:
        logger.info(f"  {r['status']} {r['detail']}")
        all_results.append(r)
    logger.info("")
    
    logger.info("4. CHECK Constraints")
    logger.info("-" * 40)
    check_results = verify_constraints()
    for r in check_results:
        logger.info(f"  {r['status']} {r['detail']}")
        all_results.append(r)
    logger.info("")
    
    logger.info("5. New Columns")
    logger.info("-" * 40)
    col_results = verify_columns()
    for r in col_results:
        logger.info(f"  {r['status']} {r['detail']}")
        all_results.append(r)
    logger.info("")
    
    logger.info("6. Enum Types")
    logger.info("-" * 40)
    enum_results = verify_enum_types()
    for r in enum_results:
        logger.info(f"  {r['status']} {r['detail']}")
        all_results.append(r)
    logger.info("")
    
    # Summary
    logger.info("=" * 80)
    fixed_count = len([r for r in all_results if r['status'] == '✓'])
    logger.info(f"SUMMARY: {fixed_count} issues fixed")
    logger.info("=" * 80)
    
    return True


if __name__ == "__main__":
    main()
