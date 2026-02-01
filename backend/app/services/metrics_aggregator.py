"""Metrics aggregation service for time-series storage.

This module provides a time-series storage system with:
- Ring buffer pattern for fixed memory usage (30-day retention)
- Thread-safe operations with asyncio.Lock
- Downsampling for long time ranges
- Filtering by model_id, tier, query_mode
- Statistical aggregation (min/max/avg/percentiles)
"""

import asyncio
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Deque, Literal, Optional

from app.core.logging import get_logger
from app.models.timeseries import (
    ChartJSData,
    ChartJSDataset,
    MetricsSummary,
    MetricType,
    ModelBreakdown,
    ModelBreakdownResponse,
    MultiMetricResponse,
    TimeRange,
    TimeSeriesPoint,
    TimeSeriesResponse
)


logger = get_logger(__name__)

# Model name resolver callback type
ModelNameResolver = Optional[callable]
_model_name_resolver: ModelNameResolver = None


def set_model_name_resolver(resolver: callable) -> None:
    """Set the model name resolver callback.

    The resolver should accept a model_id string and return a display name string.
    This allows the metrics aggregator to resolve model IDs to human-readable names
    without directly depending on the model registry.

    Args:
        resolver: Callable that takes model_id and returns display_name
    """
    global _model_name_resolver
    _model_name_resolver = resolver
    logger.info("Model name resolver configured")


def _resolve_model_name(model_id: str) -> str:
    """Resolve model ID to display name using configured resolver.

    Args:
        model_id: Model identifier

    Returns:
        Display name if resolver is configured and finds the model,
        otherwise returns the model_id as-is
    """
    if _model_name_resolver is not None:
        try:
            return _model_name_resolver(model_id)
        except Exception as e:
            logger.debug(f"Failed to resolve model name for {model_id}: {e}")
    return model_id


@dataclass
class MetricDataPoint:
    """Internal metric data point structure.

    Attributes:
        timestamp: Unix timestamp
        value: Metric value
        model_id: Optional model identifier
        tier: Optional tier (Q2, Q3, Q4)
        query_mode: Optional query mode
    """

    timestamp: float
    value: float
    model_id: Optional[str] = None
    tier: Optional[Literal["Q2", "Q3", "Q4"]] = None
    query_mode: Optional[str] = None


