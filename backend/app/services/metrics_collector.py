"""Metrics collection service.

This module provides a centralized service for collecting and aggregating
system metrics including query rates, tier performance, resource utilization,
and routing analytics.

The service maintains thread-safe circular buffers of time-series data and
provides real-time statistics for visualization in the frontend.
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Deque, Optional

import psutil

from app.core.logging import get_logger
from app.models.metrics import (
    AccuracyMetrics,
    CPUMetrics,
    DiskIOMetrics,
    MemoryMetrics,
    ModelAvailability,
    NetworkThroughputMetrics,
    QueryMetrics,
    ResourceMetrics,
    RoutingDecisionMatrix,
    RoutingMetrics,
    ThreadPoolStatus,
    TierMetrics,
    TierMetricsResponse,
    VRAMMetrics,
)

logger = get_logger(__name__)


class MetricsCollector:
    """Service for collecting and aggregating system metrics.

    This service maintains thread-safe time-series data and provides
    metrics endpoints for real-time visualization.

    Attributes:
        max_history: Maximum number of time-series data points to keep
        query_history: Circular buffer of query timestamps
        tier_performance: Performance metrics by tier
        routing_matrix: Routing decision matrix
        lock: Thread lock for safe concurrent access
    """

    def __init__(self, max_history: int = 180) -> None:
        """Initialize metrics collector.

        Args:
            max_history: Maximum time-series data points (default 180 = 30min at 10s intervals)
        """
        self.max_history = max_history
        self.lock = Lock()

        # Query metrics (30-minute rolling window)
        self.query_timestamps: Deque[float] = deque(maxlen=max_history)
        self.query_latencies: Deque[float] = deque(maxlen=max_history)
        self.query_tiers: Deque[str] = deque(maxlen=max_history)

        # Tier performance (last 20 samples per tier)
        self.tier_performance: dict[str, dict[str, Any]] = {
            "Q2": {
                "tokens_per_sec": deque(maxlen=20),
                "latency_ms": deque(maxlen=20),
                "request_count": 0,
                "error_count": 0,
            },
            "Q3": {
                "tokens_per_sec": deque(maxlen=20),
                "latency_ms": deque(maxlen=20),
                "request_count": 0,
                "error_count": 0,
            },
            "Q4": {
                "tokens_per_sec": deque(maxlen=20),
                "latency_ms": deque(maxlen=20),
                "request_count": 0,
                "error_count": 0,
            },
        }

        # Routing decision matrix
        self.routing_matrix: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"count": 0, "total_score": 0.0}
        )
        self.routing_decision_times: Deque[float] = deque(maxlen=100)
        self.fallback_count = 0
        self.total_routing_decisions = 0

        # Model availability cache (updated periodically)
        self.model_availability = {
            "Q2": {"available": 0, "total": 0},
            "Q3": {"available": 0, "total": 0},
            "Q4": {"available": 0, "total": 0},
        }

        # Resource metrics cache
        self.last_disk_io = None
        self.last_network_io = None
        self.last_io_check = 0.0

        logger.info(f"MetricsCollector initialized with buffer size {max_history}")

    def record_query(
        self,
        tier: str,
        latency_ms: float,
        tokens_generated: int = 0,
        generation_time_ms: float = 0.0,
        is_error: bool = False,
    ) -> None:
        """Record a completed query.

        Thread-safe method to record query metrics.

        Args:
            tier: Tier used (Q2, Q3, Q4)
            latency_ms: Total query latency in milliseconds
            tokens_generated: Number of tokens generated
            generation_time_ms: Time spent generating tokens
            is_error: Whether the query resulted in an error
        """
        with self.lock:
            now = time.time()

            # Record query timestamp and latency
            self.query_timestamps.append(now)
            self.query_latencies.append(latency_ms)
            self.query_tiers.append(tier)

            # Update tier performance
            if tier in self.tier_performance:
                stats = self.tier_performance[tier]
                stats["latency_ms"].append(latency_ms)
                stats["request_count"] += 1

                if is_error:
                    stats["error_count"] += 1

                # Calculate tokens/sec if generation time available
                if generation_time_ms > 0 and tokens_generated > 0:
                    tokens_per_sec = (tokens_generated / generation_time_ms) * 1000
                    stats["tokens_per_sec"].append(tokens_per_sec)

            logger.debug(
                f"Recorded query: tier={tier}, latency={latency_ms:.2f}ms, "
                f"tokens={tokens_generated}, error={is_error}"
            )

    def record_routing_decision(
        self,
        complexity: str,
        tier: str,
        score: float,
        decision_time_ms: float,
        is_fallback: bool = False,
    ) -> None:
        """Record a routing decision.

        Thread-safe method to record routing analytics.

        Args:
            complexity: Complexity level (SIMPLE, MODERATE, COMPLEX)
            tier: Selected tier (Q2, Q3, Q4)
            score: Complexity score
            decision_time_ms: Time taken to make decision
            is_fallback: Whether this was a fallback decision
        """
        with self.lock:
            # Update decision matrix
            key = (complexity, tier)
            self.routing_matrix[key]["count"] += 1
            self.routing_matrix[key]["total_score"] += score

            # Record decision time
            self.routing_decision_times.append(decision_time_ms)

            # Track fallbacks
            if is_fallback:
                self.fallback_count += 1

            self.total_routing_decisions += 1

            logger.debug(
                f"Recorded routing: {complexity} -> {tier} "
                f"(score={score:.2f}, time={decision_time_ms:.2f}ms)"
            )

    def update_model_availability(self, tier: str, available: int, total: int) -> None:
        """Update model availability for a tier.

        Args:
            tier: Tier name (Q2, Q3, Q4)
            available: Number of available models
            total: Total number of models in tier
        """
        with self.lock:
            if tier in self.model_availability:
                self.model_availability[tier]["available"] = available
                self.model_availability[tier]["total"] = total

    def get_query_metrics(self) -> QueryMetrics:
        """Get query metrics with 30-minute rolling window.

        Thread-safe method to generate query metrics snapshot.

        Returns:
            QueryMetrics with time-series data
        """
        with self.lock:
            # Calculate time window (30 minutes)
            now = time.time()
            window_start = now - 1800  # 30 minutes ago

            # Filter queries within window
            recent_queries = [
                (ts, lat, tier)
                for ts, lat, tier in zip(
                    self.query_timestamps, self.query_latencies, self.query_tiers
                )
                if ts >= window_start
            ]

            # Generate timestamps (10-second intervals)
            timestamps: list[str] = []
            query_rate: list[float] = []

            for i in range(18):  # 18 x 10s = 180s = 3 minutes (simplified view)
                bucket_start = now - (i * 10)
                bucket_end = bucket_start + 10
                timestamp = datetime.fromtimestamp(bucket_start, tz=timezone.utc)
                timestamps.insert(0, timestamp.isoformat())

                # Count queries in this 10s bucket
                count = sum(1 for ts, _, _ in recent_queries if bucket_end >= ts >= bucket_start)
                query_rate.insert(0, count / 10.0)  # Convert to queries/sec

            # Calculate totals
            total_queries = len(recent_queries)
            avg_latency = (
                sum(lat for _, lat, _ in recent_queries) / total_queries
                if total_queries > 0
                else 0.0
            )

            # Tier distribution
            tier_distribution = {
                "Q2": sum(1 for _, _, tier in recent_queries if tier == "Q2"),
                "Q3": sum(1 for _, _, tier in recent_queries if tier == "Q3"),
                "Q4": sum(1 for _, _, tier in recent_queries if tier == "Q4"),
            }

            return QueryMetrics(
                timestamps=timestamps,
                query_rate=query_rate,
                total_queries=total_queries,
                avg_latency_ms=round(avg_latency, 2),
                tier_distribution=tier_distribution,  # type: ignore[arg-type]
            )

    def get_tier_metrics(self) -> TierMetricsResponse:
        """Get tier performance metrics.

        Thread-safe method to generate tier metrics snapshot.

        Returns:
            TierMetricsResponse with metrics for all tiers
        """
        with self.lock:
            tiers = []

            for tier_name in ["Q2", "Q3", "Q4"]:
                stats = self.tier_performance[tier_name]

                # Convert deques to lists
                tokens_per_sec = list(stats["tokens_per_sec"])
                latency_ms = list(stats["latency_ms"])

                # Calculate error rate
                total_requests = stats["request_count"]
                error_count = stats["error_count"]
                error_rate = error_count / total_requests if total_requests > 0 else 0.0

                tiers.append(
                    TierMetrics(
                        name=tier_name,  # type: ignore
                        tokens_per_sec=tokens_per_sec,
                        latency_ms=latency_ms,
                        request_count=total_requests,
                        error_rate=round(error_rate, 3),
                    )
                )

            return TierMetricsResponse(tiers=tiers)

    def get_resource_metrics(self) -> ResourceMetrics:
        """Get system resource metrics.

        Returns:
            ResourceMetrics with current system state
        """
        # Get VRAM/GPU metrics (cross-platform)
        from app.services.gpu_monitor import get_gpu_metrics

        vram_used, vram_total, vram_percent, gpu_name = get_gpu_metrics()

        if gpu_name:
            logger.debug(f"GPU metrics from: {gpu_name}")

        # Get CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count(logical=True) or 1

        # Get memory metrics
        memory = psutil.virtual_memory()
        memory_used = memory.used / (1024**3)  # Convert to GB
        memory_total = memory.total / (1024**3)
        memory_percent = memory.percent

        # Get FAISS index size
        faiss_index_size = self._get_faiss_index_size()

        # Get Redis cache key count from cache metrics
        # Note: Actual Redis key count requires async get_cache_size() call
        # Using request count as a proxy metric for cache activity
        redis_cache_size = 0
        try:
            from app.services.cache_metrics import get_cache_metrics

            cache_metrics = get_cache_metrics()
            redis_cache_size = cache_metrics._total_requests
        except RuntimeError:
            # Cache metrics not initialized yet
            pass
        except Exception as e:
            logger.debug(f"Failed to get Redis cache metrics: {e}")

        # Get active WebSocket connections from event bus
        active_connections = 0
        try:
            from app.services.event_bus import get_event_bus

            event_bus_stats = get_event_bus().get_stats()
            active_connections = event_bus_stats.get("active_subscribers", 0)
        except RuntimeError:
            # EventBus not initialized yet
            pass
        except Exception as e:
            logger.debug(f"Failed to get WebSocket connection count: {e}")

        # Get thread pool status
        # Using asyncio event loop thread pool
        thread_pool_active = 0  # Placeholder
        thread_pool_queued = 0  # Placeholder

        # Get disk I/O metrics
        disk_io = self._get_disk_io_metrics()

        # Get network throughput
        network_throughput = self._get_network_metrics()

        return ResourceMetrics(
            vram=VRAMMetrics(
                used=round(vram_used, 2),
                total=round(vram_total, 2),
                percent=round(vram_percent, 1),
            ),
            cpu=CPUMetrics(percent=round(cpu_percent, 1), cores=cpu_cores),
            memory=MemoryMetrics(
                used=round(memory_used, 2),
                total=round(memory_total, 2),
                percent=round(memory_percent, 1),
            ),
            faiss_index_size=faiss_index_size,
            redis_cache_size=redis_cache_size,
            active_connections=active_connections,
            thread_pool_status=ThreadPoolStatus(
                active=thread_pool_active, queued=thread_pool_queued
            ),
            disk_io=disk_io,
            network_throughput=network_throughput,
        )

    def get_routing_metrics(self) -> RoutingMetrics:
        """Get routing analytics metrics.

        Thread-safe method to generate routing metrics snapshot.

        Returns:
            RoutingMetrics with decision matrix and accuracy data
        """
        with self.lock:
            # Build decision matrix
            decision_matrix = []
            for (complexity, tier), data in self.routing_matrix.items():
                count = int(data["count"])
                total_score = float(data["total_score"])
                avg_score = total_score / count if count > 0 else 0.0

                decision_matrix.append(
                    RoutingDecisionMatrix(
                        complexity=complexity,  # type: ignore
                        tier=tier,  # type: ignore
                        count=count,
                        avg_score=round(avg_score, 2),
                    )
                )

            # Calculate accuracy metrics
            avg_decision_time = (
                sum(self.routing_decision_times) / len(self.routing_decision_times)
                if self.routing_decision_times
                else 0.0
            )

            fallback_rate = (
                self.fallback_count / self.total_routing_decisions
                if self.total_routing_decisions > 0
                else 0.0
            )

            # Build model availability list
            model_availability = [
                ModelAvailability(
                    tier=tier,  # type: ignore
                    available=data["available"],
                    total=data["total"],
                )
                for tier, data in self.model_availability.items()
            ]

            return RoutingMetrics(
                decision_matrix=decision_matrix,
                accuracy_metrics=AccuracyMetrics(
                    total_decisions=self.total_routing_decisions,
                    avg_decision_time_ms=round(avg_decision_time, 2),
                    fallback_rate=round(fallback_rate, 3),
                ),
                model_availability=model_availability,
            )

    def _get_faiss_index_size(self) -> int:
        """Get total size of FAISS indexes in bytes.

        Returns:
            Total size in bytes
        """
        try:
            project_root = Path(__file__).parent.parent.parent.parent
            index_dir = project_root / "data" / "faiss_indexes"

            if not index_dir.exists():
                return 0

            total_size = 0
            for file in index_dir.glob("*.index"):
                total_size += file.stat().st_size

            return total_size

        except Exception as e:
            logger.warning(f"Failed to get FAISS index size: {e}")
            return 0

    def _get_disk_io_metrics(self) -> DiskIOMetrics:
        """Get disk I/O metrics.

        Returns:
            DiskIOMetrics with read/write throughput
        """
        try:
            now = time.time()

            # Sample disk I/O counters
            disk_io = psutil.disk_io_counters()

            if self.last_disk_io is None or (now - self.last_io_check) > 1.0:
                # First reading or stale data - return zeros
                self.last_disk_io = disk_io
                self.last_io_check = now
                return DiskIOMetrics(read_mbps=0.0, write_mbps=0.0)

            # Calculate throughput
            time_delta = now - self.last_io_check
            read_bytes = disk_io.read_bytes - self.last_disk_io.read_bytes
            write_bytes = disk_io.write_bytes - self.last_disk_io.write_bytes

            read_mbps = (read_bytes / time_delta) / (1024 * 1024)
            write_mbps = (write_bytes / time_delta) / (1024 * 1024)

            # Update last reading
            self.last_disk_io = disk_io
            self.last_io_check = now

            return DiskIOMetrics(read_mbps=round(read_mbps, 2), write_mbps=round(write_mbps, 2))

        except Exception as e:
            logger.warning(f"Failed to get disk I/O metrics: {e}")
            return DiskIOMetrics(read_mbps=0.0, write_mbps=0.0)

    def _get_network_metrics(self) -> NetworkThroughputMetrics:
        """Get network throughput metrics.

        Returns:
            NetworkThroughputMetrics with RX/TX throughput
        """
        try:
            now = time.time()

            # Sample network I/O counters
            net_io = psutil.net_io_counters()

            if self.last_network_io is None or (now - self.last_io_check) > 1.0:
                # First reading or stale data - return zeros
                self.last_network_io = net_io
                return NetworkThroughputMetrics(rx_mbps=0.0, tx_mbps=0.0)

            # Calculate throughput
            time_delta = now - self.last_io_check
            rx_bytes = net_io.bytes_recv - self.last_network_io.bytes_recv
            tx_bytes = net_io.bytes_sent - self.last_network_io.bytes_sent

            rx_mbps = (rx_bytes / time_delta) / (1024 * 1024)
            tx_mbps = (tx_bytes / time_delta) / (1024 * 1024)

            # Update last reading
            self.last_network_io = net_io

            return NetworkThroughputMetrics(rx_mbps=round(rx_mbps, 2), tx_mbps=round(tx_mbps, 2))

        except Exception as e:
            logger.warning(f"Failed to get network metrics: {e}")
            return NetworkThroughputMetrics(rx_mbps=0.0, tx_mbps=0.0)


# Global singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector.

    Returns:
        MetricsCollector singleton instance
    """
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(max_history=180)
        logger.info("Created global MetricsCollector instance")

    return _metrics_collector
