import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * System event types for S.Y.N.A.P.S.E. ENGINE
 */
export type SystemEventType =
  | 'query_route'
  | 'model_state'
  | 'cgrag'
  | 'cache'
  | 'error'
  | 'performance';

/**
 * Event severity levels
 */
export type EventSeverity = 'info' | 'warning' | 'error';

/**
 * System event structure
 */
export interface SystemEvent {
  timestamp: number;
  type: SystemEventType;
  message: string;
  severity?: EventSeverity;
}

/**
 * WebSocket connection states
 */
type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

/**
 * Hook return type
 */
export interface UseSystemEventsReturn {
  events: SystemEvent[];
  connected: boolean;
  connectionState: ConnectionState;
  error: Error | null;
  reconnect: () => void;
}

/**
 * Custom React hook for WebSocket-based system event stream
 *
 * Features:
 * - Auto-reconnect with exponential backoff (max 30s delay)
 * - Heartbeat ping/pong to detect dead connections (30s interval)
 * - Rolling buffer of last 8 events (FIFO queue)
 * - Graceful error handling with fallback UI state
 * - Automatic cleanup on unmount
 *
 * WebSocket Protocol:
 * - Server sends events as JSON messages
 * - Client sends "ping" every 30s, expects "pong" response
 * - Reconnect on disconnect with exponential backoff
 *
 * @param url - WebSocket URL (default: /ws/events via nginx proxy)
 * @param maxEvents - Maximum events to keep in buffer (default: 8)
 * @returns {UseSystemEventsReturn} Events state and connection info
 */
export const useSystemEvents = (
  url: string = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/events`,
  maxEvents: number = 8
): UseSystemEventsReturn => {
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
  const [error, setError] = useState<Error | null>(null);

  // Refs for stable references across renders
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Connect to WebSocket with exponential backoff
   */
  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'Reconnecting');
      wsRef.current = null;
    }

    // Clear all timers
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }

    // Update connection state
    if (reconnectAttemptsRef.current === 0) {
      setConnectionState('connecting');
    } else {
      setConnectionState('reconnecting');
    }

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[useSystemEvents] WebSocket connected');
        setConnectionState('connected');
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Start heartbeat (inline to avoid dependency)
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }

        heartbeatIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            try {
              wsRef.current.send(JSON.stringify({ type: 'ping' }));

              heartbeatTimeoutRef.current = setTimeout(() => {
                console.warn('[useSystemEvents] No pong received, closing connection');
                wsRef.current?.close(1000, 'Heartbeat timeout');
              }, 5000);
            } catch (err) {
              console.error('[useSystemEvents] Heartbeat ping failed:', err);
            }
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle pong response
          if (data.type === 'pong') {
            if (heartbeatTimeoutRef.current) {
              clearTimeout(heartbeatTimeoutRef.current);
              heartbeatTimeoutRef.current = null;
            }
            return;
          }

          // Validate event structure
          if (!data.type || !data.message) {
            console.warn('[useSystemEvents] Invalid event format:', data);
            return;
          }

          // Add timestamp if not present
          const systemEvent: SystemEvent = {
            timestamp: data.timestamp || Date.now(),
            type: data.type,
            message: data.message,
            severity: data.severity || 'info',
          };

          // Add to events buffer (inline to avoid dependency)
          setEvents((prev) => {
            const updated = [...prev, systemEvent];
            return updated.slice(-maxEvents);
          });
        } catch (err) {
          console.error('[useSystemEvents] Failed to parse message:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('[useSystemEvents] WebSocket error:', err);
        setError(new Error('WebSocket connection error'));
      };

      ws.onclose = (closeEvent) => {
        console.log(`[useSystemEvents] WebSocket closed (code: ${closeEvent.code}, reason: ${closeEvent.reason})`);
        setConnectionState('disconnected');

        // Clear timers
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }
        if (heartbeatTimeoutRef.current) {
          clearTimeout(heartbeatTimeoutRef.current);
          heartbeatTimeoutRef.current = null;
        }

        // Only reconnect if not a normal closure
        if (closeEvent.code !== 1000) {
          // Reconnect with exponential backoff (max 30s)
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          console.log(`[useSystemEvents] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else {
          console.log('[useSystemEvents] Normal closure, not reconnecting');
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[useSystemEvents] Failed to create WebSocket:', err);
      setError(err as Error);
      setConnectionState('disconnected');
    }
  }, [url, maxEvents]);

  // Initialize connection on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      console.log('[useSystemEvents] Cleaning up WebSocket');

      // Clear all timers
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
      if (heartbeatTimeoutRef.current) {
        clearTimeout(heartbeatTimeoutRef.current);
        heartbeatTimeoutRef.current = null;
      }

      // Close WebSocket with normal closure
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
        wsRef.current = null;
      }
    };
  }, [connect]);

  // Manual reconnect function
  const reconnect = useCallback(() => {
    // Clear existing connection and timers
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual reconnect');
      wsRef.current = null;
    }

    // Reset reconnect attempts for fresh start
    reconnectAttemptsRef.current = 0;

    // Reconnect immediately
    connect();
  }, [connect]);

  return {
    events,
    connected: connectionState === 'connected',
    connectionState,
    error,
    reconnect, // Expose manual reconnect function
  };
};
