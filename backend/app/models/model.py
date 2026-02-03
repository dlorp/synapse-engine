"""Data models for model status and health monitoring."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelState(str, Enum):
    """Model operational states.

    States:
        ACTIVE: Model is healthy and processing requests
        IDLE: Model is healthy but not currently processing
        PROCESSING: Model is actively processing a request
        ERROR: Model encountered an error
        OFFLINE: Model is not reachable or shut down
    """

    ACTIVE = "active"
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    OFFLINE = "offline"


class ModelHealth(BaseModel):
    """Model health check result.

    Attributes:
        is_healthy: Overall health status
        latency_ms: Health check latency in milliseconds
        last_check: Timestamp of last health check
        error_message: Error message if unhealthy
        consecutive_failures: Number of consecutive failed health checks
    """

    is_healthy: bool = Field(
        ..., serialization_alias="isHealthy", description="Overall health status"
    )
    latency_ms: float = Field(
        ...,
        ge=0,
        serialization_alias="latencyMs",
        description="Health check latency in ms",
    )
    last_check: datetime = Field(
        ..., serialization_alias="lastCheck", description="Last health check timestamp"
    )
    error_message: Optional[str] = Field(
        default=None,
        serialization_alias="errorMessage",
        description="Error message if unhealthy",
    )
    consecutive_failures: int = Field(
        default=0,
        ge=0,
        serialization_alias="consecutiveFailures",
        description="Consecutive failed checks",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ModelInfo(BaseModel):
    """Static model information.

    Attributes:
        id: Unique model identifier
        name: Human-readable model name
        tier: Model tier based on parameter size (fast, balanced, powerful)
        port: Model server port
        max_context_tokens: Maximum context window size
        description: Model description
    """

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Model name")
    tier: str = Field(..., description="Model tier (fast, balanced, powerful)")
    port: int = Field(..., ge=1, le=65535, description="Server port")
    max_context_tokens: int = Field(
        ...,
        gt=0,
        serialization_alias="maxContextTokens",
        description="Max context window",
    )
    description: Optional[str] = Field(default=None, description="Model description")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ModelStatus(BaseModel):
    """Current model status with runtime metrics.

    Attributes:
        id: Model identifier
        name: Model name
        tier: Model tier based on parameter size (fast, balanced, powerful)
        port: Server port
        state: Current operational state
        memory_used: Memory used in MB
        memory_total: Total memory available in MB
        request_count: Total requests processed
        avg_response_time: Average response time in milliseconds
        last_active: Timestamp of last activity
        error_count: Total errors encountered
        uptime_seconds: Time since model started
    """

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Model name")
    tier: str = Field(..., description="Model tier (fast, balanced, powerful)")
    port: int = Field(..., ge=1, le=65535, description="Server port")
    state: ModelState = Field(..., description="Current operational state")
    memory_used: int = Field(
        ..., ge=0, serialization_alias="memoryUsed", description="Memory used in MB"
    )
    memory_total: int = Field(
        ..., gt=0, serialization_alias="memoryTotal", description="Total memory in MB"
    )
    request_count: int = Field(
        default=0,
        ge=0,
        serialization_alias="requestCount",
        description="Total requests",
    )
    avg_response_time: float = Field(
        default=0.0,
        ge=0,
        serialization_alias="avgResponseTime",
        description="Average response time in ms",
    )
    last_active: datetime = Field(
        ..., serialization_alias="lastActive", description="Last activity timestamp"
    )
    error_count: int = Field(
        default=0, ge=0, serialization_alias="errorCount", description="Total errors"
    )
    uptime_seconds: int = Field(
        default=0,
        ge=0,
        serialization_alias="uptimeSeconds",
        description="Uptime in seconds",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SystemStatus(BaseModel):
    """Overall system status with aggregate metrics.

    Attributes:
        models: List of individual model statuses
        total_vram_gb: Total VRAM available in GB
        total_vram_used_gb: Total VRAM used in GB
        cache_hit_rate: Cache hit rate (0.0 to 1.0)
        active_queries: Number of active queries
        total_requests: Total requests processed
        timestamp: Status timestamp
    """

    models: List[ModelStatus] = Field(..., description="Model statuses")
    total_vram_gb: float = Field(
        ..., ge=0, serialization_alias="totalVramGb", description="Total VRAM in GB"
    )
    total_vram_used_gb: float = Field(
        ..., ge=0, serialization_alias="totalVramUsedGb", description="VRAM used in GB"
    )
    cache_hit_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        serialization_alias="cacheHitRate",
        description="Cache hit rate",
    )
    active_queries: int = Field(
        ..., ge=0, serialization_alias="activeQueries", description="Active queries"
    )
    total_requests: int = Field(
        default=0,
        ge=0,
        serialization_alias="totalRequests",
        description="Total requests",
    )
    timestamp: datetime = Field(..., description="Status timestamp")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HealthCheckResponse(BaseModel):
    """Health check endpoint response.

    Attributes:
        status: Overall health status
        timestamp: Health check timestamp
        version: Application version
        environment: Environment name
        uptime_seconds: Application uptime
    """

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    environment: Optional[str] = Field(default=None, description="Environment name")
    uptime_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        serialization_alias="uptimeSeconds",
        description="Application uptime",
    )


class HealthResponse(BaseModel):
    """Standardized health check response per SYSTEM_IDENTITY.md.

    Attributes:
        status: Health status (ok, degraded, error)
        uptime: Uptime in seconds
        components: Component health status dictionary
        trace_id: Optional trace ID for request correlation
    """

    status: str = Field(..., description="Health status: ok, degraded, error")
    uptime: float = Field(..., ge=0, description="Uptime in seconds")
    components: Dict[str, str] = Field(
        default_factory=dict, description="Component health status"
    )
    trace_id: Optional[str] = Field(
        default=None,
        serialization_alias="traceId",
        description="Trace ID for request correlation",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
