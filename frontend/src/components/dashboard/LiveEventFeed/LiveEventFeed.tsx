import React, { useEffect, useRef } from 'react';
import { AsciiPanel } from '@/components/terminal';
import { useSystemEventsContext } from '../../../contexts/SystemEventsContext';
import type { SystemEvent } from '../../../hooks/useSystemEvents';
import styles from './LiveEventFeed.module.css';

/**
 * LiveEventFeed Component
 *
 * Real-time system event stream with 8-event rolling window and WebSocket updates.
 *
 * Features:
 * - 8-event FIFO queue (oldest events pushed out)
 * - Color-coded event types (query_route, model_state, cgrag, cache, error, performance)
 * - Auto-scroll with smooth 60fps animation
 * - WebSocket connection with auto-reconnect
 * - Monospace font for timestamp alignment
 * - Connection status indicator
 *
 * Event Format: [HH:MM:SS.mmm] [TYPE] Message
 *
 * Color Legend:
 * - Query routing: Cyan (#00ffff)
 * - Model state: Green (#00ff00) / Red (#ff0000)
 * - CGRAG retrieval: Orange (#ff9500)
 * - Cache operations: Blue (#0080ff)
 * - Errors: Red (#ff0000)
 * - Performance: Amber (#ff9500)
 *
 * @component
 */
export const LiveEventFeed: React.FC = () => {
  const { events, connected, connectionState, error, reconnect } = useSystemEventsContext();
  const contentRef = useRef<HTMLDivElement>(null);

  /**
   * Auto-scroll to bottom when new events arrive
   * Uses smooth scrolling for 60fps animation
   */
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTo({
        top: contentRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [events]);

  /**
   * Format timestamp as HH:MM:SS.mmm
   */
  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    const milliseconds = date.getMilliseconds().toString().padStart(3, '0');
    return `${hours}:${minutes}:${seconds}.${milliseconds}`;
  };

  /**
   * Format event type label for display
   */
  const formatEventType = (type: string): string => {
    const typeMap: Record<string, string> = {
      query_route: 'ROUTE',
      model_state: 'MODEL',
      cgrag: 'CGRAG',
      cache: 'CACHE',
      error: 'ERROR',
      performance: 'PERF',
      pipeline_stage_start: 'PIPE-START',
      pipeline_stage_complete: 'PIPE-DONE',
      pipeline_stage_failed: 'PIPE-FAIL',
      pipeline_complete: 'COMPLETE',
      pipeline_failed: 'FAILED',
      topology_health_update: 'HEALTH',
      topology_dataflow_update: 'FLOW',
      log: 'LOG',
    };
    return typeMap[type] || type.toUpperCase();
  };

  /**
   * Get CSS class for event type
   */
  const getEventTypeClass = (event: SystemEvent): string => {
    // Use severity for model_state events
    if (event.type === 'model_state') {
      return event.message.includes('ACTIVE') || event.message.includes('IDLE')
        ? 'model-success'
        : 'model-error';
    }
    return event.type.replace('_', '-');
  };

  /**
   * Get connection status with inline reconnect button
   */
  const getConnectionStatus = () => {
    if (connectionState === 'connected') {
      return <span className={styles.statusConnected}>STATUS: LIVE</span>;
    } else if (connectionState === 'connecting') {
      return <span className={styles.statusConnecting}>STATUS: CONNECTING</span>;
    } else if (connectionState === 'reconnecting') {
      return <span className={styles.statusReconnecting}>STATUS: RECONNECTING</span>;
    } else {
      return (
        <span className={styles.statusDisconnected}>
          STATUS: DISCONNECTED
          <button
            onClick={reconnect}
            className={styles.reconnectButtonInline}
            aria-label="Reconnect to event stream"
            title="Click to reconnect"
          >
            <span className={styles.glowIcon}>⟲</span>
          </button>
        </span>
      );
    }
  };

  return (
    <AsciiPanel
      title="SYSTEM EVENT STREAM"
      titleRight={getConnectionStatus()}
      variant="default"
      className={styles.panel}
    >
      {/* Error state */}
      {error && (
        <div className={styles.error}>
          <span className={styles.errorIcon}>⚠</span> Connection Error: {error.message}
        </div>
      )}

      {/* Event list */}
      <div ref={contentRef} className={styles.content}>
        {events.length === 0 ? (
          <div className={styles.empty}>
            {connected
              ? 'Waiting for system events...'
              : 'Connecting to event stream...'}
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={`${event.timestamp}-${index}`}
              className={`${styles.event} ${styles[getEventTypeClass(event)]}`}
            >
              <span className={styles.timestamp}>[{formatTimestamp(event.timestamp)}]</span>
              <span className={styles.type}>[{formatEventType(event.type)}]</span>
              <span className={styles.message}>{event.message}</span>
            </div>
          ))
        )}
      </div>
    </AsciiPanel>
  );
};
