"""Tests for the health monitoring service.

Tests background health monitoring, state transition detection,
and alert emission functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.health_monitor import (
    HealthMonitor,
    get_health_monitor,
    init_health_monitor,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def health_monitor():
    """Create a health monitor with short check interval for testing."""
    return HealthMonitor(check_interval=1, health_endpoint="http://localhost:8000/api/health/ready")


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    mock_bus = AsyncMock()
    mock_bus.publish = AsyncMock()
    return mock_bus


# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Tests for HealthMonitor initialization."""

    def test_default_check_interval(self):
        """Default check interval should be 60 seconds."""
        monitor = HealthMonitor()
        assert monitor.check_interval == 60

    def test_custom_check_interval(self):
        """Custom check interval should be respected."""
        monitor = HealthMonitor(check_interval=30)
        assert monitor.check_interval == 30

    def test_default_endpoint(self):
        """Default endpoint should be localhost:8000."""
        monitor = HealthMonitor()
        assert monitor.health_endpoint == "http://localhost:8000/api/health/ready"

    def test_custom_endpoint(self):
        """Custom endpoint should be respected."""
        monitor = HealthMonitor(health_endpoint="http://custom:9000/health")
        assert monitor.health_endpoint == "http://custom:9000/health"

    def test_initial_state(self, health_monitor):
        """Monitor should start with 'ok' status and not running."""
        assert health_monitor.last_status == "ok"
        assert health_monitor.degraded_since is None
        assert health_monitor.running is False
        assert health_monitor._task is None


# ============================================================================
# Start/Stop Tests
# ============================================================================


class TestStartStop:
    """Tests for starting and stopping the health monitor."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self, health_monitor):
        """Start should set running flag and create task."""
        with patch.object(health_monitor, "_monitor_loop", new_callable=AsyncMock):
            await health_monitor.start()

            assert health_monitor.running is True
            assert health_monitor._task is not None

            # Clean up
            await health_monitor.stop()

    @pytest.mark.asyncio
    async def test_start_idempotent(self, health_monitor):
        """Calling start multiple times should be safe."""
        with patch.object(health_monitor, "_monitor_loop", new_callable=AsyncMock):
            await health_monitor.start()
            task1 = health_monitor._task

            # Second start should be ignored
            await health_monitor.start()
            task2 = health_monitor._task

            # Same task should be kept
            assert task1 is task2

            # Clean up
            await health_monitor.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self, health_monitor):
        """Stop should clear running flag and cancel task."""
        with patch.object(health_monitor, "_monitor_loop", new_callable=AsyncMock):
            await health_monitor.start()
            assert health_monitor.running is True

            await health_monitor.stop()

            assert health_monitor.running is False

    @pytest.mark.asyncio
    async def test_stop_without_start(self, health_monitor):
        """Stop without start should be safe."""
        # Should not raise
        await health_monitor.stop()

        assert health_monitor.running is False


# ============================================================================
# Health Check Tests
# ============================================================================


class TestHealthCheck:
    """Tests for the _check_health method."""

    @pytest.mark.asyncio
    async def test_handles_timeout(self, health_monitor):
        """Health check should handle timeouts gracefully."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Should not raise
            await health_monitor._check_health()

            # Status should remain unchanged
            assert health_monitor.last_status == "ok"

    @pytest.mark.asyncio
    async def test_handles_non_200_response(self, health_monitor):
        """Health check should handle non-200 responses gracefully."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Should not raise
            await health_monitor._check_health()

            # Status should remain unchanged
            assert health_monitor.last_status == "ok"

    @pytest.mark.asyncio
    async def test_updates_status_on_ok(self, health_monitor):
        """Health check should maintain 'ok' status when healthy."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "ok",
                "components": {"database": "ready", "redis": "ready"},
            }
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await health_monitor._check_health()

            assert health_monitor.last_status == "ok"
            assert health_monitor.degraded_since is None

    @pytest.mark.asyncio
    async def test_detects_degraded_transition(self, health_monitor, mock_event_bus):
        """Health check should detect ok -> degraded transition."""
        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch("app.services.event_bus.get_event_bus", return_value=mock_event_bus),
        ):
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "degraded",
                "components": {"database": "ready", "redis": "unavailable"},
            }
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await health_monitor._check_health()

            assert health_monitor.last_status == "degraded"
            assert health_monitor.degraded_since is not None

    @pytest.mark.asyncio
    async def test_detects_recovery_transition(self, health_monitor, mock_event_bus):
        """Health check should detect degraded -> ok transition."""
        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch("app.services.event_bus.get_event_bus", return_value=mock_event_bus),
        ):
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "ok",
                "components": {"database": "ready", "redis": "ready"},
            }
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Simulate previous degraded state
            health_monitor.last_status = "degraded"
            health_monitor.degraded_since = datetime.utcnow() - timedelta(minutes=5)

            await health_monitor._check_health()

            assert health_monitor.last_status == "ok"
            assert health_monitor.degraded_since is None


