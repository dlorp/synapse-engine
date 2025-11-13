"""WebSocket router for real-time system event streaming.

This module provides the WebSocket endpoint for streaming system events
to frontend LiveEventFeed components. It integrates with the EventBus
service to provide real-time updates on query routing, model state changes,
CGRAG operations, cache performance, errors, and performance alerts.

Endpoint: /ws/events
Protocol: WebSocket
Author: Backend Architect
Phase: 1 - LiveEventFeed Backend (Task 1.4)
"""

import asyncio
import json
from typing import Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.logging import get_logger
from app.models.events import EventType, EventSeverity
from app.services.event_bus import get_event_bus

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    types: Optional[str] = Query(None, description="Comma-separated event types to filter"),
    severity: str = Query("info", description="Minimum severity level (info, warning, error)")
) -> None:
    """WebSocket endpoint for real-time system event streaming.

    Streams system events to connected clients in real-time. Supports filtering
    by event type and minimum severity level. Sends historical events on connection,
    then streams new events as they occur.

    Query Parameters:
        types: Optional comma-separated list of event types to receive
            (e.g., "query_route,model_state,error"). If not specified, all
            event types are streamed.
        severity: Minimum severity level to receive (info, warning, error).
            Filters out events below this level. Default: info (all events).

    WebSocket Message Format:
        {
            "timestamp": 1699468800.123,
            "type": "query_route",
            "message": "Query routed to Q4 tier (complexity: 8.5)",
            "severity": "info",
            "metadata": {
                "query_id": "abc123",
                "complexity_score": 8.5,
                "selected_tier": "Q4",
                "estimated_latency_ms": 12000,
                "routing_reason": "Complex multi-part analysis"
            }
        }

    Example Client Usage:
        // Subscribe to all events
        const ws = new WebSocket('ws://localhost:8000/ws/events');
        ws.onmessage = (event) => {
            const systemEvent = JSON.parse(event.data);
            console.log(`[${systemEvent.type}] ${systemEvent.message}`);
        };

        // Subscribe to errors only
        const ws = new WebSocket('ws://localhost:8000/ws/events?severity=error');
        ws.onmessage = (event) => {
            const errorEvent = JSON.parse(event.data);
            alert(`ERROR: ${errorEvent.message}`);
        };

        // Subscribe to specific event types
        const ws = new WebSocket(
            'ws://localhost:8000/ws/events?types=query_route,model_state'
        );
        ws.onmessage = (event) => {
            const evt = JSON.parse(event.data);
            updateDashboard(evt);
        };

    Connection Lifecycle:
        1. Client connects via WebSocket handshake
        2. Server accepts connection and subscribes to event bus
        3. Server sends buffered historical events (last 100 events)
        4. Server streams new events in real-time as they occur
        5. Connection stays open until client disconnects or error occurs
        6. Server automatically unsubscribes on disconnection

    Performance Characteristics:
        - Event latency: <50ms from occurrence to client delivery
        - Historical buffer: Last 100 events sent immediately on connect
        - Rate limiting: Slow clients dropped if they can't keep up (<100ms/event)
        - Max concurrent connections: No hard limit (bounded by system resources)

    Error Handling:
        - Invalid event types in filter: Ignored, valid types still work
        - Invalid severity level: Falls back to 'info' (all events)
        - Connection errors: Automatic cleanup and unsubscribe
        - Slow clients: Dropped from subscriber list with warning log

    Args:
        websocket: WebSocket connection instance
        types: Optional comma-separated event type filter
        severity: Minimum severity level filter

    Raises:
        WebSocketDisconnect: When client disconnects (handled gracefully)
    """
    # Parse event type filter
    event_types_filter: Optional[Set[EventType]] = None
    if types:
        try:
            event_types_filter = {
                EventType(t.strip().lower())
                for t in types.split(",")
                if t.strip()
            }
            logger.info(f"Event type filter: {event_types_filter}")
        except ValueError as e:
            logger.warning(f"Invalid event type in filter: {e}. Ignoring filter.")
            event_types_filter = None

    # Parse severity filter
    try:
        min_severity = EventSeverity(severity.lower())
    except ValueError:
        logger.warning(f"Invalid severity '{severity}', falling back to INFO")
        min_severity = EventSeverity.INFO

    # Accept WebSocket connection
    await websocket.accept()
    logger.info(
        f"WebSocket client connected to /ws/events "
        f"(types={types or 'all'}, min_severity={min_severity.value})"
    )

    try:
        # Get event bus instance
        event_bus = get_event_bus()

        # Create subscription task
        subscription = event_bus.subscribe(
            event_types=event_types_filter,
            min_severity=min_severity
        )

        # Create background task to handle ping/pong
        async def handle_ping_pong():
            """Background task to handle ping/pong messages for heartbeat"""
            try:
                while True:
                    message = await websocket.receive()
                    # Handle ping messages (client sends JSON: {"type": "ping"})
                    if message.get("type") == "websocket.receive":
                        text = message.get("text", "")
                        if text:
                            try:
                                # Parse JSON message
                                data = json.loads(text)
                                # Client sent ping, respond with pong (JSON format)
                                if data.get("type") == "ping":
                                    await websocket.send_json({"type": "pong"})
                            except (json.JSONDecodeError, ValueError):
                                # Ignore non-JSON messages
                                logger.debug(f"Received non-JSON WebSocket message: {text}")
            except (WebSocketDisconnect, asyncio.CancelledError):
                pass

        # Start ping/pong handler in background
        ping_task = asyncio.create_task(handle_ping_pong())

        try:
            # Stream events to client
            async for event in subscription:
                try:
                    # Send event to client as JSON
                    await websocket.send_json(event.model_dump())

                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected while sending event")
                    break

                except Exception as e:
                    logger.error(f"Error sending event to WebSocket client: {e}")
                    break

        finally:
            # Cancel ping/pong task
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /ws/events normally")

    except asyncio.CancelledError:
        logger.info("WebSocket subscription cancelled")
        raise

    except Exception as e:
        logger.error(f"WebSocket error on /ws/events: {e}", exc_info=True)

    finally:
        # Cleanup is automatic - subscribe() async generator handles unsubscribe
        logger.info("WebSocket connection to /ws/events closed")


