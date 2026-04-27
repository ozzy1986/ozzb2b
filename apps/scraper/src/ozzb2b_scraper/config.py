"""Scraper configuration."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OZZB2B_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development")

    database_url: str = Field(
        default="postgresql+asyncpg://ozzb2b:ozzb2b_dev_password@localhost:5433/ozzb2b"
    )
    redis_url: str = Field(default="redis://localhost:6380/0")

    user_agent: str = Field(
        default="ozzb2b-scraper/0.1 (+https://ozzb2b.com; contact: hello@ozzb2b.com)",
        description="HTTP User-Agent used for all scraping requests. Must identify us clearly.",
    )
    request_timeout_s: float = Field(default=30.0)
    rate_limit_per_host_rps: float = Field(default=0.5, description="Max requests/sec per host.")
    concurrent_requests: int = Field(default=2, description="Parallel requests cap.")
    max_response_bytes: int = Field(
        default=2 * 1024 * 1024,
        description=(
            "Hard cap on a single response body. Streamed reads abort once "
            "exceeded so a malicious or broken host cannot OOM the worker."
        ),
    )
    max_redirects: int = Field(
        default=5,
        description="Maximum redirect hops per request before giving up.",
    )
    robots_strict: bool = Field(
        default=False,
        description=(
            "When true, robots.txt fetch failures fail closed (no fetch). "
            "Default is fail-open to keep crawling resilient."
        ),
    )
    fns_sme_data_path: str | None = Field(
        default=None,
        description="Local path to an official FNS SME registry XML/ZIP dump or prepared JSONL.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
