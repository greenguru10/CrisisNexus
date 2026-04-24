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
    # 1. Fetch all tasks assigned to this volunteer (direct or team)
    from models.need_volunteer_assignment import NeedVolunteerAssignment
    team_assignments = db.query(NeedVolunteerAssignment).filter(
        NeedVolunteerAssignment.volunteer_id == volunteer.id,
        # Remove is_active check to show past tasks too
    ).all()
    team_need_ids = [a.need_id for a in team_assignments]
    team_tasks = db.query(Need).filter(Need.id.in_(team_need_ids)).all() if team_need_ids else []

    # Map by ID
    task_map = {t.id: t for t in team_tasks}
    # 3. Pool assignments (borrowed volunteers)
    from models.pool_request import PoolAssignment
    pool_assignments = db.query(PoolAssignment).filter(
        PoolAssignment.volunteer_id == volunteer.id,
        PoolAssignment.status == "approved"
    ).all()
    pool_req_ids = [pa.pool_request_id for pa in pool_assignments]
    if pool_req_ids:
        from models.pool_request import VolunteerPoolRequest
        pool_reqs = db.query(VolunteerPoolRequest).filter(VolunteerPoolRequest.id.in_(pool_req_ids)).all()
        pool_need_ids = [pr.need_id for pr in pool_reqs if pr.need_id]
        pool_tasks = db.query(Need).filter(Need.id.in_(pool_need_ids)).all() if pool_need_ids else []
        for pt in pool_tasks:
            if pt.id not in task_map:
                pt.is_global_pool = True # UI marker
                task_map[pt.id] = pt

    tasks = sorted(task_map.values(), key=lambda x: x.updated_at, reverse=True)
    from schemas.need_schema import NeedResponse
    from models.need_ngo_assignment import NeedNGOAssignment
    
    results = []
    for t in tasks:
        resp = NeedResponse.model_validate(t)
        if hasattr(t, 'is_global_pool'):
            resp.is_global_pool = True

        # Check if the volunteer's NGO has completed this task
        if volunteer.ngo_id:
            ngo_assignment = db.query(NeedNGOAssignment).filter_by(need_id=t.id, ngo_id=volunteer.ngo_id).first()
            if ngo_assignment:
                resp.my_ngo_completed = ngo_assignment.is_completed
        results.append(resp)
        
    return results



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

    Multi-NGO consensus:
    - Marks this NGO's NeedNGOAssignment as is_completed=True.
    - Need becomes COMPLETED only when ALL accepted NGO assignments are completed.
    - If no NGO assignments exist (legacy/single-NGO), completes immediately.
    - Restores volunteer availability in all paths.
    - Triggers gamification in background.
    """
    from datetime import datetime, timezone
    from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus
    from models.need_volunteer_assignment import NeedVolunteerAssignment

    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")

    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    
    # Authorization: Volunteer must have an active assignment (direct or pool)
    from models.pool_request import PoolAssignment, VolunteerPoolRequest
    
    direct_assignment = db.query(NeedVolunteerAssignment).filter_by(
        need_id=need_id, volunteer_id=volunteer.id, is_active=True
    ).first()
    
    pool_assignment = None
    pool_req_ids = db.query(VolunteerPoolRequest.id).filter_by(need_id=need_id).all()
    if pool_req_ids:
        pool_assignment = db.query(PoolAssignment).filter(
            PoolAssignment.pool_request_id.in_([r.id for r in pool_req_ids]),
            PoolAssignment.volunteer_id == volunteer.id,
            PoolAssignment.status == "approved",
            PoolAssignment.is_active == True
        ).first()

    if not (direct_assignment or pool_assignment):
        raise HTTPException(status_code=403, detail="You are not authorized to complete this task (no active assignment found)")

    if need.status not in [NeedStatus.ACCEPTED, NeedStatus.IN_PROGRESS, NeedStatus.ASSIGNED]:
        raise HTTPException(
            status_code=400, detail="Cannot complete task that isn't in an active state"
        )

    now = datetime.now(timezone.utc)

    # ── Step 1: Mark the appropriate NGO assignment as completed ────────────
    ngo_to_credit_id = None
    if direct_assignment:
        ngo_to_credit_id = volunteer.ngo_id
    elif pool_assignment:
        # For pooled volunteers, we credit the borrowing NGO
        pool_req = db.query(VolunteerPoolRequest).filter_by(id=pool_assignment.pool_request_id).first()
        if pool_req:
            ngo_to_credit_id = pool_req.requesting_ngo_id

    if ngo_to_credit_id:
        ngo_assignment = (
            db.query(NeedNGOAssignment)
            .filter_by(need_id=need_id, ngo_id=ngo_to_credit_id, status=NgoAssignStatus.ACCEPTED)
            .first()
        )
        if ngo_assignment and not ngo_assignment.is_completed:
            ngo_assignment.is_completed = True
            ngo_assignment.completed_at = now
            ngo_assignment.completed_by_volunteer_id = volunteer.id
            logger.info("NGO %d marked as completed for need %d by volunteer %s", ngo_to_credit_id, need_id, volunteer.email)

    # ── Step 2: Restore volunteer availability ───────────────────────────────
    # The volunteer is free to take new tasks as soon as they finish their part.
    volunteer.availability = True

    # ── Step 3: Check if ALL assigned NGO missions are complete ──────────────
    # We must check every NGO that was assigned and DID NOT REJECT.
    # If an NGO is still PENDING or ACCEPTED but not done, the task stays active.
    all_ngo_assignments = (
        db.query(NeedNGOAssignment)
        .filter(NeedNGOAssignment.need_id == need_id, NeedNGOAssignment.status != NgoAssignStatus.REJECTED)
        .all()
    )

    all_done = (
        not all_ngo_assignments  # legacy/no multi-NGO → complete immediately
        or all(a.is_completed and a.status == NgoAssignStatus.ACCEPTED for a in all_ngo_assignments)
    )

    if all_done:
        need.status = NeedStatus.COMPLETED
        need.feedback_rating = payload.feedback_rating
        need.feedback_comments = payload.feedback_comments
        
        # Mark all involved volunteers as available again and deactivate assignments
        db.query(NeedVolunteerAssignment).filter_by(need_id=need_id).update({"is_active": False})
        v_ids = [a.volunteer_id for a in db.query(NeedVolunteerAssignment).filter_by(need_id=need_id).all()]
        for v_id in v_ids:
            v = db.query(Volunteer).filter_by(id=v_id).first()
            if v: v.availability = True

        # Release Pool Volunteers
        from models.pool_request import VolunteerPoolRequest, PoolAssignment
        pool_reqs = db.query(VolunteerPoolRequest).filter_by(need_id=need_id).all()
        for pr in pool_reqs:
            pas = db.query(PoolAssignment).filter_by(pool_request_id=pr.id, is_active=True).all()
            for pa in pas:
                pa.is_active = False
                v = db.query(Volunteer).filter_by(id=pa.volunteer_id).first()
                if v:
                    v.availability = True # Mark available for home NGO again
        
        logger.info(
            "Need %d FULLY COMPLETED — all assigned NGOs have finished. Triggered by volunteer %s.",
            need_id, volunteer.email,
        )
    else:
        pending_ngos = [a.ngo_id for a in all_ngo_assignments if not a.is_completed]
        logger.info(
            "Volunteer %s completed their part for need %d. NGOs still pending: %s",
            volunteer.email, need_id, pending_ngos,
        )

    db.commit()

    # ── Gamification & Trails ────────────────────────────────────────────────
    from services.trail_service import add_trail_entry
    from models.task_trail import TrailAction
    from services.gamification_service import award_points_to_team

    add_trail_entry(
        db, need_id=need_id, action=TrailAction.COMPLETED,
        actor_id=current_user.id, actor_role="volunteer", actor_name=volunteer.name,
        detail={
            "volunteer_id": volunteer.id, 
            "volunteer_name": volunteer.name,
            "feedback_rating": payload.feedback_rating,
            "fully_completed": all_done
        },
    )

    if all_done:
        background_tasks.add_task(
            award_points_to_team,
            need_id,
            payload.feedback_rating,
        )

    if all_done:
        return {"message": "Task fully completed — all NGOs finished!", "status": need.status}
    else:
        pending_count = sum(1 for a in all_ngo_assignments if not a.is_completed)
        return {
            "message": f"Your part is done! Waiting for {pending_count} other NGO(s) to complete.",
            "status": need.status,
            "all_completed": False,
            "ngo_completion_pending": pending_count,
        }



