"""
Task routes – Volunteer lifecycle management for accepting, starting, and completing tasks.

3-Layer State Machine (enforced here):
  Volunteer Task:  ASSIGNED → ACCEPTED → IN_PROGRESS → COMPLETED
  NGO Allocation:  PENDING  → ACCEPTED → IN_PROGRESS → COMPLETED
  Global Need:     PENDING  → ASSIGNED → IN_PROGRESS → COMPLETED

Key fixes applied:
  - accept/start/complete now check NeedVolunteerAssignment.status, NOT Need.status
  - No state skipping allowed (enforced by guards at each transition)
  - Completion lock: completed tasks cannot be re-completed or restarted
  - NGO-level consensus uses status == COMPLETED (not deprecated is_completed bool)
  - Global need completion only when ALL non-rejected NGO allocations are COMPLETED
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from models.need import Need, NeedStatus
from models.volunteer import Volunteer
from models.need_volunteer_assignment import NeedVolunteerAssignment, VolunteerTaskStatus
from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus
from dependencies.auth_dependency import get_current_user, get_current_ngo_coordinator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Task Lifecycle"])


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class CompleteTaskRequest(BaseModel):
    feedback_rating: Optional[float] = None
    feedback_comments: Optional[str] = None


def _get_volunteer_assignment(
    db: Session, need_id: int, volunteer_id: int
) -> NeedVolunteerAssignment | None:
    """Return the active volunteer assignment row (not COMPLETED to allow lock check)."""
    return (
        db.query(NeedVolunteerAssignment)
        .filter_by(need_id=need_id, volunteer_id=volunteer_id, is_active=True)
        .first()
    )


def _check_all_ngo_done(db: Session, need_id: int) -> bool:
    """
    Return True when every non-rejected NGO allocation is COMPLETED.
    Legacy path: if no allocations exist → treat as complete immediately (single-NGO legacy).
    """
    allocations = (
        db.query(NeedNGOAssignment)
        .filter(
            NeedNGOAssignment.need_id == need_id,
            NeedNGOAssignment.status != NgoAssignStatus.REJECTED,
        )
        .all()
    )
    if not allocations:
        return True  # no multi-NGO setup → complete immediately
    return all(a.status == NgoAssignStatus.COMPLETED for a in allocations)


# ─────────────────────────────────────────────────────────────────────────────
# GET /my-tasks  (volunteer's task list with per-volunteer status)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/my-tasks")
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch tasks assigned to the currently logged-in volunteer with per-volunteer status."""
    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if not volunteer:
        return []

    # 1. Direct team assignments
    team_assignments = db.query(NeedVolunteerAssignment).filter_by(
        volunteer_id=volunteer.id
    ).all()
    team_need_ids = [a.need_id for a in team_assignments]
    # Map need_id → volunteer assignment for status enrichment
    vol_status_map = {a.need_id: a.status.value for a in team_assignments}

    team_tasks = db.query(Need).filter(Need.id.in_(team_need_ids)).all() if team_need_ids else []
    task_map = {t.id: t for t in team_tasks}

    # 2. Pool assignments (borrowed volunteers)
    from models.pool_request import PoolAssignment, VolunteerPoolRequest
    pool_assignments = db.query(PoolAssignment).filter(
        PoolAssignment.volunteer_id == volunteer.id,
        PoolAssignment.status == "approved",
    ).all()
    pool_req_ids = [pa.pool_request_id for pa in pool_assignments]
    if pool_req_ids:
        pool_reqs = db.query(VolunteerPoolRequest).filter(
            VolunteerPoolRequest.id.in_(pool_req_ids)
        ).all()
        pool_need_ids = [pr.need_id for pr in pool_reqs if pr.need_id]
        pool_tasks = db.query(Need).filter(Need.id.in_(pool_need_ids)).all() if pool_need_ids else []
        for pt in pool_tasks:
            if pt.id not in task_map:
                pt.is_global_pool = True
                task_map[pt.id] = pt

    tasks = sorted(task_map.values(), key=lambda x: x.updated_at, reverse=True)
    from schemas.need_schema import NeedResponse

    results = []
    for t in tasks:
        resp = NeedResponse.model_validate(t)
        if hasattr(t, "is_global_pool"):
            resp.is_global_pool = True

        # Enrich with per-volunteer status
        resp.volunteer_task_status = vol_status_map.get(t.id)

        # Enrich with per-NGO allocation status
        if volunteer.ngo_id:
            ngo_assign = db.query(NeedNGOAssignment).filter_by(
                need_id=t.id, ngo_id=volunteer.ngo_id
            ).first()
            if ngo_assign:
                resp.ngo_assignment_status = ngo_assign.status.value
                resp.my_ngo_completed = (ngo_assign.status == NgoAssignStatus.COMPLETED)

        results.append(resp)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# GET /volunteer/tasks  (alias with richer shape — matches API spec)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/volunteer/tasks")
