"""
LLM Service – Groq-powered extraction for the CommunitySync NLP pipeline.

Uses Groq's `llama3-8b-8192` model to extract structured data from
raw NGO survey/report text. Fully async with timeout fallback.
"""

import json
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# ── Lazy-init Groq client (avoids crash if key is blank) ─────────

_groq_client = None


def _get_groq_client():
    """Lazy-initialize the Groq client on first use."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    try:
        from config import settings
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("your_"):
            logger.warning("GROQ_API_KEY not configured – LLM extraction will be skipped.")
            return None

        from groq import Groq
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("Groq LLM client initialized (model: llama-3.1-8b-instant)")
        return _groq_client
    except ImportError:
        logger.warning("groq package not installed – run: pip install groq")
        return None
    except Exception as e:
        logger.error("Failed to initialize Groq client: %s", e)
        return None


# ── System prompt for structured extraction ──────────────────────

EXTRACTION_PROMPT = """You are a disaster relief data extraction AI.
From the following report text, extract these fields:

- categories: list of disaster relief categories detected (choose from: food, water, medical, shelter, clothing, sanitation, education, logistics, general). Return MULTIPLE if applicable.
- people_count: the estimated number of people affected (integer). If not clear, estimate based on context.
- urgency: the urgency level (low, medium, or high)
- description: a concise 1-2 line summary of the situation
- location_area: the specific area, neighbourhood, suburb, or locality mentioned (e.g. "Govandi", "Dharavi"). Return "" if not found.
- location_city: the city, town, or district mentioned (e.g. "Mumbai", "Delhi"). Return "" if not found.

IMPORTANT RULES:
1. Return ONLY valid JSON, no markdown, no backticks, no explanation.
2. If a field is unclear, make your best estimate.
3. For categories, always return a list even if only one category.
4. For location, extract the MOST COMPLETE location possible. Ignore noise words like 'near', 'maybe', 'around', 'side', 'area'.
5. If the location is given as "Area, City" (e.g., "Govandi, Mumbai"), extract "Govandi" as location_area and "Mumbai" as location_city. DO NOT drop the city or combine them into one field.
6. Do NOT hallucinate locations that are not mentioned or implied.

Return ONLY this JSON structure:
{"categories": [], "people_count": 0, "urgency": "", "description": "", "location_area": "", "location_city": ""}"""


# ── Public API ───────────────────────────────────────────────────

async def llm_extract(text: str, timeout: float = 15.0) -> Optional[dict]:
    """
    Send text to Groq LLM for structured extraction.

    Args:
        text: Preprocessed report text (can be summarized if long).
        timeout: Maximum seconds to wait for LLM response.

    Returns:
        Parsed dict with categories, people_count, urgency, description, location.
        Returns None if LLM call fails or times out.
    """
    client = _get_groq_client()
    if client is None:
        return None

    try:
        # Run synchronous Groq call in executor to stay async
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, _sync_groq_call, client, text
            ),
            timeout=timeout,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("Groq LLM call timed out after %.1fs – falling back to rule-based.", timeout)
        return None
    except Exception as e:
        logger.error("Groq extraction failed: %s", e)
        return None


def _sync_groq_call(client, text: str) -> Optional[dict]:
    """Synchronous Groq API call (run inside executor)."""
    try:
        # Truncate very long texts to fit context window
        if len(text) > 6000:
            text = text[:6000] + "..."

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        raw_content = response.choices[0].message.content.strip()
        logger.debug("Groq raw response: %s", raw_content[:300])

        # Clean up common LLM formatting issues
        cleaned = raw_content
        if cleaned.startswith("```"):
            # Remove markdown code fence
            cleaned = cleaned.strip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        parsed = json.loads(cleaned)

        # Validate structure
        if not isinstance(parsed, dict):
            logger.warning("LLM returned non-dict JSON: %s", type(parsed))
            return None

        logger.info(
            "LLM extraction successful: categories=%s, people=%s, urgency=%s, loc_area=%s, loc_city=%s",
            parsed.get("categories"), parsed.get("people_count"),
            parsed.get("urgency"), parsed.get("location_area"), parsed.get("location_city"),
        )
        return parsed

    except json.JSONDecodeError as e:
        logger.warning("LLM returned invalid JSON: %s – %s", e, raw_content[:200])
        return None
    except Exception as e:
        logger.error("Groq API call error: %s", e)
        return None
