"""Application startup service.

Orchestrates the PRAXIS startup sequence:
1. Discover models (or load cached registry)
2. Load profile from PRAXIS_PROFILE env var
3. Filter to enabled models
4. Launch llama.cpp servers for enabled models
5. Health check all servers

This service replaces manual configuration with automated,
profile-based model management.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.services.model_discovery import ModelDiscoveryService
from app.services.llama_server_manager import LlamaServerManager
from app.services.profile_manager import ProfileManager
from app.models.discovered_model import ModelRegistry, DiscoveredModel
from app.models.profile import ModelProfile
from app.models.config import AppConfig
from app.core.exceptions import SynapseException

logger = logging.getLogger(__name__)


class StartupService:
    """Orchestrates PRAXIS startup sequence."""

    def __init__(
        self,
        config: AppConfig,
        profile_name: Optional[str] = None
    ):
        """Initialize startup service.

        Args:
            config: Application configuration
            profile_name: Profile to load (defaults to 'development')
        """
        self.config = config
        self.profile_name = profile_name or os.getenv("PRAXIS_PROFILE", "development")

        # Services (initialized during startup)
        self.discovery_service: Optional[ModelDiscoveryService] = None
        self.server_manager: Optional[LlamaServerManager] = None

        # Initialize ProfileManager with correct path
        # Profiles are at project_root/config/profiles
        # __file__ is /app/app/services/startup.py in Docker, need to go up 3 levels to /app
        project_root = Path(__file__).parent.parent.parent
        profiles_dir = project_root / "config" / "profiles"
        self.profile_manager: ProfileManager = ProfileManager(profiles_dir=profiles_dir)

        # State
        self.registry: Optional[ModelRegistry] = None
        self.profile: Optional[ModelProfile] = None
        self.enabled_models: List[DiscoveredModel] = []

        logger.info(f"StartupService initialized with profile: {self.profile_name}")

    async def initialize(self) -> ModelRegistry:
        """Run complete startup sequence.

        Returns:
            ModelRegistry with discovered and configured models

        Raises:
            SynapseException: If startup fails
        """
        logger.info("=" * 70)
        logger.info("PRAXIS STARTUP SEQUENCE")
        logger.info("=" * 70)
        logger.info(f"Profile: {self.profile_name}")
        logger.info(f"Time: {datetime.now().isoformat()}")
        logger.info("=" * 70)

        try:
            # Step 1: Discover/load models
            logger.info("[1/5] Model Discovery")
            self.registry = await self._discover_models()
            logger.info(f"✅ Discovered {len(self.registry.models)} models")

            # Step 2: Load profile
            logger.info(f"[2/5] Loading profile '{self.profile_name}'")
            self.profile = self._load_profile()
            logger.info(f"✅ Profile loaded: {self.profile.description}")

            # Step 3: Filter enabled models
            logger.info("[3/5] Filtering enabled models")
            self.enabled_models = self._filter_enabled_models()
            logger.info(f"✅ {len(self.enabled_models)} models enabled")

            # Step 4: Launch servers
            logger.info(f"[4/5] Launching servers")
            await self._launch_servers()
            logger.info(f"✅ Servers launched")

            # Step 5: Health check
            logger.info("[5/5] Health check")
            health_status = await self._health_check()
            logger.info(f"✅ Health check complete")

            # Summary
            logger.info("=" * 70)
            logger.info("PRAXIS STARTUP COMPLETE")
            logger.info(f"  Profile: {self.profile.name}")
            logger.info(f"  Models discovered: {len(self.registry.models)}")
            logger.info(f"  Models enabled: {len(self.enabled_models)}")
            logger.info(f"  Servers launched: {health_status['total_servers']}")
            logger.info(f"  Servers ready: {health_status['ready_servers']}")
            logger.info("=" * 70)

            return self.registry

        except Exception as e:
            logger.error(f"❌ STARTUP FAILED: {e}", exc_info=True)
            raise SynapseException(
                f"PRAXIS startup failed: {e}",
                details={"phase": "startup", "profile": self.profile_name}
            )

    async def _discover_models(self) -> ModelRegistry:
        """Discover or load model registry.

        Returns:
            ModelRegistry instance
        """
        # Get paths from environment or config
        scan_path = Path(os.getenv(
            "MODEL_SCAN_PATH",
            "${PRAXIS_MODEL_PATH}/"
        ))
        registry_path = Path(os.getenv(
            "REGISTRY_PATH",
            "data/model_registry.json"
        ))

        # Initialize discovery service
        self.discovery_service = ModelDiscoveryService(
            scan_path=scan_path,
            port_range=(8080, 8099)
        )

        # Load cached registry or discover
        if registry_path.exists():
            logger.info(f"Loading cached registry: {registry_path}")
            try:
                registry = self.discovery_service.load_registry(registry_path)
                logger.info(f"Loaded {len(registry.models)} models from cache")
                return registry
            except Exception as e:
                logger.warning(f"Failed to load cached registry: {e}")
                logger.info("Falling back to fresh discovery")

        # Fresh discovery
        if not scan_path.exists():
            logger.warning(f"Scan path does not exist: {scan_path}")
            logger.warning("Creating empty registry")
            return ModelRegistry(
                models={},
                scan_path=str(scan_path),
                last_scan=datetime.now().isoformat()
            )

        logger.info(f"Discovering models in: {scan_path}")
        registry = self.discovery_service.discover_models()

        # Save for next time
        self.discovery_service.save_registry(registry, registry_path)
        logger.info(f"Saved registry to: {registry_path}")

        return registry

    def _load_profile(self) -> ModelProfile:
        """Load profile from profile manager.

        Returns:
            ModelProfile instance

        Raises:
            SynapseException: If profile not found
        """
        try:
            profile = self.profile_manager.load_profile(self.profile_name)

            # Validate profile against registry
            if self.registry:
                missing = self.profile_manager.validate_profile(
                    profile,
                    list(self.registry.models.keys())
                )
                if missing:
                    logger.warning(
                        f"Profile references {len(missing)} missing models: {missing}"
                    )

            return profile

        except Exception as e:
            logger.error(f"Failed to load profile '{self.profile_name}': {e}")
            raise

    def _filter_enabled_models(self) -> List[DiscoveredModel]:
        """Filter to enabled models from profile.

        Returns:
            List of enabled DiscoveredModel instances
        """
        enabled = []

        if not self.profile or not self.registry:
            logger.warning("No profile or registry available")
            return enabled

        for model_id in self.profile.enabled_models:
            if model_id in self.registry.models:
                model = self.registry.models[model_id]
                model.enabled = True  # Mark as enabled
                enabled.append(model)
                logger.info(f"  ✅ {model.get_display_name()}")
            else:
                logger.warning(f"  ⚠️  Model not found: {model_id}")

        return enabled

    async def _launch_servers(self) -> None:
        """Launch llama.cpp servers for enabled models."""
        if not self.enabled_models:
            logger.warning("No enabled models. Skipping server launch.")
            return

        # Get llama-server path
        llama_server_path = Path(os.getenv(
            "LLAMA_SERVER_PATH",
            "/usr/local/bin/llama-server"
        ))

        # Check for external server mode (Metal acceleration on macOS)
        use_external_servers_env = os.getenv("USE_EXTERNAL_SERVERS", "false")
        use_external_servers = use_external_servers_env.lower() == "true"
        logger.info(f"🔍 DEBUG: USE_EXTERNAL_SERVERS env var = '{use_external_servers_env}'")
        logger.info(f"🔍 DEBUG: use_external_servers flag = {use_external_servers}")

        # Initialize server manager
        self.server_manager = LlamaServerManager(
            llama_server_path=llama_server_path,
            max_startup_time=int(os.getenv("MODEL_MAX_STARTUP_TIME", "120")),
            readiness_check_interval=2,
            host="0.0.0.0",  # Docker: bind to all interfaces
            use_external_servers=use_external_servers
        )

        # Launch servers (concurrent or sequential based on config)
        concurrent = os.getenv("MODEL_CONCURRENT_STARTS", "true").lower() == "true"

        if concurrent:
            logger.info("Starting servers concurrently...")
            await self.server_manager.start_all(self.enabled_models)
        else:
            logger.info("Starting servers sequentially...")
            for model in self.enabled_models:
                try:
                    await self.server_manager.start_server(model)
                except Exception as e:
                    logger.error(f"Failed to start {model.model_id}: {e}")

    async def _health_check(self) -> dict:
        """Perform initial health check on servers.

        Returns:
            Status summary dictionary
        """
        if not self.server_manager:
            return {"total_servers": 0, "ready_servers": 0}

        status = self.server_manager.get_status_summary()

        ready = status['ready_servers']
        total = status['total_servers']

        if ready == total and total > 0:
            logger.info(f"✅ All {total} servers ready!")
        elif ready < total:
            logger.warning(f"⚠️  Only {ready}/{total} servers ready")
        else:
            logger.warning("⚠️  No servers launched")

        return status

    async def shutdown(self) -> None:
        """Gracefully shutdown all servers."""
        logger.info("Shutting down PRAXIS...")

        if self.server_manager:
            await self.server_manager.stop_all(timeout=10)

        logger.info("✅ Shutdown complete")
