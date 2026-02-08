"""Model management endpoints for status, configuration, and profile management.

This module provides REST API endpoints for:
- Model registry access and management
- Model configuration (tier, thinking, enabled status)
- Server status monitoring
- Profile CRUD operations
- Model rescanning and discovery
"""

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import LoggerDependency, ModelManagerDependency
from app.core.exceptions import SynapseException
from app.models.api import (
    BulkEnabledUpdateResponse,
    EnabledUpdateRequest,
    EnabledUpdateResponse,
    PortRangeUpdateRequest,
    PortRangeUpdateResponse,
    PortUpdateRequest,
    PortUpdateResponse,
    ProfileCreateRequest,
    ProfileCreateResponse,
    ProfileDeleteResponse,
    RescanResponse,
    RuntimeSettingsUpdateRequest,
    RuntimeSettingsUpdateResponse,
    ServerStatusResponse,
    ThinkingUpdateRequest,
    ThinkingUpdateResponse,
    TierUpdateRequest,
    TierUpdateResponse,
)
from app.models.discovered_model import DiscoveredModel, ModelRegistry, ModelTier
from app.models.model_metrics import ModelMetrics
from app.models.profile import ModelProfile
from app.services.llama_server_manager import LlamaServerManager
from app.services.model_discovery import ModelDiscoveryService
from app.services.profile_manager import ProfileManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])

# Global service instances (initialized in main.py lifespan)
model_registry: Optional[ModelRegistry] = None
server_manager: Optional[LlamaServerManager] = None
profile_manager: Optional[ProfileManager] = None
discovery_service: Optional[ModelDiscoveryService] = None


def _get_registry() -> ModelRegistry:
    """Get model registry with error handling.

    Returns:
        ModelRegistry instance

    Raises:
        HTTPException: If registry not initialized
    """
    if model_registry is None:
        logger.error("Model registry not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "Model registry not initialized. Run discovery first.",
                "details": {},
            },
        )
    return model_registry


def _get_server_manager() -> LlamaServerManager:
    """Get server manager with error handling.

    Returns:
        LlamaServerManager instance

    Raises:
        HTTPException: If server manager not initialized
    """
    if server_manager is None:
        logger.error("Server manager not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "Server manager not initialized",
                "details": {},
            },
        )
    return server_manager


def _get_profile_manager() -> ProfileManager:
    """Get profile manager with error handling.

    Returns:
        ProfileManager instance

    Raises:
        HTTPException: If profile manager not initialized
    """
    if profile_manager is None:
        logger.error("Profile manager not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "Profile manager not initialized",
                "details": {},
            },
        )
    return profile_manager


def _get_discovery_service() -> ModelDiscoveryService:
    """Get discovery service with error handling.

    Returns:
        ModelDiscoveryService instance

    Raises:
        HTTPException: If discovery service not initialized
    """
    if discovery_service is None:
        logger.error("Discovery service not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ServiceUnavailable",
                "message": "Discovery service not initialized",
                "details": {},
            },
        )
    return discovery_service


