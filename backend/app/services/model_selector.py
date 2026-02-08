"""Registry-based model selection service.

This module provides model selection functionality using the new
ModelRegistry system instead of the legacy ModelManager config-based approach.

It integrates with LlamaServerManager to check which models are actually
running and available for queries.
"""

import logging
from collections import defaultdict
from typing import List, Optional

from app.core.exceptions import NoModelsAvailableError
from app.models.discovered_model import DiscoveredModel, ModelRegistry, ModelTier
from app.services.llama_server_manager import LlamaServerManager

logger = logging.getLogger(__name__)


class ModelSelector:
    """Select models from registry based on tier and availability.

    This class bridges the registry (which knows about enabled models) and
    the server manager (which knows about running servers) to provide
    intelligent model selection for query routing.

    Attributes:
        registry: Model registry with all discovered models
        server_manager: Server manager tracking running servers
        request_counts: Load balancing counter per model
    """

    def __init__(self, registry: ModelRegistry, server_manager: LlamaServerManager):
        """Initialize model selector.

        Args:
            registry: ModelRegistry instance
            server_manager: LlamaServerManager instance
        """
        self.registry = registry
        self.server_manager = server_manager
        self._request_counts: dict[str, int] = defaultdict(int)

        logger.info(
            "ModelSelector initialized",
            extra={
                "total_models": len(registry.models),
                "enabled_models": len([m for m in registry.models.values() if m.enabled]),
            },
        )

    def is_model_available(self, model: DiscoveredModel) -> bool:
        """Check if a model is available for queries.

        A model is available if:
        1. It's enabled in the registry
        2. Its server is running (according to server_manager)

        Args:
            model: DiscoveredModel to check

        Returns:
            True if model is available, False otherwise
        """
        if not model.enabled:
            return False

        # Check if server is running
        return self.server_manager.is_server_running(model.model_id)

    async def select_model(self, tier: str) -> DiscoveredModel:
        """Select best available model for the specified tier.

        Implements round-robin load balancing across multiple models in the same tier.

        Args:
            tier: Model tier (fast, balanced, or powerful)

        Returns:
            DiscoveredModel instance of the selected model

        Raises:
            NoModelsAvailableError: If no available models in the requested tier

        Example:
            >>> selector = ModelSelector(registry, server_manager)
            >>> model = await selector.select_model("fast")
            >>> print(f"Selected: {model.model_id}")
        """
        # Convert tier string to enum
        try:
            tier_enum = ModelTier(tier)
        except ValueError:
            logger.error(f"Invalid tier: {tier}")
            raise NoModelsAvailableError(
                tier=tier, details={"valid_tiers": ["fast", "balanced", "powerful"]}
            )

        # Get all models in the requested tier
        tier_models = self.registry.get_by_tier(tier_enum)

        # Filter to only available (enabled AND running) models
        available_models = [model for model in tier_models if self.is_model_available(model)]

        if not available_models:
            # Find which tiers DO have available models
            available_tiers = set()
            for check_tier in [ModelTier.FAST, ModelTier.BALANCED, ModelTier.POWERFUL]:
                check_tier_models = self.registry.get_by_tier(check_tier)
                if any(self.is_model_available(m) for m in check_tier_models):
                    available_tiers.add(check_tier.value)

            logger.error(
                f"No available models in tier {tier}",
                extra={
                    "tier": tier,
                    "tier_total_models": len(tier_models),
                    "tier_enabled_models": len([m for m in tier_models if m.enabled]),
                    "tier_running_models": len(available_models),
                    "available_tiers": list(available_tiers),
                },
            )

            raise NoModelsAvailableError(
                tier=tier,
                details={
                    "available_tiers": list(available_tiers),
                    "tier_total_models": len(tier_models),
                    "tier_enabled_models": len([m for m in tier_models if m.enabled]),
                },
            )

        # For single model, return it
        if len(available_models) == 1:
            selected = available_models[0]
            self._request_counts[selected.model_id] += 1
            logger.debug(
                f"Selected only model in tier {tier}: {selected.model_id}",
                extra={"tier": tier, "model_id": selected.model_id},
            )
            return selected

        # For multiple models, use round-robin based on request counts
        selected = min(available_models, key=lambda m: self._request_counts[m.model_id])

        self._request_counts[selected.model_id] += 1

        logger.debug(
            f"Selected model {selected.model_id} for tier {tier} (round-robin)",
            extra={
                "tier": tier,
                "model_id": selected.model_id,
                "request_counts": {
                    m.model_id: self._request_counts[m.model_id] for m in available_models
                },
            },
        )

        return selected

    def get_available_models(self) -> List[DiscoveredModel]:
        """Get list of all available (enabled AND running) models.

        Returns:
            List of DiscoveredModel instances that are available
        """
        return [model for model in self.registry.models.values() if self.is_model_available(model)]

    def get_available_count(self, tier: Optional[str] = None) -> int:
        """Get count of available models, optionally filtered by tier.

        Args:
            tier: Optional tier filter (fast, balanced, powerful)

        Returns:
            Number of available models
        """
        if tier:
            try:
                tier_enum = ModelTier(tier)
                tier_models = self.registry.get_by_tier(tier_enum)
                return len([m for m in tier_models if self.is_model_available(m)])
            except ValueError:
                return 0
        else:
            return len(self.get_available_models())
