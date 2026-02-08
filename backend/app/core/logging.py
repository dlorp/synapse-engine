"""Structured logging configuration with JSON support and request tracking.

S.Y.N.A.P.S.E. CORE (PRAXIS) logging implementation with canonical service tags.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

from app.models.config import LoggingConfig

# Context variable for request ID tracking across async contexts
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Context variable for trace ID tracking
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# Context variable for session ID tracking
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)


class ServiceTag(str, Enum):
    """Canonical service logging tags per SYSTEM_IDENTITY.md"""

    PRAXIS = "prx"  # CORE:PRAXIS - Orchestrator
    MEMEX = "mem"  # CORE:MEMEX - Redis cache
    RECALL = "rec"  # NODE:RECALL - CGRAG/SearXNG
    NEURAL = "nrl"  # NODE:NEURAL - Host API
    INTERFACE = "ifc"  # CORE:INTERFACE - Frontend


class RequestIdFilter(logging.Filter):
    """Logging filter that adds request ID to log records.

    The request ID is stored in a context variable and automatically
    included in all log messages within that context.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to log record.

        Args:
            record: Log record to filter

        Returns:
            Always True (never filters out records)
        """
        record.request_id = request_id_var.get() or "N/A"
        return True


class StructuredFormatter(logging.Formatter):
    """Enhanced formatter with service tags and trace IDs per SYSTEM_IDENTITY.md"""

    def __init__(self, service_tag: ServiceTag = ServiceTag.PRAXIS):
        """Initialize structured formatter.

        Args:
            service_tag: Service tag for logging prefix
        """
        self.service_tag = service_tag
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with service tag and structured data.

        Args:
            record: Log record to format

        Returns:
            Formatted log string as JSON
        """
        tag = f"{self.service_tag.value}:"
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "tag": tag,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add trace ID if present
        if hasattr(record, "trace_id") and record.trace_id:
            log_data["trace_id"] = record.trace_id
        else:
            trace_id = trace_id_var.get()
            if trace_id:
                log_data["trace_id"] = trace_id

        # Add session ID if present
        if hasattr(record, "session_id") and record.session_id:
            log_data["session_id"] = record.session_id
        else:
            session_id = session_id_var.get()
            if session_id:
                log_data["session_id"] = session_id

        # Add request ID if present
        if hasattr(record, "request_id") and record.request_id != "N/A":
            log_data["request_id"] = record.request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields.

    Adds standard fields to all log records for consistent structured logging.
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to JSON log record.

        Args:
            log_record: Dictionary to be serialized as JSON
            record: Original log record
            message_dict: Parsed message dictionary
        """
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["request_id"] = getattr(record, "request_id", "N/A")

        # Add exception info if present
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)


def setup_logging(config: LoggingConfig, service_tag: ServiceTag = ServiceTag.PRAXIS) -> None:
    """Configure application logging based on configuration.

    Sets up handlers, formatters, and filters for structured logging with
    S.Y.N.A.P.S.E. service tags.

    Args:
        config: Logging configuration
        service_tag: Service tag for logging prefix (default: PRAXIS)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.level)

    # Add request ID filter
    request_id_filter = RequestIdFilter()
    console_handler.addFilter(request_id_filter)

    # Configure formatter based on format setting
    formatter: logging.Formatter
    if config.format == "json":
        # Use StructuredFormatter with service tags for JSON format
        formatter = StructuredFormatter(service_tag=service_tag)
    else:
        # Text format with service tag prefix
        formatter = logging.Formatter(
            fmt=f"%(asctime)s [{service_tag.value}:%(levelname)s] [%(request_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if log file is specified
    if config.log_file:
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(config.level)
        file_handler.addFilter(request_id_filter)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID for the current context.

    If no request_id is provided, generates a new UUID.

    Args:
        request_id: Optional request ID to set

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get the current request ID from context.

    Returns:
        Current request ID or None if not set
    """
    return request_id_var.get()


def clear_request_id() -> None:
    """Clear the request ID from the current context."""
    request_id_var.set(None)


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """Set trace ID for the current context.

    If no trace_id is provided, generates a new UUID.

    Args:
        trace_id: Optional trace ID to set

    Returns:
        The trace ID that was set
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())

    trace_id_var.set(trace_id)
    return trace_id


def get_trace_id() -> Optional[str]:
    """Get the current trace ID from context.

    Returns:
        Current trace ID or None if not set
    """
    return trace_id_var.get()


def clear_trace_id() -> None:
    """Clear the trace ID from the current context."""
    trace_id_var.set(None)


def set_session_id(session_id: Optional[str] = None) -> str:
    """Set session ID for the current context.

    If no session_id is provided, generates a new UUID.

    Args:
        session_id: Optional session ID to set

    Returns:
        The session ID that was set
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    session_id_var.set(session_id)
    return session_id


def get_session_id() -> Optional[str]:
    """Get the current session ID from context.

    Returns:
        Current session ID or None if not set
    """
    return session_id_var.get()


def clear_session_id() -> None:
    """Clear the session ID from the current context."""
    session_id_var.set(None)


class LoggerMixin:
    """Mixin class that provides a logger property to any class.

    The logger is automatically named after the class.
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class.

        Returns:
            Logger instance named after the class
        """
        return get_logger(self.__class__.__name__)
