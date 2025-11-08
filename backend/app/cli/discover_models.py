"""
CLI tool for discovering GGUF models and generating model registry.

Usage:
    python -m app.cli.discover_models --scan-path /path/to/models
    python -m app.cli.discover_models  # Uses default from env/config
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from app.models.discovered_model import DiscoveredModel, ModelRegistry, ModelTier
from app.services.model_discovery import ModelDiscoveryService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner() -> None:
    """Print ASCII banner for S.Y.N.A.P.S.E. ENGINE discovery tool."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   S.Y.N.A.P.S.E. ENGINE MODEL DISCOVERY SYSTEM v4.0          ║
║   Multi-Model Orchestration WebUI                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_model_summary(model: DiscoveredModel) -> None:
    """Print single-line summary for discovered model.

    Args:
        model: Model to summarize
    """
    # Build summary components
    display_name = model.get_display_name()

    # Handle both enum and string values (Pydantic may convert)
    tier_value = model.assigned_tier if isinstance(model.assigned_tier, str) else model.assigned_tier.value
    tier = tier_value.upper()

    port = f"@ port {model.port}" if model.port else "(no port)"

    # Add thinking indicator
    thinking_marker = " ⚡" if model.is_effectively_thinking() else ""

    print(f"  Discovered: {display_name}{thinking_marker} [{tier}] {port}")


def print_tier_summary(registry: ModelRegistry) -> None:
    """Print detailed tier assignment summary.

    Args:
        registry: Registry to summarize
    """
    print("\n" + "=" * 64)
    print("MODEL TIER ASSIGNMENT SUMMARY")
    print("=" * 64)

    for tier in [ModelTier.FAST, ModelTier.BALANCED, ModelTier.POWERFUL]:
        models = registry.get_by_tier(tier)
        tier_name = tier.value.upper()

        print(f"\n{tier_name} tier: {len(models)} models")

        if models:
            # Sort by size descending, then quantization
            models.sort(
                key=lambda m: (-m.size_params,
                              m.quantization if isinstance(m.quantization, str) else m.quantization.value)
            )

            for model in models:
                thinking_marker = " ⚡" if model.is_effectively_thinking() else ""
                port_info = f"@ port {model.port}" if model.port else "(no port)"
                print(f"  - {model.get_display_name()}{thinking_marker} {port_info}")

    print("=" * 64)


def print_statistics(registry: ModelRegistry, gguf_count: int) -> None:
    """Print discovery statistics.

    Args:
        registry: Discovered registry
        gguf_count: Total GGUF files found
    """
    parsed_count = len(registry.models)
    failed_count = gguf_count - parsed_count

    print(f"\n{'─' * 64}")
    print("DISCOVERY STATISTICS")
    print(f"{'─' * 64}")
    print(f"  Total GGUF files found:     {gguf_count}")
    print(f"  Successfully parsed:        {parsed_count}")
    if failed_count > 0:
        print(f"  Failed to parse:            {failed_count}")

    # Tier distribution
    fast_count = len(registry.get_by_tier(ModelTier.FAST))
    balanced_count = len(registry.get_by_tier(ModelTier.BALANCED))
    powerful_count = len(registry.get_by_tier(ModelTier.POWERFUL))

    print(f"\n  Tier Distribution:")
    print(f"    FAST:      {fast_count:2d} models")
    print(f"    BALANCED:  {balanced_count:2d} models")
    print(f"    POWERFUL:  {powerful_count:2d} models")

    # Thinking models
    thinking_count = sum(
        1 for m in registry.models.values()
        if m.is_effectively_thinking()
    )
    if thinking_count > 0:
        print(f"\n  Reasoning models: {thinking_count} ⚡")

    # Port allocation
    models_with_ports = sum(
        1 for m in registry.models.values()
        if m.port is not None
    )
    print(f"\n  Port allocation: {models_with_ports}/{parsed_count} models")

    print(f"{'─' * 64}")


