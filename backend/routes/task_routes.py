"""
Task routes – Volunteer lifecycle management for accepting, starting, and completing tasks.
Updated: hooks gamification service on completion.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.need import Need, NeedStatus
from models.volunteer import Volunteer
from dependencies.auth_dependency import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Task Lifecycle"])


class CompleteTaskRequest(BaseModel):
    feedback_rating: Optional[float] = None
    feedback_comments: Optional[str] = None


@router.get("/my-tasks")
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch tasks assigned to the currently logged-in volunteer."""
    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if not volunteer:
        return []
    from models.need_volunteer_assignment import NeedVolunteerAssignment
    assignments = db.query(NeedVolunteerAssignment).filter(
        NeedVolunteerAssignment.volunteer_id == volunteer.id,
        NeedVolunteerAssignment.is_active == True
    ).all()
    need_ids = [a.need_id for a in assignments]
    if not need_ids:
        return []

    tasks = db.query(Need).filter(Need.id.in_(need_ids)).order_by(Need.updated_at.desc()).all()
    from schemas.need_schema import NeedResponse
    return [NeedResponse.model_validate(t) for t in tasks]


@router.post("/{need_id}/accept")
def accept_task(
    need_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Volunteer accepts an assigned task."""
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")

    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    from models.need_volunteer_assignment import NeedVolunteerAssignment
    assignment = db.query(NeedVolunteerAssignment).filter_by(need_id=need_id, volunteer_id=volunteer.id, is_active=True).first() if volunteer else None
    
    if not volunteer or not assignment:
        raise HTTPException(status_code=403, detail="You are not authorized to accept this task")

    if need.status not in [NeedStatus.ASSIGNED, NeedStatus.PENDING]:
        raise HTTPException(status_code=400, detail=f"Cannot accept task in '{need.status}' status")

    # Reset streak if skipping (not applicable here — this is acceptance)
    need.status = NeedStatus.ACCEPTED
    db.commit()
    logger.info("Volunteer %s accepted task %d", volunteer.email, need_id)
    return {"message": "Task accepted successfully", "status": need.status}


@router.post("/{need_id}/start")
def start_task(
    need_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Volunteer starts working on an accepted task."""
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")

    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    from models.need_volunteer_assignment import NeedVolunteerAssignment
    assignment = db.query(NeedVolunteerAssignment).filter_by(need_id=need_id, volunteer_id=volunteer.id, is_active=True).first() if volunteer else None

    if not volunteer or not assignment:
        raise HTTPException(status_code=403, detail="Not authorized")

    if need.status != NeedStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Must accept task before starting")

    need.status = NeedStatus.IN_PROGRESS
    db.commit()
    return {"message": "Task marked as in progress", "status": need.status}


@router.post("/{need_id}/complete")
def complete_task(
    need_id: int,
    payload: CompleteTaskRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Volunteer completes a task and optionally leaves feedback.
    Triggers gamification: badge checks and stats update run in background.
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")

    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    from models.need_volunteer_assignment import NeedVolunteerAssignment
    assignment = db.query(NeedVolunteerAssignment).filter_by(need_id=need_id, volunteer_id=volunteer.id, is_active=True).first() if volunteer else None

    if not volunteer or not assignment:
        raise HTTPException(status_code=403, detail="Not authorized")

    if need.status not in [NeedStatus.ACCEPTED, NeedStatus.IN_PROGRESS, NeedStatus.ASSIGNED]:
        raise HTTPException(
            status_code=400, detail="Cannot complete task that isn't pending or in progress"
        )

    need.status = NeedStatus.COMPLETED
    need.feedback_rating = payload.feedback_rating
    need.feedback_comments = payload.feedback_comments
    volunteer.availability = True
    db.commit()

    logger.info("Volunteer %s completed task %d", volunteer.email, need_id)

    # ── Gamification: update stats and award badges in background ─
    from services.gamification_service import update_volunteer_stats_on_completion
    background_tasks.add_task(
        update_volunteer_stats_on_completion,
        volunteer.id,
        payload.feedback_rating,
        db,
    )

    return {"message": "Task completed successfully", "status": need.status}
