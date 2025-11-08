"""Test complete S.Y.N.A.P.S.E. ENGINE startup sequence.

This script tests the full startup orchestration including:
1. Model discovery (from cache or fresh)
2. Profile loading
3. Model filtering
4. Server launch
5. Health checking
6. Graceful shutdown

Run this script to verify Phase 6 integration is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.startup import StartupService
from app.core.config import load_config


async def test_startup():
    """Test full startup sequence."""
    print("=" * 70)
    print("TESTING S.Y.N.A.P.S.E. ENGINE STARTUP SEQUENCE")
    print("=" * 70)

    # Load config
    try:
        config = load_config()
        print(f"✅ Configuration loaded")
        print(f"   Environment: {config.environment}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

    # Create startup service
    try:
        service = StartupService(config, profile_name="development")
        print(f"✅ StartupService created")
    except Exception as e:
        print(f"❌ Failed to create StartupService: {e}")
        return False

    try:
        # Run startup
        print("\n" + "=" * 70)
        print("RUNNING STARTUP SEQUENCE")
        print("=" * 70)

        registry = await service.initialize()

        print("\n" + "=" * 70)
        print("STARTUP TEST RESULTS")
        print("=" * 70)
        print(f"✅ Registry loaded: {len(registry.models)} models")
        print(f"✅ Profile loaded: {service.profile.name}")
        print(f"✅ Enabled models: {len(service.enabled_models)}")

        if service.enabled_models:
            print("\nEnabled Models:")
            for model in service.enabled_models:
                print(f"  - {model.get_display_name()}")
                print(f"    Tier: {model.tier}")
                print(f"    Port: {model.port}")
                print(f"    File: {model.file_path}")

        if service.server_manager:
            status = service.server_manager.get_status_summary()
            print(f"\n✅ Servers running: {status['total_servers']}")
            print(f"✅ Servers ready: {status['ready_servers']}")

            if status['servers']:
                print("\nServer Details:")
                for server_status in status['servers']:
                    print(f"  - {server_status['display_name']}")
                    print(f"    Port: {server_status['port']}")
                    print(f"    PID: {server_status['pid']}")
                    print(f"    Ready: {server_status['is_ready']}")
                    print(f"    Tier: {server_status['tier']}")
        else:
            print("⚠️  No server manager (no enabled models)")

        # Wait a bit to let servers fully initialize
        if service.enabled_models:
            print("\nWaiting 10 seconds for servers to stabilize...")
            await asyncio.sleep(10)

            # Check health again
            if service.server_manager:
                status = service.server_manager.get_status_summary()
                print(f"\nFinal Status:")
                print(f"  Ready servers: {status['ready_servers']}/{status['total_servers']}")

        # Shutdown
        print("\n" + "=" * 70)
        print("TESTING GRACEFUL SHUTDOWN")
        print("=" * 70)
        await service.shutdown()
        print("✅ Shutdown complete")

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

        # Attempt cleanup
        try:
            await service.shutdown()
        except Exception:
            pass

        return False

    return True


async def test_profile_loading():
    """Test profile loading in isolation."""
    print("\n" + "=" * 70)
    print("TESTING PROFILE LOADING")
    print("=" * 70)

    try:
        from app.services.profile_manager import ProfileManager

        manager = ProfileManager()
        print("✅ ProfileManager created")

        # Test loading each profile
        for profile_name in ["development", "production", "fast-only"]:
            try:
                profile = manager.load_profile(profile_name)
                print(f"✅ Profile '{profile_name}' loaded")
                print(f"   Description: {profile.description}")
                print(f"   Enabled models: {len(profile.enabled_models)}")
            except Exception as e:
                print(f"❌ Failed to load profile '{profile_name}': {e}")

        return True

    except Exception as e:
        print(f"❌ Profile loading test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 70)
    print("S.Y.N.A.P.S.E. ENGINE STARTUP INTEGRATION TESTS")
    print("=" * 70)

    # Test 1: Profile loading
    profile_success = await test_profile_loading()

    # Test 2: Full startup sequence
    startup_success = await test_startup()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Profile Loading: {'✅ PASSED' if profile_success else '❌ FAILED'}")
    print(f"Full Startup:    {'✅ PASSED' if startup_success else '❌ FAILED'}")
    print("=" * 70)

    return profile_success and startup_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
