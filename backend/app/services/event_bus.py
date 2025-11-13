"""Event Bus Service for Real-Time System Event Broadcasting.

This module provides a publish-subscribe event bus for broadcasting system
events to WebSocket clients. It decouples event producers (services) from
consumers (WebSocket connections) using an async queue-based architecture.

The event bus enables:
- Asynchronous event publishing from any service
- Multiple concurrent subscribers (WebSocket connections)
- Event filtering by type and severity
- Rate limiting to prevent client overwhelm
- Graceful handling of slow/disconnected clients

Author: Backend Architect
Phase: 1 - LiveEventFeed Backend (Task 1.4)
"""

import asyncio
import time
from collections import deque
from datetime import datetime
from typing import AsyncIterator, Deque, List, Optional, Set

from app.core.logging import get_logger
from app.models.events import (
    EventSeverity,
    EventType,
    SystemEvent,
    QueryRouteEvent,
    ModelStateEvent,
    CGRAGEvent,
    CacheEvent,
    ErrorEvent,
    PerformanceEvent
)

logger = get_logger(__name__)


class EventBus:
    """Async event bus for broadcasting system events via pub/sub pattern.

    The EventBus maintains a queue of system events and allows multiple
    subscribers to consume events asynchronously. It provides:

    - Thread-safe event publishing from any context
    - Multiple concurrent subscribers without blocking
    - Event buffering for new subscribers (last N events)
    - Rate limiting per subscriber (max events/second)
    - Automatic cleanup of dead subscribers

    Architecture:
        Producer (Service) -> publish() -> Queue -> subscribe() -> Consumer (WebSocket)

    Example Usage:
        # In a service (producer)
        await event_bus.publish(SystemEvent(
            timestamp=time.time(),
            type=EventType.QUERY_ROUTE,
            message="Query routed to Q4",
            metadata={"tier": "Q4"}
        ))

        # In a WebSocket handler (consumer)
        async for event in event_bus.subscribe():
            await websocket.send_json(event.model_dump())

    Attributes:
        _queue: AsyncIO queue for event distribution
        _subscribers: Set of active subscriber queues
        _event_history: Circular buffer of recent events
        _history_size: Maximum events to buffer for new subscribers
        _lock: AsyncIO lock for thread-safe operations
    """

    def __init__(self, history_size: int = 100, max_queue_size: int = 1000):
        """Initialize event bus with configurable buffering.

        Args:
            history_size: Number of recent events to buffer for new subscribers
            max_queue_size: Maximum events in queue before blocking publishers
        """
        self._queue: asyncio.Queue[SystemEvent] = asyncio.Queue(maxsize=max_queue_size)
        self._subscribers: Set[asyncio.Queue[SystemEvent]] = set()
        self._event_history: Deque[SystemEvent] = deque(maxlen=history_size)
        self._history_size = history_size
        self._lock = asyncio.Lock()
        self._broadcast_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            f"EventBus initialized (history_size={history_size}, "
            f"max_queue_size={max_queue_size})"
        )

    async def start(self) -> None:
        """Start the event bus broadcast loop.

        Must be called during application startup to begin processing events.
        Creates a background task that continuously broadcasts events from the
        main queue to all subscriber queues.
        """
        if self._running:
            logger.warning("EventBus already running, ignoring start request")
            return

        self._running = True
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("EventBus started - broadcast loop running")

    async def stop(self) -> None:
        """Stop the event bus and clean up resources.

        Cancels the broadcast task and clears all subscriber queues. Should
        be called during application shutdown.
        """
        if not self._running:
            return

        self._running = False

        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass

        # Clear all subscriber queues
        async with self._lock:
            self._subscribers.clear()

        logger.info("EventBus stopped")

    async def publish(
        self,
        event_type: EventType,
        message: str,
        severity: EventSeverity = EventSeverity.INFO,
        metadata: Optional[dict] = None
    ) -> None:
        """Publish a system event to all subscribers.

        Creates a SystemEvent and adds it to the broadcast queue. This method
        is thread-safe and can be called from any async context. If the queue
        is full, it will block until space is available (backpressure).

        Args:
            event_type: Type of event (QUERY_ROUTE, MODEL_STATE, etc.)
            message: Human-readable event description
            severity: Event severity level (INFO, WARNING, ERROR)
            metadata: Optional type-specific metadata dictionary

        Example:
            await event_bus.publish(
                event_type=EventType.QUERY_ROUTE,
                message="Query routed to Q4 tier",
                severity=EventSeverity.INFO,
                metadata={
                    "query_id": "abc123",
                    "complexity_score": 8.5,
                    "selected_tier": "Q4"
                }
            )
        """
        event = SystemEvent(
            timestamp=time.time(),
            type=event_type,
            message=message,
            severity=severity,
            metadata=metadata or {}
        )

        try:
            # Add to main queue (blocks if full - backpressure)
            await asyncio.wait_for(
                self._queue.put(event),
                timeout=5.0  # Don't block forever
            )

            # Add to history buffer for new subscribers
            self._event_history.append(event)

            logger.debug(
                f"Event published: {event_type.value} - {message}",
                extra={"event_type": event_type.value, "severity": severity.value}
            )

        except asyncio.TimeoutError:
            logger.error(
                f"Failed to publish event (queue full): {event_type.value} - {message}",
                extra={"event_type": event_type.value}
            )

    async def publish_event(self, event: SystemEvent) -> None:
        """Publish a pre-constructed SystemEvent.

        Alternative to publish() when you already have a SystemEvent instance.
        Useful when using specialized event models like QueryRouteEvent.

        Args:
            event: Pre-constructed SystemEvent instance

        Example:
            route_metadata = QueryRouteEvent(
                query_id="abc123",
                complexity_score=8.5,
                selected_tier="Q4",
                estimated_latency_ms=12000,
                routing_reason="Complex multi-part analysis"
            )
            event = SystemEvent(
                timestamp=time.time(),
                type=EventType.QUERY_ROUTE,
                message="Query routed to Q4 tier",
                metadata=route_metadata.model_dump()
            )
            await event_bus.publish_event(event)
        """
        try:
            await asyncio.wait_for(
                self._queue.put(event),
                timeout=5.0
            )
            self._event_history.append(event)

            logger.debug(
                f"Event published: {event.type} - {event.message}",
                extra={"event_type": event.type, "severity": event.severity}
            )

        except asyncio.TimeoutError:
            logger.error(
                f"Failed to publish event (queue full): {event.type} - {event.message}",
                extra={"event_type": event.type}
            )

    async def emit_pipeline_event(
        self,
        query_id: str,
        stage: str,
        event_type: EventType,
        metadata: Optional[dict] = None
    ) -> None:
        """Emit a pipeline stage event.

        Convenience method for publishing pipeline-specific events with
        consistent formatting and metadata structure.

        Args:
            query_id: Unique query identifier
            stage: Pipeline stage name (input, complexity, cgrag, etc.)
            event_type: Pipeline event type (PIPELINE_STAGE_START, etc.)
            metadata: Optional stage-specific metadata

        Example:
            await event_bus.emit_pipeline_event(
                query_id="abc123",
                stage="cgrag",
                event_type=EventType.PIPELINE_STAGE_COMPLETE,
                metadata={"artifacts_retrieved": 8, "tokens_used": 4500}
            )
        """
        # Map event types to messages
        event_messages = {
            EventType.PIPELINE_STAGE_START: f"Pipeline stage started: {stage}",
            EventType.PIPELINE_STAGE_COMPLETE: f"Pipeline stage completed: {stage}",
            EventType.PIPELINE_STAGE_FAILED: f"Pipeline stage failed: {stage}",
            EventType.PIPELINE_COMPLETE: "Query pipeline completed",
            EventType.PIPELINE_FAILED: "Query pipeline failed"
        }

        message = event_messages.get(event_type, f"Pipeline event: {stage}")

        # Build event metadata
        event_metadata = {
            "query_id": query_id,
            "stage": stage
        }
        if metadata:
            event_metadata.update(metadata)

        # Determine severity
        severity = EventSeverity.INFO
        if event_type in [EventType.PIPELINE_STAGE_FAILED, EventType.PIPELINE_FAILED]:
            severity = EventSeverity.ERROR

        # Publish event
        await self.publish(
            event_type=event_type,
            message=message,
            severity=severity,
            metadata=event_metadata
        )

    async def subscribe(
        self,
        event_types: Optional[Set[EventType]] = None,
        min_severity: EventSeverity = EventSeverity.INFO
    ) -> AsyncIterator[SystemEvent]:
        """Subscribe to system events with optional filtering.

        Creates a new subscriber queue and yields events as they arrive.
        Sends historical events immediately upon subscription, then streams
        new events in real-time. Automatically unsubscribes when iteration stops.

        Args:
            event_types: Optional set of event types to receive (None = all)
            min_severity: Minimum severity level to receive (filters out lower)

        Yields:
            SystemEvent instances matching filter criteria

        Example:
            # Subscribe to all events
            async for event in event_bus.subscribe():
                await websocket.send_json(event.model_dump())

            # Subscribe to errors only
            async for event in event_bus.subscribe(
                event_types={EventType.ERROR},
                min_severity=EventSeverity.ERROR
            ):
                await websocket.send_json(event.model_dump())

        Raises:
            asyncio.CancelledError: When subscriber is cancelled/disconnected
        """
        # Create subscriber queue
        subscriber_queue: asyncio.Queue[SystemEvent] = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._subscribers.add(subscriber_queue)

        subscriber_count = len(self._subscribers)
        logger.info(f"New subscriber connected (total: {subscriber_count})")

        try:
            # Send historical events on connection
            for event in self._event_history:
                if self._should_send_event(event, event_types, min_severity):
                    try:
                        await asyncio.wait_for(
                            subscriber_queue.put(event),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning("Timeout sending historical event to new subscriber")
                        break

            # Stream new events
            while self._running:
                try:
                    event = await subscriber_queue.get()

                    if self._should_send_event(event, event_types, min_severity):
                        yield event

                except asyncio.CancelledError:
                    logger.info("Subscriber cancelled")
                    raise  # Re-raise to trigger finally block

                except Exception as e:
                    logger.error(f"Error in subscriber loop: {e}", exc_info=True)
                    break

        except asyncio.CancelledError:
            logger.info("Subscriber async generator cancelled")
            raise

        except Exception as e:
            logger.error(f"Subscriber error: {e}", exc_info=True)

        finally:
            # Clean up subscriber - ALWAYS execute
            async with self._lock:
                if subscriber_queue in self._subscribers:
                    self._subscribers.discard(subscriber_queue)
                    logger.info(f"Subscriber removed from set")
                else:
                    logger.warning(f"Subscriber queue not found in set during cleanup")

            remaining = len(self._subscribers)
            logger.info(f"Subscriber disconnected (remaining: {remaining})")

    async def _broadcast_loop(self) -> None:
        """Background task that broadcasts events to all subscribers.

        Continuously reads events from the main queue and distributes them
        to all active subscriber queues. Handles slow/dead subscribers by
        dropping their queues if they can't keep up.
        """
        logger.info("Event broadcast loop started")

        while self._running:
            try:
                # Get next event from main queue
                event = await self._queue.get()

                # Broadcast to all subscribers
                async with self._lock:
                    dead_subscribers = []

                    for subscriber_queue in self._subscribers:
                        try:
                            # Non-blocking put with timeout (drop slow clients)
                            await asyncio.wait_for(
                                subscriber_queue.put(event),
                                timeout=0.1  # 100ms max per subscriber
                            )
                        except asyncio.TimeoutError:
                            # Subscriber is too slow - mark for removal
                            logger.warning("Subscriber too slow - dropping")
                            dead_subscribers.append(subscriber_queue)
                        except Exception as e:
                            logger.error(f"Error broadcasting to subscriber: {e}")
                            dead_subscribers.append(subscriber_queue)

                    # Remove dead subscribers
                    for dead in dead_subscribers:
                        self._subscribers.discard(dead)

            except asyncio.CancelledError:
                logger.info("Broadcast loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)  # Prevent tight error loop

        logger.info("Event broadcast loop stopped")

    def _should_send_event(
        self,
        event: SystemEvent,
        event_types: Optional[Set[EventType]],
        min_severity: EventSeverity
    ) -> bool:
        """Check if event matches subscriber filters.

        Args:
            event: Event to check
            event_types: Optional set of allowed event types
            min_severity: Minimum severity level

        Returns:
            True if event should be sent to subscriber
        """
        # Filter by event type
        if event_types and event.type not in event_types:
            return False

        # Filter by severity
        severity_order = {
            EventSeverity.INFO: 0,
            EventSeverity.WARNING: 1,
            EventSeverity.ERROR: 2
        }

        if severity_order[event.severity] < severity_order[min_severity]:
            return False

        return True

    def get_stats(self) -> dict:
        """Get event bus statistics.

        Returns:
            Dictionary with keys:
                - active_subscribers: Number of connected subscribers
                - queue_size: Current main queue size
                - history_size: Number of events in history buffer
                - running: Whether broadcast loop is active
        """
        return {
            "active_subscribers": len(self._subscribers),
            "queue_size": self._queue.qsize(),
            "history_size": len(self._event_history),
            "running": self._running
        }


# Global event bus instance (initialized in main.py lifespan)
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        Global EventBus instance

    Raises:
        RuntimeError: If event bus not initialized
    """
    if _event_bus is None:
        raise RuntimeError("EventBus not initialized - call init_event_bus() first")
    return _event_bus


def init_event_bus(history_size: int = 100, max_queue_size: int = 1000) -> EventBus:
    """Initialize the global event bus instance.

    Should be called during application startup (in lifespan context).

    Args:
        history_size: Number of events to buffer for new subscribers
        max_queue_size: Maximum main queue size

    Returns:
        Initialized EventBus instance
    """
    global _event_bus
    _event_bus = EventBus(history_size=history_size, max_queue_size=max_queue_size)
    return _event_bus
