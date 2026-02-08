"""Settings API router for runtime configuration management.

Provides REST endpoints for viewing and modifying runtime settings
that can be adjusted without system reconfiguration.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from app.models.runtime_settings import RuntimeSettings
from app.services import runtime_settings as settings_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Response model for settings operations."""

    success: bool
    settings: RuntimeSettings
    restart_required: bool = False
    validation_errors: list[str] = []
    message: str = ""
    metadata: Dict[str, Any] = {}


class SettingsUpdateRequest(BaseModel):
    """Request model for settings updates."""

    settings: RuntimeSettings


class SettingsImportRequest(BaseModel):
    """Request model for importing settings from JSON."""

    json_data: str


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current runtime settings.

    Returns:
        SettingsResponse with current settings and metadata
    """
    try:
        settings = settings_service.get_runtime_settings()
        metadata = await settings_service.get_settings_metadata()

        return SettingsResponse(
            success=True,
            settings=settings,
            restart_required=False,
            message="Settings retrieved successfully",
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve settings: {str(e)}")


@router.put("", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest):
    """Update runtime settings with validation.

    This endpoint validates the new settings and saves them if valid.
    Changes to GPU/VRAM settings will set restart_required=True.

    Args:
        request: SettingsUpdateRequest with new settings

    Returns:
        SettingsResponse with updated settings and restart flag
    """
    try:
        (
            success,
            updated_settings,
            restart_required,
            errors,
        ) = await settings_service.update_runtime_settings(request.settings)

        if not success:
            return SettingsResponse(
                success=False,
                settings=settings_service.get_runtime_settings(),  # Return current settings
                restart_required=False,
                validation_errors=errors,
                message="Settings validation failed",
            )

        message = "Settings updated successfully"
        if restart_required:
            message += " (server restart required for GPU/VRAM changes to take effect)"

        return SettingsResponse(
            success=True,
            settings=updated_settings,
            restart_required=restart_required,
            message=message,
            metadata=await settings_service.get_settings_metadata(),
        )

    except ValidationError as e:
        logger.warning(f"Settings validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid settings: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.post("/validate", response_model=SettingsResponse)
async def validate_settings(request: SettingsUpdateRequest):
    """Validate settings without saving.

    Useful for client-side validation before user commits changes.

    Args:
        request: SettingsUpdateRequest with settings to validate

    Returns:
        SettingsResponse with validation results
    """
    try:
        is_valid, errors = await settings_service.validate_settings(request.settings)

        current_settings = settings_service.get_runtime_settings()
        restart_required = request.settings.requires_server_restart(current_settings)

        return SettingsResponse(
            success=is_valid,
            settings=request.settings if is_valid else current_settings,
            restart_required=restart_required,
            validation_errors=errors,
            message="Validation successful" if is_valid else "Validation failed",
        )

    except Exception as e:
        logger.error(f"Failed to validate settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate settings: {str(e)}")


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings():
    """Reset settings to defaults.

    This will overwrite the current settings file with default values.

    Returns:
        SettingsResponse with default settings
    """
    try:
        defaults = await settings_service.reset_to_defaults()

        return SettingsResponse(
            success=True,
            settings=defaults,
            restart_required=True,  # Assume defaults differ from current
            message="Settings reset to defaults successfully",
            metadata=await settings_service.get_settings_metadata(),
        )

    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")


@router.get("/export")
async def export_settings():
    """Export current settings as JSON.

    Returns:
        JSON string of current settings
    """
    try:
        json_str = await settings_service.export_settings_json()

        return {
            "success": True,
            "json_data": json_str,
            "message": "Settings exported successfully",
        }

    except Exception as e:
        logger.error(f"Failed to export settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export settings: {str(e)}")


@router.post("/import", response_model=SettingsResponse)
async def import_settings(request: SettingsImportRequest):
    """Import settings from JSON string.

    Validates the JSON and settings schema before importing.
    Does NOT save automatically - use PUT /api/settings to save.

    Args:
        request: SettingsImportRequest with JSON data

    Returns:
        SettingsResponse with imported settings (not saved)
    """
    try:
        (
            success,
            imported_settings,
            errors,
        ) = await settings_service.import_settings_json(request.json_data)

        if not success or imported_settings is None:
            return SettingsResponse(
                success=False,
                settings=settings_service.get_runtime_settings(),
                validation_errors=errors,
                message="Settings import failed",
            )

        current_settings = settings_service.get_runtime_settings()
        restart_required = imported_settings.requires_server_restart(current_settings)

        return SettingsResponse(
            success=True,
            settings=imported_settings,
            restart_required=restart_required,
            message="Settings imported successfully (not saved - use PUT to save)",
        )

    except Exception as e:
        logger.error(f"Failed to import settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import settings: {str(e)}")


@router.get("/schema")
async def get_settings_schema():
    """Get JSON schema for RuntimeSettings.

    Useful for dynamically generating UI forms.

    Returns:
        JSON schema dict
    """
    try:
        schema = RuntimeSettings.model_json_schema()

        return {
            "success": True,
            "schema": schema,
            "message": "Settings schema retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Failed to get settings schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve settings schema: {str(e)}")


@router.get("/vram-estimate")
async def estimate_vram(model_size_b: float = 8.0, quantization: str = "Q4_K_M"):
    """Estimate VRAM usage per model with current settings.

    Query parameters:
        model_size_b: Model size in billions (default: 8.0)
        quantization: Quantization type (default: Q4_K_M)

    Returns:
        VRAM estimate in GB
    """
    try:
        # Validate model_size_b range
        if model_size_b < 0.1 or model_size_b > 100.0:
            raise HTTPException(
                status_code=400, detail="model_size_b must be between 0.1 and 100.0"
            )

        settings = settings_service.get_runtime_settings()
        vram_gb = settings.estimate_vram_per_model(
            model_size_b=model_size_b, quantization=quantization
        )

        return {
            "success": True,
            "vram_gb": vram_gb,
            "model_size_b": model_size_b,
            "quantization": quantization,
            "settings": {
                "n_gpu_layers": settings.n_gpu_layers,
                "ctx_size": settings.ctx_size,
            },
            "message": f"Estimated VRAM: {vram_gb} GB",
        }

    except Exception as e:
        logger.error(f"Failed to estimate VRAM: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to estimate VRAM: {str(e)}")
