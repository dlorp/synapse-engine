"""Runtime settings service for persistence and management.

Handles loading, saving, and validating runtime settings that can be
modified via the WebUI. Settings are persisted to data/runtime_settings.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from pydantic import ValidationError

from app.models.runtime_settings import RuntimeSettings

logger = logging.getLogger(__name__)

# Global singleton instance
_runtime_settings: Optional[RuntimeSettings] = None
_settings_file_path: Path = Path("data/runtime_settings.json")


async def load_runtime_settings(file_path: Optional[Path] = None) -> RuntimeSettings:
    """Load runtime settings from JSON file.

    Args:
        file_path: Optional custom path to settings file

    Returns:
        RuntimeSettings instance (defaults if file doesn't exist)
    """
    global _runtime_settings
    global _settings_file_path

    if file_path:
        _settings_file_path = file_path

    # Create data directory if it doesn't exist
    _settings_file_path.parent.mkdir(parents=True, exist_ok=True)

    # If file doesn't exist, create default settings
    if not _settings_file_path.exists():
        logger.info(
            f"Runtime settings file not found at {_settings_file_path}, creating defaults"
        )
        _runtime_settings = RuntimeSettings()
        await save_runtime_settings(_runtime_settings)
        return _runtime_settings

    # Load from file
    try:
        with open(_settings_file_path, "r") as f:
            data = json.load(f)

        _runtime_settings = RuntimeSettings(**data)
        logger.info(f"Loaded runtime settings from {_settings_file_path}")
        return _runtime_settings

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in runtime settings file: {e}")
        logger.warning("Using default runtime settings")
        _runtime_settings = RuntimeSettings()
        return _runtime_settings

    except ValidationError as e:
        logger.error(f"Invalid runtime settings schema: {e}")
        logger.warning("Using default runtime settings")
        _runtime_settings = RuntimeSettings()
        return _runtime_settings

    except Exception as e:
        logger.error(f"Failed to load runtime settings: {e}")
        logger.warning("Using default runtime settings")
        _runtime_settings = RuntimeSettings()
        return _runtime_settings


async def save_runtime_settings(
    settings: RuntimeSettings, file_path: Optional[Path] = None
) -> None:
    """Save runtime settings to JSON file (atomic write).

    Args:
        settings: RuntimeSettings to save
        file_path: Optional custom path to settings file
    """
    global _runtime_settings
    global _settings_file_path

    if file_path:
        _settings_file_path = file_path

    # Create data directory if it doesn't exist
    _settings_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file then rename
    temp_path = _settings_file_path.with_suffix(".tmp")

    try:
        # Convert to dict and add metadata
        data = settings.model_dump()
        data["_metadata"] = {
            "last_modified": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
        }

        # Write to temp file
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)

        # Atomic rename
        temp_path.replace(_settings_file_path)

        # Update global singleton
        _runtime_settings = settings

        logger.info(f"Saved runtime settings to {_settings_file_path}")

    except Exception as e:
        logger.error(f"Failed to save runtime settings: {e}")
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        raise


async def validate_settings(settings: RuntimeSettings) -> Tuple[bool, List[str]]:
    """Validate runtime settings for consistency and feasibility.

    Args:
        settings: RuntimeSettings to validate

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []

    # Validate GPU layers
    if settings.n_gpu_layers < 0 or settings.n_gpu_layers > 999:
        errors.append("n_gpu_layers must be between 0 and 999")

    # Validate context size (must be power of 2 or common values)
    valid_ctx_sizes = {512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072}
    if settings.ctx_size not in valid_ctx_sizes:
        errors.append(
            f"ctx_size must be one of {valid_ctx_sizes} (got {settings.ctx_size})"
        )

    # Validate ubatch_size <= batch_size
    if settings.ubatch_size > settings.batch_size:
        errors.append(
            f"ubatch_size ({settings.ubatch_size}) must be <= batch_size ({settings.batch_size})"
        )

    # Validate threads
    if settings.threads < 1 or settings.threads > 64:
        errors.append("threads must be between 1 and 64")

    # Validate embedding model name (basic check)
    if (
        not settings.embedding_model_name
        or len(settings.embedding_model_name.strip()) == 0
    ):
        errors.append("embedding_model_name cannot be empty")

    # Validate embedding cache path if provided
    if settings.embedding_model_cache_path:
        cache_path = Path(settings.embedding_model_cache_path)
        if not cache_path.exists():
            errors.append(
                f"embedding_model_cache_path does not exist: {settings.embedding_model_cache_path}"
            )
        elif not cache_path.is_dir():
            errors.append(
                f"embedding_model_cache_path must be a directory: {settings.embedding_model_cache_path}"
            )

    # Validate CGRAG parameters
    if settings.cgrag_token_budget < 1000:
        errors.append("cgrag_token_budget must be at least 1000")

    if settings.cgrag_min_relevance < 0.0 or settings.cgrag_min_relevance > 1.0:
        errors.append("cgrag_min_relevance must be between 0.0 and 1.0")

    if settings.cgrag_chunk_overlap >= settings.cgrag_chunk_size:
        errors.append(
            f"cgrag_chunk_overlap ({settings.cgrag_chunk_overlap}) must be less than "
            f"cgrag_chunk_size ({settings.cgrag_chunk_size})"
        )

    # Validate benchmark parameters
    if settings.benchmark_default_max_tokens < 128:
        errors.append("benchmark_default_max_tokens must be at least 128")

    if settings.benchmark_parallel_max_models < 1:
        errors.append("benchmark_parallel_max_models must be at least 1")

    # Validate web search parameters
    if settings.websearch_max_results < 1:
        errors.append("websearch_max_results must be at least 1")

    if settings.websearch_timeout_seconds < 5:
        errors.append("websearch_timeout_seconds must be at least 5")

    is_valid = len(errors) == 0
    return is_valid, errors


async def reset_to_defaults() -> RuntimeSettings:
    """Reset runtime settings to defaults and save.

    Returns:
        New RuntimeSettings with default values
    """
    logger.info("Resetting runtime settings to defaults")
    defaults = RuntimeSettings()
    await save_runtime_settings(defaults)
    return defaults


def get_runtime_settings() -> RuntimeSettings:
    """Get the current runtime settings singleton.

    Returns:
        RuntimeSettings instance (creates defaults if not loaded)
    """
    global _runtime_settings

    if _runtime_settings is None:
        logger.warning("Runtime settings not loaded, creating defaults")
        _runtime_settings = RuntimeSettings()

    return _runtime_settings


async def update_runtime_settings(
    new_settings: RuntimeSettings,
) -> Tuple[bool, RuntimeSettings, bool, List[str]]:
    """Update runtime settings with validation.

    Args:
        new_settings: New RuntimeSettings to apply

    Returns:
        Tuple of (success, updated_settings, restart_required, errors)
    """
    # Validate new settings
    is_valid, errors = await validate_settings(new_settings)

    if not is_valid:
        logger.warning(f"Invalid settings update rejected: {errors}")
        return False, get_runtime_settings(), False, errors

    # Check if restart required
    current_settings = get_runtime_settings()
    restart_required = new_settings.requires_server_restart(current_settings)

    # Save new settings
    try:
        await save_runtime_settings(new_settings)
        logger.info(
            f"Runtime settings updated successfully "
            f"(restart_required={restart_required})"
        )
        return True, new_settings, restart_required, []

    except Exception as e:
        logger.error(f"Failed to save updated settings: {e}")
        return False, current_settings, False, [str(e)]


async def get_settings_metadata() -> dict:
    """Get metadata about current settings file.

    Returns:
        Dict with file path, last modified time, size
    """
    global _settings_file_path

    if not _settings_file_path.exists():
        return {
            "exists": False,
            "path": str(_settings_file_path),
        }

    stat = _settings_file_path.stat()

    return {
        "exists": True,
        "path": str(_settings_file_path),
        "size_bytes": stat.st_size,
        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z",
    }


async def export_settings_json() -> str:
    """Export current settings as formatted JSON string.

    Returns:
        JSON string of current settings
    """
    settings = get_runtime_settings()
    data = settings.model_dump()
    return json.dumps(data, indent=2)


async def import_settings_json(
    json_str: str,
) -> Tuple[bool, Optional[RuntimeSettings], List[str]]:
    """Import settings from JSON string with validation.

    Args:
        json_str: JSON string containing settings

    Returns:
        Tuple of (success, settings if valid, errors)
    """
    try:
        data = json.loads(json_str)
        settings = RuntimeSettings(**data)

        is_valid, errors = await validate_settings(settings)

        if is_valid:
            return True, settings, []
        else:
            return False, None, errors

    except json.JSONDecodeError as e:
        return False, None, [f"Invalid JSON: {str(e)}"]

    except ValidationError as e:
        return False, None, [f"Invalid settings schema: {str(e)}"]

    except Exception as e:
        return False, None, [f"Import failed: {str(e)}"]
