"""Pipeline status data models for query processing visualization.

This module defines Pydantic models for tracking and querying the status of
query processing pipelines. These models power the Processing Pipeline
Visualization feature in the frontend, showing real-time progress through
query processing stages.

Author: Backend Architect
Feature: Processing Pipeline Visualization
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PipelineStage(BaseModel):
    """Status of a single pipeline stage.

    Represents the state of one stage in the query processing pipeline,
    including timing information and stage-specific metadata.

    Attributes:
        stage_name: Name of the stage (input, complexity, cgrag, etc.)
        status: Current status (pending, active, completed, failed)
        start_time: When stage started (None if not started)
        end_time: When stage ended (None if not completed)
        duration_ms: Stage duration in milliseconds (None if not completed)
        metadata: Stage-specific data (complexity score, artifacts count, etc.)

    Example:
        >>> stage = PipelineStage(
        ...     stage_name="complexity",
        ...     status="completed",
        ...     start_time=datetime.now(),
        ...     end_time=datetime.now(),
        ...     duration_ms=40,
        ...     metadata={"complexity_score": 6.5, "tier": "Q3"}
        ... )
    """

    stage_name: Literal["input", "complexity", "cgrag", "routing", "generation", "response"] = (
        Field(..., description="Pipeline stage identifier")
    )
    status: Literal["pending", "active", "completed", "failed"] = Field(
        ..., description="Current stage status"
    )
    start_time: Optional[datetime] = Field(None, description="Stage start timestamp")
    end_time: Optional[datetime] = Field(None, description="Stage completion timestamp")
    duration_ms: Optional[int] = Field(None, description="Stage duration in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Stage-specific metadata")


class PipelineStatus(BaseModel):
    """Complete status of a query processing pipeline.

    Aggregates the status of all stages in a query processing pipeline,
    providing a complete view of query progress for frontend visualization.

    Attributes:
        query_id: Unique identifier for the query
        current_stage: Name of the currently active stage
        stages: List of all pipeline stages with their status
        overall_status: Overall pipeline status (processing, completed, failed)
        total_duration_ms: Total pipeline duration (None if not completed)
        model_selected: Model ID used for generation (None if not selected yet)
        tier: Model tier selected (Q2/Q3/Q4, None if not selected yet)
        cgrag_artifacts_count: Number of CGRAG artifacts retrieved (None if not retrieved)

    Example:
        >>> pipeline_status = PipelineStatus(
        ...     query_id="550e8400-e29b-41d4-a716-446655440000",
        ...     current_stage="generation",
        ...     overall_status="processing",
        ...     stages=[stage1, stage2, ...],
        ...     model_selected="deepseek-r1:8b",
        ...     tier="Q3",
        ...     cgrag_artifacts_count=8
        ... )
    """

    query_id: str = Field(..., description="Unique query identifier")
    current_stage: str = Field(..., description="Currently active pipeline stage")
    stages: List[PipelineStage] = Field(..., description="Status of all pipeline stages")
    overall_status: Literal["processing", "completed", "failed"] = Field(
        ..., description="Overall pipeline status"
    )
    total_duration_ms: Optional[int] = Field(
        None, description="Total pipeline duration in milliseconds"
    )
    model_selected: Optional[str] = Field(None, description="Model ID used for generation")
    tier: Optional[str] = Field(None, description="Model tier selected (Q2/Q3/Q4)")
    cgrag_artifacts_count: Optional[int] = Field(
        None, description="Number of CGRAG artifacts retrieved"
    )
