"""
Trail routes — read the audit log for any need.
GET  /api/needs/{need_id}/trail   → list trail entries (admin, ngo, volunteer who is assigned)
POST /api/needs/{need_id}/trail/note → admin/ngo adds a free-text note
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from database import get_db
from models.task_trail import TaskTrail, TrailAction
from models.need import Need
from dependencies.auth_dependency import get_current_user, get_current_admin, get_current_ngo_coordinator
from services.trail_service import add_trail_entry

router = APIRouter(prefix="/api/needs", tags=["trail"])


# ── Pydantic schemas ─────────────────────────────────────────────────────────
class TrailEntryOut(BaseModel):
    id: int
    need_id: int
    actor_role: str
    actor_name: str | None
    action: str
    detail_json: dict | None
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_custom(cls, obj: TaskTrail):
        return cls(
            id=obj.id,
            need_id=obj.need_id,
            actor_role=obj.actor_role,
            actor_name=obj.actor_name,
            action=obj.action.value if hasattr(obj.action, 'value') else str(obj.action),
            detail_json=obj.detail_json or {},
            created_at=obj.created_at.isoformat() if obj.created_at else "",
        )


class NoteIn(BaseModel):
    note: str


# ── GET trail ────────────────────────────────────────────────────────────────
@router.get("/{need_id}/trail", response_model=List[TrailEntryOut])
def get_trail(
    need_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")

    entries = (
        db.query(TaskTrail)
        .filter(TaskTrail.need_id == need_id)
        .order_by(TaskTrail.created_at.asc())
        .all()
    )
    return [TrailEntryOut.from_orm_custom(e) for e in entries]


# ── POST note ────────────────────────────────────────────────────────────────
@router.post("/{need_id}/trail/note", response_model=TrailEntryOut)
def add_note(
    need_id: int,
    body: NoteIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from models.user import UserRole
    if current_user.role not in (UserRole.ADMIN, UserRole.NGO_COORDINATOR):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin or NGO Coordinator required")

    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")

    entry = add_trail_entry(
        db,
        need_id=need_id,
        action=TrailAction.STATUS_CHANGED,
        actor_id=current_user.id,
        actor_role=current_user.role.value,
        actor_name=current_user.email,
        detail={"note": body.note},
    )
    db.commit()
    db.refresh(entry)
    return TrailEntryOut.from_orm_custom(entry)

