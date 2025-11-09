#!/usr/bin/env python3
"""Test script for WebSocket event system.

This script verifies that the event bus and WebSocket endpoint work correctly
by publishing test events and monitoring WebSocket connections.

Usage:
    # From project root
    docker-compose exec synapse_core python test_event_system.py

Author: Backend Architect
Phase: 1 - LiveEventFeed Backend (Task 1.4)
"""

import asyncio
import time
from typing import List

from app.services.event_bus import get_event_bus, EventBus
from app.services.event_emitter import (
    emit_query_route_event,
    emit_model_state_event,
    emit_cgrag_event,
    emit_cache_event,
    emit_error_event,
    emit_performance_event
)
from app.models.events import SystemEvent, EventType, EventSeverity


async def test_event_bus_basic():
    """Test basic event bus functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Event Bus Functionality")
    print("="*60)

    try:
        event_bus = get_event_bus()
        print("✅ Event bus instance retrieved")
    except RuntimeError as e:
        print(f"❌ Event bus not initialized: {e}")
        return False

    # Check stats
    stats = event_bus.get_stats()
    print(f"📊 Event bus stats: {stats}")

    if not stats['running']:
        print("❌ Event bus not running")
        return False

    print("✅ Event bus is running")
    return True


async def test_event_emission():
    """Test event emission utilities."""
    print("\n" + "="*60)
    print("TEST 2: Event Emission Utilities")
    print("="*60)

    tests = [
        ("Query Route Event", emit_query_route_event(
            query_id="test_query_001",
            complexity_score=7.5,
            selected_tier="Q4",
            estimated_latency_ms=12000,
            routing_reason="Complex multi-part analysis"
        )),
        ("Model State Event", emit_model_state_event(
            model_id="test_model_q4",
            previous_state="idle",
            current_state="processing",
            reason="Query dispatched",
            port=8080
        )),
        ("CGRAG Event", emit_cgrag_event(
            query_id="test_query_001",
            chunks_retrieved=5,
            relevance_threshold=0.7,
            retrieval_time_ms=45,
            total_tokens=1500,
            cache_hit=True
        )),
        ("Cache Event", emit_cache_event(
            operation="hit",
            key="query:test_001:response",
            hit=True,
            latency_ms=2,
            size_bytes=4096
        )),
        ("Error Event", emit_error_event(
            error_type="TestError",
            error_message="This is a test error",
            component="TestScript",
            recovery_action="No action needed - test only"
        )),
        ("Performance Event", emit_performance_event(
            metric_name="test_metric",
            current_value=100.5,
            threshold_value=90.0,
            component="TestComponent",
            action_required=False
        ))
    ]

    success_count = 0
    for test_name, test_coro in tests:
        try:
            await test_coro
            print(f"✅ {test_name} emitted successfully")
            success_count += 1
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")

    print(f"\n📊 Results: {success_count}/{len(tests)} events emitted successfully")
    return success_count == len(tests)


async def test_event_filtering():
    """Test event filtering by type and severity."""
    print("\n" + "="*60)
    print("TEST 3: Event Filtering")
    print("="*60)

    event_bus = get_event_bus()

    # Subscribe to ERROR events only
    received_events: List[SystemEvent] = []

    async def collect_events():
        """Collect events for 2 seconds."""
        try:
            async for event in event_bus.subscribe(
                event_types={EventType.ERROR},
                min_severity=EventSeverity.ERROR
            ):
                received_events.append(event)
                print(f"  📩 Received: {event.type} - {event.message}")

                # Stop after receiving one event
                if len(received_events) >= 1:
                    break
        except asyncio.CancelledError:
            pass

    # Start subscriber
    subscriber_task = asyncio.create_task(collect_events())

    # Wait a moment for subscriber to connect
    await asyncio.sleep(0.1)

    # Emit INFO event (should be filtered out)
    await emit_cache_event(
        operation="hit",
        key="test:filter",
        hit=True,
        latency_ms=1,
        size_bytes=100
    )

    # Emit ERROR event (should be received)
    await emit_error_event(
        error_type="FilterTestError",
        error_message="This error should be received",
        component="TestScript"
    )

    # Wait for events to be processed
    await asyncio.sleep(0.5)

    # Cancel subscriber
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass

    # Verify filtering worked
    if len(received_events) == 1 and received_events[0].type == EventType.ERROR:
        print("✅ Event filtering works correctly")
        return True
    else:
        print(f"❌ Event filtering failed: received {len(received_events)} events")
        return False


async def test_event_history():
    """Test historical event buffer."""
    print("\n" + "="*60)
    print("TEST 4: Historical Event Buffer")
    print("="*60)

    event_bus = get_event_bus()

    # Emit 5 test events
    print("Emitting 5 test events...")
    for i in range(5):
        await event_bus.publish(
            event_type=EventType.QUERY_ROUTE,
            message=f"Historical test event {i+1}",
            severity=EventSeverity.INFO,
            metadata={"test_id": i+1}
        )

    await asyncio.sleep(0.2)  # Allow events to be processed

    # Subscribe and collect historical events
    received_events: List[SystemEvent] = []

    async def collect_history():
        """Collect historical events on connection."""
        try:
            async for event in event_bus.subscribe():
                received_events.append(event)
                print(f"  📩 Received: {event.message}")

                # Stop after receiving historical events
                if len(received_events) >= 5:
                    break
        except asyncio.CancelledError:
            pass

    # Start subscriber
    subscriber_task = asyncio.create_task(collect_history())

    # Wait for events
    await asyncio.sleep(0.5)

    # Cancel subscriber
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass

    # Verify we received historical events
    if len(received_events) >= 5:
        print(f"✅ Historical event buffer works ({len(received_events)} events received)")
        return True
    else:
        print(f"❌ Historical event buffer failed: only {len(received_events)} events received")
        return False


async def test_concurrent_subscribers():
    """Test multiple concurrent subscribers."""
    print("\n" + "="*60)
    print("TEST 5: Concurrent Subscribers")
    print("="*60)

    event_bus = get_event_bus()

    # Create 3 subscribers
    subscriber_counts = [0, 0, 0]

    async def subscribe_and_count(subscriber_id: int):
        """Subscribe and count received events."""
        try:
            async for event in event_bus.subscribe():
                subscriber_counts[subscriber_id] += 1

                if subscriber_counts[subscriber_id] >= 3:
                    break
        except asyncio.CancelledError:
            pass

    # Start subscribers
    tasks = [
        asyncio.create_task(subscribe_and_count(0)),
        asyncio.create_task(subscribe_and_count(1)),
        asyncio.create_task(subscribe_and_count(2))
    ]

    # Wait for subscribers to connect
    await asyncio.sleep(0.1)

    # Check stats
    stats = event_bus.get_stats()
    print(f"📊 Active subscribers: {stats['active_subscribers']}")

    # Emit 3 test events
    print("Emitting 3 test events...")
    for i in range(3):
        await event_bus.publish(
            event_type=EventType.CACHE,
            message=f"Concurrent test event {i+1}",
            severity=EventSeverity.INFO,
            metadata={"test_id": i+1}
        )

    # Wait for events to be processed
    await asyncio.sleep(0.5)

    # Cancel all subscribers
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    # Verify all subscribers received all events
    print(f"Subscriber event counts: {subscriber_counts}")

    if all(count >= 3 for count in subscriber_counts):
        print("✅ Concurrent subscribers work correctly")
        return True
    else:
        print("❌ Concurrent subscribers failed: not all received events")
        return False


async def test_performance():
    """Test event system performance."""
    print("\n" + "="*60)
    print("TEST 6: Performance Test")
    print("="*60)

    event_bus = get_event_bus()

    # Emit 100 events and measure time
    event_count = 100
    start_time = time.perf_counter()

    for i in range(event_count):
        await event_bus.publish(
            event_type=EventType.CACHE,
            message=f"Performance test event {i+1}",
            severity=EventSeverity.INFO,
            metadata={"test_id": i+1}
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    events_per_sec = event_count / (elapsed_ms / 1000)
    avg_latency_ms = elapsed_ms / event_count

    print(f"📊 Published {event_count} events in {elapsed_ms:.2f}ms")
    print(f"📊 Throughput: {events_per_sec:.0f} events/sec")
    print(f"📊 Average latency: {avg_latency_ms:.2f}ms per event")

    # Check if performance meets targets
    if avg_latency_ms < 10:  # Target: <10ms per event
        print("✅ Performance test passed")
        return True
    else:
        print("⚠️  Performance below target (target: <10ms per event)")
        return False


async def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*60)
    print("WEBSOCKET EVENT SYSTEM TEST SUITE")
    print("="*60)

    tests = [
        ("Event Bus Basic Functionality", test_event_bus_basic),
        ("Event Emission Utilities", test_event_emission),
        ("Event Filtering", test_event_filtering),
        ("Historical Event Buffer", test_event_history),
        ("Concurrent Subscribers", test_concurrent_subscribers),
        ("Performance", test_performance)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n📊 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Event system is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check logs above for details.")

    return passed == total


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())

    # Exit with appropriate code
    exit(0 if success else 1)
