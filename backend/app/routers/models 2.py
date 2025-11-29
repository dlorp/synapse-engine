"""Model management endpoints for status and configuration."""

from fastapi import APIRouter

from app.core.dependencies import LoggerDependency, ModelManagerDependency
from app.models.model import SystemStatus

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/status", response_model=SystemStatus, response_model_by_alias=True)
async def get_models_status(
    model_manager: ModelManagerDependency,
    logger: LoggerDependency
) -> SystemStatus:
    """Get status of all models with system metrics.

    Retrieves real-time status from all configured model instances,
    including health state, performance metrics, and aggregate statistics.

    Args:
        model_manager: ModelManager instance (injected)
        logger: Logger instance (injected)

    Returns:
        System status with all model statuses and aggregate metrics
    """
    logger.debug("Models status requested")

    # Get real status from ModelManager
    system_status = await model_manager.get_status()

    logger.info(
        "Models status retrieved",
        extra={
            'model_count': len(system_status.models),
            'active_queries': system_status.active_queries,
            'total_requests': system_status.total_requests,
            'healthy_models': sum(
                1 for m in system_status.models
                if m.state.value in ['active', 'idle']
            )
        }
    )

    return system_status
