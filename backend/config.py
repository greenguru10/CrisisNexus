"""
Application configuration module.
Loads ALL settings from the .env file — no secrets are hardcoded.
"""

import json
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """
    Application settings loaded exclusively from environment variables / .env file.
    Sensitive values have no default — the app will fail fast
    if .env is missing, rather than silently using wrong credentials.
    """

    # Database — NO default, must be set in .env
    DATABASE_URL: str

    # Application
    APP_TITLE: str
    APP_VERSION: str
    DEBUG: bool

    # CORS
    CORS_ORIGINS: str

    # ── JWT Authentication ───────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRY_MINUTES: int

    # ── Email (SMTP via FastAPI-Mail) ────────────────────────────
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_FROM: str | None = None

    # ── Twilio WhatsApp ──────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE: str
    TWILIO_JOIN_CODE: str = "store-creature"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string to list."""
        return json.loads(self.CORS_ORIGINS)

    @property
    def email_configured(self) -> bool:
        return bool(self.EMAIL_USERNAME and self.EMAIL_PASSWORD)

    @property
    def twilio_configured(self) -> bool:
        return bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN and self.TWILIO_PHONE)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

