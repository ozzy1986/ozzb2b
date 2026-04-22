"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ozzb2b_api import __version__
from ozzb2b_api.config import Settings, get_settings
from ozzb2b_api.logging import configure_logging, get_logger
from ozzb2b_api.routes import auth, catalog, health, search


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

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(catalog.router)
    app.include_router(search.router)

    return app


app = create_app()
