"""Orchestrator status models.

This module defines Pydantic models for orchestrator telemetry data,
including routing decisions, complexity distribution, and tier utilization.
"""

from typing import Literal

from pydantic import BaseModel, Field


# Type aliases for better type safety
ComplexityLevel = Literal["SIMPLE", "MODERATE", "COMPLEX"]
ModelTierLabel = Literal["Q2", "Q3", "Q4"]


class RoutingDecision(BaseModel):
    """Individual routing decision record.

    Represents a single query routing event with metadata.

    Attributes:
        id: Unique identifier for this decision
        query: Query text (truncated to 100 chars)
        tier: Model tier selected (Q2/Q3/Q4)
        complexity: Complexity classification
        timestamp: ISO timestamp when decision was made
        score: Numerical complexity score (0-10 range)
    """

    id: str = Field(..., description="Unique decision ID")
    query: str = Field(..., max_length=100, description="Query text (truncated)")
    tier: ModelTierLabel = Field(..., description="Selected model tier")
    complexity: ComplexityLevel = Field(..., description="Complexity classification")
    timestamp: str = Field(..., description="ISO timestamp of decision")
    score: float = Field(..., ge=0.0, le=15.0, description="Complexity score")


class TierUtilization(BaseModel):
    """Model tier utilization metrics.

    Tracks usage statistics for a single model tier.

    Attributes:
        tier: Model tier label (Q2/Q3/Q4)
        utilization_percent: Percentage utilization (0-100)
        active_requests: Current number of active requests
        total_processed: Total queries processed by this tier
    """

    tier: ModelTierLabel = Field(..., description="Model tier label")
    utilization_percent: int = Field(
        ...,
        ge=0,
        le=100,
        description="Utilization percentage",
        serialization_alias="utilizationPercent",
    )
    active_requests: int = Field(
        ...,
        ge=0,
        description="Active requests count",
        serialization_alias="activeRequests",
    )
    total_processed: int = Field(
        ...,
        ge=0,
        description="Total processed queries",
        serialization_alias="totalProcessed",
    )

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True  # Allow both snake_case and camelCase


class ComplexityDistribution(BaseModel):
    """Query complexity distribution statistics.

    Percentages should sum to 100% (or close to it).

    Attributes:
        simple: Percentage of simple queries (0-100)
        moderate: Percentage of moderate complexity queries (0-100)
        complex: Percentage of complex queries (0-100)
    """

    simple: int = Field(..., ge=0, le=100, description="Simple query percentage")
    moderate: int = Field(..., ge=0, le=100, description="Moderate query percentage")
    complex: int = Field(..., ge=0, le=100, description="Complex query percentage")


class OrchestratorStatusResponse(BaseModel):
    """Complete orchestrator status response.

    Aggregates all orchestrator telemetry data for real-time visualization.

    Attributes:
        tier_utilization: List of tier utilization metrics (Q2, Q3, Q4)
        recent_decisions: List of recent routing decisions (up to 10)
        complexity_distribution: Distribution of query complexities
        total_decisions: Total number of decisions made since startup
        avg_decision_time_ms: Average decision time in milliseconds
        timestamp: ISO timestamp of this status snapshot
    """

    tier_utilization: list[TierUtilization] = Field(
        ...,
        description="Tier utilization metrics",
        serialization_alias="tierUtilization",
    )
    recent_decisions: list[RoutingDecision] = Field(
        ...,
        max_length=10,
        description="Recent routing decisions",
        serialization_alias="recentDecisions",
    )
    complexity_distribution: ComplexityDistribution = Field(
        ...,
        description="Complexity distribution",
        serialization_alias="complexityDistribution",
    )
    total_decisions: int = Field(
        ...,
        ge=0,
        description="Total decisions made",
        serialization_alias="totalDecisions",
    )
    avg_decision_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Average decision time in ms",
        serialization_alias="avgDecisionTimeMs",
    )
    timestamp: str = Field(..., description="ISO timestamp of snapshot")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True  # Allow both snake_case and camelCase
        json_schema_extra = {
            "example": {
                "tierUtilization": [
                    {
                        "tier": "Q2",
                        "utilizationPercent": 75,
                        "activeRequests": 2,
                        "totalProcessed": 1250,
                    },
                    {
                        "tier": "Q3",
                        "utilizationPercent": 50,
                        "activeRequests": 1,
                        "totalProcessed": 680,
                    },
                    {
                        "tier": "Q4",
                        "utilizationPercent": 25,
                        "activeRequests": 0,
                        "totalProcessed": 320,
                    },
                ],
                "recentDecisions": [
                    {
                        "id": "dec-1234",
                        "query": "What is the current time?",
                        "tier": "Q2",
                        "complexity": "SIMPLE",
                        "timestamp": "2025-11-08T10:30:00Z",
                        "score": 1.2,
                    }
                ],
                "complexityDistribution": {"simple": 45, "moderate": 35, "complex": 20},
                "totalDecisions": 2250,
                "avgDecisionTimeMs": 12.5,
                "timestamp": "2025-11-08T10:35:00Z",
            }
        }
