"""Custom preset storage and management.

This module provides persistent storage for user-created custom presets.
Built-in presets are protected and cannot be modified or deleted.

Custom presets are stored in JSON format at data/custom_presets.json.

Author: Backend Architect
Phase: Code Chat Custom Presets Implementation
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.models.code_chat import ModelPreset, PRESETS

logger = logging.getLogger(__name__)

# Storage path for custom presets
CUSTOM_PRESETS_FILE = Path("data/custom_presets.json")


class PresetStore:
    """Storage manager for custom presets.

    Provides CRUD operations for user-created custom presets while
    protecting built-in presets from modification.

    Custom presets are persisted to JSON storage and automatically
    loaded on initialization.

    Thread-safety note: This implementation assumes single-process
    deployment. For multi-process deployments, consider using Redis
    or a proper database.

    Attributes:
        _custom_presets: In-memory cache of custom presets

    Example:
        >>> store = PresetStore()
        >>> all_presets = store.get_all()  # Built-in + custom
        >>> custom = store.create(ModelPreset(name="my_preset", ...))
        >>> store.update("my_preset", updated_preset)
        >>> store.delete("my_preset")
    """

    def __init__(self):
        """Initialize preset store and load custom presets from disk."""
        self._custom_presets: Dict[str, ModelPreset] = {}
        self._load()
        logger.info(
            f"PresetStore initialized with {len(self._custom_presets)} custom presets"
        )

    def _load(self) -> None:
        """Load custom presets from JSON file.

        If file doesn't exist or is invalid, starts with empty store.
        Logs errors but doesn't raise exceptions to ensure service starts.
        """
        if not CUSTOM_PRESETS_FILE.exists():
            logger.info("No custom presets file found - starting with empty store")
            return

        try:
            data = json.loads(CUSTOM_PRESETS_FILE.read_text())
            for name, preset_data in data.items():
                try:
                    # Respect is_custom from JSON, default to True for backwards compatibility
                    if "is_custom" not in preset_data:
                        preset_data["is_custom"] = True
                    preset = ModelPreset(**preset_data)
                    self._custom_presets[name] = preset
                except Exception as e:
                    logger.error(f"Failed to load custom preset '{name}': {e}")
                    continue

            logger.info(f"Loaded {len(self._custom_presets)} custom presets from disk")

        except Exception as e:
            logger.error(f"Failed to load custom presets file: {e}", exc_info=True)

    def _save(self) -> None:
        """Save custom presets to JSON file.

        Creates parent directories if needed. Logs errors but doesn't
        raise exceptions to prevent service disruption.
        """
        try:
            # Create parent directories
            CUSTOM_PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict format
            data = {
                name: preset.model_dump()
                for name, preset in self._custom_presets.items()
            }

            # Write with pretty formatting
            CUSTOM_PRESETS_FILE.write_text(json.dumps(data, indent=2))
            logger.info(f"Saved {len(self._custom_presets)} custom presets to disk")

        except Exception as e:
            logger.error(f"Failed to save custom presets: {e}", exc_info=True)

    def get_all(self) -> List[ModelPreset]:
        """Get all presets (built-in + custom).

        Returns:
            List of all available presets with built-in first, then custom

        Example:
            >>> store = PresetStore()
            >>> presets = store.get_all()
            >>> print([p.name for p in presets])
            ['speed', 'balanced', 'quality', 'coding', 'research', 'my_custom']
        """
        # Built-in presets first
        all_presets = list(PRESETS.values())

        # Then custom presets (sorted by name for consistency)
        custom_sorted = sorted(
            self._custom_presets.values(), key=lambda p: p.name.lower()
        )
        all_presets.extend(custom_sorted)

        return all_presets

    def get(self, name: str) -> Optional[ModelPreset]:
        """Get a specific preset by name.

        Checks built-in presets first, then custom presets.

        Args:
            name: Preset name to retrieve

        Returns:
            ModelPreset if found, None otherwise

        Example:
            >>> store = PresetStore()
            >>> preset = store.get("balanced")
            >>> if preset:
            ...     print(preset.description)
        """
        # Check built-in first
        if name in PRESETS:
            return PRESETS[name]

        # Then check custom
        return self._custom_presets.get(name)

    def create(self, preset: ModelPreset) -> ModelPreset:
        """Create a new custom preset.

        Args:
            preset: ModelPreset to create

        Returns:
            Created preset with isCustom=True

        Raises:
            ValueError: If preset name conflicts with built-in or existing custom

        Example:
            >>> store = PresetStore()
            >>> custom = ModelPreset(
            ...     name="fast_coding",
            ...     description="Ultra-fast code edits",
            ...     planning_tier="fast",
            ...     tool_configs={}
            ... )
            >>> created = store.create(custom)
        """
        # Validate name doesn't conflict with built-in
        if preset.name in PRESETS:
            raise ValueError(
                f"Cannot create preset '{preset.name}': "
                f"name conflicts with built-in preset"
            )

        # Validate name doesn't already exist
        if preset.name in self._custom_presets:
            raise ValueError(
                f"Cannot create preset '{preset.name}': "
                f"custom preset with this name already exists"
            )

        # Ensure isCustom flag is set
        preset.is_custom = True

        # Store in memory
        self._custom_presets[preset.name] = preset

        # Persist to disk
        self._save()

        logger.info(f"Created custom preset: {preset.name}")
        return preset

    def update(self, name: str, preset: ModelPreset) -> ModelPreset:
        """Update an existing custom preset.

        Args:
            name: Name of preset to update
            preset: Updated preset configuration

        Returns:
            Updated preset

        Raises:
            ValueError: If trying to update built-in preset or preset not found

        Example:
            >>> store = PresetStore()
            >>> updated = store.update("my_preset", modified_config)
        """
        # Cannot modify built-in presets
        if name in PRESETS:
            raise ValueError(
                f"Cannot modify built-in preset '{name}'. "
                f"Create a custom preset instead."
            )

        # Preset must exist
        if name not in self._custom_presets:
            raise ValueError(f"Custom preset '{name}' not found")

        # If renaming, check new name doesn't conflict
        if preset.name != name:
            if preset.name in PRESETS:
                raise ValueError(
                    f"Cannot rename to '{preset.name}': "
                    f"name conflicts with built-in preset"
                )
            if preset.name in self._custom_presets:
                raise ValueError(
                    f"Cannot rename to '{preset.name}': "
                    f"custom preset with this name already exists"
                )

            # Remove old name
            del self._custom_presets[name]

        # Ensure isCustom flag is set
        preset.is_custom = True

        # Update in memory
        self._custom_presets[preset.name] = preset

        # Persist to disk
        self._save()

        logger.info(f"Updated custom preset: {name} -> {preset.name}")
        return preset

    def delete(self, name: str) -> bool:
        """Delete a custom preset.

        Args:
            name: Name of preset to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete built-in preset

        Example:
            >>> store = PresetStore()
            >>> deleted = store.delete("my_preset")
            >>> print(deleted)  # True if found and deleted
        """
        # Cannot delete built-in presets
        if name in PRESETS:
            raise ValueError(
                f"Cannot delete built-in preset '{name}'. "
                f"Built-in presets are protected."
            )

        # Check if exists
        if name not in self._custom_presets:
            logger.warning(f"Attempted to delete non-existent preset: {name}")
            return False

        # Remove from memory
        del self._custom_presets[name]

        # Persist to disk
        self._save()

        logger.info(f"Deleted custom preset: {name}")
        return True

    def list_custom(self) -> List[ModelPreset]:
        """Get only custom presets.

        Returns:
            List of custom presets (sorted by name)

        Example:
            >>> store = PresetStore()
            >>> custom_only = store.list_custom()
            >>> print([p.name for p in custom_only])
            ['fast_coding', 'research_deep']
        """
        return sorted(self._custom_presets.values(), key=lambda p: p.name.lower())

    def is_custom(self, name: str) -> bool:
        """Check if a preset is custom (not built-in).

        Args:
            name: Preset name to check

        Returns:
            True if custom, False if built-in or not found

        Example:
            >>> store = PresetStore()
            >>> store.is_custom("balanced")  # False (built-in)
            >>> store.is_custom("my_preset")  # True (custom)
        """
        return name in self._custom_presets


# Global singleton instance
preset_store = PresetStore()
