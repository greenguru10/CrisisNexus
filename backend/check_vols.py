import sys
import logging
import json

logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
sys.path.append(r"d:\Repo-Merge-GSC\Fedeerated_NGO\CrisisNexus\backend")

from database import SessionLocal
from models.user import User
from models.volunteer import Volunteer
from models.ngo import NGO

db = SessionLocal()

out = {"ngos": [], "users": [], "vols": []}

for n in db.query(NGO).all():
    out["ngos"].append({"id": n.id, "name": n.name, "coord": n.coordinator_user_id})

for u in db.query(User).filter(User.role.in_(["ngo", "volunteer"])).all():
    out["users"].append({"id": u.id, "email": u.email, "role": u.role.value, "status": u.account_status.value})

for v in db.query(Volunteer).all():
    app_val = v.approval_status.value if v.approval_status else None
    out["vols"].append({"id": v.id, "email": v.email, "ngo_id": v.ngo_id, "appr": app_val})

db.close()

with open("vols_dump.json", "w") as f:
    json.dump(out, f, indent=2)
