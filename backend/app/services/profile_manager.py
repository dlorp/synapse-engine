"""Profile management service for S.Y.N.A.P.S.E. ENGINE model configuration.

This module provides the ProfileManager service for loading, saving, validating,
and managing model configuration profiles from YAML files.
"""

import logging
from pathlib import Path
from typing import List
import yaml

from app.models.profile import ModelProfile
from app.core.exceptions import SynapseException

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages loading and validation of model profiles.

    The ProfileManager handles loading profile YAML files, validating them against
    the model registry, and providing CRUD operations for profiles.
    """

    def __init__(self, profiles_dir: Path = Path("config/profiles")):
        """Initialize profile manager.

        Args:
            profiles_dir: Directory containing profile YAML files
        """
        self.profiles_dir = Path(profiles_dir)
        logger.info(f"ProfileManager initialized with directory: {self.profiles_dir}")

    def list_profiles(self) -> List[str]:
        """List available profile names.

        Returns:
            List of profile names (without .yaml extension)
        """
        if not self.profiles_dir.exists():
            logger.warning(f"Profiles directory does not exist: {self.profiles_dir}")
            return []

        profiles = []
        for yaml_file in self.profiles_dir.glob("*.yaml"):
            profiles.append(yaml_file.stem)

        logger.info(f"Found {len(profiles)} profiles: {profiles}")
        return sorted(profiles)

    def load_profile(self, name: str) -> ModelProfile:
        """Load a profile by name.

        Args:
            name: Profile name (without .yaml extension)

        Returns:
            ModelProfile instance

        Raises:
            SynapseException: If profile not found or invalid
        """
        profile_path = self.profiles_dir / f"{name}.yaml"

        if not profile_path.exists():
            raise SynapseException(
                f"Profile '{name}' not found",
                details={
                    "path": str(profile_path),
                    "available_profiles": self.list_profiles()
                },
                status_code=404
            )

        try:
            with open(profile_path, 'r') as f:
                data = yaml.safe_load(f)

            # Support both flat and nested structures
            if 'profile' in data:
                # Nested: profile key + other keys
                profile_data = {**data['profile'], **{k: v for k, v in data.items() if k != 'profile'}}
            else:
                # Flat: all keys at root
                profile_data = data

            profile = ModelProfile(**profile_data)
            logger.info(f"Loaded profile '{name}' with {len(profile.enabled_models)} enabled models")
            return profile

        except Exception as e:
            logger.error(f"Failed to load profile '{name}': {e}", exc_info=True)
            raise SynapseException(
                f"Failed to load profile '{name}': {e}",
                details={"path": str(profile_path), "error": str(e)},
                status_code=500
            )

    def save_profile(self, profile: ModelProfile) -> Path:
        """Save a profile to disk.

        Args:
            profile: ModelProfile instance to save

        Returns:
            Path to saved profile file
        """
        # Ensure directory exists
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from profile name
        filename = profile.name.lower().replace(' ', '-').replace('_', '-')
        profile_path = self.profiles_dir / f"{filename}.yaml"

        # Convert to dict
        data = {
            'profile': {
                'name': profile.name,
                'description': profile.description
            },
            'enabled_models': profile.enabled_models,
            'tier_config': [t.model_dump() for t in profile.tier_config],
            'two_stage': profile.two_stage.model_dump(),
            'load_balancing': profile.load_balancing.model_dump()
        }

        # Write to YAML
        with open(profile_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved profile '{profile.name}' to {profile_path}")
        return profile_path

    def delete_profile(self, name: str) -> None:
        """Delete a profile.

        Args:
            name: Profile name to delete

        Raises:
            SynapseException: If profile not found
        """
        profile_path = self.profiles_dir / f"{name}.yaml"

        if not profile_path.exists():
            raise SynapseException(
                f"Profile '{name}' not found",
                details={"path": str(profile_path)},
                status_code=404
            )

        profile_path.unlink()
        logger.info(f"Deleted profile '{name}'")

    def validate_profile(self, profile: ModelProfile, available_model_ids: List[str]) -> List[str]:
        """Validate that all enabled models exist in registry.

        Args:
            profile: Profile to validate
            available_model_ids: List of valid model IDs from registry

        Returns:
            List of missing model IDs (empty if valid)
        """
        missing = []
        for model_id in profile.enabled_models:
            if model_id not in available_model_ids:
                missing.append(model_id)

        if missing:
            logger.warning(
                f"Profile '{profile.name}' references {len(missing)} missing models: {missing}"
            )

        return missing