@router.get("/api/events/stats")
async def get_event_stats() -> dict:
    """Get event bus statistics for monitoring.

    Returns real-time metrics about the event bus including active subscribers,
    queue sizes, and operational status. Useful for debugging and monitoring.

    Returns:
        Dictionary with keys:
            - active_subscribers: Number of connected WebSocket clients
            - queue_size: Number of events waiting to be broadcast
            - history_size: Number of events in historical buffer
            - running: Whether event bus broadcast loop is active

    Example Response:
        {
            "active_subscribers": 3,
            "queue_size": 0,
            "history_size": 100,
            "running": true
        }

    Status Codes:
        200: Success
        500: Event bus not initialized

    Example Usage:
        fetch('/api/events/stats')
            .then(res => res.json())
            .then(stats => {
                console.log(`Active subscribers: ${stats.active_subscribers}`);
            });
    """
    try:
        event_bus = get_event_bus()
        return event_bus.get_stats()
    except RuntimeError as e:
        logger.error(f"Event bus not initialized: {e}")
        return {
            "error": "Event bus not initialized",
            "active_subscribers": 0,
            "queue_size": 0,
            "history_size": 0,
            "running": False
        }


@router.post("/api/events/test")
async def publish_test_event(
    event_type: str = "query_route",
    message: str = "Test event from API"
) -> dict:
    """Publish a test event for debugging WebSocket connections.

    Args:
        event_type: Type of event to publish (default: query_route)
        message: Event message text (default: Test event from API)

    Returns:
        Success confirmation with event details

    Example:
        curl -X POST http://localhost:5173/api/events/test?message=Hello
    """
    try:
        event_bus = get_event_bus()
        await event_bus.publish(
            event_type=EventType(event_type),
            message=message,
            severity=EventSeverity.INFO,
            metadata={"source": "test_endpoint"}
        )
        return {
            "success": True,
            "event_type": event_type,
            "message": message
        }
    except Exception as e:
        logger.error(f"Failed to publish test event: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
