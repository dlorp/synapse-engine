#!/usr/bin/env python3
"""Test script for active moderator system in Council Debate Mode.

This script tests the moderator interjection functionality by sending
test queries to the backend and checking if moderator intervenes when
models go off-topic.
"""

import requests
import time


def test_active_moderator(
    query: str,
    moderator_check_frequency: int = 2,
    max_turns: int = 6,
    expected_interjections: int = 0
):
    """
    Test active moderator with a specific query.

    Args:
        query: The debate question
        moderator_check_frequency: How often moderator checks (default: 2 turns)
        max_turns: Maximum debate turns
        expected_interjections: Expected number of interjections (for validation)
    """
    print(f"\n{'='*80}")
    print(f"Testing query: {query}")
    print(f"Moderator check frequency: {moderator_check_frequency}")
    print(f"Max turns: {max_turns}")
    print(f"{'='*80}\n")

    # Build request
    request_data = {
        "query": query,
        "mode": "council",
        "useContext": False,  # Disable context for cleaner test
        "useWebSearch": False,
        "councilAdversarial": True,  # Debate mode
        "councilModerator": True,  # Enable moderator
        "councilModeratorCheckFrequency": moderator_check_frequency,
        "councilMaxTurns": max_turns,
        "councilDynamicTermination": False,  # Disable early termination to see all turns
        "temperature": 0.7
    }

    # Send request
    print("Sending request to backend...")
    start_time = time.time()

    try:
        response = requests.post(
            "http://localhost:8000/api/query",
            json=request_data,
            timeout=300  # 5 minute timeout for debate
        )

        elapsed_time = time.time() - start_time

        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

        result = response.json()

        # Extract metadata
        metadata = result.get("metadata", {})
        council_turns = metadata.get("councilTurns", [])
        moderator_interjections = metadata.get("councilModeratorInterjections", 0)

        print(f"✅ Request completed in {elapsed_time:.2f}s")
        print("\n📊 Results:")
        print(f"  Total turns: {len(council_turns)}")
        print(f"  Moderator interjections: {moderator_interjections}")
        print(f"  Termination reason: {metadata.get('councilTerminationReason', 'N/A')}")

        # Show turn-by-turn breakdown
        print("\n📝 Turn-by-turn breakdown:")
        for i, turn in enumerate(council_turns, 1):
            speaker = turn.get("speakerId", "Unknown")
            content_preview = turn.get("content", "")[:100] + "..."

            if speaker == "MODERATOR":
                print(f"  Turn {i}: 🎓 MODERATOR INTERJECTION")
                print(f"    Content: {turn.get('content', '')[:200]}")
            else:
                print(f"  Turn {i}: {speaker}")
                print(f"    Preview: {content_preview}")

        # Validation
        print("\n✓ Validation:")
        if expected_interjections > 0:
            if moderator_interjections >= expected_interjections:
                print(f"  ✅ Got expected interjections (>= {expected_interjections})")
            else:
                print(f"  ❌ Expected >= {expected_interjections} interjections, got {moderator_interjections}")

        # Check if moderator turns exist in conversation
        moderator_turns = [t for t in council_turns if t.get("speakerId") == "MODERATOR"]
        if moderator_turns:
            print(f"  ✅ Found {len(moderator_turns)} moderator turns in conversation")
        else:
            print("  ⚠️  No moderator turns found (may be expected if debate stayed on track)")

        return True

    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after {elapsed_time:.2f}s")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    """Run test scenarios."""

    print("\n" + "="*80)
    print("Active Moderator System Test Suite")
    print("="*80)

    # Test 1: Simple query (should NOT require interjections)
    print("\n### Test 1: Simple Query (Moderator should NOT interject)")
    test_active_moderator(
        query="What is the capital of France?",
        moderator_check_frequency=2,
        max_turns=4,
        expected_interjections=0  # Expect NO interjections - debate should stay focused
    )

    time.sleep(2)  # Brief pause between tests

    # Test 2: Abstract query (may trigger interjection if models drift)
    print("\n### Test 2: Abstract Query (Moderator may interject)")
    test_active_moderator(
        query="Is artificial intelligence beneficial or harmful to society?",
        moderator_check_frequency=2,
        max_turns=8,
        expected_interjections=0  # No expectation, just observe
    )

    print("\n" + "="*80)
    print("Test suite completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
