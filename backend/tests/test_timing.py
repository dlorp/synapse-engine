"""Unit tests for the timing utilities module.

Tests the Timer class and timed_operation context manager for
measuring execution time with proper edge case handling.
"""

import time
import pytest
from unittest.mock import patch

from app.utils.timing import Timer, timed_operation


class TestTimer:
    """Tests for the Timer class."""

    def test_basic_context_manager_usage(self):
        """Test Timer as a context manager."""
        with Timer("test_operation") as timer:
            time.sleep(0.01)  # 10ms sleep
        
        # Should have measured approximately 10ms (allow for some variance)
        assert timer.elapsed_ms >= 9  # At least 9ms
        assert timer.elapsed_ms < 50  # But not more than 50ms

    def test_timer_name_attribute(self):
        """Test that timer name is set correctly."""
        timer = Timer("my_operation")
        assert timer.name == "my_operation"

    def test_start_returns_self(self):
        """Test that start() returns self for chaining."""
        timer = Timer("test")
        result = timer.start()
        
        assert result is timer

    def test_stop_returns_elapsed_ms(self):
        """Test that stop() returns elapsed time in ms."""
        timer = Timer("test")
        timer.start()
        time.sleep(0.005)  # 5ms
        elapsed = timer.stop()
        
        assert isinstance(elapsed, float)
        assert elapsed >= 4  # At least 4ms

    def test_elapsed_ms_property_during_run(self):
        """Test elapsed_ms during running timer."""
        timer = Timer("test")
        timer.start()
        time.sleep(0.005)
        
        # Timer still running, should still get elapsed time
        elapsed = timer.elapsed_ms
        assert elapsed >= 4

    def test_elapsed_ms_property_after_stop(self):
        """Test elapsed_ms property after timer stopped."""
        timer = Timer("test")
        timer.start()
        time.sleep(0.005)
        timer.stop()
        
        # Multiple calls should return same value
        elapsed1 = timer.elapsed_ms
        time.sleep(0.005)
        elapsed2 = timer.elapsed_ms
        
        assert elapsed1 == elapsed2  # Should be same since timer stopped

    def test_elapsed_seconds_property(self):
        """Test elapsed_seconds conversion."""
        with Timer("test") as timer:
            time.sleep(0.01)
        
        # elapsed_seconds should be elapsed_ms / 1000
        assert abs(timer.elapsed_seconds - timer.elapsed_ms / 1000) < 0.001

    def test_stop_without_start_raises_error(self):
        """Test that stop() without start() raises RuntimeError."""
        timer = Timer("test")
        
        with pytest.raises(RuntimeError) as exc_info:
            timer.stop()
        
        assert "test" in str(exc_info.value)
        assert "not started" in str(exc_info.value)

    def test_elapsed_ms_without_start_raises_error(self):
        """Test that elapsed_ms without start raises RuntimeError."""
        timer = Timer("unstarted")
        
        with pytest.raises(RuntimeError) as exc_info:
            _ = timer.elapsed_ms
        
        assert "unstarted" in str(exc_info.value)

    def test_manual_start_stop_usage(self):
        """Test manual start/stop usage pattern."""
        timer = Timer("manual")
        
        timer.start()
        time.sleep(0.005)
        elapsed = timer.stop()
        
        assert elapsed >= 4
        assert timer.start_time is not None
        assert timer.end_time is not None

    def test_timer_reset_on_restart(self):
        """Test that start() resets the timer."""
        timer = Timer("reset_test")
        
        timer.start()
        time.sleep(0.005)
        timer.stop()
        first_elapsed = timer.elapsed_ms
        
        # Restart the timer
        timer.start()
        time.sleep(0.005)
        timer.stop()
        second_elapsed = timer.elapsed_ms
        
        # Both should be similar (around 5ms each)
        assert abs(first_elapsed - second_elapsed) < 10

    def test_context_manager_exception_still_stops(self):
        """Test timer stops even when exception occurs in context."""
        timer = Timer("exception_test")
        
        try:
            with timer:
                time.sleep(0.005)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Timer should still have stopped
        assert timer.end_time is not None
        assert timer.elapsed_ms >= 4

    @patch("app.utils.timing.logger")
    def test_log_result_true_logs_on_stop(self, mock_logger):
        """Test that log_result=True logs when timer stops."""
        timer = Timer("logged_op", log_result=True)
        timer.start()
        time.sleep(0.001)
        timer.stop()
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "logged_op" in call_args[0][0]

    @patch("app.utils.timing.logger")
    def test_log_result_false_no_logging(self, mock_logger):
        """Test that log_result=False doesn't log."""
        timer = Timer("silent_op", log_result=False)
        timer.start()
        timer.stop()
        
        mock_logger.info.assert_not_called()

    def test_very_short_duration(self):
        """Test measurement of very short operations."""
        with Timer("fast") as timer:
            pass  # Nearly instant
        
        # Should be measurable but very small
        assert timer.elapsed_ms >= 0
        assert timer.elapsed_ms < 10

    def test_zero_elapsed_time_possible(self):
        """Test that zero or near-zero time is valid."""
        timer = Timer("instant")
        timer.start_time = 1000.0
        timer.end_time = 1000.0
        
        assert timer.elapsed_ms == 0.0


