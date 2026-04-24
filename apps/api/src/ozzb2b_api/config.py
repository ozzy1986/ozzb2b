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
    db_pool_size: int = Field(
        default=10,
        description=(
            "SQLAlchemy core pool size. Tune up on bigger VPS tiers; "
            "the API does mostly short OLTP-style transactions."
        ),
    )
    db_max_overflow: int = Field(
        default=10,
        description="Extra connections beyond `db_pool_size` allowed under burst.",
    )
    db_pool_recycle_seconds: int = Field(
        default=1800,
        description=(
            "Recycle pooled connections older than this. Prevents stale "
            "Postgres backends across long-lived workers."
        ),
    )

    redis_url: str = Field(default="redis://localhost:6380/0")
    redis_max_connections: int = Field(
        default=50,
        description="Per-process cap on the Redis connection pool.",
    )

    meilisearch_url: str = Field(default="http://localhost:7700")
    meilisearch_key: str = Field(default="ozzb2b_dev_master_key_change_me")

    matcher_enabled: bool = Field(
        default=False,
        description=(
            "When true the /search endpoint re-ranks Meilisearch hits via "
            "the Rust matcher."
        ),
    )
    matcher_grpc_addr: str = Field(
        default="matcher:9090",
        description="host:port of the matcher gRPC service.",
    )
    matcher_timeout_ms: int = Field(
        default=150,
        description="Hard deadline for a single matcher.Rank call.",
    )

    events_enabled: bool = Field(
        default=False,
        description="When true the API publishes product events to Redis Streams.",
    )
    events_stream_name: str = Field(default="ozzb2b:events:v1")
    events_stream_maxlen: int = Field(
        default=100_000,
        description="Approximate cap for the Redis Stream (XADD MAXLEN ~).",
    )

    clickhouse_url: str = Field(
        default="http://clickhouse:8123",
        description="Base URL of the ClickHouse HTTP interface.",
    )
    clickhouse_user: str = Field(default="default")
    clickhouse_password: str = Field(default="")
    clickhouse_database: str = Field(default="ozzb2b")
    clickhouse_timeout_ms: int = Field(default=2000)

    rate_limit_enabled: bool = Field(
        default=True,
        description="When true the auth endpoints are protected by a Redis fixed-window limiter.",
    )
    rate_limit_login_max: int = Field(default=10, description="Login attempts per window.")
    rate_limit_register_max: int = Field(default=5, description="Registrations per window.")
    rate_limit_refresh_max: int = Field(default=30, description="Token refreshes per window.")
    rate_limit_window_seconds: int = Field(default=300)
    rate_limit_search_max: int = Field(
        default=120,
        description="Public /search calls per window per IP (anti-scraping).",
    )
    rate_limit_claim_init_max: int = Field(
        default=10,
        description="claim-initiation requests per window per user/IP.",
    )
    rate_limit_claim_verify_max: int = Field(
        default=20,
        description="claim-verify (homepage fetch) requests per window per user.",
    )
    rate_limit_ws_token_max: int = Field(
        default=60,
        description="Chat ws-token issuance per window per user.",
    )
    rate_limit_logout_max: int = Field(
        default=30,
        description="Logout calls per window per IP.",
    )

    hsts_max_age_seconds: int = Field(default=15_552_000)

    jwt_secret: str = Field(default="please_change_me_in_every_env")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_ttl_seconds: int = Field(default=15 * 60)
    jwt_refresh_ttl_seconds: int = Field(default=30 * 24 * 60 * 60)
    jwt_issuer: str = Field(
        default="ozzb2b",
        description=(
            "JWT `iss` claim; verified on decode so a token issued for "
            "another service or by an attacker minting their own claims is "
            "rejected even if the secret is shared."
        ),
    )
    jwt_audience_api: str = Field(
        default="ozzb2b-api",
        description="JWT `aud` claim for HTTP access tokens.",
    )
    jwt_audience_ws_chat: str = Field(
        default="ozzb2b-ws-chat",
        description="JWT `aud` claim for the chat WebSocket handshake token.",
    )
    jwt_leeway_seconds: int = Field(
        default=5,
        description=(
            "Clock-skew leeway when verifying `exp`/`nbf`/`iat`. Keep small "
            "so a stolen short-lived token isn't usable for much longer "
            "than its declared expiry."
        ),
    )

    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed origins.",
    )

    trusted_proxy_count: int = Field(
        default=0,
        description=(
            "How many reverse-proxy hops to trust when reading "
            "`X-Forwarded-For`. 0 = ignore the header and use the socket "
            "peer (safe default for dev). On the production VPS Nginx adds "
            "exactly one hop, so set this to 1 in `.env.prod`."
        ),
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
