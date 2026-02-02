"""Comprehensive tests for EventBus service.

Tests cover:
- EventBus initialization and lifecycle (start/stop)
- Event publishing (publish, publish_event, emit_pipeline_event)
- Subscriber management (subscribe, unsubscribe, filtering)
- Event history buffer
- Concurrent subscribers
- Error handling and edge cases
- Statistics reporting
"""

import asyncio
import pytest
import time
from typing import Set

from app.models.events import EventSeverity, EventType, SystemEvent
from app.services.event_bus import (
    EventBus,
    get_event_bus,
    init_event_bus,
)


class TestEventBusInitialization:
    """Tests for EventBus initialization and configuration."""

    def test_init_with_defaults(self):
        """EventBus initializes with default parameters."""
        bus = EventBus()
        stats = bus.get_stats()

        assert stats["active_subscribers"] == 0
        assert stats["queue_size"] == 0
        assert stats["history_size"] == 0
        assert stats["running"] is False

    def test_init_with_custom_params(self):
        """EventBus accepts custom history_size and max_queue_size."""
        bus = EventBus(history_size=50, max_queue_size=500)
        # Verify internal state (accessing private attrs for testing)
        assert bus._history_size == 50
        assert bus._queue.maxsize == 500

    @pytest.mark.asyncio
    async def test_start_creates_broadcast_task(self):
        """Starting EventBus creates background broadcast task."""
        bus = EventBus()

        assert bus._running is False
        assert bus._broadcast_task is None

        await bus.start()

        assert bus._running is True
        assert bus._broadcast_task is not None
        assert not bus._broadcast_task.done()

        await bus.stop()

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self):
        """Calling start() twice doesn't create duplicate tasks."""
        bus = EventBus()
        await bus.start()

        first_task = bus._broadcast_task
        await bus.start()  # Should be ignored

        assert bus._broadcast_task is first_task
        await bus.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_broadcast_task(self):
        """Stopping EventBus cancels the broadcast task."""
        bus = EventBus()
        await bus.start()

        task = bus._broadcast_task
        await bus.stop()

        assert bus._running is False
        assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_stop_clears_subscribers(self):
        """Stopping EventBus clears all subscriber queues."""
        bus = EventBus()
        await bus.start()

        # Add a fake subscriber
        async with bus._lock:
            bus._subscribers.add(asyncio.Queue())

        assert len(bus._subscribers) == 1

        await bus.stop()

        assert len(bus._subscribers) == 0


class TestEventPublishing:
    """Tests for event publishing methods."""

    @pytest.mark.asyncio
    async def test_publish_creates_event(self, clean_event_bus: EventBus):
        """publish() creates SystemEvent and adds to queue."""
        await clean_event_bus.publish(
            event_type=EventType.QUERY_ROUTE,
            message="Test query routed",
            severity=EventSeverity.INFO,
            metadata={"query_id": "test-123"},
        )

        # Give time for event to be processed
        await asyncio.sleep(0.05)

        stats = clean_event_bus.get_stats()
        assert stats["history_size"] == 1

    @pytest.mark.asyncio
    async def test_publish_adds_to_history(self, clean_event_bus: EventBus):
        """Published events are added to history buffer."""
        for i in range(5):
            await clean_event_bus.publish(
                event_type=EventType.MODEL_STATE, message=f"Model state change {i}"
            )

        await asyncio.sleep(0.05)

        assert len(clean_event_bus._event_history) == 5

    @pytest.mark.asyncio
    async def test_publish_respects_history_limit(self):
        """History buffer respects max size limit."""
        bus = EventBus(history_size=3, max_queue_size=100)
        await bus.start()

        try:
            for i in range(10):
                await bus.publish(
                    event_type=EventType.MODEL_STATE, message=f"Event {i}"
                )

            await asyncio.sleep(0.05)

            # Only last 3 events should be in history
            assert len(bus._event_history) == 3
            messages = [e.message for e in bus._event_history]
            assert messages == ["Event 7", "Event 8", "Event 9"]
        finally:
            await bus.stop()

    @pytest.mark.asyncio
    async def test_publish_event_with_preconstructed_event(
        self, clean_event_bus: EventBus
    ):
        """publish_event() accepts pre-constructed SystemEvent."""
        event = SystemEvent(
            timestamp=time.time(),
            type=EventType.ERROR,
            message="Test error event",
            severity=EventSeverity.ERROR,
            metadata={"error_code": 500},
        )

        await clean_event_bus.publish_event(event)
        await asyncio.sleep(0.05)

        assert len(clean_event_bus._event_history) == 1
        assert clean_event_bus._event_history[0].message == "Test error event"
        assert clean_event_bus._event_history[0].severity == EventSeverity.ERROR

    @pytest.mark.asyncio
    async def test_emit_pipeline_event_start(self, clean_event_bus: EventBus):
        """emit_pipeline_event() creates proper pipeline start events."""
        await clean_event_bus.emit_pipeline_event(
            query_id="pipeline-test",
            stage="complexity",
            event_type=EventType.PIPELINE_STAGE_START,
        )

        await asyncio.sleep(0.05)

        event = clean_event_bus._event_history[0]
        assert event.type == EventType.PIPELINE_STAGE_START
        assert "Pipeline stage started: complexity" in event.message
        assert event.metadata["query_id"] == "pipeline-test"
        assert event.metadata["stage"] == "complexity"
        assert event.severity == EventSeverity.INFO

    @pytest.mark.asyncio
    async def test_emit_pipeline_event_failed_has_error_severity(
        self, clean_event_bus: EventBus
    ):
        """Failed pipeline events have ERROR severity."""
        await clean_event_bus.emit_pipeline_event(
            query_id="pipeline-fail",
            stage="generation",
            event_type=EventType.PIPELINE_STAGE_FAILED,
            metadata={"error": "Model timeout"},
        )

        await asyncio.sleep(0.05)

        event = clean_event_bus._event_history[0]
        assert event.severity == EventSeverity.ERROR
        assert event.metadata["error"] == "Model timeout"


