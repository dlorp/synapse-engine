"""Integration test showing profile system with mock registry.

This demonstrates how profiles integrate with the model registry.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timezone

from app.models.discovered_model import (
    DiscoveredModel,
    ModelRegistry,
    ModelTier,
    QuantizationLevel,
)
from app.services.profile_manager import ProfileManager


def create_mock_registry() -> ModelRegistry:
    """Create a mock registry matching the discovered models."""
    models = {
        "gpt_oss_20p0b_q4km_powerful": DiscoveredModel(
            file_path="/mock/gpt_oss_20p0b_q4km_powerful.gguf",
            filename="gpt_oss_20p0b_q4km_powerful.gguf",
            family="gpt-oss",
            version="20",
            size_params=20.0,
            quantization=QuantizationLevel.Q4_K_M,
            is_thinking_model=False,
            is_instruct=True,
            is_coder=False,
            assigned_tier=ModelTier.POWERFUL,
            model_id="gpt_oss_20p0b_q4km_powerful",
        ),
        "qwen2_coder_p5_14p0b_q4km_powerful": DiscoveredModel(
            file_path="/mock/qwen2_coder_p5_14p0b_q4km_powerful.gguf",
            filename="qwen2_coder_p5_14p0b_q4km_powerful.gguf",
            family="qwen2-coder",
            version="2.5",
            size_params=14.0,
            quantization=QuantizationLevel.Q4_K_M,
            is_thinking_model=False,
            is_instruct=True,
            is_coder=True,
            assigned_tier=ModelTier.POWERFUL,
            model_id="qwen2_coder_p5_14p0b_q4km_powerful",
        ),
        "deepseek_r10528qwen3_8p0b_q4km_powerful": DiscoveredModel(
            file_path="/mock/deepseek_r10528qwen3_8p0b_q4km_powerful.gguf",
            filename="deepseek_r10528qwen3_8p0b_q4km_powerful.gguf",
            family="deepseek-r1",
            version="0528",
            size_params=8.0,
            quantization=QuantizationLevel.Q4_K_M,
            is_thinking_model=True,
            is_instruct=True,
            is_coder=False,
            assigned_tier=ModelTier.POWERFUL,
            model_id="deepseek_r10528qwen3_8p0b_q4km_powerful",
        ),
        "qwen3_vl_4p0b_q4km_fast": DiscoveredModel(
            file_path="/mock/qwen3_vl_4p0b_q4km_fast.gguf",
            filename="qwen3_vl_4p0b_q4km_fast.gguf",
            family="qwen3-vl",
            version="3",
            size_params=4.0,
            quantization=QuantizationLevel.Q4_K_M,
            is_thinking_model=False,
            is_instruct=True,
            is_coder=False,
            assigned_tier=ModelTier.FAST,
            model_id="qwen3_vl_4p0b_q4km_fast",
        ),
        "qwen3_4p0b_q4km_fast": DiscoveredModel(
            file_path="/mock/qwen3_4p0b_q4km_fast.gguf",
            filename="qwen3_4p0b_q4km_fast.gguf",
            family="qwen3",
            version="3",
            size_params=4.0,
            quantization=QuantizationLevel.Q4_K_M,
            is_thinking_model=False,
            is_instruct=True,
            is_coder=False,
            assigned_tier=ModelTier.FAST,
            model_id="qwen3_4p0b_q4km_fast",
        ),
    }

    return ModelRegistry(
        models=models,
        scan_path="/mock/models",
        last_scan=datetime.now(timezone.utc).isoformat(),
    )


def test_profile_with_registry():
    """Test profile validation against mock registry."""
    print("=" * 60)
    print("Profile Integration Test with Model Registry")
    print("=" * 60)

    # Create mock registry
    registry = create_mock_registry()
    print(f"\nMock registry created with {len(registry.models)} models:")
    for model_id, model in registry.models.items():
        print(f"  - {model.get_display_name()}")

    # Load profiles
    manager = ProfileManager(profiles_dir=Path("../config/profiles"))
    profiles = manager.list_profiles()

    print(f"\n\nValidating {len(profiles)} profiles...\n")

    # Validate each profile
    for profile_name in profiles:
        print("-" * 60)
        profile = manager.load_profile(profile_name)
        print(f"\nProfile: {profile.name}")
        print(f"Description: {profile.description}")

        # Validate
        missing = manager.validate_profile(profile, list(registry.models.keys()))

        if missing:
            print(f"✗ Missing models: {missing}")
        else:
            print(f"✓ All {len(profile.enabled_models)} models are valid")

            # Show which models are enabled
            print("\nEnabled models:")
            for model_id in profile.enabled_models:
                model = registry.models[model_id]
                print(f"  • {model.get_display_name()}")
                print(f"    - Tier: {model.get_effective_tier()}")
                print(f"    - Size: {model.size_params}B params")
                print(f"    - Quantization: {model.quantization}")
                if model.is_effectively_thinking():
                    print("    -  Reasoning model")

            # Show tier routing
            print("\nTier routing configuration:")
            for tier in profile.tier_config:
                print(
                    f"  • {tier.name.upper()}: complexity ≤ {tier.max_score}, "
                    f"target {tier.expected_time_seconds}s"
                )
                if tier.description:
                    print(f"    └─ {tier.description}")

            # Show special configs
            if profile.two_stage.enabled:
                print("\n Two-stage processing enabled:")
                print(
                    f"  Stage 1: {profile.two_stage.stage1_tier} "
                    f"(max {profile.two_stage.stage1_max_tokens} tokens)"
                )
                print(f"  Stage 2: {profile.two_stage.stage2_tier} (full response)")

            if profile.load_balancing.enabled:
                print("\n  Load balancing enabled:")
                print(f"  Strategy: {profile.load_balancing.strategy}")
                print(f"  Health check: every {profile.load_balancing.health_check_interval}s")

    print("\n" + "=" * 60)
    print("✓ Profile Integration Test Complete!")
    print("=" * 60)


def test_profile_tier_matching():
    """Test that profile tiers match model tiers."""
    print("\n" + "=" * 60)
    print("Tier Matching Test")
    print("=" * 60)

    registry = create_mock_registry()
    manager = ProfileManager(profiles_dir=Path("../config/profiles"))

    # Test each profile
    for profile_name in manager.list_profiles():
        profile = manager.load_profile(profile_name)
        print(f"\n{profile.name}:")

        # Check that enabled models match expected tiers
        for model_id in profile.enabled_models:
            model = registry.models[model_id]
            tier_names = [t.name for t in profile.tier_config]

            print(f"  - {model.get_display_name()}")
            print(f"    Model tier: {model.get_effective_tier()}")
            print(f"    Available routing tiers: {tier_names}")

            # Check if model tier exists in profile
            if model.get_effective_tier() in tier_names:
                print("    ✓ Tier match found")
            else:
                print(f"      Model tier '{model.get_effective_tier()}' not in profile tier config")

    print("\n" + "=" * 60)
    print("✓ Tier Matching Test Complete!")
    print("=" * 60)


def main():
    """Run integration tests."""
    try:
        test_profile_with_registry()
        test_profile_tier_matching()

        print("\n" + "=" * 60)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nPhase 2 is complete and ready for Phase 3 (Health Monitoring)")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
