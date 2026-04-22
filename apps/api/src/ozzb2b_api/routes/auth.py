"""Auth endpoints: register, login, refresh, logout, me."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from ozzb2b_api.clients.redis import get_redis
from ozzb2b_api.config import get_settings
from ozzb2b_api.db.models import User
from ozzb2b_api.observability.metrics import auth_rate_limit_blocked_total
from ozzb2b_api.routes.deps import DbSession, get_current_user
from ozzb2b_api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from ozzb2b_api.security.rate_limit import RateLimiter, client_ip
from ozzb2b_api.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


REFRESH_COOKIE = "ozzb2b_rt"
ACCESS_COOKIE = "ozzb2b_at"


def _request_headers(request: Request) -> dict[str, str]:
    return {k.lower(): v for k, v in request.headers.items()}


async def _enforce_rate_limit(
    *,
    request: Request,
    response: Response,
    endpoint: str,
    scope_key: str | None,
    limit: int,
) -> None:
    cfg = get_settings()
    if not cfg.rate_limit_enabled or limit <= 0:
        return
    limiter = RateLimiter(redis=get_redis(), window_seconds=cfg.rate_limit_window_seconds)
    ip = client_ip(_request_headers(request), request.client.host if request.client else None)

    # Always throttle by IP; additionally throttle by the supplied scope
    # (e.g. email) so a single attacker can't burn through many accounts
    # from rotating addresses.
    for scope_name, scope_value in (("ip", ip), ("scope", scope_key)):
        if not scope_value:
            continue
        outcome = await limiter.hit(
            endpoint=endpoint,
            scope=f"{scope_name}:{scope_value}",
            limit=limit,
        )
        if not outcome.allowed:
            auth_rate_limit_blocked_total.labels(endpoint, scope_name).inc()
            response.headers["Retry-After"] = str(outcome.retry_after_seconds)
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "слишком много попыток, попробуйте позже",
            )


def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    access_expires_at: datetime,
    refresh_token: str,
    refresh_expires_at: datetime,
) -> None:
    cfg = get_settings()
    secure = cfg.is_production
    # In production the API (api.ozzb2b.com) is on a different origin from the
    # browser (ozzb2b.com), so we need SameSite=None + Secure for the cookies
    # to be sent with cross-site credentialed requests. In dev we use Lax.
    samesite: Literal["lax", "none"] = "none" if cfg.is_production else "lax"
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        expires=refresh_expires_at,
        path="/auth",
    )
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        expires=access_expires_at,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/auth")
    response.delete_cookie(ACCESS_COOKIE, path="/")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> TokenResponse:
    cfg = get_settings()
    await _enforce_rate_limit(
        request=request,
        response=response,
        endpoint="register",
        scope_key=payload.email.lower(),
        limit=cfg.rate_limit_register_max,
    )
    try:
        user = await auth_service.register(
            db,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    tokens = await auth_service.issue_tokens(
        db,
        user=user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_auth_cookies(
        response,
        access_token=tokens.access_token,
        access_expires_at=tokens.access_expires_at,
        refresh_token=tokens.refresh_token,
        refresh_expires_at=tokens.refresh_expires_at,
    )
    return TokenResponse(
        access_token=tokens.access_token,
        expires_at=tokens.access_expires_at,
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> TokenResponse:
    cfg = get_settings()
    await _enforce_rate_limit(
        request=request,
        response=response,
        endpoint="login",
        scope_key=payload.email.lower(),
        limit=cfg.rate_limit_login_max,
    )
    try:
        user = await auth_service.authenticate(db, email=payload.email, password=payload.password)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    tokens = await auth_service.issue_tokens(
        db,
        user=user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_auth_cookies(
        response,
        access_token=tokens.access_token,
        access_expires_at=tokens.access_expires_at,
        refresh_token=tokens.refresh_token,
        refresh_expires_at=tokens.refresh_expires_at,
    )
    return TokenResponse(
        access_token=tokens.access_token,
        expires_at=tokens.access_expires_at,
        user=UserPublic.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: DbSession,
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> TokenResponse:
    cfg = get_settings()
    await _enforce_rate_limit(
        request=request,
        response=response,
        endpoint="refresh",
        scope_key=None,
        limit=cfg.rate_limit_refresh_max,
    )
    if not refresh_cookie:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing refresh token")
    try:
        user, tokens = await auth_service.rotate_refresh(
            db,
            raw_refresh_token=refresh_cookie,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except auth_service.InvalidRefreshTokenError as exc:
        _clear_auth_cookies(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    _set_auth_cookies(
        response,
        access_token=tokens.access_token,
        access_expires_at=tokens.access_expires_at,
        refresh_token=tokens.refresh_token,
        refresh_expires_at=tokens.refresh_expires_at,
    )
    return TokenResponse(
        access_token=tokens.access_token,
        expires_at=tokens.access_expires_at,
        user=UserPublic.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: DbSession,
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> Response:
    if refresh_cookie:
        await auth_service.revoke_refresh(db, raw_refresh_token=refresh_cookie)
    _clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserPublic)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.model_validate(current_user)
