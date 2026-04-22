"""
Models package – imports all ORM models to register them with SQLAlchemy.
This ensures that all models are available when creating the database schema.
"""

from models.user import User
from models.ngo import NGO
from models.need import Need
from models.volunteer import Volunteer
from models.resource import ResourceInventory, ResourceRequest, InventoryContribution
from models.task_trail import TaskTrail
from models.pool_request import VolunteerPoolRequest, PoolAssignment
from models.gamification import Badge, VolunteerBadge
from models.need_ngo_assignment import NeedNGOAssignment
from models.need_volunteer_assignment import NeedVolunteerAssignment

__all__ = [
    "User",
    "NGO",
    "Need",
    "Volunteer",
    "ResourceInventory",
    "ResourceRequest",
    "InventoryContribution",
    "TaskTrail",
    "VolunteerPoolRequest",
    "PoolAssignment",
    "Badge",
    "VolunteerBadge",
    "NeedNGOAssignment",
    "NeedVolunteerAssignment",
]