class TestEventSubscription:
    """Tests for event subscription and filtering."""

    @pytest.mark.asyncio
    async def test_subscriber_receives_events(self, clean_event_bus: EventBus):
        """Subscribers receive published events."""
        received_events = []

        async def subscriber():
            async for event in clean_event_bus.subscribe():
                received_events.append(event)
                if len(received_events) >= 3:
                    break

        # Start subscriber task
        task = asyncio.create_task(subscriber())
        await asyncio.sleep(0.05)  # Let subscriber connect

        # Publish events
        for i in range(3):
            await clean_event_bus.publish(
                event_type=EventType.MODEL_STATE, message=f"Event {i}"
            )

        await asyncio.wait_for(task, timeout=2.0)

        assert len(received_events) == 3

    @pytest.mark.asyncio
    async def test_subscriber_receives_history_on_connect(self):
        """New subscribers receive historical events immediately."""
        bus = EventBus(history_size=5, max_queue_size=100)
        await bus.start()

        try:
            # Publish events BEFORE subscribing
            for i in range(3):
                await bus.publish(
                    event_type=EventType.CGRAG, message=f"Historical event {i}"
                )

            await asyncio.sleep(0.05)

            # Now subscribe and check we get history
            received = []

            async def subscriber():
                async for event in bus.subscribe():
                    received.append(event)
                    if len(received) >= 3:
                        break

            await asyncio.wait_for(subscriber(), timeout=2.0)

            assert len(received) == 3
            assert all("Historical event" in e.message for e in received)
        finally:
            await bus.stop()

    @pytest.mark.asyncio
    async def test_filter_by_event_type(self, clean_event_bus: EventBus):
        """Subscribers can filter events by type."""
        received = []

        async def subscriber():
            async for event in clean_event_bus.subscribe(event_types={EventType.ERROR}):
                received.append(event)
                if len(received) >= 2:
                    break

        task = asyncio.create_task(subscriber())
        await asyncio.sleep(0.05)

        # Publish mixed events
        await clean_event_bus.publish(EventType.MODEL_STATE, "State change")
        await clean_event_bus.publish(EventType.ERROR, "Error 1", EventSeverity.ERROR)
        await clean_event_bus.publish(EventType.CGRAG, "CGRAG result")
        await clean_event_bus.publish(EventType.ERROR, "Error 2", EventSeverity.ERROR)

        await asyncio.wait_for(task, timeout=2.0)

        assert len(received) == 2
        assert all(e.type == EventType.ERROR for e in received)

    @pytest.mark.asyncio
    async def test_filter_by_severity(self, clean_event_bus: EventBus):
        """Subscribers can filter by minimum severity."""
        received = []

        async def subscriber():
            async for event in clean_event_bus.subscribe(
                min_severity=EventSeverity.WARNING
            ):
                received.append(event)
                if len(received) >= 2:
                    break

        task = asyncio.create_task(subscriber())
        await asyncio.sleep(0.05)

        # Publish events with different severities
        await clean_event_bus.publish(EventType.MODEL_STATE, "Info", EventSeverity.INFO)
        await clean_event_bus.publish(
            EventType.MODEL_STATE, "Warning", EventSeverity.WARNING
        )
        await clean_event_bus.publish(
            EventType.MODEL_STATE, "Info 2", EventSeverity.INFO
        )
        await clean_event_bus.publish(EventType.ERROR, "Error", EventSeverity.ERROR)

        await asyncio.wait_for(task, timeout=2.0)

        assert len(received) == 2
        assert received[0].severity == EventSeverity.WARNING
        assert received[1].severity == EventSeverity.ERROR

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, clean_event_bus: EventBus):
        """Multiple subscribers all receive the same events."""
        received1 = []
        received2 = []

        async def subscriber1():
            async for event in clean_event_bus.subscribe():
                received1.append(event)
                if len(received1) >= 2:
                    break

        async def subscriber2():
            async for event in clean_event_bus.subscribe():
                received2.append(event)
                if len(received2) >= 2:
                    break

        task1 = asyncio.create_task(subscriber1())
        task2 = asyncio.create_task(subscriber2())
        await asyncio.sleep(0.05)

        await clean_event_bus.publish(EventType.CACHE, "Event A")
        await clean_event_bus.publish(EventType.CACHE, "Event B")

        await asyncio.wait_for(asyncio.gather(task1, task2), timeout=2.0)

        assert len(received1) == 2
        assert len(received2) == 2

    @pytest.mark.asyncio
    async def test_subscriber_cleanup_on_disconnect(self, clean_event_bus: EventBus):
        """Subscribers are cleaned up when they disconnect."""

        async def short_subscriber():
            count = 0
            async for event in clean_event_bus.subscribe():
                count += 1
                if count >= 1:
                    break  # Exit early

        assert clean_event_bus.get_stats()["active_subscribers"] == 0

        # Start and complete a subscriber
        task = asyncio.create_task(short_subscriber())
        await asyncio.sleep(0.05)

        # Should have one subscriber
        assert clean_event_bus.get_stats()["active_subscribers"] == 1

        # Publish to trigger subscriber exit
        await clean_event_bus.publish(EventType.MODEL_STATE, "Trigger")

        await asyncio.wait_for(task, timeout=2.0)
        await asyncio.sleep(0.1)  # Allow cleanup

        # Subscriber should be removed
        assert clean_event_bus.get_stats()["active_subscribers"] == 0


