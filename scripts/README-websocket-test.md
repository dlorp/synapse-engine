# WebSocket Test Page - User Guide

## Overview

The WebSocket test page (`test-websocket.html`) is a standalone diagnostic tool for testing the S.Y.N.A.P.S.E. ENGINE real-time event streaming system. It provides visual feedback on WebSocket connection health, event delivery, and ping/pong heartbeat cycles.

## Purpose

Use this tool to:
- **Verify WebSocket connectivity** - Confirm `/ws/events` endpoint is accessible
- **Test heartbeat mechanism** - Monitor ping/pong cycles every 30 seconds
- **Debug event streaming** - See real-time events as they're broadcast
- **Troubleshoot frontend issues** - Isolate WebSocket problems from React components
- **Monitor connection stability** - Track reconnection attempts and failures

## Quick Start

### 1. Start Docker Services

```bash
# From project root
docker compose up -d

# Verify services are running
docker compose ps
```

### 2. Open Test Page

```bash
# macOS
open http://localhost:5173/scripts/test-websocket.html

# Linux
xdg-open http://localhost:5173/scripts/test-websocket.html

# Or manually navigate to:
http://localhost:5173/scripts/test-websocket.html
```

### 3. Observe Connection

The page auto-connects on load. You should see:
- Status changes: "Connecting..." → "Connected" (green)
- Event count increments as events arrive
- Ping/pong count increments every 30 seconds

## Features

### Status Indicator

**Visual States:**
- 🟡 **Connecting** - Initial connection attempt (yellow border)
- 🟢 **Connected** - Active WebSocket connection (green border)
- 🔴 **Disconnected** - Connection lost or failed (red border)

### Statistics Dashboard

Three real-time metrics:

1. **EVENTS RECEIVED** - Total events received since page load
2. **RECONNECT ATTEMPTS** - Number of automatic reconnection attempts
3. **PING/PONG CYCLES** - Successful heartbeat cycles (increments every 30s)

### Control Buttons

- **Connect** - Manually initiate WebSocket connection
- **Disconnect** - Close WebSocket connection (code 1000)
- **Send Test Event** - Publish test event via API (appears in all clients)
- **Clear Events** - Reset event display (keeps connection active)

### Event Stream

Real-time scrolling event feed with:
- **Last 20 events** displayed (FIFO - newest at top)
- **Color-coded severity:**
  - 🔵 Blue border = Info
  - 🟡 Yellow border = Warning
  - 🔴 Red border = Error
- **Timestamps** - Human-readable time for each event
- **Event types** - [query_route], [model_state], [cgrag], etc.
- **Messages** - Human-readable event description

## Testing Scenarios

### Scenario 1: Basic Connectivity Test

**Goal:** Verify WebSocket endpoint is accessible

**Steps:**
1. Open test page
2. Page auto-connects on load
3. Verify status shows "Connected" (green)
4. Check browser console for connection logs

**Expected Result:**
```
Connecting to: ws://localhost:5173/ws/events
WebSocket connected
```

**Troubleshooting:**
- If status stays "Connecting" (yellow) → Backend not responding
- If status shows "Disconnected" (red) → Check Docker containers running
- Check backend logs: `docker compose logs -f synapse_core | grep websocket`

### Scenario 2: Heartbeat Test

**Goal:** Verify ping/pong mechanism works

**Steps:**
1. Connect to WebSocket
2. Wait 30 seconds (heartbeat interval)
3. Observe "PING/PONG CYCLES" counter increment

**Expected Result:**
- Counter increments from 0 → 1 after 30s
- No disconnections or reconnections
- Browser console shows: "Sending ping" → "Received pong"

**Troubleshooting:**
- If connection drops after 35s → Backend not sending pong responses
- If counter doesn't increment → Frontend not sending pings
- Check backend logs for ping/pong messages

### Scenario 3: Event Streaming Test

**Goal:** Verify events broadcast correctly

**Steps:**
1. Connect to WebSocket
2. Click "Send Test Event" button
3. Observe event appears in event stream

**Expected Result:**
- Event appears immediately in stream (within 100ms)
- All connected clients receive the event
- Event has timestamp, type, and message

**Alternative Method:**
```bash
# Send test event via curl
curl -X POST "http://localhost:5173/api/events/test?message=Hello+World"
```

**Troubleshooting:**
- If event doesn't appear → Event bus not broadcasting
- If event delayed (>1s) → Backpressure or slow client handling
- Check event bus stats: `curl http://localhost:5173/api/events/stats`

### Scenario 4: Reconnection Test

**Goal:** Verify auto-reconnect logic

**Steps:**
1. Connect to WebSocket
2. Stop backend: `docker compose stop synapse_core`
3. Observe status changes to "Disconnected"
4. Check "RECONNECT ATTEMPTS" counter increments
5. Restart backend: `docker compose start synapse_core`
6. Observe automatic reconnection

**Expected Result:**
- Status changes: Connected → Disconnected
- Reconnect attempts: 0 → 1 → 2 → 3 (with exponential backoff)
- After backend restart: Auto-reconnects and shows "Connected"
- Events resume streaming

**Troubleshooting:**
- If doesn't reconnect after 5 attempts → Max attempts reached (check console)
- If reconnects too fast (no backoff) → Exponential backoff not working
- Check browser console for reconnection logs

### Scenario 5: Multiple Client Test

**Goal:** Verify multiple simultaneous connections

**Steps:**
1. Open test page in 3 browser tabs
2. Verify all tabs show "Connected"
3. Click "Send Test Event" in one tab
4. Verify event appears in all 3 tabs

**Expected Result:**
- All tabs receive the same event simultaneously
- No connection drops or conflicts
- Event bus stats show 3 active subscribers

