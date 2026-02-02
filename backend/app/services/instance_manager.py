"""
Instance Manager Service for Multi-Instance Model Management.

Manages model instance configurations and lifecycle, enabling multiple
instances of the same base model with different configurations.

Features:
- Instance CRUD operations with port allocation
- Integration with LlamaServerManager for server lifecycle
- Persistent registry storage to JSON
- System prompt and web search configuration per instance
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from app.models.instance import (
    InstanceConfig,
    InstanceRegistry,
    InstanceStatus,
    CreateInstanceRequest,
    UpdateInstanceRequest,
    SystemPromptPreset,
)
from app.models.discovered_model import DiscoveredModel, ModelRegistry
from app.core.exceptions import SynapseException

if TYPE_CHECKING:
    from app.services.llama_server_manager import LlamaServerManager

logger = logging.getLogger(__name__)


# Default system prompt presets
DEFAULT_PRESETS: List[SystemPromptPreset] = [
    SystemPromptPreset(
        id="concise",
        name="Concise Assistant",
        prompt="You are a concise assistant. Keep responses brief and to the point. Avoid unnecessary elaboration.",
        description="For quick, short answers",
        category="general",
    ),
    SystemPromptPreset(
        id="researcher",
        name="Research Assistant",
        prompt="You are a thorough research assistant. Provide detailed, well-sourced answers. When citing information, be specific about sources. Consider multiple perspectives.",
        description="For in-depth research queries",
        category="research",
    ),
    SystemPromptPreset(
        id="coder",
        name="Code Assistant",
        prompt="You are an expert programmer. Write clean, well-documented code. Explain your reasoning and design decisions. Follow best practices and handle edge cases.",
        description="For coding tasks",
        category="development",
    ),
    SystemPromptPreset(
        id="creative",
        name="Creative Writer",
        prompt="You are a creative writing assistant. Help with storytelling, brainstorming, and creative content. Be imaginative and engaging while maintaining coherence.",
        description="For creative writing tasks",
        category="creative",
    ),
    SystemPromptPreset(
        id="analyst",
        name="Data Analyst",
        prompt="You are a data analyst. Analyze information systematically, identify patterns, and provide data-driven insights. Be precise with numbers and statistics.",
        description="For data analysis tasks",
        category="analysis",
    ),
]


class InstanceManager:
    """Manages model instance configurations and lifecycle.

    Provides CRUD operations for instances, handles port allocation,
    and integrates with LlamaServerManager for server lifecycle.
    """

    def __init__(
        self,
        registry_path: Path,
        model_registry: ModelRegistry,
        server_manager: Optional["LlamaServerManager"] = None,
    ):
        """Initialize the instance manager.

        Args:
            registry_path: Path to instance_registry.json file
            model_registry: ModelRegistry containing base model definitions
            server_manager: Optional LlamaServerManager for server lifecycle
        """
        self.registry_path = registry_path
        self.model_registry = model_registry
        self.server_manager = server_manager
        self.registry: InstanceRegistry = self._load_registry()

        logger.info(
            f"Initialized InstanceManager with {len(self.registry.instances)} instances"
        )
        logger.info(f"  Registry path: {registry_path}")
        logger.info(f"  Port range: {self.registry.port_range}")

    def set_server_manager(self, server_manager: "LlamaServerManager") -> None:
        """Set the server manager after initialization (for dependency injection)."""
        self.server_manager = server_manager

    def _load_registry(self) -> InstanceRegistry:
        """Load instance registry from JSON file.

        Returns:
            InstanceRegistry loaded from file, or empty registry if file doesn't exist
        """
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)
                registry = InstanceRegistry.model_validate(data)
                logger.info(
                    f"Loaded instance registry with {len(registry.instances)} instances"
                )
                return registry
            except Exception as e:
                logger.error(f"Failed to load instance registry: {e}")
                logger.info("Creating new empty registry")

        # Return empty registry
        return InstanceRegistry(
            instances={},
            port_range=(8100, 8199),
            last_updated=datetime.utcnow().isoformat() + "Z",
        )

    def _save_registry(self) -> None:
        """Save instance registry to JSON file."""
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict and save
            data = self.registry.model_dump(by_alias=True)
            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(
                f"Saved instance registry with {len(self.registry.instances)} instances"
            )
        except Exception as e:
            logger.error(f"Failed to save instance registry: {e}")
            raise SynapseException(
                "Failed to save instance registry", details={"error": str(e)}
            )

    def _get_base_model(self, model_id: str) -> DiscoveredModel:
        """Get base model from model registry.

        Args:
            model_id: ID of the base model

        Returns:
            DiscoveredModel from registry

        Raises:
            SynapseException: If model not found
        """
        model = self.model_registry.models.get(model_id)
        if not model:
            raise SynapseException(
                f"Base model not found: {model_id}", details={"model_id": model_id}
            )
        return model

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_instance(self, request: CreateInstanceRequest) -> InstanceConfig:
        """Create a new instance of a base model.

        Args:
            request: CreateInstanceRequest with instance configuration

        Returns:
            Created InstanceConfig

        Raises:
            SynapseException: If model not found or no ports available
        """
        # Validate base model exists
        self._get_base_model(request.model_id)

        # Generate instance_id
        instance_num = self.registry.get_next_instance_number(request.model_id)
        instance_id = f"{request.model_id}:{instance_num:02d}"

        # Allocate port
        port = self.registry.get_available_port()
        if port is None:
            raise SynapseException(
                "No available ports for new instance",
                details={
                    "model_id": request.model_id,
                    "port_range": self.registry.port_range,
                },
            )

        # Create config
        config = InstanceConfig(
            instance_id=instance_id,
            model_id=request.model_id,
            instance_number=instance_num,
            display_name=request.display_name,
            system_prompt=request.system_prompt,
            web_search_enabled=request.web_search_enabled,
            port=port,
            status=InstanceStatus.STOPPED,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        # Add to registry and persist
        self.registry.add_instance(config)
        self._save_registry()

        logger.info(f"Created instance {instance_id} on port {port}")
        logger.info(f"  Display name: {config.display_name}")
        logger.info(f"  Web search: {config.web_search_enabled}")
        logger.info(f"  System prompt: {len(config.system_prompt or '')} chars")

        return config

    def get_instance(self, instance_id: str) -> Optional[InstanceConfig]:
        """Get instance by ID.

        Args:
            instance_id: Instance identifier

        Returns:
            InstanceConfig if found, None otherwise
        """
        return self.registry.instances.get(instance_id)

    def get_all_instances(self) -> List[InstanceConfig]:
        """Get all configured instances.

        Returns:
            List of all InstanceConfig objects
        """
        return list(self.registry.instances.values())

    def get_instances_for_model(self, model_id: str) -> List[InstanceConfig]:
        """Get all instances of a specific base model.

        Args:
            model_id: Base model identifier

        Returns:
            List of InstanceConfig for the model
        """
        return self.registry.get_instances_for_model(model_id)

    def update_instance(
        self, instance_id: str, request: UpdateInstanceRequest
    ) -> InstanceConfig:
        """Update an existing instance configuration.

        Args:
            instance_id: Instance to update
            request: UpdateInstanceRequest with new values

        Returns:
            Updated InstanceConfig

        Raises:
            SynapseException: If instance not found
        """
        config = self.registry.instances.get(instance_id)
        if not config:
            raise SynapseException(
                f"Instance not found: {instance_id}",
                details={"instance_id": instance_id},
            )

        # Update fields if provided
        if request.display_name is not None:
            config.display_name = request.display_name
        if request.system_prompt is not None:
            config.system_prompt = (
                request.system_prompt if request.system_prompt else None
            )
        if request.web_search_enabled is not None:
            config.web_search_enabled = request.web_search_enabled

        config.updated_at = datetime.utcnow().isoformat() + "Z"

        # Persist changes
        self.registry.add_instance(config)
        self._save_registry()

        logger.info(f"Updated instance {instance_id}")
        return config

    def delete_instance(self, instance_id: str) -> bool:
        """Delete an instance.

        Args:
            instance_id: Instance to delete

        Returns:
            True if deleted, False if not found

        Raises:
            SynapseException: If instance is currently running
        """
        config = self.registry.instances.get(instance_id)
        if not config:
            return False

        # Check if running
        if config.status == InstanceStatus.ACTIVE:
            raise SynapseException(
                f"Cannot delete running instance: {instance_id}",
                details={"instance_id": instance_id, "status": config.status},
            )

        # Remove from registry
        removed = self.registry.remove_instance(instance_id)
        if removed:
            self._save_registry()
            logger.info(f"Deleted instance {instance_id}")

        return removed

    # =========================================================================
    # Server Lifecycle
    # =========================================================================

    async def start_instance(self, instance_id: str) -> InstanceConfig:
        """Start an instance's llama-server.

        Args:
            instance_id: Instance to start

        Returns:
            Updated InstanceConfig with ACTIVE status

        Raises:
            SynapseException: If instance not found or server_manager not set
        """
        config = self.registry.instances.get(instance_id)
        if not config:
            raise SynapseException(
                f"Instance not found: {instance_id}",
                details={"instance_id": instance_id},
            )

        if not self.server_manager:
            raise SynapseException(
                "Server manager not configured", details={"instance_id": instance_id}
            )

        # Get base model
        model = self._get_base_model(config.model_id)

        # Create augmented model with instance port
        augmented_model = self._create_augmented_model(model, config)

        # Update status to starting
        config.status = InstanceStatus.STARTING
        self._save_registry()

        try:
            # Start server using instance_id as key
            server_process = await self.server_manager.start_server(augmented_model)

            # Store in servers dict with instance_id key
            self.server_manager.servers[instance_id] = server_process

            # Update status
            config.status = InstanceStatus.ACTIVE
            self._save_registry()

            logger.info(f"Started instance {instance_id} on port {config.port}")
            return config

        except Exception as e:
            config.status = InstanceStatus.ERROR
            self._save_registry()
            logger.error(f"Failed to start instance {instance_id}: {e}")
            raise

    async def stop_instance(self, instance_id: str) -> InstanceConfig:
        """Stop an instance's llama-server.

        Args:
            instance_id: Instance to stop

        Returns:
            Updated InstanceConfig with STOPPED status

        Raises:
            SynapseException: If instance not found
        """
        config = self.registry.instances.get(instance_id)
        if not config:
            raise SynapseException(
                f"Instance not found: {instance_id}",
                details={"instance_id": instance_id},
            )

        if not self.server_manager:
            raise SynapseException(
                "Server manager not configured", details={"instance_id": instance_id}
            )

        # Update status to stopping
        config.status = InstanceStatus.STOPPING
        self._save_registry()

        try:
            # Get base model for stop operation
            model = self._get_base_model(config.model_id)
            augmented_model = self._create_augmented_model(model, config)

            # Stop server
            await self.server_manager.stop_server(augmented_model)

            # Remove from servers dict
            if instance_id in self.server_manager.servers:
                del self.server_manager.servers[instance_id]

            # Update status
            config.status = InstanceStatus.STOPPED
            self._save_registry()

            logger.info(f"Stopped instance {instance_id}")
            return config

        except Exception as e:
            config.status = InstanceStatus.ERROR
            self._save_registry()
            logger.error(f"Failed to stop instance {instance_id}: {e}")
            raise

    def get_instance_status(self, instance_id: str) -> Dict:
        """Get detailed status for an instance.

        Args:
            instance_id: Instance to check

        Returns:
            Dictionary with status details
        """
        config = self.registry.instances.get(instance_id)
        if not config:
            return {"error": "Instance not found"}

        status = {
            "instance_id": instance_id,
            "display_name": config.display_name,
            "status": config.status,
            "port": config.port,
            "model_id": config.model_id,
            "web_search_enabled": config.web_search_enabled,
            "has_system_prompt": config.system_prompt is not None,
        }

        # Add server process info if available
        if self.server_manager and instance_id in self.server_manager.servers:
            server = self.server_manager.servers[instance_id]
            status.update(
                {
                    "is_ready": server.is_ready,
                    "is_running": server.is_running(),
                    "uptime_seconds": server.get_uptime_seconds(),
                }
            )

        return status

    def _create_augmented_model(
        self, model: DiscoveredModel, config: InstanceConfig
    ) -> DiscoveredModel:
        """Create a copy of the model with instance-specific settings.

        Args:
            model: Base DiscoveredModel
            config: InstanceConfig with instance settings

        Returns:
            New DiscoveredModel with instance port and model_id
        """
        # Create a copy with instance port
        augmented = model.model_copy()
        augmented.port = config.port
        # Use instance_id as model_id for server manager tracking
        augmented.model_id = config.instance_id
        return augmented

    # =========================================================================
    # System Prompt Presets
    # =========================================================================

    def get_system_prompt_presets(self) -> List[SystemPromptPreset]:
        """Get available system prompt presets.

        Returns:
            List of SystemPromptPreset objects
        """
        return DEFAULT_PRESETS

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_instance_counts_by_model(self) -> Dict[str, int]:
        """Get count of instances per base model.

        Returns:
            Dictionary mapping model_id to instance count
        """
        counts: Dict[str, int] = {}
        for config in self.registry.instances.values():
            counts[config.model_id] = counts.get(config.model_id, 0) + 1
        return counts

    def get_active_instances(self) -> List[InstanceConfig]:
        """Get all instances with ACTIVE status.

        Returns:
            List of active InstanceConfig objects
        """
        return self.registry.get_active_instances()

    def get_instances_with_web_search(self) -> List[InstanceConfig]:
        """Get all instances with web search enabled.

        Returns:
            List of InstanceConfig with web_search_enabled=True
        """
        return [
            inst for inst in self.registry.instances.values() if inst.web_search_enabled
        ]


# Global instance manager (initialized in main.py)
instance_manager: Optional[InstanceManager] = None


def get_instance_manager() -> InstanceManager:
    """Get the global instance manager.

    Returns:
        InstanceManager instance

    Raises:
        SynapseException: If not initialized
    """
    if instance_manager is None:
        raise SynapseException("Instance manager not initialized")
    return instance_manager


def init_instance_manager(
    registry_path: Path,
    model_registry: ModelRegistry,
    server_manager: Optional["LlamaServerManager"] = None,
) -> InstanceManager:
    """Initialize the global instance manager.

    Args:
        registry_path: Path to instance_registry.json
        model_registry: ModelRegistry with base models
        server_manager: Optional LlamaServerManager

    Returns:
        Initialized InstanceManager
    """
    global instance_manager
    instance_manager = InstanceManager(registry_path, model_registry, server_manager)
    return instance_manager