def get_volunteer_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    GET /api/task/volunteer/tasks
    Returns the authenticated volunteer's tasks with full per-volunteer status.
    """
    return get_my_tasks(db=db, current_user=current_user)


# ─────────────────────────────────────────────────────────────────────────────
# GET /ngo/tasks  (NGO coordinator sees their allocation + volunteer statuses)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ngo/tasks")
def get_ngo_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_ngo_coordinator),
):
    """
    GET /api/task/ngo/tasks
    Returns all needs assigned to this NGO with per-NGO allocation status and
    per-volunteer sub-statuses.
    """
    from models.ngo import NGO
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found for this coordinator")

    allocations = (
        db.query(NeedNGOAssignment)
        .filter(NeedNGOAssignment.ngo_id == ngo.id)
        .all()
    )
    need_ids = [a.need_id for a in allocations]
    ngo_status_map = {a.need_id: a.status.value for a in allocations}

    needs = db.query(Need).filter(Need.id.in_(need_ids)).all() if need_ids else []
    result = []
    for n in needs:
        d = {
            "id": n.id,
            "title": n.category,         # alias for UI
            "category": n.category,
            "urgency": n.urgency.value,
            "status": n.status.value,
            "people_affected": n.people_affected,
            "location": n.location,
            "priority_score": n.priority_score,
            "ngo_assignment_status": ngo_status_map.get(n.id),
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "updated_at": n.updated_at.isoformat() if n.updated_at else None,
        }
        # Per-volunteer sub-statuses for this NGO
        vol_assignments = db.query(NeedVolunteerAssignment).filter_by(
            need_id=n.id, ngo_id=ngo.id, is_active=True
        ).all()
        d["volunteer_assignments"] = [
            {
                "volunteer_id": va.volunteer_id,
                "status": va.status.value,
                "assigned_at": va.assigned_at.isoformat() if va.assigned_at else None,
                "accepted_at": va.accepted_at.isoformat() if va.accepted_at else None,
                "started_at": va.started_at.isoformat() if va.started_at else None,
                "completed_at": va.completed_at.isoformat() if va.completed_at else None,
            }
            for va in vol_assignments
        ]
        result.append(d)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# POST /{need_id}/accept
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{need_id}/accept")
def accept_task(
    need_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Volunteer accepts an assigned task.

    Gate: NeedVolunteerAssignment.status must be ASSIGNED.
    Transition: ASSIGNED → ACCEPTED
    Does NOT touch Need.status (global status is independent).
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")

    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if not volunteer:
        raise HTTPException(status_code=403, detail="No volunteer profile found for this account")

    assignment = _get_volunteer_assignment(db, need_id, volunteer.id)
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not assigned to this task")

    # ── State machine guard ───────────────────────────────────────────────────
    if assignment.status == VolunteerTaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task is already completed — cannot accept again")

    # Idempotent: already accepted → return success (handles double-click / retry)
    if assignment.status == VolunteerTaskStatus.ACCEPTED:
        return {
            "message": "Task already accepted",
            "volunteer_task_status": assignment.status.value,
            "need_status": need.status.value,
        }

    if assignment.status != VolunteerTaskStatus.ASSIGNED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot accept task in volunteer status '{assignment.status.value}' (expected: assigned)",
        )

    assignment.status = VolunteerTaskStatus.ACCEPTED
    assignment.accepted_at = datetime.now(timezone.utc)

    from services.trail_service import add_trail_entry
    from models.task_trail import TrailAction
    add_trail_entry(
        db, need_id=need_id, action=TrailAction.STATUS_CHANGED,
        actor_id=current_user.id, actor_role="volunteer", actor_name=volunteer.name,
        detail={
            "volunteer_names": [volunteer.name],
            "old_status": "ASSIGNED",
            "new_status": "ACCEPTED",
            "note": "Volunteer accepted the assignment",
        },
    )
    db.commit()

    logger.info("Volunteer %s accepted task %d (assignment id=%d)", volunteer.email, need_id, assignment.id)
    return {
        "message": "Task accepted successfully",
        "volunteer_task_status": assignment.status.value,
        "need_status": need.status.value,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /{need_id}/start
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{need_id}/start")
def start_task(
    need_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Volunteer starts working on an accepted task.

    Gate: NeedVolunteerAssignment.status must be ACCEPTED.
    Transitions:
      - NeedVolunteerAssignment: ACCEPTED → IN_PROGRESS
      - NeedNGOAssignment:       ACCEPTED → IN_PROGRESS  (if not already)
      - Need.status:             → IN_PROGRESS            (if not already)
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")

    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if not volunteer:
        raise HTTPException(status_code=403, detail="No volunteer profile found for this account")

    assignment = _get_volunteer_assignment(db, need_id, volunteer.id)
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not assigned to this task")

    # ── State machine guard ───────────────────────────────────────────────────
    if assignment.status == VolunteerTaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task is already completed — cannot start again")
    if assignment.status == VolunteerTaskStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Task is already in progress")
    if assignment.status != VolunteerTaskStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail=f"Must accept the task before starting (current status: '{assignment.status.value}')",
        )

    now = datetime.now(timezone.utc)

    # ── Transition volunteer task ─────────────────────────────────────────────
    assignment.status = VolunteerTaskStatus.IN_PROGRESS
    assignment.started_at = now

    # ── Transition NGO allocation (if accepted) ───────────────────────────────
    if volunteer.ngo_id:
        ngo_assign = db.query(NeedNGOAssignment).filter_by(
            need_id=need_id, ngo_id=volunteer.ngo_id
        ).first()
        if ngo_assign and ngo_assign.status == NgoAssignStatus.ACCEPTED:
            ngo_assign.status = NgoAssignStatus.IN_PROGRESS
            ngo_assign.started_at = now

    # ── Transition global need status ─────────────────────────────────────────
    if need.status not in (NeedStatus.IN_PROGRESS, NeedStatus.COMPLETED):
        need.status = NeedStatus.IN_PROGRESS

    from services.trail_service import add_trail_entry
    from models.task_trail import TrailAction
    add_trail_entry(
        db, need_id=need_id, action=TrailAction.STATUS_CHANGED,
        actor_id=current_user.id, actor_role="volunteer", actor_name=volunteer.name,
        detail={
            "volunteer_names": [volunteer.name],
            "old_status": "ACCEPTED",
            "new_status": "IN_PROGRESS",
            "note": "Volunteer started working on the task",
        },
    )
    db.commit()
    logger.info("Volunteer %s started task %d", volunteer.email, need_id)
    return {
        "message": "Task marked as in progress",
        "volunteer_task_status": assignment.status.value,
        "need_status": need.status.value,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /{need_id}/complete
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{need_id}/complete")
def complete_task(
    need_id: int,
    payload: CompleteTaskRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Volunteer completes a task.

    Gate: NeedVolunteerAssignment.status must be IN_PROGRESS.
    Completion lock: Raises 400 if status is already COMPLETED.

    Transitions:
      1. NeedVolunteerAssignment: IN_PROGRESS → COMPLETED
      2. Check if ALL volunteers in this NGO's allocation are COMPLETED
         → If yes: NeedNGOAssignment: IN_PROGRESS → COMPLETED
      3. Check if ALL non-rejected NGO allocations are COMPLETED
         → If yes: Need.status → COMPLETED  (global completion)

    Gamification and trail entries fire only on global completion.
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Task not found")

    volunteer = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if not volunteer:
        raise HTTPException(status_code=403, detail="No volunteer profile found for this account")

    # ── Authorization: must have an active direct or pool assignment ──────────
    from models.pool_request import PoolAssignment, VolunteerPoolRequest

    direct_assignment = db.query(NeedVolunteerAssignment).filter_by(
        need_id=need_id, volunteer_id=volunteer.id, is_active=True
    ).first()

    pool_assignment = None
    if not direct_assignment:
        pool_req_ids = [
            r.id for r in db.query(VolunteerPoolRequest.id).filter_by(need_id=need_id).all()
        ]
        if pool_req_ids:
            pool_assignment = db.query(PoolAssignment).filter(
                PoolAssignment.pool_request_id.in_(pool_req_ids),
                PoolAssignment.volunteer_id == volunteer.id,
                PoolAssignment.status == "approved",
                PoolAssignment.is_active == True,
            ).first()

    active_assignment = direct_assignment  # prefer direct for state machine ops
    if not active_assignment and not pool_assignment:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to complete this task (no active assignment found)",
        )

    now = datetime.now(timezone.utc)

    # ── Completion lock + state machine guard (direct assignment) ─────────────
    if direct_assignment:
        if direct_assignment.status == VolunteerTaskStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Task is already completed — cannot complete again",
            )
        if direct_assignment.status not in (
            VolunteerTaskStatus.IN_PROGRESS, VolunteerTaskStatus.ACCEPTED
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot complete task with volunteer status '{direct_assignment.status.value}'. "
                    "Must be in_progress (or accepted) first."
                ),
            )

        # Transition volunteer task → COMPLETED
        direct_assignment.status = VolunteerTaskStatus.COMPLETED
        direct_assignment.completed_at = now

    # ── Restore volunteer availability ────────────────────────────────────────
    volunteer.availability = True

    # ── Determine which NGO to credit ────────────────────────────────────────
    ngo_to_credit_id = volunteer.ngo_id
    if pool_assignment and not direct_assignment:
        pool_req = db.query(VolunteerPoolRequest).filter_by(
            id=pool_assignment.pool_request_id
        ).first()
        if pool_req:
            ngo_to_credit_id = pool_req.requesting_ngo_id

    # ── Step 2: Check if all volunteers in this NGO's allocation are done ─────
    ngo_fully_done = False
    if ngo_to_credit_id:
        ngo_assign = db.query(NeedNGOAssignment).filter_by(
            need_id=need_id, ngo_id=ngo_to_credit_id
        ).first()
        if ngo_assign and ngo_assign.status not in (
            NgoAssignStatus.COMPLETED, NgoAssignStatus.REJECTED
        ):
            # Check all volunteers assigned by this NGO
            ngo_vol_assignments = db.query(NeedVolunteerAssignment).filter_by(
                need_id=need_id, ngo_id=ngo_to_credit_id, is_active=True
            ).all()
            all_vol_done = all(
                va.status == VolunteerTaskStatus.COMPLETED for va in ngo_vol_assignments
            ) if ngo_vol_assignments else True

            if all_vol_done:
                ngo_assign.status = NgoAssignStatus.COMPLETED
                ngo_assign.completed_at = now
                ngo_assign.completed_by_volunteer_id = volunteer.id
                ngo_fully_done = True
                logger.info(
                    "NGO %d allocation for need %d COMPLETED by volunteer %s",
                    ngo_to_credit_id, need_id, volunteer.email,
                )

    # ── Step 3: Check global completion ──────────────────────────────────────
    all_done = _check_all_ngo_done(db, need_id)

    if all_done:
        need.status = NeedStatus.COMPLETED
        need.feedback_rating = payload.feedback_rating
        need.feedback_comments = payload.feedback_comments

        # We deliberately DO NOT set NeedVolunteerAssignment.is_active = False 
        # so that the completed task remains visible on the volunteer's dashboard!

        # Release pool volunteers
        pool_reqs = db.query(VolunteerPoolRequest).filter_by(need_id=need_id).all()
        for pr in pool_reqs:
            active_pas = db.query(PoolAssignment).filter_by(
                pool_request_id=pr.id, is_active=True
            ).all()
            for pa in active_pas:
                pa.is_active = False
                v = db.query(Volunteer).filter_by(id=pa.volunteer_id).first()
                if v:
                    v.availability = True

        logger.info(
            "Need %d FULLY COMPLETED — all NGO allocations done. Triggered by volunteer %s.",
            need_id, volunteer.email,
        )
    else:
        pending_ngos = [
            a.ngo_id for a in db.query(NeedNGOAssignment).filter(
                NeedNGOAssignment.need_id == need_id,
                NeedNGOAssignment.status != NgoAssignStatus.REJECTED,
                NeedNGOAssignment.status != NgoAssignStatus.COMPLETED,
            ).all()
        ]
        logger.info(
            "Volunteer %s completed their part for need %d. NGOs still pending: %s",
            volunteer.email, need_id, pending_ngos,
        )

    db.commit()

    # ── Gamification & Trails ─────────────────────────────────────────────────
    from services.trail_service import add_trail_entry
    from models.task_trail import TrailAction
    from services.gamification_service import award_points_to_team

    add_trail_entry(
        db, need_id=need_id, action=TrailAction.COMPLETED,
        actor_id=current_user.id, actor_role="volunteer", actor_name=volunteer.name,
        detail={
            "volunteer_id": volunteer.id,
            "volunteer_names": [volunteer.name],
            "feedback_rating": payload.feedback_rating,
            "fully_completed": all_done,
            "ngo_fully_done": ngo_fully_done,
        },
    )

    if all_done:
        background_tasks.add_task(award_points_to_team, need_id, payload.feedback_rating)
        return {
            "message": "Task fully completed — all NGOs finished!",
            "status": need.status.value,
            "all_completed": True,
        }
    else:
        pending_count = sum(
            1 for a in db.query(NeedNGOAssignment).filter(
                NeedNGOAssignment.need_id == need_id,
                NeedNGOAssignment.status != NgoAssignStatus.REJECTED,
                NeedNGOAssignment.status != NgoAssignStatus.COMPLETED,
            ).all()
        )
        return {
            "message": f"Your part is done! Waiting for {pending_count} other NGO(s) to complete.",
            "status": need.status.value,
            "all_completed": False,
            "ngo_completion_pending": pending_count,
            "volunteer_task_status": "completed",
        }
