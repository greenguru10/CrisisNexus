"""
Task routes – Volunteer lifecycle management for accepting, starting, and completing tasks.
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

def _verify_assignment(need: Need, user):
    """Ensure the user is actually the assigned volunteer."""
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # In a real app we might link User.email to Volunteer.email directly to confirm identity
    # Currently get_current_user returns a User object. We need to find the related Volunteer.
    from models.user import User
    pass

@router.post("/{need_id}/accept")
def accept_task(
    need_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Volunteer accepts an assigned task."""
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")
        
    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if not volunteer or need.assigned_volunteer_id != volunteer.id:
        raise HTTPException(status_code=403, detail="You are not authorized to accept this task")

    if need.status not in [NeedStatus.ASSIGNED, NeedStatus.PENDING]:
        raise HTTPException(status_code=400, detail=f"Cannot accept task in {need.status} status")

    need.status = NeedStatus.ACCEPTED
    db.commit()
    logger.info("Volunteer %s accepted task %d", volunteer.email, need_id)
    return {"message": "Task accepted successfully", "status": need.status}

@router.post("/{need_id}/start")
def start_task(
    need_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Volunteer starts working on an accepted task."""
    need = db.query(Need).filter(Need.id == need_id).first()
    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    
    if not volunteer or need.assigned_volunteer_id != volunteer.id:
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Volunteer completes a task and optionally leaves feedback."""
    need = db.query(Need).filter(Need.id == need_id).first()
    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    
    if not volunteer or need.assigned_volunteer_id != volunteer.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if need.status not in [NeedStatus.ACCEPTED, NeedStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="Cannot complete task that isn't started or accepted")

    need.status = NeedStatus.COMPLETED
    need.feedback_rating = payload.feedback_rating
    need.feedback_comments = payload.feedback_comments
    
    # Mark volunteer as available again now that a task is finished
    volunteer.availability = True
    
    db.commit()
    
    logger.info("Volunteer %s completed task %d", volunteer.email, need_id)
    return {"message": "Task completed successfully", "status": need.status}

@router.get("/my-tasks")
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Fetch tasks assigned to the currently logged in volunteer."""
    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if not volunteer:
        return []
        
    tasks = db.query(Need).filter(Need.assigned_volunteer_id == volunteer.id).order_by(Need.updated_at.desc()).all()
    # Serialize using dict or schema
    from schemas.need_schema import NeedResponse
    return [NeedResponse.model_validate(t) for t in tasks]
