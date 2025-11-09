/**
 * SystemStatusPanelEnhanced Component - Dense system metrics with sparklines
 *
 * Expanded system status panel with 8+ metrics including real-time sparklines.
 * Implements Task 1.2 from SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md.
 *
 * Features:
 * - 8+ system metrics in dense 2-column grid
 * - Real-time sparklines for trending metrics
 * - Color-coded status indicators
 * - Responsive layout (mobile → tablet → desktop)
 * - WebSocket/polling-based live updates
 */

import React, { useMemo } from 'react';
import { DotMatrixPanel } from '../DotMatrixPanel';
import { Sparkline } from '../Sparkline';
import { StatusIndicator } from '../StatusIndicator';
import { ModelStatusResponse } from '@/types/models';
import { MetricsHistory } from '@/hooks/useMetricsHistory';
import styles from './SystemStatusPanel.module.css';

export interface SystemStatusPanelEnhancedProps {
  modelStatus: ModelStatusResponse;
  metricsHistory: MetricsHistory;
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
    return `${days}d ${hours}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
};

/**
 * Calculate system uptime from oldest model start time
 */
const calculateSystemUptime = (models: any[]): number => {
  if (models.length === 0) return 0;

  const maxUptime = Math.max(...models.map((m) => m.uptimeSeconds || 0));
  return maxUptime;
};

/**
 * Calculate context window utilization (placeholder - needs backend data)
 */
const calculateContextUtilization = (models: any[]): number => {
  // TODO: Implement when backend provides context window data
  // For now, estimate based on active queries
  const activeModels = models.filter((m) => m.state === 'processing');
  return Math.min(100, activeModels.length * 15); // Rough estimate
};

/**
 * Calculate CGRAG retrieval latency (placeholder - needs backend data)
 */
const calculateCGRAGLatency = (): number => {
  // TODO: Implement when backend provides CGRAG metrics
  return Math.random() * 50 + 30; // Mock: 30-80ms
};

/**
 * Calculate WebSocket connections (placeholder - needs backend data)
 */
const calculateWebSocketConnections = (): number => {
  // TODO: Implement when backend provides WebSocket metrics
  return Math.floor(Math.random() * 5) + 1; // Mock: 1-5 connections
};

export const SystemStatusPanelEnhanced: React.FC<SystemStatusPanelEnhancedProps> = ({
  modelStatus,
  metricsHistory,
  className,
  title = 'SYSTEM STATUS',
  compact = false,
}) => {
  // Calculate derived metrics
  const activeModels = useMemo(() => {
    const models = modelStatus.models.filter(
      (m) => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
    );
    const byTier = {
      q2: models.filter((m) => m.tier === 'Q2').length,
      q3: models.filter((m) => m.tier === 'Q3').length,
      q4: models.filter((m) => m.tier === 'Q4').length,
    };
    return { total: models.length, ...byTier };
  }, [modelStatus.models]);

  const systemUptime = useMemo(
    () => calculateSystemUptime(modelStatus.models),
    [modelStatus.models]
  );

  const contextUtilization = useMemo(
    () => calculateContextUtilization(modelStatus.models),
    [modelStatus.models]
  );

  const cgragLatency = useMemo(() => calculateCGRAGLatency(), []);

  const wsConnections = useMemo(() => calculateWebSocketConnections(), []);

  // Current metric values (last value from history)
  const currentQPS = metricsHistory.queriesPerSec[metricsHistory.queriesPerSec.length - 1] || 0;
  const currentTokenRate = metricsHistory.tokenGenRate[metricsHistory.tokenGenRate.length - 1] || 0;
  const currentLatency = metricsHistory.avgLatency[metricsHistory.avgLatency.length - 1] || 0;

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
      <div className={compact ? styles.compactGrid : styles.gridEnhanced}>
        {/* 1. Queries/sec with sparkline */}
        <div className={styles.metricRow}>
          <span className={styles.label}>QUERIES/SEC</span>
          <span className={styles.valueWithSparkline}>
            <span className="phosphor-glow-static-orange">
              {currentQPS.toFixed(2)}
            </span>
            <Sparkline
              data={metricsHistory.queriesPerSec}
              width={15}
              color="primary"
              className={styles.sparkline}
            />
          </span>
        </div>

        {/* 2. Active Models with tier breakdown */}
        <div className={styles.metricRow}>
          <span className={styles.label}>ACTIVE MODELS</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {activeModels.total}
            </span>
            <span className={styles.breakdown}>
              {' '}(Q2:{activeModels.q2} Q3:{activeModels.q3} Q4:{activeModels.q4})
            </span>
          </span>
        </div>

        {/* 3. Token Generation Rate with sparkline */}
        <div className={styles.metricRow}>
          <span className={styles.label}>TOKEN GEN RATE</span>
          <span className={styles.valueWithSparkline}>
            <span className="phosphor-glow-static-orange">
              {currentTokenRate.toFixed(1)} T/s
            </span>
            <Sparkline
              data={metricsHistory.tokenGenRate}
              width={15}
              color="accent"
              className={styles.sparkline}
            />
          </span>
        </div>

        {/* 4. Context Window Utilization */}
        <div className={styles.metricRow}>
          <span className={styles.label}>CONTEXT UTIL</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {contextUtilization.toFixed(0)}%
            </span>
            {contextUtilization > 80 && (
              <StatusIndicator
                status="warning"
                showDot
                size="sm"
                className={styles.inlineStatus}
              />
            )}
          </span>
        </div>

        {/* 5. Cache Hit Rate with sparkline */}
        <div className={styles.metricRow}>
          <span className={styles.label}>CACHE HIT RATE</span>
          <span className={styles.valueWithSparkline}>
            <span className="phosphor-glow-static-orange">
              {(modelStatus.cacheHitRate * 100).toFixed(1)}%
            </span>
            <Sparkline
              data={metricsHistory.cacheHitRate}
              width={15}
              color={modelStatus.cacheHitRate > 0.7 ? 'success' : 'warning'}
              className={styles.sparkline}
            />
          </span>
        </div>

        {/* 6. CGRAG Retrieval Latency */}
        <div className={styles.metricRow}>
          <span className={styles.label}>CGRAG LATENCY</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {cgragLatency.toFixed(0)}ms
            </span>
            {cgragLatency > 100 && (
              <StatusIndicator
                status="warning"
                showDot
                size="sm"
                className={styles.inlineStatus}
              />
            )}
          </span>
        </div>

        {/* 7. WebSocket Connections */}
        <div className={styles.metricRow}>
          <span className={styles.label}>WS CONNECTIONS</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {wsConnections}
            </span>
            <StatusIndicator
              status={wsConnections > 0 ? 'active' : 'idle'}
              showDot
              size="sm"
              className={styles.inlineStatus}
            />
          </span>
        </div>

        {/* 8. System Uptime */}
        <div className={styles.metricRow}>
          <span className={styles.label}>SYSTEM UPTIME</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {formatUptime(systemUptime)}
            </span>
          </span>
        </div>

        {/* 9. Average Query Latency with sparkline */}
        <div className={styles.metricRow}>
          <span className={styles.label}>AVG LATENCY</span>
          <span className={styles.valueWithSparkline}>
            <span className="phosphor-glow-static-orange">
              {currentLatency.toFixed(0)}ms
            </span>
            <Sparkline
              data={metricsHistory.avgLatency}
              width={15}
              color={currentLatency > 2000 ? 'error' : 'primary'}
              className={styles.sparkline}
            />
          </span>
        </div>

        {/* 10. Active Queries */}
        <div className={styles.metricRow}>
          <span className={styles.label}>ACTIVE QUERIES</span>
          <span className={styles.value}>
            <span className="phosphor-glow-static-orange">
              {modelStatus.activeQueries}
            </span>
            {modelStatus.activeQueries > 0 && (
              <StatusIndicator
                status="processing"
                pulse
                showDot
                size="sm"
                className={styles.inlineStatus}
              />
            )}
          </span>
        </div>
      </div>
    </DotMatrixPanel>
  );
};
