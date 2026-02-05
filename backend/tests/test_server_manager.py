"""
Test script for S.Y.N.A.P.S.E. ENGINE LlamaServerManager - Phase 4 validation.

Tests server lifecycle management including:
- Single server startup and readiness detection
- Status monitoring
- Graceful shutdown

Run from backend/ directory:
    python test_server_manager.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.model_discovery import ModelDiscoveryService
from app.services.llama_server_manager import LlamaServerManager


async def test_server_manager():
    """Test server manager with a single fast model."""
    print("=" * 80)
    print("S.Y.N.A.P.S.E. ENGINE Phase 4 Test: Llama Server Manager")
    print("=" * 80)
    print()

    # Load model registry from Phase 1
    print("[1/6] Loading model registry...")
    discovery = ModelDiscoveryService(scan_path=Path("${PRAXIS_MODEL_PATH}/"))

    registry_path = Path("data/model_registry.json")
    if not registry_path.exists():
        print(f"✗ Registry not found at {registry_path}")
        print("   Run Phase 1 (model discovery) first to create registry")
        return

    registry = discovery.load_registry(registry_path)
    print(f"✓ Loaded registry with {len(registry.models)} models")
    print()

    # Select a fast model for testing (Q4_K_M is good balance)
    print("[2/6] Selecting test model...")
    test_model = registry.models.get("qwen3_4p0b_q4km_fast")

    if not test_model:
        print("✗ Test model 'qwen3_4p0b_q4km_fast' not found in registry")
        print(f"   Available models: {list(registry.models.keys())}")
        return

    # Ensure model is enabled
    test_model.enabled = True

    print(f"✓ Selected: {test_model.get_display_name()}")
    print(f"   Model ID: {test_model.model_id}")
    print(f"   File: {Path(test_model.file_path).name}")
    print(f"   Port: {test_model.port}")
    # Handle tier as either enum or string
    tier = test_model.get_effective_tier()
    tier_str = tier.value if hasattr(tier, "value") else tier
    print(f"   Tier: {tier_str}")
    print(f"   Thinking: {test_model.is_effectively_thinking()}")
    print()

    # Create server manager
    print("[3/6] Initializing server manager...")
    manager = LlamaServerManager(
        llama_server_path=Path("/usr/local/bin/llama-server"),
        max_startup_time=60,  # 1 minute timeout for testing
        readiness_check_interval=2,
    )
    print("✓ Manager initialized")
    print(f"   Binary: {manager.llama_server_path}")
    print(f"   Host: {manager.host}")
    print(f"   Max startup time: {manager.max_startup_time}s")
    print()

    try:
        # Start server
        print("[4/6] Starting llama.cpp server...")
        print("   This may take 30-60 seconds for model loading...")
        print()

        server = await manager.start_server(test_model)

        print("✓ Server started successfully!")
        print(f"   PID: {server.pid}")
        print(f"   Port: {server.port}")
        print(f"   Ready: {server.is_ready}")
        print(f"   Uptime: {server.get_uptime_seconds()}s")
        print()

        # Get status summary
        print("[5/6] Checking status...")
        status = manager.get_status_summary()

        print("Status Summary:")
        print(f"   Total servers: {status['total_servers']}")
        print(f"   Ready servers: {status['ready_servers']}")
        print(f"   Running servers: {status['running_servers']}")
        print()

        if status["servers"]:
            server_info = status["servers"][0]
            print("Server Details:")
            print(f"   Model: {server_info['display_name']}")
            print(f"   PID: {server_info['pid']}")
            print(f"   Port: {server_info['port']}")
            print(f"   Ready: {server_info['is_ready']}")
            print(f"   Running: {server_info['is_running']}")
            print(f"   Uptime: {server_info['uptime_seconds']}s")
            print(f"   Tier: {server_info['tier']}")
            print(f"   Thinking: {server_info['is_thinking']}")
            print()

        # Wait a bit to observe running state
        print("Waiting 5 seconds to observe running state...")
        await asyncio.sleep(5)
        print(f"   Uptime now: {server.get_uptime_seconds()}s")
        print()

        # Test server lookup
        print("Testing server lookup...")
        found_server = manager.get_server(test_model.model_id)
        if found_server:
            print("✓ Server lookup successful")
            print(f"   Found: {found_server.model.get_display_name()}")
        else:
            print("✗ Server lookup failed")
        print()

        # Check if running
        is_running = manager.is_server_running(test_model.model_id)
        print(f"Is server running? {is_running}")
        print()

        # Stop server
        print("[6/6] Stopping server gracefully...")
        await manager.stop_server(test_model.model_id, timeout=10)
        print("✓ Server stopped")
        print()

        # Verify stopped
        final_status = manager.get_status_summary()
        print("Final status:")
        print(f"   Total servers: {final_status['total_servers']}")
        print()

        print("=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Phase 4 server manager is working correctly!")
        print("Ready for Phase 5: Profile-Based Orchestration")

    except Exception as e:
        print(f"✗ Error during test: {e}")
        print()
        import traceback

        traceback.print_exc()

        # Attempt cleanup
        print()
        print("Attempting to stop any running servers...")
        try:
            await manager.stop_all(timeout=5)
            print("✓ Cleanup successful")
        except Exception as cleanup_error:
            print(f"✗ Cleanup failed: {cleanup_error}")


async def test_concurrent_startup():
    """Test concurrent startup of multiple servers."""
    print("=" * 80)
    print("BONUS TEST: Concurrent Server Startup")
    print("=" * 80)
    print()

    print("[1/3] Loading models...")
    discovery = ModelDiscoveryService(scan_path=Path("${PRAXIS_MODEL_PATH}/"))
    registry = discovery.load_registry(Path("data/model_registry.json"))

    # Select 2 fast models for concurrent test
    # Note: Only select models that exist in the registry
    available_fast_models = [
        model_id
        for model_id, model in registry.models.items()
        if "fast" in model_id and model.port is not None
    ]

    if len(available_fast_models) < 2:
        print("✗ Not enough fast models in registry")
        print(f"   Found: {available_fast_models}")
        print("   Skipping concurrent test")
        return

    test_models = [
        registry.models[available_fast_models[0]],
        registry.models[available_fast_models[1]],
    ]

    for model in test_models:
        model.enabled = True

    print(f"✓ Selected {len(test_models)} models:")
    for model in test_models:
        print(f"   - {model.get_display_name()} (port {model.port})")
    print()

    print("[2/3] Starting servers concurrently...")
    manager = LlamaServerManager(
        llama_server_path=Path("/usr/local/bin/llama-server"), max_startup_time=90
    )

    try:
        started = await manager.start_all(test_models)
        print(f"✓ Started {len(started)}/{len(test_models)} servers")
        print()

        status = manager.get_status_summary()
        print(f"Status: {status['ready_servers']}/{status['total_servers']} ready")
        print()

        print("[3/3] Stopping all servers...")
        await manager.stop_all(timeout=10)
        print("✓ All servers stopped")
        print()

        print("✓ Concurrent startup test passed!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()

        # Cleanup
        await manager.stop_all(timeout=5)


if __name__ == "__main__":
    print()
    print("S.Y.N.A.P.S.E. ENGINE Model Management System - Phase 4 Test")
    print("Llama Server Manager Validation")
    print()

    # Run main test
    asyncio.run(test_server_manager())

    print()
    print("=" * 80)
    print()

    # Ask if user wants to run concurrent test
    print("Run concurrent startup test? (will start 2 servers simultaneously)")
    response = input("Continue? [y/N]: ").strip().lower()

    if response == "y":
        print()
        asyncio.run(test_concurrent_startup())
    else:
        print("Skipping concurrent test.")

    print()
    print("Test suite complete!")
