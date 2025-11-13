/**
 * SystemHealthOverview Component
 *
 * Displays aggregate system health metrics with ASCII sparklines.
 * Shows the 4 core metrics removed from HomePage as trends.
 * Follows breathing bars aesthetic: dense, monospace, Unicode blocks.
 *
 * Features:
 * - 4 ASCII sparkline visualizations (30-min rolling history)
 * - Real-time updates at 1Hz via useMetricsHistory hook
 * - Color-coded status indicators (green, amber, red)
 * - Unicode block characters (▁▂▃▄▅▆▇█) for height-based visualization
 *
 * Performance: <10ms render time (memoized sparklines)
 */

import React, { useMemo } from 'react';
import { useModelStatus } from '@/hooks/useModelStatus';
import { useMetricsHistory } from '@/hooks/useMetricsHistory';
import { TerminalSpinner, AsciiPanel } from '@/components/terminal';
import styles from './SystemHealthOverview.module.css';

/**
 * Generate ASCII sparkline using Unicode block characters
 * Pattern: ▁▂▃▄▅▆▇█ (8 height levels)
 */
const generateAsciiSparkline = (data: number[], width: number = 30): string => {
  if (data.length === 0) return '▁'.repeat(width);

  const blocks = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min;

  // Normalize data to 0-7 range for block selection
  const normalized = data.map(val => {
    if (range === 0) return 0;
    return Math.round(((val - min) / range) * 7);
  });

  // Take last `width` points for sparkline
  const displayData = normalized.slice(-width);

  // Pad with ▁ if not enough data
  while (displayData.length < width) {
    displayData.unshift(0);
  }

  return displayData.map(idx => blocks[idx] || '▁').join('');
};

export const SystemHealthOverview: React.FC = () => {
  // ALL HOOKS MUST BE CALLED FIRST (Rules of Hooks - must be unconditional)
  const { data: modelStatus, isLoading, error } = useModelStatus();
  const metricsHistory = useMetricsHistory();

  // Calculate current values and sparklines (memoized for performance)
  // Safe to calculate even during loading/error states
  const metrics = useMemo(() => {
    const currentQPS = metricsHistory.queriesPerSec[metricsHistory.queriesPerSec.length - 1] || 0;
    const currentTokenRate = metricsHistory.tokenGenRate[metricsHistory.tokenGenRate.length - 1] || 0;
    const currentLatency = metricsHistory.avgLatency[metricsHistory.avgLatency.length - 1] || 0;
    const currentCacheRate = metricsHistory.cacheHitRate[metricsHistory.cacheHitRate.length - 1] || 0;

    return [
      {
        label: 'QUERIES/SEC',
        value: `${currentQPS.toFixed(2)} q/s`,
        sparkline: generateAsciiSparkline(metricsHistory.queriesPerSec),
        color: currentQPS > 5 ? '#00ff41' : '#00ffff',
      },
      {
        label: 'TOKEN GEN',
        value: `${currentTokenRate.toFixed(1)} t/s`,
        sparkline: generateAsciiSparkline(metricsHistory.tokenGenRate),
        color: '#00ffff',
      },
      {
        label: 'AVG LATENCY',
        value: `${currentLatency.toFixed(0)} ms`,
        sparkline: generateAsciiSparkline(metricsHistory.avgLatency),
        color: currentLatency > 2000 ? '#ff0000' : currentLatency > 1000 ? '#ff9500' : '#00ff41',
      },
      {
        label: 'CACHE HIT',
        value: `${currentCacheRate.toFixed(1)} %`,
        sparkline: generateAsciiSparkline(metricsHistory.cacheHitRate),
        color: currentCacheRate > 70 ? '#00ff41' : currentCacheRate > 50 ? '#ff9500' : '#ff0000',
      },
    ];
  }, [metricsHistory]);

  // NOW conditional returns are safe (after all hooks)
  // Loading state
  if (isLoading) {
    return (
      <AsciiPanel title="SYSTEM HEALTH OVERVIEW">
        <div className={styles.loading}>
          <TerminalSpinner style="dots" size={24} />
          <span>LOADING SYSTEM METRICS...</span>
        </div>
      </AsciiPanel>
    );
  }

  // Error state
  if (error) {
    return (
      <AsciiPanel title="SYSTEM HEALTH OVERVIEW">
        <div className={styles.error}>
          <span className={styles.errorIcon}>✖</span>
          <div className={styles.errorMessage}>
            <div className={styles.errorTitle}>SYSTEM METRICS UNAVAILABLE</div>
            <div className={styles.errorDetail}>
              {error.message || 'Failed to fetch system health data'}
            </div>
          </div>
        </div>
      </AsciiPanel>
    );
  }

  // No data state
  if (!modelStatus) {
    return (
      <AsciiPanel title="SYSTEM HEALTH OVERVIEW">
        <div className={styles.noData}>
          <span>NO SYSTEM DATA AVAILABLE</span>
        </div>
      </AsciiPanel>
    );
  }

  // Check if any models are running
  const runningModels = modelStatus.models.filter(
    m => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
  );

  // No models running state
  if (runningModels.length === 0) {
    return (
      <AsciiPanel title="SYSTEM HEALTH OVERVIEW">
        <div className={styles.awaitingModels}>
          <div className={styles.emptyMetricsTable}>
            <div className={styles.emptyMetricRow}>
              <div className={styles.emptyMetricLabel}>QUERIES/SEC:</div>
              <div className={styles.emptyMetricValue}>0.00 q/s</div>
              <div className={styles.emptySparkline}>
                [▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁]
              </div>
            </div>

            <div className={styles.emptyMetricRow}>
              <div className={styles.emptyMetricLabel}>TOKEN GEN:</div>
              <div className={styles.emptyMetricValue}>0.0 t/s</div>
              <div className={styles.emptySparkline}>
                [▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁]
              </div>
            </div>

            <div className={styles.emptyMetricRow}>
              <div className={styles.emptyMetricLabel}>AVG LATENCY:</div>
              <div className={styles.emptyMetricValue}>0 ms</div>
              <div className={styles.emptySparkline}>
                [▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁]
              </div>
            </div>

            <div className={styles.emptyMetricRow}>
              <div className={styles.emptyMetricLabel}>CACHE HIT:</div>
              <div className={styles.emptyMetricValue}>0.0 %</div>
              <div className={styles.emptySparkline}>
                [▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁]
              </div>
            </div>
          </div>

          <div className={styles.emptyHint}>
            → NO ACTIVE MODELS - Deploy to begin monitoring
          </div>
        </div>
      </AsciiPanel>
    );
  }

  return (
    <AsciiPanel title="SYSTEM HEALTH OVERVIEW">
      <div className={styles.content}>
        <div className={styles.subtitle}>
          Aggregate system performance trends (30-min rolling history)
        </div>
        {/* Dense 4-row layout with ASCII sparklines */}
        <div className={styles.metricsTable}>
          {metrics.map((metric, idx) => (
            <div key={idx} className={styles.metricRow}>
              <div className={styles.metricLabel}>{metric.label}:</div>
              <div className={styles.metricValue}>{metric.value}</div>
              <div
                className={styles.sparkline}
                style={{ color: metric.color }}
                aria-label={`${metric.label} trend (30 min)`}
              >
                {metric.sparkline}
              </div>
              <div className={styles.metricTimeframe}>[30m]</div>
            </div>
          ))}
        </div>
      </div>
    </AsciiPanel>
  );
};
