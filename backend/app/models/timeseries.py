"""Time-series metrics models.

This module defines Pydantic models for time-series metrics API endpoints,
supporting historical data queries with flexible time ranges, filtering,
and aggregation for Chart.js visualizations.
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Supported metric types for time-series queries."""

    RESPONSE_TIME = "response_time"
    TOKENS_PER_SECOND = "tokens_per_second"
    CACHE_HIT_RATE = "cache_hit_rate"
    COMPLEXITY_SCORE = "complexity_score"
    CGRAG_RETRIEVAL_TIME = "cgrag_retrieval_time"
    MODEL_LOAD = "model_load"


class TimeRange(str, Enum):
    """Supported time ranges for queries."""

    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWENTY_FOUR_HOURS = "24h"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"


class TimeSeriesPoint(BaseModel):
    """Single time-series data point with metadata.

    Attributes:
        timestamp: ISO8601 timestamp of the data point
        value: Numeric value for the metric
        metadata: Optional metadata (model_id, tier, mode, etc.)
    """

    timestamp: str = Field(..., description="ISO8601 timestamp")
    value: float = Field(..., description="Metric value")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (model_id, tier, query_mode, etc.)",
    )


class MetricsSummary(BaseModel):
    """Statistical summary of metric values.

    Attributes:
        min: Minimum value
        max: Maximum value
        avg: Average value
        p50: 50th percentile (median)
        p95: 95th percentile
        p99: 99th percentile
    """

    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    avg: float = Field(..., description="Average value")
    p50: float = Field(..., alias="p50", description="50th percentile (median)")
    p95: float = Field(..., alias="p95", description="95th percentile")
    p99: float = Field(..., alias="p99", description="99th percentile")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True


class TimeSeriesResponse(BaseModel):
    """Time-series data response.

    Attributes:
        metric_name: Name of the metric
        time_range: Time range covered
        unit: Unit of measurement
        data_points: List of time-series data points
        summary: Statistical summary of values
    """

    metric_name: str = Field(..., alias="metricName", description="Metric name")
    time_range: str = Field(..., alias="timeRange", description="Time range covered")
    unit: str = Field(..., description="Unit of measurement")
    data_points: list[TimeSeriesPoint] = Field(
        ..., alias="dataPoints", description="Time-series data points"
    )
    summary: MetricsSummary = Field(..., description="Statistical summary")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True


class ChartJSDataset(BaseModel):
    """Chart.js compatible dataset.

    Attributes:
        label: Dataset label
        data: List of numeric values
        metadata: Optional metadata for the dataset
    """

    label: str = Field(..., description="Dataset label")
    data: list[float] = Field(..., description="Data values")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Dataset metadata"
    )


class ChartJSData(BaseModel):
    """Chart.js compatible data structure.

    Attributes:
        labels: X-axis labels (timestamps)
        datasets: List of datasets to plot
    """

    labels: list[str] = Field(..., description="X-axis labels (ISO8601 timestamps)")
    datasets: list[ChartJSDataset] = Field(..., description="Datasets to plot")


class MultiMetricResponse(BaseModel):
    """Multi-metric comparison response.

    Attributes:
        time_range: Time range covered
        chart_data: Chart.js compatible data structure
    """

    time_range: str = Field(..., alias="timeRange", description="Time range covered")
    chart_data: ChartJSData = Field(..., alias="chartData", description="Chart.js data")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True


class ModelBreakdown(BaseModel):
    """Per-model metric breakdown.

    Attributes:
        model_id: Model identifier
        display_name: Human-readable model name
        tier: Model tier (Q2, Q3, Q4)
        data_points: Time-series data for this model
        summary: Statistical summary
    """

    model_id: str = Field(..., alias="modelId", description="Model identifier")
    display_name: str = Field(
        ..., alias="displayName", description="Human-readable model name"
    )
    tier: Literal["Q2", "Q3", "Q4"] = Field(..., description="Model tier")
    data_points: list[TimeSeriesPoint] = Field(
        ..., alias="dataPoints", description="Time-series data"
    )
    summary: MetricsSummary = Field(..., description="Statistical summary")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True


class ModelBreakdownResponse(BaseModel):
    """Per-model breakdown response.

    Attributes:
        metric_name: Name of the metric
        time_range: Time range covered
        unit: Unit of measurement
        models: List of per-model breakdowns
    """

    metric_name: str = Field(..., alias="metricName", description="Metric name")
    time_range: str = Field(..., alias="timeRange", description="Time range covered")
    unit: str = Field(..., description="Unit of measurement")
    models: list[ModelBreakdown] = Field(..., description="Per-model breakdowns")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
