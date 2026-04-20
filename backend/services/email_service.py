"""
Email Service – Send emails via SMTP using FastAPI-Mail.

Features:
  - Volunteer assignment notifications
  - Registration welcome emails
  - Generic send_email() helper

Gracefully degrades if email is not configured in .env.
"""

import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# ── Lazy-loaded mail config ──────────────────────────────────────

_mail_connection = None


def _get_mail():
    """Lazy-initialize FastAPI-Mail connection."""
    global _mail_connection
    if _mail_connection is not None:
        return _mail_connection

    if not settings.email_configured:
        logger.warning("Email not configured — EMAIL_USERNAME / EMAIL_PASSWORD missing in .env")
        return None

    try:
        from fastapi_mail import FastMail, ConnectionConfig

        conf = ConnectionConfig(
            MAIL_USERNAME=settings.EMAIL_USERNAME,
            MAIL_PASSWORD=settings.EMAIL_PASSWORD,
            MAIL_FROM=settings.EMAIL_FROM or settings.EMAIL_USERNAME,
            MAIL_PORT=settings.EMAIL_PORT,
            MAIL_SERVER=settings.EMAIL_HOST,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
        _mail_connection = FastMail(conf)
        return _mail_connection
    except Exception as e:
        logger.error("Failed to initialize email: %s", e)
        return None


# ── Public API ───────────────────────────────────────────────────

async def send_email(to: str, subject: str, body: str) -> bool:
    """
    Send an email. Returns True if sent, False if email is not configured or fails.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: HTML email body.
    """
    fm = _get_mail()
    if fm is None:
        logger.info("[EMAIL SKIPPED] To: %s | Subject: %s (email not configured)", to, subject)
        return False

    try:
        from fastapi_mail import MessageSchema, MessageType

        message = MessageSchema(
            subject=subject,
            recipients=[to],
            body=body,
            subtype=MessageType.html,
        )
        await fm.send_message(message)
        logger.info("[EMAIL SENT] To: %s | Subject: %s", to, subject)
        return True
    except Exception as e:
        logger.error("[EMAIL FAILED] To: %s | Error: %s", to, e)
        return False


async def send_assignment_email(
    volunteer_email: str,
    volunteer_name: str,
    category: str,
    location: Optional[str],
    priority_score: float,
) -> bool:
    """Send notification when a volunteer is assigned to a need."""
    subject = f"🚨 New Assignment: {category.title()} Need in {location or 'Unknown Location'}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Hello {volunteer_name},</h2>
        <p>You have been assigned to a new task:</p>
        <table style="border-collapse: collapse; width: 100%; max-width: 400px;">
            <tr><td style="padding: 8px; font-weight: bold;">Category:</td><td style="padding: 8px;">{category.title()}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Location:</td><td style="padding: 8px;">{location or 'N/A'}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Priority Score:</td><td style="padding: 8px;">{priority_score}/100</td></tr>
        </table>
        <p style="margin-top: 20px;">Please check the dashboard for full details.</p>
        <p>Thank you for your service!<br>— CommunitySync Team</p>
    </body>
    </html>
    """
    return await send_email(volunteer_email, subject, body)


async def send_welcome_email(email: str, role: str) -> bool:
    """Send welcome email after registration."""
    subject = "🎉 Welcome to CommunitySync!"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Welcome to CommunitySync!</h2>
        <p>Your account has been created successfully.</p>
        <p><strong>Role:</strong> {role.title()}</p>
        <p>You can now log in and start using the platform.</p>
        <p>— CommunitySync Team</p>
    </body>
    </html>
    """
    return await send_email(email, subject, body)

async def send_password_reset_email(email: str, token: str) -> bool:
    """Send link to reset password."""
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    subject = "🔒 Reset Your Password"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Password Reset Request</h2>
        <p>You requested to reset your password. Click the link below to set a new password:</p>
        <p><a href="{reset_link}" style="display:inline-block; padding:10px 20px; background-color:#2563eb; color:white; text-decoration:none; border-radius:5px;">Reset Password</a></p>
        <p>If you did not request this, please ignore this email. The link expires in 15 minutes.</p>
        <p>— CommunitySync Team</p>
    </body>
    </html>
    """
    return await send_email(email, subject, body)

async def send_admin_created_volunteer_email(email: str, temp_password: str) -> bool:
    """Send welcome email with generated password for admin-created volunteers."""
    login_link = "http://localhost:3000/login"
    subject = "👋 Welcome to CommunitySync (Action Required)"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Welcome to CommunitySync!</h2>
        <p>An administrator has created a volunteer account for you.</p>
        <p><strong>Your Email:</strong> {email}</p>
        <p><strong>Temporary Password:</strong> <code>{temp_password}</code></p>
        <p>Click the link below to log in, and <b>please update your password and other details</b> in your Profile settings immediately.</p>
        <p><a href="{login_link}" style="display:inline-block; padding:10px 20px; background-color:#2563eb; color:white; text-decoration:none; border-radius:5px;">Log In Now</a></p>
        <p>— CommunitySync Team</p>
    </body>
    </html>
    """
    return await send_email(email, subject, body)


async def send_onboarding_email(name: str, email: str) -> bool:
    """Send WhatsApp onboarding instructions when a new volunteer is created."""
    # Pull dynamic values from config
    twilio_phone = settings.TWILIO_PHONE.replace("whatsapp:", "")
    join_code = settings.TWILIO_JOIN_CODE

    subject = "📲 Activate WhatsApp Alerts – CommunitySync"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #2563eb;">Hello {name},</h2>
        <p>You have been successfully registered as a volunteer on <strong>CommunitySync</strong>.</p>

        <p>To receive <strong>real-time task updates via WhatsApp</strong>, please follow these steps:</p>

        <div style="background: #f0f9ff; border-left: 4px solid #2563eb; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0 0 8px 0;"><strong>Step 1:</strong> Open WhatsApp on your phone</p>
            <p style="margin: 0 0 8px 0;"><strong>Step 2:</strong> Send the following message:</p>
            <p style="margin: 0 0 8px 0; padding: 8px 16px; background: #dbeafe; border-radius: 4px; font-family: monospace; font-size: 16px; display: inline-block;">
                join {join_code}
            </p>
            <p style="margin: 8px 0 0 0;"><strong>Step 3:</strong> Send it to: <code style="font-size: 15px; background: #dbeafe; padding: 2px 8px; border-radius: 4px;">{twilio_phone}</code></p>
        </div>

        <p>Once completed, you will start receiving task notifications instantly. ✅</p>
        <p style="color: #6b7280; font-size: 13px;"><em>Note: This is a one-time setup. You only need to do this once.</em></p>

        <br/>
        <p>Thank you for your service!<br/>— <strong>CommunitySync Team</strong></p>
    </body>
    </html>
    """
    return await send_email(email, subject, body)


async def send_volunteer_welcome_email(name: str, email: str) -> bool:
    """
    Send welcome email after a volunteer's account is approved by admin.
    This is different from the generic registration welcome — it confirms
    that the volunteer is now active and will start receiving tasks.
    """
    subject = "Welcome to CommunitySync"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #2563eb;">Hello {name},</h2>
        <p>Welcome to <strong>CommunitySync</strong>!</p>
        <p>You are now an <strong>active volunteer</strong> and will start receiving tasks.</p>

        <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0;">Your account has been reviewed and approved. You can now log in and access the platform.</p>
        </div>

        <p>
            <a href="http://localhost:3000/login"
               style="display:inline-block; padding:10px 20px; background-color:#2563eb; color:white; text-decoration:none; border-radius:5px;">
                Log In Now
            </a>
        </p>

        <br/>
        <p>Thank you for your service!<br/>— <strong>CommunitySync Team</strong></p>
    </body>
    </html>
    """
    return await send_email(email, subject, body)

