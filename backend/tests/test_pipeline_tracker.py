"""Tests for the pipeline tracking service.

Tests the PipelineTracker helper class for instrumenting query processing
with automatic state management and event emission.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.models.events import EventType
from app.services.pipeline_tracker import PipelineTracker

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_pipeline_manager():
    """Create a mock pipeline state manager."""
    manager = AsyncMock()
    manager.create_pipeline = AsyncMock()
    manager.start_stage = AsyncMock()
    manager.complete_stage = AsyncMock()
    manager.fail_stage = AsyncMock()
    manager.complete_pipeline = AsyncMock()
    manager.fail_pipeline = AsyncMock()
    return manager


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    bus = AsyncMock()
    bus.emit_pipeline_event = AsyncMock()
    return bus


@pytest.fixture
def tracker():
    """Create a pipeline tracker instance."""
    return PipelineTracker(query_id="test-query-123")


# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Tests for PipelineTracker initialization."""

    def test_stores_query_id(self, tracker):
        """Tracker should store the query ID."""
        assert tracker.query_id == "test-query-123"

    def test_managers_initially_none(self, tracker):
        """Managers should be None until lazy initialization."""
        assert tracker._pipeline_manager is None
        assert tracker._event_bus is None

    def test_creates_with_custom_query_id(self):
        """Tracker should accept custom query ID."""
        tracker = PipelineTracker(query_id="custom-id-456")
        assert tracker.query_id == "custom-id-456"


# ============================================================================
# Manager Lazy Loading Tests
# ============================================================================


class TestManagerLazyLoading:
    """Tests for lazy loading of managers."""

    def test_get_managers_loads_dependencies(self, tracker, mock_pipeline_manager, mock_event_bus):
        """_get_managers should load pipeline manager and event bus."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            tracker._get_managers()

            assert tracker._pipeline_manager is mock_pipeline_manager
            assert tracker._event_bus is mock_event_bus

    def test_get_managers_handles_missing_dependencies(self, tracker):
        """_get_managers should handle missing dependencies gracefully."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                side_effect=RuntimeError("Not initialized"),
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                side_effect=RuntimeError("Not initialized"),
            ),
        ):
            # Should not raise
            tracker._get_managers()

            # Managers should remain None
            assert tracker._pipeline_manager is None
            assert tracker._event_bus is None


# ============================================================================
# Create Pipeline Tests
# ============================================================================


class TestCreatePipeline:
    """Tests for create_pipeline method."""

    @pytest.mark.asyncio
    async def test_calls_pipeline_manager_create(
        self, tracker, mock_pipeline_manager, mock_event_bus
    ):
        """create_pipeline should call pipeline manager's create_pipeline."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            await tracker.create_pipeline()

            mock_pipeline_manager.create_pipeline.assert_called_once_with("test-query-123")

    @pytest.mark.asyncio
    async def test_handles_missing_manager(self, tracker):
        """create_pipeline should handle missing manager gracefully."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                side_effect=RuntimeError("Not initialized"),
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                side_effect=RuntimeError("Not initialized"),
            ),
        ):
            # Should not raise
            await tracker.create_pipeline()


# ============================================================================
# Stage Context Manager Tests
# ============================================================================


