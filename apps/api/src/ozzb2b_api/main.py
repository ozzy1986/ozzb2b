"""Module entry point for `python -m ozzb2b_api`."""

from __future__ import annotations

import uvicorn

from ozzb2b_api.config import get_settings


def run() -> None:
    settings = get_settings()
    # Listen on all interfaces inside the container so the host / reverse proxy can reach uvicorn.
    uvicorn.run(
        "ozzb2b_api.app:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=not settings.is_production,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
