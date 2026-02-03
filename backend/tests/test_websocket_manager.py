"""Tests for the WebSocket manager service.

Tests WebSocket connection management, log broadcasting, and buffering
functionality for real-time log streaming.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock

from app.services.websocket_manager import WebSocketManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def websocket_manager():
    """Create a fresh WebSocket manager instance for each test."""
    return WebSocketManager(buffer_size=100)


@pytest.fixture
def small_buffer_manager():
    """Create a WebSocket manager with a small buffer for testing overflow."""
    return WebSocketManager(buffer_size=5)


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.fixture
def sample_log_entry():
    """Create a sample log entry for testing."""
    return {
        "timestamp": "2025-02-03T10:30:00Z",
        "model_id": "test_model_1",
        "port": 8080,
        "level": "INFO",
        "message": "Test log message",
    }


# ============================================================================
# Connection Management Tests
# ============================================================================


class TestConnectionManagement:
    """Tests for WebSocket connection lifecycle management."""

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, websocket_manager, mock_websocket):
        """Connect should accept the WebSocket handshake."""
        await websocket_manager.connect(mock_websocket)

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_adds_to_active_connections(
        self, websocket_manager, mock_websocket
    ):
        """Connect should add WebSocket to active connections list."""
        assert len(websocket_manager.active_connections) == 0

        await websocket_manager.connect(mock_websocket)

        assert len(websocket_manager.active_connections) == 1
        assert mock_websocket in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_multiple_connections(self, websocket_manager):
        """Manager should handle multiple concurrent connections."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await websocket_manager.connect(ws1)
        await websocket_manager.connect(ws2)
        await websocket_manager.connect(ws3)

        assert len(websocket_manager.active_connections) == 3
        assert ws1 in websocket_manager.active_connections
        assert ws2 in websocket_manager.active_connections
        assert ws3 in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(
        self, websocket_manager, mock_websocket
    ):
        """Disconnect should remove WebSocket from active connections."""
        await websocket_manager.connect(mock_websocket)
        assert len(websocket_manager.active_connections) == 1

        await websocket_manager.disconnect(mock_websocket)

        assert len(websocket_manager.active_connections) == 0
        assert mock_websocket not in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_handles_nonexistent_connection(
        self, websocket_manager, mock_websocket
    ):
        """Disconnect should handle gracefully if WebSocket was never connected."""
        # Should not raise an error
        await websocket_manager.disconnect(mock_websocket)

        assert len(websocket_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_disconnect_leaves_other_connections(self, websocket_manager):
        """Disconnect should only remove the specified connection."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await websocket_manager.connect(ws1)
        await websocket_manager.connect(ws2)
        assert len(websocket_manager.active_connections) == 2

        await websocket_manager.disconnect(ws1)

        assert len(websocket_manager.active_connections) == 1
        assert ws1 not in websocket_manager.active_connections
        assert ws2 in websocket_manager.active_connections

    def test_get_connection_count(self, websocket_manager):
        """get_connection_count should return correct count."""
        assert websocket_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_get_connection_count_with_connections(
        self, websocket_manager, mock_websocket
    ):
        """get_connection_count should update as connections are added/removed."""
        assert websocket_manager.get_connection_count() == 0

        await websocket_manager.connect(mock_websocket)
        assert websocket_manager.get_connection_count() == 1

        ws2 = AsyncMock()
        await websocket_manager.connect(ws2)
        assert websocket_manager.get_connection_count() == 2

        await websocket_manager.disconnect(mock_websocket)
        assert websocket_manager.get_connection_count() == 1


# ============================================================================
# Log Broadcasting Tests
# ============================================================================


class TestLogBroadcasting:
    """Tests for broadcasting logs to connected clients."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(
        self, websocket_manager, sample_log_entry
    ):
        """Broadcast should send log entry to all connected clients."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await websocket_manager.connect(ws1)
        await websocket_manager.connect(ws2)
        await websocket_manager.connect(ws3)

        await websocket_manager.broadcast_log(sample_log_entry)

        ws1.send_json.assert_called_once_with(sample_log_entry)
        ws2.send_json.assert_called_once_with(sample_log_entry)
        ws3.send_json.assert_called_once_with(sample_log_entry)

    @pytest.mark.asyncio
    async def test_broadcast_stores_in_buffer(
        self, websocket_manager, sample_log_entry
    ):
        """Broadcast should store log entry in buffer."""
        await websocket_manager.broadcast_log(sample_log_entry)

        model_id = sample_log_entry["model_id"]
        assert len(websocket_manager.log_buffer[model_id]) == 1
        assert websocket_manager.log_buffer[model_id][0] == sample_log_entry

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_send(
        self, websocket_manager, sample_log_entry
    ):
        """Broadcast should handle clients that fail to receive."""
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_json.side_effect = Exception("Connection closed")

        await websocket_manager.connect(ws_good)
        await websocket_manager.connect(ws_bad)
        assert websocket_manager.get_connection_count() == 2

        # Broadcast should succeed and remove dead connection
        await websocket_manager.broadcast_log(sample_log_entry)

        # Good connection should receive the message
        ws_good.send_json.assert_called_once_with(sample_log_entry)
        # Bad connection should be removed
        assert websocket_manager.get_connection_count() == 1
        assert ws_bad not in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_removes_multiple_dead_connections(
        self, websocket_manager, sample_log_entry
    ):
        """Broadcast should remove all dead connections."""
        ws_good = AsyncMock()
        ws_bad1 = AsyncMock()
        ws_bad1.send_json.side_effect = Exception("Connection closed")
        ws_bad2 = AsyncMock()
        ws_bad2.send_json.side_effect = Exception("Timeout")

        await websocket_manager.connect(ws_good)
        await websocket_manager.connect(ws_bad1)
        await websocket_manager.connect(ws_bad2)
        assert websocket_manager.get_connection_count() == 3

        await websocket_manager.broadcast_log(sample_log_entry)

        assert websocket_manager.get_connection_count() == 1
        assert ws_good in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(
        self, websocket_manager, sample_log_entry
    ):
        """Broadcast should work even with no connected clients."""
        # Should not raise an error
        await websocket_manager.broadcast_log(sample_log_entry)

        # Log should still be buffered
        model_id = sample_log_entry["model_id"]
        assert len(websocket_manager.log_buffer[model_id]) == 1

    @pytest.mark.asyncio
    async def test_broadcast_unknown_model_id(self, websocket_manager):
        """Broadcast should handle logs without model_id."""
        log_entry = {
            "timestamp": "2025-02-03T10:30:00Z",
            "port": 8080,
            "level": "INFO",
            "message": "No model ID",
        }

        await websocket_manager.broadcast_log(log_entry)

        # Should buffer under "unknown"
        assert len(websocket_manager.log_buffer["unknown"]) == 1


# ============================================================================
# Log Buffer Tests
# ============================================================================


class TestLogBuffer:
    """Tests for log buffering functionality."""

    @pytest.mark.asyncio
    async def test_buffer_size_limit(self, small_buffer_manager):
        """Buffer should not exceed configured size."""
        model_id = "test_model"

        # Add more logs than buffer can hold
        for i in range(10):
            await small_buffer_manager.broadcast_log(
                {
                    "timestamp": f"2025-02-03T10:30:{i:02d}Z",
                    "model_id": model_id,
                    "port": 8080,
                    "level": "INFO",
                    "message": f"Message {i}",
                }
            )

        # Buffer should only contain last 5 messages
        assert len(small_buffer_manager.log_buffer[model_id]) == 5

        # Verify oldest messages were dropped
        messages = [log["message"] for log in small_buffer_manager.log_buffer[model_id]]
        assert messages == [
            "Message 5",
            "Message 6",
            "Message 7",
            "Message 8",
            "Message 9",
        ]

    @pytest.mark.asyncio
    async def test_separate_buffers_per_model(self, websocket_manager):
        """Each model should have its own log buffer."""
        await websocket_manager.broadcast_log(
            {
                "timestamp": "2025-02-03T10:30:00Z",
                "model_id": "model_a",
                "level": "INFO",
                "message": "Model A log",
            }
        )
        await websocket_manager.broadcast_log(
            {
                "timestamp": "2025-02-03T10:30:01Z",
                "model_id": "model_b",
                "level": "INFO",
                "message": "Model B log",
            }
        )

        assert len(websocket_manager.log_buffer["model_a"]) == 1
        assert len(websocket_manager.log_buffer["model_b"]) == 1
        assert websocket_manager.log_buffer["model_a"][0]["message"] == "Model A log"
        assert websocket_manager.log_buffer["model_b"][0]["message"] == "Model B log"

    def test_get_logs_for_specific_model(self, websocket_manager):
        """get_logs should return only logs for specified model."""
        websocket_manager.log_buffer["model_a"].append({"message": "A"})
        websocket_manager.log_buffer["model_b"].append({"message": "B"})

        logs = websocket_manager.get_logs("model_a")

        assert len(logs) == 1
        assert logs[0]["message"] == "A"

    def test_get_logs_all_models(self, websocket_manager):
        """get_logs without model_id should return all logs."""
        websocket_manager.log_buffer["model_a"].append(
            {"timestamp": "2025-02-03T10:30:00Z", "message": "A"}
        )
        websocket_manager.log_buffer["model_b"].append(
            {"timestamp": "2025-02-03T10:30:01Z", "message": "B"}
        )

        logs = websocket_manager.get_logs()

        assert len(logs) == 2

    def test_get_logs_sorted_by_timestamp(self, websocket_manager):
        """get_logs without model_id should return logs sorted by timestamp."""
        websocket_manager.log_buffer["model_a"].append(
            {"timestamp": "2025-02-03T10:30:02Z", "message": "A"}
        )
        websocket_manager.log_buffer["model_b"].append(
            {"timestamp": "2025-02-03T10:30:00Z", "message": "B"}
        )
        websocket_manager.log_buffer["model_c"].append(
            {"timestamp": "2025-02-03T10:30:01Z", "message": "C"}
        )

        logs = websocket_manager.get_logs()

        messages = [log["message"] for log in logs]
        assert messages == ["B", "C", "A"]  # Sorted by timestamp

    def test_get_logs_nonexistent_model(self, websocket_manager):
        """get_logs should return empty list for nonexistent model."""
        logs = websocket_manager.get_logs("nonexistent_model")

        assert logs == []

    def test_clear_logs_specific_model(self, websocket_manager):
        """clear_logs with model_id should only clear that model's logs."""
        websocket_manager.log_buffer["model_a"].append({"message": "A"})
        websocket_manager.log_buffer["model_b"].append({"message": "B"})

        websocket_manager.clear_logs("model_a")

        assert len(websocket_manager.log_buffer["model_a"]) == 0
        assert len(websocket_manager.log_buffer["model_b"]) == 1

    def test_clear_logs_all(self, websocket_manager):
        """clear_logs without model_id should clear all logs."""
        websocket_manager.log_buffer["model_a"].append({"message": "A"})
        websocket_manager.log_buffer["model_b"].append({"message": "B"})

        websocket_manager.clear_logs()

        assert len(websocket_manager.log_buffer) == 0

    def test_clear_logs_nonexistent_model(self, websocket_manager):
        """clear_logs should handle nonexistent model gracefully."""
        # Should not raise an error
        websocket_manager.clear_logs("nonexistent_model")


