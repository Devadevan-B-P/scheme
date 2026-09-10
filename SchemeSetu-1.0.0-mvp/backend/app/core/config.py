"""
Application configuration using pydantic-settings.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "SchemeSetu"
    PROJECT_NAME: str = "SchemeSetu API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database — PyMongo Async
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string",
    )
    MONGODB_DB_NAME: str = "schemesetu"

    # AI / LLM — env configurable, never hardcoded
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google AI Studio API key for Gemini",
    )
    GEMINI_MODEL: str = Field(
        default="gemini-3.8-flash",
        description="Gemini model identifier",
    )

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "*",
    ]

    # Cloud DLP (Tier 2 defense-in-depth, MockDlpClient by default in dev/tests)
    GOOGLE_CLOUD_PROJECT: str = Field(
        default="",
        description="GCP project ID for Cloud DLP",
    )
    DLP_ENABLED: bool = Field(
        default=False,
        description="Enable Cloud DLP second-pass sanitizer",
    )
    DLP_INTEGRATION_TESTS: bool = Field(
        default=False,
        description="Run real DLP integration tests with ADC",
    )
    DLP_TIMEOUT_SECONDS: float = Field(
        default=2.0,
        description="DLP API timeout in seconds",
    )

    # Rate Limiting
    RATE_LIMIT_CHAT_PER_SESSION: int = Field(
        default=60,
        description="Max chat requests per session per hour",
    )
    RATE_LIMIT_UPLOAD_PER_SESSION: int = Field(
        default=10,
        description="Max document uploads per session per hour",
    )

    # OCR Configuration
    OCR_CONFIRMATION_EXPIRY_MINUTES: int = Field(
        default=10,
        description="Minutes before a pending OCR confirmation token expires",
    )

    # Admin Seeding Endpoint (Disabled by default, CLI is primary)
    ENABLE_ADMIN_SEED_ENDPOINT: bool = Field(
        default=False,
        description="Allow invoking /api/v1/admin/seed with X-Admin-Key",
    )
    ADMIN_API_KEY: str = Field(
        default="",
        description="Shared secret required if ENABLE_ADMIN_SEED_ENDPOINT is True",
    )

    # Scraper Configuration
    FIRECRAWL_API_KEY: str = Field(
        default="",
        description="Firecrawl API key (optional; falls back to httpx if empty)",
    )


settings = Settings()
