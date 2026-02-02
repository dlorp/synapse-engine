"""Custom Logging Handler for Log Aggregation.

This module provides a custom logging.Handler that intercepts all Python logging
events and feeds them to the LogAggregator service. It integrates with the
existing structured logging infrastructure and preserves all metadata.

The handler extracts structured information from log records including:
- Log level and message
- Logger name (source)
- Request ID, trace ID, session ID from context
- Service tags (prx:, mem:, rec:, etc.)
- File location (pathname, lineno, funcName)

Author: Backend Architect
Task: Comprehensive Log Aggregation and Streaming System
"""

import asyncio
import logging
from typing import Optional

from app.core.logging import get_request_id, get_trace_id, get_session_id


class AggregatorHandler(logging.Handler):
    """Custom logging handler that sends logs to LogAggregator.

    Intercepts all log records emitted by Python's logging system and
    asynchronously forwards them to the LogAggregator service. Preserves
    all structured logging metadata including request IDs, trace IDs, and
    service tags.

    The handler is non-blocking and uses asyncio to prevent logging from
    impacting application performance. If the event loop is not available
    or the aggregator is not initialized, logs are silently dropped (fail-safe).

    Architecture:
        Python Logger -> AggregatorHandler -> LogAggregator -> Circular Buffer
                                                            -> EventBus

    Example Usage:
        # In main.py startup
        aggregator_handler = AggregatorHandler(log_aggregator)
        aggregator_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(aggregator_handler)

    Attributes:
        aggregator: LogAggregator instance to send logs to
        loop: AsyncIO event loop (detected automatically)
    """

    def __init__(self, aggregator):
        """Initialize aggregator handler.

        Args:
            aggregator: LogAggregator instance to send logs to
        """
        super().__init__()
        self.aggregator = aggregator
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    # Loggers to exclude from aggregation to prevent infinite loops
    # event_bus logs "Event published" which would create recursive loop
    EXCLUDED_LOGGERS = frozenset(
        [
            "app.services.event_bus",
            "app.services.log_aggregator",
        ]
    )

    def emit(self, record: logging.LogRecord) -> None:
        """Handle log record by sending to LogAggregator asynchronously.

        This method is called by Python's logging system for every log event.
        It extracts structured metadata and creates an async task to add the
        log to the aggregator without blocking the logging call.

        Thread Safety:
            This method can be called from any thread. It safely detects the
            event loop and creates tasks in the appropriate context.

        Args:
            record: LogRecord instance from Python's logging system
        """
        # Skip excluded loggers to prevent infinite recursion
        # (event_bus logs "Event published" which would loop back)
        if record.name in self.EXCLUDED_LOGGERS:
            return

        # Get or detect event loop
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                # No event loop available - can't process async logs
                # This can happen during startup before asyncio is initialized
                return

        # Extract metadata from log record
        level = record.levelname
        source = record.name
        message = record.getMessage()

        # Extract structured metadata
        extra = {
            "pathname": record.pathname,
            "lineno": record.lineno,
            "funcName": record.funcName,
            "module": record.module,
        }

        # Extract request ID from context or record
        request_id = None
        if hasattr(record, "request_id") and record.request_id != "N/A":
            request_id = record.request_id
        else:
            request_id = get_request_id()

        # Extract trace ID from context or record
        trace_id = None
        if hasattr(record, "trace_id"):
            trace_id = record.trace_id
        else:
            trace_id = get_trace_id()

        # Extract session ID from context or record
        session_id = get_session_id()
        if session_id:
            extra["session_id"] = session_id

        # Extract service tag from record if present
        service_tag = None
        if hasattr(record, "service_tag"):
            service_tag = record.service_tag

        # Add exception info if present
        if record.exc_info:
            extra["exc_info"] = (
                self.formatter.formatException(record.exc_info)
                if self.formatter
                else str(record.exc_info)
            )

        # Create async task to add log (non-blocking)
        try:
            asyncio.create_task(
                self.aggregator.add_log(
                    level=level,
                    source=source,
                    message=message,
                    extra=extra,
                    request_id=request_id,
                    trace_id=trace_id,
                    service_tag=service_tag,
                )
            )
        except RuntimeError:
            # Event loop is closed or not available
            # This can happen during shutdown - just drop the log
            pass
        except Exception:
            # Don't let handler errors crash the application
            # Silently drop the log (fail-safe behavior)
            pass


class BufferedAggregatorHandler(logging.Handler):
    """Buffered version of AggregatorHandler for high-throughput scenarios.

    This handler buffers log records and flushes them in batches to reduce
    overhead. Useful when logging hundreds of records per second. Automatically
    flushes when buffer is full or on application shutdown.

    Note: Standard AggregatorHandler is sufficient for most use cases. Only
    use this if you're seeing performance issues from high log volume.

    Attributes:
        aggregator: LogAggregator instance
        buffer_size: Maximum records to buffer before flushing
        buffer: List of buffered log records
        loop: AsyncIO event loop
    """

    def __init__(self, aggregator, buffer_size: int = 100):
        """Initialize buffered aggregator handler.

        Args:
            aggregator: LogAggregator instance
            buffer_size: Flush buffer after this many records (default 100)
        """
        super().__init__()
        self.aggregator = aggregator
        self.buffer_size = buffer_size
        self.buffer = []
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def emit(self, record: logging.LogRecord) -> None:
        """Buffer log record and flush if buffer is full.

        Args:
            record: LogRecord from Python's logging system
        """
        self.buffer.append(record)

        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """Flush buffered log records to aggregator.

        Processes all buffered records and sends them to the aggregator
        asynchronously. Thread-safe and clears buffer after flushing.
        """
        if not self.buffer:
            return

        # Get or detect event loop
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                # No event loop - clear buffer and return
                self.buffer.clear()
                return

        # Process all buffered records
        records_to_process = self.buffer[:]
        self.buffer.clear()

        for record in records_to_process:
            # Extract metadata (same as AggregatorHandler)
            level = record.levelname
            source = record.name
            message = record.getMessage()

            extra = {
                "pathname": record.pathname,
                "lineno": record.lineno,
                "funcName": record.funcName,
                "module": record.module,
            }

            request_id = None
            if hasattr(record, "request_id") and record.request_id != "N/A":
                request_id = record.request_id
            else:
                request_id = get_request_id()

            trace_id = None
            if hasattr(record, "trace_id"):
                trace_id = record.trace_id
            else:
                trace_id = get_trace_id()

            session_id = get_session_id()
            if session_id:
                extra["session_id"] = session_id

            service_tag = None
            if hasattr(record, "service_tag"):
                service_tag = record.service_tag

            if record.exc_info:
                extra["exc_info"] = (
                    self.formatter.formatException(record.exc_info)
                    if self.formatter
                    else str(record.exc_info)
                )

            # Create async task
            try:
                asyncio.create_task(
                    self.aggregator.add_log(
                        level=level,
                        source=source,
                        message=message,
                        extra=extra,
                        request_id=request_id,
                        trace_id=trace_id,
                        service_tag=service_tag,
                    )
                )
            except (RuntimeError, Exception):
                # Silently drop on error (fail-safe)
                pass

    def close(self) -> None:
        """Close handler and flush remaining buffered records.

        Called during application shutdown to ensure no logs are lost.
        """
        self.flush()
        super().close()
