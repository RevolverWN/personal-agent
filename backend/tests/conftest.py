"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import create_access_token


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # Create a test token
    token = create_access_token(data={"sub": "1"})  # User ID 1
    return {"Authorization": f"Bearer {token}"}
