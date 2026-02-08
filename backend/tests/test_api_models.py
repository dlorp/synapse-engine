"""Tests for API request/response models.

Tests validation, serialization aliases, and model behavior
for the model management API endpoints.
"""

import pytest
from pydantic import ValidationError

from app.models.api import (
    BulkEnabledUpdateResponse,
    EnabledUpdateRequest,
    EnabledUpdateResponse,
    ExternalServerItem,
    ExternalServerStatusResponse,
    PortRangeUpdateRequest,
    PortUpdateRequest,
    ProfileCreateRequest,
    RescanResponse,
    RuntimeSettingsUpdateRequest,
    ServerStatusItem,
    ServerStatusResponse,
    ThinkingUpdateRequest,
    ThinkingUpdateResponse,
    TierUpdateRequest,
    TierUpdateResponse,
)


class TestTierUpdateRequest:
    """Tests for TierUpdateRequest model."""

    def test_valid_fast_tier(self):
        """Test valid fast tier."""
        req = TierUpdateRequest(tier="fast")
        assert req.tier == "fast"

    def test_valid_balanced_tier(self):
        """Test valid balanced tier."""
        req = TierUpdateRequest(tier="balanced")
        assert req.tier == "balanced"

    def test_valid_powerful_tier(self):
        """Test valid powerful tier."""
        req = TierUpdateRequest(tier="powerful")
        assert req.tier == "powerful"

    def test_invalid_tier_rejected(self):
        """Test that invalid tier values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TierUpdateRequest(tier="invalid")
        assert "tier" in str(exc_info.value)

    def test_empty_tier_rejected(self):
        """Test that empty tier is rejected."""
        with pytest.raises(ValidationError):
            TierUpdateRequest(tier="")

    def test_case_sensitive_tier(self):
        """Test that tier validation is case-sensitive."""
        with pytest.raises(ValidationError):
            TierUpdateRequest(tier="FAST")


class TestThinkingUpdateRequest:
    """Tests for ThinkingUpdateRequest model."""

    def test_thinking_true(self):
        """Test thinking flag set to true."""
        req = ThinkingUpdateRequest(thinking=True)
        assert req.thinking is True

    def test_thinking_false(self):
        """Test thinking flag set to false."""
        req = ThinkingUpdateRequest(thinking=False)
        assert req.thinking is False

    def test_thinking_required(self):
        """Test that thinking field is required."""
        with pytest.raises(ValidationError):
            ThinkingUpdateRequest()


class TestEnabledUpdateRequest:
    """Tests for EnabledUpdateRequest model."""

    def test_enabled_true(self):
        """Test enabled flag set to true."""
        req = EnabledUpdateRequest(enabled=True)
        assert req.enabled is True

    def test_enabled_false(self):
        """Test enabled flag set to false."""
        req = EnabledUpdateRequest(enabled=False)
        assert req.enabled is False


class TestTierUpdateResponse:
    """Tests for TierUpdateResponse model."""

    def test_response_creation(self):
        """Test creating a valid response."""
        resp = TierUpdateResponse(
            message="Tier updated",
            model_id="test_model",
            tier="powerful",
            override=True,
        )
        assert resp.message == "Tier updated"
        assert resp.model_id == "test_model"
        assert resp.tier == "powerful"
        assert resp.override is True

    def test_serialization_alias(self):
        """Test that serialization alias works for modelId."""
        resp = TierUpdateResponse(
            message="Test",
            model_id="my_model",
            tier="fast",
            override=False,
        )
        data = resp.model_dump(by_alias=True)
        assert "modelId" in data
        assert data["modelId"] == "my_model"


class TestThinkingUpdateResponse:
    """Tests for ThinkingUpdateResponse model."""

    def test_response_creation(self):
        """Test creating a valid response."""
        resp = ThinkingUpdateResponse(
            message="Updated",
            model_id="test_model",
            thinking=True,
            override=True,
            tier_changed=False,
        )
        assert resp.thinking is True
        assert resp.tier_changed is False

    def test_serialization_aliases(self):
        """Test serialization aliases."""
        resp = ThinkingUpdateResponse(
            message="Test",
            model_id="model",
            thinking=False,
            override=False,
            tier_changed=True,
        )
        data = resp.model_dump(by_alias=True)
        assert "modelId" in data
        assert "tierChanged" in data


class TestEnabledUpdateResponse:
    """Tests for EnabledUpdateResponse model."""

    def test_response_with_server_status(self):
        """Test response with server status."""
        resp = EnabledUpdateResponse(
            message="Model enabled",
            model_id="test_model",
            enabled=True,
            restart_required=False,
            server_status="started",
        )
        assert resp.server_status == "started"

    def test_response_without_server_status(self):
        """Test response without server status (optional)."""
        resp = EnabledUpdateResponse(
            message="Model disabled",
            model_id="test_model",
            enabled=False,
            restart_required=True,
        )
        assert resp.server_status is None


class TestBulkEnabledUpdateResponse:
    """Tests for BulkEnabledUpdateResponse model."""

    def test_response_creation(self):
        """Test creating bulk response."""
        resp = BulkEnabledUpdateResponse(
            message="All models enabled",
            models_updated=5,
            enabled=True,
            timestamp="2025-01-30T10:00:00Z",
        )
        assert resp.models_updated == 5


class TestRescanResponse:
    """Tests for RescanResponse model."""

    def test_response_with_changes(self):
        """Test rescan response with model changes."""
        resp = RescanResponse(
            message="Rescan complete",
            models_found=10,
            models_added=2,
            models_removed=1,
            timestamp="2025-01-30T10:00:00Z",
        )
        assert resp.models_found == 10
        assert resp.models_added == 2
        assert resp.models_removed == 1

    def test_response_defaults(self):
        """Test default values for added/removed."""
        resp = RescanResponse(
            message="Rescan complete",
            models_found=5,
            timestamp="2025-01-30T10:00:00Z",
        )
        assert resp.models_added == 0
        assert resp.models_removed == 0


class TestServerStatusItem:
    """Tests for ServerStatusItem model."""

    def test_item_creation(self):
        """Test creating server status item."""
        item = ServerStatusItem(
            model_id="test_model",
            display_name="Test Model",
            port=8080,
            pid=12345,
            is_ready=True,
            is_running=True,
            uptime_seconds=120,
            tier="powerful",
            is_thinking=True,
        )
        assert item.model_id == "test_model"
        assert item.pid == 12345

    def test_item_without_pid(self):
        """Test external server without PID."""
        item = ServerStatusItem(
            model_id="external",
            display_name="External Server",
            port=8080,
            is_ready=True,
            is_running=True,
            uptime_seconds=3600,
            tier="balanced",
            is_thinking=False,
        )
        assert item.pid is None


class TestServerStatusResponse:
    """Tests for ServerStatusResponse model."""

    def test_response_with_servers(self):
        """Test response with server list."""
        server = ServerStatusItem(
            model_id="test",
            display_name="Test",
            port=8080,
            is_ready=True,
            is_running=True,
            uptime_seconds=60,
            tier="fast",
            is_thinking=False,
        )
        resp = ServerStatusResponse(
            total_servers=1,
            ready_servers=1,
            servers=[server],
        )
        assert len(resp.servers) == 1

    def test_empty_servers(self):
        """Test response with no servers."""
        resp = ServerStatusResponse(
            total_servers=0,
            ready_servers=0,
            servers=[],
        )
        assert resp.total_servers == 0


class TestProfileCreateRequest:
    """Tests for ProfileCreateRequest model."""

    def test_minimal_profile(self):
        """Test creating profile with minimal fields."""
        req = ProfileCreateRequest(name="Test")
        assert req.name == "Test"
        assert req.description is None
        assert req.enabled_models == []

    def test_full_profile(self):
        """Test creating profile with all fields."""
        req = ProfileCreateRequest(
            name="Production",
            description="Production config",
            enabled_models=["model1", "model2"],
        )
        assert req.description == "Production config"
        assert len(req.enabled_models) == 2


class TestPortUpdateRequest:
    """Tests for PortUpdateRequest model."""

    def test_valid_port(self):
        """Test valid port assignment."""
        req = PortUpdateRequest(port=8080)
        assert req.port == 8080

    def test_port_too_low(self):
        """Test port below allowed range."""
        with pytest.raises(ValidationError) as exc_info:
            PortUpdateRequest(port=80)
        assert "port" in str(exc_info.value).lower()

    def test_port_too_high(self):
        """Test port above allowed range."""
        with pytest.raises(ValidationError):
            PortUpdateRequest(port=70000)

    def test_minimum_port(self):
        """Test minimum allowed port."""
        req = PortUpdateRequest(port=1024)
        assert req.port == 1024

    def test_maximum_port(self):
        """Test maximum allowed port."""
        req = PortUpdateRequest(port=65535)
        assert req.port == 65535


class TestRuntimeSettingsUpdateRequest:
    """Tests for RuntimeSettingsUpdateRequest model."""

    def test_all_none(self):
        """Test request with all optional fields as None."""
        req = RuntimeSettingsUpdateRequest()
        assert req.n_gpu_layers is None
        assert req.ctx_size is None
        assert req.n_threads is None
        assert req.batch_size is None

    def test_partial_settings(self):
        """Test request with some settings."""
        req = RuntimeSettingsUpdateRequest(n_gpu_layers=50, ctx_size=32768)
        assert req.n_gpu_layers == 50
        assert req.ctx_size == 32768
        assert req.n_threads is None

    def test_n_gpu_layers_validation(self):
        """Test GPU layers validation."""
        with pytest.raises(ValidationError):
            RuntimeSettingsUpdateRequest(n_gpu_layers=-1)
        with pytest.raises(ValidationError):
            RuntimeSettingsUpdateRequest(n_gpu_layers=1000)

    def test_ctx_size_validation(self):
        """Test context size validation."""
        with pytest.raises(ValidationError):
            RuntimeSettingsUpdateRequest(ctx_size=256)  # Below min
        with pytest.raises(ValidationError):
            RuntimeSettingsUpdateRequest(ctx_size=200000)  # Above max

    def test_n_threads_validation(self):
        """Test thread count validation."""
        with pytest.raises(ValidationError):
            RuntimeSettingsUpdateRequest(n_threads=0)
        with pytest.raises(ValidationError):
            RuntimeSettingsUpdateRequest(n_threads=200)

    def test_batch_size_validation(self):
        """Test batch size validation."""
        with pytest.raises(ValidationError):
            RuntimeSettingsUpdateRequest(batch_size=0)
        with pytest.raises(ValidationError):
            RuntimeSettingsUpdateRequest(batch_size=10000)


class TestPortRangeUpdateRequest:
    """Tests for PortRangeUpdateRequest model."""

    def test_valid_range(self):
        """Test valid port range."""
        req = PortRangeUpdateRequest(start=8080, end=8099)
        assert req.start == 8080
        assert req.end == 8099

    def test_start_too_low(self):
        """Test start port below allowed range."""
        with pytest.raises(ValidationError):
            PortRangeUpdateRequest(start=80, end=8099)

    def test_end_too_high(self):
        """Test end port above allowed range."""
        with pytest.raises(ValidationError):
            PortRangeUpdateRequest(start=8080, end=70000)


class TestExternalServerItem:
    """Tests for ExternalServerItem model."""

    def test_online_server(self):
        """Test online server status."""
        item = ExternalServerItem(
            port=8080,
            status="online",
            response_time_ms=45,
        )
        assert item.status == "online"
        assert item.response_time_ms == 45
        assert item.error_message is None

    def test_offline_server(self):
        """Test offline server with error."""
        item = ExternalServerItem(
            port=8080,
            status="offline",
            error_message="Connection refused",
        )
        assert item.status == "offline"
        assert item.response_time_ms is None
        assert item.error_message == "Connection refused"


class TestExternalServerStatusResponse:
    """Tests for ExternalServerStatusResponse model."""

    def test_all_reachable(self):
        """Test response when all servers reachable."""
        server = ExternalServerItem(port=8080, status="online", response_time_ms=50)
        resp = ExternalServerStatusResponse(
            are_reachable=True,
            use_external_servers=True,
            servers=[server],
            message="All servers online",
            checked_at="2025-01-30T10:00:00Z",
        )
        assert resp.are_reachable is True

    def test_external_disabled(self):
        """Test response when external servers disabled."""
        resp = ExternalServerStatusResponse(
            are_reachable=False,
            use_external_servers=False,
            servers=[],
            message="External servers disabled",
            checked_at="2025-01-30T10:00:00Z",
        )
        assert resp.use_external_servers is False
