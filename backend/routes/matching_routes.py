"""
Matching routes – Match volunteers to needs + dashboard analytics.
Updated: NGO coordinators auto-match within their own NGO's volunteer pool.
Admin retains global match capability.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.need import Need, NeedStatus
from models.ngo import NGO
from models.user import User, UserRole, AccountStatus
from models.volunteer import Volunteer
from schemas.volunteer_schema import MatchResult
from services.matching_service import find_best_volunteer
from services.email_service import send_assignment_email
from services.whatsapp_service import send_assignment_whatsapp
from dependencies.auth_dependency import get_current_user, get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Matching & Analytics"])


def _get_approved_volunteers(db: Session, ngo_id: int | None = None):
    """
    Return approved AND currently available volunteers.
    If ngo_id is set: only volunteers from that NGO.
    Admin (ngo_id=None): all approved volunteers system-wide.
    """
    query = (
        db.query(Volunteer)
        .join(User, User.email == Volunteer.email)
        .filter(
            User.account_status == AccountStatus.APPROVED,
            Volunteer.availability == True,  # noqa: E712 — must be available
        )
    )
    if ngo_id is not None:
        query = query.filter(Volunteer.ngo_id == ngo_id)
    return query.all()


@router.post("/match/{need_id}", response_model=MatchResult)
def match_volunteer(
    need_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Auto-match best available volunteer for a need.
    - **Admin**: Matches from all approved volunteers globally.
    - **NGO Coordinator**: Matches only from their own NGO's volunteers.
    Sends email + WhatsApp notifications in background.
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail=f"Need {need_id} not found")
    if need.status == NeedStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Need {need_id} is already completed")

    # Determine scope
    scope_ngo_id = None
    if current_user.role == UserRole.NGO:
        from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus
        from models.need_volunteer_assignment import NeedVolunteerAssignment
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo:
            raise HTTPException(status_code=403, detail="No approved NGO found for this coordinator")
        scope_ngo_id = ngo.id

        # Check if already has manual assignments
        existing_vols = db.query(NeedVolunteerAssignment).filter_by(
            need_id=need_id, ngo_id=scope_ngo_id, is_active=True
        ).count()
        if existing_vols > 0:
            raise HTTPException(status_code=400, detail="This task already has volunteers assigned by your NGO. Manual assignment is in use.")

        has_ngo_assignment = db.query(NeedNGOAssignment).filter_by(
            need_id=need_id, ngo_id=scope_ngo_id, status=NgoAssignStatus.ACCEPTED
        ).first()
        if not has_ngo_assignment:
            raise HTTPException(status_code=403, detail="This need is not assigned to your NGO")
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admin or NGO coordinators can match volunteers")

    available_volunteers = _get_approved_volunteers(db, ngo_id=scope_ngo_id)
    if not available_volunteers:
        raise HTTPException(
            status_code=404,
            detail="No approved volunteers available" + (f" in NGO id={scope_ngo_id}" if scope_ngo_id else ""),
        )

    # Build workload map
    from models.need_volunteer_assignment import NeedVolunteerAssignment
    active_needs = db.query(NeedVolunteerAssignment.volunteer_id, func.count(NeedVolunteerAssignment.need_id)).join(
        Need, Need.id == NeedVolunteerAssignment.need_id
    ).filter(
        NeedVolunteerAssignment.is_active == True,
        Need.status.in_([NeedStatus.PENDING, NeedStatus.ACCEPTED, NeedStatus.IN_PROGRESS])
    ).group_by(NeedVolunteerAssignment.volunteer_id).all()
    workloads = {vol_id: count for vol_id, count in active_needs if vol_id}

    result = find_best_volunteer(need, available_volunteers, workloads)
    if not result:
        raise HTTPException(status_code=404, detail="No suitable volunteer found for this need")

    volunteer = db.query(Volunteer).filter(Volunteer.id == result["volunteer_id"]).first()
    
    if current_user.role == UserRole.NGO:
        from models.need_volunteer_assignment import NeedVolunteerAssignment
        # Use team assignment table for NGOs
        db.add(NeedVolunteerAssignment(
            need_id=need_id, volunteer_id=result["volunteer_id"], ngo_id=scope_ngo_id,
            assigned_by_id=current_user.id
        ))
        # Keep lifecycle at ASSIGNED so volunteer must explicitly accept.
        # Do not downgrade if another NGO has already progressed it to IN_PROGRESS.
        if need.status == NeedStatus.PENDING:
            need.status = NeedStatus.ASSIGNED
    else:
        # Admin still uses the global single-volunteer field logic, now routed to junction table
        if need.status == NeedStatus.PENDING:
            need.status = NeedStatus.ASSIGNED
        from models.need_volunteer_assignment import NeedVolunteerAssignment
        db.add(NeedVolunteerAssignment(
            need_id=need_id, volunteer_id=result["volunteer_id"], ngo_id=volunteer.ngo_id,
            assigned_by_id=current_user.id
        ))

    if volunteer:
        volunteer.availability = False

    db.commit()
    logger.info("Matched need %d → volunteer %d (%s) score=%.4f [scope_ngo=%s]",
                need_id, result["volunteer_id"], result["volunteer_name"],
                result["match_score"], scope_ngo_id)

    if volunteer:
        if volunteer.email:
            background_tasks.add_task(
                send_assignment_email,
                volunteer_email=volunteer.email,
                volunteer_name=volunteer.name,
                category=need.category,
                location=need.location,
                priority_score=need.priority_score,
            )
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

@router.post("/match/{need_id}/manual")
def manual_match_volunteer(
    need_id: int,
    payload: ManualMatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually assign a specific volunteer to a need. Admin or NGO coordinator."""
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail=f"Need {need_id} not found")
    if need.status == NeedStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot assign a completed need")

    # NGO coordinators can only assign within their NGO
    if current_user.role == UserRole.NGO:
        from models.need_ngo_assignment import NeedNGOAssignment
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo:
            raise HTTPException(status_code=403, detail="No NGO found for coordinator")
        # Check via junction table only (need.ngo_id column has been dropped)
        ngo_assignment = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo.id).first()
        if not ngo_assignment:
            raise HTTPException(status_code=403, detail="Need does not belong to your NGO")
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin or NGO Coordinator required")

    volunteer = db.query(Volunteer).filter(Volunteer.id == payload.volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    vol_user = db.query(User).filter(User.email == volunteer.email).first()
    if not vol_user or vol_user.account_status != AccountStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Volunteer account is not approved")

    # NGO coordinator can only assign volunteers from their NGO
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if volunteer.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Volunteer does not belong to your NGO")

    if need.status == NeedStatus.PENDING:
        need.status = NeedStatus.ASSIGNED
    from models.need_volunteer_assignment import NeedVolunteerAssignment
    db.add(NeedVolunteerAssignment(
        need_id=need_id, volunteer_id=volunteer.id, ngo_id=volunteer.ngo_id,
        assigned_by_id=current_user.id
    ))
    volunteer.availability = False
    db.commit()

    if volunteer.email:
        background_tasks.add_task(
            send_assignment_email,
            volunteer_email=volunteer.email,
            volunteer_name=volunteer.name,
            category=need.category,
            location=need.location,
            priority_score=need.priority_score,
        )
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
    current_user: User = Depends(get_current_user),
):
    """Unassign a volunteer. Admin can unassign any; NGO coordinator only their NGO's needs."""
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail=f"Need {need_id} not found")
    if need.status != NeedStatus.ASSIGNED:
        raise HTTPException(status_code=400, detail="Need is not currently assigned")

    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo or need.ngo_id != ngo.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin or NGO Coordinator required")

    # Unassign logic
    from models.need_volunteer_assignment import NeedVolunteerAssignment
    assignment = db.query(NeedVolunteerAssignment).filter_by(need_id=need_id, is_active=True).first()
    if assignment:
        old_vol = db.query(Volunteer).filter(Volunteer.id == assignment.volunteer_id).first()
        if old_vol:
            old_vol.availability = True
        assignment.is_active = False

    need.status = NeedStatus.PENDING
    db.commit()
    return {"message": f"Need {need_id} is now unassigned and back to pending."}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Return aggregated analytics overview (preserved for backward compatibility)."""
    total_needs = db.query(func.count(Need.id)).scalar() or 0
    pending = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.PENDING).scalar() or 0
    accepted = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.ACCEPTED).scalar() or 0
    in_progress = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.IN_PROGRESS).scalar() or 0
    assigned = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.ASSIGNED).scalar() or 0
    completed = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.COMPLETED).scalar() or 0
    high_priority = db.query(func.count(Need.id)).filter(Need.urgency == "high").scalar() or 0

    total_volunteers = db.query(func.count(Volunteer.id)).scalar() or 0
    available_volunteers = db.query(func.count(Volunteer.id)).filter(Volunteer.availability == True).scalar() or 0
    avg_score = db.query(func.avg(Need.priority_score)).scalar()

    category_rows = db.query(Need.category, func.count(Need.id)).group_by(Need.category).all()
    urgency_rows = db.query(Need.urgency, func.count(Need.id)).group_by(Need.urgency).all()

    return {
        "total_needs": total_needs,
        "pending_needs": pending,
        "accepted_needs": accepted,
        "in_progress_needs": in_progress,
        "assigned_needs": assigned,
        "completed_needs": completed,
        "high_priority_needs": high_priority,
        "total_volunteers": total_volunteers,
        "available_volunteers": available_volunteers,
        "category_breakdown": {r[0]: r[1] for r in category_rows},
        "urgency_breakdown": {
            (r[0].value if hasattr(r[0], "value") else r[0]): r[1] for r in urgency_rows
        },
        "average_priority_score": round(float(avg_score), 2) if avg_score else 0.0,
    }
