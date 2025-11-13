"""Pipeline status endpoints for query processing visualization.

This module provides REST APIs for retrieving query processing pipeline status.
The pipeline status shows real-time progress through processing stages for
frontend visualization.

Author: Backend Architect
Feature: Processing Pipeline Visualization
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from app.core.logging import get_logger
from app.models.pipeline import PipelineStatus
from app.services.pipeline_state import get_pipeline_state_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/pipeline")


@router.get("/status/{query_id}", response_model=PipelineStatus)
async def get_pipeline_status(query_id: str) -> PipelineStatus:
    """Retrieve pipeline status for a specific query.

    Returns the complete status of all processing stages for a query,
    including current stage, completion status, timing information, and
    stage-specific metadata.

    This endpoint is polled by the frontend to update the Processing
    Pipeline Visualization in real-time.

    Args:
        query_id: Unique query identifier

    Returns:
        PipelineStatus with all stage information

    Raises:
        HTTPException(404): If query_id not found in pipeline tracking
        HTTPException(503): If pipeline state manager not available

    Example Response:
        {
            "query_id": "550e8400-e29b-41d4-a716-446655440000",
            "current_stage": "generation",
            "overall_status": "processing",
            "stages": [
                {
                    "stage_name": "input",
                    "status": "completed",
                    "start_time": "2025-11-12T20:30:00Z",
                    "end_time": "2025-11-12T20:30:00.010Z",
                    "duration_ms": 10,
                    "metadata": {"query_length": 45}
                },
                {
                    "stage_name": "complexity",
                    "status": "completed",
                    "start_time": "2025-11-12T20:30:00.010Z",
                    "end_time": "2025-11-12T20:30:00.050Z",
                    "duration_ms": 40,
                    "metadata": {"complexity_score": 6.5, "tier": "Q3"}
                },
                {
                    "stage_name": "generation",
                    "status": "active",
                    "start_time": "2025-11-12T20:30:00.140Z",
                    "metadata": {"tokens_generated": 120}
                }
            ],
            "model_selected": "deepseek-r1:8b",
            "tier": "Q3",
            "cgrag_artifacts_count": 8
        }
    """
    try:
        # Get pipeline state manager
        pipeline_manager = get_pipeline_state_manager()

        # Retrieve pipeline status
        pipeline_status = await pipeline_manager.get_pipeline(query_id)

        if pipeline_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline not found for query: {query_id}"
            )

        logger.debug(
            f"Retrieved pipeline status for query {query_id}",
            extra={
                "query_id": query_id,
                "current_stage": pipeline_status.current_stage,
                "overall_status": pipeline_status.overall_status
            }
        )

        return pipeline_status

    except HTTPException:
        raise
    except RuntimeError as e:
        # Pipeline manager not initialized
        logger.error(f"Pipeline state manager not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline state manager not available"
        )
    except Exception as e:
        logger.error(
            f"Error retrieving pipeline status for query {query_id}: {e}",
            exc_info=True,
            extra={"query_id": query_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pipeline status"
        )


@router.get("/stats")
async def get_pipeline_stats() -> dict:
    """Get pipeline state manager statistics.

    Returns aggregate statistics about pipeline tracking, including
    number of active, completed, and failed pipelines.

    Returns:
        Dictionary with pipeline statistics

    Raises:
        HTTPException(503): If pipeline state manager not available

    Example Response:
        {
            "total_pipelines": 42,
            "processing": 3,
            "completed": 37,
            "failed": 2
        }
    """
    try:
        # Get pipeline state manager
        pipeline_manager = get_pipeline_state_manager()

        # Get statistics
        stats = pipeline_manager.get_stats()

        logger.debug("Retrieved pipeline statistics", extra=stats)

        return stats

    except RuntimeError as e:
        # Pipeline manager not initialized
        logger.error(f"Pipeline state manager not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline state manager not available"
        )
    except Exception as e:
        logger.error(f"Error retrieving pipeline statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pipeline statistics"
        )
