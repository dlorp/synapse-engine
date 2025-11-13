"""System topology and health data models.

This module defines Pydantic models for the system architecture topology,
component health metrics, and data flow path visualization. Used by the
Dashboard's System Architecture Diagram to render interactive node-based
visualizations with React Flow.

Author: Backend Architect
Phase: 4 - Dashboard Features (Component 4)
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComponentNode(BaseModel):
    """System component node for architecture topology.

    Represents a single component in the S.Y.N.A.P.S.E. ENGINE system
    architecture with health status and metadata for visualization.

    Attributes:
        id: Unique identifier (e.g., "orchestrator", "q2_fast_1", "faiss_index")
        type: Component category (orchestrator, model, service, storage)
        label: Human-readable display name
        status: Current health status
        metadata: Additional component info (version, uptime, memory, etc.)
        position: Optional x,y coordinates for React Flow layout

    Example:
        >>> node = ComponentNode(
        ...     id="q2_fast_1",
        ...     type="model",
        ...     label="Q2 FAST #1",
        ...     status="healthy",
        ...     metadata={"tier": "Q2", "memory_usage_mb": 2048.5},
        ...     position={"x": 100, "y": 350}
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Unique component identifier")
    type: Literal["orchestrator", "model", "service", "storage"] = Field(
        ..., description="Component category"
    )
    label: str = Field(..., description="Display name")
    status: Literal["healthy", "degraded", "unhealthy", "offline"] = Field(
        ..., description="Health status"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional component info"
    )
    position: Optional[Dict[str, float]] = Field(
        None, description="React Flow position {x, y}"
    )


class ComponentConnection(BaseModel):
    """Connection between system components.

    Represents a directed edge in the system architecture graph with
    connection type, activity status, and throughput metadata.

    Attributes:
        source: Source node ID
        target: Target node ID
        type: Connection category (data_flow, control, dependency)
        label: Optional connection description
        active: Whether connection is currently active (for animation)
        metadata: Connection stats (throughput, latency, etc.)

    Example:
        >>> conn = ComponentConnection(
        ...     source="orchestrator",
        ...     target="q2_fast_1",
        ...     type="data_flow",
        ...     label="Query routing",
        ...     active=True,
        ...     metadata={"throughput_qps": 12.5, "avg_latency_ms": 150}
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: Literal["data_flow", "control", "dependency"] = Field(
        ..., description="Connection category"
    )
    label: Optional[str] = Field(None, description="Connection description")
    active: bool = Field(default=False, description="Currently active")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Connection stats"
    )


class SystemTopology(BaseModel):
    """Complete system architecture topology.

    Aggregates all component nodes and connections with overall health
    status for full system visualization.

    Attributes:
        nodes: List of all system components
        connections: List of all component connections
        last_updated: Timestamp of last topology update
        overall_health: System-wide health status

    Example:
        >>> topology = SystemTopology(
        ...     nodes=[node1, node2],
        ...     connections=[conn1, conn2],
        ...     last_updated=datetime.utcnow(),
        ...     overall_health="healthy"
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    nodes: List[ComponentNode] = Field(..., description="System components")
    connections: List[ComponentConnection] = Field(
        ..., description="Component connections"
    )
    last_updated: datetime = Field(..., description="Last update timestamp")
    overall_health: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="System-wide health status"
    )


class DataFlowPath(BaseModel):
    """Query data flow path through system components.

    Tracks the ordered sequence of components a query traversed with
    timestamps for visualization and latency analysis.

    Attributes:
        query_id: Unique query identifier
        path: Ordered list of node IDs
        timestamps: Map of node_id -> entry timestamp
        status: Current flow status

    Example:
        >>> flow = DataFlowPath(
        ...     query_id="550e8400-e29b-41d4-a716-446655440000",
        ...     path=["orchestrator", "cgrag_engine", "q3_balanced_1"],
        ...     timestamps={
        ...         "orchestrator": datetime.utcnow().isoformat(),
        ...         "cgrag_engine": datetime.utcnow().isoformat(),
        ...         "q3_balanced_1": datetime.utcnow().isoformat()
        ...     },
        ...     status="completed"
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    query_id: str = Field(..., description="Unique query identifier")
    path: List[str] = Field(..., description="Ordered node IDs")
    timestamps: Dict[str, str] = Field(
        ..., description="Node entry timestamps (ISO format)"
    )
    status: Literal["active", "completed", "failed"] = Field(
        ..., description="Flow status"
    )


class HealthMetrics(BaseModel):
    """Component health metrics for monitoring.

    Detailed health metrics for a single system component including
    resource usage and performance indicators.

    Attributes:
        component_id: Component identifier
        status: Health status
        uptime_seconds: Time since component started
        memory_usage_mb: Memory usage in megabytes
        cpu_percent: CPU usage percentage
        error_rate: Percentage of failed operations (0.0-100.0)
        avg_latency_ms: Average operation latency in milliseconds
        last_check: Timestamp of last health check

    Example:
        >>> metrics = HealthMetrics(
        ...     component_id="q2_fast_1",
        ...     status="healthy",
        ...     uptime_seconds=172800,
        ...     memory_usage_mb=2048.5,
        ...     cpu_percent=45.2,
        ...     error_rate=0.5,
        ...     avg_latency_ms=1850.0,
        ...     last_check=datetime.utcnow()
        ... )
    """

    model_config = ConfigDict(populate_by_name=True)

    component_id: str = Field(..., description="Component identifier")
    status: Literal["healthy", "degraded", "unhealthy", "offline"] = Field(
        ..., description="Health status"
    )
    uptime_seconds: int = Field(..., description="Uptime in seconds")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    error_rate: float = Field(..., description="Error rate (0.0-100.0)")
    avg_latency_ms: float = Field(..., description="Average latency in ms")
    last_check: datetime = Field(..., description="Last health check time")
