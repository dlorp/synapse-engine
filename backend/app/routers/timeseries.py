"""Time-series metrics endpoints.

This module provides REST API endpoints for querying historical time-series
metrics data with flexible time ranges, filtering, and aggregation for
Chart.js visualizations.
"""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import get_logger
from app.models.timeseries import (
    MetricType,
    MetricsSummary,
    ModelBreakdownResponse,
    MultiMetricResponse,
    TimeRange,
    TimeSeriesResponse,
)
from app.services.metrics_aggregator import get_metrics_aggregator


logger = get_logger(__name__)
router = APIRouter(prefix="/api/timeseries")


@router.get(
    "/",
    response_model=TimeSeriesResponse,
    summary="Get time-series data",
    description="""
    Retrieve time-series data for a specific metric with optional filtering.

    **Supported Metrics:**
    - `response_time` - Query response time in milliseconds
    - `tokens_per_second` - Token generation rate
    - `cache_hit_rate` - Cache hit percentage
    - `complexity_score` - Query complexity score
    - `cgrag_retrieval_time` - CGRAG retrieval time in ms
    - `model_load` - Model CPU/GPU load percentage

    **Time Ranges:**
    - `1h` - Last 1 hour (1-minute intervals)
    - `6h` - Last 6 hours (5-minute intervals)
    - `24h` - Last 24 hours (10-minute intervals)
    - `7d` - Last 7 days (1-hour intervals)
    - `30d` - Last 30 days (1-hour intervals)

    **Filters:**
    - `model` - Filter by specific model ID
    - `tier` - Filter by tier (Q2, Q3, Q4)

    **Example:**
    ```
    GET /api/timeseries?metric=response_time&range=24h&tier=Q2
    ```

    Returns time-series data points with statistical summary.
    """,
    responses={
        200: {
            "description": "Time-series data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "metricName": "response_time",
                        "timeRange": "24h",
                        "unit": "ms",
                        "dataPoints": [
                            {
                                "timestamp": "2025-11-12T10:00:00Z",
                                "value": 1250.5,
                                "metadata": {
                                    "model_id": "deepseek_r1_8b_q2k",
                                    "tier": "Q2",
                                    "query_mode": "auto",
                                },
                            }
                        ],
                        "summary": {
                            "min": 950.0,
                            "max": 2100.0,
                            "avg": 1350.5,
                            "p50": 1280.0,
                            "p95": 1850.0,
                            "p99": 2000.0,
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid metric or time range"},
        500: {"description": "Internal server error"},
    },
)
async def get_timeseries(
    metric: MetricType = Query(..., description="Metric type to retrieve"),
    range: TimeRange = Query(
        TimeRange.TWENTY_FOUR_HOURS, description="Time range for data"
    ),
    model: Optional[str] = Query(None, description="Filter by model ID"),
    tier: Optional[Literal["Q2", "Q3", "Q4"]] = Query(
        None, description="Filter by tier"
    ),
) -> TimeSeriesResponse:
    """Get time-series data for a metric.

    Args:
        metric: Metric type to retrieve
        range: Time range for data
        model: Optional model ID filter
        tier: Optional tier filter

    Returns:
        TimeSeriesResponse with filtered time-series data

    Raises:
        HTTPException(400): Invalid parameters
        HTTPException(500): Internal server error
    """
    try:
        aggregator = get_metrics_aggregator()

        logger.info(
            f"Fetching time-series: metric={metric.value}, range={range.value}, "
            f"model={model}, tier={tier}"
        )

        response = await aggregator.get_time_series(
            metric_name=metric, time_range=range, model_id=model, tier=tier
        )

        logger.debug(
            f"Time-series retrieved: {len(response.data_points)} points",
            extra={
                "metric": metric.value,
                "range": range.value,
                "point_count": len(response.data_points),
            },
        )

        return response

    except RuntimeError as e:
        logger.error(f"MetricsAggregator not initialized: {e}")
        raise HTTPException(
            status_code=500, detail="Metrics aggregator not initialized"
        )
    except Exception as e:
        logger.error(f"Error fetching time-series: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch time-series data: {str(e)}"
        )


@router.get(
    "/summary",
    response_model=MetricsSummary,
    summary="Get metric summary statistics",
    description="""
    Retrieve statistical summary (min/max/avg/percentiles) for a metric.

    Returns aggregated statistics without individual data points for
    quick overview dashboards.

    **Example:**
    ```
    GET /api/timeseries/summary?metric=response_time&range=7d
    ```
    """,
    responses={
        200: {
            "description": "Summary statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "min": 950.0,
                        "max": 8500.0,
                        "avg": 2350.5,
                        "p50": 1850.0,
                        "p95": 5200.0,
                        "p99": 7800.0,
                    }
                }
            },
        }
    },
)
async def get_summary(
    metric: MetricType = Query(..., description="Metric type"),
    range: TimeRange = Query(TimeRange.TWENTY_FOUR_HOURS, description="Time range"),
) -> MetricsSummary:
    """Get statistical summary for a metric.

    Args:
        metric: Metric type
        range: Time range

    Returns:
        MetricsSummary with statistics

    Raises:
        HTTPException(500): Internal server error
    """
    try:
        aggregator = get_metrics_aggregator()

        summary = await aggregator.get_summary(metric_name=metric, time_range=range)

        logger.debug(
            f"Summary retrieved: {metric.value} over {range.value}",
            extra={"metric": metric.value, "range": range.value, "avg": summary.avg},
        )

        return summary

    except RuntimeError as e:
        logger.error(f"MetricsAggregator not initialized: {e}")
        raise HTTPException(
            status_code=500, detail="Metrics aggregator not initialized"
        )
    except Exception as e:
        logger.error(f"Error fetching summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch summary: {str(e)}"
        )


