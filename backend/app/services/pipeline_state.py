"""Pipeline State Manager for tracking query processing progress.

This module provides a centralized state management service for query processing
pipelines. It tracks the status of each pipeline stage, stores timing information,
and provides retrieval APIs for the frontend visualization.

The manager uses an in-memory dictionary for fast access with optional Redis
persistence for production deployments.

Author: Backend Architect
Feature: Processing Pipeline Visualization
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Optional

from app.core.logging import get_logger
from app.models.pipeline import PipelineStage, PipelineStatus

logger = get_logger(__name__)


class PipelineStateManager:
    """Manages query processing pipeline state and stage transitions.

    Tracks the progress of each query through the processing pipeline,
    storing stage status, timing data, and metadata. Provides retrieval
    APIs for frontend visualization.

    Architecture:
        - In-memory dict for fast access (sub-millisecond latency)
        - Auto-cleanup of old pipelines after 1 hour
        - Thread-safe operations with asyncio.Lock
        - Optional Redis persistence (future enhancement)

    Attributes:
        _pipelines: Dict mapping query_id to PipelineStatus
        _lock: AsyncIO lock for thread-safe operations
        _cleanup_task: Background task for auto-cleanup
    """

    def __init__(self, cleanup_interval: int = 300, ttl_seconds: int = 3600):
        """Initialize pipeline state manager.

        Args:
            cleanup_interval: How often to run cleanup task (seconds)
            ttl_seconds: How long to keep completed pipelines (seconds)
        """
        self._pipelines: Dict[str, PipelineStatus] = {}
        self._stage_start_times: Dict[str, Dict[str, float]] = {}  # query_id -> stage -> start_time
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._ttl_seconds = ttl_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            f"PipelineStateManager initialized (cleanup_interval={cleanup_interval}s, "
            f"ttl={ttl_seconds}s)"
        )

    async def start(self) -> None:
        """Start the state manager and cleanup background task."""
        if self._running:
            logger.warning("PipelineStateManager already running")
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("PipelineStateManager started")

    async def stop(self) -> None:
        """Stop the state manager and cleanup task."""
        if not self._running:
            return

        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("PipelineStateManager stopped")

    async def create_pipeline(self, query_id: str) -> None:
        """Create a new pipeline tracking entry for a query.

        Initializes all stages to "pending" status and sets the current
        stage to "input".

        Args:
            query_id: Unique query identifier
        """
        async with self._lock:
            # Initialize all stages as pending
            stages = []
            for stage_name in ["input", "complexity", "cgrag", "routing", "generation", "response"]:
                stages.append(
                    PipelineStage(
                        stage_name=stage_name,
                        status="pending"
                    )
                )

            pipeline_status = PipelineStatus(
                query_id=query_id,
                current_stage="input",
                stages=stages,
                overall_status="processing"
            )

            self._pipelines[query_id] = pipeline_status
            self._stage_start_times[query_id] = {}

            logger.debug(f"Created pipeline tracking for query {query_id}")

    async def start_stage(
        self,
        query_id: str,
        stage_name: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Mark a pipeline stage as started.

        Updates stage status to "active", records start time, and updates
        current_stage in the pipeline.

        Args:
            query_id: Unique query identifier
            stage_name: Name of the stage to start
            metadata: Optional stage-specific metadata
        """
        async with self._lock:
            if query_id not in self._pipelines:
                logger.warning(f"Pipeline not found for query {query_id}, creating it")
                await self.create_pipeline(query_id)

            pipeline = self._pipelines[query_id]

            # Find and update the stage
            for stage in pipeline.stages:
                if stage.stage_name == stage_name:
                    stage.status = "active"
                    stage.start_time = datetime.now()
                    if metadata:
                        stage.metadata.update(metadata)

                    # Record start time for duration calculation
                    self._stage_start_times[query_id][stage_name] = time.time()

                    # Update current stage
                    pipeline.current_stage = stage_name

                    logger.debug(
                        f"Stage started: {stage_name} for query {query_id}",
                        extra={"query_id": query_id, "stage": stage_name}
                    )
                    break

    async def complete_stage(
        self,
        query_id: str,
        stage_name: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Mark a pipeline stage as completed.

        Updates stage status to "completed", records end time, calculates
        duration, and updates metadata.

        Args:
            query_id: Unique query identifier
            stage_name: Name of the stage to complete
            metadata: Optional stage-specific metadata
        """
        async with self._lock:
            if query_id not in self._pipelines:
                logger.warning(f"Pipeline not found for query {query_id}")
                return

            pipeline = self._pipelines[query_id]

            # Find and update the stage
            for stage in pipeline.stages:
                if stage.stage_name == stage_name:
                    stage.status = "completed"
                    stage.end_time = datetime.now()

                    # Calculate duration
                    if query_id in self._stage_start_times and stage_name in self._stage_start_times[query_id]:
                        start_time = self._stage_start_times[query_id][stage_name]
                        stage.duration_ms = int((time.time() - start_time) * 1000)

                    if metadata:
                        stage.metadata.update(metadata)

                    logger.debug(
                        f"Stage completed: {stage_name} for query {query_id} "
                        f"(duration: {stage.duration_ms}ms)",
                        extra={
                            "query_id": query_id,
                            "stage": stage_name,
                            "duration_ms": stage.duration_ms
                        }
                    )
                    break

    async def fail_stage(
        self,
        query_id: str,
        stage_name: str,
        error_message: str
    ) -> None:
        """Mark a pipeline stage as failed.

        Updates stage status to "failed" and records error information.

        Args:
            query_id: Unique query identifier
            stage_name: Name of the stage that failed
            error_message: Error description
        """
        async with self._lock:
            if query_id not in self._pipelines:
                logger.warning(f"Pipeline not found for query {query_id}")
                return

            pipeline = self._pipelines[query_id]

            # Find and update the stage
            for stage in pipeline.stages:
                if stage.stage_name == stage_name:
                    stage.status = "failed"
                    stage.end_time = datetime.now()
                    stage.metadata["error"] = error_message

                    # Calculate duration
                    if query_id in self._stage_start_times and stage_name in self._stage_start_times[query_id]:
                        start_time = self._stage_start_times[query_id][stage_name]
                        stage.duration_ms = int((time.time() - start_time) * 1000)

                    logger.warning(
                        f"Stage failed: {stage_name} for query {query_id} - {error_message}",
                        extra={
                            "query_id": query_id,
                            "stage": stage_name,
                            "error": error_message
                        }
                    )
                    break

            # Mark overall pipeline as failed
            pipeline.overall_status = "failed"

    async def complete_pipeline(
        self,
        query_id: str,
        model_selected: Optional[str] = None,
        tier: Optional[str] = None,
        cgrag_artifacts_count: Optional[int] = None
    ) -> None:
        """Mark entire pipeline as completed.

        Updates overall_status to "completed", calculates total duration,
        and stores summary metadata.

        Args:
            query_id: Unique query identifier
            model_selected: Model ID used for generation
            tier: Model tier selected (Q2/Q3/Q4)
            cgrag_artifacts_count: Number of CGRAG artifacts retrieved
        """
        async with self._lock:
            if query_id not in self._pipelines:
                logger.warning(f"Pipeline not found for query {query_id}")
                return

            pipeline = self._pipelines[query_id]
            pipeline.overall_status = "completed"

            # Calculate total duration (sum of all stage durations)
            total_duration = 0
            for stage in pipeline.stages:
                if stage.duration_ms:
                    total_duration += stage.duration_ms

            pipeline.total_duration_ms = total_duration
            pipeline.model_selected = model_selected
            pipeline.tier = tier
            pipeline.cgrag_artifacts_count = cgrag_artifacts_count

            logger.info(
                f"Pipeline completed for query {query_id} (total: {total_duration}ms)",
                extra={
                    "query_id": query_id,
                    "total_duration_ms": total_duration,
                    "model": model_selected,
                    "tier": tier
                }
            )

    async def fail_pipeline(
        self,
        query_id: str,
        error_message: str
    ) -> None:
        """Mark entire pipeline as failed.

        Updates overall_status to "failed" and records error information.

        Args:
            query_id: Unique query identifier
            error_message: Error description
        """
        async with self._lock:
            if query_id not in self._pipelines:
                logger.warning(f"Pipeline not found for query {query_id}")
                return

            pipeline = self._pipelines[query_id]
            pipeline.overall_status = "failed"

            logger.error(
                f"Pipeline failed for query {query_id}: {error_message}",
                extra={"query_id": query_id, "error": error_message}
            )

    async def get_pipeline(self, query_id: str) -> Optional[PipelineStatus]:
        """Retrieve pipeline status for a query.

        Args:
            query_id: Unique query identifier

        Returns:
            PipelineStatus if found, None otherwise
        """
        async with self._lock:
            return self._pipelines.get(query_id)

    async def _cleanup_loop(self) -> None:
        """Background task that periodically cleans up old pipelines.

        Removes completed/failed pipelines older than TTL to prevent
        memory growth.
        """
        logger.info("Pipeline cleanup loop started")

        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)

                async with self._lock:
                    current_time = time.time()
                    to_remove = []

                    for query_id, pipeline in self._pipelines.items():
                        # Only clean up completed/failed pipelines
                        if pipeline.overall_status in ["completed", "failed"]:
                            # Check if any stage has a timestamp
                            latest_time = None
                            for stage in pipeline.stages:
                                if stage.end_time:
                                    stage_timestamp = stage.end_time.timestamp()
                                    if latest_time is None or stage_timestamp > latest_time:
                                        latest_time = stage_timestamp

                            # Remove if older than TTL
                            if latest_time and (current_time - latest_time > self._ttl_seconds):
                                to_remove.append(query_id)

                    # Remove old pipelines
                    for query_id in to_remove:
                        del self._pipelines[query_id]
                        if query_id in self._stage_start_times:
                            del self._stage_start_times[query_id]

                    if to_remove:
                        logger.info(
                            f"Cleaned up {len(to_remove)} old pipelines",
                            extra={"removed_count": len(to_remove)}
                        )

            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Prevent tight error loop

        logger.info("Pipeline cleanup loop stopped")

    def get_stats(self) -> Dict:
        """Get pipeline state manager statistics.

        Returns:
            Dictionary with statistics (active pipelines, completed, failed)
        """
        processing = sum(1 for p in self._pipelines.values() if p.overall_status == "processing")
        completed = sum(1 for p in self._pipelines.values() if p.overall_status == "completed")
        failed = sum(1 for p in self._pipelines.values() if p.overall_status == "failed")

        return {
            "total_pipelines": len(self._pipelines),
            "processing": processing,
            "completed": completed,
            "failed": failed
        }


# Global instance (initialized in main.py lifespan)
_pipeline_state_manager: Optional[PipelineStateManager] = None


def get_pipeline_state_manager() -> PipelineStateManager:
    """Get the global pipeline state manager instance.

    Returns:
        Global PipelineStateManager instance

    Raises:
        RuntimeError: If manager not initialized
    """
    if _pipeline_state_manager is None:
        raise RuntimeError(
            "PipelineStateManager not initialized - call init_pipeline_state_manager() first"
        )
    return _pipeline_state_manager


def init_pipeline_state_manager(
    cleanup_interval: int = 300,
    ttl_seconds: int = 3600
) -> PipelineStateManager:
    """Initialize the global pipeline state manager instance.

    Should be called during application startup (in lifespan context).

    Args:
        cleanup_interval: How often to run cleanup task (seconds)
        ttl_seconds: How long to keep completed pipelines (seconds)

    Returns:
        Initialized PipelineStateManager instance
    """
    global _pipeline_state_manager
    _pipeline_state_manager = PipelineStateManager(
        cleanup_interval=cleanup_interval,
        ttl_seconds=ttl_seconds
    )
    return _pipeline_state_manager
