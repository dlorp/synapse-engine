"""Health check endpoints for monitoring system status."""

import time
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter

from app.core.dependencies import ConfigDependency, LoggerDependency
from app.models.model import HealthCheckResponse, ModelHealth

router = APIRouter(prefix="/health", tags=["health"])

# Track application start time for uptime calculation
_start_time = time.time()


@router.get("", response_model=HealthCheckResponse, response_model_by_alias=True)
async def health_check(
    config: ConfigDependency,
    logger: LoggerDependency
) -> HealthCheckResponse:
    """Basic health check endpoint.

    Returns:
        Health check response with status and version information
    """
    logger.debug("Health check requested")

    uptime = int(time.time() - _start_time)

    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=config.version,
        environment=config.environment,
        uptime_seconds=uptime
    )


@router.get("/models", response_model=List[ModelHealth], response_model_by_alias=True)
async def models_health_check(
    config: ConfigDependency,
    logger: LoggerDependency
) -> List[ModelHealth]:
    """Health check for all configured models.

    Returns mock data for Session 1. Will be replaced with real
    health checks in Session 2.

    Returns:
        List of model health statuses
    """
    logger.debug("Models health check requested")

    # Mock health data for all configured models
    mock_health: List[ModelHealth] = []

    # Get current timestamp
    now = datetime.now(timezone.utc)

    # Generate mock health for each configured model
    for model_id, model_config in config.models.items():
        # All models healthy with low latency for mock data
        health = ModelHealth(
            is_healthy=True,
            latency_ms=12.5,
            last_check=now,
            error_message=None,
            consecutive_failures=0
        )
        mock_health.append(health)

    logger.info(
        f"Models health check completed: {len(mock_health)} models checked",
        extra={'model_count': len(mock_health)}
    )

    return mock_health