class TestShouldSendEvent:
    """Tests for event filtering logic."""

    def test_no_filters_passes_all(self):
        """Without filters, all events pass."""
        bus = EventBus()
        event = SystemEvent(
            timestamp=time.time(),
            type=EventType.CGRAG,
            message="Test",
            severity=EventSeverity.INFO,
        )

        assert bus._should_send_event(event, None, EventSeverity.INFO) is True

    def test_event_type_filter_matches(self):
        """Event type filter allows matching types."""
        bus = EventBus()
        event = SystemEvent(
            timestamp=time.time(),
            type=EventType.ERROR,
            message="Test",
            severity=EventSeverity.ERROR,
        )

        allowed_types: Set[EventType] = {EventType.ERROR, EventType.PERFORMANCE}
        assert bus._should_send_event(event, allowed_types, EventSeverity.INFO) is True

    def test_event_type_filter_blocks(self):
        """Event type filter blocks non-matching types."""
        bus = EventBus()
        event = SystemEvent(
            timestamp=time.time(),
            type=EventType.CGRAG,
            message="Test",
            severity=EventSeverity.INFO,
        )

        allowed_types: Set[EventType] = {EventType.ERROR}
        assert bus._should_send_event(event, allowed_types, EventSeverity.INFO) is False

    def test_severity_filter_allows_higher(self):
        """Severity filter allows events at or above threshold."""
        bus = EventBus()

        error_event = SystemEvent(
            timestamp=time.time(),
            type=EventType.ERROR,
            message="Error",
            severity=EventSeverity.ERROR,
        )

        # ERROR is above WARNING threshold
        assert bus._should_send_event(error_event, None, EventSeverity.WARNING) is True

    def test_severity_filter_blocks_lower(self):
        """Severity filter blocks events below threshold."""
        bus = EventBus()

        info_event = SystemEvent(
            timestamp=time.time(),
            type=EventType.MODEL_STATE,
            message="Info",
            severity=EventSeverity.INFO,
        )

        # INFO is below WARNING threshold
        assert bus._should_send_event(info_event, None, EventSeverity.WARNING) is False


