import sys
import logging
import json

logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
sys.path.append(r"d:\Repo-Merge-GSC\Fedeerated_NGO\CrisisNexus\backend")

from database import SessionLocal
from models.user import User, UserRole, AccountStatus
from models.volunteer import Volunteer, VolunteerApprovalStatus
from models.ngo import NGO

db = SessionLocal()

# Simulate current_user is NGO
current_user = db.query(User).filter(User.email == "vin123@gmail.com").first()
print(f"Current User: {current_user.email}, Role: {current_user.role.value}")

query = (
    db.query(Volunteer)
    .join(User, User.email == Volunteer.email)
    .filter(User.role == UserRole.VOLUNTEER)
    .filter(User.account_status == AccountStatus.APPROVED)
    .filter(Volunteer.approval_status == VolunteerApprovalStatus.APPROVED)
)

ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
scope_id = ngo.id if ngo else -1
print(f"NGO scope_id: {scope_id}")

query = query.filter(Volunteer.ngo_id == scope_id)

results = query.all()
print(f"Results Count: {len(results)}")
for r in results:
    print(f" - {r.name} ({r.email})")

db.close()
