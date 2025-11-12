"""Test configuration and fixtures."""
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from practice02.main import create_app

@pytest.fixture(scope="module")
def test_app() -> Generator[TestClient, None]:
    """Create a test client for the FastAPI application."""
    test_app = create_app(enable_rate_limiting=False)
    with TestClient(test_app) as client:
        yield client

@pytest.fixture(scope="module")
def auth_headers() -> dict[str, str]:
    """Return headers for authenticated requests."""
    # We don't really do any authentication yet, but it is convenient to add the JSON content type header here.
    return {"Content-Type": "application/json"}