# ============================================================================
# Buffer Statistics Tests
# ============================================================================


class TestBufferStats:
    """Tests for get_buffer_stats functionality."""

    def test_empty_buffer_stats(self, websocket_manager):
        """Stats should reflect empty buffer state."""
        stats = websocket_manager.get_buffer_stats()

        assert stats["total_models"] == 0
        assert stats["total_logs"] == 0
        assert stats["models"] == {}

    @pytest.mark.asyncio
    async def test_buffer_stats_with_data(self, websocket_manager):
        """Stats should accurately reflect buffer contents."""
        # Add logs for multiple models
        for i in range(5):
            await websocket_manager.broadcast_log(
                {
                    "timestamp": f"2025-02-03T10:30:0{i}Z",
                    "model_id": "model_a",
                    "message": f"A{i}",
                }
            )
        for i in range(3):
            await websocket_manager.broadcast_log(
                {
                    "timestamp": f"2025-02-03T10:31:0{i}Z",
                    "model_id": "model_b",
                    "message": f"B{i}",
                }
            )

        stats = websocket_manager.get_buffer_stats()

        assert stats["total_models"] == 2
        assert stats["total_logs"] == 8
        assert stats["models"]["model_a"] == 5
        assert stats["models"]["model_b"] == 3


# ============================================================================
# Thread Safety Tests
# ============================================================================


