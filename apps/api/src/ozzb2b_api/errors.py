"""Typed domain error hierarchy.

Services raise these instead of ``HTTPException`` so business logic stays free
of HTTP concerns. The central exception handler in :mod:`ozzb2b_api.app` maps
each subclass to a stable ``status_code`` and a machine-readable English
``detail`` string. The frontend turns the ``detail`` into Russian via
``humanizeError``.
"""

from __future__ import annotations

from http import HTTPStatus


class DomainError(Exception):
    """Base class for service-layer domain errors.

    Subclasses set a class-level :attr:`status_code` so the global handler can
    pick the right HTTP response without an ``isinstance`` ladder. The
    ``detail`` returned to clients is always the exception message (plain
    English, stable across releases).
    """

    status_code: int = HTTPStatus.BAD_REQUEST


class NotFoundError(DomainError):
    status_code = HTTPStatus.NOT_FOUND


class ConflictError(DomainError):
    status_code = HTTPStatus.CONFLICT


class ValidationError(DomainError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY


class AuthenticationError(DomainError):
    status_code = HTTPStatus.UNAUTHORIZED


class ForbiddenError(DomainError):
    status_code = HTTPStatus.FORBIDDEN


class ExternalServiceError(DomainError):
    status_code = HTTPStatus.BAD_GATEWAY


class RateLimitedError(DomainError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