**Check Stats:**
```bash
curl http://localhost:5173/api/events/stats
# Expected: {"active_subscribers": 3, "queue_size": 0, "history_size": 100, "running": true}
```

**Troubleshooting:**
- If only some tabs receive event → Event bus filtering issue
- If connection drops on other tabs → Connection limit reached
- Check backend logs for subscriber count

## API Endpoints

### Test Event Publishing

**Endpoint:** `POST /api/events/test`

**Query Parameters:**
- `event_type` (optional) - Event type (default: `query_route`)
- `message` (optional) - Event message (default: `Test event from API`)

**Example:**
```bash
# Simple test event
curl -X POST "http://localhost:5173/api/events/test"

# Custom message
curl -X POST "http://localhost:5173/api/events/test?message=Custom+message"

# Custom type and message
curl -X POST "http://localhost:5173/api/events/test?event_type=error&message=Test+error"
```

**Response:**
```json
{
  "success": true,
  "event_type": "query_route",
  "message": "Test event from API"
}
```

### Event Bus Statistics

**Endpoint:** `GET /api/events/stats`

**Example:**
```bash
curl http://localhost:5173/api/events/stats
```

**Response:**
```json
{
  "active_subscribers": 2,
  "queue_size": 0,
  "history_size": 100,
  "running": true
}
```

**Fields:**
- `active_subscribers` - Number of connected WebSocket clients
- `queue_size` - Events waiting to be broadcast
- `history_size` - Events in historical buffer (sent to new connections)
- `running` - Event bus broadcast loop status

## Browser Console Commands

Open browser console (F12) and run:

```javascript
// Check WebSocket state
console.log('WebSocket state:', ws?.readyState);
// 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED

// Manually send ping
ws?.send(JSON.stringify({ type: 'ping' }));

// Check connection URL
console.log('WebSocket URL:', ws?.url);

// Force disconnect
disconnect();

// Force reconnect
connect();
```

## Common Issues

### Issue: Connection Immediately Closes

**Symptoms:**
- Status briefly shows "Connected" then "Disconnected"
- Infinite reconnection loop

**Causes:**
- Backend WebSocket endpoint not responding
- Nginx proxy misconfigured
- Port 8000 not accessible

**Solution:**
```bash
# Check backend health
curl http://localhost:8000/health/healthz

# Check backend logs
docker compose logs -f synapse_core | grep -i error

# Restart backend
docker compose restart synapse_core
```

### Issue: No Events Appearing

**Symptoms:**
- Connection stable ("Connected")
- Ping/pong working
- "Send Test Event" button does nothing

**Causes:**
- Event bus not running
- Event publishing failed
- Frontend not handling events correctly

**Solution:**
```bash
# Check event bus status
curl http://localhost:5173/api/events/stats

# Check if event bus is running
docker compose logs synapse_core | grep "Event bus"

# Try manual event publish
curl -X POST "http://localhost:5173/api/events/test?message=Debug"
```

### Issue: Ping/Pong Counter Not Incrementing

**Symptoms:**
- Connection stable
- No disconnections
- Counter stays at 0 after 30+ seconds

**Causes:**
- Heartbeat interval not starting
- Backend not responding to pings
- Frontend not parsing pong responses

**Solution:**
- Check browser console for "Sending ping" logs
- Check backend logs for ping/pong handling
- Verify backend code has JSON ping/pong handler

## Performance Expectations

- **Connection establishment:** <100ms
- **Event delivery latency:** <50ms (from publish to display)
- **Heartbeat interval:** 30 seconds (consistent)
- **Reconnection backoff:** 1s → 2s → 4s → 8s → 16s → 30s (max)
- **Max reconnect attempts:** 5 (then manual reconnect required)
- **Event buffer:** 100 events (historical events sent on connect)

## Terminal Aesthetic

The test page follows S.Y.N.A.P.S.E. ENGINE design principles:
- **Phosphor orange** (#ff9500) primary text and borders
- **Pure black** (#000) background
- **Cyan accents** (#00ffff) for stats and event types
- **Monospace fonts** (Courier New)
- **Terminal-style layout** with bordered panels

## Integration with LiveEventFeed

This test page uses the **same WebSocket protocol** as the `LiveEventFeed` React component:

**Shared Behavior:**
- Connects to `/ws/events`
- Sends JSON ping: `{"type": "ping"}`
- Expects JSON pong: `{"type": "pong"}`
- Receives events: `{timestamp, type, message, severity, metadata}`
- Auto-reconnects with exponential backoff
- 30-second heartbeat interval

**Differences:**
- Test page: 20-event buffer, test page: 8-event buffer
- Test page: Manual controls, LiveEventFeed: Automatic
- Test page: Detailed statistics, LiveEventFeed: Simple status indicator

## Related Files

- **Test Page:** `/home/user/synapse-engine/scripts/test-websocket.html`
- **Frontend Hook:** `/home/user/synapse-engine/frontend/src/hooks/useSystemEvents.ts`
- **Backend Endpoint:** `/home/user/synapse-engine/backend/app/routers/events.py`
- **Event Bus:** `/home/user/synapse-engine/backend/app/services/event_bus.py`
- **Vite Proxy:** `/home/user/synapse-engine/frontend/vite.config.ts`
- **Nginx Config:** `/home/user/synapse-engine/frontend/nginx.conf`

## Support

For issues or questions:
1. Check session notes: `/home/user/synapse-engine/SESSION_NOTES.md`
2. Review backend logs: `docker compose logs -f synapse_core`
3. Check event bus stats: `curl http://localhost:5173/api/events/stats`
4. Test backend health: `curl http://localhost:8000/health/healthz`