# ============================================================================
# Alert Emission Tests
# ============================================================================


class TestAlertEmission:
    """Tests for alert emission methods."""

    @pytest.mark.asyncio
    async def test_emit_degraded_alert_single_component(self, health_monitor, mock_event_bus):
        """Degraded alert should list single failed component."""
        with patch("app.services.event_bus.get_event_bus", return_value=mock_event_bus):
            await health_monitor._emit_degraded_alert({"database": "ready", "redis": "unavailable"})

            mock_event_bus.publish.assert_called_once()
            call_args = mock_event_bus.publish.call_args
            assert "redis" in call_args.kwargs["message"]
            assert "unavailable" in call_args.kwargs["message"]

    @pytest.mark.asyncio
    async def test_emit_degraded_alert_multiple_components(self, health_monitor, mock_event_bus):
        """Degraded alert should list multiple failed components."""
        with patch("app.services.event_bus.get_event_bus", return_value=mock_event_bus):
            await health_monitor._emit_degraded_alert(
                {"database": "unavailable", "redis": "unavailable", "cache": "ready"}
            )

            mock_event_bus.publish.assert_called_once()
            call_args = mock_event_bus.publish.call_args
            assert (
                "database" in call_args.kwargs["message"] or "redis" in call_args.kwargs["message"]
            )

    @pytest.mark.asyncio
    async def test_emit_recovery_alert(self, health_monitor, mock_event_bus):
        """Recovery alert should be emitted with duration."""
        with patch("app.services.event_bus.get_event_bus", return_value=mock_event_bus):
            health_monitor.degraded_since = datetime.utcnow() - timedelta(minutes=5)

            await health_monitor._emit_recovery_alert()

            mock_event_bus.publish.assert_called_once()
            call_args = mock_event_bus.publish.call_args
            assert "recovered" in call_args.kwargs["message"].lower()

    @pytest.mark.asyncio
    async def test_emit_alerts_handle_missing_event_bus(self, health_monitor):
        """Alert methods should handle missing event bus gracefully."""
        with patch(
            "app.services.event_bus.get_event_bus",
            side_effect=RuntimeError("Event bus not initialized"),
        ):
            # Should not raise
            await health_monitor._emit_degraded_alert({"redis": "unavailable"})
            await health_monitor._emit_recovery_alert()


# ============================================================================
# Helper Method Tests
# ============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_failed_components_single(self, health_monitor):
        """Should identify single failed component."""
        components = {"database": "ready", "redis": "unavailable"}
        failed = health_monitor._get_failed_components(components)

        assert failed == ["redis"]

    def test_get_failed_components_multiple(self, health_monitor):
        """Should identify multiple failed components."""
        components = {
            "database": "unavailable",
            "redis": "unavailable",
            "cache": "ready",
        }
        failed = health_monitor._get_failed_components(components)

        assert set(failed) == {"database", "redis"}

    def test_get_failed_components_all_healthy(self, health_monitor):
        """Should return empty list when all healthy."""
        components = {"database": "ready", "redis": "ready", "cache": "ok"}
        failed = health_monitor._get_failed_components(components)

        assert failed == []

    def test_get_failed_components_alive_status(self, health_monitor):
        """Should treat 'alive' status as healthy."""
        components = {"service": "alive"}
        failed = health_monitor._get_failed_components(components)

        assert failed == []

    def test_format_duration_seconds(self, health_monitor):
        """Should format seconds correctly."""
        assert health_monitor._format_duration(30) == "30s"
        assert health_monitor._format_duration(45) == "45s"

    def test_format_duration_minutes(self, health_monitor):
        """Should format minutes correctly."""
        assert health_monitor._format_duration(60) == "1m 0s"
        assert health_monitor._format_duration(90) == "1m 30s"
        assert health_monitor._format_duration(150) == "2m 30s"

    def test_format_duration_hours(self, health_monitor):
        """Should format hours correctly."""
        assert health_monitor._format_duration(3600) == "1h 0m"
        assert health_monitor._format_duration(3660) == "1h 1m"
        assert health_monitor._format_duration(7200) == "2h 0m"


