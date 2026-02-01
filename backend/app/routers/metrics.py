"""Metrics endpoints.

This module provides API endpoints for retrieving system metrics including:
- Query time-series data
- Tier performance metrics
- System resource utilization
- Routing analytics

Also includes WebSocket endpoint for real-time metrics streaming.
"""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.models.metrics import (
    QueryMetrics,
    TierMetricsResponse,
    ResourceMetrics,
    RoutingMetrics,
    MetricsUpdate,
    HistoricalMetrics,
    ContextUtilization
)
from app.services.metrics_collector import get_metrics_collector

# Application start time for uptime calculation (set during startup)
import time
_app_start_time: float = time.time()


logger = get_logger(__name__)
router = APIRouter(prefix="/api/metrics")


@router.get(
    "/queries",
    response_model=QueryMetrics,
    summary="Get query metrics",
    description="""
    Retrieve time-series query data for the last 30 minutes.

    Returns data points at 10-second intervals showing:
    - Query rate (queries/sec)
    - Total queries processed
    - Average latency
    - Distribution across tiers (Q2/Q3/Q4)

    **Use Case:** ASCII line charts in MetricsPage

    **Performance Target:** <100ms response time
    """,
    responses={
        200: {
            "description": "Query metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "timestamps": [
                            "2025-11-09T10:00:00Z",
                            "2025-11-09T10:00:10Z",
                            "2025-11-09T10:00:20Z"
                        ],
                        "queryRate": [0.5, 0.8, 1.2],
                        "totalQueries": 450,
                        "avgLatencyMs": 2350.5,
                        "tierDistribution": {
                            "Q2": 300,
                            "Q3": 100,
                            "Q4": 50
                        }
                    }
                }
            }
        }
    }
)
async def get_query_metrics() -> QueryMetrics:
    """Get query metrics with 30-minute rolling window.

    Returns time-series data for query rate visualization.

    Returns:
        QueryMetrics with timestamps, rates, and distribution
    """
    collector = get_metrics_collector()
    metrics = collector.get_query_metrics()

    logger.debug(
        "Query metrics retrieved",
        extra={
            'total_queries': metrics.total_queries,
            'avg_latency_ms': metrics.avg_latency_ms
        }
    )

    return metrics


