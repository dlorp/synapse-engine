/**
 * Log entry types for S.Y.N.A.P.S.E. ENGINE LogViewer component
 *
 * Defines TypeScript interfaces for system logs displayed in the LogViewer.
 * Logs are captured from WebSocket events (SystemEvent type) and displayed
 * with comprehensive filtering and terminal aesthetic styling.
 *
 * Author: Frontend Engineer
 */

/**
 * Log level enum matching backend EventSeverity
 */
export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

/**
 * Log entry structure
 *
 * Maps from backend SystemEvent to frontend log display format
 */
export interface LogEntry {
  /** ISO 8601 timestamp or Unix timestamp */
  timestamp: string | number;
  /** Log severity level */
  level: LogLevel;
  /** Logger source/component name (e.g., "cgrag", "query_route", "model_state") */
  source: string;
  /** Primary log message */
  message: string;
  /** Additional structured data (from SystemEvent metadata) */
  extra?: Record<string, unknown>;
}

/**
 * Log statistics for display in filter panel
 */
export interface LogStats {
  /** Total number of logs in buffer */
  total_logs: number;
  /** Count by log level */
  by_level: Record<LogLevel, number>;
  /** Buffer capacity */
  buffer_size: number;
  /** Oldest log timestamp */
  oldest_timestamp?: string;
  /** Newest log timestamp */
  newest_timestamp?: string;
}

/**
 * Log filter state
 */
export interface LogFilters {
  /** Filter by log level (null = all levels) */
  level: LogLevel | null;
  /** Filter by source/component (null = all sources) */
  source: string | null;
  /** Search text filter (case-insensitive) */
  searchText: string;
  /** Time range filter start (ISO 8601) */
  timeRangeStart: string | null;
  /** Time range filter end (ISO 8601) */
  timeRangeEnd: string | null;
}

/**
 * Log source information for filter dropdown
 */
export interface LogSource {
  /** Source identifier */
  name: string;
  /** Number of logs from this source */
  count: number;
}
