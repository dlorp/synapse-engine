"""Profile data models for S.Y.N.A.P.S.E. ENGINE model configuration.

This module defines the data models for configuration profiles that control
model selection, tier routing, two-stage processing, and load balancing.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class TierConfig(BaseModel):
    """Configuration for a single tier."""

    name: str = Field(..., description="Tier name (fast/balanced/powerful)")
    max_score: float = Field(..., description="Maximum complexity score for this tier")
    expected_time_seconds: int = Field(..., description="Expected response time")
    description: Optional[str] = Field(None, description="Human-readable description")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "fast",
                "max_score": 3.0,
                "expected_time_seconds": 2,
                "description": "Quick responses for simple queries"
            }
        }
    )


class TwoStageConfig(BaseModel):
    """Two-stage processing configuration."""

    enabled: bool = Field(default=False, description="Enable two-stage processing")
    stage1_tier: str = Field(default="balanced", description="First stage tier")
    stage2_tier: str = Field(default="powerful", description="Second stage tier")
    stage1_max_tokens: int = Field(default=500, description="Max tokens for stage 1")

    model_config = ConfigDict(populate_by_name=True)


class LoadBalancingConfig(BaseModel):
    """Load balancing configuration."""

    enabled: bool = Field(default=True, description="Enable load balancing")
    strategy: str = Field(
        default="round_robin",
        description="Strategy: round_robin, least_loaded, random"
    )
    health_check_interval: int = Field(
        default=30,
        description="Seconds between health checks"
    )

    model_config = ConfigDict(populate_by_name=True)


class ModelProfile(BaseModel):
    """A named configuration profile for model selection.

    Profiles define which models to enable, how to route queries by complexity,
    whether to use two-stage processing, and load balancing strategies.
    """

    name: str = Field(..., description="Profile name")
    description: Optional[str] = Field(None, description="Profile description")

    # Which models to enable (list of model_ids from registry)
    enabled_models: List[str] = Field(
        default_factory=list,
        description="List of model_ids to enable"
    )

    # Tier configuration
    tier_config: List[TierConfig] = Field(
        default_factory=lambda: [
            TierConfig(
                name="fast",
                max_score=3.0,
                expected_time_seconds=2,
                description="Fast processing for simple queries"
            ),
            TierConfig(
                name="balanced",
                max_score=7.0,
                expected_time_seconds=5,
                description="Balanced processing for moderate complexity"
            ),
            TierConfig(
                name="powerful",
                max_score=float('inf'),
                expected_time_seconds=15,
                description="Deep processing for complex queries"
            )
        ],
        description="Tier routing configuration"
    )

    # Two-stage processing
    two_stage: TwoStageConfig = Field(
        default_factory=TwoStageConfig,
        description="Two-stage workflow configuration"
    )

    # Load balancing
    load_balancing: LoadBalancingConfig = Field(
        default_factory=LoadBalancingConfig,
        description="Load balancing configuration"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Development",
                "description": "Fast iteration with small models",
                "enabled_models": ["qwen3_4p0b_q4km_fast"],
                "tier_config": [
                    {
                        "name": "fast",
                        "max_score": 5.0,
                        "expected_time_seconds": 2
                    }
                ],
                "two_stage": {"enabled": False},
                "load_balancing": {"enabled": False, "strategy": "round_robin"}
            }
        }
    )
