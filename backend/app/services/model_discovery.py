"""
Model discovery service for automatic GGUF model detection.

This service scans HuggingFace cache directories for GGUF model files,
parses filenames using multiple regex patterns, detects model capabilities,
assigns performance tiers, and maintains a persistent model registry.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.models.discovered_model import (
    DiscoveredModel,
    ModelRegistry,
    ModelTier,
    QuantizationLevel,
)

logger = logging.getLogger(__name__)


class ModelDiscoveryService:
    """Service for discovering and cataloging GGUF models.

    Scans specified directories for GGUF files, parses filenames to extract
    metadata, assigns performance tiers based on model capabilities, and
    maintains a persistent registry.
    """

    # Pattern 1: qwen2.5-coder-14b-instruct-q4_k_m.gguf
    PATTERN_1 = re.compile(
        r"^(?P<family>[\w]+)"
        r"(?P<version>[\d.]+)?"
        r"(?:-(?P<variant>[\w-]+?))?"
        r"-(?P<size>\d+)b"
        r"(?:-(?P<suffix>instruct|chat|coder))?"
        r"-(?P<quant>q\d+_[\w]+|f\d+)"
        r"\.gguf$",
        re.IGNORECASE,
    )

    # Pattern 2: DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf or Qwen3-VL-4B-Instruct-Q4_K_M.gguf
    PATTERN_2 = re.compile(
        r"^(?P<family>[\w]+)"
        r"-(?P<variant>[\w\d]+)"
        r"(?:-(?P<version>[\d]+))?"
        r"(?:-(?P<submodel>[\w\d]+))?"
        r"-(?P<size>\d+)B"
        r"(?:-(?P<suffix>Instruct|Chat|Coder))?"
        r"-(?P<quant>Q\d+_[\w]+|F\d+)"
        r"\.gguf$"
    )

    # Pattern 3: gpt-oss-20b-Q4_K_M.gguf or Qwen3-4B-Q4_K_M.gguf (simple format)
    PATTERN_3 = re.compile(
        r"^(?P<family>[\w-]+?)"
        r"-(?P<size>\d+)[bB]"
        r"-(?P<quant>[qQfF]\d+_[\w]+|[fF]\d+)"
        r"\.gguf$",
        re.IGNORECASE,
    )

    # Keywords for detecting thinking/reasoning models
    THINKING_KEYWORDS = ["r1", "o1", "reasoning", "think"]

    def __init__(
        self,
        scan_path: Path,
        port_range: Tuple[int, int] = (8080, 8099),
        powerful_threshold: float = 14.0,
        fast_threshold: float = 7.0,
    ):
        """Initialize model discovery service.

        Args:
            scan_path: Directory path to scan for GGUF files
            port_range: Tuple of (min_port, max_port) for llama.cpp servers
            powerful_threshold: Minimum parameter count for POWERFUL tier
            fast_threshold: Maximum parameter count for FAST tier (with low quant)
        """
        self.scan_path = Path(scan_path)
        self.port_range = port_range
        self.powerful_threshold = powerful_threshold
        self.fast_threshold = fast_threshold

        logger.info(
            f"Initialized ModelDiscoveryService: "
            f"scan_path={self.scan_path}, "
            f"port_range={port_range}, "
            f"thresholds=(fast<{fast_threshold}B, powerful>={powerful_threshold}B)"
        )

    def discover_models(self) -> ModelRegistry:
        """Scan directory and discover all GGUF models.

        Recursively searches the scan path for .gguf files, parses each file
        to extract metadata, assigns ports sequentially, and creates a complete
        model registry.

        Returns:
            ModelRegistry with all discovered models

        Raises:
            FileNotFoundError: If scan_path does not exist
            PermissionError: If scan_path is not readable
        """
        if not self.scan_path.exists():
            raise FileNotFoundError(f"Scan path does not exist: {self.scan_path}")

        if not self.scan_path.is_dir():
            raise ValueError(f"Scan path is not a directory: {self.scan_path}")

        logger.info(f"Starting model discovery in: {self.scan_path}")

        # Find all GGUF files recursively
        gguf_files = list(self.scan_path.rglob("*.gguf"))
        logger.info(f"Found {len(gguf_files)} GGUF files")

        # Parse each file
        discovered_models: List[DiscoveredModel] = []
        for gguf_file in gguf_files:
            try:
                model = self._parse_model_file(gguf_file)
                if model:
                    discovered_models.append(model)
                    tier_str = (
                        model.assigned_tier
                        if isinstance(model.assigned_tier, str)
                        else model.assigned_tier.value
                    )
                    logger.info(
                        f"Parsed: {model.filename} -> {model.get_display_name()} [{tier_str}]"
                    )
                else:
                    logger.warning(f"Failed to parse: {gguf_file.name}")
            except Exception as e:
                logger.error(f"Error parsing {gguf_file.name}: {e}", exc_info=True)

        # Sort by tier (POWERFUL first), then size (descending), then quantization
        discovered_models.sort(
            key=lambda m: (
                0
                if (m.assigned_tier if isinstance(m.assigned_tier, str) else m.assigned_tier.value)
                == "powerful"
                else 1
                if (m.assigned_tier if isinstance(m.assigned_tier, str) else m.assigned_tier.value)
                == "balanced"
                else 2,
                -m.size_params,
                m.quantization if isinstance(m.quantization, str) else m.quantization.value,
            )
        )

        # Assign ports sequentially
        next_port = self.port_range[0]
        for model in discovered_models:
            model.port = next_port
            next_port += 1
            if next_port > self.port_range[1]:
                logger.warning(
                    f"Exceeded port range! Model {model.model_id} and beyond have no ports"
                )
                model.port = None

        # Create registry
        registry = ModelRegistry(
            models={model.model_id: model for model in discovered_models},
            scan_path=str(self.scan_path.absolute()),
            last_scan=datetime.utcnow().isoformat(),
            port_range=self.port_range,
            tier_thresholds={
                "powerful_min": self.powerful_threshold,
                "fast_max": self.fast_threshold,
            },
        )

        logger.info(
            f"Discovery complete: {len(discovered_models)} models registered "
            f"(FAST: {len(registry.get_by_tier(ModelTier.FAST))}, "
            f"BALANCED: {len(registry.get_by_tier(ModelTier.BALANCED))}, "
            f"POWERFUL: {len(registry.get_by_tier(ModelTier.POWERFUL))})"
        )

        return registry

    def _parse_model_file(self, file_path: Path) -> Optional[DiscoveredModel]:
        """Parse GGUF filename and extract metadata.

        Tries three regex patterns in order to extract model family, version,
        size, quantization, and other metadata from the filename.

        Args:
            file_path: Path to GGUF file

        Returns:
            DiscoveredModel if parsing succeeds, None otherwise
        """
        filename = file_path.name
        logger.debug(f"Parsing: {filename}")

        # Try each pattern in order
        for pattern_num, pattern in enumerate([self.PATTERN_1, self.PATTERN_2, self.PATTERN_3], 1):
            match = pattern.match(filename)
            if match:
                groups = match.groupdict()
                logger.debug(f"Pattern {pattern_num} matched: {groups}")

                try:
                    return self._create_model_from_match(file_path, groups)
                except Exception as e:
                    logger.error(
                        f"Failed to create model from match (pattern {pattern_num}): {e}",
                        exc_info=True,
                    )
                    return None

        logger.warning(f"No pattern matched for: {filename}")
        return None

    def _create_model_from_match(
        self, file_path: Path, groups: Dict[str, Optional[str]]
    ) -> DiscoveredModel:
        """Create DiscoveredModel from regex match groups.

        Args:
            file_path: Path to GGUF file
            groups: Regex match groups dict

        Returns:
            DiscoveredModel instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract required fields
        family_raw = groups["family"]
        if family_raw is None:
            raise ValueError("Missing family field")
        family = family_raw.lower()
        size_str = groups["size"]
        if size_str is None:
            raise ValueError("Missing size field")
        quant_raw = groups["quant"]
        if quant_raw is None:
            raise ValueError("Missing quant field")
        quant_str = quant_raw.lower()

        # Parse size (handle both "7" and "7b" formats)
        try:
            size_params = float(size_str)
        except ValueError:
            raise ValueError(f"Invalid size parameter: {size_str}")

        # Parse quantization
        try:
            quantization = QuantizationLevel(quant_str)
        except ValueError:
            # Try normalizing common variations
            normalized_quant = quant_str.replace("-", "_")
            try:
                quantization = QuantizationLevel(normalized_quant)
            except ValueError:
                raise ValueError(f"Unknown quantization level: {quant_str}")

        # Extract optional fields
        version = groups.get("version")
        suffix = groups.get("suffix", "").lower() if groups.get("suffix") else ""

        # Detect model capabilities from filename and suffix
        filename_lower = file_path.name.lower()
        is_instruct = (
            "instruct" in filename_lower
            or "chat" in filename_lower
            or suffix in ["instruct", "chat"]
        )
        is_coder = "coder" in filename_lower or suffix == "coder"
        is_thinking = self._is_thinking_model(file_path.name, groups)

        # Assign tier based on model characteristics (do this first)
        # Create a temporary model to assess tier
        temp_model = DiscoveredModel(
            file_path=str(file_path.absolute()),
            filename=file_path.name,
            family=family,
            version=version,
            size_params=size_params,
            quantization=quantization,
            is_thinking_model=is_thinking,
            is_instruct=is_instruct,
            is_coder=is_coder,
            assigned_tier=ModelTier.BALANCED,  # Placeholder for assessment
            model_id="temp",  # Temporary
            enabled=False,
        )

        assigned_tier = self._assign_tier(temp_model)

        # Extract variant information for unique ID
        variant = groups.get("variant") or groups.get("submodel")

        # Generate model ID using the assigned tier
        model_id = self._generate_model_id_from_parts(
            family=family,
            version=version,
            variant=variant,
            size_params=size_params,
            quantization=quantization,
            tier=assigned_tier,
        )

        # Create final model with proper tier and ID
        model = DiscoveredModel(
            file_path=str(file_path.absolute()),
            filename=file_path.name,
            family=family,
            version=version,
            size_params=size_params,
            quantization=quantization,
            is_thinking_model=is_thinking,
            is_instruct=is_instruct,
            is_coder=is_coder,
            assigned_tier=assigned_tier,
            model_id=model_id,
            enabled=False,
        )

        return model

    def _is_thinking_model(self, filename: str, groups: Dict[str, Optional[str]]) -> bool:
        """Detect if model is a thinking/reasoning model.

        Checks for keywords like 'r1', 'o1', 'reasoning', 'think' in the
        filename or extracted groups (case-insensitive).

        Args:
            filename: Original filename
            groups: Regex match groups

        Returns:
            True if thinking model detected, False otherwise
        """
        # Check filename
        filename_lower = filename.lower()
        for keyword in self.THINKING_KEYWORDS:
            if keyword in filename_lower:
                logger.debug(f"Detected thinking model (keyword '{keyword}'): {filename}")
                return True

        # Check variant/submodel fields
        for field in ["variant", "submodel"]:
            value = groups.get(field)
            if value and any(keyword in value.lower() for keyword in self.THINKING_KEYWORDS):
                logger.debug(f"Detected thinking model (field '{field}'): {filename}")
                return True

        return False

    def _assign_tier(self, model: DiscoveredModel) -> ModelTier:
        """Auto-assign tier based on size and capabilities.

        Tier assignment logic:
        1. Thinking models → POWERFUL (always)
        2. Size >= powerful_threshold → POWERFUL
        3. Size < fast_threshold AND low quantization → FAST
        4. Everything else → BALANCED

        Args:
            model: Model to assign tier for

        Returns:
            Assigned ModelTier
        """
        # Thinking models always go to POWERFUL tier
        if model.is_effectively_thinking():
            logger.debug(f"Assigning POWERFUL tier to thinking model: {model.filename}")
            return ModelTier.POWERFUL

        # Large models go to POWERFUL tier
        if model.size_params >= self.powerful_threshold:
            logger.debug(
                f"Assigning POWERFUL tier (size {model.size_params}B >= {self.powerful_threshold}B): "
                f"{model.filename}"
            )
            return ModelTier.POWERFUL

        # Small models with low quantization go to FAST tier
        low_quants = [
            "q2_k",
            "q2_k_s",
            "q3_k",
            "q3_k_m",
            "q3_k_s",
            "q4_0",
            "q4_k",
            "q4_k_m",
            "q4_k_s",
        ]
        # Handle both enum and string values (Pydantic may convert)
        quant_value = (
            model.quantization if isinstance(model.quantization, str) else model.quantization.value
        )
        if model.size_params < self.fast_threshold and quant_value in low_quants:
            logger.debug(
                f"Assigning FAST tier (size {model.size_params}B < {self.fast_threshold}B, "
                f"low quant {quant_value}): {model.filename}"
            )
            return ModelTier.FAST

        # Default to BALANCED
        logger.debug(f"Assigning BALANCED tier (default): {model.filename}")
        return ModelTier.BALANCED

    def _generate_model_id_from_parts(
        self,
        family: str,
        version: Optional[str],
        variant: Optional[str],
        size_params: float,
        quantization: QuantizationLevel,
        tier: ModelTier,
    ) -> str:
        """Generate unique model identifier from parts.

        Format: {family}[{variant}][{version}]_{size}b_{quant}_{tier}
        Examples:
            - deepseek_r1_8b_q4km_powerful
            - qwen3_vl_4b_q4km_fast
            - gpt_20b_q4km_powerful

        Args:
            family: Model family name
            version: Model version (optional)
            variant: Model variant (e.g., R1, VL, coder) (optional)
            size_params: Model size in billions
            quantization: Quantization level
            tier: Assigned model tier

        Returns:
            Generated model ID string
        """
        # Normalize components
        family_clean = family.replace("-", "").replace("_", "").lower()

        # Build ID parts
        id_parts = [family_clean]

        # Add variant if present (helps distinguish VL, R1, etc.)
        if variant:
            variant_clean = variant.replace("-", "").replace("_", "").lower()
            id_parts.append(variant_clean)

        # Add version if present
        if version:
            version_clean = version.replace(".", "p").replace("-", "").lower()
            id_parts.append(version_clean)

        # Get enum values explicitly (enums inherit from str, so isinstance doesn't work)
        if isinstance(quantization, QuantizationLevel):
            quant_value = quantization.value
        else:
            quant_value = str(quantization)
        quant_clean = quant_value.replace("_", "").replace("-", "").lower()

        size_clean = f"{size_params}b".replace(".", "p")

        # Get enum value explicitly
        if isinstance(tier, ModelTier):
            tier_value = tier.value
        else:
            tier_value = str(tier)

        # Join all parts with underscores
        model_id = "_".join(id_parts) + f"_{size_clean}_{quant_clean}_{tier_value}"

        return model_id

    def save_registry(self, registry: ModelRegistry, path: Path) -> None:
        """Save registry to JSON file.

        Creates parent directories if they don't exist. Writes with indentation
        for human readability.

        Args:
            registry: ModelRegistry to save
            path: Output file path

        Raises:
            IOError: If file cannot be written
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                # Convert to dict and write
                registry_dict = registry.model_dump(mode="json")
                json.dump(registry_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Registry saved to: {path.absolute()}")
        except Exception as e:
            logger.error(f"Failed to save registry to {path}: {e}", exc_info=True)
            raise IOError(f"Failed to save registry: {e}") from e

    def load_registry(self, path: Path) -> ModelRegistry:
        """Load registry from JSON file.

        Args:
            path: Input file path

        Returns:
            Loaded ModelRegistry

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If JSON is invalid or schema mismatch
        """
        if not path.exists():
            raise FileNotFoundError(f"Registry file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                registry_dict = json.load(f)

            registry = ModelRegistry(**registry_dict)
            logger.info(f"Registry loaded from: {path.absolute()} ({len(registry.models)} models)")
            return registry
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in registry file: {e}", exc_info=True)
            raise ValueError(f"Invalid JSON in registry file: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load registry from {path}: {e}", exc_info=True)
            raise ValueError(f"Failed to load registry: {e}") from e

    def rescan_and_update(self, existing_registry: ModelRegistry) -> ModelRegistry:
        """Rescan directory and update existing registry.

        Preserves user overrides (tier_override, thinking_override, enabled)
        from existing registry while updating with newly discovered models.

        Args:
            existing_registry: Current registry to update

        Returns:
            Updated ModelRegistry with preserved overrides
        """
        logger.info("Rescanning and updating existing registry")

        # Perform fresh discovery
        new_registry = self.discover_models()

        # Preserve user overrides from existing registry
        for model_id, new_model in new_registry.models.items():
            if model_id in existing_registry.models:
                old_model = existing_registry.models[model_id]

                # Preserve overrides
                new_model.tier_override = old_model.tier_override
                new_model.thinking_override = old_model.thinking_override
                new_model.enabled = old_model.enabled

                logger.debug(f"Preserved overrides for: {model_id}")

        logger.info(f"Registry updated: {len(new_registry.models)} models")
        return new_registry
