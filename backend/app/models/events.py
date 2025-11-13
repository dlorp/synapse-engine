"""System event data models for real-time event streaming.

This module defines Pydantic models for system events broadcast via WebSocket
to frontend LiveEventFeed components. Events track query routing, model state
changes, CGRAG retrievals, cache operations, errors, and performance alerts.

Author: Backend Architect
Phase: 1 - LiveEventFeed Backend (Task 1.4)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """System event types for classification.

    Event types define the category of system activity being reported:
    - QUERY_ROUTE: Query complexity assessment and model tier selection
    - MODEL_STATE: Model state transitions (active, idle, processing, error)
    - CGRAG: Context retrieval operations and results
    - CACHE: Redis cache hits/misses and performance metrics
    - ERROR: System errors, warnings, and failures
    - PERFORMANCE: Performance threshold alerts (latency, memory)
    - PIPELINE_STAGE_START: Pipeline stage started
    - PIPELINE_STAGE_COMPLETE: Pipeline stage completed
    - PIPELINE_STAGE_FAILED: Pipeline stage failed
    - PIPELINE_COMPLETE: Entire pipeline completed
    - PIPELINE_FAILED: Entire pipeline failed
    - TOPOLOGY_HEALTH_UPDATE: Component health status changed
    - TOPOLOGY_DATAFLOW_UPDATE: Query entered a new component
    """
    QUERY_ROUTE = "query_route"
    MODEL_STATE = "model_state"
    CGRAG = "cgrag"
    CACHE = "cache"
    ERROR = "error"
    PERFORMANCE = "performance"
    PIPELINE_STAGE_START = "pipeline_stage_start"
    PIPELINE_STAGE_COMPLETE = "pipeline_stage_complete"
    PIPELINE_STAGE_FAILED = "pipeline_stage_failed"
    PIPELINE_COMPLETE = "pipeline_complete"
    PIPELINE_FAILED = "pipeline_failed"
    TOPOLOGY_HEALTH_UPDATE = "topology_health_update"
    TOPOLOGY_DATAFLOW_UPDATE = "topology_dataflow_update"


class EventSeverity(str, Enum):
    """Event severity levels for filtering and display.

    Severity levels indicate the importance and urgency of events:
    - INFO: Normal operational events (default)
    - WARNING: Potential issues requiring attention
    - ERROR: Errors requiring immediate attention
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SystemEvent(BaseModel):
    """Base model for all system events broadcast via WebSocket.

    SystemEvent provides a consistent schema for all event types with
    timestamp, classification, severity, and extensible metadata. Events
    are serialized to JSON and sent to all connected WebSocket clients.

    Attributes:
        timestamp: Unix timestamp with milliseconds (float for precision)
        type: Event classification (query_route, model_state, etc.)
        message: Human-readable event description
        severity: Event severity level (info, warning, error)
        metadata: Additional type-specific data (flexible dict)

    Example:
        >>> event = SystemEvent(
        ...     timestamp=1699468800.123,
        ...     type=EventType.QUERY_ROUTE,
        ...     message="Query routed to Q4 tier (complexity: 8.5)",
        ...     severity=EventSeverity.INFO,
        ...     metadata={
        ...         "query_id": "abc123",
        ...         "complexity_score": 8.5,
        ...         "selected_tier": "Q4",
        ...         "estimated_latency_ms": 12000
        ...     }
        ... )
        >>> event.model_dump_json()
        '{"timestamp": 1699468800.123, "type": "query_route", ...}'
    """

    model_config = ConfigDict(
        # Serialize enums as values, use camelCase aliases
        use_enum_values=True,
        populate_by_name=True
    )

    timestamp: float = Field(
        ...,
        description="Unix timestamp with milliseconds precision"
    )
    type: EventType = Field(
        ...,
        description="Event type classification"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Human-readable event description"
    )
    severity: EventSeverity = Field(
        default=EventSeverity.INFO,
        description="Event severity level"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific metadata and context"
    )


class QueryRouteEvent(BaseModel):
    """Specialized event for query routing decisions.

    Captures details about query complexity assessment and model tier
    selection for observability and debugging.

    Attributes:
        query_id: Unique identifier for the query
        complexity_score: Numeric complexity score (0-10+)
        selected_tier: Model tier selected (Q2/Q3/Q4)
        estimated_latency_ms: Expected response time in milliseconds
        routing_reason: Human-readable explanation for tier selection

    Example:
        >>> metadata = QueryRouteEvent(
        ...     query_id="query_abc123",
        ...     complexity_score=3.2,
        ...     selected_tier="Q3",
        ...     estimated_latency_ms=5000,
        ...     routing_reason="Multi-part query with comparison"
        ... ).model_dump()
    """

    query_id: str = Field(..., description="Unique query identifier")
    complexity_score: float = Field(..., description="Complexity score (0-10+)")
    selected_tier: Literal["Q2", "Q3", "Q4"] = Field(..., description="Selected model tier")
    estimated_latency_ms: int = Field(..., description="Expected latency in ms")
    routing_reason: str = Field(..., description="Tier selection explanation")


