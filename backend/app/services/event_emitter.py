"""Event emission utilities for system event broadcasting.

This module provides convenience functions for emitting system events from
various services without directly coupling to the EventBus. Services can
import and use these functions to broadcast events for real-time monitoring.

Example Integration:
    # In query router
    from app.services.event_emitter import emit_query_route_event

    await emit_query_route_event(
        query_id="abc123",
        complexity_score=8.5,
        selected_tier="Q4",
        estimated_latency_ms=12000,
        routing_reason="Complex multi-part analysis"
    )

Author: Backend Architect
Phase: 1 - LiveEventFeed Backend (Task 1.4)
"""

from typing import Optional

from app.core.logging import get_logger
from app.models.events import (
    EventType,
    EventSeverity,
    QueryRouteEvent,
    ModelStateEvent,
    CGRAGEvent,
    CacheEvent,
    ErrorEvent,
    PerformanceEvent
)
from app.services.event_bus import get_event_bus

logger = get_logger(__name__)


async def emit_query_route_event(
    query_id: str,
    complexity_score: float,
    selected_tier: str,
    estimated_latency_ms: int,
    routing_reason: str
) -> None:
    """Emit a query routing event.

    Call this when a query is routed to a specific model tier.

    Args:
        query_id: Unique query identifier
        complexity_score: Complexity score (0-10+)
        selected_tier: Model tier selected (Q2/Q3/Q4)
        estimated_latency_ms: Expected response time
        routing_reason: Human-readable routing explanation

    Example:
        await emit_query_route_event(
            query_id="query_abc123",
            complexity_score=3.2,
            selected_tier="Q3",
            estimated_latency_ms=5000,
            routing_reason="Multi-part query with comparison"
        )
    """
    try:
        event_bus = get_event_bus()

        metadata = QueryRouteEvent(
            query_id=query_id,
            complexity_score=complexity_score,
            selected_tier=selected_tier,
            estimated_latency_ms=estimated_latency_ms,
            routing_reason=routing_reason
        )

        await event_bus.publish(
            event_type=EventType.QUERY_ROUTE,
            message=f"Query routed to {selected_tier} tier (complexity: {complexity_score:.1f})",
            severity=EventSeverity.INFO,
            metadata=metadata.model_dump()
        )

    except Exception as e:
        logger.error(f"Failed to emit query route event: {e}")


async def emit_model_state_event(
    model_id: str,
    previous_state: str,
    current_state: str,
    reason: str,
    port: Optional[int] = None
) -> None:
    """Emit a model state change event.

    Call this when a model transitions between states (active, idle, processing, error).

    Args:
        model_id: Model identifier
        previous_state: Previous state
        current_state: New current state
        reason: State transition reason
        port: Optional model server port

    Example:
        await emit_model_state_event(
            model_id="deepseek_r1_8b_q4km",
            previous_state="idle",
            current_state="processing",
            reason="Query dispatched to model",
            port=8080
        )
    """
    try:
        event_bus = get_event_bus()

        metadata = ModelStateEvent(
            model_id=model_id,
            previous_state=previous_state,
            current_state=current_state,
            reason=reason,
            port=port
        )

        # Determine severity based on state
        severity = EventSeverity.INFO
        if current_state == "error":
            severity = EventSeverity.ERROR
        elif current_state in ["warning", "degraded"]:
            severity = EventSeverity.WARNING

        await event_bus.publish(
            event_type=EventType.MODEL_STATE,
            message=f"Model {model_id} state: {previous_state} → {current_state}",
            severity=severity,
            metadata=metadata.model_dump()
        )

    except Exception as e:
        logger.error(f"Failed to emit model state event: {e}")


async def emit_cgrag_event(
    query_id: str,
    chunks_retrieved: int,
    relevance_threshold: float,
    retrieval_time_ms: int,
    total_tokens: int,
    cache_hit: bool
) -> None:
    """Emit a CGRAG context retrieval event.

    Call this after CGRAG retrieves context for a query.

    Args:
        query_id: Query identifier
        chunks_retrieved: Number of chunks retrieved
        relevance_threshold: Minimum relevance score used
        retrieval_time_ms: Retrieval time in milliseconds
        total_tokens: Total tokens in retrieved context
        cache_hit: Whether retrieval used cached embeddings

    Example:
        await emit_cgrag_event(
            query_id="query_abc123",
            chunks_retrieved=5,
            relevance_threshold=0.7,
            retrieval_time_ms=45,
            total_tokens=1500,
            cache_hit=True
        )
    """
    try:
        event_bus = get_event_bus()

        metadata = CGRAGEvent(
            query_id=query_id,
            chunks_retrieved=chunks_retrieved,
            relevance_threshold=relevance_threshold,
            retrieval_time_ms=retrieval_time_ms,
            total_tokens=total_tokens,
            cache_hit=cache_hit
        )

        # Determine severity based on performance
        severity = EventSeverity.INFO
        if retrieval_time_ms > 100:  # Over 100ms target
            severity = EventSeverity.WARNING

        cache_status = "cached" if cache_hit else "fresh"

        await event_bus.publish(
            event_type=EventType.CGRAG,
            message=f"Retrieved {chunks_retrieved} chunks ({total_tokens} tokens) in {retrieval_time_ms}ms ({cache_status})",
            severity=severity,
            metadata=metadata.model_dump()
        )

    except Exception as e:
        logger.error(f"Failed to emit CGRAG event: {e}")


