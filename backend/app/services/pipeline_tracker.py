"""Pipeline tracking helper for instrumenting query processing.

This module provides a context manager for tracking query processing pipeline
stages with automatic state management and event emission.

Author: Backend Architect
Feature: Processing Pipeline Visualization
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Optional

from app.core.logging import get_logger
from app.models.events import EventType
from app.services.event_bus import get_event_bus
from app.services.pipeline_state import get_pipeline_state_manager

logger = get_logger(__name__)


class PipelineTracker:
    """Helper class for tracking pipeline stages during query processing.

    Provides convenience methods for updating pipeline state and emitting
    events without cluttering query processing code.

    Example:
        tracker = PipelineTracker(query_id="abc123")
        async with tracker.stage("complexity") as metadata:
            # Do complexity assessment
            complexity_score = assess_complexity(query)
            metadata["complexity_score"] = complexity_score
            metadata["tier"] = "Q3"
        # Stage automatically marked complete with metadata
    """

    def __init__(self, query_id: str):
        """Initialize pipeline tracker.

        Args:
            query_id: Unique query identifier
        """
        self.query_id = query_id
        self._pipeline_manager = None
        self._event_bus = None

    def _get_managers(self):
        """Get pipeline manager and event bus (lazy initialization)."""
        if self._pipeline_manager is None:
            try:
                self._pipeline_manager = get_pipeline_state_manager()
                self._event_bus = get_event_bus()
            except RuntimeError as e:
                logger.warning(f"Pipeline tracking disabled: {e}")

    async def create_pipeline(self) -> None:
        """Create pipeline tracking entry."""
        self._get_managers()
        if self._pipeline_manager:
            await self._pipeline_manager.create_pipeline(self.query_id)
            logger.debug(f"Pipeline created for query {self.query_id}")

    @asynccontextmanager
    async def stage(self, stage_name: str) -> AsyncIterator[Dict]:
        """Track a pipeline stage with automatic state management.

        Context manager that automatically starts and completes a pipeline
        stage, emitting appropriate events. Metadata can be added to the
        stage via the yielded dict.

        Args:
            stage_name: Name of the pipeline stage

        Yields:
            Metadata dict for collecting stage-specific data

        Example:
            async with tracker.stage("cgrag") as metadata:
                artifacts = await retrieve_context(query)
                metadata["artifacts_retrieved"] = len(artifacts)
                metadata["tokens_used"] = sum(a.token_count for a in artifacts)
        """
        self._get_managers()

        metadata: Dict = {}
        start_time = time.time()

        # Start stage
        if self._pipeline_manager and self._event_bus:
            await self._pipeline_manager.start_stage(self.query_id, stage_name)
            await self._event_bus.emit_pipeline_event(
                query_id=self.query_id,
                stage=stage_name,
                event_type=EventType.PIPELINE_STAGE_START,
            )

        try:
            # Yield control to caller
            yield metadata

            # Complete stage (success)
            duration_ms = int((time.time() - start_time) * 1000)
            metadata["duration_ms"] = duration_ms

            if self._pipeline_manager and self._event_bus:
                await self._pipeline_manager.complete_stage(
                    self.query_id, stage_name, metadata=metadata
                )
                await self._event_bus.emit_pipeline_event(
                    query_id=self.query_id,
                    stage=stage_name,
                    event_type=EventType.PIPELINE_STAGE_COMPLETE,
                    metadata=metadata,
                )

        except Exception as e:
            # Fail stage (error)
            error_message = str(e)

            if self._pipeline_manager and self._event_bus:
                await self._pipeline_manager.fail_stage(
                    self.query_id, stage_name, error_message=error_message
                )
                await self._event_bus.emit_pipeline_event(
                    query_id=self.query_id,
                    stage=stage_name,
                    event_type=EventType.PIPELINE_STAGE_FAILED,
                    metadata={"error": error_message},
                )

            # Re-raise exception
            raise

    async def complete_pipeline(
        self,
        model_selected: Optional[str] = None,
        tier: Optional[str] = None,
        cgrag_artifacts_count: Optional[int] = None,
    ) -> None:
        """Mark pipeline as completed successfully.

        Args:
            model_selected: Model ID used for generation
            tier: Model tier selected (Q2/Q3/Q4)
            cgrag_artifacts_count: Number of CGRAG artifacts retrieved
        """
        self._get_managers()

        if self._pipeline_manager and self._event_bus:
            await self._pipeline_manager.complete_pipeline(
                self.query_id,
                model_selected=model_selected,
                tier=tier,
                cgrag_artifacts_count=cgrag_artifacts_count,
            )
            await self._event_bus.emit_pipeline_event(
                query_id=self.query_id,
                stage="response",
                event_type=EventType.PIPELINE_COMPLETE,
                metadata={
                    "model_selected": model_selected,
                    "tier": tier,
                    "cgrag_artifacts_count": cgrag_artifacts_count,
                },
            )

    async def fail_pipeline(self, error_message: str) -> None:
        """Mark pipeline as failed.

        Args:
            error_message: Error description
        """
        self._get_managers()

        if self._pipeline_manager and self._event_bus:
            await self._pipeline_manager.fail_pipeline(self.query_id, error_message=error_message)
            await self._event_bus.emit_pipeline_event(
                query_id=self.query_id,
                stage="error",
                event_type=EventType.PIPELINE_FAILED,
                metadata={"error": error_message},
            )
