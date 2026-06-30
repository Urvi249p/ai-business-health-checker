"""
settings.py — central config for the whole app.

Everything reads from .env (or environment variables).
Import these constants anywhere:

    from src.config.settings import settings
    print(settings.PORT)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class Settings:
    # ── Server ──────────────────────────────────────────────
    PORT: int = int(os.getenv("PORT", "8000"))

    # ── OpenAI ──────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")

    # ── Database ─────────────────────────────────────────────
    # PostgreSQL connection URL
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/business_audit"
    )

    # ── File storage ─────────────────────────────────────────
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp_reports")

    # ── Logging ──────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── Authentication ───────────────────────────────────────
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # ── 2FA ──────────────────────────────────────────────────
    TOTP_ISSUER: str = os.getenv("TOTP_ISSUER", "BusinessAuditAPI")
    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "5"))

    def validate(self) -> None:
        """
        Called once at startup. Raises if required values are missing.
        """
        if not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Copy .env.example to .env and add your key."
            )

        if self.JWT_SECRET_KEY == "change-this-secret":
            import warnings
            warnings.warn(
                "JWT_SECRET_KEY is using the default value. "
                "Set a real secret in .env"
            )


# Single shared instance — import this everywhere
settings = Settings()