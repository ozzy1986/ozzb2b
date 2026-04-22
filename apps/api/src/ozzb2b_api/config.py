"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration. All fields are env-overridable with the OZZB2B_ prefix."""

    model_config = SettingsConfigDict(
        env_prefix="OZZB2B_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development", description="development | test | staging | production")

    database_url: str = Field(
        default="postgresql+asyncpg://ozzb2b:ozzb2b_dev_password@localhost:5433/ozzb2b"
    )
    database_echo: bool = Field(default=False)

    redis_url: str = Field(default="redis://localhost:6380/0")

    meilisearch_url: str = Field(default="http://localhost:7700")
    meilisearch_key: str = Field(default="ozzb2b_dev_master_key_change_me")

    jwt_secret: str = Field(default="please_change_me_in_every_env")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_ttl_seconds: int = Field(default=15 * 60)
    jwt_refresh_ttl_seconds: int = Field(default=30 * 24 * 60 * 60)

    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed origins.",
    )

    log_level: str = Field(default="INFO")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def is_test(self) -> bool:
        return self.env.lower() == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor to avoid re-parsing env on every call."""
    return Settings()
