/**
 * LogFilters Component - Comprehensive log filtering controls
 *
 * Features:
 * - Level filter dropdown (DEBUG, INFO, WARNING, ERROR, CRITICAL)
 * - Source/component filter dropdown
 * - Search text input (case-insensitive)
 * - Statistics display (total logs, counts by level)
 * - Action buttons (refresh, export, clear)
 * - Auto-scroll toggle
 * - Terminal aesthetic with phosphor orange accents
 *
 * Author: Frontend Engineer
 */

import React, { useMemo } from 'react';
import { Input } from '@/components/terminal/Input';
import { Button } from '@/components/terminal/Button';
import type { LogLevel, LogStats } from '@/types/logs';
import styles from './LogFilters.module.css';

export interface LogFiltersProps {
  /** Current level filter (null = all levels) */
  levelFilter: LogLevel | null;
  /** Set level filter */
  setLevelFilter: (level: LogLevel | null) => void;
  /** Current source filter (null = all sources) */
  sourceFilter: string | null;
  /** Set source filter */
  setSourceFilter: (source: string | null) => void;
  /** Available log sources */
  sources: string[];
  /** Search text */
  searchText: string;
  /** Set search text */
  setSearchText: (text: string) => void;
  /** Log statistics */
  stats: LogStats | null;
  /** Clear logs handler */
  onClear: () => void;
  /** Export logs handler */
  onExport: () => void;
  /** Refresh logs handler */
  onRefresh: () => void;
  /** Auto-scroll enabled */
  autoScroll: boolean;
  /** Set auto-scroll */
  setAutoScroll: (enabled: boolean) => void;
  /** Number of filtered logs currently displayed */
  filteredCount?: number;
}

/**
 * LogFilters - Filter controls and statistics for LogViewer
 */
export const LogFilters: React.FC<LogFiltersProps> = ({
  levelFilter,
  setLevelFilter,
  sourceFilter,
  setSourceFilter,
  sources,
  searchText,
  setSearchText,
  stats,
  onClear,
  onExport,
  onRefresh,
  autoScroll,
  setAutoScroll,
  filteredCount,
}) => {
  const levels: Array<LogLevel | null> = [null, 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

  /**
   * Format stats for display
   */
  const statsDisplay = useMemo(() => {
    if (!stats) {
      return null;
    }

    const entries = Object.entries(stats.by_level || {})
      .filter(([_, count]) => count > 0)
      .map(([level, count]) => ({ level, count }));

    return entries;
  }, [stats]);

  return (
    <div className={styles.filters}>
      {/* Filter Controls Row */}
      <div className={styles.filterRow}>
        <div className={styles.filterGroup}>
          <label htmlFor="level-filter" className={styles.filterLabel}>
            LEVEL:
          </label>
          <select
            id="level-filter"
            value={levelFilter || ''}
            onChange={(e) => setLevelFilter((e.target.value as LogLevel) || null)}
            className={styles.select}
            aria-label="Filter by log level"
          >
            {levels.map((level) => (
              <option key={level || 'all'} value={level || ''}>
                {level || 'ALL LEVELS'}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.filterGroup}>
          <label htmlFor="source-filter" className={styles.filterLabel}>
            SOURCE:
          </label>
          <select
            id="source-filter"
            value={sourceFilter || ''}
            onChange={(e) => setSourceFilter(e.target.value || null)}
            className={styles.select}
            aria-label="Filter by log source"
          >
            <option value="">ALL SOURCES</option>
            {sources.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.filterGroup}>
          <label htmlFor="search-text" className={styles.filterLabel}>
            SEARCH:
          </label>
          <input
            id="search-text"
            type="text"
            placeholder="Search logs..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className={styles.searchInput}
            aria-label="Search log messages"
          />
        </div>

        <div className={styles.checkboxGroup}>
          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              aria-label="Enable auto-scroll to bottom"
            />
            <span className={styles.checkboxLabel}>AUTO-SCROLL</span>
          </label>
        </div>
      </div>

      {/* Statistics Row */}
      {stats && (
        <div className={styles.statsRow}>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>TOTAL:</span>
            <span className={styles.statValue}>{stats.total_logs}</span>
          </div>

          {filteredCount !== undefined && filteredCount !== stats.total_logs && (
            <div className={styles.statItem}>
              <span className={styles.statLabel}>FILTERED:</span>
              <span className={styles.statValue}>{filteredCount}</span>
            </div>
          )}

          {statsDisplay &&
            statsDisplay.map(({ level, count }) => (
              <div key={level} className={styles.statItem}>
                <span className={`${styles.statLabel} ${styles[`level${level}`]}`}>
                  {level}:
                </span>
                <span className={styles.statValue}>{count}</span>
              </div>
            ))}

          {stats.buffer_size && (
            <div className={styles.statItem}>
              <span className={styles.statLabel}>BUFFER:</span>
              <span className={styles.statValue}>{stats.buffer_size}</span>
            </div>
          )}
        </div>
      )}

      {/* Actions Row */}
      <div className={styles.actionsRow}>
        <Button
          variant="secondary"
          size="sm"
          onClick={onRefresh}
          aria-label="Refresh logs"
          title="Refresh logs"
        >
          ⟳ REFRESH
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={onExport}
          aria-label="Export logs to file"
          title="Export logs to file"
        >
          ↓ EXPORT
        </Button>
        <Button
          variant="danger"
          size="sm"
          onClick={onClear}
          aria-label="Clear all logs"
          title="Clear all logs"
        >
          ✕ CLEAR
        </Button>
      </div>
    </div>
  );
};