@router.get(
    "/tiers",
    response_model=TierMetricsResponse,
    summary="Get tier performance metrics",
    description="""
    Retrieve performance metrics for all model tiers (Q2/Q3/Q4).

    Returns the last 20 data points for each tier showing:
    - Token generation rate (tokens/sec)
    - Query latency (ms)
    - Request count
    - Error rate

    **Use Case:** Sparklines and tier comparison panels

    **Performance Target:** <100ms response time
    """,
    responses={
        200: {
            "description": "Tier metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "tiers": [
                            {
                                "name": "Q2",
                                "tokensPerSec": [45.2, 48.1, 46.7],
                                "latencyMs": [1200, 1150, 1180],
                                "requestCount": 1250,
                                "errorRate": 0.015
                            },
                            {
                                "name": "Q3",
                                "tokensPerSec": [38.5, 39.2, 37.8],
                                "latencyMs": [3200, 3100, 3250],
                                "requestCount": 680,
                                "errorRate": 0.008
                            },
                            {
                                "name": "Q4",
                                "tokensPerSec": [28.3, 29.1, 27.9],
                                "latencyMs": [8500, 8300, 8700],
                                "requestCount": 320,
                                "errorRate": 0.005
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_tier_metrics() -> TierMetricsResponse:
    """Get tier performance metrics.

    Returns performance statistics for Q2, Q3, and Q4 tiers.

    Returns:
        TierMetricsResponse with metrics for all tiers
    """
    collector = get_metrics_collector()
    metrics = collector.get_tier_metrics()

    logger.debug(
        "Tier metrics retrieved",
        extra={
            'tier_count': len(metrics.tiers)
        }
    )

    return metrics


@router.get(
    "/resources",
    response_model=ResourceMetrics,
    summary="Get system resource metrics",
    description="""
    Retrieve current system resource utilization metrics.

    Returns 9-metric grid data including:
    - VRAM usage (used/total/percent)
    - CPU usage (percent/cores)
    - Memory usage (used/total/percent)
    - FAISS index size (bytes)
    - Redis cache size (bytes)
    - Active WebSocket connections
    - Thread pool status (active/queued)
    - Disk I/O (read/write MB/s)
    - Network throughput (RX/TX MB/s)

    **Use Case:** Resource monitoring grid in MetricsPage

    **Performance Target:** <100ms response time
    """,
    responses={
        200: {
            "description": "Resource metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "vram": {
                            "used": 8.5,
                            "total": 24.0,
                            "percent": 35.4
                        },
                        "cpu": {
                            "percent": 45.2,
                            "cores": 16
                        },
                        "memory": {
                            "used": 12.3,
                            "total": 32.0,
                            "percent": 38.4
                        },
                        "faissIndexSize": 524288000,
                        "redisCacheSize": 104857600,
                        "activeConnections": 5,
                        "threadPoolStatus": {
                            "active": 4,
                            "queued": 2
                        },
                        "diskIO": {
                            "readMBps": 15.3,
                            "writeMBps": 8.7
                        },
                        "networkThroughput": {
                            "rxMBps": 2.5,
                            "txMBps": 1.8
                        }
                    }
                }
            }
        }
    }
)
async def get_resource_metrics() -> ResourceMetrics:
    """Get system resource utilization metrics.

    Returns current resource usage across multiple subsystems.

    Returns:
        ResourceMetrics with complete resource snapshot
    """
    collector = get_metrics_collector()
    metrics = collector.get_resource_metrics()

    logger.debug(
        "Resource metrics retrieved",
        extra={
            'cpu_percent': metrics.cpu.percent,
            'memory_percent': metrics.memory.percent,
            'vram_percent': metrics.vram.percent
        }
    )

    return metrics


