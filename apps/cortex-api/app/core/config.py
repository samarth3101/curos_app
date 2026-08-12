"""Cortex OI API — Application Configuration.

Uses pydantic-settings for 12-factor config.
Values are read from environment variables and .env files.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_name: str = "Cortex OI"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ---- API ----
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # ---- Database ----
    database_url: PostgresDsn

    # ---- Redis ----
    redis_url: RedisDsn

    # ---- Security / JWT ----
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ---- CORS ----
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Allow CORS origins as comma-separated string or list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        """Enforce production-specific constraints."""
        _insecure_keys = ("changeme", "changeme-generate-a-strong-random-key-for-production")
        if self.environment == "production":
            if self.secret_key in _insecure_keys:
                msg = "SECRET_KEY must be set to a secure value in production"
                raise ValueError(msg)
            if self.debug:
                msg = "DEBUG must be False in production"
                raise ValueError(msg)
        return self

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def database_url_str(self) -> str:
        return str(self.database_url)

    @property
    def redis_url_str(self) -> str:
        return str(self.redis_url)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings.

    Using lru_cache ensures settings are loaded once and reused.
    In tests, call get_settings.cache_clear() to reload.
    """
    return Settings()  # type: ignore[call-arg]