@router.get("/status")
async def get_models_status(model_manager: ModelManagerDependency, logger_dep: LoggerDependency):
    """Get status of all models with system metrics and time-series data.

    Retrieves real-time status from all configured model instances,
    including health state, performance metrics, aggregate statistics,
    and per-model time-series metrics for sparkline visualization.

    Also includes models from server_manager (dynamic/external Metal servers).

    Args:
        model_manager: ModelManager instance (injected)
        logger_dep: Logger instance (injected)

    Returns:
        System status with all model statuses, aggregate metrics, and
        per-model time-series metrics (tokens/sec, memory, latency)
    """
    logger_dep.debug("Models status requested")

    # Get real status from ModelManager (legacy static models)
    system_status = await model_manager.get_status()

    # Also include models from server_manager (dynamic/external Metal servers)
    if server_manager and server_manager.servers:
        from app.models.model import ModelState, ModelStatus

        existing_ids = {m.id for m in system_status.models}

        for model_id, server_proc in server_manager.servers.items():
            if model_id not in existing_ids:
                # Create ModelStatus for this dynamic server
                dynamic_status = ModelStatus(
                    id=model_id,
                    name=server_proc.model.get_display_name(),
                    tier=str(server_proc.model.get_effective_tier()),
                    port=server_proc.port,
                    state=ModelState.ACTIVE if server_proc.is_ready else ModelState.OFFLINE,
                    memory_used=0,  # Not tracked for external servers
                    memory_total=16384,  # Assume 16GB total
                    request_count=0,
                    avg_response_time=0.0,
                    last_active=datetime.now(timezone.utc),
                    error_count=0,
                    uptime_seconds=server_proc.get_uptime_seconds(),
                )
                system_status.models.append(dynamic_status)
                logger_dep.debug(f"Added dynamic model to status: {model_id}")

    logger_dep.info(
        "Models status retrieved",
        extra={
            "model_count": len(system_status.models),
            "active_queries": system_status.active_queries,
            "total_requests": system_status.total_requests,
            "healthy_models": sum(
                1 for m in system_status.models if m.state.value in ["active", "idle"]
            ),
        },
    )

    # Add per-model time-series metrics
    models_metrics = []
    for model_id, state in model_manager._model_states.items():
        metrics = ModelMetrics(
            model_id=model_id,
            tokens_per_second=list(state["tokens_per_second_history"]),
            current_tokens_per_second=state["last_tokens_per_second"],
            memory_gb=list(state["memory_gb_history"]),
            current_memory_gb=state["last_memory_gb"],
            latency_ms=list(state["latency_ms_history"]),
            current_latency_ms=state["latency_ms"],
        )
        models_metrics.append(metrics)

    logger_dep.debug(
        f"Collected metrics for {len(models_metrics)} models",
        extra={"metrics_count": len(models_metrics)},
    )

    # Return combined response (backward compatible)
    return {
        **system_status.model_dump(by_alias=True),
        "metrics": [m.model_dump(by_alias=True) for m in models_metrics],
        "metricsTimestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/registry", response_model_by_alias=True)
async def get_model_registry() -> dict:
    """Get full model registry with all discovered models.

    Returns:
        ModelRegistry with all models, scan info, and tier thresholds

    Raises:
        HTTPException: 503 if registry not initialized
    """
    logger.info("Model registry requested")
    registry = _get_registry()

    logger.info(
        f"Returned registry with {len(registry.models)} models",
        extra={"model_count": len(registry.models)},
    )

    # Convert to dict with camelCase aliases
    return registry.model_dump(by_alias=True)


@router.post("/rescan", response_model=RescanResponse, response_model_by_alias=True)
async def rescan_models() -> RescanResponse:
    """Re-scan HUB folder for new/removed models.

    Preserves existing user overrides (tier, thinking, enabled) while
    updating the registry with newly discovered models.

    Returns:
        Rescan results with counts of models found/added/removed

    Raises:
        HTTPException: 503 if services not initialized, 500 if rescan fails
    """
    logger.info("Model rescan requested")

    global model_registry

    registry = _get_registry()
    discovery = _get_discovery_service()

    try:
        # Store current model count
        models_before = len(registry.models)
        models_ids_before = set(registry.models.keys())

        # Perform rescan with override preservation
        updated_registry = discovery.rescan_and_update(registry)

        # Calculate changes
        models_after = len(updated_registry.models)
        models_ids_after = set(updated_registry.models.keys())

        models_added = len(models_ids_after - models_ids_before)
        models_removed = len(models_ids_before - models_ids_after)

        # Save updated registry
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery.save_registry(updated_registry, registry_path)

        # Update global state
        model_registry = updated_registry

        logger.info(
            f"Rescan complete: {models_after} total, +{models_added}, -{models_removed}",
            extra={
                "models_before": models_before,
                "models_after": models_after,
                "models_added": models_added,
                "models_removed": models_removed,
            },
        )

        return RescanResponse(
            message="Re-scan completed successfully",
            models_found=models_after,
            models_added=models_added,
            models_removed=models_removed,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    except Exception as e:
        logger.error(f"Rescan failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RescanFailed",
                "message": f"Failed to rescan models: {str(e)}",
                "details": {"error": str(e)},
            },
        )