class TestStageContextManager:
    """Tests for the stage() async context manager."""

    @pytest.mark.asyncio
    async def test_starts_stage_on_entry(self, tracker, mock_pipeline_manager, mock_event_bus):
        """Stage context manager should start stage on entry."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            async with tracker.stage("complexity"):
                pass

            mock_pipeline_manager.start_stage.assert_called_once_with(
                "test-query-123", "complexity"
            )

    @pytest.mark.asyncio
    async def test_emits_start_event(self, tracker, mock_pipeline_manager, mock_event_bus):
        """Stage context manager should emit start event."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            async with tracker.stage("cgrag"):
                pass

            # First call should be the start event
            start_call = mock_event_bus.emit_pipeline_event.call_args_list[0]
            assert start_call.kwargs["query_id"] == "test-query-123"
            assert start_call.kwargs["stage"] == "cgrag"
            assert start_call.kwargs["event_type"] == EventType.PIPELINE_STAGE_START

    @pytest.mark.asyncio
    async def test_completes_stage_on_success(self, tracker, mock_pipeline_manager, mock_event_bus):
        """Stage context manager should complete stage on success."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            async with tracker.stage("routing"):
                pass

            mock_pipeline_manager.complete_stage.assert_called_once()
            call_args = mock_pipeline_manager.complete_stage.call_args
            assert call_args.args[0] == "test-query-123"
            assert call_args.args[1] == "routing"

    @pytest.mark.asyncio
    async def test_emits_complete_event_on_success(
        self, tracker, mock_pipeline_manager, mock_event_bus
    ):
        """Stage context manager should emit complete event on success."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            async with tracker.stage("generation"):
                pass

            # Second call should be the complete event
            complete_call = mock_event_bus.emit_pipeline_event.call_args_list[1]
            assert complete_call.kwargs["event_type"] == EventType.PIPELINE_STAGE_COMPLETE

    @pytest.mark.asyncio
    async def test_collects_metadata(self, tracker, mock_pipeline_manager, mock_event_bus):
        """Stage context manager should collect metadata from yielded dict."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            async with tracker.stage("cgrag") as metadata:
                metadata["artifacts_retrieved"] = 5
                metadata["tokens_used"] = 1500

            # Verify metadata was passed to complete_stage
            call_args = mock_pipeline_manager.complete_stage.call_args
            assert "artifacts_retrieved" in call_args.kwargs["metadata"]
            assert call_args.kwargs["metadata"]["artifacts_retrieved"] == 5

    @pytest.mark.asyncio
    async def test_includes_duration_in_metadata(
        self, tracker, mock_pipeline_manager, mock_event_bus
    ):
        """Stage context manager should include duration in metadata."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            async with tracker.stage("complexity"):
                await asyncio.sleep(0.1)  # Small delay to ensure duration > 0

            call_args = mock_pipeline_manager.complete_stage.call_args
            assert "duration_ms" in call_args.kwargs["metadata"]
            assert call_args.kwargs["metadata"]["duration_ms"] >= 100

    @pytest.mark.asyncio
    async def test_fails_stage_on_exception(self, tracker, mock_pipeline_manager, mock_event_bus):
        """Stage context manager should fail stage on exception."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            with pytest.raises(ValueError):
                async with tracker.stage("routing"):
                    raise ValueError("Test error")

            mock_pipeline_manager.fail_stage.assert_called_once_with(
                "test-query-123", "routing", error_message="Test error"
            )

    @pytest.mark.asyncio
    async def test_emits_fail_event_on_exception(
        self, tracker, mock_pipeline_manager, mock_event_bus
    ):
        """Stage context manager should emit fail event on exception."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            with pytest.raises(RuntimeError):
                async with tracker.stage("generation"):
                    raise RuntimeError("Generation failed")

            # Second call should be the fail event
            fail_call = mock_event_bus.emit_pipeline_event.call_args_list[1]
            assert fail_call.kwargs["event_type"] == EventType.PIPELINE_STAGE_FAILED
            assert "error" in fail_call.kwargs["metadata"]

    @pytest.mark.asyncio
    async def test_reraises_exception(self, tracker, mock_pipeline_manager, mock_event_bus):
        """Stage context manager should re-raise exceptions."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            with pytest.raises(ValueError) as exc_info:
                async with tracker.stage("test"):
                    raise ValueError("Original error")

            assert str(exc_info.value) == "Original error"

    @pytest.mark.asyncio
    async def test_handles_missing_managers_gracefully(self, tracker):
        """Stage should work even without managers (no-op mode)."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                side_effect=RuntimeError("Not initialized"),
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                side_effect=RuntimeError("Not initialized"),
            ),
        ):
            # Should not raise
            async with tracker.stage("test") as metadata:
                metadata["test_key"] = "test_value"


# ============================================================================
# Complete Pipeline Tests
# ============================================================================