@router.get(
    "/routing",
    response_model=RoutingMetrics,
    summary="Get routing analytics",
    description="""
    Retrieve routing decision analytics and accuracy metrics.

    Returns:
    - Decision matrix (complexity x tier with counts and scores)
    - Accuracy metrics (total decisions, avg time, fallback rate)
    - Model availability by tier (available/total)

    **Use Case:** Routing analytics panel and decision matrix visualization

    **Performance Target:** <100ms response time
    """,
    responses={
        200: {
            "description": "Routing metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "decisionMatrix": [
                            {
                                "complexity": "SIMPLE",
                                "tier": "Q2",
                                "count": 850,
                                "avgScore": 1.8
                            },
                            {
                                "complexity": "MODERATE",
                                "tier": "Q3",
                                "count": 450,
                                "avgScore": 5.2
                            },
                            {
                                "complexity": "COMPLEX",
                                "tier": "Q4",
                                "count": 180,
                                "avgScore": 8.7
                            }
                        ],
                        "accuracyMetrics": {
                            "totalDecisions": 2250,
                            "avgDecisionTimeMs": 12.5,
                            "fallbackRate": 0.03
                        },
                        "modelAvailability": [
                            {
                                "tier": "Q2",
                                "available": 3,
                                "total": 3
                            },
                            {
                                "tier": "Q3",
                                "available": 2,
                                "total": 2
                            },
                            {
                                "tier": "Q4",
                                "available": 1,
                                "total": 1
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_routing_metrics() -> RoutingMetrics:
    """Get routing analytics metrics.

    Returns routing decision matrix and accuracy data.

    Returns:
        RoutingMetrics with decision analytics
    """
    collector = get_metrics_collector()
    metrics = collector.get_routing_metrics()

    logger.debug(
        "Routing metrics retrieved",
        extra={
            'total_decisions': metrics.accuracy_metrics.total_decisions,
            'fallback_rate': metrics.accuracy_metrics.fallback_rate
        }
    )

    return metrics


@router.get(
    "/historical",
    response_model=HistoricalMetrics,
    summary="Get lifetime/historical metrics",
    description="""
    Retrieve aggregate metrics since system startup.

    Returns lifetime statistics including:
    - Total requests and errors
    - Error rate percentage
    - Latency percentiles (avg, P95, P99)
    - System uptime (days/hours)
    - Cache performance (hits, misses, hit rate)

    **Use Case:** Historical Metrics Panel showing system lifetime statistics

    **Performance Target:** <100ms response time
    """,
    responses={
        200: {
            "description": "Historical metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "totalRequests": 125000,
                        "totalErrors": 125,
                        "errorRate": 0.1,
                        "avgLatencyMs": 2350.5,
                        "p95LatencyMs": 4230.9,
                        "p99LatencyMs": 5877.5,
                        "uptimeDays": 45,
                        "uptimeHours": 12,
                        "uptimeSeconds": 3931200,
                        "totalCacheHits": 87500,
                        "totalCacheMisses": 37500,
                        "cacheHitRate": 70.0
                    }
                }
            }
        }
    }
)
async def get_historical_metrics() -> HistoricalMetrics:
    """Get lifetime/historical metrics since system startup.

    Aggregates data from metrics collector and cache metrics to provide
    a comprehensive view of system performance since startup.

    Returns:
        HistoricalMetrics with lifetime statistics
    """
    collector = get_metrics_collector()

    # Calculate uptime from app start time
    uptime_seconds = int(time.time() - _app_start_time)
    uptime_days = uptime_seconds // 86400
    uptime_hours = (uptime_seconds % 86400) // 3600

    # Get tier metrics for aggregate statistics
    tier_metrics = collector.get_tier_metrics()

    # Calculate totals across all tiers
    total_requests = sum(t.request_count for t in tier_metrics.tiers)
    total_errors = 0
    total_latency = 0.0
    latency_samples = []

    for tier in tier_metrics.tiers:
        # Estimate errors from error rate
        tier_errors = int(tier.request_count * tier.error_rate)
        total_errors += tier_errors
        # Collect latency samples for percentile calculation
        latency_samples.extend(tier.latency_ms)

    # Calculate error rate
    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0

    # Calculate latency statistics
    if latency_samples:
        avg_latency = sum(latency_samples) / len(latency_samples)
        sorted_latencies = sorted(latency_samples)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p99_idx = int(len(sorted_latencies) * 0.99)
        p95_latency = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]
        p99_latency = sorted_latencies[min(p99_idx, len(sorted_latencies) - 1)]
    else:
        avg_latency = 0.0
        p95_latency = 0.0
        p99_latency = 0.0

    # Get cache metrics
    total_cache_hits = 0
    total_cache_misses = 0
    try:
        from app.services.cache_metrics import get_cache_metrics
        cache_metrics = get_cache_metrics()
        total_cache_hits = cache_metrics._cache_hits
        total_cache_misses = cache_metrics._cache_misses
    except (RuntimeError, AttributeError):
        # Cache metrics not initialized or no attributes
        pass

    cache_total = total_cache_hits + total_cache_misses
    cache_hit_rate = (total_cache_hits / cache_total * 100) if cache_total > 0 else 0.0

    logger.debug(
        "Historical metrics retrieved",
        extra={
            'total_requests': total_requests,
            'total_errors': total_errors,
            'uptime_days': uptime_days
        }
    )

    return HistoricalMetrics(
        total_requests=total_requests,
        total_errors=total_errors,
        error_rate=round(error_rate, 2),
        avg_latency_ms=round(avg_latency, 2),
        p95_latency_ms=round(p95_latency, 2),
        p99_latency_ms=round(p99_latency, 2),
        uptime_days=uptime_days,
        uptime_hours=uptime_hours,
        uptime_seconds=uptime_seconds,
        total_cache_hits=total_cache_hits,
        total_cache_misses=total_cache_misses,
        cache_hit_rate=round(cache_hit_rate, 2)
    )


