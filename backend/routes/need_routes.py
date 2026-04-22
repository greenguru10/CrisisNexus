"""
Need routes – Upload reports and list needs.
Supports both raw text and file uploads (PDF, DOCX, TXT).
Uses the ASYNC hybrid NLP pipeline (Rule-based + Groq LLM + OpenCage geocoding).
"""

import logging
import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models.need import Need, UrgencyLevel, NeedStatus
from schemas.need_schema import ReportUpload, NeedResponse
from services.nlp_service import extract_from_text_async
from services.priority_service import compute_priority_score
from services.validation_service import validate_report

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


async def _process_and_store_need(raw_text: str, db: Session) -> Need:
    """
    Shared logic: Validation gate → Hybrid NLP pipeline → priority → store in DB.
    """
    # ── Step 0: Validate that the text is a real community report ──
    validation = await validate_report(raw_text)
    if validation["status"] == "INVALID":
        logger.warning(
            "Report rejected by validation gate: confidence=%d reason='%s'",
            validation["confidence"], validation["reason"],
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Invalid report",
                "message": f"{validation['reason']} (Extracted text: '{raw_text[:150]}...')",
                "confidence": validation["confidence"],
            },
        )

    # ── Step 1: Hybrid NLP pipeline (UNTOUCHED) ──
    extracted = await extract_from_text_async(raw_text)

    # Convert array of categories to comma-separated string
    categories = extracted.get("categories", ["general"])
    if not categories:
        categories = ["general"]
    
    category_str = ", ".join(categories)

    # 2. Compute priority score
    priority = compute_priority_score(
        urgency=extracted["urgency"],
        people_affected=extracted["people_affected"],
        category=category_str,
    )

    # 3. Persist to database
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
    db.commit()
    db.refresh(need)

    logger.info(
        "Created need id=%d category=%s urgency=%s people=%d location=%s "
        "lat=%.4f lon=%.4f priority=%.2f confidence=%d",
        need.id, need.category, need.urgency.value, need.people_affected,
        need.location or "unknown",
        need.latitude or 0, need.longitude or 0,
        need.priority_score, extracted.get("confidence", 0),
    )

    return need


# ── Endpoints ────────────────────────────────────────────────────

@router.post("/upload-report", response_model=NeedResponse, status_code=201)
async def upload_report(
    payload: ReportUpload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Accept a raw NGO survey report as **text**, process it through the
    hybrid NLP pipeline (Rule-based + Groq LLM + Geocoding),
    compute priority score, and store the structured need.

    **Sample request body:**
    ```json
    {
        "raw_text": "Urgent: 200 families in Kathmandu need clean drinking water and medical supplies immediately."
    }
    ```

    **Pipeline:**
    1. Preprocessing (slang expansion, cleanup)
    2. Summarization (for long text)
    3. Rule-based extraction (category, urgency, people count)
    4. Groq LLM extraction (structured JSON)
    5. Location extraction (LLM + spaCy NER + city fallback)
    6. OpenCage geocoding (lat/lon)
    7. Merge + fallback defaults
    """
    need = await _process_and_store_need(payload.raw_text, db)
    background_tasks.add_task(_log_new_need, need.id, need.category)
    return need


@router.post("/upload-file", response_model=NeedResponse, status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Upload a PDF, DOCX, TXT, or image report file"),
    db: Session = Depends(get_db),
):
    """
    Upload an NGO survey report as a **file**.
    The text is extracted from the file, then processed through the hybrid NLP pipeline.

    **Supported formats:** `.pdf`, `.docx`, `.txt`, `.jpg`, `.jpeg`, `.png`

    For images and scanned PDFs, Tesseract OCR is used to extract text.
    OCR is completely local – no LLM/Groq usage for text extraction.

    **Pipeline:**
    File → Text Extraction (+ OCR if needed) → Validation (Groq) → NLP (Groq)
    """
    from services.ocr_service import (
        SUPPORTED_IMAGE_EXTS,
        extract_text_from_image,
        extract_text_from_scanned_pdf,
        validate_file_size,
    )

    ACCEPTED_EXTS = {"pdf", "docx", "txt"} | SUPPORTED_IMAGE_EXTS

    # Validate file type
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ACCEPTED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{extension}'. Accepted: {', '.join(sorted(ACCEPTED_EXTS))}"
        )

    # Read file bytes
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Enforce file size limit
    try:
        validate_file_size(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ── Extract text based on file type ──────────────────────────
    raw_text = ""

    if extension in SUPPORTED_IMAGE_EXTS:
        # ── Image → OCR API ──
        try:
            raw_text = await extract_text_from_image(file_bytes, filename)
            logger.info("OCR extracted %d chars from image '%s'", len(raw_text), filename)
        except (RuntimeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))

    elif extension == "pdf":
        # ── PDF → try normal extraction first, OCR fallback ──
        raw_text = _extract_text_from_pdf(file_bytes)

        if not raw_text or len(raw_text.strip()) < 10:
            logger.info("PDF '%s' has no extractable text – falling back to OCR API", filename)
            try:
                raw_text = await extract_text_from_scanned_pdf(file_bytes, filename)
                logger.info("OCR fallback extracted %d chars from PDF '%s'", len(raw_text), filename)
            except (RuntimeError, ValueError) as e:
                raise HTTPException(status_code=400, detail=str(e))

    elif extension == "docx":
        raw_text = _extract_text_from_docx(file_bytes)

    else:  # txt
        raw_text = file_bytes.decode("utf-8", errors="ignore")

    # ── Validate extracted text ──────────────────────────────────
    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough text from the file. "
                   "For images, ensure the text is clearly visible."
        )

    logger.info("Extracted %d characters from '%s'", len(raw_text), filename)

    # ── Pass to existing validation → NLP pipeline (UNTOUCHED) ──
    need = await _process_and_store_need(raw_text, db)
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
