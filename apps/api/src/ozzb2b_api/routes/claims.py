"""Claim-your-company endpoints (user-facing).

Admin review endpoints live in routes.admin.
"""

from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import Provider, User
from ozzb2b_api.routes.catalog import to_provider_detail
from ozzb2b_api.routes.deps import DbSession, get_current_user
from ozzb2b_api.schemas.catalog import ProviderDetail
from ozzb2b_api.schemas.claims import (
    ClaimInitiateResponse,
    ClaimPublic,
    ProviderUpdateRequest,
)
from ozzb2b_api.services import catalog as catalog_service
from ozzb2b_api.services import claims as claims_service
from ozzb2b_api.services.claims import (
    HomepageUnreachableError,
    MetaTagNotFoundError,
    NoVerifiableWebsiteError,
    ProviderAlreadyClaimedError,
)

router = APIRouter(tags=["claims"])


async def _fetch_homepage(url: str) -> str:
    """Default fetcher used during verification.

    Separate function to keep `verify_claim` easy to unit test without network.
    """
    cfg = get_settings()
    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        headers={
            "User-Agent": f"ozzb2b-claim-verifier/{cfg.env}",
            "Accept": "text/html,application/xhtml+xml",
        },
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


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
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> ClaimInitiateResponse:
    provider = await _load_provider_or_404(db, slug)
    if not provider.website:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "provider has no website, verification impossible",
        )
    try:
        result = await claims_service.initiate_claim(db, provider=provider, user=user)
    except ProviderAlreadyClaimedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
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
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> ClaimPublic:
    provider = await _load_provider_or_404(db, slug)
    try:
        claim = await claims_service.verify_claim(
            db,
            provider=provider,
            user=user,
            homepage_fetcher=_fetch_homepage,
        )
    except ProviderAlreadyClaimedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except NoVerifiableWebsiteError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except HomepageUnreachableError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    except MetaTagNotFoundError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except claims_service.ClaimError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
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
    if not claims_service.user_may_edit_provider(user, provider):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not an owner of this provider")
    data = payload.model_dump(exclude_unset=True)
    # Normalize empty strings to nulls so the UI can clear fields explicitly.
    for field, value in data.items():
        if isinstance(value, str) and not value.strip():
            setattr(provider, field, None)
        else:
            setattr(provider, field, value)
    await db.commit()
    await db.refresh(provider)
    return to_provider_detail(provider)