# ============================================================================
# Status Tests
# ============================================================================


class TestGetStatus:
    """Tests for get_status method."""

    def test_get_status_initial(self, health_monitor):
        """Status should reflect initial state."""
        status = health_monitor.get_status()

        assert status["running"] is False
        assert status["last_status"] == "ok"
        assert status["degraded_since"] is None
        assert status["check_interval"] == 1

    @pytest.mark.asyncio
    async def test_get_status_running(self, health_monitor):
        """Status should reflect running state."""
        with patch.object(health_monitor, "_monitor_loop", new_callable=AsyncMock):
            await health_monitor.start()

            status = health_monitor.get_status()

            assert status["running"] is True

            await health_monitor.stop()

    def test_get_status_degraded(self, health_monitor):
        """Status should include degraded_since when degraded."""
        health_monitor.last_status = "degraded"
        health_monitor.degraded_since = datetime(2025, 2, 3, 10, 30, 0)

        status = health_monitor.get_status()

        assert status["last_status"] == "degraded"
        assert status["degraded_since"] == "2025-02-03T10:30:00"


# ============================================================================
# Global Instance Tests
# ============================================================================


class TestGlobalInstance:
    """Tests for global health monitor instance management."""

    def test_init_health_monitor(self):
        """init_health_monitor should create global instance."""
        monitor = init_health_monitor(check_interval=120)

        assert monitor is not None
        assert monitor.check_interval == 120

    def test_get_health_monitor_before_init(self):
        """get_health_monitor should raise if not initialized."""
        import app.services.health_monitor as hm_module

        # Reset the global instance
        original = hm_module._health_monitor
        hm_module._health_monitor = None

        try:
            with pytest.raises(RuntimeError) as exc_info:
                get_health_monitor()

            assert "not initialized" in str(exc_info.value)
        finally:
            # Restore original
            hm_module._health_monitor = original

    def test_get_health_monitor_after_init(self):
        """get_health_monitor should return initialized instance."""

        monitor = init_health_monitor(check_interval=30)

        try:
            retrieved = get_health_monitor()
            assert retrieved is monitor
            assert retrieved.check_interval == 30
        finally:
            # Clean up by setting to None for other tests
            pass  # Note: Global state persists between tests


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for health monitoring workflow."""

    @pytest.mark.asyncio
    async def test_degradation_and_recovery_workflow(self, health_monitor, mock_event_bus):
        """Test complete workflow: ok -> degraded -> ok."""
        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch("app.services.event_bus.get_event_bus", return_value=mock_event_bus),
        ):
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Initial state: ok
            assert health_monitor.last_status == "ok"

            # Step 1: System goes degraded
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "degraded",
                "components": {"redis": "unavailable"},
            }
            mock_client.get = AsyncMock(return_value=mock_response)

            await health_monitor._check_health()

            assert health_monitor.last_status == "degraded"
            assert health_monitor.degraded_since is not None

            # Step 2: System recovers
            mock_response.json.return_value = {
                "status": "ok",
                "components": {"redis": "ready"},
            }

            await health_monitor._check_health()

            assert health_monitor.last_status == "ok"
            assert health_monitor.degraded_since is None

            # Verify alerts were emitted
            assert mock_event_bus.publish.call_count == 2
