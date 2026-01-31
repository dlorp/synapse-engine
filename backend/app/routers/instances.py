"""Instance management endpoints for multi-instance model support.

This module provides REST API endpoints for:
- Instance CRUD operations (create, read, update, delete)
- Instance lifecycle management (start, stop)
- Instance status and health checks
- System prompt presets

Instances allow multiple configurations of the same base model
with different system prompts, web search settings, etc.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.exceptions import SynapseException
from app.models.instance import (
    InstanceConfig,
    InstanceListResponse,
    CreateInstanceRequest,
    UpdateInstanceRequest,
    SystemPromptPresetsResponse,
)
from app.services.instance_manager import InstanceManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/instances", tags=["instances"])

# Global instance manager (initialized in main.py lifespan)
instance_manager: Optional[InstanceManager] = None


def _get_instance_manager() -> InstanceManager:
    """Get instance manager with error handling.

    Returns:
        InstanceManager instance

    Raises:
        HTTPException: If instance manager not initialized
    """
    if instance_manager is None:
        logger.error("Instance manager not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "Instance manager not initialized",
                "details": {}
            }
        )
    return instance_manager


# =============================================================================
# List & Get Endpoints
# =============================================================================

@router.get("", response_model=InstanceListResponse)
async def list_instances() -> InstanceListResponse:
    """List all configured instances.

    Returns:
        InstanceListResponse with all instances, total count, and counts by model
    """
    mgr = _get_instance_manager()

    instances = mgr.get_all_instances()
    by_model = mgr.get_instance_counts_by_model()

    return InstanceListResponse(
        instances=instances,
        total=len(instances),
        by_model=by_model
    )


@router.get("/model/{model_id}", response_model=List[InstanceConfig])
async def list_instances_for_model(model_id: str) -> List[InstanceConfig]:
    """List all instances of a specific base model.

    Args:
        model_id: Base model identifier

    Returns:
        List of InstanceConfig for the model
    """
    mgr = _get_instance_manager()
    return mgr.get_instances_for_model(model_id)


@router.get("/presets", response_model=SystemPromptPresetsResponse)
async def get_system_prompt_presets() -> SystemPromptPresetsResponse:
    """Get available system prompt presets.

    Returns:
        SystemPromptPresetsResponse with available presets
    """
    mgr = _get_instance_manager()
    presets = mgr.get_system_prompt_presets()
    return SystemPromptPresetsResponse(presets=presets)


@router.get("/{instance_id}", response_model=InstanceConfig)
async def get_instance(instance_id: str) -> InstanceConfig:
    """Get a specific instance by ID.

    Args:
        instance_id: Instance identifier (format: model_id:NN)

    Returns:
        InstanceConfig for the instance

    Raises:
        HTTPException: If instance not found
    """
    mgr = _get_instance_manager()
    config = mgr.get_instance(instance_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Instance not found: {instance_id}",
                "details": {"instance_id": instance_id}
            }
        )

    return config


@router.get("/{instance_id}/status")
async def get_instance_status(instance_id: str) -> dict:
    """Get detailed status for an instance.

    Args:
        instance_id: Instance identifier

    Returns:
        Dictionary with status details including server process info
    """
    mgr = _get_instance_manager()
    status_info = mgr.get_instance_status(instance_id)

    if "error" in status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": status_info["error"],
                "details": {"instance_id": instance_id}
            }
        )

    return status_info


# =============================================================================
# Create, Update, Delete Endpoints
# =============================================================================

@router.post("", response_model=InstanceConfig, status_code=status.HTTP_201_CREATED)
async def create_instance(request: CreateInstanceRequest) -> InstanceConfig:
    """Create a new model instance.

    Args:
        request: CreateInstanceRequest with instance configuration

    Returns:
        Created InstanceConfig

    Raises:
        HTTPException: If creation fails (model not found, no ports available)
    """
    mgr = _get_instance_manager()

    try:
        config = mgr.create_instance(request)
        logger.info(f"Created instance {config.instance_id} for model {request.model_id}")
        return config
    except SynapseException as e:
        logger.error(f"Failed to create instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "CreateFailed",
                "message": str(e),
                "details": e.details if hasattr(e, 'details') else {}
            }
        )


@router.put("/{instance_id}", response_model=InstanceConfig)
async def update_instance(
    instance_id: str,
    request: UpdateInstanceRequest
) -> InstanceConfig:
    """Update an existing instance configuration.

    Args:
        instance_id: Instance to update
        request: UpdateInstanceRequest with new values

    Returns:
        Updated InstanceConfig

    Raises:
        HTTPException: If instance not found
    """
    mgr = _get_instance_manager()

    try:
        config = mgr.update_instance(instance_id, request)
        logger.info(f"Updated instance {instance_id}")
        return config
    except SynapseException as e:
        logger.error(f"Failed to update instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "UpdateFailed",
                "message": str(e),
                "details": e.details if hasattr(e, 'details') else {}
            }
        )


@router.delete("/{instance_id}")
async def delete_instance(instance_id: str) -> JSONResponse:
    """Delete an instance.

    Args:
        instance_id: Instance to delete

    Returns:
        Success message

    Raises:
        HTTPException: If instance not found or is currently running
    """
    mgr = _get_instance_manager()

    try:
        deleted = mgr.delete_instance(instance_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NotFound",
                    "message": f"Instance not found: {instance_id}",
                    "details": {"instance_id": instance_id}
                }
            )

        logger.info(f"Deleted instance {instance_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Instance {instance_id} deleted successfully",
                "instance_id": instance_id
            }
        )
    except SynapseException as e:
        logger.error(f"Failed to delete instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DeleteFailed",
                "message": str(e),
                "details": e.details if hasattr(e, 'details') else {}
            }
        )


# =============================================================================
# Lifecycle Endpoints (Start/Stop)
# =============================================================================

@router.post("/{instance_id}/start", response_model=InstanceConfig)
async def start_instance(instance_id: str) -> InstanceConfig:
    """Start an instance's llama-server.

    Args:
        instance_id: Instance to start

    Returns:
        Updated InstanceConfig with ACTIVE status

    Raises:
        HTTPException: If instance not found or start fails
    """
    mgr = _get_instance_manager()

    try:
        config = await mgr.start_instance(instance_id)
        logger.info(f"Started instance {instance_id} on port {config.port}")
        return config
    except SynapseException as e:
        logger.error(f"Failed to start instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "StartFailed",
                "message": str(e),
                "details": e.details if hasattr(e, 'details') else {}
            }
        )


@router.post("/{instance_id}/stop", response_model=InstanceConfig)
async def stop_instance(instance_id: str) -> InstanceConfig:
    """Stop an instance's llama-server.

    Args:
        instance_id: Instance to stop

    Returns:
        Updated InstanceConfig with STOPPED status

    Raises:
        HTTPException: If instance not found or stop fails
    """
    mgr = _get_instance_manager()

    try:
        config = await mgr.stop_instance(instance_id)
        logger.info(f"Stopped instance {instance_id}")
        return config
    except SynapseException as e:
        logger.error(f"Failed to stop instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "StopFailed",
                "message": str(e),
                "details": e.details if hasattr(e, 'details') else {}
            }
        )


# =============================================================================
# Batch Operations
# =============================================================================

@router.post("/start-all")
async def start_all_instances() -> JSONResponse:
    """Start all configured instances.

    Returns:
        Summary of start results
    """
    mgr = _get_instance_manager()
    instances = mgr.get_all_instances()

    started = []
    failed = []

    for config in instances:
        if config.status != "active":
            try:
                await mgr.start_instance(config.instance_id)
                started.append(config.instance_id)
            except Exception as e:
                failed.append({
                    "instance_id": config.instance_id,
                    "error": str(e)
                })

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Started {len(started)} instances",
            "started": started,
            "failed": failed,
            "total": len(instances)
        }
    )


@router.post("/stop-all")
async def stop_all_instances() -> JSONResponse:
    """Stop all running instances.

    Returns:
        Summary of stop results
    """
    mgr = _get_instance_manager()
    active_instances = mgr.get_active_instances()

    stopped = []
    failed = []

    for config in active_instances:
        try:
            await mgr.stop_instance(config.instance_id)
            stopped.append(config.instance_id)
        except Exception as e:
            failed.append({
                "instance_id": config.instance_id,
                "error": str(e)
            })

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Stopped {len(stopped)} instances",
            "stopped": stopped,
            "failed": failed
        }
    )
