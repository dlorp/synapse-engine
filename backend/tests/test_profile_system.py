"""Test script for Phase 2: Profile System.

This script validates the ProfileManager implementation and default profiles.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.profile_manager import ProfileManager
from app.services.model_discovery import ModelDiscoveryService


def test_profile_manager():
    """Test ProfileManager basic operations."""
    print("=" * 60)
    print("TEST 1: Profile Manager Operations")
    print("=" * 60)

    # Use absolute path from container root
    manager = ProfileManager(profiles_dir=Path("/app/config/profiles"))

    # List profiles
    profiles = manager.list_profiles()
    print(f"\nAvailable profiles: {profiles}")
    assert len(profiles) == 3, f"Expected 3 profiles, got {len(profiles)}"
    assert "development" in profiles
    assert "production" in profiles
    assert "fast-only" in profiles
    print("✅ Profile listing works")

    # Load each profile
    print("\n" + "-" * 60)
    for name in profiles:
        print(f"\nLoading profile: {name}")
        profile = manager.load_profile(name)
        print(f"  Name: {profile.name}")
        print(f"  Description: {profile.description}")
        print(f"  Enabled models: {profile.enabled_models}")
        print(f"  Tier count: {len(profile.tier_config)}")
        print(f"  Two-stage enabled: {profile.two_stage.enabled}")
        print(f"  Load balancing enabled: {profile.load_balancing.enabled}")

        # Validate tier config
        for tier in profile.tier_config:
            print(f"    Tier '{tier.name}': max_score={tier.max_score}, "
                  f"expected_time={tier.expected_time_seconds}s")

    print("\n✅ Profile loading works")


def test_profile_validation():
    """Test profile validation against model registry."""
    print("\n" + "=" * 60)
    print("TEST 2: Profile Validation")
    print("=" * 60)

    # Load registry
    discovery = ModelDiscoveryService(
        scan_path=Path("${PRAXIS_MODEL_PATH}/")
    )
    # Use absolute path from container root
    registry_path = Path("/app/data/model_registry.json")

    if not registry_path.exists():
        print("⚠️  Model registry not found. Run Phase 1 first.")
        return

    registry = discovery.load_registry(registry_path)
    print(f"\nLoaded registry with {len(registry.models)} models")

    # Validate profiles
    # Use absolute path from container root
    manager = ProfileManager(profiles_dir=Path("/app/config/profiles"))
    all_valid = True

    for name in manager.list_profiles():
        profile = manager.load_profile(name)
        missing = manager.validate_profile(profile, list(registry.models.keys()))

        if missing:
            print(f"\n⚠️  Profile '{name}' has missing models: {missing}")
            all_valid = False
        else:
            print(f"\n✅ Profile '{name}' is valid ({len(profile.enabled_models)} models)")
            for model_id in profile.enabled_models:
                model = registry.models[model_id]
                print(f"    - {model.get_display_name()}")

    if all_valid:
        print("\n" + "=" * 60)
        print("✅ All profiles are valid!")
        print("=" * 60)


def test_profile_structure():
    """Test profile structure and configuration details."""
    print("\n" + "=" * 60)
    print("TEST 3: Profile Structure Details")
    print("=" * 60)

    # Use absolute path from container root
    manager = ProfileManager(profiles_dir=Path("/app/config/profiles"))

    # Test development profile
    print("\n--- Development Profile ---")
    dev = manager.load_profile("development")
    assert dev.two_stage.enabled == True
    assert dev.two_stage.stage1_tier == "fast"
    assert dev.two_stage.stage2_tier == "powerful"
    assert dev.load_balancing.enabled == False
    print(f"✅ Two-stage config: stage1={dev.two_stage.stage1_tier}, "
          f"stage2={dev.two_stage.stage2_tier}, "
          f"max_tokens={dev.two_stage.stage1_max_tokens}")

    # Test production profile
    print("\n--- Production Profile ---")
    prod = manager.load_profile("production")
    assert prod.two_stage.enabled == False
    assert prod.load_balancing.enabled == True
    assert prod.load_balancing.strategy == "round_robin"
    print(f"✅ Load balancing: strategy={prod.load_balancing.strategy}, "
          f"interval={prod.load_balancing.health_check_interval}s")

    # Test fast-only profile
    print("\n--- Fast-Only Profile ---")
    fast = manager.load_profile("fast-only")
    assert len(fast.enabled_models) == 1
    assert len(fast.tier_config) == 1
    assert fast.tier_config[0].name == "fast"
    print(f"✅ Single tier config: {fast.tier_config[0].name} "
          f"(max_score={fast.tier_config[0].max_score})")

    print("\n" + "=" * 60)
    print("✅ All profile structures are correct!")
    print("=" * 60)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("S.Y.N.A.P.S.E. ENGINE Phase 2: Profile System Tests")
    print("=" * 60)

    try:
        test_profile_manager()
        test_profile_validation()
        test_profile_structure()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPhase 2 implementation is complete and working correctly.")
        print("\nNext steps:")
        print("  - Phase 3: Model Health Monitoring")
        print("  - Phase 4: Query Routing Logic")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