class TestEventBusStats:
    """Tests for statistics reporting."""

    @pytest.mark.asyncio
    async def test_stats_reflect_state(self, clean_event_bus: EventBus):
        """get_stats() returns accurate state information."""
        # Initial state
        stats = clean_event_bus.get_stats()
        assert stats["running"] is True
        assert stats["active_subscribers"] == 0
        assert stats["queue_size"] == 0
        assert stats["history_size"] == 0

        # Add events
        for _ in range(3):
            await clean_event_bus.publish(EventType.MODEL_STATE, "Test")

        await asyncio.sleep(0.05)

        stats = clean_event_bus.get_stats()
        assert stats["history_size"] == 3


class TestGlobalEventBus:
    """Tests for global event bus singleton functions."""

    def test_get_event_bus_without_init_raises(self):
        """get_event_bus() raises if not initialized."""
        # Reset global state
        import app.services.event_bus as eb_module

        original = eb_module._event_bus
        eb_module._event_bus = None

        try:
            with pytest.raises(RuntimeError, match="EventBus not initialized"):
                get_event_bus()
        finally:
            eb_module._event_bus = original

    def test_init_event_bus_creates_instance(self):
        """init_event_bus() creates global instance."""
        import app.services.event_bus as eb_module

        original = eb_module._event_bus
        eb_module._event_bus = None

        try:
            bus = init_event_bus(history_size=25, max_queue_size=250)
            assert bus is not None
            assert eb_module._event_bus is bus
            assert bus._history_size == 25
        finally:
            eb_module._event_bus = original


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_stop_without_start_is_safe(self):
        """Calling stop() on unstarted bus doesn't crash."""
        bus = EventBus()
        await bus.stop()  # Should not raise
        assert bus._running is False

    @pytest.mark.asyncio
    async def test_publish_with_empty_metadata(self, clean_event_bus: EventBus):
        """Publishing with None metadata uses empty dict."""
        await clean_event_bus.publish(
            event_type=EventType.MODEL_STATE, message="No metadata", metadata=None
        )

        await asyncio.sleep(0.05)

        event = clean_event_bus._event_history[0]
        assert event.metadata == {}

    @pytest.mark.asyncio
    async def test_concurrent_publish(self, clean_event_bus: EventBus):
        """Multiple concurrent publishes don't corrupt state."""

        async def publisher(prefix: str):
            for i in range(10):
                await clean_event_bus.publish(
                    event_type=EventType.MODEL_STATE, message=f"{prefix}-{i}"
                )

        # Run multiple publishers concurrently
        await asyncio.gather(publisher("A"), publisher("B"), publisher("C"))

        await asyncio.sleep(0.1)

        # All 30 events should be published (though only last 50 in history)
        assert len(clean_event_bus._event_history) == 30

    @pytest.mark.asyncio
    async def test_slow_subscriber_gets_dropped(self):
        """Slow subscribers that can't keep up are dropped."""
        bus = EventBus(history_size=10, max_queue_size=100)
        await bus.start()

        try:
            # Create a slow subscriber that blocks
            slow_queue: asyncio.Queue[SystemEvent] = asyncio.Queue(maxsize=1)

            async with bus._lock:
                bus._subscribers.add(slow_queue)

            # Fill the slow subscriber's queue
            await slow_queue.put(
                SystemEvent(
                    timestamp=time.time(),
                    type=EventType.MODEL_STATE,
                    message="Blocking event",
                )
            )

            # Publish many events - should eventually drop the slow subscriber
            for i in range(20):
                await bus.publish(EventType.MODEL_STATE, f"Event {i}")

            await asyncio.sleep(2.0)  # Wait for broadcasts and timeout

            # Slow subscriber should have been removed
            async with bus._lock:
                assert slow_queue not in bus._subscribers
        finally:
            await bus.stop()
