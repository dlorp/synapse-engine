/**
 * SystemStatusPanel Component - Dense system metrics display
 *
 * Comprehensive system status panel with 8+ dense metrics in terminal aesthetic.
 * Uses DotMatrixPanel wrapper with phosphor glow effects.
 *
 * Features:
 * - 8+ system metrics in dense 2-column grid
 * - Real-time updates with smooth transitions
 * - Phosphor-glow-static-orange on metric values
 * - Color-coded status indicators
 * - Border glow on panel
 * - Scan lines and grid background
 */

import React, { useMemo } from 'react';
import { DotMatrixPanel } from '../DotMatrixPanel';
import styles from './SystemStatusPanel.module.css';

export interface SystemMetrics {
  cpuUsage: number; // 0-100
  memoryUsedMb: number;
  memoryTotalMb: number;
  activeModels: {
    total: number;
    q2: number;
    q3: number;
    q4: number;
  };
  queryQueue: number;
  cgragIndexSize: number;
  cacheHitRate: number; // 0-1
  avgQueryLatencyMs: number;
  uptimeSeconds: number;
  activeQueries?: number;
  totalQueries?: number;
  errorRate?: number; // 0-1
}

export interface SystemStatusPanelProps {
  metrics: SystemMetrics;
  className?: string;
  title?: string;
  compact?: boolean;
}

/**
 * Format uptime duration as human-readable string
 */
const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
};

/**
 * Format bytes as MB/GB
 */
const formatMemory = (mb: number): string => {
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(1)}GB`;
  }
  return `${mb.toFixed(0)}MB`;
};

/**
 * Get status color based on value and thresholds
 */
const getStatusColor = (
  value: number,
  thresholds: { warning: number; critical: number },
  inverse: boolean = false
): string => {
  if (inverse) {
    // Lower is better (e.g., latency, error rate)
    if (value >= thresholds.critical) return 'var(--text-error)';
    if (value >= thresholds.warning) return 'var(--text-warning)';
    return 'var(--text-accent)';
  } else {
    // Higher is better (e.g., cache hit rate)
    if (value >= thresholds.critical) return 'var(--text-accent)';
    if (value >= thresholds.warning) return 'var(--text-primary)';
    return 'var(--text-error)';
  }
};

export const SystemStatusPanel: React.FC<SystemStatusPanelProps> = ({
  metrics,
  className,
  title = 'SYSTEM STATUS',
  compact = false,
}) => {
  // Calculate memory usage percentage
  const memoryPercent = useMemo(
    () => (metrics.memoryUsedMb / metrics.memoryTotalMb) * 100,
    [metrics.memoryUsedMb, metrics.memoryTotalMb]
  );

  // Get status colors for key metrics
  const cpuColor = useMemo(
    () => getStatusColor(metrics.cpuUsage, { warning: 70, critical: 90 }, true),
    [metrics.cpuUsage]
  );

  const memoryColor = useMemo(
    () => getStatusColor(memoryPercent, { warning: 70, critical: 90 }, true),
    [memoryPercent]
  );

  const cacheColor = useMemo(
    () => getStatusColor(metrics.cacheHitRate * 100, { warning: 50, critical: 70 }, false),
    [metrics.cacheHitRate]
  );

  const latencyColor = useMemo(
    () => getStatusColor(metrics.avgQueryLatencyMs, { warning: 2000, critical: 5000 }, true),
    [metrics.avgQueryLatencyMs]
  );

  return (
    <DotMatrixPanel
      title={title}
      enableGrid
      gridDensity="dense"
      enableScanLines
      scanLineSpeed="slow"
      enableBorderGlow
      glowColor="orange"
      className={className}
    >
      <div className={compact ? styles.compactGrid : styles.grid}>
        {/* CPU Usage */}
        <div className={styles.metricRow}>
          <span className={styles.label}>CPU USAGE</span>
          <span className={styles.value} style={{ color: cpuColor }}>
            <span className="phosphor-glow-static-orange">{metrics.cpuUsage.toFixed(1)}%</span>
          </span>
        </div>

        {/* Memory Usage */}
        <div className={styles.metricRow}>
          <span className={styles.label}>MEMORY</span>
          <span className={styles.value} style={{ color: memoryColor }}>
            <span className="phosphor-glow-static-orange">
              {formatMemory(metrics.memoryUsedMb)} / {formatMemory(metrics.memoryTotalMb)}
            </span>
          </span>
        </div>

        {/* Active Models */}
        <div className={styles.metricRow}>
          <span className={styles.label}>ACTIVE MODELS</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {metrics.activeModels.total}
            </span>
            <span className={styles.breakdown}>
              {' '}(Q2:{metrics.activeModels.q2} Q3:{metrics.activeModels.q3} Q4:{metrics.activeModels.q4})
            </span>
          </span>
        </div>

        {/* Query Queue */}
        <div className={styles.metricRow}>
          <span className={styles.label}>QUERY QUEUE</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">{metrics.queryQueue}</span>
            {metrics.queryQueue > 0 && <span className={styles.processing}> PENDING</span>}
          </span>
        </div>

        {/* CGRAG Index Size */}
        <div className={styles.metricRow}>
          <span className={styles.label}>CGRAG INDEX</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {metrics.cgragIndexSize.toLocaleString()} DOCS
            </span>
          </span>
        </div>

        {/* Cache Hit Rate */}
        <div className={styles.metricRow}>
          <span className={styles.label}>CACHE HIT RATE</span>
          <span className={styles.value} style={{ color: cacheColor }}>
            <span className="phosphor-glow-static-orange">
              {(metrics.cacheHitRate * 100).toFixed(1)}%
            </span>
          </span>
        </div>

        {/* Average Query Latency */}
        <div className={styles.metricRow}>
          <span className={styles.label}>AVG LATENCY</span>
          <span className={styles.value} style={{ color: latencyColor }}>
            <span className="phosphor-glow-static-orange">
              {metrics.avgQueryLatencyMs.toFixed(0)}ms
            </span>
          </span>
        </div>

        {/* System Uptime */}
        <div className={styles.metricRow}>
          <span className={styles.label}>UPTIME</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {formatUptime(metrics.uptimeSeconds)}
            </span>
          </span>
        </div>

        {/* Optional: Active Queries */}
        {metrics.activeQueries !== undefined && (
          <div className={styles.metricRow}>
            <span className={styles.label}>ACTIVE QUERIES</span>
            <span className={styles.value}>
              <span className="phosphor-glow-static-orange">{metrics.activeQueries}</span>
            </span>
          </div>
        )}

        {/* Optional: Total Queries */}
        {metrics.totalQueries !== undefined && (
          <div className={styles.metricRow}>
            <span className={styles.label}>TOTAL QUERIES</span>
            <span className={styles.value}>
              <span className="phosphor-glow-static-orange">
                {metrics.totalQueries.toLocaleString()}
              </span>
            </span>
          </div>
        )}

        {/* Optional: Error Rate */}
        {metrics.errorRate !== undefined && (
          <div className={styles.metricRow}>
            <span className={styles.label}>ERROR RATE</span>
            <span className={styles.value}>
              <span
                className="phosphor-glow-static-orange"
                style={{
                  color: metrics.errorRate > 0.05 ? 'var(--text-error)' : 'var(--text-accent)',
                }}
              >
                {(metrics.errorRate * 100).toFixed(2)}%
              </span>
            </span>
          </div>
        )}
      </div>
    </DotMatrixPanel>
  );
};
