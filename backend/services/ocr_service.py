"""
OCR Service – Local EasyOCR text extraction for images and scanned PDFs.

Handles:
  * Direct images (JPG, JPEG, PNG, WEBP)
  * Scanned / image-based PDFs (fallback when PyPDF2 returns no text)

Design:
  * Uses local EasyOCR (PyTorch) instead of external APIs.
  * Uses PyMuPDF (fitz) to handle PDFs locally.
  * Applies advanced OpenCV image preprocessing before extraction.
  * Max file size enforced to prevent memory issues.
"""

import re
import io
import logging
import numpy as np
from typing import Optional

from services.image_preprocess import preprocess_image_for_ocr

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────

MAX_FILE_SIZE_MB = 10
MAX_IMAGE_DIMENSION = 3000   # px – resize larger images for speed
SUPPORTED_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}

# ── Lazy imports (avoid crash if optional deps missing) ──────────

_reader = None

def _get_easyocr_reader():
    """Lazy initialize EasyOCR reader."""
    global _reader
    if _reader is None:
        try:
            import easyocr
            # Initialize with English, use CPU to avoid CUDA dependency issues
            logger.info("Initializing EasyOCR models (may take a moment on first run)...")
            _reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR initialized successfully.")
        except ImportError:
            raise RuntimeError(
                "easyocr is not installed. Run: pip install easyocr"
            )
    return _reader


# ═══════════════════════════════════════════════════════════════════
# 1. TEXT CLEANING
# ═══════════════════════════════════════════════════════════════════

def _clean_ocr_text(raw: str) -> str:
    """Clean OCR output: collapse whitespace and remove isolated junk."""
    if not raw:
        return ""

    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip lines that are purely non-alphanumeric (OCR junk)
        if not re.search(r"[a-zA-Z0-9]", stripped):
            continue
        cleaned_lines.append(stripped)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_from_image_array(img_array: np.ndarray) -> str:
    """Helper to run EasyOCR on a numpy array image."""
    reader = _get_easyocr_reader()
    
    # EasyOCR returns list of strings when detail=0
    results = reader.readtext(img_array, detail=0)
    raw_text = "\n".join(results)
    return _clean_ocr_text(raw_text)


# ═══════════════════════════════════════════════════════════════════
# 2. IMAGE OCR
# ═══════════════════════════════════════════════════════════════════

async def extract_text_from_image(file_bytes: bytes, filename: str = "image.png") -> str:
    """
    Extract text from an image file using OpenCV preprocessing + EasyOCR.
    """
    try:
        # 1. Apply OpenCV preprocessing (resize, grayscale, threshold, blur)
        logger.info("Applying OpenCV preprocessing to image '%s'", filename)
        processed_bytes = preprocess_image_for_ocr(file_bytes)

        # 2. Convert processed bytes back to numpy array for EasyOCR
        # (EasyOCR expects standard BGR/RGB numpy arrays)
        np_arr = np.frombuffer(processed_bytes, np.uint8)
        import cv2
        img_array = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img_array is None:
             raise ValueError("Failed to decode preprocessed image.")

        # 3. Extract text using EasyOCR
        cleaned = _extract_from_image_array(img_array)
        
        # 4. Mandatory Quality Check
        word_count = len(cleaned.split())
        if word_count < 5:
            logger.warning("OCR Quality Check failed: Only %d words extracted.", word_count)
            raise ValueError("OCR_FAILED: Image quality too low")
            
        logger.info("OCR: Extracted %d characters from image", len(cleaned))
        print("\n\n================ EXTRACTED OCR TEXT ================")
        print(cleaned)
        print("====================================================\n\n")
        return cleaned

    except ValueError:
        raise
    except Exception as e:
        logger.error("OCR image extraction failed: %s", e)
        raise ValueError(f"Unable to extract text from image: {e}")


# ═══════════════════════════════════════════════════════════════════
# 3. PDF OCR (scanned / image-based PDFs)
# ═══════════════════════════════════════════════════════════════════

async def extract_text_from_scanned_pdf(file_bytes: bytes, filename: str = "document.pdf") -> str:
    """
    Extract text from a scanned / image-based PDF using PyMuPDF + OpenCV + EasyOCR.
    """
    try:
        import fitz  # PyMuPDF
        import cv2
        
        logger.info("OCR: converting scanned PDF pages to images via PyMuPDF…")
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        page_texts = []
        for i, page in enumerate(doc):
            # Render page to an image pixmap
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Convert to numpy array
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            
            # Handle grayscale or RGBA
            if pix.n == 4:
                img_array = img_array[:, :, :3]
            elif pix.n == 1:
                img_array = np.repeat(img_array, 3, axis=2)
                
            # Convert RGB to BGR for OpenCV
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Encode to PNG to pass through our preprocessing function
            success, encoded_pg = cv2.imencode('.png', img_array)
            if success:
                processed_pg_bytes = preprocess_image_for_ocr(encoded_pg.tobytes())
                np_arr = np.frombuffer(processed_pg_bytes, np.uint8)
                processed_img_array = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                page_text = _extract_from_image_array(processed_img_array)
                if page_text:
                    page_texts.append(page_text)
                logger.debug("OCR: page %d → %d chars", i + 1, len(page_text))
            
        doc.close()
        
        merged = "\n\n".join(page_texts)
        cleaned = _clean_ocr_text(merged)
        
        # Mandatory Quality Check
        word_count = len(cleaned.split())
        if word_count < 5:
            logger.warning("OCR Quality Check failed: Only %d words extracted from PDF.", word_count)
            raise ValueError("OCR_FAILED: Image quality too low")

        logger.info("OCR: total extracted %d characters from PDF", len(cleaned))
        print("\n\n================ EXTRACTED OCR TEXT ================")
        print(cleaned)
        print("====================================================\n\n")
        return cleaned

    except ImportError:
        raise RuntimeError("PyMuPDF is not installed. Run: pip install PyMuPDF")
    except ValueError:
        raise
    except Exception as e:
        logger.error("OCR PDF extraction failed: %s", e)
        raise ValueError(f"Unable to extract text from scanned PDF: {e}")


# ═══════════════════════════════════════════════════════════════════
# 4. FILE SIZE GUARD
# ═══════════════════════════════════════════════════════════════════

def validate_file_size(file_bytes: bytes, max_mb: float = MAX_FILE_SIZE_MB) -> None:
    """Raise ValueError if file exceeds size limit."""
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"File too large ({size_mb:.1f} MB). Maximum allowed: {max_mb} MB")
