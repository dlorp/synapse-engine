/**
 * LogViewer Component - Comprehensive system log viewer with real-time updates
 *
 * Features:
 * - Real-time log streaming via WebSocket /ws/events
 * - Comprehensive filtering: level, source, search text
 * - Auto-scroll to bottom (pause on user scroll)
 * - Color-coded log levels (ERROR=red, WARNING=amber, INFO=cyan, DEBUG=gray)
 * - Expandable log entries for full metadata
 * - Copy to clipboard functionality
 * - Clear logs and export to file
 * - Terminal aesthetic with phosphor orange accents
 *
 * Integration:
 * - Uses SystemEventsContext for WebSocket events
 * - Converts SystemEvent to LogEntry format
 * - Maintains rolling buffer of logs (configurable max)
 *
 * Author: Frontend Engineer
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { AsciiPanel } from '@/components/terminal/AsciiPanel';
import { useSystemEventsContext } from '@/contexts/SystemEventsContext';
import { LogEntry as LogEntryComponent } from './LogEntry';
import { LogFilters } from './LogFilters';
import type { LogEntry, LogLevel, LogStats } from '@/types/logs';
import styles from './LogViewer.module.css';

export interface LogViewerProps {
  /** Model IDs for context (currently not used, reserved for future filtering) */
  modelIds?: string[];
  /** Maximum logs to display (default 500) */
  maxLines?: number;
}

/**
 * LogViewer - Main log viewer component with real-time updates and filtering
 */
export const LogViewer: React.FC<LogViewerProps> = ({ maxLines = 500 }) => {
  const { events } = useSystemEventsContext();

  // Log state
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);

  // Filter state
  const [levelFilter, setLevelFilter] = useState<LogLevel | null>(null);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [searchText, setSearchText] = useState('');

  // UI state
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  /**
   * Convert SystemEvent to LogEntry format
   */
  const systemEventToLogEntry = useCallback((event: any): LogEntry => {
    // Map SystemEvent severity to LogLevel
    const severityToLevel = (severity?: string): LogLevel => {
      if (!severity) return 'INFO';
      const normalized = severity.toUpperCase();
      if (normalized === 'ERROR') return 'ERROR';
      if (normalized === 'WARNING') return 'WARNING';
      if (normalized === 'INFO') return 'INFO';
      return 'DEBUG';
    };

    return {
      timestamp: event.timestamp || Date.now(),
      level: severityToLevel(event.severity),
      source: event.type || 'system',
      message: event.message || 'No message',
      extra: event.metadata || {},
    };
  }, []);

  /**
   * Process new WebSocket events and convert to logs
   */
  useEffect(() => {
    if (events.length === 0) return;

    // Get the most recent event
    const latestEvent = events[events.length - 1];

    // Convert to log entry
    const logEntry = systemEventToLogEntry(latestEvent);

    // Add to logs buffer (FIFO with maxLines limit)
    setLogs((prev) => {
      const updated = [...prev, logEntry];
      return updated.slice(-maxLines);
    });
  }, [events, maxLines, systemEventToLogEntry]);

  /**
   * Extract unique sources from logs
   */
  const sources = useMemo(() => {
    const sourceSet = new Set<string>();
    logs.forEach((log) => sourceSet.add(log.source));
    return Array.from(sourceSet).sort();
  }, [logs]);

  /**
   * Calculate log statistics
   */
  const stats: LogStats = useMemo(() => {
    const byLevel: Record<LogLevel, number> = {
      DEBUG: 0,
      INFO: 0,
      WARNING: 0,
      ERROR: 0,
      CRITICAL: 0,
    };

    logs.forEach((log) => {
      if (log.level in byLevel) {
        byLevel[log.level]++;
      }
    });

    return {
      total_logs: logs.length,
      by_level: byLevel,
      buffer_size: maxLines,
      oldest_timestamp:
        logs.length > 0 ? String(logs[0]?.timestamp) : undefined,
      newest_timestamp:
        logs.length > 0 ? String(logs[logs.length - 1]?.timestamp) : undefined,
    };
  }, [logs, maxLines]);

  /**
   * Apply filters to logs
   */
  useEffect(() => {
    let filtered = [...logs];

    // Level filter
    if (levelFilter) {
      filtered = filtered.filter((log) => log.level === levelFilter);
    }

    // Source filter
    if (sourceFilter) {
      filtered = filtered.filter((log) => log.source === sourceFilter);
    }

    // Search text filter (case-insensitive)
    if (searchText.trim()) {
      const search = searchText.toLowerCase();
      filtered = filtered.filter((log) =>
        log.message.toLowerCase().includes(search)
      );
    }

    setFilteredLogs(filtered);
  }, [logs, levelFilter, sourceFilter, searchText]);

  /**
   * Auto-scroll to bottom when new logs arrive
   */
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll]);

  /**
   * Detect user scroll and pause auto-scroll if scrolled up
   */
  const handleScroll = useCallback(() => {
    if (!logContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;

    setAutoScroll(isAtBottom);
  }, []);

  /**
   * Clear all logs
   */
  const handleClearLogs = useCallback(() => {
    setLogs([]);
    setFilteredLogs([]);
  }, []);

  /**
   * Export logs to text file
   */
  const handleExportLogs = useCallback(() => {
    const content = filteredLogs
      .map(
        (log) =>
          `[${log.timestamp}] [${log.level}] [${log.source}] ${log.message}`
      )
      .join('\n');

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `synapse-logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredLogs]);

  /**
   * Refresh logs (no-op since we're using WebSocket, but included for consistency)
   */
  const handleRefreshLogs = useCallback(() => {
    // No-op: logs are already streaming in real-time
    // Could potentially fetch historical logs from API in future
    console.log('[LogViewer] Refresh requested (no-op in WebSocket mode)');
  }, []);

  /**
   * Scroll to bottom manually
   */
  const handleScrollToBottom = useCallback(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
      setAutoScroll(true);
    }
  }, []);

  return (
    <AsciiPanel title="SYSTEM LOGS" className={styles.logViewer}>
      <LogFilters
        levelFilter={levelFilter}
        setLevelFilter={setLevelFilter}
        sourceFilter={sourceFilter}
        setSourceFilter={setSourceFilter}
        sources={sources}
        searchText={searchText}
        setSearchText={setSearchText}
        stats={stats}
        onClear={handleClearLogs}
        onExport={handleExportLogs}
        onRefresh={handleRefreshLogs}
        autoScroll={autoScroll}
        setAutoScroll={setAutoScroll}
        filteredCount={filteredLogs.length}
      />

      <div
        ref={logContainerRef}
        className={styles.logContainer}
        onScroll={handleScroll}
        role="log"
        aria-live="polite"
        aria-label="System logs"
      >
        {filteredLogs.length === 0 ? (
          <div className={styles.emptyState}>
            {logs.length === 0
              ? 'NO LOGS YET - WAITING FOR EVENTS...'
              : 'NO LOGS MATCHING FILTERS'}
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <LogEntryComponent
              key={`${log.timestamp}-${index}`}
              log={log}
              index={index}
            />
          ))
        )}
      </div>

      {!autoScroll && (
        <button
          className={styles.scrollToBottom}
          onClick={handleScrollToBottom}
          aria-label="Scroll to bottom"
        >
          ↓ SCROLL TO BOTTOM ({filteredLogs.length - Math.floor((logContainerRef.current?.scrollTop || 0) / 30)} NEW)
        </button>
      )}
    </AsciiPanel>
  );
};