async def emit_cache_event(
    operation: str,
    key: str,
    hit: bool,
    latency_ms: int,
    size_bytes: Optional[int] = None
) -> None:
    """Emit a cache operation event.

    Call this for Redis cache operations (hit, miss, set, evict).

    Args:
        operation: Cache operation (hit, miss, set, evict)
        key: Cache key
        hit: Whether operation was a cache hit
        latency_ms: Operation latency in milliseconds
        size_bytes: Optional value size in bytes

    Example:
        await emit_cache_event(
            operation="hit",
            key="query:abc123:response",
            hit=True,
            latency_ms=2,
            size_bytes=4096
        )
    """
    try:
        event_bus = get_event_bus()

        metadata = CacheEvent(
            operation=operation,
            key=key,
            hit=hit,
            latency_ms=latency_ms,
            size_bytes=size_bytes
        )

        status = "HIT" if hit else "MISS"
        size_info = f", {size_bytes} bytes" if size_bytes else ""

        await event_bus.publish(
            event_type=EventType.CACHE,
            message=f"Cache {operation.upper()}: {key} ({status}, {latency_ms}ms{size_info})",
            severity=EventSeverity.INFO,
            metadata=metadata.model_dump()
        )

    except Exception as e:
        logger.error(f"Failed to emit cache event: {e}")


async def emit_error_event(
    error_type: str,
    error_message: str,
    component: str,
    stack_trace: Optional[str] = None,
    recovery_action: Optional[str] = None
) -> None:
    """Emit a system error event.

    Call this when an error occurs that should be visible in monitoring.

    Args:
        error_type: Error class name
        error_message: Human-readable error description
        component: Component where error occurred
        stack_trace: Optional stack trace
        recovery_action: Optional suggested recovery action

    Example:
        await emit_error_event(
            error_type="ModelUnavailableError",
            error_message="Q4 model not responding",
            component="ModelManager",
            recovery_action="Retry with Q3 tier"
        )
    """
    try:
        event_bus = get_event_bus()

        metadata = ErrorEvent(
            error_type=error_type,
            error_message=error_message,
            component=component,
            stack_trace=stack_trace,
            recovery_action=recovery_action
        )

        await event_bus.publish(
            event_type=EventType.ERROR,
            message=f"ERROR in {component}: {error_message}",
            severity=EventSeverity.ERROR,
            metadata=metadata.model_dump()
        )

    except Exception as e:
        logger.error(f"Failed to emit error event: {e}")


async def emit_performance_event(
    metric_name: str,
    current_value: float,
    threshold_value: float,
    component: str,
    action_required: bool = False
) -> None:
    """Emit a performance threshold alert event.

    Call this when a performance metric exceeds defined thresholds.

    Args:
        metric_name: Name of metric (e.g., "query_latency_ms")
        current_value: Current metric value
        threshold_value: Threshold that was exceeded
        component: Component being monitored
        action_required: Whether manual intervention is needed

    Example:
        await emit_performance_event(
            metric_name="query_latency_ms",
            current_value=18000,
            threshold_value=15000,
            component="Q4_POWERFUL_1",
            action_required=False
        )
    """
    try:
        event_bus = get_event_bus()

        metadata = PerformanceEvent(
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            component=component,
            action_required=action_required
        )

        severity = EventSeverity.ERROR if action_required else EventSeverity.WARNING

        await event_bus.publish(
            event_type=EventType.PERFORMANCE,
            message=f"Performance alert: {metric_name} = {current_value:.1f} (threshold: {threshold_value:.1f}) in {component}",
            severity=severity,
            metadata=metadata.model_dump()
        )

    except Exception as e:
        logger.error(f"Failed to emit performance event: {e}")