class TestTimedOperation:
    """Tests for the timed_operation context manager function."""

    @patch("app.utils.timing.logger")
    def test_basic_usage_with_logging(self, mock_logger):
        """Test basic timed_operation usage with default logging."""
        with timed_operation("database_query") as timer:
            time.sleep(0.005)
        
        assert timer.elapsed_ms >= 4
        mock_logger.info.assert_called_once()

    @patch("app.utils.timing.logger")
    def test_logging_disabled(self, mock_logger):
        """Test timed_operation with logging disabled."""
        with timed_operation("silent_op", log_result=False) as timer:
            time.sleep(0.001)
        
        assert timer.elapsed_ms >= 0
        mock_logger.info.assert_not_called()

    def test_timer_accessible_in_context(self):
        """Test that timer is accessible within the context."""
        with timed_operation("accessible", log_result=False) as timer:
            assert isinstance(timer, Timer)
            assert timer.name == "accessible"

    @patch("app.utils.timing.logger")
    def test_exception_still_stops_timer(self, mock_logger):
        """Test that timer stops even on exception."""
        try:
            with timed_operation("error_op", log_result=False) as timer:
                time.sleep(0.005)
                raise RuntimeError("Intentional error")
        except RuntimeError:
            pass
        
        assert timer.end_time is not None
        assert timer.elapsed_ms >= 4

    @patch("app.utils.timing.logger")
    def test_exception_still_logs(self, mock_logger):
        """Test that exception doesn't prevent logging."""
        try:
            with timed_operation("logged_error"):
                raise ValueError("Error")
        except ValueError:
            pass
        
        # Should still log despite exception
        mock_logger.info.assert_called_once()

    def test_nested_timers(self):
        """Test nested timed operations."""
        with timed_operation("outer", log_result=False) as outer:
            time.sleep(0.005)
            with timed_operation("inner", log_result=False) as inner:
                time.sleep(0.005)
        
        # Inner should be ~5ms, outer should be ~10ms
        assert inner.elapsed_ms >= 4
        assert outer.elapsed_ms >= 9
        assert outer.elapsed_ms > inner.elapsed_ms


class TestTimerEdgeCases:
    """Edge case tests for Timer."""

    def test_timer_with_empty_name(self):
        """Test timer with empty string name."""
        timer = Timer("")
        timer.start()
        timer.stop()
        
        assert timer.name == ""
        assert timer.elapsed_ms >= 0

    def test_timer_with_special_characters_in_name(self):
        """Test timer with special characters in name."""
        timer = Timer("api/v1/query?param=value")
        timer.start()
        timer.stop()
        
        assert timer.name == "api/v1/query?param=value"

    def test_timer_with_unicode_name(self):
        """Test timer with unicode characters."""
        timer = Timer("操作タイマー")  # "operation timer" in mixed CJK
        timer.start()
        timer.stop()
        
        assert timer.name == "操作タイマー"

    def test_multiple_stops_use_first_end_time(self):
        """Test that multiple stop() calls use first end time."""
        timer = Timer("multi_stop")
        timer.start()
        time.sleep(0.005)
        first_elapsed = timer.stop()
        
        time.sleep(0.010)  # Wait longer
        
        # elapsed_ms should still return first measurement
        assert timer.elapsed_ms == first_elapsed

    def test_enter_exit_methods_directly(self):
        """Test __enter__ and __exit__ methods directly."""
        timer = Timer("direct")
        
        result = timer.__enter__()
        assert result is timer
        assert timer.start_time is not None
        
        time.sleep(0.001)
        timer.__exit__(None, None, None)
        assert timer.end_time is not None

    def test_exit_with_exception_info(self):
        """Test __exit__ receives exception info correctly."""
        timer = Timer("exc_test")
        timer.__enter__()
        
        # Simulate exception context
        try:
            raise ValueError("Test")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            timer.__exit__(*exc_info)
        
        # Timer should still have stopped
        assert timer.end_time is not None
