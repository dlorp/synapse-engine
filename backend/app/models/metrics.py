"""Metrics models.

This module defines Pydantic models for system metrics endpoints,
including query metrics, tier performance, resource utilization,
and routing analytics.
"""

from typing import Literal

from pydantic import BaseModel, Field


# Type aliases
TierName = Literal['Q2', 'Q3', 'Q4']
ComplexityLevel = Literal['SIMPLE', 'MODERATE', 'COMPLEX']


class QueryMetrics(BaseModel):
    """Time-series query metrics for 30-minute rolling window.

    Attributes:
        timestamps: List of ISO8601 timestamps for data points
        query_rate: Queries per second at each timestamp
        total_queries: Total queries processed
        avg_latency_ms: Average latency across all queries
        tier_distribution: Count of queries per tier
    """

    timestamps: list[str] = Field(
        ...,
        description="ISO8601 timestamps for data points"
    )
    query_rate: list[float] = Field(
        ...,
        alias="queryRate",
        description="Queries per second at each timestamp"
    )
    total_queries: int = Field(
        ...,
        ge=0,
        alias="totalQueries",
        description="Total queries processed"
    )
    avg_latency_ms: float = Field(
        ...,
        ge=0.0,
        alias="avgLatencyMs",
        description="Average latency in milliseconds"
    )
    tier_distribution: dict[TierName, int] = Field(
        ...,
        alias="tierDistribution",
        description="Query count by tier"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class TierMetrics(BaseModel):
    """Performance metrics for a single model tier.

    Attributes:
        name: Tier name (Q2, Q3, Q4)
        tokens_per_sec: Token generation rate samples
        latency_ms: Latency samples in milliseconds
        request_count: Total requests processed
        error_rate: Error rate (0.0-1.0)
    """

    name: TierName = Field(..., description="Tier name")
    tokens_per_sec: list[float] = Field(
        ...,
        alias="tokensPerSec",
        description="Token generation rate samples"
    )
    latency_ms: list[float] = Field(
        ...,
        alias="latencyMs",
        description="Latency samples in milliseconds"
    )
    request_count: int = Field(
        ...,
        ge=0,
        alias="requestCount",
        description="Total requests processed"
    )
    error_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        alias="errorRate",
        description="Error rate (0.0-1.0)"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class TierMetricsResponse(BaseModel):
    """Response containing metrics for all tiers.

    Attributes:
        tiers: List of tier metrics
    """

    tiers: list[TierMetrics] = Field(..., description="Metrics for each tier")


class VRAMMetrics(BaseModel):
    """VRAM utilization metrics.

    Attributes:
        used: VRAM used in GB
        total: Total VRAM in GB
        percent: Utilization percentage
    """

    used: float = Field(..., ge=0.0, description="VRAM used (GB)")
    total: float = Field(..., ge=0.0, description="Total VRAM (GB)")
    percent: float = Field(..., ge=0.0, le=100.0, description="Utilization %")


class CPUMetrics(BaseModel):
    """CPU utilization metrics.

    Attributes:
        percent: CPU utilization percentage
        cores: Number of CPU cores
    """

    percent: float = Field(..., ge=0.0, le=100.0, description="CPU usage %")
    cores: int = Field(..., ge=1, description="CPU core count")


class MemoryMetrics(BaseModel):
    """RAM utilization metrics.

    Attributes:
        used: RAM used in GB
        total: Total RAM in GB
        percent: Utilization percentage
    """

    used: float = Field(..., ge=0.0, description="RAM used (GB)")
    total: float = Field(..., ge=0.0, description="Total RAM (GB)")
    percent: float = Field(..., ge=0.0, le=100.0, description="Utilization %")


class ThreadPoolStatus(BaseModel):
    """Thread pool status metrics.

    Attributes:
        active: Active threads
        queued: Queued tasks
    """

    active: int = Field(..., ge=0, description="Active threads")
    queued: int = Field(..., ge=0, description="Queued tasks")


class DiskIOMetrics(BaseModel):
    """Disk I/O metrics.

    Attributes:
        read_mbps: Read throughput in MB/s
        write_mbps: Write throughput in MB/s
    """

    read_mbps: float = Field(
        ...,
        ge=0.0,
        alias="readMBps",
        description="Read throughput (MB/s)"
    )
    write_mbps: float = Field(
        ...,
        ge=0.0,
        alias="writeMBps",
        description="Write throughput (MB/s)"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class NetworkThroughputMetrics(BaseModel):
    """Network throughput metrics.

    Attributes:
        rx_mbps: Receive throughput in MB/s
        tx_mbps: Transmit throughput in MB/s
    """

    rx_mbps: float = Field(
        ...,
        ge=0.0,
        alias="rxMBps",
        description="RX throughput (MB/s)"
    )
    tx_mbps: float = Field(
        ...,
        ge=0.0,
        alias="txMBps",
        description="TX throughput (MB/s)"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class ResourceMetrics(BaseModel):
    """System resource utilization metrics.

    Attributes:
        vram: VRAM metrics
        cpu: CPU metrics
        memory: RAM metrics
        faiss_index_size: FAISS index size in bytes
        redis_cache_size: Redis cache size in bytes
        active_connections: Active WebSocket connections
        thread_pool_status: Thread pool metrics
        disk_io: Disk I/O metrics
        network_throughput: Network metrics
    """

    vram: VRAMMetrics = Field(..., description="VRAM metrics")
    cpu: CPUMetrics = Field(..., description="CPU metrics")
    memory: MemoryMetrics = Field(..., description="RAM metrics")
    faiss_index_size: int = Field(
        ...,
        ge=0,
        alias="faissIndexSize",
        description="FAISS index size (bytes)"
    )
    redis_cache_size: int = Field(
        ...,
        ge=0,
        alias="redisCacheSize",
        description="Redis cache size (bytes)"
    )
    active_connections: int = Field(
        ...,
        ge=0,
        alias="activeConnections",
        description="Active WebSocket connections"
    )
    thread_pool_status: ThreadPoolStatus = Field(
        ...,
        alias="threadPoolStatus",
        description="Thread pool status"
    )
    disk_io: DiskIOMetrics = Field(
        ...,
        alias="diskIO",
        description="Disk I/O metrics"
    )
    network_throughput: NetworkThroughputMetrics = Field(
        ...,
        alias="networkThroughput",
        description="Network throughput"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class RoutingDecisionMatrix(BaseModel):
    """Routing decision matrix entry.

    Attributes:
        complexity: Complexity level
        tier: Tier selected
        count: Number of decisions
        avg_score: Average complexity score
    """

    complexity: ComplexityLevel = Field(..., description="Complexity level")
    tier: TierName = Field(..., description="Tier selected")
    count: int = Field(..., ge=0, description="Decision count")
    avg_score: float = Field(
        ...,
        ge=0.0,
        alias="avgScore",
        description="Average complexity score"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class AccuracyMetrics(BaseModel):
    """Routing accuracy metrics.

    Attributes:
        total_decisions: Total routing decisions
        avg_decision_time_ms: Average decision time
        fallback_rate: Fallback rate (0.0-1.0)
    """

    total_decisions: int = Field(
        ...,
        ge=0,
        alias="totalDecisions",
        description="Total decisions"
    )
    avg_decision_time_ms: float = Field(
        ...,
        ge=0.0,
        alias="avgDecisionTimeMs",
        description="Average decision time (ms)"
    )
    fallback_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        alias="fallbackRate",
        description="Fallback rate"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class ModelAvailability(BaseModel):
    """Model availability metrics for a tier.

    Attributes:
        tier: Tier name
        available: Number of available models
        total: Total number of models
    """

    tier: TierName = Field(..., description="Tier name")
    available: int = Field(..., ge=0, description="Available models")
    total: int = Field(..., ge=0, description="Total models")


class RoutingMetrics(BaseModel):
    """Routing analytics and decision metrics.

    Attributes:
        decision_matrix: Routing decision matrix
        accuracy_metrics: Accuracy metrics
        model_availability: Model availability by tier
    """

    decision_matrix: list[RoutingDecisionMatrix] = Field(
        ...,
        alias="decisionMatrix",
        description="Routing decision matrix"
    )
    accuracy_metrics: AccuracyMetrics = Field(
        ...,
        alias="accuracyMetrics",
        description="Accuracy metrics"
    )
    model_availability: list[ModelAvailability] = Field(
        ...,
        alias="modelAvailability",
        description="Model availability by tier"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True


class MetricsUpdate(BaseModel):
    """WebSocket metrics update message.

    Attributes:
        type: Message type (always "metrics_update")
        timestamp: ISO8601 timestamp
        queries: Query metrics
        resources: Resource metrics
        routing: Routing metrics
    """

    type: Literal["metrics_update"] = Field(
        default="metrics_update",
        description="Message type"
    )
    timestamp: str = Field(..., description="ISO8601 timestamp")
    queries: QueryMetrics = Field(..., description="Query metrics")
    resources: ResourceMetrics = Field(..., description="Resource metrics")
    routing: RoutingMetrics = Field(..., description="Routing metrics")
