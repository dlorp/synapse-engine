"""Performance timing utilities for tracking execution time."""

import time
from typing import Optional
from contextlib import contextmanager
from app.core.logging import get_logger

logger = get_logger(__name__)


class Timer:
    """Context manager for measuring execution time.

    Can be used as a context manager or manually started/stopped.

    Example:
        with Timer("operation_name") as t:
            perform_operation()
        print(f"Operation took {t.elapsed_ms}ms")

        # Or manual usage:
        timer = Timer("operation")
        timer.start()
        perform_operation()
        timer.stop()
        print(f"Elapsed: {timer.elapsed_ms}ms")
    """

    def __init__(self, name: str, log_result: bool = False) -> None:
        """Initialize timer.

        Args:
            name: Name of the operation being timed
            log_result: If True, automatically log the result when timer stops
        """
        self.name = name
        self.log_result = log_result
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> 'Timer':
        """Start the timer.

        Returns:
            Self for method chaining
        """
        self.start_time = time.perf_counter()
        self.end_time = None
        return self

    def stop(self) -> float:
        """Stop the timer and return elapsed time.

        Returns:
            Elapsed time in milliseconds

        Raises:
            RuntimeError: If timer was not started
        """
        if self.start_time is None:
            raise RuntimeError(f"Timer '{self.name}' was not started")

        self.end_time = time.perf_counter()
        elapsed = self.elapsed_ms

        if self.log_result:
            logger.info(
                f"Timer: {self.name} completed",
                extra={
                    'timer_name': self.name,
                    'elapsed_ms': elapsed
                }
            )

        return elapsed

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds.

        Returns:
            Elapsed time in milliseconds

        Raises:
            RuntimeError: If timer was not started or stopped
        """
        if self.start_time is None:
            raise RuntimeError(f"Timer '{self.name}' was not started")

        end_time = self.end_time if self.end_time is not None else time.perf_counter()
        elapsed_seconds = end_time - self.start_time
        return elapsed_seconds * 1000

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds.

        Returns:
            Elapsed time in seconds
        """
        return self.elapsed_ms / 1000

    def __enter__(self) -> 'Timer':
        """Enter context manager.

        Returns:
            Self
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Exit context manager.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        self.stop()


@contextmanager
def timed_operation(name: str, log_result: bool = True):  # type: ignore
    """Context manager for timing operations with automatic logging.

    Args:
        name: Name of the operation
        log_result: Whether to log the result

    Yields:
        Timer instance

    Example:
        with timed_operation("database_query"):
            result = db.query()
    """
    timer = Timer(name, log_result=log_result)
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()
