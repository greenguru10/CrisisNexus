"""
Gamification routes – Leaderboards, badges, and volunteer achievement tracking.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole
from models.ngo import NGO
from models.volunteer import Volunteer
from models.gamification import Badge, VolunteerBadge
from dependencies.auth_dependency import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/gamification", tags=["Gamification"])


@router.get("/leaderboard")
def get_leaderboard(
    ngo_id: Optional[int] = Query(None, description="Filter by NGO (required for volunteers)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    NGO-scoped leaderboard of top volunteers by tasks_completed.
    - Admin: can view any NGO (pass ngo_id) or see global top performers.
    - NGO Coordinator: automatically scoped to own NGO.
    - Volunteer: automatically scoped to own NGO.
    """
    scope_ngo_id = ngo_id

    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if not ngo:
            raise HTTPException(status_code=404, detail="NGO not found")
        scope_ngo_id = ngo.id
    elif current_user.role == UserRole.VOLUNTEER:
        # Find volunteer's NGO
        vol = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
        if vol and vol.ngo_id:
            scope_ngo_id = vol.ngo_id
        else:
            return {"leaderboard": [], "ngo_id": None, "message": "Volunteer not assigned to an NGO"}

    q = db.query(Volunteer)
    if scope_ngo_id:
        q = q.filter(Volunteer.ngo_id == scope_ngo_id)

    top = q.order_by(Volunteer.points.desc(), Volunteer.rating.desc()).limit(limit).all()

    # Enrich with badges
    leaderboard = []
    for rank, vol in enumerate(top, start=1):
        earned = db.query(VolunteerBadge).filter(VolunteerBadge.volunteer_id == vol.id).all()
        badge_codes = []
        for vb in earned:
            badge = db.query(Badge).filter(Badge.id == vb.badge_id).first()
            if badge:
                badge_codes.append({"code": badge.code, "icon": badge.icon_emoji, "name": badge.name})

        leaderboard.append({
            "rank": rank,
            "volunteer_id": vol.id,
            "name": vol.name,
            "tasks_completed": vol.tasks_completed,
            "points": vol.points,
            "rating": vol.rating,
            "availability": vol.availability,
            "badges": badge_codes,
        })


    return {"leaderboard": leaderboard, "ngo_id": scope_ngo_id}


@router.get("/badges")
def list_badges(db: Session = Depends(get_db)):
    """Public: List all available badges in the system."""
    badges = db.query(Badge).order_by(Badge.threshold).all()
    return [
        {
            "code": b.code, "name": b.name, "description": b.description,
            "icon_emoji": b.icon_emoji, "criteria_type": b.criteria_type, "threshold": b.threshold,
        }
        for b in badges
    ]


@router.get("/badges/my")
def my_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """[Volunteer] Get own earned badges."""
    vol = db.query(Volunteer).filter(Volunteer.email == current_user.email).first()
    if not vol:
        raise HTTPException(status_code=404, detail="Volunteer profile not found")

    earned = db.query(VolunteerBadge).filter(VolunteerBadge.volunteer_id == vol.id).all()
    result = []
    for vb in earned:
        badge = db.query(Badge).filter(Badge.id == vb.badge_id).first()
        if badge:
            result.append({
                "code": badge.code, "name": badge.name, "description": badge.description,
                "icon_emoji": badge.icon_emoji, "earned_at": vb.earned_at.isoformat(),
            })
    return {"volunteer_id": vol.id, "badges": result}


@router.get("/volunteer/{volunteer_id}/badges")
def volunteer_badges(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get badges for a specific volunteer (Admin/NGO can view any)."""
    vol = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not vol:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    earned = db.query(VolunteerBadge).filter(VolunteerBadge.volunteer_id == volunteer_id).all()
    result = []
    for vb in earned:
        badge = db.query(Badge).filter(Badge.id == vb.badge_id).first()
        if badge:
            result.append({
                "code": badge.code, "name": badge.name, "icon_emoji": badge.icon_emoji,
                "earned_at": vb.earned_at.isoformat(),
            })
    return {"volunteer_id": volunteer_id, "name": vol.name, "badges": result}
