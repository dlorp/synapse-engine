"""Tests for the proxy router endpoints.

Tests cover:
- Server manager validation
- Server running/not running states
- Proxy POST request handling
- Health check endpoint
- Error handling for connection failures
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import RequestError

from app.main import app
from app.routers import proxy


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_server():
    """Create a mock server object."""
    server = MagicMock()
    server.port = 8080
    return server


@pytest.fixture
def mock_server_manager(mock_server):
    """Create and inject a mock server manager."""
    manager = MagicMock()
    manager.is_server_running.return_value = True
    manager.servers = {"test_model": mock_server}

    # Inject mock
    original_manager = proxy.server_manager
    proxy.server_manager = manager
    yield manager
    proxy.server_manager = original_manager


@pytest.fixture
def no_server_manager():
    """Temporarily set server_manager to None."""
    original_manager = proxy.server_manager
    proxy.server_manager = None
    yield
    proxy.server_manager = original_manager


class TestValidateServerManager:
    """Tests for _validate_server_manager helper."""

    def test_raises_503_when_not_initialized(self, client, no_server_manager):
        """Should raise 503 when server manager is None."""
        response = client.post(
            "/api/proxy/test_model/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Server manager not initialized" in response.json()["detail"]


class TestGetServerPort:
    """Tests for _get_server_port helper."""

    def test_raises_503_when_server_not_running(self, client, mock_server_manager):
        """Should raise 503 when model server is not running."""
        mock_server_manager.is_server_running.return_value = False

        response = client.post(
            "/api/proxy/test_model/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "not running" in response.json()["detail"]

    def test_raises_404_when_server_not_found(self, client, mock_server_manager):
        """Should raise 404 when model not in servers dict."""
        mock_server_manager.is_server_running.return_value = True
        mock_server_manager.servers = {}  # Empty servers dict

        response = client.post(
            "/api/proxy/unknown_model/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found in registry" in response.json()["detail"]


class TestProxyChatCompletions:
    """Tests for POST /api/proxy/{model_id}/v1/chat/completions."""

    @patch("app.routers.proxy.httpx.AsyncClient")
    def test_successful_proxy(self, mock_client_class, client, mock_server_manager):
        """Should successfully proxy chat completion request."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"choices": [{"message": {"content": "Hello!"}}]}'
        mock_response.headers = {"content-type": "application/json"}

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        response = client.post(
            "/api/proxy/test_model/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

        assert response.status_code == 200
        assert "choices" in response.json()

    @patch("app.routers.proxy.httpx.AsyncClient")
    def test_connection_error_returns_502(self, mock_client_class, client, mock_server_manager):
        """Should return 502 when connection to model server fails."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(
            side_effect=RequestError("Connection refused", request=MagicMock())
        )
        mock_client_class.return_value = mock_client

        response = client.post(
            "/api/proxy/test_model/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "Failed to connect to model server" in response.json()["detail"]


class TestProxyCompletions:
    """Tests for POST /api/proxy/{model_id}/v1/completions."""

    @patch("app.routers.proxy.httpx.AsyncClient")
    def test_successful_proxy(self, mock_client_class, client, mock_server_manager):
        """Should successfully proxy completion request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"choices": [{"text": "...once upon a time"}]}'
        mock_response.headers = {"content-type": "application/json"}

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        response = client.post(
            "/api/proxy/test_model/v1/completions",
            json={"prompt": "Once upon a time", "max_tokens": 100},
        )

        assert response.status_code == 200
        assert "choices" in response.json()


class TestProxyHealthCheck:
    """Tests for GET /api/proxy/{model_id}/health."""

    def test_returns_503_when_server_not_running(self, client, mock_server_manager):
        """Should return 503 with not_running status when server not running."""
        mock_server_manager.is_server_running.return_value = False

        response = client.get("/api/proxy/test_model/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json()["status"] == "not_running"

    def test_returns_404_when_server_not_found(self, client, mock_server_manager):
        """Should return 404 when server not in registry."""
        mock_server_manager.is_server_running.return_value = True
        mock_server_manager.servers = {}

        response = client.get("/api/proxy/unknown_model/health")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.routers.proxy.httpx.AsyncClient")
    def test_successful_health_check(self, mock_client_class, client, mock_server_manager):
        """Should return proxied health check response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"status": "ok", "model_loaded": true}'
        mock_response.headers = {"content-type": "application/json"}

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        response = client.get("/api/proxy/test_model/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @patch("app.routers.proxy.httpx.AsyncClient")
    def test_unreachable_server(self, mock_client_class, client, mock_server_manager):
        """Should return 503 with unreachable status on connection error."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(
            side_effect=RequestError("Connection refused", request=MagicMock())
        )
        mock_client_class.return_value = mock_client

        response = client.get("/api/proxy/test_model/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json()["status"] == "unreachable"

    def test_returns_503_when_manager_not_initialized(self, client, no_server_manager):
        """Should raise 503 when server manager is None."""
        response = client.get("/api/proxy/test_model/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Server manager not initialized" in response.json()["detail"]


class TestProxyPostRequestHelper:
    """Tests for _proxy_post_request helper function."""

    @patch("app.routers.proxy.httpx.AsyncClient")
    def test_uses_correct_timeout(self, mock_client_class, client, mock_server_manager):
        """Should use 300s timeout for LLM inference requests."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"choices": []}'
        mock_response.headers = {}

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        client.post(
            "/api/proxy/test_model/v1/chat/completions",
            json={"messages": []},
        )

        # Verify AsyncClient was created with 300s timeout
        mock_client_class.assert_called_with(timeout=300.0)

    @patch("app.routers.proxy.httpx.AsyncClient")
    def test_forwards_request_body(self, mock_client_class, client, mock_server_manager):
        """Should forward the request body to target server."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"choices": []}'
        mock_response.headers = {}

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        request_body = {"messages": [{"role": "user", "content": "Test"}]}
        client.post(
            "/api/proxy/test_model/v1/chat/completions",
            json=request_body,
        )

        # Verify post was called with the body
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert b"Test" in call_args.kwargs.get("content", b"")