class TestThreadSafety:
    """Tests for thread-safe operations."""

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, websocket_manager):
        """Multiple concurrent connections should be handled safely."""
        websockets = [AsyncMock() for _ in range(100)]

        # Connect all at once
        await asyncio.gather(*[websocket_manager.connect(ws) for ws in websockets])

        assert websocket_manager.get_connection_count() == 100

    @pytest.mark.asyncio
    async def test_concurrent_disconnections(self, websocket_manager):
        """Multiple concurrent disconnections should be handled safely."""
        websockets = [AsyncMock() for _ in range(50)]

        # Connect all
        for ws in websockets:
            await websocket_manager.connect(ws)
        assert websocket_manager.get_connection_count() == 50

        # Disconnect all at once
        await asyncio.gather(*[websocket_manager.disconnect(ws) for ws in websockets])

        assert websocket_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_concurrent_broadcasts(self, websocket_manager):
        """Multiple concurrent broadcasts should be handled safely."""
        ws = AsyncMock()
        await websocket_manager.connect(ws)

        # Broadcast multiple logs concurrently
        logs = [
            {
                "timestamp": f"2025-02-03T10:30:{i:02d}Z",
                "model_id": "model",
                "message": f"Message {i}",
            }
            for i in range(50)
        ]

        await asyncio.gather(*[websocket_manager.broadcast_log(log) for log in logs])

        # All logs should be sent and buffered
        assert ws.send_json.call_count == 50
        assert len(websocket_manager.log_buffer["model"]) == 50


# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Tests for WebSocket manager initialization."""

    def test_default_buffer_size(self):
        """Default buffer size should be 500."""
        manager = WebSocketManager()
        assert manager.buffer_size == 500

    def test_custom_buffer_size(self):
        """Custom buffer size should be respected."""
        manager = WebSocketManager(buffer_size=1000)
        assert manager.buffer_size == 1000

    def test_initial_state(self, websocket_manager):
        """Manager should start with empty connections and buffers."""
        assert len(websocket_manager.active_connections) == 0
        assert len(websocket_manager.log_buffer) == 0
        assert websocket_manager.get_connection_count() == 0
