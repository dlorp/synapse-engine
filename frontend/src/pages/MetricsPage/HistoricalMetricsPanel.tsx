/**
 * HistoricalMetricsPanel - Collapsible lifetime/historical metrics panel
 *
 * Displays aggregate system metrics since system startup:
 * - Total requests/errors
 * - All-time error rate and latency percentiles
 * - Cache performance metrics
 * - System uptime
 *
 * Features:
 * - Collapsible design (default: collapsed)
 * - Click header to toggle expand/collapse
 * - Smooth 0.3s animation
 * - NGE/NERV terminal aesthetic (phosphor orange #ff9500)
 * - Dense 2-column grid layout
 * - Color-coded error rates
 *
 * State Management:
 * - Uses useHistoricalMetrics() hook for backend data
 * - Handles loading, error, and no-data states
 *
 * Performance:
 * - GPU-accelerated CSS transforms
 * - Debounced toggle animation
 */

import React, { useState } from 'react';
import { useHistoricalMetrics } from '@/hooks/useHistoricalMetrics';
import { TerminalSpinner } from '@/components/terminal';
import styles from './HistoricalMetricsPanel.module.css';

/**
 * Format number with commas for readability
 * Example: 1234567 -> "1,234,567"
 */
const formatNumber = (value: number): string => {
  return value.toLocaleString('en-US');
};

/**
 * Calculate error rate color based on percentage
 * <1% = green, <5% = amber, >=5% = red
 */
const getErrorRateColor = (rate: number): string => {
  if (rate < 1) return '#00ff00';   // Green - excellent
  if (rate < 5) return '#ff9500';   // Amber - warning
  return '#ff0000';                  // Red - critical
};

/**
 * Format uptime as "Xd Yh" format
 * Example: (45, 12) -> "45d 12h"
 */
const formatUptime = (days: number, hours: number): string => {
  return `${days}d ${hours}h`;
};

export const HistoricalMetricsPanel: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { data: historicalMetrics, isLoading, error } = useHistoricalMetrics();

  // Toggle expand/collapse
  const handleToggle = () => {
    setIsExpanded(prev => !prev);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.panel}>
        <div className={styles.header} onClick={handleToggle}>
          <span className={styles.title}>HISTORICAL METRICS</span>
          <span className={styles.toggleIcon}>{isExpanded ? '▲' : '▼'}</span>
        </div>
        <div className={`${styles.content} ${isExpanded ? styles.expanded : styles.collapsed}`}>
          <div className={styles.loadingContainer}>
            <TerminalSpinner size={20} color="#ff9500" />
            <span className={styles.loadingText}>LOADING HISTORICAL DATA...</span>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.panel}>
        <div className={styles.header} onClick={handleToggle}>
          <span className={styles.title}>HISTORICAL METRICS</span>
          <span className={styles.toggleIcon}>{isExpanded ? '▲' : '▼'}</span>
        </div>
        <div className={`${styles.content} ${isExpanded ? styles.expanded : styles.collapsed}`}>
          <div className={styles.errorContainer}>
            <span className={styles.errorIcon}>✗</span>
            <span className={styles.errorText}>ERROR LOADING HISTORICAL DATA</span>
            <span className={styles.errorDetails}>{error.message}</span>
          </div>
        </div>
      </div>
    );
  }

  // No data state
  if (!historicalMetrics || historicalMetrics.totalRequests === 0) {
    return (
      <div className={styles.panel}>
        <div className={styles.header} onClick={handleToggle}>
          <span className={styles.title}>HISTORICAL METRICS</span>
          <span className={styles.toggleIcon}>{isExpanded ? '▲' : '▼'}</span>
        </div>
        <div className={`${styles.content} ${isExpanded ? styles.expanded : styles.collapsed}`}>
          <div className={styles.noDataContainer}>
            <span className={styles.noDataIcon}>◇</span>
            <span className={styles.noDataText}>NO HISTORICAL DATA AVAILABLE</span>
            <span className={styles.noDataHint}>Process queries to generate historical metrics</span>
          </div>
        </div>
      </div>
    );
  }

  // Render metrics grid
  return (
    <div className={styles.panel}>
      <div className={styles.header} onClick={handleToggle}>
        <span className={styles.title}>HISTORICAL METRICS</span>
        <span className={styles.toggleIcon}>{isExpanded ? '▲' : '▼'}</span>
      </div>
      <div className={`${styles.content} ${isExpanded ? styles.expanded : styles.collapsed}`}>
        <div className={styles.sectionTitle}>LIFETIME STATISTICS</div>
        <div className={styles.metricsGrid}>
          {/* Row 1 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Total Requests:</span>
            <span className={styles.metricValue}>
              {formatNumber(historicalMetrics.totalRequests)}
            </span>
          </div>

          {/* Row 2 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Total Errors:</span>
            <span className={styles.metricValue}>
              {formatNumber(historicalMetrics.totalErrors)}
            </span>
          </div>

          {/* Row 3 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Error Rate:</span>
            <span
              className={styles.metricValue}
              style={{ color: getErrorRateColor(historicalMetrics.errorRate) }}
            >
              {historicalMetrics.errorRate.toFixed(2)}%
            </span>
          </div>

          {/* Row 4 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Avg Latency (All-Time):</span>
            <span className={styles.metricValue}>
              {Math.round(historicalMetrics.avgLatencyMs)}ms
            </span>
          </div>

          {/* Row 5 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>P95 Latency:</span>
            <span className={styles.metricValue}>
              {Math.round(historicalMetrics.p95LatencyMs)}ms
            </span>
          </div>

          {/* Row 6 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>P99 Latency:</span>
            <span className={styles.metricValue}>
              {Math.round(historicalMetrics.p99LatencyMs)}ms
            </span>
          </div>

          {/* Row 7 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Total Uptime:</span>
            <span className={styles.metricValue}>
              {formatUptime(historicalMetrics.uptimeDays, historicalMetrics.uptimeHours)}
            </span>
          </div>

          {/* Row 8 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Total Cache Hits:</span>
            <span className={styles.metricValue}>
              {formatNumber(historicalMetrics.totalCacheHits)}
            </span>
          </div>

          {/* Row 9 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Total Cache Misses:</span>
            <span className={styles.metricValue}>
              {formatNumber(historicalMetrics.totalCacheMisses)}
            </span>
          </div>

          {/* Row 10 */}
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Cache Hit Rate:</span>
            <span className={styles.metricValue}>
              {historicalMetrics.cacheHitRate.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
