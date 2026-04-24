
import sys
import os
import logging

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, Base
# Import all models to ensure they are registered with Base.metadata
from models.user import User
from models.ngo import NGO
from models.volunteer import Volunteer
from models.need import Need
from models.need_ngo_assignment import NeedNGOAssignment
from models.need_volunteer_assignment import NeedVolunteerAssignment
from models.resource import ResourceInventory, ResourceRequest, InventoryContribution
from models.pool_request import VolunteerPoolRequest, PoolAssignment
from models.task_trail import TaskTrail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    logger.info("Initializing database schema...")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database schema created successfully.")
        
        print("\n" + "="*50)
        print("DATABASE SETUP COMPLETE")
        print("="*50)
        print("\nNext steps:")
        print("1. Run 'python add_admin.py' to create your admin account.")
        print("2. Start the backend server: 'uvicorn main:app --reload'")
        print("="*50)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
