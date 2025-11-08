"""API request and response models for model management endpoints.

This module defines Pydantic models for validating API requests and
responses in the model management REST API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class TierUpdateRequest(BaseModel):
    """Request to update model tier assignment."""

    tier: str = Field(
        ...,
        description="New tier (fast/balanced/powerful)",
        pattern="^(fast|balanced|powerful)$"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tier": "powerful"
            }
        }
    )


class ThinkingUpdateRequest(BaseModel):
    """Request to update thinking capability."""

    thinking: bool = Field(
        ...,
        description="Thinking model flag"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "thinking": True
            }
        }
    )


class EnabledUpdateRequest(BaseModel):
    """Request to toggle enabled status."""

    enabled: bool = Field(
        ...,
        description="Enabled flag"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True
            }
        }
    )


class TierUpdateResponse(BaseModel):
    """Response from tier update operation."""

    message: str = Field(..., description="Human-readable success message")
    model_id: str = Field(..., description="Model identifier", alias="modelId")
    tier: str = Field(..., description="New tier value")
    override: bool = Field(..., description="Whether this is a user override")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Tier updated for deepseek_r1_8b_q4km_powerful",
                "modelId": "deepseek_r1_8b_q4km_powerful",
                "tier": "powerful",
                "override": True
            }
        }
    )


class ThinkingUpdateResponse(BaseModel):
    """Response from thinking capability update operation."""

    message: str = Field(..., description="Human-readable success message")
    model_id: str = Field(..., description="Model identifier", alias="modelId")
    thinking: bool = Field(..., description="New thinking status")
    override: bool = Field(..., description="Whether this is a user override")
    tier_changed: bool = Field(
        ...,
        description="Whether tier was auto-updated",
        alias="tierChanged"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Thinking capability updated for deepseek_r1_8b_q4km_powerful",
                "modelId": "deepseek_r1_8b_q4km_powerful",
                "thinking": True,
                "override": True,
                "tierChanged": False
            }
        }
    )


class EnabledUpdateResponse(BaseModel):
    """Response from enabled status update operation."""

    message: str = Field(..., description="Human-readable success message")
    model_id: str = Field(..., description="Model identifier", alias="modelId")
    enabled: bool = Field(..., description="New enabled status")
    restart_required: bool = Field(
        ...,
        description="Whether server restart is required",
        alias="restartRequired"
    )
    server_status: Optional[str] = Field(
        default=None,
        description="Dynamic server status (started, stopped, already_running, etc.)",
        alias="serverStatus"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Model deepseek_r1_8b_q4km_powerful enabled",
                "modelId": "deepseek_r1_8b_q4km_powerful",
                "enabled": True,
                "restartRequired": False,
                "serverStatus": "started"
            }
        }
    )


class RescanResponse(BaseModel):
    """Response from model rescan operation."""

    message: str = Field(..., description="Human-readable success message")
    models_found: int = Field(..., description="Total models found", alias="modelsFound")
    models_added: int = Field(
        default=0,
        description="Number of new models added",
        alias="modelsAdded"
    )
    models_removed: int = Field(
        default=0,
        description="Number of models removed",
        alias="modelsRemoved"
    )
    timestamp: str = Field(..., description="ISO timestamp of rescan")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Re-scan completed successfully",
                "modelsFound": 5,
                "modelsAdded": 1,
                "modelsRemoved": 0,
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }
    )


class ServerStatusItem(BaseModel):
    """Status information for a single running server."""

    model_id: str = Field(..., description="Model identifier", alias="modelId")
    display_name: str = Field(..., description="Human-readable name", alias="displayName")
    port: int = Field(..., description="HTTP port server is listening on")
    pid: Optional[int] = Field(None, description="Process ID (None for external servers)")
    is_ready: bool = Field(..., description="Server readiness status", alias="isReady")
    is_running: bool = Field(..., description="Process alive status", alias="isRunning")
    uptime_seconds: int = Field(..., description="Uptime in seconds", alias="uptimeSeconds")
    tier: str = Field(..., description="Model tier")
    is_thinking: bool = Field(..., description="Thinking model flag", alias="isThinking")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "modelId": "deepseek_r1_8b_q4km_powerful",
                "displayName": "DEEPSEEK R1 8.0B Q4_K_M",
                "port": 8080,
                "pid": 12345,
                "isReady": True,
                "isRunning": True,
                "uptimeSeconds": 120,
                "tier": "powerful",
                "isThinking": True
            }
        }
    )


class ServerStatusResponse(BaseModel):
    """Response containing status of all running servers."""

    total_servers: int = Field(
        ...,
        description="Total number of servers",
        alias="totalServers"
    )
    ready_servers: int = Field(
        ...,
        description="Number of ready servers",
        alias="readyServers"
    )
    servers: List[ServerStatusItem] = Field(..., description="List of server statuses")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "totalServers": 2,
                "readyServers": 2,
                "servers": [
                    {
                        "modelId": "deepseek_r1_8b_q4km_powerful",
                        "displayName": "DEEPSEEK R1 8.0B Q4_K_M",
                        "port": 8080,
                        "pid": 12345,
                        "isReady": True,
                        "isRunning": True,
                        "uptimeSeconds": 120,
                        "tier": "powerful",
                        "isThinking": True
                    }
                ]
            }
        }
    )


class ProfileCreateRequest(BaseModel):
    """Request to create a new profile."""

    name: str = Field(..., description="Profile name")
    description: Optional[str] = Field(None, description="Profile description")
    enabled_models: List[str] = Field(
        default_factory=list,
        description="List of model IDs to enable",
        alias="enabledModels"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Production",
                "description": "Production deployment with all tiers",
                "enabledModels": [
                    "qwen3_4p0b_q4km_fast",
                    "qwen3_7p0b_q4km_balanced",
                    "deepseek_r1_8b_q4km_powerful"
                ]
            }
        }
    )


class ProfileCreateResponse(BaseModel):
    """Response from profile creation."""

    message: str = Field(..., description="Human-readable success message")
    profile_name: str = Field(..., description="Created profile name", alias="profileName")
    path: str = Field(..., description="Path to profile file")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Profile 'Production' created successfully",
                "profileName": "production",
                "path": "/Users/dperez/Documents/Programming/S.Y.N.A.P.S.E-ENGINE/config/profiles/production.yaml"
            }
        }
    )


class ProfileDeleteResponse(BaseModel):
    """Response from profile deletion."""

    message: str = Field(..., description="Human-readable success message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Profile 'test' deleted successfully"
            }
        }
    )


# Phase 2: Per-model configuration endpoints


class PortUpdateRequest(BaseModel):
    """Request to update model port assignment."""

    port: int = Field(
        ...,
        ge=1024,
        le=65535,
        description="Port number to assign to model"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "port": 8083
            }
        }
    )


class PortUpdateResponse(BaseModel):
    """Response from port assignment update."""

    message: str = Field(..., description="Human-readable success message")
    model_id: str = Field(..., description="Model identifier", alias="modelId")
    port: int = Field(..., description="Assigned port number")
    restart_required: bool = Field(
        ...,
        description="Whether server restart is required",
        alias="restartRequired"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Port assigned successfully",
                "modelId": "deepseek_r1_8b_q4km_powerful",
                "port": 8083,
                "restartRequired": True
            }
        }
    )


class RuntimeSettingsUpdateRequest(BaseModel):
    """Request to update per-model runtime settings overrides."""

    n_gpu_layers: Optional[int] = Field(
        None,
        ge=0,
        le=999,
        description="GPU layers override (None = use global)",
        alias="nGpuLayers"
    )
    ctx_size: Optional[int] = Field(
        None,
        ge=512,
        le=131072,
        description="Context size override (None = use global)",
        alias="ctxSize"
    )
    n_threads: Optional[int] = Field(
        None,
        ge=1,
        le=128,
        description="Thread count override (None = use global)",
        alias="nThreads"
    )
    batch_size: Optional[int] = Field(
        None,
        ge=1,
        le=4096,
        description="Batch size override (None = use global)",
        alias="batchSize"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "nGpuLayers": 50,
                "ctxSize": 32768,
                "nThreads": 8,
                "batchSize": 512
            }
        }
    )


class RuntimeSettingsUpdateResponse(BaseModel):
    """Response from runtime settings update."""

    message: str = Field(..., description="Human-readable success message")
    model_id: str = Field(..., description="Model identifier", alias="modelId")
    n_gpu_layers: Optional[int] = Field(None, description="GPU layers override", alias="nGpuLayers")
    ctx_size: Optional[int] = Field(None, description="Context size override", alias="ctxSize")
    n_threads: Optional[int] = Field(None, description="Thread count override", alias="nThreads")
    batch_size: Optional[int] = Field(None, description="Batch size override", alias="batchSize")
    restart_required: bool = Field(
        ...,
        description="Whether server restart is required",
        alias="restartRequired"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Runtime settings updated successfully",
                "modelId": "deepseek_r1_8b_q4km_powerful",
                "nGpuLayers": 50,
                "ctxSize": 32768,
                "nThreads": 8,
                "batchSize": 512,
                "restartRequired": True
            }
        }
    )


class PortRangeUpdateRequest(BaseModel):
    """Request to update model server port range."""

    start: int = Field(..., ge=1024, le=65535, description="Start port of range (minimum 1024)")
    end: int = Field(..., ge=1024, le=65535, description="End port of range (maximum 65535)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start": 8080,
                "end": 8099
            }
        }
    )


class PortRangeUpdateResponse(BaseModel):
    """Response from port range update operation."""

    message: str = Field(..., description="Human-readable success message")
    start: int = Field(..., description="Start port of new range")
    end: int = Field(..., description="End port of new range")
    restart_required: bool = Field(
        ...,
        description="Whether server restart is required",
        alias="restartRequired"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Port range updated successfully. Restart servers to apply changes.",
                "start": 8080,
                "end": 8099,
                "restartRequired": True
            }
        }
    )


class ExternalServerItem(BaseModel):
    """Details about a single external Metal server."""

    port: int = Field(..., description="Port number the server is running on")
    status: str = Field(..., description="Server status: 'online', 'offline', or 'error'")
    response_time_ms: Optional[int] = Field(
        None,
        description="Response time in milliseconds (null if unreachable)",
        alias="responseTimeMs"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if server is unreachable",
        alias="errorMessage"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "port": 8080,
                "status": "online",
                "responseTimeMs": 45,
                "errorMessage": None
            }
        }
    )


class ExternalServerStatusResponse(BaseModel):
    """Response from external server health check."""

    are_reachable: bool = Field(
        ...,
        description="True if all enabled external servers are reachable",
        alias="areReachable"
    )
    use_external_servers: bool = Field(
        ...,
        description="True if system is configured to use external servers",
        alias="useExternalServers"
    )
    servers: List[ExternalServerItem] = Field(
        ...,
        description="Status details for each external server"
    )
    message: str = Field(..., description="Human-readable status message")
    checked_at: str = Field(
        ...,
        description="ISO 8601 timestamp when check was performed",
        alias="checkedAt"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "areReachable": True,
                "useExternalServers": True,
                "servers": [
                    {
                        "port": 8080,
                        "status": "online",
                        "responseTimeMs": 45,
                        "errorMessage": None
                    }
                ],
                "message": "All 1 external servers are online",
                "checkedAt": "2025-11-07T10:30:00Z"
            }
        }
    )
