"""Log Aggregation Service for System-Wide Log Collection and Streaming.

This module provides a centralized log aggregation system that captures ALL logs
from backend services and makes them queryable via REST API and streamable via
WebSocket. It uses a circular buffer for efficient memory usage and integrates
with the EventBus for real-time broadcasting.

Features:
- Captures logs from all Python loggers (FastAPI, model servers, CGRAG, etc.)
- Thread-safe circular buffer with configurable size
- Real-time WebSocket streaming via EventBus integration
- REST API for log querying with filtering (level, source, search text)
- Log statistics and source tracking
- JSON-structured log entries with metadata

Author: Backend Architect
Task: Comprehensive Log Aggregation and Streaming System
"""

import asyncio
import time
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class LogEntry:
    """Structured log entry with metadata.

    Attributes:
        timestamp: ISO 8601 timestamp string
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        source: Logger name (e.g., "app.services.models")
        message: Log message text
        extra: Additional metadata (pathname, lineno, funcName, etc.)
    """

    def __init__(
        self,
        timestamp: str,
        level: str,
        source: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        service_tag: Optional[str] = None,
    ):
        """Initialize log entry.

        Args:
            timestamp: ISO 8601 timestamp string
            level: Log level name
            source: Logger name
            message: Log message
            extra: Optional metadata dictionary
            request_id: Optional request ID for tracing
            trace_id: Optional trace ID for distributed tracing
            service_tag: Optional service tag (prx:, mem:, etc.)
        """
        self.timestamp = timestamp
        self.level = level
        self.source = source
        self.message = message
        self.extra = extra or {}
        self.request_id = request_id
        self.trace_id = trace_id
        self.service_tag = service_tag

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for JSON serialization.

        Returns:
            Dictionary with all log entry fields
        """
        result = {
            "timestamp": self.timestamp,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "extra": self.extra,
        }

        # Add optional fields if present
        if self.request_id:
            result["request_id"] = self.request_id
        if self.trace_id:
            result["trace_id"] = self.trace_id
        if self.service_tag:
            result["service_tag"] = self.service_tag

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEntry":
        """Create LogEntry from dictionary.

        Args:
            data: Dictionary with log entry fields

        Returns:
            LogEntry instance
        """
        return cls(
            timestamp=data["timestamp"],
            level=data["level"],
            source=data["source"],
            message=data["message"],
            extra=data.get("extra", {}),
            request_id=data.get("request_id"),
            trace_id=data.get("trace_id"),
            service_tag=data.get("service_tag"),
        )


class LogAggregator:
    """Central log aggregation service with real-time streaming.

    Aggregates logs from all backend services using a circular buffer for
    efficient memory usage. Broadcasts logs in real-time via EventBus for
    WebSocket streaming. Provides query methods for log filtering and retrieval.

    The aggregator uses asyncio locks for thread-safety and integrates with
    the existing EventBus infrastructure for seamless WebSocket broadcasting.

    Architecture:
        Python Logger -> LogHandler -> LogAggregator -> Circular Buffer
                                                     -> EventBus -> WebSocket

    Example Usage:
        # Add log
        await log_aggregator.add_log(
            level="INFO",
            source="app.services.models",
            message="Model server started on port 8080"
        )

        # Query logs
        logs = await log_aggregator.get_logs(level="ERROR", limit=50)

        # Get statistics
        stats = await log_aggregator.get_stats()

    Attributes:
        max_logs: Maximum number of logs to buffer
        logs: Circular buffer (deque) of LogEntry instances
        _lock: AsyncIO lock for thread-safe operations
        _start_time: Timestamp when aggregator was initialized
    """

    def __init__(self, max_logs: int = 1000):
        """Initialize log aggregator with circular buffer.

        Args:
            max_logs: Maximum logs to buffer (older logs auto-discarded)
        """
        self.max_logs = max_logs
        self.logs: Deque[LogEntry] = deque(maxlen=max_logs)
        self._lock = asyncio.Lock()
        self._start_time = time.time()

        logger.info(
            f"LogAggregator initialized (max_logs={max_logs})",
            extra={"max_logs": max_logs},
        )

    async def add_log(
        self,
        level: str,
        source: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        service_tag: Optional[str] = None,
    ) -> None:
        """Add log entry and broadcast via EventBus.

        Thread-safe method to add a log entry to the circular buffer and
        broadcast it in real-time to all WebSocket subscribers via EventBus.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            source: Logger name (e.g., "app.routers.query")
            message: Log message text
            extra: Optional metadata (pathname, lineno, funcName, etc.)
            request_id: Optional request ID for request tracing
            trace_id: Optional trace ID for distributed tracing
            service_tag: Optional service tag (prx:, mem:, rec:, etc.)
        """
        async with self._lock:
            # Create log entry
            entry = LogEntry(
                timestamp=datetime.utcnow().isoformat() + "Z",
                level=level,
                source=source,
                message=message,
                extra=extra,
                request_id=request_id,
                trace_id=trace_id,
                service_tag=service_tag,
            )

            # Add to circular buffer (auto-discards oldest if full)
            self.logs.append(entry)

        # Broadcast to WebSocket clients via EventBus (outside lock)
        await self._broadcast_log(entry)

    async def _broadcast_log(self, entry: LogEntry) -> None:
        """Broadcast log entry to WebSocket subscribers via EventBus.

        Publishes log entry as a system event with event_type="log" for
        real-time streaming to connected WebSocket clients. Uses the
        existing EventBus infrastructure for decoupled broadcasting.

        Args:
            entry: LogEntry to broadcast
        """
        try:
            from app.models.events import EventSeverity, EventType
            from app.services.event_bus import get_event_bus

            event_bus = get_event_bus()

            # Map log level to event severity
            severity_map = {
                "DEBUG": EventSeverity.INFO,
                "INFO": EventSeverity.INFO,
                "WARNING": EventSeverity.WARNING,
                "ERROR": EventSeverity.ERROR,
                "CRITICAL": EventSeverity.ERROR,
            }

            severity = severity_map.get(entry.level, EventSeverity.INFO)

            # Publish as system event
            await event_bus.publish(
                event_type=EventType.LOG,
                message=entry.message,
                severity=severity,
                metadata=entry.to_dict(),
            )

        except Exception as e:
            # Don't let broadcast failures crash the application
            # Just log the error (but avoid infinite recursion!)
            if logger.name != __name__:
                logger.error(f"Failed to broadcast log to EventBus: {e}")

    async def get_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Query logs with filtering.

        Returns logs matching filter criteria, sorted by timestamp (newest first).
        All filters are applied as AND conditions.

        Args:
            level: Filter by log level (exact match, case-insensitive)
            source: Filter by source (substring match, case-insensitive)
            search: Search in message text (substring match, case-insensitive)
            start_time: Filter logs after this timestamp (ISO 8601)
            end_time: Filter logs before this timestamp (ISO 8601)
            limit: Maximum logs to return (default 500, max 2000)

        Returns:
            List of log entry dictionaries, newest first

        Example:
            # Get last 50 ERROR logs from model services
            logs = await aggregator.get_logs(
                level="ERROR",
                source="app.services.models",
                limit=50
            )
        """
        async with self._lock:
            filtered_logs = list(self.logs)

        # Filter by level (exact match, case-insensitive)
        if level:
            level_upper = level.upper()
            filtered_logs = [log for log in filtered_logs if log.level.upper() == level_upper]

        # Filter by source (substring match, case-insensitive)
        if source:
            source_lower = source.lower()
            filtered_logs = [log for log in filtered_logs if source_lower in log.source.lower()]

        # Filter by search text in message (substring match, case-insensitive)
        if search:
            search_lower = search.lower()
            filtered_logs = [log for log in filtered_logs if search_lower in log.message.lower()]

        # Filter by time range
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]

        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]

        # Apply limit (most recent first)
        # Circular buffer is already chronologically ordered
        filtered_logs = filtered_logs[-limit:]

        # Convert to dictionaries and reverse (newest first)
        return [log.to_dict() for log in reversed(filtered_logs)]

    async def get_sources(self) -> List[str]:
        """Get list of unique log sources.

        Returns all unique logger names that have emitted logs, sorted
        alphabetically. Useful for building filter UIs.

        Returns:
            Sorted list of unique source names
        """
        async with self._lock:
            sources = set(log.source for log in self.logs)

        return sorted(sources)

    async def get_stats(self) -> Dict[str, Any]:
        """Get log aggregator statistics.

        Returns comprehensive statistics about the log buffer including
        counts by level, unique sources, buffer utilization, and uptime.

        Returns:
            Dictionary with statistics:
                - total_logs: Current number of logs in buffer
                - max_logs: Maximum buffer size
                - buffer_utilization: Percentage of buffer used
                - by_level: Count of logs per level
                - unique_sources: Number of unique log sources
                - oldest_log_time: Timestamp of oldest log in buffer
                - newest_log_time: Timestamp of newest log in buffer
                - uptime_seconds: Time since aggregator initialization
        """
        async with self._lock:
            total = len(self.logs)

            # Count logs by level
            by_level: Dict[str, int] = {}
            for log in self.logs:
                by_level[log.level] = by_level.get(log.level, 0) + 1

            # Get unique sources count
            unique_sources = len(set(log.source for log in self.logs))

            # Get time range
            oldest_time = self.logs[0].timestamp if self.logs else None
            newest_time = self.logs[-1].timestamp if self.logs else None

        uptime = time.time() - self._start_time
        buffer_utilization = (total / self.max_logs) * 100 if self.max_logs > 0 else 0

        return {
            "total_logs": total,
            "max_logs": self.max_logs,
            "buffer_utilization": round(buffer_utilization, 2),
            "by_level": by_level,
            "unique_sources": unique_sources,
            "oldest_log_time": oldest_time,
            "newest_log_time": newest_time,
            "uptime_seconds": round(uptime, 2),
        }

    async def clear(self) -> None:
        """Clear all logs from buffer.

        Thread-safe operation to clear the circular buffer. Useful for
        testing or periodic cleanup. Does not affect aggregator configuration.
        """
        async with self._lock:
            self.logs.clear()

        logger.info("Log buffer cleared")


# Global log aggregator instance (initialized in main.py lifespan)
_log_aggregator: Optional[LogAggregator] = None


def get_log_aggregator() -> LogAggregator:
    """Get the global log aggregator instance.

    Returns:
        Global LogAggregator instance

    Raises:
        RuntimeError: If log aggregator not initialized
    """
    if _log_aggregator is None:
        raise RuntimeError("LogAggregator not initialized - call init_log_aggregator() first")
    return _log_aggregator


def init_log_aggregator(max_logs: int = 1000) -> LogAggregator:
    """Initialize the global log aggregator instance.

    Should be called during application startup in the lifespan context
    manager. Creates a LogAggregator with the specified buffer size.

    Args:
        max_logs: Maximum logs to buffer (default 1000)

    Returns:
        Initialized LogAggregator instance
    """
    global _log_aggregator
    _log_aggregator = LogAggregator(max_logs=max_logs)
    logger.info(f"Global LogAggregator initialized (max_logs={max_logs})")
    return _log_aggregator