@router.put("/port-range", response_model=PortRangeUpdateResponse, response_model_by_alias=True)
async def update_port_range(request: PortRangeUpdateRequest) -> PortRangeUpdateResponse:
    """Update the model server port range.

    This endpoint updates the port range configuration in the model registry.
    Server restart is required for changes to take effect.

    Args:
        request: PortRangeUpdateRequest with new start and end ports

    Returns:
        PortRangeUpdateResponse with updated range

    Raises:
        HTTPException: 400 if validation fails, 503 if services not initialized, 500 if update fails
    """
    logger.info(f"Port range update requested: {request.start}-{request.end}")

    global model_registry

    registry = _get_registry()
    discovery = _get_discovery_service()

    # Validate port range
    if request.start >= request.end:
        logger.warning(f"Invalid port range: start ({request.start}) >= end ({request.end})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidPortRange",
                "message": "Start port must be less than end port",
                "details": {"start": request.start, "end": request.end},
            },
        )

    if request.start < 1024 or request.end > 65535:
        logger.warning(f"Port range out of bounds: {request.start}-{request.end}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidPortRange",
                "message": "Port range must be between 1024 and 65535",
                "details": {"start": request.start, "end": request.end},
            },
        )

    try:
        # Update registry port range
        registry.port_range = (request.start, request.end)

        # Save updated registry
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery.save_registry(registry, registry_path)

        # Update global state
        model_registry = registry

        logger.info(
            f"Port range updated successfully: {request.start}-{request.end}",
            extra={"start": request.start, "end": request.end},
        )

        return PortRangeUpdateResponse(
            message="Port range updated successfully. Restart servers to apply changes.",
            start=request.start,
            end=request.end,
            restart_required=True,
        )

    except Exception as e:
        logger.error(f"Failed to update port range: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PortRangeUpdateFailed",
                "message": f"Failed to update port range: {str(e)}",
                "details": {"error": str(e)},
            },
        )


@router.put("/{model_id}/tier", response_model=TierUpdateResponse, response_model_by_alias=True)
async def update_model_tier(model_id: str, request: TierUpdateRequest) -> TierUpdateResponse:
    """Update tier assignment for a model (user override).

    Args:
        model_id: Model ID from registry
        request: Tier update request with new tier value

    Returns:
        Confirmation with updated tier information

    Raises:
        HTTPException: 404 if model not found, 400 if tier invalid
    """
    logger.info(f"Tier update requested for {model_id}: {request.tier}")

    global model_registry
    registry = _get_registry()

    # Validate model exists
    if model_id not in registry.models:
        logger.warning(f"Model not found: {model_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ModelNotFound",
                "message": f"Model '{model_id}' not found in registry",
                "details": {"model_id": model_id},
            },
        )

    # Validate tier value
    try:
        tier_enum = ModelTier(request.tier)
    except ValueError:
        logger.warning(f"Invalid tier value: {request.tier}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidTier",
                "message": f"Invalid tier value: {request.tier}",
                "details": {
                    "tier": request.tier,
                    "valid_tiers": ["fast", "balanced", "powerful"],
                },
            },
        )

    # Update tier override
    model = registry.models[model_id]
    model.tier_override = tier_enum

    # Save registry
    try:
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery = _get_discovery_service()
        discovery.save_registry(registry, registry_path)

        logger.info(
            f"Tier updated for {model_id}: {request.tier}",
            extra={"model_id": model_id, "tier": request.tier},
        )

        return TierUpdateResponse(
            message=f"Tier updated for {model_id}",
            model_id=model_id,
            tier=request.tier,
            override=True,
        )

    except Exception as e:
        logger.error(f"Failed to save registry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RegistrySaveFailed",
                "message": f"Failed to save registry: {str(e)}",
                "details": {"error": str(e)},
            },
        )


