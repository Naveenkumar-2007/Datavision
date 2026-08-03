"""
DataVision — Centralized Configuration Module
Uses Pydantic Settings v2 for type-safe, environment-driven configuration.

All settings are loaded from environment variables or .env files.
Required variables will raise validation errors on startup if missing.
"""

from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Environment ─────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False
    APP_NAME: str = "DataVision AI"
    APP_VERSION: str = "1.0.0"

    # ── Database ────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL async connection URL (postgresql+asyncpg://...)"
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # ── JWT Auth ────────────────────────────────────────────────────
    JWT_SECRET: str = Field(
        ...,
        description="Secret key for signing JWT tokens. Must be kept secret."
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Security ────────────────────────────────────────────────────
    CORS_ORIGINS: str = "*"
    ALLOWED_HOSTS: str = "*"
    BCRYPT_ROUNDS: int = 12

    # ── Redis (Optional) ────────────────────────────────────────────
    REDIS_URL: Optional[str] = None

    # ── LLM Providers ───────────────────────────────────────────────
    GROQ_API_KEY: Optional[str] = None
    GROQ_KEY_1: Optional[str] = None
    GROQ_KEY_2: Optional[str] = None
    GROQ_KEY_3: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None

    # ── Email ───────────────────────────────────────────────────────
    RESEND_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@datavision.ai"

    # ── OAuth ───────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS from comma-separated string to list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
