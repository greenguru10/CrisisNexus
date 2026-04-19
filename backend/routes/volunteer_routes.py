"""
Volunteer routes – Add and list volunteers.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.volunteer import Volunteer
from schemas.volunteer_schema import VolunteerCreate, VolunteerResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Volunteers"])


@router.post("/add-volunteer", response_model=VolunteerResponse, status_code=201)
def add_volunteer(
    payload: VolunteerCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new volunteer.

    **Sample request body:**
    ```json
    {
        "name": "Priya Sharma",
        "skills": ["medical", "first_aid", "logistics"],
        "location": "Mumbai, India",
        "latitude": 19.076,
        "longitude": 72.8777,
        "availability": true,
        "rating": 4.5
    }
    ```
    """
    volunteer = Volunteer(
        name=payload.name,
        skills=payload.skills,
        location=payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        availability=payload.availability,
        rating=payload.rating,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)

    logger.info("Registered volunteer id=%d name=%s", volunteer.id, volunteer.name)
    return volunteer


@router.get("/volunteers", response_model=List[VolunteerResponse])
def list_volunteers(
    available: Optional[bool] = Query(None, description="Filter by availability"),
    skill: Optional[str] = Query(None, description="Filter by skill (partial match)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List all volunteers with optional filters.
    """
    query = db.query(Volunteer)

    if available is not None:
        query = query.filter(Volunteer.availability == available)
    if skill:
        # PostgreSQL ARRAY contains — matches volunteers who have the skill
        query = query.filter(Volunteer.skills.any(skill.lower()))

    volunteers = query.order_by(Volunteer.name).offset(skip).limit(limit).all()
    return volunteers


@router.get("/volunteers/{volunteer_id}", response_model=VolunteerResponse)
def get_volunteer(volunteer_id: int, db: Session = Depends(get_db)):
    """Get a single volunteer by ID."""
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer with id {volunteer_id} not found")
    return volunteer