@router.put(
    "/{model_id}/thinking",
    response_model=ThinkingUpdateResponse,
    response_model_by_alias=True,
)
async def update_model_thinking(
    model_id: str, request: ThinkingUpdateRequest
) -> ThinkingUpdateResponse:
    """Update thinking capability for a model (user override).

    If thinking=true and no tier override exists, automatically assigns
    POWERFUL tier.

    Args:
        model_id: Model ID from registry
        request: Thinking update request with new thinking status

    Returns:
        Confirmation with updated thinking status and tier change info

    Raises:
        HTTPException: 404 if model not found
    """
    logger.info(f"Thinking update requested for {model_id}: {request.thinking}")

    global model_registry
    registry = _get_registry()

    # Validate model exists
    if model_id not in registry.models:
        logger.warning(f"Model not found: {model_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ModelNotFound",
                "message": f"Model '{model_id}' not found in registry",
                "details": {"model_id": model_id},
            },
        )

    model = registry.models[model_id]

    # Update thinking override
    model.thinking_override = request.thinking

    # Auto-assign POWERFUL tier if thinking enabled and no tier override
    tier_changed = False
    if request.thinking and model.tier_override is None:
        model.tier_override = ModelTier.POWERFUL
        tier_changed = True
        logger.info(f"Auto-assigned POWERFUL tier for thinking model: {model_id}")

    # Save registry
    try:
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery = _get_discovery_service()
        discovery.save_registry(registry, registry_path)

        logger.info(
            f"Thinking capability updated for {model_id}: {request.thinking}",
            extra={
                "model_id": model_id,
                "thinking": request.thinking,
                "tier_changed": tier_changed,
            },
        )

        return ThinkingUpdateResponse(
            message=f"Thinking capability updated for {model_id}",
            model_id=model_id,
            thinking=request.thinking,
            override=True,
            tier_changed=tier_changed,
        )

    except Exception as e:
        logger.error(f"Failed to save registry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RegistrySaveFailed",
                "message": f"Failed to save registry: {str(e)}",
                "details": {"error": str(e)},
            },
        )


@router.put(
    "/{model_id}/enabled",
    response_model=EnabledUpdateResponse,
    response_model_by_alias=True,
)
async def toggle_model_enabled(
    model_id: str, request: EnabledUpdateRequest
) -> EnabledUpdateResponse:
    """Enable or disable a model AND start/stop its server dynamically.

    Args:
        model_id: Model ID from registry
        request: Enabled status update request

    Returns:
        Confirmation with enabled status and server status

    Raises:
        HTTPException: 404 if model not found
    """
    logger.info(f"Enabled status update requested for {model_id}: {request.enabled}")

    global model_registry
    registry = _get_registry()

    # Validate model exists
    if model_id not in registry.models:
        logger.warning(f"Model not found: {model_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ModelNotFound",
                "message": f"Model '{model_id}' not found in registry",
                "details": {"model_id": model_id},
            },
        )

    model = registry.models[model_id]

    # Update enabled status
    model.enabled = request.enabled

    # Save registry
    try:
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery = _get_discovery_service()
        discovery.save_registry(registry, registry_path)

        status_str = "enabled" if request.enabled else "disabled"
        logger.info(
            f"Model {model_id} {status_str}",
            extra={"model_id": model_id, "enabled": request.enabled},
        )

    except Exception as e:
        logger.error(f"Failed to save registry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RegistrySaveFailed",
                "message": f"Failed to save registry: {str(e)}",
                "details": {"error": str(e)},
            },
        )

    # NOTE: Enabling/disabling only updates registry - does NOT start/stop servers
    # Use "START ALL ENABLED" button to start servers for enabled models
    return EnabledUpdateResponse(
        message=f"Model {model_id} {status_str} in registry",
        model_id=model_id,
        enabled=request.enabled,
        restart_required=False,
        server_status="registry_updated",
    )


