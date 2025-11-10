"""Pydantic models for per-model metrics responses.

This module defines the data structures for time-series performance metrics
collected from individual model instances during health checks.
"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ModelMetrics(BaseModel):
    """Time-series metrics for a single model.

    Each array contains up to 20 datapoints representing the last
    ~100 seconds of metrics (sampled at 1Hz during health checks).

    Attributes:
        model_id: Unique model identifier
        tokens_per_second: Token generation rate history (tokens/sec)
        current_tokens_per_second: Most recent tokens/sec value
        memory_gb: VRAM usage history (gigabytes)
        current_memory_gb: Most recent memory usage in GB
        latency_ms: Health check latency history (milliseconds)
        current_latency_ms: Most recent latency in ms
    """

    model_id: str = Field(..., description="Unique model identifier", alias="modelId")

    # Token generation metrics
    tokens_per_second: List[float] = Field(
        default_factory=list,
        description="Token generation rate history (tokens/sec)",
        alias="tokensPerSecond"
    )
    current_tokens_per_second: float = Field(
        0.0,
        description="Most recent tokens/sec value",
        alias="currentTokensPerSecond"
    )

    # Memory usage metrics
    memory_gb: List[float] = Field(
        default_factory=list,
        description="VRAM usage history (gigabytes)",
        alias="memoryGb"
    )
    current_memory_gb: float = Field(
        0.0,
        description="Most recent memory usage in GB",
        alias="currentMemoryGb"
    )

    # Latency metrics
    latency_ms: List[float] = Field(
        default_factory=list,
        description="Health check latency history (milliseconds)",
        alias="latencyMs"
    )
    current_latency_ms: float = Field(
        0.0,
        description="Most recent latency in ms",
        alias="currentLatencyMs"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )


class AllModelsMetricsResponse(BaseModel):
    """Response containing metrics for all models.

    Attributes:
        models: Metrics for each model
        timestamp: ISO 8601 timestamp of response
    """

    models: List[ModelMetrics] = Field(
        ...,
        description="Metrics for each model"
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of response"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
