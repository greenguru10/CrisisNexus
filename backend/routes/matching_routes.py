"""
Matching routes – Match volunteers to needs + dashboard analytics.
Sends email and WhatsApp notifications on assignment via BackgroundTasks.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.need import Need, NeedStatus
from models.volunteer import Volunteer
from schemas.volunteer_schema import MatchResult
from services.matching_service import find_best_volunteer
from services.email_service import send_assignment_email
from services.whatsapp_service import send_assignment_whatsapp

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Matching & Analytics"])


@router.post("/match/{need_id}", response_model=MatchResult)
def match_volunteer(
    need_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Find and assign the best available volunteer for a given need.
    Updates the need status to 'assigned' and marks the volunteer as unavailable.
    Sends email + WhatsApp notifications in the background.

    **Sample response:**
    ```json
    {
        "need_id": 1,
        "volunteer_id": 5,
        "volunteer_name": "Priya Sharma",
        "match_score": 0.7125,
        "distance_km": 23.45,
        "skill_match": 0.6667,
        "message": "Volunteer Priya Sharma assigned to need 1"
    }
    ```
    """
    # Validate need exists and is pending
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail=f"Need with id {need_id} not found")

    if need.status == NeedStatus.ASSIGNED:
        raise HTTPException(status_code=400, detail=f"Need {need_id} is already assigned to volunteer {need.assigned_volunteer_id}")
    if need.status == NeedStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Need {need_id} is already completed")

    # Get all available volunteers
    available_volunteers = db.query(Volunteer).filter(Volunteer.availability == True).all()
    if not available_volunteers:
        raise HTTPException(status_code=404, detail="No available volunteers found")

    # Find best match
    result = find_best_volunteer(need, available_volunteers)
    if not result:
        raise HTTPException(status_code=404, detail="No suitable volunteer found for this need")

    # Update need status
    need.status = NeedStatus.ASSIGNED
    need.assigned_volunteer_id = result["volunteer_id"]

    # Mark volunteer as unavailable
    volunteer = db.query(Volunteer).filter(Volunteer.id == result["volunteer_id"]).first()
    if volunteer:
        volunteer.availability = False

    db.commit()

    logger.info("Matched need %d → volunteer %d (%s), score=%.4f",
                need_id, result["volunteer_id"], result["volunteer_name"], result["match_score"])

    # ── Send notifications in background ─────────────────────────
    if volunteer:
        # Email notification
        if volunteer.email:
            background_tasks.add_task(
                send_assignment_email,
                volunteer_email=volunteer.email,
                volunteer_name=volunteer.name,
                category=need.category,
                location=need.location,
                priority_score=need.priority_score,
            )

        # WhatsApp notification
        if volunteer.mobile_number:
            background_tasks.add_task(
                send_assignment_whatsapp,
                to_number=volunteer.mobile_number,
                volunteer_name=volunteer.name,
                category=need.category,
                location=need.location,
            )

    return MatchResult(
        need_id=need_id,
        volunteer_id=result["volunteer_id"],
        volunteer_name=result["volunteer_name"],
        match_score=result["match_score"],
        distance_km=result["distance_km"],
        skill_match=result["skill_match"],
        message=f"Volunteer {result['volunteer_name']} assigned to need {need_id}",
    )

from schemas.auth_schema import ManualMatchRequest
from dependencies.auth_dependency import get_current_admin

@router.post("/match/{need_id}/manual")
def manual_match_volunteer(
    need_id: int,
    payload: ManualMatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """
    Manually assign a selected volunteer to a need by an Admin.
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail=f"Need with id {need_id} not found")

    if need.status == NeedStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Need {need_id} is already completed")

    volunteer = db.query(Volunteer).filter(Volunteer.id == payload.volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
        
    need.status = NeedStatus.ASSIGNED
    need.assigned_volunteer_id = volunteer.id
    volunteer.availability = False
    db.commit()

    logger.info("Admin %s manually matched need %d → volunteer %d", current_user.email, need_id, volunteer.id)

    # Email notification
    if volunteer.email:
        background_tasks.add_task(
            send_assignment_email,
            volunteer_email=volunteer.email,
            volunteer_name=volunteer.name,
            category=need.category,
            location=need.location,
            priority_score=need.priority_score,
        )

    # WhatsApp notification
    if volunteer.mobile_number:
        background_tasks.add_task(
            send_assignment_whatsapp,
            to_number=volunteer.mobile_number,
            volunteer_name=volunteer.name,
            category=need.category,
            location=need.location,
        )

    return {"message": f"Volunteer {volunteer.name} successfully assigned."}


@router.post("/match/{need_id}/unassign")
def unassign_volunteer(
    need_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """
    **[ADMIN ONLY]** Unassign a volunteer from a need.
    Sets need back to 'pending' and marks volunteer as available again.
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail=f"Need with id {need_id} not found")

    if need.status != NeedStatus.ASSIGNED:
        raise HTTPException(status_code=400, detail="Need is not currently assigned")

    # Free the previously assigned volunteer
    if need.assigned_volunteer_id:
        old_vol = db.query(Volunteer).filter(Volunteer.id == need.assigned_volunteer_id).first()
        if old_vol:
            old_vol.availability = True

    need.status = NeedStatus.PENDING
    need.assigned_volunteer_id = None
    db.commit()

    logger.info("Admin %s unassigned need %d", current_user.email, need_id)
    return {"message": f"Need {need_id} is now unassigned and back to pending."}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """
    Return analytics overview for the dashboard.

    **Sample response:**
    ```json
    {
        "total_needs": 75,
        "pending_needs": 40,
        "assigned_needs": 25,
        "completed_needs": 10,
        "high_priority_needs": 30,
        "total_volunteers": 35,
        "available_volunteers": 20,
        "category_breakdown": { "food": 15, "medical": 20 },
        "urgency_breakdown": { "high": 30, "medium": 25, "low": 20 },
        "average_priority_score": 62.5
    }
    ```
    """
    total_needs = db.query(func.count(Need.id)).scalar() or 0
    pending = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.PENDING).scalar() or 0
    assigned = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.ASSIGNED).scalar() or 0
    completed = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.COMPLETED).scalar() or 0
    high_priority = db.query(func.count(Need.id)).filter(Need.urgency == "high").scalar() or 0

    total_volunteers = db.query(func.count(Volunteer.id)).scalar() or 0
    available_volunteers = db.query(func.count(Volunteer.id)).filter(Volunteer.availability == True).scalar() or 0

    avg_score = db.query(func.avg(Need.priority_score)).scalar()
    avg_score = round(float(avg_score), 2) if avg_score else 0.0

    # Category breakdown
    category_rows = db.query(Need.category, func.count(Need.id)).group_by(Need.category).all()
    category_breakdown = {row[0]: row[1] for row in category_rows}

    # Urgency breakdown
    urgency_rows = db.query(Need.urgency, func.count(Need.id)).group_by(Need.urgency).all()
    urgency_breakdown = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in urgency_rows}

    return {
        "total_needs": total_needs,
        "pending_needs": pending,
        "assigned_needs": assigned,
        "completed_needs": completed,
        "high_priority_needs": high_priority,
        "total_volunteers": total_volunteers,
        "available_volunteers": available_volunteers,
        "category_breakdown": category_breakdown,
        "urgency_breakdown": urgency_breakdown,
        "average_priority_score": avg_score,
    }
