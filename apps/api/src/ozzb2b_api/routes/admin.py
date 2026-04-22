"""Admin-only routes.

For now only exposes a trigger that enqueues a scraper task via Celery.
Protected by a simple role check (admin only).
"""

from __future__ import annotations

from typing import Annotated

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import User, UserRole
from ozzb2b_api.routes.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user


def _celery_client() -> Celery:
    cfg = get_settings()
    c = Celery("ozzb2b_scraper", broker=cfg.redis_url, backend=cfg.redis_url)
    return c


class ScrapeTriggerRequest(BaseModel):
    source_slug: str = Field(min_length=1, max_length=64)
    limit: int | None = Field(default=None, ge=1, le=1000)


class ScrapeTriggerResponse(BaseModel):
    task_id: str
    source_slug: str


@router.post(
    "/scrape",
    response_model=ScrapeTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_scrape(
    payload: ScrapeTriggerRequest,
    _admin: Annotated[User, Depends(_require_admin)],
) -> ScrapeTriggerResponse:
    c = _celery_client()
    result = c.send_task(
        "ozzb2b.scraper.crawl_source",
        args=[payload.source_slug, payload.limit],
    )
    return ScrapeTriggerResponse(task_id=result.id, source_slug=payload.source_slug)
