"""
Data models for discovered GGUF models and model registry.

This module defines the core data structures for the S.Y.N.A.P.S.E. ENGINE model discovery system,
including quantization levels, model tiers, discovered model metadata, and the
centralized model registry.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuantizationLevel(str, Enum):
    """Supported GGUF quantization levels.

    Ordered from lowest to highest precision/size.
    """
    Q2_K = "q2_k"
    Q2_K_S = "q2_k_s"
    Q3_K = "q3_k"
    Q3_K_M = "q3_k_m"
    Q3_K_S = "q3_k_s"
    Q4_0 = "q4_0"
    Q4_K = "q4_k"
    Q4_K_M = "q4_k_m"
    Q4_K_S = "q4_k_s"
    Q5_0 = "q5_0"
    Q5_K = "q5_k"
    Q5_K_M = "q5_k_m"
    Q5_K_S = "q5_k_s"
    Q6_K = "q6_k"
    Q8_0 = "q8_0"
    F16 = "f16"
    F32 = "f32"


class ModelTier(str, Enum):
    """Model performance tiers for query routing.

    FAST: Low-precision models for simple queries (<2s target)
    BALANCED: Medium-precision models for moderate queries (<5s target)
    POWERFUL: High-precision/reasoning models for complex queries (<15s target)
    """
    FAST = "fast"
    BALANCED = "balanced"
    POWERFUL = "powerful"


class DiscoveredModel(BaseModel):
    """Metadata for a discovered GGUF model.

    Represents a single GGUF model file found during directory scanning,
    with parsed metadata, auto-assigned tier, and configuration state.
    """

    # File information
    file_path: str = Field(description="Absolute path to GGUF file", alias="filePath")
    filename: str = Field(description="Base filename without path")

    # Model identity
    family: str = Field(description="Model family (qwen, deepseek, llama, etc.)")
    version: Optional[str] = Field(default=None, description="Model version (2.5, 3, etc.)")
    size_params: float = Field(description="Model size in billions of parameters", alias="sizeParams")
    quantization: QuantizationLevel = Field(description="Quantization level")

    # Capabilities
    is_thinking_model: bool = Field(
        default=False,
        description="Auto-detected reasoning/thinking model (r1, o1, etc.)",
        alias="isThinkingModel"
    )
    thinking_override: Optional[bool] = Field(
        default=None,
        description="User override for thinking model status",
        alias="thinkingOverride"
    )
    is_instruct: bool = Field(default=False, description="Instruction-tuned model", alias="isInstruct")
    is_coder: bool = Field(default=False, description="Code-specialized model", alias="isCoder")

    # Tier assignment
    assigned_tier: ModelTier = Field(description="Auto-assigned performance tier", alias="assignedTier")
    tier_override: Optional[ModelTier] = Field(
        default=None,
        description="User override for tier assignment",
        alias="tierOverride"
    )

    # Runtime configuration
    port: Optional[int] = Field(default=None, description="Assigned llama.cpp server port")
    enabled: bool = Field(default=False, description="Whether model is enabled for use")

    # Per-model runtime overrides (Phase 2)
    # If None, uses global runtime settings; if set, overrides global value
    n_gpu_layers: Optional[int] = Field(
        default=None,
        ge=0,
        le=999,
        description="Per-model GPU layers override (None = use global setting)",
        alias="nGpuLayers"
    )
    ctx_size: Optional[int] = Field(
        default=None,
        ge=512,
        le=131072,
        description="Per-model context size override (None = use global setting)",
        alias="ctxSize"
    )
    n_threads: Optional[int] = Field(
        default=None,
        ge=1,
        le=128,
        description="Per-model thread count override (None = use global setting)",
        alias="nThreads"
    )
    batch_size: Optional[int] = Field(
        default=None,
        ge=1,
        le=4096,
        description="Per-model batch size override (None = use global setting)",
        alias="batchSize"
    )

    # Generated identifier
    model_id: str = Field(description="Generated unique identifier", alias="modelId")

    def get_display_name(self) -> str:
        """Generate human-readable display name.

        Returns:
            Formatted display name (e.g., "DEEPSEEK R1 8.0B Q4_K_M")
        """
        parts = [self.family.upper().replace("-", " ")]

        if self.version:
            parts.append(self.version)

        parts.append(f"{self.size_params}B")

        # Add capability flags
        if self.is_effectively_thinking():
            parts.append("(Reasoning)")
        elif self.is_coder:
            parts.append("(Coder)")
        elif self.is_instruct:
            parts.append("(Instruct)")

        # Handle both enum and string values (Pydantic may convert)
        quant_str = self.quantization if isinstance(self.quantization, str) else self.quantization.value
        parts.append(quant_str.upper())

        return " ".join(parts)

    def get_effective_tier(self) -> ModelTier:
        """Get effective tier considering user override.

        Returns:
            ModelTier: Override if set, otherwise assigned tier
        """
        return self.tier_override or self.assigned_tier

    def is_effectively_thinking(self) -> bool:
        """Get effective thinking status considering user override.

        Returns:
            bool: Override if set, otherwise auto-detected status
        """
        return (
            self.thinking_override
            if self.thinking_override is not None
            else self.is_thinking_model
        )

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True  # Accept both snake_case and camelCase
    )


class ModelRegistry(BaseModel):
    """Centralized registry of discovered models.

    Maintains the complete set of discovered models with their configuration,
    tier assignments, and runtime state. Supports persistence to JSON.
    """

    models: Dict[str, DiscoveredModel] = Field(
        default_factory=dict,
        description="Map of model_id to DiscoveredModel"
    )
    scan_path: str = Field(description="Directory path that was scanned", alias="scanPath")
    last_scan: str = Field(description="ISO timestamp of last scan", alias="lastScan")
    port_range: Tuple[int, int] = Field(
        default=(8080, 8099),
        description="Available port range for llama.cpp servers",
        alias="portRange"
    )
    tier_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "powerful_min": 14.0,  # 14B+ parameters for POWERFUL tier
            "fast_max": 7.0        # <7B parameters for FAST tier (with low quant)
        },
        description="Parameter count thresholds for tier assignment",
        alias="tierThresholds"
    )

    def get_by_tier(self, tier: ModelTier) -> List[DiscoveredModel]:
        """Get all models in a specific tier (considering overrides).

        Args:
            tier: Target tier to filter by

        Returns:
            List of models with effective tier matching target
        """
        return [
            model
            for model in self.models.values()
            if model.get_effective_tier() == tier
        ]

    def get_enabled_models(self) -> List[DiscoveredModel]:
        """Get all enabled models.

        Returns:
            List of models with enabled=True
        """
        return [model for model in self.models.values() if model.enabled]

    def get_by_port(self, port: int) -> Optional[DiscoveredModel]:
        """Get model assigned to specific port.

        Args:
            port: Port number to search for

        Returns:
            Model assigned to port, or None if not found
        """
        return next(
            (model for model in self.models.values() if model.port == port),
            None
        )

    def get_available_ports(self) -> List[int]:
        """Get list of unassigned ports in range.

        Returns:
            List of port numbers not currently assigned
        """
        assigned_ports = {
            model.port
            for model in self.models.values()
            if model.port is not None
        }
        return [
            port
            for port in range(self.port_range[0], self.port_range[1] + 1)
            if port not in assigned_ports
        ]

    def add_model(self, model: DiscoveredModel) -> None:
        """Add or update model in registry.

        Args:
            model: DiscoveredModel to add/update
        """
        self.models[model.model_id] = model

    def remove_model(self, model_id: str) -> bool:
        """Remove model from registry.

        Args:
            model_id: ID of model to remove

        Returns:
            True if model was removed, False if not found
        """
        if model_id in self.models:
            del self.models[model_id]
            return True
        return False

    def update_last_scan(self) -> None:
        """Update last_scan timestamp to current time."""
        self.last_scan = datetime.utcnow().isoformat()

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True  # Accept both snake_case and camelCase
    )
