"""
Validation Service – Pre-pipeline report classifier.

A lightweight LLM gate that runs BEFORE the NLP extraction pipeline.
Determines whether the uploaded text is a genuine community problem
report.  If INVALID the request is rejected early, saving a full
pipeline invocation.

Design decisions:
  * Reuses the shared Groq client from llm_service (one init, one key).
  * Uses llama-3.1-8b-instant with temperature 0 for deterministic
    classification.
  * Fail-open: any timeout, parse error, or API failure defaults to
    VALID so real reports are never blocked during a demo.
  * Result caching via an LRU dict prevents duplicate LLM calls for
    the same text within a server lifetime.
"""

import json
import logging
import asyncio
import hashlib
from typing import Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

# ── Validation prompt ────────────────────────────────────────────

VALIDATION_PROMPT = """You are a strict classifier.

Determine whether the given text is a REAL community problem report.

DEFINITION:

VALID report:
- Describes real issues like food shortage, water problems, medical needs, shelter issues
- May mention people, urgency, or location

INVALID report:
- Notes, essays, pledges, personal writing, random content
- No actionable community issue

OUTPUT FORMAT (MANDATORY):
{"status": "VALID" or "INVALID", "confidence": 0-100, "reason": "short explanation"}

RULES:
- Be strict in classification
- Do NOT assume missing context
- If unclear → return INVALID
- Keep reason under 15 words
- Do NOT extract any additional fields
- Return ONLY JSON, no markdown, no backticks, no explanation"""


# ── LRU cache (bounded in-memory) ────────────────────────────────

_CACHE_MAX = 256
_validation_cache: OrderedDict[str, dict] = OrderedDict()


def _cache_key(text: str) -> str:
    """SHA-256 digest of the first 2000 chars (enough to identify unique reports)."""
    return hashlib.sha256(text[:2000].encode("utf-8", errors="ignore")).hexdigest()


def _cache_get(key: str) -> Optional[dict]:
    if key in _validation_cache:
        _validation_cache.move_to_end(key)
        return _validation_cache[key]
    return None


def _cache_set(key: str, value: dict) -> None:
    _validation_cache[key] = value
    if len(_validation_cache) > _CACHE_MAX:
        _validation_cache.popitem(last=False)


# ── Fail-open default ────────────────────────────────────────────

_VALID_DEFAULT = {"status": "VALID", "confidence": 50, "reason": "Validation skipped (fail-open)"}


# ── Synchronous Groq call (runs inside executor) ─────────────────

def _sync_validate_call(client, text: str) -> dict:
    """
    Blocking Groq API call for report classification.
    Returns a dict with status / confidence / reason.
    """
    try:
        # Only send a reasonable amount of text for classification
        truncated = text[:3000] if len(text) > 3000 else text

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": VALIDATION_PROMPT},
                {"role": "user", "content": truncated},
            ],
            temperature=0,
            max_tokens=150,
        )

        raw = response.choices[0].message.content.strip()
        logger.debug("Validation raw response: %s", raw[:200])

        # Clean markdown fences if present
        cleaned = raw
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        parsed = json.loads(cleaned)

        # Normalise status to uppercase
        status = str(parsed.get("status", "VALID")).upper().strip()
        if status not in ("VALID", "INVALID"):
            status = "VALID"

        result = {
            "status": status,
            "confidence": int(parsed.get("confidence", 50)),
            "reason": str(parsed.get("reason", ""))[:100],
        }

        logger.info(
            "Validation result: status=%s confidence=%d reason='%s'",
            result["status"], result["confidence"], result["reason"],
        )
        return result

    except json.JSONDecodeError as e:
        logger.warning("Validation LLM returned invalid JSON: %s – raw: %s", e, raw[:200])
        return _VALID_DEFAULT

    except Exception as e:
        logger.error("Validation Groq call error: %s", e)
        return _VALID_DEFAULT


# ── Public async API ─────────────────────────────────────────────

async def validate_report(text: str, timeout: float = 8.0) -> dict:
    """
    Classify whether *text* is a valid community report.

    Args:
        text:    Raw (or extracted) report text.
        timeout: Max seconds to wait for the LLM response.

    Returns:
        {
            "status":     "VALID" | "INVALID",
            "confidence": 0-100,
            "reason":     str
        }

    On ANY failure the function returns status=VALID (fail-open).
    """
    if not text or len(text.strip()) < 10:
        return {"status": "INVALID", "confidence": 95, "reason": "Text too short to be a report"}

    # ── Check cache ──
    key = _cache_key(text)
    cached = _cache_get(key)
    if cached is not None:
        logger.debug("Validation cache hit for key=%s", key[:12])
        return cached

    # ── Get shared Groq client ──
    from services.llm_service import _get_groq_client

    client = _get_groq_client()
    if client is None:
        logger.warning("Groq client unavailable – validation skipped (fail-open)")
        return _VALID_DEFAULT

    # ── Run LLM classification ──
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, _sync_validate_call, client, text
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.warning("Validation LLM timed out after %.1fs – defaulting to VALID", timeout)
        result = _VALID_DEFAULT
    except Exception as e:
        logger.error("Validation failed: %s – defaulting to VALID", e)
        result = _VALID_DEFAULT

    # ── Store in cache ──
    _cache_set(key, result)
    return result
