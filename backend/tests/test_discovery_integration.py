"""
Integration test for S.Y.N.A.P.S.E. ENGINE model discovery system.

This demonstrates how to use the discovery service programmatically
and validates the complete discovery workflow.
"""

from pathlib import Path
from app.services.model_discovery import ModelDiscoveryService
from app.models.discovered_model import ModelTier, QuantizationLevel


def test_discovery_integration():
    """Test complete discovery workflow."""
    print("=" * 70)
    print("S.Y.N.A.P.S.E. ENGINE MODEL DISCOVERY - INTEGRATION TEST")
    print("=" * 70)

    # Initialize service
    scan_path = Path("/Users/dperez/Documents/LLM/llm-models/HUB")

    # Check if scan path exists, if not, skip test
    if not scan_path.exists():
        print(f"\n⚠️  Scan path does not exist: {scan_path}")
        print(f"   This test requires a local model directory")
        print(f"   Skipping test (not a failure)")
        import pytest
        pytest.skip("Scan path does not exist - requires local model directory")

    service = ModelDiscoveryService(
        scan_path=scan_path,
        port_range=(8080, 8099),
        powerful_threshold=14.0,
        fast_threshold=7.0
    )
    print(f"\n✓ Service initialized")
    print(f"  Scan path: {scan_path}")

    # Discover models
    registry = service.discover_models()
    print(f"\n✓ Discovery complete")
    print(f"  Total models: {len(registry.models)}")

    # Test tier filtering
    print("\n--- Tier Distribution ---")
    for tier in [ModelTier.FAST, ModelTier.BALANCED, ModelTier.POWERFUL]:
        models = registry.get_by_tier(tier)
        print(f"  {tier.value.upper():10s}: {len(models)} models")

    # Test thinking model detection
    thinking_models = [
        m for m in registry.models.values()
        if m.is_effectively_thinking()
    ]
    print(f"\n✓ Thinking models: {len(thinking_models)}")
    for model in thinking_models:
        print(f"  - {model.get_display_name()} ⚡")

    # Test model capabilities
    print("\n--- Model Capabilities ---")
    instruct_models = [m for m in registry.models.values() if m.is_instruct]
    coder_models = [m for m in registry.models.values() if m.is_coder]
    print(f"  Instruct models: {len(instruct_models)}")
    print(f"  Coder models: {len(coder_models)}")

    # Test port allocation
    print("\n--- Port Allocation ---")
    for port in range(8080, 8085):
        model = registry.get_by_port(port)
        if model:
            tier = model.get_effective_tier()
            tier_str = tier if isinstance(tier, str) else tier.value
            thinking = " ⚡" if model.is_effectively_thinking() else ""
            print(f"  Port {port}: {model.get_display_name()}{thinking} [{tier_str.upper()}]")

    # Test quantization detection
    print("\n--- Quantization Levels ---")
    quant_counts = {}
    for model in registry.models.values():
        quant = model.quantization
        quant_str = quant if isinstance(quant, str) else quant.value
        quant_counts[quant_str] = quant_counts.get(quant_str, 0) + 1
    for quant, count in sorted(quant_counts.items()):
        print(f"  {quant.upper():10s}: {count} models")

    # Test size distribution
    print("\n--- Size Distribution ---")
    sizes = sorted([m.size_params for m in registry.models.values()])
    print(f"  Smallest: {min(sizes)}B")
    print(f"  Largest:  {max(sizes)}B")
    print(f"  Average:  {sum(sizes)/len(sizes):.1f}B")

    # Test JSON persistence
    output_path = Path("data/test_registry.json")
    service.save_registry(registry, output_path)
    print(f"\n✓ Registry saved to: {output_path}")

    # Test loading
    loaded_registry = service.load_registry(output_path)
    print(f"✓ Registry loaded successfully")
    assert len(loaded_registry.models) == len(registry.models)
    print(f"  Verified: {len(loaded_registry.models)} models")

    # Cleanup
    output_path.unlink()
    print(f"✓ Test file cleaned up")

    # Final validation
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    validations = [
        ("Model IDs are unique", len(registry.models) == len(set(registry.models.keys()))),
        ("All models have ports", all(m.port is not None for m in registry.models.values())),
        ("All models disabled by default", all(not m.enabled for m in registry.models.values())),
        ("Tier thresholds set", registry.tier_thresholds is not None),
        ("Port range valid", registry.port_range[0] < registry.port_range[1]),
        ("Scan timestamp present", registry.last_scan is not None),
        ("At least one model discovered", len(registry.models) > 0),
    ]

    all_passed = True
    for check, passed in validations:
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
    else:
        print("❌ SOME VALIDATIONS FAILED")
    print("=" * 70)

    # Use assertion for pytest, but also return for standalone script
    assert all_passed, "Some validations failed"
    return all_passed


if __name__ == "__main__":
    import sys
    try:
        success = test_discovery_integration()
        sys.exit(0 if success else 1)
    except AssertionError:
        sys.exit(1)