@router.post(
    "/enable-all",
    response_model=BulkEnabledUpdateResponse,
    response_model_by_alias=True,
)
async def enable_all_models() -> BulkEnabledUpdateResponse:
    """Enable all discovered models in the registry.

    This is a bulk operation that enables all models without starting servers.
    Use 'START ALL ENABLED' to start servers after enabling.

    Returns:
        Confirmation with count of models updated

    Raises:
        HTTPException: 503 if services not initialized, 500 if save fails
    """
    logger.info("Bulk enable requested for all models")

    registry = _get_registry()
    discovery = _get_discovery_service()

    models_updated = 0
    for model in registry.models.values():
        if not model.enabled:
            model.enabled = True
            models_updated += 1

    # Save registry
    try:
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery.save_registry(registry, registry_path)
        logger.info(f"Bulk enable completed: {models_updated} models enabled")
    except Exception as e:
        logger.error(f"Failed to save registry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RegistrySaveFailed",
                "message": f"Failed to save registry: {str(e)}",
            },
        )

    return BulkEnabledUpdateResponse(
        message=f"All models enabled ({models_updated} updated)",
        models_updated=models_updated,
        enabled=True,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post(
    "/disable-all",
    response_model=BulkEnabledUpdateResponse,
    response_model_by_alias=True,
)
async def disable_all_models() -> BulkEnabledUpdateResponse:
    """Disable all discovered models in the registry.

    This is a bulk operation that disables all models without stopping servers.
    Running servers continue until explicitly stopped.

    Returns:
        Confirmation with count of models updated

    Raises:
        HTTPException: 503 if services not initialized, 500 if save fails
    """
    logger.info("Bulk disable requested for all models")

    registry = _get_registry()
    discovery = _get_discovery_service()

    models_updated = 0
    for model in registry.models.values():
        if model.enabled:
            model.enabled = False
            models_updated += 1

    # Save registry
    try:
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery.save_registry(registry, registry_path)
        logger.info(f"Bulk disable completed: {models_updated} models disabled")
    except Exception as e:
        logger.error(f"Failed to save registry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RegistrySaveFailed",
                "message": f"Failed to save registry: {str(e)}",
            },
        )

    return BulkEnabledUpdateResponse(
        message=f"All models disabled ({models_updated} updated)",
        models_updated=models_updated,
        enabled=False,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# Phase 2: Per-Model Configuration Endpoints
# ============================================================================


@router.put("/{model_id}/port", response_model=PortUpdateResponse, response_model_by_alias=True)
async def update_model_port(model_id: str, request: PortUpdateRequest) -> PortUpdateResponse:
    """Assign a specific port to a model.

    Args:
        model_id: Model ID from registry
        request: Port assignment request

    Returns:
        Confirmation with restart_required flag

    Raises:
        HTTPException: 404 if model not found, 409 if port in use, 400 if port out of range
    """
    logger.info(f"Port assignment requested for {model_id}: port {request.port}")

    global model_registry
    registry = _get_registry()

    # Validate model exists
    if model_id not in registry.models:
        logger.warning(f"Model not found: {model_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ModelNotFound",
                "message": f"Model '{model_id}' not found in registry",
                "details": {"model_id": model_id},
            },
        )

    # Validate port in range
    if request.port < registry.port_range[0] or request.port > registry.port_range[1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PortOutOfRange",
                "message": f"Port {request.port} outside allowed range {registry.port_range}",
                "details": {"port": request.port, "port_range": registry.port_range},
            },
        )

    # Check port not already in use by another model
    for mid, m in registry.models.items():
        if mid != model_id and m.port == request.port:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "PortInUse",
                    "message": f"Port {request.port} already assigned to {m.get_display_name()}",
                    "details": {
                        "port": request.port,
                        "assigned_to": mid,
                        "assigned_to_name": m.get_display_name(),
                    },
                },
            )

    model = registry.models[model_id]
    old_port = model.port
    model.port = request.port

    # Save registry
    try:
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery = _get_discovery_service()
        discovery.save_registry(registry, registry_path)
        logger.info(f"Port updated for {model_id}: {old_port} → {request.port}")
    except Exception as e:
        logger.error(f"Failed to save registry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RegistrySaveFailed",
                "message": f"Failed to save registry: {str(e)}",
                "details": {"error": str(e)},
            },
        )

    # Check if server restart is required
    restart_required = server_manager and server_manager.is_server_running(model_id)

    return PortUpdateResponse(
        message=f"Port assigned successfully to {model.get_display_name()}",
        model_id=model_id,
        port=request.port,
        restart_required=restart_required,
    )


@router.put(
    "/{model_id}/runtime-settings",
    response_model=RuntimeSettingsUpdateResponse,
    response_model_by_alias=True,
)
async def update_model_runtime_settings(
    model_id: str, request: RuntimeSettingsUpdateRequest
) -> RuntimeSettingsUpdateResponse:
    """Update per-model runtime settings overrides.

    Any field set to a value will override the global setting.
    Any field set to None will use the global setting.

    Args:
        model_id: Model ID from registry
        request: Runtime settings update request

    Returns:
        Confirmation with current override values and restart_required flag

    Raises:
        HTTPException: 404 if model not found
    """
    logger.info(f"Runtime settings update requested for {model_id}")

    global model_registry
    registry = _get_registry()

    # Validate model exists
    if model_id not in registry.models:
        logger.warning(f"Model not found: {model_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ModelNotFound",
                "message": f"Model '{model_id}' not found in registry",
                "details": {"model_id": model_id},
            },
        )

    model = registry.models[model_id]

    # Update overrides (None means "use global setting")
    model.n_gpu_layers = request.n_gpu_layers
    model.ctx_size = request.ctx_size
    model.n_threads = request.n_threads
    model.batch_size = request.batch_size

    # Save registry
    try:
        registry_path = Path(os.getenv("REGISTRY_PATH", "data/model_registry.json"))
        discovery = _get_discovery_service()
        discovery.save_registry(registry, registry_path)
        logger.info(
            f"Runtime settings updated for {model_id}: "
            f"GPU={model.n_gpu_layers}, ctx={model.ctx_size}, "
            f"threads={model.n_threads}, batch={model.batch_size}"
        )
    except Exception as e:
        logger.error(f"Failed to save registry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RegistrySaveFailed",
                "message": f"Failed to save registry: {str(e)}",
                "details": {"error": str(e)},
            },
        )

    # Check if server restart is required
    restart_required = server_manager and server_manager.is_server_running(model_id)

    return RuntimeSettingsUpdateResponse(
        message=f"Runtime settings updated for {model.get_display_name()}",
        model_id=model_id,
        n_gpu_layers=model.n_gpu_layers,
        ctx_size=model.ctx_size,
        n_threads=model.n_threads,
        batch_size=model.batch_size,
        restart_required=restart_required,
    )


