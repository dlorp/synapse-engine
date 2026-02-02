"""Pytest configuration and shared fixtures for backend tests.

Provides common test fixtures for async testing, mocking, and test isolation.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for tests."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def mock_logger():
    """Mock logger to suppress log output in tests."""
    with patch("app.core.logging.get_logger") as mock:
        mock.return_value = MagicMock()
        yield mock.return_value


@pytest.fixture
async def clean_event_bus():
    """Create a fresh EventBus for each test, ensuring cleanup."""
    from app.services.event_bus import EventBus

    bus = EventBus(history_size=50, max_queue_size=100)
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
def sample_event_metadata():
    """Sample metadata dict for testing events."""
    return {
        "query_id": "test-query-123",
        "complexity_score": 7.5,
        "tier": "Q3",
    }
