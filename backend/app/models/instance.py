"""
Model instance configuration and registry for multi-instance management.

Extends DiscoveredModel with instance-specific configuration including
system prompts, web search capability, and unique instance identity.

Enables running multiple instances of the same base model with different
configurations (e.g., different personas, capabilities).
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class InstanceStatus(str, Enum):
    """Runtime status of a model instance."""
    STOPPED = "stopped"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    ERROR = "error"


class InstanceConfig(BaseModel):
    """Configuration for a single model instance.

    Represents a running or configured instance of a base model,
    with instance-specific settings like system prompt and web search.
    """

    # Identity
    instance_id: str = Field(
        description="Unique instance identifier (model_id:NN format)",
        alias="instanceId"
    )
    model_id: str = Field(
        description="Reference to base DiscoveredModel",
        alias="modelId"
    )
    instance_number: int = Field(
        ge=1, le=99,
        description="Instance number (01-99)",
        alias="instanceNumber"
    )

    # User-configurable settings
    display_name: str = Field(
        max_length=64,
        description="User-friendly name for this instance",
        alias="displayName"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        max_length=4096,
        description="System prompt injected at query time",
        alias="systemPrompt"
    )
    web_search_enabled: bool = Field(
        default=False,
        description="Enable SearXNG web search for this instance",
        alias="webSearchEnabled"
    )

    # Runtime configuration
    port: int = Field(
        ge=1024, le=65535,
        description="Assigned port for this instance"
    )

    # Status tracking (not persisted, computed at runtime)
    status: InstanceStatus = Field(
        default=InstanceStatus.STOPPED,
        description="Current runtime status"
    )

    # Metadata
    created_at: str = Field(
        description="ISO timestamp of instance creation",
        alias="createdAt"
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last update",
        alias="updatedAt"
    )

    @field_validator('system_prompt')
    @classmethod
    def sanitize_system_prompt(cls, v: Optional[str]) -> Optional[str]:
        """Remove control characters and null bytes from system prompt."""
        if v is None:
            return None
        # Remove null bytes
        v = v.replace('\x00', '')
        # Remove control characters except newlines/tabs
        v = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', v)
        return v.strip() if v.strip() else None

    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """Ensure display name is safe and non-empty."""
        v = v.strip()
        if not v:
            raise ValueError("Display name cannot be empty")
        # Remove any HTML-like tags for safety
        v = re.sub(r'<[^>]+>', '', v)
        return v

    @field_validator('instance_id')
    @classmethod
    def validate_instance_id(cls, v: str) -> str:
        """Validate instance_id format (model_id:NN)."""
        if not re.match(r'^[a-z0-9_]+:\d{2}$', v):
            raise ValueError("Instance ID must be in format 'model_id:NN'")
        return v

    def get_full_name(self) -> str:
        """Get formatted instance name for display."""
        return f"{self.display_name} [{self.instance_id}]"

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True
    )


class InstanceRegistry(BaseModel):
    """Registry of all configured model instances.

    Persisted to JSON and loaded at startup. Tracks all instances
    across all models with their configurations.
    """

    instances: Dict[str, InstanceConfig] = Field(
        default_factory=dict,
        description="Map of instance_id to InstanceConfig"
    )

    # Port management
    port_range: Tuple[int, int] = Field(
        default=(8100, 8199),
        description="Port range reserved for instances",
        alias="portRange"
    )

    # Metadata
    last_updated: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO timestamp of last registry update",
        alias="lastUpdated"
    )

    def get_instances_for_model(self, model_id: str) -> List[InstanceConfig]:
        """Get all instances of a specific base model."""
        return [
            inst for inst in self.instances.values()
            if inst.model_id == model_id
        ]

    def get_next_instance_number(self, model_id: str) -> int:
        """Get the next available instance number for a model."""
        existing = self.get_instances_for_model(model_id)
        if not existing:
            return 1
        max_num = max(inst.instance_number for inst in existing)
        return min(max_num + 1, 99)

    def get_available_port(self) -> Optional[int]:
        """Get next available port in the instance range."""
        used_ports = {inst.port for inst in self.instances.values()}
        for port in range(self.port_range[0], self.port_range[1] + 1):
            if port not in used_ports:
                return port
        return None

    def add_instance(self, instance: InstanceConfig) -> None:
        """Add or update an instance in the registry."""
        self.instances[instance.instance_id] = instance
        self.last_updated = datetime.utcnow().isoformat() + "Z"

    def remove_instance(self, instance_id: str) -> bool:
        """Remove an instance from the registry."""
        if instance_id in self.instances:
            del self.instances[instance_id]
            self.last_updated = datetime.utcnow().isoformat() + "Z"
            return True
        return False

    def get_active_instances(self) -> List[InstanceConfig]:
        """Get all instances with ACTIVE status."""
        return [
            inst for inst in self.instances.values()
            if inst.status == InstanceStatus.ACTIVE
        ]

    def get_instances_by_status(self, status: InstanceStatus) -> List[InstanceConfig]:
        """Get instances filtered by status."""
        return [
            inst for inst in self.instances.values()
            if inst.status == status
        ]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True
    )


class CreateInstanceRequest(BaseModel):
    """Request to create a new model instance."""

    model_id: str = Field(alias="modelId")
    display_name: str = Field(max_length=64, alias="displayName")
    system_prompt: Optional[str] = Field(
        default=None, max_length=4096, alias="systemPrompt"
    )
    web_search_enabled: bool = Field(default=False, alias="webSearchEnabled")

    model_config = ConfigDict(populate_by_name=True)


class UpdateInstanceRequest(BaseModel):
    """Request to update an existing instance."""

    display_name: Optional[str] = Field(
        default=None, max_length=64, alias="displayName"
    )
    system_prompt: Optional[str] = Field(
        default=None, max_length=4096, alias="systemPrompt"
    )
    web_search_enabled: Optional[bool] = Field(
        default=None, alias="webSearchEnabled"
    )

    model_config = ConfigDict(populate_by_name=True)


class InstanceResponse(BaseModel):
    """Response containing instance details."""

    instance: InstanceConfig
    model_display_name: str = Field(alias="modelDisplayName")
    model_tier: str = Field(alias="modelTier")

    model_config = ConfigDict(populate_by_name=True)


class InstanceListResponse(BaseModel):
    """Response containing list of instances."""

    instances: List[InstanceConfig]
    total: int
    by_model: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of instances per model_id",
        alias="byModel"
    )

    model_config = ConfigDict(populate_by_name=True)


class SystemPromptPreset(BaseModel):
    """Predefined system prompt template."""

    id: str
    name: str
    prompt: str
    description: str
    category: str = Field(default="general")

    model_config = ConfigDict(populate_by_name=True)


class SystemPromptPresetsResponse(BaseModel):
    """Response containing available system prompt presets."""

    presets: List[SystemPromptPreset]

    model_config = ConfigDict(populate_by_name=True)
