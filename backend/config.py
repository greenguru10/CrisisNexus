"""
Application configuration module.
Loads ALL settings from the .env file — no secrets are hardcoded.
"""

import json
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded exclusively from environment variables / .env file.
    Sensitive values (DATABASE_URL) have no default — the app will fail fast
    if .env is missing, rather than silently using wrong credentials.
    """

    # Database — NO default, must be set in .env
    DATABASE_URL: str

    # Application
    APP_TITLE: str = "Smart Resource Allocation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # default to False (safe for production)

    # CORS — NO default, must be set in .env
    CORS_ORIGINS: str

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string to list."""
        return json.loads(self.CORS_ORIGINS)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

