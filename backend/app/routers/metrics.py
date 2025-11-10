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
    MetricsUpdate
)
from app.services.metrics_collector import get_metrics_collector


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
