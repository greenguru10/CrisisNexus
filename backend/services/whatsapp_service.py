"""
WhatsApp Service – Send WhatsApp messages via Twilio API.

Gracefully degrades if Twilio is not configured in .env.
"""

import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# ── Lazy-loaded Twilio client ────────────────────────────────────

_twilio_client = None


def _get_twilio_client():
    """Lazy-initialize Twilio client."""
    global _twilio_client
    if _twilio_client is not None:
        return _twilio_client

    if not settings.twilio_configured:
        logger.warning("Twilio not configured — TWILIO_ACCOUNT_SID / AUTH_TOKEN / PHONE missing in .env")
        return None

    try:
        from twilio.rest import Client
        _twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return _twilio_client
    except Exception as e:
        logger.error("Failed to initialize Twilio client: %s", e)
        return None


# ── Public API ───────────────────────────────────────────────────

def send_whatsapp(to_number: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.

    Args:
        to_number: Recipient phone number (e.g., '+919876543210').
        message: Text message to send.

    Returns:
        True if sent, False if not configured or failed.
    """
    client = _get_twilio_client()
    if client is None:
        logger.info("[WHATSAPP SKIPPED] To: %s | Message: %s (Twilio not configured)", to_number, message[:50])
        return False

    try:
        # Ensure WhatsApp prefix
        from_number = settings.TWILIO_PHONE
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number,
        )
        logger.info("[WHATSAPP SENT] To: %s | SID: %s", to_number, msg.sid)
        return True
    except Exception as e:
        logger.error("[WHATSAPP FAILED] To: %s | Error: %s", to_number, e)
        return False


def send_assignment_whatsapp(
    to_number: str,
    volunteer_name: str,
    category: str,
    location: Optional[str],
) -> bool:
    """Send WhatsApp notification when a volunteer is assigned."""
    message = (
        f"Hi {volunteer_name}! 🚨\n\n"
        f"You have been assigned a new task:\n"
        f"📋 Category: {category.title()}\n"
        f"📍 Location: {location or 'N/A'}\n\n"
        f"Please check the CommunitySync dashboard for full details.\n"
        f"Thank you for your service! 🙏"
    )
    return send_whatsapp(to_number, message)
