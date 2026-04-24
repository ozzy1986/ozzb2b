"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ozzb2b_api import __version__
from ozzb2b_api.clients.matcher import get_matcher_client, reset_matcher_client
from ozzb2b_api.clients.redis import get_redis
from ozzb2b_api.config import Settings, get_settings
from ozzb2b_api.db.session import get_engine
from ozzb2b_api.errors import DomainError
from ozzb2b_api.logging import configure_logging, get_logger
from ozzb2b_api.observability.metrics import PrometheusMiddleware, metrics_response
from ozzb2b_api.observability.security_headers import SecurityHeadersMiddleware
from ozzb2b_api.routes import admin, auth, catalog, chat, claims, health, search


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app. Accepts an explicit `settings` for tests."""
    cfg = settings or get_settings()
    configure_logging(cfg.log_level)
    log = get_logger("ozzb2b_api.app")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("api.start", env=cfg.env, version=__version__)
        yield
        log.info("api.stop")
        # Best-effort teardown: each step is wrapped so a slow/broken
        # dependency cannot wedge the shutdown signal. We log instead of
        # raising — the process is exiting anyway.
        try:
            await get_matcher_client(cfg).close()
            reset_matcher_client()
        except Exception as exc:  # pragma: no cover - best effort
            log.warning("api.shutdown.matcher_close_failed", err=str(exc))
        try:
            await get_redis().aclose()
        except Exception as exc:  # pragma: no cover - best effort
            log.warning("api.shutdown.redis_close_failed", err=str(exc))
        try:
            await get_engine().dispose()
        except Exception as exc:  # pragma: no cover - best effort
            log.warning("api.shutdown.engine_dispose_failed", err=str(exc))

    app = FastAPI(
        title="ozzb2b API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if not cfg.is_production else None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Metrics middleware must stay outermost (wrap-closest-to-request) so
    # every downstream error is still counted.
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.exception_handler(DomainError)
    async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        # `detail` is the stable, machine-readable English contract; the
        # frontend translates it via humanizeError(). Logging keeps the
        # exception class name so prod logs stay greppable per error type.
        log.info(
            "api.domain_error",
            error_type=type(exc).__name__,
            detail=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc)},
        )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(catalog.router)
    app.include_router(search.router)
    app.include_router(admin.router)
    app.include_router(chat.router)
    app.include_router(claims.router)

    @app.get("/metrics", include_in_schema=False)
    def _metrics() -> object:
        return metrics_response()

    return app


app = create_app()
