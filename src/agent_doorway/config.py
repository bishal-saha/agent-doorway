"""Typed configuration, read from DOORWAY_* environment variables (and an optional .env file)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every setting the gateway reads. Invalid values stop the app at startup."""

    # hide_input_in_errors: a bad value (e.g. a DSN missing +asyncpg) must not print its password.
    model_config = SettingsConfigDict(
        env_prefix="DOORWAY_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )

    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "postgresql+asyncpg://doorway:doorway@localhost:5432/doorway"
    redis_url: str = "redis://localhost:6379/0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    probe_timeout_seconds: float = Field(default=2.0, gt=0, le=30)

    @field_validator("database_url")
    @classmethod
    def _async_postgres_only(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must start with postgresql+asyncpg://")
        return value

    @field_validator("redis_url")
    @classmethod
    def _redis_scheme(cls, value: str) -> str:
        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("redis_url must start with redis:// or rediss://")
        return value


@lru_cache
def get_settings() -> Settings:
    """The process-wide settings, read once."""
    return Settings()
