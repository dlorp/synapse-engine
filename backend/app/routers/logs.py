"""Log Query REST API Endpoints.

This module provides REST API endpoints for querying system logs captured by
the LogAggregator service. Supports filtering by level, source, search text,
and time range. Returns paginated results with comprehensive statistics.

Endpoints:
- GET /api/logs - Query logs with filtering
- GET /api/logs/sources - List unique log sources
- GET /api/logs/stats - Get log statistics
- DELETE /api/logs - Clear log buffer (admin)

Author: Backend Architect
Task: Comprehensive Log Aggregation and Streaming System
"""

from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.log_aggregator import get_log_aggregator

logger = get_logger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])


# Response models
class LogQueryResponse(BaseModel):
    """Response model for log query endpoint.

    Attributes:
        count: Number of logs returned
        total_available: Total logs in buffer matching filters
        logs: List of log entry dictionaries
    """

    count: int = Field(..., description="Number of logs returned")
    total_available: int = Field(..., description="Total logs matching filters")
    logs: List[dict] = Field(..., description="Log entries")


class LogSourcesResponse(BaseModel):
    """Response model for log sources endpoint.

    Attributes:
        count: Number of unique sources
        sources: List of source names
    """

    count: int = Field(..., description="Number of unique sources")
    sources: List[str] = Field(..., description="List of source names")


class LogStatsResponse(BaseModel):
    """Response model for log statistics endpoint.

    Attributes:
        total_logs: Total logs in buffer
        max_logs: Maximum buffer size
        buffer_utilization: Buffer usage percentage
        by_level: Count of logs per level
        unique_sources: Number of unique sources
        oldest_log_time: Timestamp of oldest log
        newest_log_time: Timestamp of newest log
        uptime_seconds: Aggregator uptime in seconds
    """

    total_logs: int = Field(..., description="Total logs in buffer")
    max_logs: int = Field(..., description="Maximum buffer size")
    buffer_utilization: float = Field(..., description="Buffer usage percentage")
    by_level: dict = Field(..., description="Count of logs per level")
    unique_sources: int = Field(..., description="Number of unique sources")
    oldest_log_time: Optional[str] = Field(None, description="Oldest log timestamp")
    newest_log_time: Optional[str] = Field(None, description="Newest log timestamp")
    uptime_seconds: float = Field(..., description="Aggregator uptime")


class ClearLogsResponse(BaseModel):
    """Response model for clear logs endpoint.

    Attributes:
        message: Success message
        cleared_at: Timestamp when logs were cleared
    """

    message: str = Field(..., description="Success message")
    cleared_at: str = Field(..., description="Clear timestamp")


