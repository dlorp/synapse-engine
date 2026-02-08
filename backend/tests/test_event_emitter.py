"""Tests for the event emitter utility functions.

This module tests the event emission convenience functions that broadcast
system events to the EventBus for real-time monitoring.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from app.models.events import EventSeverity, EventType
from app.services.event_emitter import (
    emit_cache_event,
    emit_cgrag_event,
    emit_error_event,
    emit_model_state_event,
    emit_performance_event,
    emit_query_route_event,
)


class TestEmitQueryRouteEvent:
    """Tests for emit_query_route_event function."""

    async def test_emit_query_route_event_success(self) -> None:
        """Test successful query route event emission."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_query_route_event(
                query_id="test-query-123",
                complexity_score=7.5,
                selected_tier="Q4",
                estimated_latency_ms=12000,
                routing_reason="Complex multi-part analysis",
            )

            mock_bus.publish.assert_called_once()
            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["event_type"] == EventType.QUERY_ROUTE
            assert call_kwargs["severity"] == EventSeverity.INFO
            assert "Q4" in call_kwargs["message"]
            assert "7.5" in call_kwargs["message"]

    async def test_emit_query_route_event_handles_error(self) -> None:
        """Test query route event handles errors gracefully."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_get_bus.side_effect = RuntimeError("EventBus not initialized")

            # Should not raise
            await emit_query_route_event(
                query_id="test-query-123",
                complexity_score=5.0,
                selected_tier="Q3",
                estimated_latency_ms=5000,
                routing_reason="Standard query",
            )


class TestEmitModelStateEvent:
    """Tests for emit_model_state_event function."""

    async def test_emit_model_state_event_info_severity(self) -> None:
        """Test model state event with INFO severity for normal state."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_model_state_event(
                model_id="deepseek_r1_8b",
                previous_state="idle",
                current_state="processing",
                reason="Query dispatched",
                port=8080,
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["event_type"] == EventType.MODEL_STATE
            assert call_kwargs["severity"] == EventSeverity.INFO

    async def test_emit_model_state_event_error_severity(self) -> None:
        """Test model state event with ERROR severity for error state."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_model_state_event(
                model_id="deepseek_r1_8b",
                previous_state="processing",
                current_state="error",
                reason="Model crashed",
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["severity"] == EventSeverity.ERROR

    async def test_emit_model_state_event_warning_severity(self) -> None:
        """Test model state event with WARNING severity for degraded state."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_model_state_event(
                model_id="deepseek_r1_8b",
                previous_state="active",
                current_state="degraded",
                reason="High latency detected",
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["severity"] == EventSeverity.WARNING


class TestEmitCGRAGEvent:
    """Tests for emit_cgrag_event function."""

    async def test_emit_cgrag_event_fast_retrieval(self) -> None:
        """Test CGRAG event with fast retrieval (under threshold)."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_cgrag_event(
                query_id="query-123",
                chunks_retrieved=5,
                relevance_threshold=0.7,
                retrieval_time_ms=45,  # Under 100ms threshold
                total_tokens=1500,
                cache_hit=True,
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["event_type"] == EventType.CGRAG
            assert call_kwargs["severity"] == EventSeverity.INFO
            assert "cached" in call_kwargs["message"]

    async def test_emit_cgrag_event_slow_retrieval(self) -> None:
        """Test CGRAG event with slow retrieval (over threshold)."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_cgrag_event(
                query_id="query-123",
                chunks_retrieved=10,
                relevance_threshold=0.6,
                retrieval_time_ms=150,  # Over 100ms threshold
                total_tokens=3000,
                cache_hit=False,
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["severity"] == EventSeverity.WARNING
            assert "fresh" in call_kwargs["message"]


class TestEmitCacheEvent:
    """Tests for emit_cache_event function."""

    async def test_emit_cache_event_hit(self) -> None:
        """Test cache hit event."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_cache_event(
                operation="hit",
                key="query:abc123:response",
                hit=True,
                latency_ms=2,
                size_bytes=4096,
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["event_type"] == EventType.CACHE
            assert "HIT" in call_kwargs["message"]
            assert "4096" in call_kwargs["message"]

    async def test_emit_cache_event_miss(self) -> None:
        """Test cache miss event."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_cache_event(
                operation="miss",
                key="query:xyz789",
                hit=False,
                latency_ms=1,
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert "MISS" in call_kwargs["message"]


class TestEmitErrorEvent:
    """Tests for emit_error_event function."""

    async def test_emit_error_event_basic(self) -> None:
        """Test basic error event emission."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_error_event(
                error_type="ModelUnavailableError",
                error_message="Q4 model not responding",
                component="ModelManager",
                recovery_action="Retry with Q3 tier",
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["event_type"] == EventType.ERROR
            assert call_kwargs["severity"] == EventSeverity.ERROR
            assert "ModelManager" in call_kwargs["message"]

    async def test_emit_error_event_with_stack_trace(self) -> None:
        """Test error event with stack trace."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_error_event(
                error_type="ValueError",
                error_message="Invalid configuration",
                component="ConfigLoader",
                stack_trace="Traceback (most recent call last):\n  ...",
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            metadata = call_kwargs["metadata"]
            assert metadata["stack_trace"] is not None


class TestEmitPerformanceEvent:
    """Tests for emit_performance_event function."""

    async def test_emit_performance_event_warning(self) -> None:
        """Test performance event without action required (WARNING)."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_performance_event(
                metric_name="query_latency_ms",
                current_value=18000.0,
                threshold_value=15000.0,
                component="Q4_POWERFUL_1",
                action_required=False,
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["event_type"] == EventType.PERFORMANCE
            assert call_kwargs["severity"] == EventSeverity.WARNING

    async def test_emit_performance_event_error(self) -> None:
        """Test performance event with action required (ERROR)."""
        with patch("app.services.event_emitter.get_event_bus") as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.publish = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await emit_performance_event(
                metric_name="memory_usage_percent",
                current_value=95.0,
                threshold_value=80.0,
                component="GPUMemory",
                action_required=True,
            )

            call_kwargs = mock_bus.publish.call_args.kwargs
            assert call_kwargs["severity"] == EventSeverity.ERROR
            assert "95.0" in call_kwargs["message"]
            assert "80.0" in call_kwargs["message"]
