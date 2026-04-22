"""Admin-only routes.

Protected by a simple role check (admin only).
"""

from __future__ import annotations

from typing import Annotated

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import ProviderClaim, User, UserRole
from ozzb2b_api.routes.deps import DbSession, get_current_user
from ozzb2b_api.schemas.claims import ClaimPublic, ClaimRejectRequest
from ozzb2b_api.services import analytics as analytics_service
from ozzb2b_api.services import claims as claims_service

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


class ScrapeAllTriggerRequest(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=1000)


class ScrapeAllTriggerResponse(BaseModel):
    task_id: str


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


@router.post(
    "/scrape/all",
    response_model=ScrapeAllTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_scrape_all(
    payload: ScrapeAllTriggerRequest,
    _admin: Annotated[User, Depends(_require_admin)],
) -> ScrapeAllTriggerResponse:
    c = _celery_client()
    result = c.send_task("ozzb2b.scraper.crawl_all", args=[payload.limit])
    return ScrapeAllTriggerResponse(task_id=result.id)


class AnalyticsSummaryItem(BaseModel):
    event_type: str
    count: int


class AnalyticsSummaryResponse(BaseModel):
    days: int
    items: list[AnalyticsSummaryItem]


class TopQueryItem(BaseModel):
    query: str
    count: int


class TopQueriesResponse(BaseModel):
    days: int
    items: list[TopQueryItem]


class TopProviderItem(BaseModel):
    provider_id: str
    display_name: str
    slug: str
    count: int


class TopProvidersResponse(BaseModel):
    days: int
    items: list[TopProviderItem]


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(
    _admin: Annotated[User, Depends(_require_admin)],
    days: Annotated[int, Query(ge=1, le=365)] = 7,
) -> AnalyticsSummaryResponse:
    rows = await analytics_service.event_type_counts(days=days)
    return AnalyticsSummaryResponse(
        days=days,
        items=[AnalyticsSummaryItem(event_type=r.event_type, count=r.count) for r in rows],
    )


@router.get("/analytics/top-searches", response_model=TopQueriesResponse)
async def analytics_top_searches(
    _admin: Annotated[User, Depends(_require_admin)],
    days: Annotated[int, Query(ge=1, le=365)] = 7,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
) -> TopQueriesResponse:
    rows = await analytics_service.top_searches(days=days, limit=limit)
    return TopQueriesResponse(
        days=days,
        items=[TopQueryItem(query=r.query, count=r.count) for r in rows],
    )


@router.get("/claims", response_model=list[ClaimPublic])
async def list_pending_claims_endpoint(
    db: DbSession,
    _admin: Annotated[User, Depends(_require_admin)],
) -> list[ClaimPublic]:
    rows = await claims_service.list_pending_claims(db)
    return [ClaimPublic.model_validate(r) for r in rows]


async def _load_claim_or_404(db: DbSession, claim_id: str) -> ProviderClaim:
    import uuid

    try:
        cid = uuid.UUID(claim_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "claim not found") from exc
    obj = await db.get(ProviderClaim, cid)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "claim not found")
    return obj


@router.post("/claims/{claim_id}/approve", response_model=ClaimPublic)
async def approve_claim_endpoint(
    claim_id: str,
    db: DbSession,
    admin: Annotated[User, Depends(_require_admin)],
) -> ClaimPublic:
    claim = await _load_claim_or_404(db, claim_id)
    try:
        updated = await claims_service.admin_verify_claim(db, claim=claim, reviewer=admin)
    except claims_service.ProviderAlreadyClaimedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except claims_service.ClaimError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return ClaimPublic.model_validate(updated)


@router.post("/claims/{claim_id}/reject", response_model=ClaimPublic)
async def reject_claim_endpoint(
    claim_id: str,
    payload: ClaimRejectRequest,
    db: DbSession,
    admin: Annotated[User, Depends(_require_admin)],
) -> ClaimPublic:
    claim = await _load_claim_or_404(db, claim_id)
    updated = await claims_service.admin_reject_claim(
        db, claim=claim, reviewer=admin, reason=payload.reason
    )
    return ClaimPublic.model_validate(updated)


@router.get("/analytics/top-providers", response_model=TopProvidersResponse)
async def analytics_top_providers(
    _admin: Annotated[User, Depends(_require_admin)],
    days: Annotated[int, Query(ge=1, le=365)] = 7,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
) -> TopProvidersResponse:
    rows = await analytics_service.top_providers(days=days, limit=limit)
    return TopProvidersResponse(
        days=days,
        items=[
            TopProviderItem(
                provider_id=r.provider_id,
                display_name=r.display_name,
                slug=r.slug,
                count=r.count,
            )
            for r in rows
        ],
    )