@router.get(
    "/comparison",
    response_model=MultiMetricResponse,
    summary="Compare multiple metrics",
    description="""
    Retrieve multiple metrics for comparison in a single Chart.js compatible response.

    All metrics are aligned to the same time buckets for easy visualization.

    **Example:**
    ```
    GET /api/timeseries/comparison?metrics=response_time,tokens_per_second,complexity_score&range=24h
    ```

    Returns Chart.js compatible data structure with aligned datasets.
    """,
    responses={
        200: {
            "description": "Comparison data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "timeRange": "24h",
                        "chartData": {
                            "labels": [
                                "2025-11-12T00:00:00Z",
                                "2025-11-12T00:10:00Z",
                                "2025-11-12T00:20:00Z",
                            ],
                            "datasets": [
                                {
                                    "label": "response_time",
                                    "data": [1250.5, 1180.3, 1320.8],
                                    "metadata": {"unit": "ms"},
                                },
                                {
                                    "label": "tokens_per_second",
                                    "data": [45.2, 48.1, 44.8],
                                    "metadata": {"unit": "tokens/s"},
                                },
                            ],
                        },
                    }
                }
            },
        }
    },
)
async def get_comparison(
    metrics: str = Query(..., description="Comma-separated list of metric types"),
    range: TimeRange = Query(TimeRange.TWENTY_FOUR_HOURS, description="Time range"),
) -> MultiMetricResponse:
    """Get multi-metric comparison data.

    Args:
        metrics: Comma-separated metric types
        range: Time range

    Returns:
        MultiMetricResponse with Chart.js data

    Raises:
        HTTPException(400): Invalid metric names
        HTTPException(500): Internal server error
    """
    try:
        # Parse metric names
        metric_names_str = [m.strip() for m in metrics.split(",")]

        # Validate and convert to MetricType
        try:
            metric_types = [MetricType(name) for name in metric_names_str]
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid metric name: {str(e)}"
            )

        aggregator = get_metrics_aggregator()

        logger.info(
            f"Fetching comparison: metrics={metric_names_str}, range={range.value}"
        )

        response = await aggregator.get_comparison(
            metric_names=metric_types, time_range=range
        )

        logger.debug(
            f"Comparison retrieved: {len(metric_types)} metrics",
            extra={
                "metrics": metric_names_str,
                "range": range.value,
                "dataset_count": len(response.chart_data.datasets),
            },
        )

        return response

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"MetricsAggregator not initialized: {e}")
        raise HTTPException(
            status_code=500, detail="Metrics aggregator not initialized"
        )
    except Exception as e:
        logger.error(f"Error fetching comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch comparison data: {str(e)}"
        )


@router.get(
    "/models",
    response_model=ModelBreakdownResponse,
    summary="Get per-model breakdown",
    description="""
    Retrieve per-model breakdown for a metric, showing each model's
    performance individually.

    **Example:**
    ```
    GET /api/timeseries/models?metric=response_time&range=7d
    ```

    Returns data for each model that recorded the metric, grouped by tier.
    """,
    responses={
        200: {
            "description": "Model breakdown retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "metricName": "response_time",
                        "timeRange": "7d",
                        "unit": "ms",
                        "models": [
                            {
                                "modelId": "deepseek_r1_8b_q2k",
                                "displayName": "DeepSeek R1 8B Q2K",
                                "tier": "Q2",
                                "dataPoints": [
                                    {
                                        "timestamp": "2025-11-12T10:00:00Z",
                                        "value": 1250.5,
                                        "metadata": {"model_id": "deepseek_r1_8b_q2k"},
                                    }
                                ],
                                "summary": {
                                    "min": 950.0,
                                    "max": 1850.0,
                                    "avg": 1280.5,
                                    "p50": 1250.0,
                                    "p95": 1750.0,
                                    "p99": 1820.0,
                                },
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def get_model_breakdown(
    metric: MetricType = Query(..., description="Metric type"),
    range: TimeRange = Query(TimeRange.TWENTY_FOUR_HOURS, description="Time range"),
) -> ModelBreakdownResponse:
    """Get per-model breakdown for a metric.

    Args:
        metric: Metric type
        range: Time range

    Returns:
        ModelBreakdownResponse with per-model data

    Raises:
        HTTPException(500): Internal server error
    """
    try:
        aggregator = get_metrics_aggregator()

        logger.info(
            f"Fetching model breakdown: metric={metric.value}, range={range.value}"
        )

        response = await aggregator.get_model_breakdown(
            metric_name=metric, time_range=range
        )

        logger.debug(
            f"Model breakdown retrieved: {len(response.models)} models",
            extra={
                "metric": metric.value,
                "range": range.value,
                "model_count": len(response.models),
            },
        )

        return response

    except RuntimeError as e:
        logger.error(f"MetricsAggregator not initialized: {e}")
        raise HTTPException(
            status_code=500, detail="Metrics aggregator not initialized"
        )
    except Exception as e:
        logger.error(f"Error fetching model breakdown: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch model breakdown: {str(e)}"
        )
