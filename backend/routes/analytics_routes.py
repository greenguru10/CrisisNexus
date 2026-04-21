"""
Analytics routes – BI dashboard data for Admin (system-wide + per-NGO)
and NGO Coordinator (own NGO only).
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from database import get_db
from models.user import User, UserRole
from models.ngo import NGO, NgoStatus
from models.need import Need, NeedStatus
from models.volunteer import Volunteer
from dependencies.auth_dependency import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics & BI"])


def _need_stats(db: Session, ngo_id: Optional[int] = None) -> dict:
    """Compute need lifecycle counts, optionally scoped to an NGO."""
    q = db.query(Need)
    if ngo_id:
        q = q.filter(Need.ngo_id == ngo_id)

    total = q.count()
    pending = q.filter(Need.status == NeedStatus.PENDING).count()
    assigned = q.filter(Need.status == NeedStatus.ASSIGNED).count()
    accepted = q.filter(Need.status == NeedStatus.ACCEPTED).count()
    in_progress = q.filter(Need.status == NeedStatus.IN_PROGRESS).count()
    completed = q.filter(Need.status == NeedStatus.COMPLETED).count()

    # Re-query for ungrouped
    base = db.query(Need)
    if ngo_id:
        base = base.filter(Need.ngo_id == ngo_id)

    category_rows = base.with_entities(Need.category, func.count(Need.id)).group_by(Need.category).all()
    urgency_rows = base.with_entities(Need.urgency, func.count(Need.id)).group_by(Need.urgency).all()
    avg_score = base.with_entities(func.avg(Need.priority_score)).scalar()

    completion_rate = round((completed / total * 100), 1) if total > 0 else 0.0

    return {
        "total_needs": total,
        "pending": pending,
        "assigned": assigned,
        "accepted": accepted,
        "in_progress": in_progress,
        "completed": completed,
        "completion_rate_pct": completion_rate,
        "average_priority_score": round(float(avg_score), 2) if avg_score else 0.0,
        "category_breakdown": {r[0]: r[1] for r in category_rows},
        "urgency_breakdown": {
            (r[0].value if hasattr(r[0], "value") else r[0]): r[1]
            for r in urgency_rows
        },
    }


def _volunteer_stats(db: Session, ngo_id: Optional[int] = None) -> dict:
    """Compute volunteer counts and efficiency, optionally scoped to an NGO."""
    q = db.query(Volunteer)
    if ngo_id:
        q = q.filter(Volunteer.ngo_id == ngo_id)

    total = q.count()
    available = q.filter(Volunteer.availability == True).count()
    avg_rating = q.with_entities(func.avg(Volunteer.rating)).scalar()
    avg_tasks = q.with_entities(func.avg(Volunteer.tasks_completed)).scalar()

    # Top 5 volunteers by tasks_completed
    top_vols = q.order_by(Volunteer.tasks_completed.desc()).limit(5).all()
    top_volunteers = [
        {
            "id": v.id, "name": v.name,
            "tasks_completed": v.tasks_completed,
            "rating": v.rating,
        }
        for v in top_vols
    ]

    return {
        "total_volunteers": total,
        "available_volunteers": available,
        "average_rating": round(float(avg_rating), 2) if avg_rating else 0.0,
        "average_tasks_completed": round(float(avg_tasks), 1) if avg_tasks else 0.0,
        "top_volunteers": top_volunteers,
    }


@router.get("/overview")
def system_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    [ADMIN] System-wide analytics overview.
    [NGO Coordinator] Automatically scoped to their own NGO.
    """
    ngo_id = None
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo:
            raise HTTPException(status_code=404, detail="NGO not found")
        ngo_id = ngo.id
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    ngo_stats = {}
    if current_user.role == UserRole.ADMIN:
        total_ngos = db.query(func.count(NGO.id)).scalar() or 0
        approved_ngos = db.query(func.count(NGO.id)).filter(NGO.status == NgoStatus.APPROVED).scalar() or 0
        pending_ngos = db.query(func.count(NGO.id)).filter(NGO.status == NgoStatus.PENDING).scalar() or 0
        ngo_stats = {
            "total_ngos": total_ngos,
            "approved_ngos": approved_ngos,
            "pending_ngos": pending_ngos,
        }

    return {
        "scope": "system" if not ngo_id else f"ngo_{ngo_id}",
        **ngo_stats,
        "needs": _need_stats(db, ngo_id),
        "volunteers": _volunteer_stats(db, ngo_id),
    }


@router.get("/ngo/{ngo_id}")
def ngo_analytics(
    ngo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    [ADMIN] Drill-down analytics for a specific NGO.
    [NGO Coordinator] Access only own NGO analytics.
    """
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    # NGO coordinators can only see their own NGO
    if current_user.role == UserRole.NGO:
        own_ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not own_ngo or own_ngo.id != ngo_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "ngo": {"id": ngo.id, "name": ngo.name, "type": ngo.ngo_type.value, "status": ngo.status.value},
        "needs": _need_stats(db, ngo_id),
        "volunteers": _volunteer_stats(db, ngo_id),
    }


@router.get("/volunteer-efficiency")
def volunteer_efficiency(
    ngo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Volunteer efficiency table: tasks completed, avg rating, availability.
    Admin can see all or filter by ngo_id; NGO coordinator sees own NGO only.
    """
    scope_ngo_id = ngo_id

    if current_user.role == UserRole.NGO:
        own_ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not own_ngo:
            raise HTTPException(status_code=404, detail="NGO not found")
        scope_ngo_id = own_ngo.id
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    q = db.query(Volunteer)
    if scope_ngo_id:
        q = q.filter(Volunteer.ngo_id == scope_ngo_id)

    volunteers = q.order_by(Volunteer.tasks_completed.desc()).limit(100).all()
    return [
        {
            "id": v.id, "name": v.name, "email": v.email,
            "tasks_completed": v.tasks_completed,
            "rating": v.rating,
            "availability": v.availability,
            "ngo_id": v.ngo_id,
        }
        for v in volunteers
    ]


@router.get("/funnel")
def needs_funnel(
    ngo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Funnel: Report submitted → Assigned → Accepted → In Progress → Completed."""
    scope_ngo_id = ngo_id

    if current_user.role == UserRole.NGO:
        own_ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not own_ngo:
            raise HTTPException(status_code=404, detail="NGO not found")
        scope_ngo_id = own_ngo.id
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    base = db.query(Need)
    if scope_ngo_id:
        base = base.filter(Need.ngo_id == scope_ngo_id)

    total = base.count()
    assigned = base.filter(Need.status.in_([
        NeedStatus.ASSIGNED, NeedStatus.ACCEPTED, NeedStatus.IN_PROGRESS, NeedStatus.COMPLETED
    ])).count()
    accepted = base.filter(Need.status.in_([
        NeedStatus.ACCEPTED, NeedStatus.IN_PROGRESS, NeedStatus.COMPLETED
    ])).count()
    in_progress = base.filter(Need.status.in_([
        NeedStatus.IN_PROGRESS, NeedStatus.COMPLETED
    ])).count()
    completed = base.filter(Need.status == NeedStatus.COMPLETED).count()

    return {
        "funnel": [
            {"stage": "Submitted", "count": total},
            {"stage": "Assigned", "count": assigned},
            {"stage": "Accepted", "count": accepted},
            {"stage": "In Progress", "count": in_progress},
            {"stage": "Completed", "count": completed},
        ]
    }
