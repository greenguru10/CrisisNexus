import sys
import os

# Add the backend directory to sys.path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.ngo import NGO
from models.need import Need
from models.need_ngo_assignment import NeedNGOAssignment
from models.need_volunteer_assignment import NeedVolunteerAssignment
from fastapi.encoders import jsonable_encoder
import json

db = SessionLocal()

try:
    # Just grab any NGO that has assignments
    ngo = db.query(NGO).first()
    if not ngo:
        print("No NGOs found")
        sys.exit()

    assignments = db.query(NeedNGOAssignment).filter(NeedNGOAssignment.ngo_id == ngo.id).all()
    need_ids = [a.need_id for a in assignments]
    status_map = {a.need_id: a.status.value for a in assignments}

    needs = db.query(Need).filter(Need.id.in_(need_ids)).all() if need_ids else []
    result = []
    for n in needs:
        d = n.__dict__.copy()
        d.pop("_sa_instance_state", None)
        d["ngo_assignment_status"] = status_map.get(n.id)
        
        manual_count = db.query(NeedVolunteerAssignment).filter_by(
            need_id=n.id, ngo_id=ngo.id, is_active=True
        ).count()
        d["has_manual_assignments"] = manual_count > 0
        
        result.append(d)

    # Try to encode it with FastAPI's encoder
    try:
        encoded = jsonable_encoder(result)
        print("Success! Encoding works:")
        print(json.dumps(encoded, indent=2))
    except Exception as e:
        print(f"Encoding Error: {e}")

finally:
    db.close()
