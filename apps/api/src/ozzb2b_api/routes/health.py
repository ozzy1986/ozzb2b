"""Liveness and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ozzb2b_api import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe: returns 200 as long as the process is running."""
    return HealthResponse(status="ok", service="ozzb2b-api", version=__version__)


@router.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    """Readiness probe placeholder. Will be expanded to verify DB/Redis/Meili connectivity."""
    return HealthResponse(status="ok", service="ozzb2b-api", version=__version__)