@router.get("/servers", response_model=ServerStatusResponse, response_model_by_alias=True)
async def get_server_status() -> ServerStatusResponse:
    """Get status of all running llama.cpp servers.

    Returns:
        Server status summary with details for each running server

    Raises:
        HTTPException: 503 if server manager not initialized
    """
    logger.info("Server status requested")

    manager = _get_server_manager()

    # Get status from server manager
    status_summary = manager.get_status_summary()

    logger.info(
        f"Server status retrieved: {status_summary['total_servers']} servers",
        extra={
            "total_servers": status_summary["total_servers"],
            "ready_servers": status_summary["ready_servers"],
        },
    )

    return ServerStatusResponse(
        total_servers=status_summary["total_servers"],
        ready_servers=status_summary["ready_servers"],
        servers=status_summary["servers"],
    )


# ============================================================================
# DYNAMIC MODEL SERVER CONTROL (NO RESTART REQUIRED)
# ============================================================================


@router.post("/servers/{model_id}/start", response_model=dict)
async def start_model_server(model_id: str):
    """Start llama.cpp server for a specific model (dynamic, no restart).

    This endpoint allows starting individual model servers on-demand from the WebUI.
    Users can enable a model and immediately start its server without restarting Docker.

    Args:
        model_id: Unique model identifier from registry

    Returns:
        Server start status with port and timing information

    Raises:
        404: Model not found in registry
        503: Server manager not initialized
        500: Server failed to start
    """
    if not model_registry or model_id not in model_registry.models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

    if not server_manager:
        raise HTTPException(status_code=503, detail="Server manager not initialized")

    model = model_registry.models[model_id]

    # Check if already running
    if server_manager.is_server_running(model_id):
        logger.info(f"Server already running for {model_id}")
        return {
            "message": f"Server already running for {model_id}",
            "model_id": model_id,
            "port": model.port,
            "status": "already_running",
        }

    try:
        # Start server asynchronously
        logger.info(f"Starting server for {model_id}...")
        start_time = time.time()

        await server_manager.start_server(model)

        elapsed = time.time() - start_time
        logger.info(f"✓ Started server for {model_id} on port {model.port} ({elapsed:.1f}s)")

        return {
            "message": f"Server started for {model_id}",
            "model_id": model_id,
            "display_name": model.get_display_name(),
            "port": model.port,
            "status": "started",
            "startup_time_seconds": round(elapsed, 2),
        }

    except Exception as e:
        logger.error(f"✗ Failed to start server for {model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")


@router.post("/servers/{model_id}/stop", response_model=dict)
async def stop_model_server(model_id: str):
    """Stop llama.cpp server for a specific model (dynamic, no restart).

    This endpoint allows stopping individual model servers on-demand from the WebUI.
    Servers are gracefully shut down with SIGTERM, then SIGKILL if needed.

    Args:
        model_id: Unique model identifier from registry

    Returns:
        Server stop status

    Raises:
        503: Server manager not initialized
    """
    if not server_manager:
        raise HTTPException(status_code=503, detail="Server manager not initialized")

    # Check if running
    if not server_manager.is_server_running(model_id):
        logger.info(f"Server not running for {model_id}")
        return {
            "message": f"Server not running for {model_id}",
            "model_id": model_id,
            "status": "not_running",
        }

    try:
        logger.info(f"Stopping server for {model_id}...")
        stop_time = time.time()

        await server_manager.stop_server(model_id)

        elapsed = time.time() - stop_time
        logger.info(f"✓ Stopped server for {model_id} ({elapsed:.1f}s)")

        return {
            "message": f"Server stopped for {model_id}",
            "model_id": model_id,
            "status": "stopped",
            "shutdown_time_seconds": round(elapsed, 2),
        }

    except Exception as e:
        logger.error(f"✗ Failed to stop server for {model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {str(e)}")


