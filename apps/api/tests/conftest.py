"""Pytest fixtures shared across the API test suite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ozzb2b_api.app import create_app
from ozzb2b_api.config import Settings


@pytest.fixture()
def settings() -> Settings:
    return Settings(env="test", log_level="WARNING")


@pytest.fixture()
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings=settings))
