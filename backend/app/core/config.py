"""Configuration management for S.Y.N.A.P.S.E. CORE (PRAXIS).

Handles YAML loading and environment variable substitution for the orchestrator service.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigurationError
from app.models.config import AppConfig


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables override values from YAML configuration.
    Uses pydantic-settings for type validation and .env file support.
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / '.env'),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='allow',
        protected_namespaces=()  # Disable protected namespace warnings for model_* fields
    )

    # Application settings
    app_name: str = 'S.Y.N.A.P.S.E. Core (PRAXIS)'
    service_tag: str = 'prx'
    codename: str = 'CORE:PRAXIS'
    environment: str = 'development'
    debug: bool = False
    host: str = '0.0.0.0'
    port: int = 8000

    # Redis settings
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Logging settings
    log_level: str = 'INFO'
    log_format: str = 'json'
    log_file: Optional[str] = None

    # CGRAG settings
    embedding_model: str = 'all-MiniLM-L6-v2'
    cgrag_token_budget: int = 8000
    cgrag_min_relevance: float = 0.7


class ConfigLoader:
    """Configuration loader with YAML parsing and environment variable substitution.

    Loads configuration from YAML files and substitutes environment variables
    using ${VAR_NAME} syntax. Validates the final configuration using Pydantic models.
    """

    # Pattern for matching ${VAR_NAME} in config values
    ENV_VAR_PATTERN = re.compile(r'\$\{([A-Za-z0-9_]+)\}')

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize config loader.

        Args:
            config_path: Path to YAML config file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/default.yaml relative to project root
            # Path(__file__) = .../backend/app/core/config.py
            # In local dev: .parent.parent.parent.parent = project root (S.Y.N.A.P.S.E-ENGINE/)
            # In Docker: .parent.parent.parent = /app (project root in container)
            # Check if running in Docker by looking for /app directory
            file_path = Path(__file__)
            if str(file_path).startswith('/app/'):
                # Running in Docker: /app/app/core/config.py -> /app
                project_root = file_path.parent.parent.parent
            else:
                # Running locally: .../backend/app/core/config.py -> project root
                project_root = file_path.parent.parent.parent.parent
            config_path = project_root / 'config' / 'default.yaml'

        self.config_path = config_path
        self.settings = Settings()

    def _substitute_env_vars(self, value: Any, env_dict: Dict[str, str]) -> Any:
        """Recursively substitute environment variables in configuration values.

        Supports ${VAR_NAME} syntax for variable substitution.

        Args:
            value: Configuration value (can be str, dict, list, or primitive)
            env_dict: Dictionary of environment variable names to values

        Returns:
            Value with environment variables substituted
        """
        if isinstance(value, str):
            # Find all ${VAR_NAME} patterns and substitute
            def replace_var(match: re.Match[str]) -> str:
                var_name = match.group(1)
                if var_name not in env_dict:
                    raise ConfigurationError(
                        f"Environment variable not found: {var_name}",
                        details={'variable': var_name}
                    )
                return env_dict[var_name]

            return self.ENV_VAR_PATTERN.sub(replace_var, value)

        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v, env_dict) for k, v in value.items()}

        elif isinstance(value, list):
            return [self._substitute_env_vars(item, env_dict) for item in value]

        else:
            # Primitive type (int, bool, etc.) - return as-is
            return value

    def _load_yaml(self) -> Dict[str, Any]:
        """Load and parse YAML configuration file.

        Returns:
            Parsed YAML configuration as dictionary

        Raises:
            ConfigurationError: If config file cannot be loaded or parsed
        """
        try:
            if not self.config_path.exists():
                raise ConfigurationError(
                    f"Configuration file not found: {self.config_path}",
                    details={'path': str(self.config_path)}
                )

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)

            if config_dict is None:
                raise ConfigurationError(
                    f"Configuration file is empty: {self.config_path}",
                    details={'path': str(self.config_path)}
                )

            return config_dict

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Failed to parse YAML configuration: {e}",
                details={'path': str(self.config_path)}
            ) from e
        except OSError as e:
            raise ConfigurationError(
                f"Failed to read configuration file: {e}",
                details={'path': str(self.config_path)}
            ) from e

    def _build_env_dict(self) -> Dict[str, str]:
        """Build dictionary of environment variables for substitution.

        Uses both pydantic Settings and os.environ to ensure all variables
        are available for substitution.

        Returns:
            Dictionary mapping variable names to values
        """
        env_dict: Dict[str, str] = {}

        # Add all environment variables from os.environ
        env_dict.update(os.environ)

        # Add settings from pydantic Settings (these override os.environ)
        for field_name in self.settings.model_fields.keys():
            value = getattr(self.settings, field_name)
            if value is not None:
                # Convert to uppercase for ${VAR_NAME} syntax
                env_dict[field_name.upper()] = str(value)

        return env_dict

    def load(self) -> AppConfig:
        """Load and validate application configuration.

        Loads YAML configuration, substitutes environment variables,
        and validates using Pydantic models.

        Returns:
            Validated AppConfig instance

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Load YAML configuration
        config_dict = self._load_yaml()

        # Build environment variable dictionary
        env_dict = self._build_env_dict()

        # Substitute environment variables
        config_dict = self._substitute_env_vars(config_dict, env_dict)

        # Update top-level settings from pydantic Settings
        config_dict['app_name'] = self.settings.app_name
        config_dict['environment'] = self.settings.environment
        config_dict['debug'] = self.settings.debug
        config_dict['host'] = self.settings.host
        config_dict['port'] = self.settings.port

        # Update Redis settings
        if 'redis' not in config_dict:
            config_dict['redis'] = {}
        config_dict['redis'].update({
            'host': self.settings.redis_host,
            'port': self.settings.redis_port,
            'db': self.settings.redis_db,
            'password': self.settings.redis_password,
        })

        # Update logging settings
        if 'logging' not in config_dict:
            config_dict['logging'] = {}
        config_dict['logging'].update({
            'level': self.settings.log_level,
            'format': self.settings.log_format,
            'log_file': self.settings.log_file,
        })

        # Validate with Pydantic
        try:
            return AppConfig(**config_dict)
        except Exception as e:
            raise ConfigurationError(
                f"Configuration validation failed: {e}",
                details={'error': str(e)}
            ) from e


# Global configuration instance
_config: Optional[AppConfig] = None


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load application configuration.

    This function should be called once during application startup.

    Args:
        config_path: Optional path to YAML config file

    Returns:
        Validated AppConfig instance
    """
    global _config
    loader = ConfigLoader(config_path)
    _config = loader.load()
    return _config


def get_config() -> AppConfig:
    """Get the current application configuration.

    Returns:
        Current AppConfig instance

    Raises:
        ConfigurationError: If configuration has not been loaded
    """
    if _config is None:
        raise ConfigurationError(
            "Configuration not loaded. Call load_config() first.",
            details={'hint': 'Call load_config() during application startup'}
        )
    return _config
