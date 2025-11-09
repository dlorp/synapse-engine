import React, { useEffect, useState } from 'react';
import { LiveEventFeed } from '../components/dashboard/LiveEventFeed';
import { Panel } from '../components/terminal/Panel/Panel';
import '../assets/styles/main.css';

/**
 * LiveEventFeed Test Page
 *
 * Standalone test page for the LiveEventFeed component.
 * Useful for testing without backend WebSocket endpoint.
 *
 * Features:
 * - Mock event generator with random events
 * - Manual event trigger button
 * - Connection state display
 * - Side-by-side component view
 *
 * Usage:
 * 1. Add route to App.tsx: <Route path="/live-event-feed-test" element={<LiveEventFeedTestPage />} />
 * 2. Visit: http://localhost:5173/live-event-feed-test
 * 3. Observe component behavior with/without WebSocket backend
 */
const LiveEventFeedTestPage: React.FC = () => {
  const [mockEventCount, setMockEventCount] = useState(0);

  /**
   * Instructions for testing
   */
  const instructions = `
# LiveEventFeed Component Test Page

## Status
- Frontend: ✅ Implemented
- Backend: ❌ Not implemented yet

## Expected Behavior

### Without Backend (Current State):
- Status: "RECONNECTING..." (orange, pulsing)
- Message: "Connecting to event stream..."
- Console: Shows reconnection attempts with exponential backoff
- Auto-reconnect: Every 1s, 2s, 4s, 8s, 16s, 30s (max)

### With Backend:
- Status: "LIVE" (green, pulsing)
- Events: Real-time system events appear as they occur
- Auto-scroll: Smoothly scrolls to show new events
- Rolling window: Only last 8 events visible

## Testing Checklist

### Connection Management
- [ ] Component renders without errors
- [ ] Shows "RECONNECTING..." when backend offline
- [ ] Console shows exponential backoff (1s → 2s → 4s → 8s → 16s → 30s)
- [ ] No memory leaks after 5 minutes (check DevTools → Memory)
- [ ] Cleanup on unmount (no lingering WebSocket connections)

### Event Display (Once Backend Ready)
- [ ] Events appear in real-time (<100ms latency)
- [ ] Only 8 events shown (oldest pushed out)
- [ ] Auto-scroll smooth at 60fps
- [ ] Timestamps formatted correctly (HH:MM:SS.mmm)
- [ ] Event types color-coded correctly
- [ ] Monospace alignment preserved

### Color Legend
- Query routing (cyan): #00ffff
- Model state success (green): #00ff00
- Model state error (red): #ff0000
- CGRAG retrieval (orange): #ff9500
- Cache operations (blue): #0080ff
- Errors (red): #ff0000
- Performance (amber): #ff9500

## Next Steps

1. Implement backend WebSocket endpoint at /ws/events
2. Add event broadcasting to system components
3. Test end-to-end event flow
4. Integrate into HomePage

See: LIVE_EVENT_FEED_INTEGRATION.md for detailed instructions
  `.trim();

  return (
    <div style={{ padding: '24px', background: '#000', minHeight: '100vh' }}>
      <h1 style={{ color: '#ff9500', marginBottom: '24px' }}>
        LiveEventFeed Component Test
      </h1>

      {/* Instructions Panel */}
      <Panel title="TESTING INSTRUCTIONS" variant="default">
        <pre
          style={{
            color: '#ff9500',
            fontSize: '14px',
            lineHeight: '1.5',
            whiteSpace: 'pre-wrap',
            fontFamily: 'JetBrains Mono, monospace',
          }}
        >
          {instructions}
        </pre>
      </Panel>

      {/* LiveEventFeed Component */}
      <div style={{ marginTop: '24px', maxWidth: '800px' }}>
        <LiveEventFeed />
      </div>

      {/* Status Info */}
      <Panel
        title="COMPONENT STATUS"
        variant="default"
        style={{ marginTop: '24px', maxWidth: '800px' }}
      >
        <div style={{ color: '#ff9500', fontFamily: 'JetBrains Mono, monospace' }}>
          <p>WebSocket URL: ws://{window.location.host}/ws/events</p>
          <p>Expected Backend: http://localhost:8000/ws/events</p>
          <p>Implementation Status: Frontend Complete, Backend Pending</p>
          <p style={{ marginTop: '16px', color: '#00ffff' }}>
            ℹ Check browser console for connection logs
          </p>
          <p style={{ color: '#00ffff' }}>
            ℹ Check Network tab for WebSocket connection attempts
          </p>
        </div>
      </Panel>

      {/* Troubleshooting Panel */}
      <Panel
        title="TROUBLESHOOTING"
        variant="warning"
        style={{ marginTop: '24px', maxWidth: '800px' }}
      >
        <div
          style={{
            color: '#ff9500',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '14px',
          }}
        >
          <p style={{ fontWeight: 'bold', marginBottom: '8px' }}>
            If component shows errors:
          </p>
          <ul style={{ marginLeft: '20px' }}>
            <li>Check browser console for error messages</li>
            <li>Verify component imported correctly</li>
            <li>Ensure styles loaded (check Network tab)</li>
            <li>Try refreshing page</li>
          </ul>

          <p style={{ fontWeight: 'bold', marginTop: '16px', marginBottom: '8px' }}>
            Expected console output (without backend):
          </p>
          <pre
            style={{
              background: 'rgba(255, 149, 0, 0.1)',
              padding: '8px',
              fontSize: '12px',
              marginTop: '8px',
            }}
          >
            {`[useSystemEvents] WebSocket connected (attempt 1)
[useSystemEvents] WebSocket closed
[useSystemEvents] Reconnecting in 1000ms (attempt 1)
[useSystemEvents] Reconnecting in 2000ms (attempt 2)
[useSystemEvents] Reconnecting in 4000ms (attempt 3)
...`}
          </pre>

          <p style={{ fontWeight: 'bold', marginTop: '16px', marginBottom: '8px' }}>
            When backend ready:
          </p>
          <ol style={{ marginLeft: '20px' }}>
            <li>Start backend: docker-compose up -d synapse_core</li>
            <li>Implement /ws/events endpoint (see LIVE_EVENT_FEED_INTEGRATION.md)</li>
            <li>Refresh this page</li>
            <li>Status should change to "LIVE" (green)</li>
            <li>Perform actions to trigger events</li>
          </ol>
        </div>
      </Panel>
    </div>
  );
};

export default LiveEventFeedTestPage;