def discover_models_cli(scan_path: str, output_path: str) -> int:
    """Main CLI logic for model discovery.

    Args:
        scan_path: Directory to scan for GGUF files
        output_path: Path to save registry JSON

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Resolve and validate scan path
        scan_path_obj = Path(scan_path).expanduser().resolve()

        if not scan_path_obj.exists():
            logger.error(f"Scan path does not exist: {scan_path_obj}")
            print(f"\n❌ ERROR: Directory not found: {scan_path_obj}")
            return 1

        if not scan_path_obj.is_dir():
            logger.error(f"Scan path is not a directory: {scan_path_obj}")
            print(f"\n❌ ERROR: Not a directory: {scan_path_obj}")
            return 1

        # Print header
        print(f"\nScanning for GGUF models in: {scan_path_obj}")
        print("This may take a moment for large directories...\n")

        # Count GGUF files first
        gguf_files = list(scan_path_obj.rglob("*.gguf"))
        gguf_count = len(gguf_files)

        if gguf_count == 0:
            print(f"❌ No GGUF files found in {scan_path_obj}")
            logger.warning(f"No GGUF files found in {scan_path_obj}")
            return 0

        print(f"Found {gguf_count} GGUF files\n")

        # Initialize discovery service
        service = ModelDiscoveryService(
            scan_path=scan_path_obj,
            port_range=(8080, 8099),
            powerful_threshold=14.0,
            fast_threshold=7.0
        )

        # Discover models
        registry = service.discover_models()

        # Print individual model summaries
        for model_id in sorted(registry.models.keys()):
            model = registry.models[model_id]
            print_model_summary(model)

        # Print tier summary
        print_tier_summary(registry)

        # Print statistics
        print_statistics(registry, gguf_count)

        # Save registry
        output_path_obj = Path(output_path).expanduser().resolve()
        service.save_registry(registry, output_path_obj)

        print(f"\n✅ Registry saved to: {output_path_obj}")

        # Print usage hint
        print("\n" + "─" * 64)
        print("NEXT STEPS")
        print("─" * 64)
        print("1. Review the discovered models in the registry file")
        print("2. Enable models you want to use by setting 'enabled: true'")
        print("3. Override tier assignments if needed with 'tier_override'")
        print("4. Start model servers with: docker-compose up")
        print("─" * 64 + "\n")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return 1

    except PermissionError as e:
        logger.error(f"Permission denied: {e}", exc_info=True)
        print(f"\n❌ ERROR: Permission denied: {e}")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error during discovery: {e}", exc_info=True)
        print(f"\n❌ ERROR: Unexpected error: {e}")
        print("Check logs for details")
        return 1


def main() -> int:
    """Entry point for CLI tool.

    Returns:
        Exit code
    """
    print_banner()

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Discover GGUF models and generate model registry for S.Y.N.A.P.S.E. ENGINE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.cli.discover_models --scan-path /Users/dperez/Documents/LLM/llm-models/HUB/
  python -m app.cli.discover_models --scan-path ~/models --output registry.json
  python -m app.cli.discover_models  # Uses defaults

For more information, see: docs/development/TROUBLESHOOTING.md
        """
    )

    parser.add_argument(
        '--scan-path',
        type=str,
        default='/Users/dperez/Documents/LLM/llm-models/HUB/',
        help='Directory to scan for GGUF model files (default: %(default)s)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/model_registry.json',
        help='Output path for registry JSON file (default: %(default)s)'
    )

    parser.add_argument(
        '--powerful-threshold',
        type=float,
        default=14.0,
        help='Minimum parameter count for POWERFUL tier (default: %(default)s)'
    )

    parser.add_argument(
        '--fast-threshold',
        type=float,
        default=7.0,
        help='Maximum parameter count for FAST tier (default: %(default)s)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )

    args = parser.parse_args()

    # Adjust logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Run discovery
    return discover_models_cli(
        scan_path=args.scan_path,
        output_path=args.output
    )


if __name__ == '__main__':
    sys.exit(main())