@router.get("/", response_model=LogQueryResponse)
async def get_logs(
    level: Optional[str] = Query(
        None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    ),
    source: Optional[str] = Query(
        None, description="Filter by source (substring match, case-insensitive)"
    ),
    search: Optional[str] = Query(
        None, description="Search in message text (substring match, case-insensitive)"
    ),
    start_time: Optional[str] = Query(
        None, description="Filter logs after this timestamp (ISO 8601)"
    ),
    end_time: Optional[str] = Query(
        None, description="Filter logs before this timestamp (ISO 8601)"
    ),
    limit: int = Query(
        500, ge=1, le=2000, description="Maximum logs to return (default 500, max 2000)"
    ),
) -> LogQueryResponse:
    """Query system logs with optional filtering.

    Returns logs from the aggregator buffer matching filter criteria. Logs are
    returned in reverse chronological order (newest first). All filters are
    applied as AND conditions.

    The log aggregator captures ALL logs from Python's logging system including:
    - FastAPI request/response logs
    - Model server health checks
    - CGRAG retrieval operations
    - Cache operations
    - Error and warning messages
    - All service logs (prx:, mem:, rec:, nrl:)

    Args:
        level: Filter by exact log level (case-insensitive)
        source: Filter by logger name (substring match)
        search: Search message text (substring match)
        start_time: ISO 8601 timestamp for time range start
        end_time: ISO 8601 timestamp for time range end
        limit: Maximum logs to return (1-2000)

    Returns:
        LogQueryResponse with filtered logs and metadata

    Example:
        GET /api/logs?level=ERROR&limit=50
        GET /api/logs?source=app.services.models&search=health
        GET /api/logs?start_time=2025-11-13T20:00:00Z
    """
    try:
        aggregator = get_log_aggregator()

        # Query logs with filters
        logs = await aggregator.get_logs(
            level=level,
            source=source,
            search=search,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        logger.info(
            f"Log query returned {len(logs)} logs",
            extra={
                "level_filter": level,
                "source_filter": source,
                "search_filter": search,
                "result_count": len(logs),
            },
        )

        return LogQueryResponse(
            count=len(logs),
            total_available=len(logs),  # Same as count for now (no pagination)
            logs=logs,
        )

    except RuntimeError as e:
        logger.error(f"Log aggregator not initialized: {e}")
        raise HTTPException(
            status_code=503, detail="Log aggregation service not available"
        )
    except Exception as e:
        logger.error(f"Error querying logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query logs: {str(e)}")


@router.get("/sources", response_model=LogSourcesResponse)
async def get_log_sources() -> LogSourcesResponse:
    """Get list of unique log sources.

    Returns all unique logger names that have emitted logs since the aggregator
    started. Useful for building filter dropdowns in UIs.

    Returns:
        LogSourcesResponse with sorted list of source names

    Example Sources:
        - app.main
        - app.routers.query
        - app.services.models
        - app.services.cgrag
        - app.services.cache_metrics
        - uvicorn.access
        - uvicorn.error

    Example:
        GET /api/logs/sources
    """
    try:
        aggregator = get_log_aggregator()
        sources = await aggregator.get_sources()

        logger.debug(f"Retrieved {len(sources)} unique log sources")

        return LogSourcesResponse(count=len(sources), sources=sources)

    except RuntimeError as e:
        logger.error(f"Log aggregator not initialized: {e}")
        raise HTTPException(
            status_code=503, detail="Log aggregation service not available"
        )
    except Exception as e:
        logger.error(f"Error retrieving log sources: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve log sources: {str(e)}"
        )


@router.get("/stats", response_model=LogStatsResponse)
async def get_log_stats() -> LogStatsResponse:
    """Get log aggregator statistics.

    Returns comprehensive statistics about the log buffer including:
    - Total logs in buffer
    - Buffer capacity and utilization
    - Breakdown by log level
    - Number of unique sources
    - Time range of buffered logs
    - Aggregator uptime

    Useful for monitoring log volume, identifying noisy loggers, and
    understanding system activity patterns.

    Returns:
        LogStatsResponse with detailed statistics

    Example:
        GET /api/logs/stats
    """
    try:
        aggregator = get_log_aggregator()
        stats = await aggregator.get_stats()

        logger.debug("Retrieved log aggregator statistics")

        return LogStatsResponse(
            total_logs=stats["total_logs"],
            max_logs=stats["max_logs"],
            buffer_utilization=stats["buffer_utilization"],
            by_level=stats["by_level"],
            unique_sources=stats["unique_sources"],
            oldest_log_time=stats["oldest_log_time"],
            newest_log_time=stats["newest_log_time"],
            uptime_seconds=stats["uptime_seconds"],
        )

    except RuntimeError as e:
        logger.error(f"Log aggregator not initialized: {e}")
        raise HTTPException(
            status_code=503, detail="Log aggregation service not available"
        )
    except Exception as e:
        logger.error(f"Error retrieving log stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve log statistics: {str(e)}"
        )


@router.delete("/", response_model=ClearLogsResponse)
async def clear_logs() -> ClearLogsResponse:
    """Clear all logs from the aggregator buffer.

    Removes all logs from the circular buffer. This does not affect the
    aggregator configuration or stop log collection. New logs will continue
    to be captured after clearing.

    **Warning:** This operation is irreversible. Cleared logs cannot be recovered.

    Use cases:
    - Testing log aggregation behavior
    - Clearing old logs before a demo
    - Reducing memory usage after investigating an issue
    - Resetting buffer after a long-running session

    Returns:
        ClearLogsResponse with success message and timestamp

    Example:
        DELETE /api/logs
    """
    try:
        aggregator = get_log_aggregator()

        # Get stats before clearing
        stats = await aggregator.get_stats()
        cleared_count = stats["total_logs"]

        # Clear buffer
        await aggregator.clear()

        from datetime import datetime

        cleared_at = datetime.utcnow().isoformat() + "Z"

        logger.info(
            f"Log buffer cleared - removed {cleared_count} logs",
            extra={"cleared_count": cleared_count},
        )

        return ClearLogsResponse(
            message=f"Successfully cleared {cleared_count} logs from buffer",
            cleared_at=cleared_at,
        )

    except RuntimeError as e:
        logger.error(f"Log aggregator not initialized: {e}")
        raise HTTPException(
            status_code=503, detail="Log aggregation service not available"
        )
    except Exception as e:
        logger.error(f"Error clearing logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")
