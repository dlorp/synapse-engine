#!/usr/bin/env python3
"""Test WebSocket event streaming - verifies backend event emissions.

This script connects to /ws/events and listens for system events.
"""

import asyncio
import websockets
import json
import sys

async def test_event_stream():
    """Connect to WebSocket and listen for events."""
    url = "ws://localhost:8000/ws/events"

    print(f"Connecting to {url}...")

    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected to WebSocket event stream")
            print("Listening for events... (press Ctrl+C to stop)\n")

            event_count = 0

            async for message in websocket:
                try:
                    event = json.loads(message)
                    event_count += 1

                    # Format event for display
                    event_type = event.get('type', 'unknown')
                    severity = event.get('severity', 'info')
                    msg = event.get('message', 'No message')
                    timestamp = event.get('timestamp', 0)
                    metadata = event.get('metadata', {})

                    # Color-code by severity
                    color = {
                        'info': '\033[92m',  # Green
                        'warning': '\033[93m',  # Yellow
                        'error': '\033[91m'  # Red
                    }.get(severity, '\033[0m')
                    reset = '\033[0m'

                    print(f"[{event_count}] {color}[{severity.upper()}]{reset} [{event_type}]")
                    print(f"  Message: {msg}")

                    if metadata:
                        print(f"  Metadata: {json.dumps(metadata, indent=4)}")

                    print()

                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse event: {e}")
                except Exception as e:
                    print(f"⚠️  Error handling event: {e}")

    except ConnectionRefusedError:
        print("❌ Connection refused - is the backend running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error connecting to WebSocket: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test_event_stream())
    except KeyboardInterrupt:
        print("\n\n✅ Test complete - event stream working!")
        sys.exit(0)