@router.post("/servers/start-all", response_model=dict)
async def start_all_enabled_servers():
    """Start all enabled models (dynamic, no restart).

    This endpoint launches servers for all models marked as enabled in the registry.
    Servers start concurrently for optimal performance.

    Returns:
        Summary of servers started with timing information

    Raises:
        503: Model registry or server manager not initialized
    """
    if not model_registry:
        raise HTTPException(status_code=503, detail="Model registry not initialized")

    if not server_manager:
        raise HTTPException(status_code=503, detail="Server manager not initialized")

    # Get all enabled models
    enabled_models = [model for model in model_registry.models.values() if model.enabled]

    if not enabled_models:
        logger.info("No enabled models to start")
        return {
            "message": "No enabled models to start",
            "started": 0,
            "total": 0,
            "models": [],
        }

    try:
        logger.info(f"Starting {len(enabled_models)} enabled models...")
        start_time = time.time()

        # Start all concurrently
        results = await server_manager.start_all(enabled_models)

        elapsed = time.time() - start_time
        logger.info(
            f"✓ Started {len(results)}/{len(enabled_models)} servers ({elapsed:.1f}s total)"
        )

        return {
            "message": f"Started {len(results)}/{len(enabled_models)} servers",
            "started": len(results),
            "total": len(enabled_models),
            "startup_time_seconds": round(elapsed, 2),
            "models": [
                {
                    "model_id": m.model_id,
                    "display_name": m.get_display_name(),
                    "port": m.port,
                }
                for m in enabled_models
            ],
        }

    except Exception as e:
        logger.error(f"✗ Failed to start servers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start servers: {str(e)}")


@router.post("/servers/stop-all", response_model=dict)
async def stop_all_servers():
    """Stop all running servers (dynamic, no restart).

    This endpoint gracefully shuts down all running llama.cpp servers.
    In external server mode, calls host-api to stop Metal-accelerated servers.
    Useful for freeing memory or switching to a different model set.

    Returns:
        Summary of servers stopped

    Raises:
        503: Server manager not initialized
    """
    if not server_manager:
        raise HTTPException(status_code=503, detail="Server manager not initialized")

    try:
        # In external server mode, always call stop_all() to reach host-api
        # The internal servers dict won't be populated for external servers
        if server_manager.use_external_servers:
            logger.info("🛑 Stopping external Metal servers via host API...")
            stop_time = time.time()

            await server_manager.stop_all()

            elapsed = time.time() - stop_time
            logger.info(f"✓ External Metal servers stopped ({elapsed:.1f}s)")

            return {
                "message": "Stopped Metal-accelerated servers on host",
                "stopped": 1,  # At least one conceptual "server group" was stopped
                "shutdown_time_seconds": round(elapsed, 2),
            }

        # Internal server mode - check tracked servers
        running_count = len(server_manager.servers)

        if running_count == 0:
            logger.info("No servers running to stop")
            return {"message": "No servers running", "stopped": 0}

        logger.info(f"Stopping {running_count} running servers...")
        stop_time = time.time()

        await server_manager.stop_all()

        elapsed = time.time() - stop_time
        logger.info(f"✓ Stopped {running_count} servers ({elapsed:.1f}s)")

        return {
            "message": f"Stopped {running_count} servers",
            "stopped": running_count,
            "shutdown_time_seconds": round(elapsed, 2),
        }

    except Exception as e:
        logger.error(f"✗ Failed to stop servers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop servers: {str(e)}")


