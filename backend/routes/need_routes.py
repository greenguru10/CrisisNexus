"""
Need routes – Upload reports and list needs.
Updated: tags ngo_id on created needs; adds Admin-push and NGO accept/reject endpoints.
"""

import logging
import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models.need import Need, UrgencyLevel, NeedStatus
from models.ngo import NGO, NgoStatus
from models.user import User, UserRole
from schemas.need_schema import ReportUpload, NeedResponse
from services.nlp_service import extract_from_text_async
from services.priority_service import compute_priority_score
from dependencies.auth_dependency import get_current_user, get_current_admin, get_current_ngo_coordinator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Needs"])


# ── File text extraction helpers ─────────────────────────────────

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(p.extract_text() for p in reader.pages if p.extract_text())
    except ImportError:
        raise HTTPException(status_code=500, detail="PyPDF2 not installed. Run: pip install PyPDF2")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")


def _extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise HTTPException(status_code=500, detail="python-docx not installed.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read DOCX: {e}")


async def _process_and_store_need(raw_text: str, db: Session, ngo_id: Optional[int] = None) -> Need:
    """Shared NLP pipeline → priority → DB. Accepts optional ngo_id for scoping."""
    from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus

    extracted = await extract_from_text_async(raw_text)

    categories = extracted.get("categories", ["general"]) or ["general"]
    category_str = ", ".join(categories)

    priority = compute_priority_score(
        urgency=extracted["urgency"],
        people_affected=extracted["people_affected"],
        category=category_str,
    )

    need = Need(
        raw_text=raw_text,
        category=category_str,
        urgency=UrgencyLevel(extracted["urgency"]),
        people_affected=extracted["people_affected"],
        location=extracted.get("location"),
        latitude=extracted.get("latitude"),
        longitude=extracted.get("longitude"),
        priority_score=priority,
        status=NeedStatus.PENDING,
    )
    db.add(need)
    db.flush()  # get need.id without committing

    # Tag need to owning NGO via junction table
    if ngo_id:
        db.add(NeedNGOAssignment(
            need_id=need.id,
            ngo_id=ngo_id,
            status=NgoAssignStatus.ACCEPTED,
        ))

    db.commit()
    db.refresh(need)

    logger.info(
        "Created need id=%d category=%s urgency=%s people=%d ngo_id=%s priority=%.2f",
        need.id, need.category, need.urgency.value, need.people_affected,
        ngo_id, need.priority_score,
    )
    return need


# ── Upload endpoints ─────────────────────────────────────────────

