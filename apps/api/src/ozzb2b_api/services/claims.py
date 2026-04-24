"""Claim-your-company service.

Flow:
1. User initiates a claim for a provider -> we generate a random token, store
   its SHA-256 hash and return the raw token to the user with instructions.
2. User places a `<meta name="ozzb2b-verify" content="{token}">` tag on the
   provider's homepage (the provider's stored `website`).
3. User triggers verification -> we fetch the homepage, look for the tag, and
   if it matches mark the claim `verified`, link the provider to the user and
   promote the user's role to `provider_owner` when appropriate.

Admins can also verify / reject a claim without the meta tag.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ozzb2b_api.db.models import (
    ClaimMethod,
    ClaimStatus,
    Provider,
    ProviderClaim,
    User,
    UserRole,
)
from ozzb2b_api.errors import ConflictError, DomainError, ExternalServiceError

log = structlog.get_logger("ozzb2b_api.services.claims")


META_TAG_NAME = "ozzb2b-verify"
TOKEN_PREFIX = "ozzb2b-"  # nosec B105 - public verification-token prefix, not secret
TOKEN_RANDOM_BYTES = 16  # 32 hex chars
_MAX_HOMEPAGE_BYTES = 512 * 1024  # 512 KB is more than enough for a <head>

# Accept both orders of attributes and single/double quotes around values.
_META_TAG_RE = re.compile(
    r"""<meta\s+[^>]*name\s*=\s*["']ozzb2b-verify["'][^>]*content\s*=\s*["']([^"']+)["'][^>]*/?>"""
    r"""|<meta\s+[^>]*content\s*=\s*["']([^"']+)["'][^>]*name\s*=\s*["']ozzb2b-verify["'][^>]*/?>""",
    re.IGNORECASE,
)


class ClaimError(DomainError):
    """Base class for domain errors raised by the claim service."""


class ProviderAlreadyClaimedError(ConflictError):
    """Provider already has a verified owner."""


class NoVerifiableWebsiteError(ClaimError):
    """Provider has no website to verify against (HTTP 400)."""


class HomepageUnreachableError(ExternalServiceError):
    """Couldn't fetch the provider homepage."""


class MetaTagNotFoundError(ClaimError):
    """Homepage fetched but the verification meta tag is missing or wrong."""


HomepageFetcher = Callable[[str], Awaitable[str]]


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_hex(TOKEN_RANDOM_BYTES)


@dataclass(frozen=True)
class ClaimInitiation:
    claim: ProviderClaim
    raw_token: str
    meta_tag_snippet: str


async def initiate_claim(
    db: AsyncSession,
    *,
    provider: Provider,
    user: User,
) -> ClaimInitiation:
    """Create (or refresh) a pending claim for `user` on `provider`.

    If the user already has a pending claim for this provider we mint a fresh
    token and reuse the existing record, so the user can request new instructions
    without orphaning rows. If another user's claim is already verified, we
    refuse.
    """
    if provider.is_claimed and provider.claimed_by_user_id != user.id:
        raise ProviderAlreadyClaimedError("provider already claimed")

    raw = _generate_token()
    token_hash = _hash_token(raw)
    now = datetime.now(tz=UTC)

    existing_stmt = select(ProviderClaim).where(
        ProviderClaim.provider_id == provider.id,
        ProviderClaim.user_id == user.id,
        ProviderClaim.status == ClaimStatus.PENDING,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

    if existing is None:
        claim = ProviderClaim(
            provider_id=provider.id,
            user_id=user.id,
            status=ClaimStatus.PENDING,
            method=ClaimMethod.META_TAG,
            token_hash=token_hash,
        )
        db.add(claim)
    else:
        existing.token_hash = token_hash
        existing.updated_at = now
        claim = existing

    await db.flush()
    await db.commit()
    await db.refresh(claim)

    snippet = f'<meta name="{META_TAG_NAME}" content="{raw}">'
    return ClaimInitiation(claim=claim, raw_token=raw, meta_tag_snippet=snippet)


def extract_token_from_html(html: str) -> str | None:
    """Return the token value of the verification meta tag, or None."""
    if not html:
        return None
    match = _META_TAG_RE.search(html[:_MAX_HOMEPAGE_BYTES])
    if not match:
        return None
    # Either group 1 (name-first) or group 2 (content-first) will be set.
    return (match.group(1) or match.group(2)).strip()


async def verify_claim(
    db: AsyncSession,
    *,
    provider: Provider,
    user: User,
    homepage_fetcher: HomepageFetcher,
) -> ProviderClaim:
    """Verify a pending claim by fetching the homepage and checking the tag."""
    if provider.is_claimed and provider.claimed_by_user_id != user.id:
        raise ProviderAlreadyClaimedError("provider already claimed")
    if not provider.website:
        raise NoVerifiableWebsiteError("provider has no website")

    stmt = select(ProviderClaim).where(
        ProviderClaim.provider_id == provider.id,
        ProviderClaim.user_id == user.id,
        ProviderClaim.status == ClaimStatus.PENDING,
    )
    claim = (await db.execute(stmt)).scalar_one_or_none()
    if claim is None:
        raise ClaimError("no pending claim for this user and provider")

    try:
        html = await homepage_fetcher(provider.website)
    except Exception as exc:
        log.info("claims.verify.fetch_failed", provider_id=str(provider.id), error=str(exc))
        raise HomepageUnreachableError(str(exc)) from exc

    token = extract_token_from_html(html)
    if not token or _hash_token(token) != claim.token_hash:
        raise MetaTagNotFoundError("verification meta tag missing or invalid")

    await _mark_claim_verified(db, claim=claim, provider=provider, user=user)
    return claim


async def admin_verify_claim(
    db: AsyncSession, *, claim: ProviderClaim, reviewer: User
) -> ProviderClaim:
    if reviewer.role != UserRole.ADMIN:
        raise PermissionError("admin only")
    provider = await db.get(Provider, claim.provider_id)
    user = await db.get(User, claim.user_id)
    if provider is None or user is None:
        raise ClaimError("claim references missing entities")
    if provider.is_claimed and provider.claimed_by_user_id != user.id:
        raise ProviderAlreadyClaimedError("provider already claimed")
    claim.method = ClaimMethod.ADMIN_MANUAL
    await _mark_claim_verified(db, claim=claim, provider=provider, user=user)
    return claim


async def admin_reject_claim(
    db: AsyncSession,
    *,
    claim: ProviderClaim,
    reviewer: User,
    reason: str | None,
) -> ProviderClaim:
    if reviewer.role != UserRole.ADMIN:
        raise PermissionError("admin only")
    claim.status = ClaimStatus.REJECTED
    claim.rejected_at = datetime.now(tz=UTC)
    claim.rejected_reason = (reason or "")[:1000] or None
    await db.commit()
    await db.refresh(claim)
    return claim


async def _mark_claim_verified(
    db: AsyncSession,
    *,
    claim: ProviderClaim,
    provider: Provider,
    user: User,
) -> None:
    now = datetime.now(tz=UTC)
    claim.status = ClaimStatus.VERIFIED
    claim.verified_at = now

    provider.is_claimed = True
    provider.claimed_by_user_id = user.id

    # Promote client -> provider_owner; never demote an admin.
    if user.role == UserRole.CLIENT:
        user.role = UserRole.PROVIDER_OWNER

    # Reject every other pending claim for the same provider, as we now have
    # a verified owner. This avoids a second user finishing verification after
    # the first already won.
    await db.execute(
        update(ProviderClaim)
        .where(
            ProviderClaim.provider_id == provider.id,
            ProviderClaim.id != claim.id,
            ProviderClaim.status == ClaimStatus.PENDING,
        )
        .values(
            status=ClaimStatus.REJECTED,
            rejected_at=now,
            rejected_reason="provider already claimed by another user",
        )
    )

    await db.commit()
    await db.refresh(claim)
    await db.refresh(provider)
    await db.refresh(user)


async def list_claims_for_user(db: AsyncSession, *, user: User) -> list[ProviderClaim]:
    stmt = (
        select(ProviderClaim)
        .where(ProviderClaim.user_id == user.id)
        .options(selectinload(ProviderClaim.provider))
        .order_by(ProviderClaim.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_pending_claims(db: AsyncSession) -> list[ProviderClaim]:
    stmt = (
        select(ProviderClaim)
        .where(ProviderClaim.status == ClaimStatus.PENDING)
        .options(selectinload(ProviderClaim.provider), selectinload(ProviderClaim.user))
        .order_by(ProviderClaim.created_at.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_owned_providers(db: AsyncSession, *, user: User) -> list[Provider]:
    stmt = (
        select(Provider)
        .where(Provider.claimed_by_user_id == user.id)
        .options(
            selectinload(Provider.country),
            selectinload(Provider.city),
            selectinload(Provider.legal_form),
            selectinload(Provider.categories),
        )
        .order_by(Provider.display_name.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


def user_may_edit_provider(user: User, provider: Provider) -> bool:
    """Owner-or-admin check for edits. Kept separate for testability."""
    if user.role == UserRole.ADMIN:
        return True
    return bool(provider.is_claimed) and provider.claimed_by_user_id == user.id


async def update_owned_provider(
    db: AsyncSession,
    *,
    provider: Provider,
    user: User,
    fields: dict[str, object],
) -> Provider:
    """Apply an owner edit to ``provider``.

    Empty/whitespace string values are normalised to ``None`` so the UI can
    clear fields explicitly. Authorisation is checked via
    :func:`user_may_edit_provider`; callers should map the raised
    :class:`PermissionError` to a 403.
    """
    if not user_may_edit_provider(user, provider):
        raise PermissionError("not an owner of this provider")

    for field, value in fields.items():
        if isinstance(value, str) and not value.strip():
            setattr(provider, field, None)
        else:
            setattr(provider, field, value)

    await db.commit()
    await db.refresh(provider)
    return provider
