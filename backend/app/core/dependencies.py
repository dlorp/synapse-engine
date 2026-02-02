"""FastAPI dependency injection providers.

These functions provide shared resources to endpoint handlers
through FastAPI's dependency injection system.
"""

import logging
from typing import Annotated, TYPE_CHECKING

from fastapi import Depends, Request

from app.core.config import get_config
from app.models.config import AppConfig

if TYPE_CHECKING:
    from app.services.models import ModelManager


def get_app_config() -> AppConfig:
    """Get application configuration.

    Returns:
        Current application configuration

    Example:
        @app.get("/endpoint")
        async def endpoint(config: AppConfig = Depends(get_app_config)):
            return {"app_name": config.app_name}
    """
    return get_config()


def get_request_logger(
    config: Annotated[AppConfig, Depends(get_app_config)],
) -> logging.Logger:
    """Get logger for request handlers.

    Args:
        config: Application configuration (injected)

    Returns:
        Logger instance

    Example:
        @app.get("/endpoint")
        async def endpoint(logger: logging.Logger = Depends(get_request_logger)):
            logger.info("Processing request")
            return {"status": "ok"}
    """
    return logging.getLogger("api")


def get_model_manager(request: Request) -> "ModelManager":
    """Get ModelManager instance from application state.

    Args:
        request: FastAPI request object

    Returns:
        ModelManager instance

    Example:
        @app.get("/endpoint")
        async def endpoint(
            model_manager: ModelManager = Depends(get_model_manager)
        ):
            status = await model_manager.get_status()
            return status
    """
    return request.app.state.model_manager


# Type aliases for dependency injection
ConfigDependency = Annotated[AppConfig, Depends(get_app_config)]
LoggerDependency = Annotated[logging.Logger, Depends(get_request_logger)]
ModelManagerDependency = Annotated["ModelManager", Depends(get_model_manager)]
