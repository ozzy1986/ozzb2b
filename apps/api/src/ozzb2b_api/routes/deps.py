"""Common route dependencies: auth + DB session."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ozzb2b_api.db.models import User
from ozzb2b_api.db.session import get_db
from ozzb2b_api.security.tokens import TokenError, decode_access_token

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def _extract_access_token(
    authorization: str | None,
    cookie_token: str | None,
) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return cookie_token


async def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    access_token_cookie: Annotated[str | None, Cookie(alias="ozzb2b_at")] = None,
) -> User:
    token = await _extract_access_token(authorization, access_token_cookie)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    try:
        claims = decode_access_token(token)
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    try:
        user_id = uuid.UUID(claims.sub)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid subject") from exc
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


async def get_current_user_optional(
    db: DbSession,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    access_token_cookie: Annotated[str | None, Cookie(alias="ozzb2b_at")] = None,
) -> User | None:
    token = await _extract_access_token(authorization, access_token_cookie)
    if not token:
        return None
    try:
        claims = decode_access_token(token)
        user_id = uuid.UUID(claims.sub)
    except (TokenError, ValueError):
        return None
    return (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