class TestCompletePipeline:
    """Tests for complete_pipeline method."""

    @pytest.mark.asyncio
    async def test_calls_pipeline_manager_complete(
        self, tracker, mock_pipeline_manager, mock_event_bus
    ):
        """complete_pipeline should call pipeline manager's complete_pipeline."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            await tracker.complete_pipeline(
                model_selected="deepseek_8b",
                tier="balanced",
                cgrag_artifacts_count=5,
            )

            mock_pipeline_manager.complete_pipeline.assert_called_once_with(
                "test-query-123",
                model_selected="deepseek_8b",
                tier="balanced",
                cgrag_artifacts_count=5,
            )

    @pytest.mark.asyncio
    async def test_emits_complete_event(self, tracker, mock_pipeline_manager, mock_event_bus):
        """complete_pipeline should emit PIPELINE_COMPLETE event."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            await tracker.complete_pipeline(
                model_selected="test_model", tier="fast", cgrag_artifacts_count=3
            )

            mock_event_bus.emit_pipeline_event.assert_called_once()
            call_args = mock_event_bus.emit_pipeline_event.call_args
            assert call_args.kwargs["event_type"] == EventType.PIPELINE_COMPLETE
            assert call_args.kwargs["metadata"]["model_selected"] == "test_model"
            assert call_args.kwargs["metadata"]["tier"] == "fast"

    @pytest.mark.asyncio
    async def test_handles_optional_parameters(
        self, tracker, mock_pipeline_manager, mock_event_bus
    ):
        """complete_pipeline should handle None parameters."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            await tracker.complete_pipeline()

            mock_pipeline_manager.complete_pipeline.assert_called_once_with(
                "test-query-123",
                model_selected=None,
                tier=None,
                cgrag_artifacts_count=None,
            )


# ============================================================================
# Fail Pipeline Tests
# ============================================================================


class TestFailPipeline:
    """Tests for fail_pipeline method."""

    @pytest.mark.asyncio
    async def test_calls_pipeline_manager_fail(
        self, tracker, mock_pipeline_manager, mock_event_bus
    ):
        """fail_pipeline should call pipeline manager's fail_pipeline."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            await tracker.fail_pipeline(error_message="Query failed due to timeout")

            mock_pipeline_manager.fail_pipeline.assert_called_once_with(
                "test-query-123", error_message="Query failed due to timeout"
            )

    @pytest.mark.asyncio
    async def test_emits_fail_event(self, tracker, mock_pipeline_manager, mock_event_bus):
        """fail_pipeline should emit PIPELINE_FAILED event."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            await tracker.fail_pipeline(error_message="Model unavailable")

            mock_event_bus.emit_pipeline_event.assert_called_once()
            call_args = mock_event_bus.emit_pipeline_event.call_args
            assert call_args.kwargs["event_type"] == EventType.PIPELINE_FAILED
            assert call_args.kwargs["metadata"]["error"] == "Model unavailable"

    @pytest.mark.asyncio
    async def test_handles_missing_managers(self, tracker):
        """fail_pipeline should handle missing managers gracefully."""
        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                side_effect=RuntimeError("Not initialized"),
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                side_effect=RuntimeError("Not initialized"),
            ),
        ):
            # Should not raise
            await tracker.fail_pipeline(error_message="Test error")


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for complete pipeline tracking workflow."""

    @pytest.mark.asyncio
    async def test_complete_pipeline_workflow(self, mock_pipeline_manager, mock_event_bus):
        """Test complete workflow from creation to completion."""
        tracker = PipelineTracker(query_id="integration-test-123")

        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            # Create pipeline
            await tracker.create_pipeline()

            # Process stages
            async with tracker.stage("input") as metadata:
                metadata["query_length"] = 50

            async with tracker.stage("complexity") as metadata:
                metadata["score"] = 3.5
                metadata["tier"] = "balanced"

            async with tracker.stage("cgrag") as metadata:
                metadata["artifacts_retrieved"] = 8

            async with tracker.stage("routing") as metadata:
                metadata["model_selected"] = "test_model"

            async with tracker.stage("generation") as metadata:
                metadata["tokens_generated"] = 500

            # Complete pipeline
            await tracker.complete_pipeline(
                model_selected="test_model",
                tier="balanced",
                cgrag_artifacts_count=8,
            )

            # Verify all stages were tracked
            assert mock_pipeline_manager.create_pipeline.call_count == 1
            assert mock_pipeline_manager.start_stage.call_count == 5
            assert mock_pipeline_manager.complete_stage.call_count == 5
            assert mock_pipeline_manager.complete_pipeline.call_count == 1

    @pytest.mark.asyncio
    async def test_pipeline_with_failure(self, mock_pipeline_manager, mock_event_bus):
        """Test pipeline workflow with stage failure."""
        tracker = PipelineTracker(query_id="failure-test-456")

        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            # Create pipeline
            await tracker.create_pipeline()

            # Process some stages successfully
            async with tracker.stage("input") as metadata:
                metadata["query"] = "test query"

            # Stage that fails
            try:
                async with tracker.stage("generation"):
                    raise RuntimeError("Model timeout")
            except RuntimeError:
                pass

            # Mark pipeline as failed
            await tracker.fail_pipeline(error_message="Model timeout")

            # Verify failure was tracked
            assert mock_pipeline_manager.fail_stage.call_count == 1
            assert mock_pipeline_manager.fail_pipeline.call_count == 1

    @pytest.mark.asyncio
    async def test_multiple_trackers_independent(self, mock_pipeline_manager, mock_event_bus):
        """Multiple trackers should track independently."""
        tracker1 = PipelineTracker(query_id="query-1")
        tracker2 = PipelineTracker(query_id="query-2")

        with (
            patch(
                "app.services.pipeline_tracker.get_pipeline_state_manager",
                return_value=mock_pipeline_manager,
            ),
            patch(
                "app.services.pipeline_tracker.get_event_bus",
                return_value=mock_event_bus,
            ),
        ):
            await tracker1.create_pipeline()
            await tracker2.create_pipeline()

            # Both should create separate pipelines
            assert mock_pipeline_manager.create_pipeline.call_count == 2

            calls = mock_pipeline_manager.create_pipeline.call_args_list
            query_ids = [call.args[0] for call in calls]
            assert "query-1" in query_ids
            assert "query-2" in query_ids
