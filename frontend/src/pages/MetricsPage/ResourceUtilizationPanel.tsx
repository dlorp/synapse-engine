/**
 * ResourceUtilizationPanel - System resource metrics dashboard
 * Displays 9 real-time metrics in 3x3 grid with color-coded status
 * Updates at 1Hz with optimized rendering
 */

import React, { useMemo } from 'react';
import { AsciiPanel } from '@/components/terminal';
import { ResourceMetricCard } from '@/components/metrics';
import { TerminalSpinner } from '@/components/terminal/TerminalSpinner/TerminalSpinner';
import { useResourceMetrics } from '@/hooks/useResourceMetrics';
import { useModelStatus } from '@/hooks/useModelStatus';
import {
  formatBytes,
  formatMemory,
  formatPercent,
  formatRatio,
  getPercentStatus,
} from '@/utils/formatters';
import styles from './ResourceUtilizationPanel.module.css';

export const ResourceUtilizationPanel: React.FC = () => {
  const { data: metrics, isLoading, isError, error } = useResourceMetrics();
  const { data: modelStatus } = useModelStatus();

  // Memoize formatted metrics to prevent unnecessary recalculations
  const formattedMetrics = useMemo(() => {
    if (!metrics) return null;

    return {
      vram: {
        value: formatMemory(metrics.vram.used),
        percent: metrics.vram.percent,
        status: getPercentStatus(metrics.vram.percent),
        secondary: `${formatMemory(metrics.vram.total)} total`,
      },
      cpu: {
        value: formatPercent(metrics.cpu.percent),
        percent: metrics.cpu.percent,
        status: getPercentStatus(metrics.cpu.percent),
        secondary: `${metrics.cpu.cores} cores`,
      },
      memory: {
        value: formatMemory(metrics.memory.used),
        percent: metrics.memory.percent,
        status: getPercentStatus(metrics.memory.percent),
        secondary: `${formatMemory(metrics.memory.total)} total`,
      },
      faiss: {
        value: formatBytes(metrics.faissIndexSize),
        status: 'ok' as const,
      },
      redis: {
        value: formatBytes(metrics.redisCacheSize),
        status: 'ok' as const,
      },
      connections: {
        value: metrics.activeConnections,
        status: 'ok' as const,
      },
      threads: {
        value: formatRatio(metrics.threadPoolStatus.active,
                          metrics.threadPoolStatus.active + metrics.threadPoolStatus.queued),
        status: 'ok' as const,
        secondary: metrics.threadPoolStatus.queued > 0 ? `${metrics.threadPoolStatus.queued} queued` : 'no queue',
      },
      diskIO: {
        value: `${metrics.diskIO.readMBps.toFixed(1)}↓ ${metrics.diskIO.writeMBps.toFixed(1)}↑`,
        status: 'ok' as const,
        secondary: 'MB/s',
      },
      network: {
        value: `${metrics.networkThroughput.rxMBps.toFixed(1)}↓ ${metrics.networkThroughput.txMBps.toFixed(1)}↑`,
        status: 'ok' as const,
        secondary: 'MB/s',
      },
    };
  }, [metrics]);

  // Loading state
  if (isLoading) {
    return (
      <AsciiPanel title="SYSTEM RESOURCE UTILIZATION">
        <div className={styles.loadingContainer}>
          <TerminalSpinner size={32} style="arc" />
          <span className={styles.loadingText}>INITIALIZING RESOURCE MONITORS...</span>
        </div>
      </AsciiPanel>
    );
  }

  // Error state
  if (isError) {
    return (
      <AsciiPanel title="SYSTEM RESOURCE UTILIZATION">
        <div className={styles.errorContainer}>
          <div className={styles.errorIcon}>⚠</div>
          <div className={styles.errorText}>
            RESOURCE MONITOR ERROR
          </div>
          <div className={styles.errorDetail}>
            {error?.message || 'Failed to fetch resource metrics'}
          </div>
        </div>
      </AsciiPanel>
    );
  }

  // No data state
  if (!formattedMetrics) {
    return (
      <AsciiPanel title="SYSTEM RESOURCE UTILIZATION">
        <div className={styles.errorContainer}>
          <div className={styles.errorText}>NO RESOURCE DATA AVAILABLE</div>
        </div>
      </AsciiPanel>
    );
  }

  // Check if any models are running
  const runningModels = modelStatus?.models.filter(
    m => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
  ) || [];

  // No models running state
  if (runningModels.length === 0) {
    const emptyResources = [
      { label: 'VRAM USAGE', value: '0 GB' },
      { label: 'CPU USAGE', value: '0%' },
      { label: 'MEMORY USAGE', value: '0 GB' },
      { label: 'FAISS INDEX', value: '0 MB' },
      { label: 'REDIS CACHE', value: '0 MB' },
      { label: 'CONNECTIONS', value: '0' },
      { label: 'THREAD POOL', value: '0/0' },
      { label: 'DISK I/O', value: '0↓ 0↑' },
      { label: 'NETWORK', value: '0↓ 0↑' },
    ];

    return (
      <AsciiPanel title="SYSTEM RESOURCE UTILIZATION">
        <div className={styles.awaitingModels}>
          <div className={styles.emptyResourceGrid}>
            {emptyResources.map((resource, idx) => (
              <div key={idx} className={styles.emptyResourceCard}>
                <div className={styles.emptyResourceLabel}>{resource.label}</div>
                <div className={styles.emptyResourceBar}>
                  <span className={styles.emptyBar}>[░░░░░░░░░░]</span>
                  <span className={styles.emptyValue}>{resource.value}</span>
                </div>
              </div>
            ))}
          </div>
          <div className={styles.emptyHint}>
            → Deploy models via Model Management to enable resource monitoring
          </div>
        </div>
      </AsciiPanel>
    );
  }

  return (
    <AsciiPanel title="SYSTEM RESOURCE UTILIZATION">
      <div className={styles.grid}>
        {/* Row 1: Core Resources */}
        <ResourceMetricCard
          label="VRAM USAGE"
          value={formattedMetrics.vram.value}
          percent={formattedMetrics.vram.percent}
          status={formattedMetrics.vram.status}
          secondary={formattedMetrics.vram.secondary}
        />

        <ResourceMetricCard
          label="CPU USAGE"
          value={formattedMetrics.cpu.value}
          percent={formattedMetrics.cpu.percent}
          status={formattedMetrics.cpu.status}
          secondary={formattedMetrics.cpu.secondary}
        />

        <ResourceMetricCard
          label="MEMORY USAGE"
          value={formattedMetrics.memory.value}
          percent={formattedMetrics.memory.percent}
          status={formattedMetrics.memory.status}
          secondary={formattedMetrics.memory.secondary}
        />

        {/* Row 2: Data Stores */}
        <ResourceMetricCard
          label="FAISS INDEX"
          value={formattedMetrics.faiss.value}
          status={formattedMetrics.faiss.status}
        />

        <ResourceMetricCard
          label="REDIS CACHE"
          value={formattedMetrics.redis.value}
          status={formattedMetrics.redis.status}
        />

        <ResourceMetricCard
          label="CONNECTIONS"
          value={formattedMetrics.connections.value}
          status={formattedMetrics.connections.status}
        />

        {/* Row 3: Throughput */}
        <ResourceMetricCard
          label="THREAD POOL"
          value={formattedMetrics.threads.value}
          status={formattedMetrics.threads.status}
          secondary={formattedMetrics.threads.secondary}
        />

        <ResourceMetricCard
          label="DISK I/O"
          value={formattedMetrics.diskIO.value}
          status={formattedMetrics.diskIO.status}
          secondary={formattedMetrics.diskIO.secondary}
        />

        <ResourceMetricCard
          label="NETWORK"
          value={formattedMetrics.network.value}
          status={formattedMetrics.network.status}
          secondary={formattedMetrics.network.secondary}
        />
      </div>
    </AsciiPanel>
  );
};