class MetricsAggregator:
    """Time-series metrics storage and aggregation service.

    This service maintains ring buffers of metric data with 30-day retention,
    providing efficient storage and retrieval with downsampling support.

    Attributes:
        max_retention_seconds: Maximum data retention in seconds (default 30 days)
        lock: Async lock for thread-safe operations
        metrics: Dictionary of metric buffers by metric type
    """

    def __init__(
        self,
        max_retention_seconds: int = 30 * 24 * 60 * 60  # 30 days
    ) -> None:
        """Initialize metrics aggregator.

        Args:
            max_retention_seconds: Maximum data retention in seconds (default 30 days)
        """
        self.max_retention_seconds = max_retention_seconds
        self.lock = asyncio.Lock()

        # Metric storage: {metric_type: deque[MetricDataPoint]}
        # Ring buffer with maxlen for automatic eviction
        # Estimate: ~1 point/query * 10k queries/day * 30 days = 300k points max
        self.metrics: dict[MetricType, Deque[MetricDataPoint]] = {
            metric_type: deque(maxlen=500_000)  # ~300k expected, 500k for safety
            for metric_type in MetricType
        }

        # TTL cleanup task handle
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(
            f"MetricsAggregator initialized with {max_retention_seconds}s retention "
            f"(~{max_retention_seconds / (24*60*60):.1f} days)"
        )

    async def start(self) -> None:
        """Start the metrics aggregator with periodic TTL cleanup."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("MetricsAggregator started with TTL cleanup task")

    async def stop(self) -> None:
        """Stop the metrics aggregator and cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("MetricsAggregator stopped")

    async def record_metric(
        self,
        metric_name: MetricType,
        value: float,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """Record a metric data point.

        Thread-safe method to record a metric with optional metadata.

        Args:
            metric_name: Type of metric to record
            value: Metric value
            metadata: Optional metadata (model_id, tier, query_mode)
        """
        async with self.lock:
            now = time.time()

            # Extract metadata
            model_id = metadata.get("model_id") if metadata else None
            tier = metadata.get("tier") if metadata else None
            query_mode = metadata.get("query_mode") if metadata else None

            # Create data point
            data_point = MetricDataPoint(
                timestamp=now,
                value=value,
                model_id=model_id,
                tier=tier,
                query_mode=query_mode
            )

            # Append to ring buffer (automatically evicts oldest if at capacity)
            self.metrics[metric_name].append(data_point)

            logger.debug(
                f"Recorded metric: {metric_name.value}={value:.2f}",
                extra={
                    "metric": metric_name.value,
                    "value": value,
                    "model_id": model_id,
                    "tier": tier
                }
            )

    async def get_time_series(
        self,
        metric_name: MetricType,
        time_range: TimeRange,
        model_id: Optional[str] = None,
        tier: Optional[Literal["Q2", "Q3", "Q4"]] = None,
        query_mode: Optional[str] = None
    ) -> TimeSeriesResponse:
        """Get time-series data for a metric.

        Thread-safe method to retrieve time-series data with filtering.

        Args:
            metric_name: Type of metric to retrieve
            time_range: Time range for data (1h, 6h, 24h, 7d, 30d)
            model_id: Optional filter by model ID
            tier: Optional filter by tier
            query_mode: Optional filter by query mode

        Returns:
            TimeSeriesResponse with filtered and potentially downsampled data
        """
        async with self.lock:
            # Calculate time window
            window_seconds = self._time_range_to_seconds(time_range)
            now = time.time()
            window_start = now - window_seconds

            # Get metric buffer
            buffer = self.metrics[metric_name]

            # Filter data points
            filtered_points = [
                point for point in buffer
                if point.timestamp >= window_start
                and (model_id is None or point.model_id == model_id)
                and (tier is None or point.tier == tier)
                and (query_mode is None or point.query_mode == query_mode)
            ]

            # Downsample if necessary
            data_points = self._downsample(filtered_points, time_range)

            # Calculate summary statistics
            values = [p.value for p in filtered_points]
            summary = self._calculate_summary(values) if values else MetricsSummary(
                min=0.0, max=0.0, avg=0.0, p50=0.0, p95=0.0, p99=0.0
            )

            # Convert to response format
            unit = self._get_metric_unit(metric_name)
            return TimeSeriesResponse(
                metric_name=metric_name.value,
                time_range=time_range.value,
                unit=unit,
                data_points=[
                    TimeSeriesPoint(
                        timestamp=datetime.fromtimestamp(
                            p.timestamp, tz=timezone.utc
                        ).isoformat(),
                        value=round(p.value, 2),
                        metadata={
                            "model_id": p.model_id,
                            "tier": p.tier,
                            "query_mode": p.query_mode
                        }
                    )
                    for p in data_points
                ],
                summary=summary
            )

    async def get_summary(
        self,
        metric_name: MetricType,
        time_range: TimeRange
    ) -> MetricsSummary:
        """Get statistical summary for a metric.

        Args:
            metric_name: Type of metric
            time_range: Time range for data

        Returns:
            MetricsSummary with min/max/avg/percentiles
        """
        async with self.lock:
            # Calculate time window
            window_seconds = self._time_range_to_seconds(time_range)
            now = time.time()
            window_start = now - window_seconds

            # Get metric buffer
            buffer = self.metrics[metric_name]

            # Filter data points
            values = [
                point.value for point in buffer
                if point.timestamp >= window_start
            ]

            return self._calculate_summary(values) if values else MetricsSummary(
                min=0.0, max=0.0, avg=0.0, p50=0.0, p95=0.0, p99=0.0
            )

    async def get_comparison(
        self,
        metric_names: list[MetricType],
        time_range: TimeRange
    ) -> MultiMetricResponse:
        """Get multi-metric comparison data in Chart.js format.

        Args:
            metric_names: List of metric types to compare
            time_range: Time range for data

        Returns:
            MultiMetricResponse with Chart.js compatible data
        """
        async with self.lock:
            # Calculate time window
            window_seconds = self._time_range_to_seconds(time_range)
            now = time.time()
            window_start = now - window_seconds

            # Determine bucket interval for alignment
            bucket_interval = self._get_bucket_interval(time_range)

            # Create aligned time buckets
            bucket_count = int(window_seconds / bucket_interval)
            bucket_timestamps = [
                now - (i * bucket_interval)
                for i in range(bucket_count, -1, -1)
            ]

            # Generate labels
            labels = [
                datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                for ts in bucket_timestamps
            ]

            # Build datasets
            datasets: list[ChartJSDataset] = []

            for metric_name in metric_names:
                buffer = self.metrics[metric_name]

                # Filter data points
                filtered_points = [
                    point for point in buffer
                    if point.timestamp >= window_start
                ]

                # Bucket data points and average
                bucket_values: list[float] = []
                for i in range(len(bucket_timestamps) - 1):
                    bucket_start = bucket_timestamps[i]
                    bucket_end = bucket_timestamps[i + 1]

                    # Find points in this bucket
                    bucket_points = [
                        p.value for p in filtered_points
                        if bucket_start <= p.timestamp < bucket_end
                    ]

                    # Average or 0 if no data
                    avg = statistics.mean(bucket_points) if bucket_points else 0.0
                    bucket_values.append(round(avg, 2))

                datasets.append(
                    ChartJSDataset(
                        label=metric_name.value,
                        data=bucket_values,
                        metadata={"unit": self._get_metric_unit(metric_name)}
                    )
                )

            return MultiMetricResponse(
                time_range=time_range.value,
                chart_data=ChartJSData(
                    labels=labels,
                    datasets=datasets
                )
            )

    async def get_model_breakdown(
        self,
        metric_name: MetricType,
        time_range: TimeRange
    ) -> ModelBreakdownResponse:
        """Get per-model breakdown for a metric.

        Args:
            metric_name: Type of metric
            time_range: Time range for data

        Returns:
            ModelBreakdownResponse with per-model statistics
        """
        async with self.lock:
            # Calculate time window
            window_seconds = self._time_range_to_seconds(time_range)
            now = time.time()
            window_start = now - window_seconds

            # Get metric buffer
            buffer = self.metrics[metric_name]

            # Filter data points
            filtered_points = [
                point for point in buffer
                if point.timestamp >= window_start and point.model_id is not None
            ]

            # Group by model_id
            model_data: dict[str, list[MetricDataPoint]] = defaultdict(list)
            for point in filtered_points:
                if point.model_id:
                    model_data[point.model_id].append(point)

            # Build per-model breakdowns
            models: list[ModelBreakdown] = []

            for model_id, points in model_data.items():
                # Downsample points
                downsampled = self._downsample(points, time_range)

                # Calculate summary
                values = [p.value for p in points]
                summary = self._calculate_summary(values)

                # Determine tier from data
                tier = points[0].tier or "Q2"  # Default to Q2 if missing

                models.append(
                    ModelBreakdown(
                        model_id=model_id,
                        display_name=_resolve_model_name(model_id),
                        tier=tier,  # type: ignore
                        data_points=[
                            TimeSeriesPoint(
                                timestamp=datetime.fromtimestamp(
                                    p.timestamp, tz=timezone.utc
                                ).isoformat(),
                                value=round(p.value, 2),
                                metadata={
                                    "model_id": p.model_id,
                                    "tier": p.tier,
                                    "query_mode": p.query_mode
                                }
                            )
                            for p in downsampled
                        ],
                        summary=summary
                    )
                )

            # Sort by tier then model_id
            models.sort(key=lambda m: (m.tier, m.model_id))

            unit = self._get_metric_unit(metric_name)
            return ModelBreakdownResponse(
                metric_name=metric_name.value,
                time_range=time_range.value,
                unit=unit,
                models=models
            )

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired data points.

        Runs every 1 hour and removes data points older than retention period.
        """
        while True:
            try:
                # Wait 1 hour between cleanups
                await asyncio.sleep(3600)

                # Run cleanup
                await self._cleanup_expired_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics cleanup loop: {e}", exc_info=True)

    async def _cleanup_expired_data(self) -> None:
        """Remove data points older than retention period.

        This is a safety mechanism - the ring buffer automatically evicts
        old data when at capacity, but this ensures TTL-based cleanup.
        """
        async with self.lock:
            now = time.time()
            cutoff = now - self.max_retention_seconds

            removed_count = 0

            for metric_name, buffer in self.metrics.items():
                # Remove expired points from left side
                while buffer and buffer[0].timestamp < cutoff:
                    buffer.popleft()
                    removed_count += 1

            if removed_count > 0:
                logger.info(
                    f"TTL cleanup removed {removed_count} expired data points",
                    extra={"removed_count": removed_count}
                )

    def _downsample(
        self,
        points: list[MetricDataPoint],
        time_range: TimeRange
    ) -> list[MetricDataPoint]:
        """Downsample data points for long time ranges.

        For long time ranges (7d, 30d), aggregate into hourly buckets
        to reduce data volume.

        Args:
            points: Raw data points
            time_range: Time range (determines downsampling strategy)

        Returns:
            Downsampled data points
        """
        # No downsampling for short ranges
        if time_range in [TimeRange.ONE_HOUR, TimeRange.SIX_HOURS]:
            return points

        # Hourly downsampling for long ranges
        if time_range in [TimeRange.SEVEN_DAYS, TimeRange.THIRTY_DAYS]:
            bucket_interval = 3600  # 1 hour

            # Group points into hourly buckets
            buckets: dict[int, list[MetricDataPoint]] = defaultdict(list)
            for point in points:
                bucket_key = int(point.timestamp // bucket_interval)
                buckets[bucket_key].append(point)

            # Average each bucket
            downsampled: list[MetricDataPoint] = []
            for bucket_key in sorted(buckets.keys()):
                bucket_points = buckets[bucket_key]
                avg_value = statistics.mean([p.value for p in bucket_points])

                # Use first point's metadata
                first = bucket_points[0]
                downsampled.append(
                    MetricDataPoint(
                        timestamp=bucket_key * bucket_interval,
                        value=avg_value,
                        model_id=first.model_id,
                        tier=first.tier,
                        query_mode=first.query_mode
                    )
                )

            return downsampled

        # 10-minute downsampling for 24h
        if time_range == TimeRange.TWENTY_FOUR_HOURS:
            bucket_interval = 600  # 10 minutes

            buckets: dict[int, list[MetricDataPoint]] = defaultdict(list)
            for point in points:
                bucket_key = int(point.timestamp // bucket_interval)
                buckets[bucket_key].append(point)

            downsampled: list[MetricDataPoint] = []
            for bucket_key in sorted(buckets.keys()):
                bucket_points = buckets[bucket_key]
                avg_value = statistics.mean([p.value for p in bucket_points])

                first = bucket_points[0]
                downsampled.append(
                    MetricDataPoint(
                        timestamp=bucket_key * bucket_interval,
                        value=avg_value,
                        model_id=first.model_id,
                        tier=first.tier,
                        query_mode=first.query_mode
                    )
                )

            return downsampled

        # Default: return as-is
        return points

    def _calculate_summary(self, values: list[float]) -> MetricsSummary:
        """Calculate statistical summary of values.

        Args:
            values: List of numeric values

        Returns:
            MetricsSummary with min/max/avg/percentiles
        """
        if not values:
            return MetricsSummary(
                min=0.0, max=0.0, avg=0.0, p50=0.0, p95=0.0, p99=0.0
            )

        sorted_values = sorted(values)

        return MetricsSummary(
            min=round(min(values), 2),
            max=round(max(values), 2),
            avg=round(statistics.mean(values), 2),
            p50=round(statistics.median(sorted_values), 2),
            p95=round(self._percentile(sorted_values, 95), 2),
            p99=round(self._percentile(sorted_values, 99), 2)
        )

    def _percentile(self, sorted_values: list[float], p: int) -> float:
        """Calculate percentile of sorted values.

        Args:
            sorted_values: List of values (must be sorted)
            p: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not sorted_values:
            return 0.0

        k = (len(sorted_values) - 1) * (p / 100.0)
        f = int(k)
        c = f + 1

        if c >= len(sorted_values):
            return sorted_values[-1]

        d0 = sorted_values[f]
        d1 = sorted_values[c]

        return d0 + (d1 - d0) * (k - f)

    def _time_range_to_seconds(self, time_range: TimeRange) -> int:
        """Convert time range enum to seconds.

        Args:
            time_range: Time range enum

        Returns:
            Number of seconds
        """
        mapping = {
            TimeRange.ONE_HOUR: 3600,
            TimeRange.SIX_HOURS: 6 * 3600,
            TimeRange.TWENTY_FOUR_HOURS: 24 * 3600,
            TimeRange.SEVEN_DAYS: 7 * 24 * 3600,
            TimeRange.THIRTY_DAYS: 30 * 24 * 3600
        }
        return mapping[time_range]

    def _get_bucket_interval(self, time_range: TimeRange) -> int:
        """Get bucket interval for time range.

        Args:
            time_range: Time range

        Returns:
            Bucket interval in seconds
        """
        mapping = {
            TimeRange.ONE_HOUR: 60,  # 1 minute
            TimeRange.SIX_HOURS: 300,  # 5 minutes
            TimeRange.TWENTY_FOUR_HOURS: 600,  # 10 minutes
            TimeRange.SEVEN_DAYS: 3600,  # 1 hour
            TimeRange.THIRTY_DAYS: 3600  # 1 hour
        }
        return mapping[time_range]

    def _get_metric_unit(self, metric_name: MetricType) -> str:
        """Get unit of measurement for metric.

        Args:
            metric_name: Metric type

        Returns:
            Unit string
        """
        units = {
            MetricType.RESPONSE_TIME: "ms",
            MetricType.TOKENS_PER_SECOND: "tokens/s",
            MetricType.CACHE_HIT_RATE: "%",
            MetricType.COMPLEXITY_SCORE: "score",
            MetricType.CGRAG_RETRIEVAL_TIME: "ms",
            MetricType.MODEL_LOAD: "%"
        }
        return units.get(metric_name, "")


# Global singleton instance
_metrics_aggregator: Optional[MetricsAggregator] = None


def get_metrics_aggregator() -> MetricsAggregator:
    """Get the global metrics aggregator instance.

    Returns:
        MetricsAggregator singleton

    Raises:
        RuntimeError: If aggregator not initialized
    """
    if _metrics_aggregator is None:
        raise RuntimeError(
            "MetricsAggregator not initialized. Call init_metrics_aggregator() first."
        )
    return _metrics_aggregator


def init_metrics_aggregator() -> MetricsAggregator:
    """Initialize the global metrics aggregator.

    Returns:
        MetricsAggregator singleton
    """
    global _metrics_aggregator

    if _metrics_aggregator is None:
        _metrics_aggregator = MetricsAggregator(
            max_retention_seconds=30 * 24 * 60 * 60  # 30 days
        )
        logger.info("Initialized global MetricsAggregator")

    return _metrics_aggregator
