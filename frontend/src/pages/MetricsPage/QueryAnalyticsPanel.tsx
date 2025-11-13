/**
 * Query Analytics Panel
 *
 * Displays real-time query metrics using ASCII charts:
 * - Line chart for query rate over time
 * - Bar chart for tier distribution (Q2/Q3/Q4)
 *
 * Updates every second via TanStack Query.
 */

import React, { useMemo } from 'react';
import { AsciiPanel } from '@/components/terminal';
import { TerminalSpinner } from '@/components/terminal/TerminalSpinner/TerminalSpinner';
import { AsciiLineChart } from '@/components/charts/AsciiLineChart';
import { AsciiBarChart, type BarData } from '@/components/charts/AsciiBarChart';
import { useQueryMetrics } from '@/hooks/useQueryMetrics';
import { useModelStatus } from '@/hooks/useModelStatus';
import styles from './QueryAnalyticsPanel.module.css';

export const QueryAnalyticsPanel: React.FC = () => {
  const { data: metrics, error, isLoading } = useQueryMetrics();
  const { data: modelStatus } = useModelStatus();

  // Prepare bar chart data for tier distribution
  const tierBarData = useMemo<BarData[]>(() => {
    if (!metrics) return [];

    return [
      {
        label: 'Q2',
        value: metrics.tierDistribution.Q2,
        color: '#ff9500', // Phosphor orange
      },
      {
        label: 'Q3',
        value: metrics.tierDistribution.Q3,
        color: '#ff9500',
      },
      {
        label: 'Q4',
        value: metrics.tierDistribution.Q4,
        color: '#ff9500',
      },
    ];
  }, [metrics]);

  // Format large numbers with commas
  const formatNumber = (num: number): string => {
    return num.toLocaleString('en-US');
  };

  // Render loading state
  if (isLoading) {
    return (
      <AsciiPanel title="QUERY ANALYTICS">
        <div className={styles.loading}>
          <TerminalSpinner style="arc" size={24} />
          <span className={styles.loadingText}>Loading metrics...</span>
        </div>
      </AsciiPanel>
    );
  }

  // Render error state
  if (error) {
    return (
      <AsciiPanel title="QUERY ANALYTICS">
        <div className={styles.error}>
          <div className={styles.errorTitle}>ERROR: Failed to load metrics</div>
          <div className={styles.errorMessage}>{error.message}</div>
        </div>
      </AsciiPanel>
    );
  }

  // Render empty state
  if (!metrics) {
    return (
      <AsciiPanel title="QUERY ANALYTICS">
        <div className={styles.empty}>No metrics data available</div>
      </AsciiPanel>
    );
  }

  // Check if any models are running
  const runningModels = modelStatus?.models.filter(
    m => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
  ) || [];

  // No models running state
  if (runningModels.length === 0) {
    return (
      <AsciiPanel title="QUERY ANALYTICS">
        <div className={styles.awaitingModels}>
          <div className={styles.emptyChartContainer}>
            <div className={styles.emptyChartArt}>
              <span>     ▁</span>
              <span>    ▁▁</span>
              <span>   ▁▁▁</span>
              <span>  ▁▁▁▁</span>
              <span> ▁▁▁▁▁</span>
              <span>▁▁▁▁▁▁</span>
              <span>───────────────────</span>
            </div>
            <div className={styles.emptyChartMessage}>NO QUERIES PROCESSED</div>
          </div>
          <div className={styles.emptyHint}>
            → Deploy models via Model Management to enable query analytics
          </div>
        </div>
      </AsciiPanel>
    );
  }

  return (
    <AsciiPanel title="QUERY ANALYTICS">
      <div className={styles.container}>
        {/* Summary Statistics */}
        <div className={styles.summary}>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Total Queries:</span>
            <span className={styles.statValue}>{formatNumber(metrics.totalQueries)}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Avg Latency:</span>
            <span className={styles.statValue}>{metrics.avgLatencyMs.toFixed(1)}ms</span>
          </div>
        </div>

        {/* Query Rate Line Chart */}
        <div className={styles.section}>
          <AsciiLineChart
            data={metrics.queryRate}
            height={10}
            color="#ff9500"
            title="Query Rate (queries/sec)"
            xLabel="Time (last 18 samples)"
            yLabel="Rate"
          />
        </div>

        {/* Tier Distribution Bar Chart */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>Tier Distribution</div>
          <AsciiBarChart
            data={tierBarData}
            maxBarLength={30}
            showPercentage={true}
            showValue={true}
          />
        </div>
      </div>
    </AsciiPanel>
  );
};
