"""
Trail service: helper used by all routes to append entries to task_trail.
Import and call `add_trail_entry(...)` after every significant action.
"""
from sqlalchemy.orm import Session
from models.task_trail import TaskTrail, TrailAction


def add_trail_entry(
    db: Session,
    *,
    need_id: int,
    action: TrailAction,
    actor_id: int | None = None,
    actor_role: str = "system",
    actor_name: str | None = None,
    detail: dict | None = None,
) -> TaskTrail:
    """Append one immutable trail entry. Caller must call db.commit()."""
    entry = TaskTrail(
        need_id=need_id,
        actor_id=actor_id,
        actor_role=actor_role,
        actor_name=actor_name or actor_role,
        action=action,
        detail_json=detail or {},
    )
    db.add(entry)
    return entry