class ModelStateEvent(BaseModel):
    """Specialized event for model state transitions.

    Tracks changes in model operational state for monitoring and alerting.

    Attributes:
        model_id: Model identifier (e.g., "deepseek_r1_8b_q4km")
        previous_state: Previous state before transition
        current_state: New current state
        reason: Reason for state change
        port: Model server port number (optional)

    Example:
        >>> metadata = ModelStateEvent(
        ...     model_id="deepseek_r1_8b_q4km",
        ...     previous_state="idle",
        ...     current_state="processing",
        ...     reason="Query dispatched to model",
        ...     port=8080
        ... ).model_dump()
    """

    model_id: str = Field(..., description="Model identifier")
    previous_state: str = Field(..., description="Previous state")
    current_state: str = Field(..., description="New current state")
    reason: str = Field(..., description="State transition reason")
    port: Optional[int] = Field(None, description="Model server port")


class CGRAGEvent(BaseModel):
    """Specialized event for CGRAG context retrieval operations.

    Tracks vector search performance and retrieval results for optimization.

    Attributes:
        query_id: Query identifier
        chunks_retrieved: Number of chunks retrieved
        relevance_threshold: Minimum relevance score used
        retrieval_time_ms: Time taken for retrieval in milliseconds
        total_tokens: Total tokens in retrieved context
        cache_hit: Whether retrieval used cached embeddings

    Example:
        >>> metadata = CGRAGEvent(
        ...     query_id="query_abc123",
        ...     chunks_retrieved=5,
        ...     relevance_threshold=0.7,
        ...     retrieval_time_ms=45,
        ...     total_tokens=1500,
        ...     cache_hit=True
        ... ).model_dump()
    """

    query_id: str = Field(..., description="Query identifier")
    chunks_retrieved: int = Field(..., description="Number of chunks retrieved")
    relevance_threshold: float = Field(..., description="Minimum relevance score")
    retrieval_time_ms: int = Field(..., description="Retrieval time in ms")
    total_tokens: int = Field(..., description="Total tokens in context")
    cache_hit: bool = Field(..., description="Cache hit status")


class CacheEvent(BaseModel):
    """Specialized event for Redis cache operations.

    Tracks cache performance metrics for monitoring hit rates and latency.

    Attributes:
        operation: Cache operation type (hit, miss, set, evict)
        key: Cache key accessed
        hit: Whether operation was a cache hit
        latency_ms: Operation latency in milliseconds
        size_bytes: Size of cached value in bytes (optional)

    Example:
        >>> metadata = CacheEvent(
        ...     operation="hit",
        ...     key="query:abc123:response",
        ...     hit=True,
        ...     latency_ms=2,
        ...     size_bytes=4096
        ... ).model_dump()
    """

    operation: Literal["hit", "miss", "set", "evict"] = Field(..., description="Cache operation")
    key: str = Field(..., description="Cache key")
    hit: bool = Field(..., description="Cache hit status")
    latency_ms: int = Field(..., description="Operation latency in ms")
    size_bytes: Optional[int] = Field(None, description="Value size in bytes")


class ErrorEvent(BaseModel):
    """Specialized event for system errors and warnings.

    Captures error details for alerting and debugging.

    Attributes:
        error_type: Error class name (e.g., "ModelUnavailableError")
        error_message: Human-readable error description
        component: System component where error occurred
        stack_trace: Optional stack trace for debugging
        recovery_action: Suggested recovery action (optional)

    Example:
        >>> metadata = ErrorEvent(
        ...     error_type="ModelUnavailableError",
        ...     error_message="Q4 model not responding",
        ...     component="ModelManager",
        ...     recovery_action="Retry with Q3 tier"
        ... ).model_dump()
    """

    error_type: str = Field(..., description="Error class name")
    error_message: str = Field(..., description="Error description")
    component: str = Field(..., description="Component where error occurred")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    recovery_action: Optional[str] = Field(None, description="Suggested recovery")


class PerformanceEvent(BaseModel):
    """Specialized event for performance threshold alerts.

    Alerts when system metrics exceed defined thresholds.

    Attributes:
        metric_name: Name of metric (e.g., "query_latency_ms")
        current_value: Current metric value
        threshold_value: Threshold that was exceeded
        component: Component being monitored
        action_required: Whether manual intervention is needed

    Example:
        >>> metadata = PerformanceEvent(
        ...     metric_name="query_latency_ms",
        ...     current_value=18000,
        ...     threshold_value=15000,
        ...     component="Q4_POWERFUL_1",
        ...     action_required=False
        ... ).model_dump()
    """

    metric_name: str = Field(..., description="Metric name")
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold value")
    component: str = Field(..., description="Component being monitored")
    action_required: bool = Field(default=False, description="Manual intervention needed")


class PipelineEvent(BaseModel):
    """Specialized event for query processing pipeline stage updates.

    Tracks real-time progress through query processing stages for visualization.

    Attributes:
        query_id: Unique query identifier
        stage: Pipeline stage name (input, complexity, cgrag, routing, generation, response)
        metadata: Stage-specific metadata (duration_ms, artifacts, model selected, etc.)

    Example:
        >>> metadata = PipelineEvent(
        ...     query_id="550e8400-e29b-41d4-a716-446655440000",
        ...     stage="cgrag",
        ...     metadata={"artifacts_retrieved": 8, "tokens_used": 4500, "duration_ms": 70}
        ... ).model_dump()
    """

    query_id: str = Field(..., description="Unique query identifier")
    stage: Literal["input", "complexity", "cgrag", "routing", "generation", "response"] = Field(
        ...,
        description="Pipeline stage name"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific metadata"
    )