@router.get("/tiers/{tier}", response_model=List[DiscoveredModel], response_model_by_alias=True)
async def get_models_by_tier(tier: str) -> List[DiscoveredModel]:
    """Get all models in a specific tier.

    Args:
        tier: Tier name (fast, balanced, powerful)

    Returns:
        List of DiscoveredModel objects in that tier

    Raises:
        HTTPException: 400 if tier invalid, 503 if registry not initialized
    """
    logger.info(f"Models by tier requested: {tier}")

    registry = _get_registry()

    # Validate tier
    try:
        tier_enum = ModelTier(tier)
    except ValueError:
        logger.warning(f"Invalid tier value: {tier}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidTier",
                "message": f"Invalid tier value: {tier}",
                "details": {
                    "tier": tier,
                    "valid_tiers": ["fast", "balanced", "powerful"],
                },
            },
        )

    # Get models in tier
    models = registry.get_by_tier(tier_enum)

    logger.info(
        f"Found {len(models)} models in tier '{tier}'",
        extra={"tier": tier, "count": len(models)},
    )

    return models


@router.get("/profiles", response_model=List[str])
async def list_profiles() -> List[str]:
    """List available configuration profiles.

    Returns:
        List of profile names (without .yaml extension)

    Raises:
        HTTPException: 503 if profile manager not initialized
    """
    logger.info("Profile list requested")

    manager = _get_profile_manager()
    profiles = manager.list_profiles()

    logger.info(f"Found {len(profiles)} profiles", extra={"count": len(profiles)})

    return profiles


@router.get(
    "/profiles/{profile_name}",
    response_model=ModelProfile,
    response_model_by_alias=True,
)
async def get_profile(profile_name: str) -> ModelProfile:
    """Get details of a specific profile.

    Args:
        profile_name: Profile name to retrieve

    Returns:
        ModelProfile with full configuration

    Raises:
        HTTPException: 404 if profile not found, 503 if manager not initialized
    """
    logger.info(f"Profile details requested: {profile_name}")

    manager = _get_profile_manager()

    try:
        profile = manager.load_profile(profile_name)

        logger.info(
            f"Loaded profile '{profile_name}'",
            extra={
                "profile": profile_name,
                "enabled_models": len(profile.enabled_models),
            },
        )

        return profile

    except SynapseException as e:
        logger.warning(f"Profile not found: {profile_name}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": "ProfileNotFound",
                "message": e.message,
                "details": e.details,
            },
        )


@router.post(
    "/profiles",
    response_model=ProfileCreateResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    profile_request: ProfileCreateRequest,
) -> ProfileCreateResponse:
    """Create a new configuration profile.

    Args:
        profile_request: Profile creation request with name and settings

    Returns:
        Confirmation with profile name and file path

    Raises:
        HTTPException: 400 if validation fails, 503 if manager not initialized
    """
    logger.info(f"Profile creation requested: {profile_request.name}")

    manager = _get_profile_manager()

    try:
        # Create ModelProfile from request
        profile = ModelProfile(
            name=profile_request.name,
            description=profile_request.description,
            enabled_models=profile_request.enabled_models,
        )

        # Save profile
        profile_path = manager.save_profile(profile)

        logger.info(
            f"Profile '{profile_request.name}' created",
            extra={"profile": profile_request.name, "path": str(profile_path)},
        )

        return ProfileCreateResponse(
            message=f"Profile '{profile_request.name}' created successfully",
            profile_name=profile_path.stem,
            path=str(profile_path.absolute()),
        )

    except Exception as e:
        logger.error(f"Failed to create profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ProfileCreationFailed",
                "message": f"Failed to create profile: {str(e)}",
                "details": {"error": str(e)},
            },
        )


@router.delete(
    "/profiles/{profile_name}",
    response_model=ProfileDeleteResponse,
    response_model_by_alias=True,
)
async def delete_profile(profile_name: str) -> ProfileDeleteResponse:
    """Delete a configuration profile.

    Note: Cannot delete the currently active profile.

    Args:
        profile_name: Profile name to delete

    Returns:
        Confirmation message

    Raises:
        HTTPException: 404 if profile not found, 503 if manager not initialized
    """
    logger.info(f"Profile deletion requested: {profile_name}")

    manager = _get_profile_manager()

    try:
        manager.delete_profile(profile_name)

        logger.info(f"Profile '{profile_name}' deleted")

        return ProfileDeleteResponse(message=f"Profile '{profile_name}' deleted successfully")

    except SynapseException as e:
        logger.warning(f"Failed to delete profile '{profile_name}': {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": "ProfileDeletionFailed",
                "message": e.message,
                "details": e.details,
            },
        )
