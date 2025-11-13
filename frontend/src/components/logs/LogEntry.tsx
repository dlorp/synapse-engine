/**
 * LogEntry Component - Individual log entry display with expandable details
 *
 * Features:
 * - Color-coded by severity level (ERROR=red, WARNING=amber, INFO=cyan, DEBUG=gray)
 * - Expandable for extra metadata details
 * - Copy to clipboard functionality
 * - Terminal aesthetic with monospace font
 * - Timestamp formatting with millisecond precision
 *
 * Author: Frontend Engineer
 */

import React, { useState, useCallback } from 'react';
import { toast } from 'react-toastify';
import type { LogEntry as LogEntryType } from '@/types/logs';
import styles from './LogEntry.module.css';

export interface LogEntryProps {
  /** Log entry data */
  log: LogEntryType;
  /** Index in log list (for key generation) */
  index?: number;
}

/**
 * LogEntry - Displays a single log entry with expandable details
 */
export const LogEntry: React.FC<LogEntryProps> = ({ log, index = 0 }) => {
  const [expanded, setExpanded] = useState(false);

  /**
   * Get CSS class for log level color coding
   */
  const getLevelColor = useCallback((level: string): string => {
    switch (level) {
      case 'ERROR':
      case 'CRITICAL':
        return styles.levelError;
      case 'WARNING':
        return styles.levelWarning;
      case 'INFO':
        return styles.levelInfo;
      case 'DEBUG':
        return styles.levelDebug;
      default:
        return styles.levelDefault;
    }
  }, []);

  /**
   * Format timestamp with millisecond precision
   */
  const formatTimestamp = useCallback((timestamp: string | number): string => {
    const date = typeof timestamp === 'number' ? new Date(timestamp) : new Date(timestamp);

    if (isNaN(date.getTime())) {
      return String(timestamp);
    }

    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });
  }, []);

  /**
   * Copy log entry to clipboard
   */
  const handleCopy = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();

      const text = `[${log.timestamp}] [${log.level}] [${log.source}] ${log.message}`;

      if (navigator.clipboard) {
        navigator.clipboard
          .writeText(text)
          .then(() => {
            toast.success('✓ Log entry copied to clipboard', {
              autoClose: 2000,
              position: 'bottom-right',
            });
          })
          .catch((err) => {
            console.error('Failed to copy log entry:', err);
            toast.error('Failed to copy to clipboard', {
              autoClose: 2000,
              position: 'bottom-right',
            });
          });
      } else {
        // Fallback for browsers without clipboard API
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
          document.execCommand('copy');
          toast.success('✓ Log entry copied to clipboard', {
            autoClose: 2000,
            position: 'bottom-right',
          });
        } catch (err) {
          console.error('Failed to copy log entry:', err);
          toast.error('Failed to copy to clipboard', {
            autoClose: 2000,
            position: 'bottom-right',
          });
        }
        document.body.removeChild(textarea);
      }
    },
    [log]
  );

  /**
   * Toggle expanded state
   */
  const toggleExpanded = useCallback(() => {
    if (log.extra && Object.keys(log.extra).length > 0) {
      setExpanded((prev) => !prev);
    }
  }, [log.extra]);

  const hasExtra = log.extra && Object.keys(log.extra).length > 0;

  return (
    <div
      className={`${styles.logEntry} ${getLevelColor(log.level)} ${
        hasExtra ? styles.expandable : ''
      }`}
      data-log-index={index}
    >
      <div className={styles.logHeader} onClick={toggleExpanded}>
        <span className={styles.timestamp}>{formatTimestamp(log.timestamp)}</span>
        <span className={styles.level}>[{log.level}]</span>
        <span className={styles.source}>[{log.source}]</span>
        <span className={styles.message}>{log.message}</span>
        <div className={styles.actions}>
          {hasExtra && (
            <button
              className={styles.expandButton}
              onClick={toggleExpanded}
              aria-label={expanded ? 'Collapse details' : 'Expand details'}
              aria-expanded={expanded}
            >
              {expanded ? '▼' : '▶'}
            </button>
          )}
          <button
            className={styles.copyButton}
            onClick={handleCopy}
            aria-label="Copy log entry to clipboard"
            title="Copy to clipboard"
          >
            ⎘
          </button>
        </div>
      </div>

      {expanded && hasExtra && (
        <div className={styles.logExtra}>
          <div className={styles.extraHeader}>METADATA:</div>
          {Object.entries(log.extra).map(([key, value]) => (
            <div key={key} className={styles.extraItem}>
              <span className={styles.extraKey}>{key}:</span>
              <span className={styles.extraValue}>
                {typeof value === 'object' && value !== null
                  ? JSON.stringify(value, null, 2)
                  : String(value)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
