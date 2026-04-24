"""Claim-your-company endpoints (user-facing).

Admin review endpoints live in routes.admin.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import Provider, User
from ozzb2b_api.routes.deps import DbSession, get_current_user
from ozzb2b_api.schemas.catalog import ProviderDetail
from ozzb2b_api.schemas.claims import (
    ClaimInitiateResponse,
    ClaimPublic,
    ProviderUpdateRequest,
)
from ozzb2b_api.security.rate_limit import enforce_rate_limit
from ozzb2b_api.security.safe_http import SafeHttpPolicy, UnsafeUrlError, fetch_text
from ozzb2b_api.services import catalog as catalog_service
from ozzb2b_api.services import claims as claims_service
from ozzb2b_api.services.claims import HomepageUnreachableError
from ozzb2b_api.services.provider_mapping import to_detail as to_provider_detail

router = APIRouter(tags=["claims"])


async def _fetch_homepage(url: str) -> str:
    """Default fetcher used during verification.

    Routes through :func:`ozzb2b_api.security.safe_http.fetch_text` so the
    request is hardened against SSRF (scheme/host/IP allowlist, bounded
    redirects, bounded body and time). Failures are normalised into
    :class:`HomepageUnreachableError` so callers don't have to know about
    the safe-http layer.
    """
    cfg = get_settings()
    policy = SafeHttpPolicy(allow_http=not cfg.is_production)
    try:
        return await fetch_text(
            url,
            policy=policy,
            user_agent=f"ozzb2b-claim-verifier/{cfg.env}",
        )
    except UnsafeUrlError as exc:
        raise HomepageUnreachableError(str(exc)) from exc


async def _load_provider_or_404(db: AsyncSession, slug: str) -> Provider:
    provider = await catalog_service.get_provider_by_slug(db, slug)
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "provider not found")
    return provider


@router.post(
    "/providers/{slug}/claim",
    response_model=ClaimInitiateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_claim(
    slug: str,
    request: Request,
    response: Response,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> ClaimInitiateResponse:
    cfg = get_settings()
    await enforce_rate_limit(
        request=request,
        response=response,
        endpoint="claim_init",
        limit=cfg.rate_limit_claim_init_max,
        user_scope=str(user.id),
    )
    provider = await _load_provider_or_404(db, slug)
    if not provider.website:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "provider has no website, verification impossible",
        )
    # Domain errors raised below are translated to HTTP responses by the
    # global DomainError handler in `ozzb2b_api.app`.
    result = await claims_service.initiate_claim(db, provider=provider, user=user)
    return ClaimInitiateResponse(
        claim_id=result.claim.id,
        status=result.claim.status.value,
        token=result.raw_token,
        meta_tag=result.meta_tag_snippet,
        instructions=(
            "Разместите указанный meta-тег в <head> главной страницы сайта "
            "компании и нажмите «Проверить»."
        ),
    )


@router.post(
    "/providers/{slug}/claim/verify",
    response_model=ClaimPublic,
)
async def verify_claim(
    slug: str,
    request: Request,
    response: Response,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> ClaimPublic:
    cfg = get_settings()
    # Verification triggers an outbound HTTP fetch of the provider's homepage,
    # which is the most expensive (and SSRF-sensitive) action a user can
    # trigger. Rate-limit per user so repeated abuse is throttled.
    await enforce_rate_limit(
        request=request,
        response=response,
        endpoint="claim_verify",
        limit=cfg.rate_limit_claim_verify_max,
        user_scope=str(user.id),
    )
    provider = await _load_provider_or_404(db, slug)
    # All claim-domain errors have their own HTTP status_code and are mapped
    # by the global DomainError handler in `ozzb2b_api.app`.
    claim = await claims_service.verify_claim(
        db,
        provider=provider,
        user=user,
        homepage_fetcher=_fetch_homepage,
    )
    return ClaimPublic.model_validate(claim)


@router.get("/me/claims", response_model=list[ClaimPublic])
async def list_my_claims(
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> list[ClaimPublic]:
    rows = await claims_service.list_claims_for_user(db, user=user)
    return [ClaimPublic.model_validate(r) for r in rows]


@router.get("/me/providers", response_model=list[ProviderDetail])
async def list_my_providers(
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> list[ProviderDetail]:
    rows = await claims_service.list_owned_providers(db, user=user)
    return [to_provider_detail(p) for p in rows]


@router.patch("/providers/{slug}", response_model=ProviderDetail)
async def update_provider(
    slug: str,
    payload: ProviderUpdateRequest,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> ProviderDetail:
    provider = await _load_provider_or_404(db, slug)
    try:
        updated = await claims_service.update_owned_provider(
            db,
            provider=provider,
            user=user,
            fields=payload.model_dump(exclude_unset=True),
        )
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    return to_provider_detail(updated)
