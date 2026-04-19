"""
Need routes – Upload reports and list needs.
Supports both raw text and file uploads (PDF, DOCX, TXT).
"""

import logging
import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models.need import Need, UrgencyLevel, NeedStatus
from schemas.need_schema import ReportUpload, NeedResponse
from services.nlp_service import extract_from_text
from services.priority_service import compute_priority_score
from utils.location_utils import geocode_location

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Needs"])


# ── Helpers for text extraction from files ───────────────────────

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PyPDF2 is not installed. Run: pip install PyPDF2"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="python-docx is not installed. Run: pip install python-docx"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read DOCX: {str(e)}")


def _process_and_store_need(raw_text: str, db: Session) -> Need:
    """Shared logic: NLP → priority → store in DB."""
    # 1. NLP extraction
    extracted = extract_from_text(raw_text)

    # 2. Geocode location if possible
    lat, lon = geocode_location(extracted.get("location"))

    # 3. Compute priority score
    priority = compute_priority_score(
        urgency=extracted["urgency"],
        people_affected=extracted["people_affected"],
        category=extracted["category"],
    )

    # 4. Persist to database
    need = Need(
        raw_text=raw_text,
        category=extracted["category"],
        urgency=UrgencyLevel(extracted["urgency"]),
        people_affected=extracted["people_affected"],
        location=extracted.get("location"),
        latitude=lat,
        longitude=lon,
        priority_score=priority,
        status=NeedStatus.PENDING,
    )
    db.add(need)
    db.commit()
    db.refresh(need)

    logger.info("Created need id=%d category=%s priority=%.2f", need.id, need.category, need.priority_score)
    return need


# ── Endpoints ────────────────────────────────────────────────────

@router.post("/upload-report", response_model=NeedResponse, status_code=201)
def upload_report(
    payload: ReportUpload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Accept a raw NGO survey report as **text**, process it through the NLP pipeline,
    compute priority score, and store the structured need.

    **Sample request body:**
    ```json
    {
        "raw_text": "Urgent: 200 families in Kathmandu need clean drinking water and medical supplies immediately."
    }
    ```
    """
    need = _process_and_store_need(payload.raw_text, db)
    background_tasks.add_task(_log_new_need, need.id, need.category)
    return need


@router.post("/upload-file", response_model=NeedResponse, status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Upload a PDF, DOCX, or TXT report file"),
    db: Session = Depends(get_db),
):
    """
    Upload an NGO survey report as a **file** (PDF, DOCX, or TXT).
    The text is extracted from the file, then processed through the NLP pipeline.

    **Supported formats:** `.pdf`, `.docx`, `.txt`
    """
    # Validate file type
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ("pdf", "docx", "txt"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{extension}'. Accepted: .pdf, .docx, .txt"
        )

    # Read file bytes
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Extract text based on file type
    if extension == "pdf":
        raw_text = _extract_text_from_pdf(file_bytes)
    elif extension == "docx":
        raw_text = _extract_text_from_docx(file_bytes)
    else:  # txt
        raw_text = file_bytes.decode("utf-8", errors="ignore")

    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Could not extract enough text from the file")

    logger.info("Extracted %d characters from '%s'", len(raw_text), filename)

    need = _process_and_store_need(raw_text, db)
    background_tasks.add_task(_log_new_need, need.id, need.category)
    return need


@router.get("/needs", response_model=List[NeedResponse])
def list_needs(
    status: Optional[str] = Query(None, description="Filter by status: pending, assigned, completed"),
    category: Optional[str] = Query(None, description="Filter by category"),
    urgency: Optional[str] = Query(None, description="Filter by urgency: low, medium, high"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """
    List all needs with optional filters.
    Sorted by priority_score descending (highest priority first).
    """
    from models.volunteer import Volunteer

    query = db.query(Need)

    if status:
        query = query.filter(Need.status == status)
    if category:
        query = query.filter(Need.category == category)
    if urgency:
        query = query.filter(Need.urgency == urgency)

    needs = query.order_by(Need.priority_score.desc()).offset(skip).limit(limit).all()

    # Enrich with volunteer names
    results = []
    for need in needs:
        data = NeedResponse.model_validate(need)
        if need.assigned_volunteer_id:
            vol = db.query(Volunteer).filter(Volunteer.id == need.assigned_volunteer_id).first()
            if vol:
                data.assigned_volunteer_name = vol.name
        results.append(data)

    return results


@router.get("/needs/{need_id}", response_model=NeedResponse)
def get_need(need_id: int, db: Session = Depends(get_db)):
    """Get a single need by ID."""
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail=f"Need with id {need_id} not found")
    return need


# ── Background task helper ───────────────────────────────────────

def _log_new_need(need_id: int, category: str):
    """Background task to log need creation (extendable for notifications)."""
    logger.info("[BG] New need recorded: id=%d category=%s", need_id, category)