@router.post("/upload-report", response_model=NeedResponse, status_code=201)
async def upload_report(
    payload: ReportUpload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept a raw survey report as text, process through hybrid NLP pipeline.
    Automatically tags the need to the uploader's NGO (if NGO coordinator).
    """
    ngo_id = None
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if ngo:
            ngo_id = ngo.id

    need = await _process_and_store_need(payload.raw_text, db, ngo_id=ngo_id)
    background_tasks.add_task(_log_new_need, need.id, need.category)
    return need


@router.post("/upload-file", response_model=NeedResponse, status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload PDF/DOCX/TXT report — same NLP pipeline as upload-report."""
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ("pdf", "docx", "txt"):
        raise HTTPException(status_code=400, detail=f"Unsupported type '.{extension}'")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if extension == "pdf":
        raw_text = _extract_text_from_pdf(file_bytes)
    elif extension == "docx":
        raw_text = _extract_text_from_docx(file_bytes)
    else:
        raw_text = file_bytes.decode("utf-8", errors="ignore")

    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Could not extract enough text from file")

    ngo_id = None
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        if ngo:
            ngo_id = ngo.id

    need = await _process_and_store_need(raw_text, db, ngo_id=ngo_id)
    background_tasks.add_task(_log_new_need, need.id, need.category)
    return need


# ── List / Get needs ─────────────────────────────────────────────

@router.get("/needs", response_model=List[NeedResponse])
def list_needs(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    ngo_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List needs. NGO coordinators automatically see only their NGO's needs.
    Admin can optionally filter by ngo_id.
    """
    from models.volunteer import Volunteer

    # Scope NGO coordinator to their own needs
    scope_ngo_id = ngo_id
    if current_user.role == UserRole.NGO:
        ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
        scope_ngo_id = ngo.id if ngo else -1  # -1 returns nothing if no NGO found

    from models.need_ngo_assignment import NeedNGOAssignment
    from models.volunteer import Volunteer

    query = db.query(Need)
    if scope_ngo_id is not None:
        # Filter through the junction table instead of the dropped ngo_id column
        ngo_need_ids = [
            row.need_id for row in
            db.query(NeedNGOAssignment.need_id).filter(NeedNGOAssignment.ngo_id == scope_ngo_id).all()
        ]
        query = query.filter(Need.id.in_(ngo_need_ids))
    if status:
        query = query.filter(Need.status == status)
    if category:
        query = query.filter(Need.category == category)
    if urgency:
        query = query.filter(Need.urgency == urgency)

    needs = query.order_by(Need.priority_score.desc()).offset(skip).limit(limit).all()

    results = []
    for need in needs:
        data = NeedResponse.model_validate(need)
        # Populate assigned_volunteer_name if someone is assigned
        vol_id = need.assigned_volunteer_id
        if vol_id:
            vol = db.query(Volunteer).filter(Volunteer.id == vol_id).first()
            if vol:
                data.assigned_volunteer_name = vol.name
        results.append(data)
    return results


@router.get("/needs/{need_id}", response_model=NeedResponse)
def get_need(need_id: int, db: Session = Depends(get_db)):
    """Get a single need by ID."""
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail=f"Need {need_id} not found")
    return need


# ── Admin: Push task to a specific NGO ──────────────────────────

@router.post("/admin/needs/{need_id}/assign-to-ngo")
def admin_push_task_to_ngo(
    need_id: int,
    ngo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """[ADMIN] Assign/push an existing need to a specific NGO for handling."""
    from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus

    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")

    ngo = db.query(NGO).filter(NGO.id == ngo_id, NGO.status == NgoStatus.APPROVED).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="Approved NGO not found")

    # Upsert NeedNGOAssignment (PENDING awaiting coordinator acceptance)
    existing = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo_id).first()
    if not existing:
        db.add(NeedNGOAssignment(
            need_id=need_id, ngo_id=ngo_id,
            status=NgoAssignStatus.PENDING,
        ))
    elif existing.status == NgoAssignStatus.REJECTED:
        existing.status = NgoAssignStatus.PENDING

    need.assigned_by_admin = True
    need.ngo_accepted = None  # Reset flag (legacy field kept)
    db.commit()

    logger.info("Admin %s pushed need %d to NGO %d (%s)", current_user.email, need_id, ngo_id, ngo.name)
    return {"message": f"Need {need_id} assigned to NGO '{ngo.name}'. Awaiting coordinator acceptance."}


# ── NGO Coordinator: Accept/Reject admin-pushed task ────────────

@router.post("/needs/{need_id}/ngo-accept")
def ngo_accept_task(
    need_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] Accept a task that Admin pushed to this NGO."""
    from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus

    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    assignment = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo.id).first()
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need or not assignment:
        raise HTTPException(status_code=404, detail="Need not found for your NGO")
    if not need.assigned_by_admin:
        raise HTTPException(status_code=400, detail="This task was not pushed by Admin")

    assignment.status = NgoAssignStatus.ACCEPTED
    need.ngo_accepted = True
    db.commit()
    logger.info("NGO %s accepted task %d", ngo.name, need_id)
    return {"message": f"Task {need_id} accepted by {ngo.name}"}


@router.post("/needs/{need_id}/ngo-reject")
def ngo_reject_task(
    need_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """[NGO Coordinator] Reject a task pushed by Admin. Task returns to global pending."""
    from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus

    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    assignment = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo.id).first()
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need or not assignment:
        raise HTTPException(status_code=404, detail="Need not found for your NGO")

    assignment.status = NgoAssignStatus.REJECTED
    need.ngo_accepted = False
    need.assigned_by_admin = False
    need.status = NeedStatus.PENDING
    db.commit()
    logger.info("NGO %s rejected task %d — returned to global pending", ngo.name, need_id)
    return {"message": f"Task {need_id} rejected. Returned to Admin for re-assignment."}


# ── Background helper ────────────────────────────────────────────

def _log_new_need(need_id: int, category: str):
    logger.info("[BG] New need recorded: id=%d category=%s", need_id, category)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Multi-NGO assignment & volunteer assignment
# ═══════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel as _BM
from models.need_ngo_assignment import NeedNGOAssignment, NgoAssignStatus
from models.need_volunteer_assignment import NeedVolunteerAssignment
from models.task_trail import TrailAction
from services.trail_service import add_trail_entry


class AssignNgosIn(_BM):
    ngo_ids: List[int]
    note: Optional[str] = None


class AssignVolunteersIn(_BM):
    volunteer_ids: List[int]


# ── Admin: assign need to multiple NGOs ─────────────────────────
@router.post("/admin/needs/{need_id}/assign-to-ngos")
def assign_need_to_ngos(
    need_id: int,
    body: AssignNgosIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Admin assigns a need to one or more NGOs (parallel collaborative response)."""
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")
    if not body.ngo_ids:
        raise HTTPException(status_code=422, detail="Provide at least one ngo_id")

    # Get current assignments
    current_assignments = db.query(NeedNGOAssignment).filter(
        NeedNGOAssignment.need_id == need_id,
        NeedNGOAssignment.status != NgoAssignStatus.REJECTED
    ).all()
    
    current_ngo_ids = {a.ngo_id for a in current_assignments}
    new_ngo_ids = set(body.ngo_ids)
    
    # NGOs to remove: in current but NOT in new
    to_remove = current_ngo_ids - new_ngo_ids
    for ngo_id_to_rem in to_remove:
        a = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo_id_to_rem).first()
        if a:
            a.status = NgoAssignStatus.REJECTED # Mark as rejected/removed so consensus ignores them
            logger.info("Admin %s removed NGO %d from need %d during reassignment", current_user.email, ngo_id_to_rem, need_id)

    ngo_names = []
    for ngo_id in body.ngo_ids:
        ngo = db.query(NGO).filter(NGO.id == ngo_id, NGO.status == NgoStatus.APPROVED).first()
        if not ngo:
            raise HTTPException(status_code=404, detail=f"NGO {ngo_id} not found or not approved")
        
        # Upsert assignment (idempotent)
        existing = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo_id).first()
        if not existing:
            db.add(NeedNGOAssignment(need_id=need_id, ngo_id=ngo_id, admin_note=body.note))
        elif existing.status == NgoAssignStatus.REJECTED:
            existing.status = NgoAssignStatus.PENDING # Bring back if it was removed
            
        ngo_names.append(ngo.name)

    # Update need
    need.assigned_by_admin = True
    need.status = NeedStatus.ASSIGNED if need.status == NeedStatus.PENDING else need.status

    add_trail_entry(
        db, need_id=need_id, action=TrailAction.ASSIGNED_TO_NGO,
        actor_id=current_user.id, actor_role="admin", actor_name=current_user.email,
        detail={"ngo_ids": body.ngo_ids, "ngo_names": ngo_names, "note": body.note or ""},
    )
    db.commit()
    return {"message": f"Need {need_id} assigned to {len(body.ngo_ids)} NGO(s)", "ngo_names": ngo_names}


# ── GET NGO-assigned needs list (for NGO dashboard) ─────────────
@router.get("/ngo/needs/assigned")
def get_assigned_needs_for_ngo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """Returns all needs assigned to the current NGO coordinator's NGO."""
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    assignments = (
        db.query(NeedNGOAssignment)
        .filter(NeedNGOAssignment.ngo_id == ngo.id)
        .all()
    )
    need_ids = [a.need_id for a in assignments]
    status_map = {a.need_id: a.status.value for a in assignments}

    needs = db.query(Need).filter(Need.id.in_(need_ids)).all() if need_ids else []
    result = []
    for n in needs:
        d = n.__dict__.copy()
        d.pop("_sa_instance_state", None)
        d["ngo_assignment_status"] = status_map.get(n.id)
        
        # Check for manual team assignments
        manual_count = db.query(NeedVolunteerAssignment).filter_by(
            need_id=n.id, ngo_id=ngo.id, is_active=True
        ).count()
        d["has_manual_assignments"] = manual_count > 0
        
        result.append(d)
    return result


# ── NGO: accept assigned need ────────────────────────────────────
@router.post("/ngo/needs/{need_id}/accept-assignment")
def ngo_accept_assignment(
    need_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    assignment = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo.id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="No assignment found for your NGO")

    from datetime import datetime, timezone
    assignment.status = NgoAssignStatus.ACCEPTED
    assignment.resolved_at = datetime.now(timezone.utc)

    add_trail_entry(
        db, need_id=need_id, action=TrailAction.NGO_ACCEPTED,
        actor_id=current_user.id, actor_role="ngo", actor_name=ngo.name,
        detail={"ngo_id": ngo.id, "ngo_name": ngo.name},
    )
    db.commit()
    return {"message": "Assignment accepted"}


# ── NGO: reject assigned need ────────────────────────────────────
@router.post("/ngo/needs/{need_id}/reject-assignment")
def ngo_reject_assignment(
    need_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()
    assignment = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo.id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="No assignment found for your NGO")

    from datetime import datetime, timezone
    assignment.status = NgoAssignStatus.REJECTED
    assignment.resolved_at = datetime.now(timezone.utc)

    add_trail_entry(
        db, need_id=need_id, action=TrailAction.NGO_REJECTED,
        actor_id=current_user.id, actor_role="ngo", actor_name=ngo.name,
        detail={"ngo_id": ngo.id, "ngo_name": ngo.name},
    )
    db.commit()
    return {"message": "Assignment rejected"}


# ── NGO: assign multiple volunteers to a need ────────────────────
@router.post("/ngo/needs/{need_id}/assign-volunteers")
def ngo_assign_volunteers(
    need_id: int,
    body: AssignVolunteersIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_ngo_coordinator),
):
    """NGO manually assigns one or more volunteers to an accepted need (team assignment)."""
    from models.volunteer import Volunteer
    ngo = db.query(NGO).filter(NGO.coordinator_user_id == current_user.id).first()

    # Must be accepted by this NGO
    assignment = db.query(NeedNGOAssignment).filter_by(need_id=need_id, ngo_id=ngo.id, status="accepted").first()
    if not assignment:
        raise HTTPException(status_code=400, detail="Accept the task first before assigning volunteers")
    if assignment.is_completed:
        raise HTTPException(status_code=400, detail="Your NGO has already completed this task")

    need = db.query(Need).filter(Need.id == need_id).first()
    if need and need.status == NeedStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot assign volunteers to a completed task")

    volunteer_names = []
    for vol_id in body.volunteer_ids:
        vol = db.query(Volunteer).filter(Volunteer.id == vol_id, Volunteer.ngo_id == ngo.id).first()
        if not vol:
            continue
        exists = db.query(NeedVolunteerAssignment).filter_by(
            need_id=need_id, volunteer_id=vol_id, ngo_id=ngo.id, is_active=True
        ).first()
        if not exists:
            db.add(NeedVolunteerAssignment(
                need_id=need_id, volunteer_id=vol_id, ngo_id=ngo.id,
                assigned_by_id=current_user.id,
            ))
        vol.availability = False
        volunteer_names.append(vol.name or f"Vol#{vol_id}")

    add_trail_entry(
        db, need_id=need_id, action=TrailAction.VOLUNTEER_ASSIGNED,
        actor_id=current_user.id, actor_role="ngo", actor_name=ngo.name,
        detail={"volunteer_ids": body.volunteer_ids, "volunteer_names": volunteer_names, "ngo_name": ngo.name},
    )

    if need and need.status == NeedStatus.PENDING:
        need.status = NeedStatus.ASSIGNED
    db.commit()
    return {"message": f"{len(volunteer_names)} volunteer(s) assigned", "names": volunteer_names}


# ── GET per-need NGO assignment summary (for trail / admin view) ─
@router.get("/admin/needs/{need_id}/assignments")
def get_need_assignments(
    need_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Returns the NGO assignment records + volunteer assignments for a need."""
    ngo_assignments = db.query(NeedNGOAssignment).filter_by(need_id=need_id).all()
    vol_assignments = db.query(NeedVolunteerAssignment).filter_by(need_id=need_id, is_active=True).all()

    from models.volunteer import Volunteer
    result_ngos = []
    for a in ngo_assignments:
        ngo = db.query(NGO).filter(NGO.id == a.ngo_id).first()
        result_ngos.append({
            "ngo_id": a.ngo_id, "ngo_name": ngo.name if ngo else "?",
            "status": a.status.value, "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
        })
    result_vols = []
    for v in vol_assignments:
        vol = db.query(Volunteer).filter(Volunteer.id == v.volunteer_id).first()
        ngo = db.query(NGO).filter(NGO.id == v.ngo_id).first()
        result_vols.append({
            "volunteer_id": v.volunteer_id, "name": vol.name if vol else "?",
            "ngo_name": ngo.name if ngo else "?", "assigned_at": v.assigned_at.isoformat() if v.assigned_at else None,
        })
    return {"ngo_assignments": result_ngos, "volunteer_assignments": result_vols}