@router.get(
    "/context-utilization",
    response_model=ContextUtilization,
    summary="Get context window utilization",
    description="""
    Retrieve real-time context window utilization across active queries.

    Returns aggregate statistics including:
    - Average utilization percentage
    - Total tokens currently in use
    - Total context window capacity
    - Number of active queries with context allocation

    **Use Case:** System Status Panel context utilization metric

    **Performance Target:** <50ms response time
    """,
    responses={
        200: {
            "description": "Context utilization retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "percentage": 65.5,
                        "tokensUsed": 52400,
                        "tokensTotal": 80000,
                        "activeQueries": 10
                    }
                }
            }
        }
    }
)
async def get_context_utilization() -> ContextUtilization:
    """Get real-time context window utilization.

    Aggregates context allocation data from all active queries to provide
    a real-time view of context window usage.

    Returns:
        ContextUtilization with aggregate statistics
    """
    try:
        from app.services.context_state import get_context_state_manager
        context_manager = get_context_state_manager()
        stats = context_manager.get_stats()

        # Calculate aggregate stats from tracked allocations
        total_allocations = stats.get("total_allocations", 0)
        avg_utilization = stats.get("avg_utilization_percentage", 0.0)

        # Estimate tokens based on average context window size
        # Assumes 8192 tokens default context window per query
        default_context_size = 8192
        tokens_total = total_allocations * default_context_size if total_allocations > 0 else default_context_size
        tokens_used = int((avg_utilization / 100) * tokens_total)

        logger.debug(
            "Context utilization retrieved",
            extra={
                'percentage': avg_utilization,
                'active_queries': total_allocations
            }
        )

        return ContextUtilization(
            percentage=round(avg_utilization, 1),
            tokens_used=tokens_used,
            tokens_total=tokens_total,
            active_queries=total_allocations
        )

    except RuntimeError:
        # Context state manager not initialized
        logger.warning("Context state manager not initialized, returning defaults")
        return ContextUtilization(
            percentage=0.0,
            tokens_used=0,
            tokens_total=8192,
            active_queries=0
        )


@router.websocket("/ws")
async def websocket_metrics(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time metrics streaming.

    Streams complete metrics update at 1Hz (1 update per second).

    **Connection Lifecycle:**
    1. Client connects via WebSocket
    2. Server sends initial metrics snapshot
    3. Server sends updates every 1 second
    4. Connection stays open until client disconnects

    **Message Format:**
    ```json
    {
        "type": "metrics_update",
        "timestamp": "2025-11-09T10:30:00Z",
        "queries": { ... },
        "resources": { ... },
        "routing": { ... }
    }
    ```

    **Example Client Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/metrics/ws');
    ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        console.log('Metrics update:', update);
    };
    ```

    Args:
        websocket: WebSocket connection instance
    """
    await websocket.accept()
    logger.info("Metrics WebSocket client connected")

    collector = get_metrics_collector()

    try:
        # Send initial metrics snapshot
        initial_update = _create_metrics_update(collector)
        await websocket.send_json(initial_update.model_dump(by_alias=True))

        # Stream updates at 1Hz
        while True:
            # Wait 1 second
            await asyncio.sleep(1.0)

            # Generate metrics update
            update = _create_metrics_update(collector)

            # Send to client
            await websocket.send_json(update.model_dump(by_alias=True))

            logger.debug("Sent metrics update to client")

    except WebSocketDisconnect:
        logger.info("Metrics WebSocket client disconnected normally")

    except Exception as e:
        logger.error(f"Metrics WebSocket error: {e}", exc_info=True)

    finally:
        logger.info("Metrics WebSocket connection closed")


def _create_metrics_update(collector) -> MetricsUpdate:
    """Create a complete metrics update message.

    Args:
        collector: MetricsCollector instance

    Returns:
        MetricsUpdate with all current metrics
    """
    return MetricsUpdate(
        timestamp=datetime.now(timezone.utc).isoformat(),
        queries=collector.get_query_metrics(),
        resources=collector.get_resource_metrics(),
        routing=collector.get_routing_metrics()
    )
