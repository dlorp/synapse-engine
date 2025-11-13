/**
 * HealthMetricsPopup Component - Detailed Health Metrics Display
 *
 * Displays comprehensive health metrics for a selected topology node:
 * - Current status with color coding
 * - Uptime
 * - Memory usage
 * - CPU percentage
 * - Error rate
 * - Average latency
 * - Last check timestamp
 *
 * Fetches data from: GET /api/topology/health/{component_id}
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { TerminalSpinner } from '@/components/terminal';
import styles from './HealthMetricsPopup.module.css';

interface HealthMetrics {
  component_id: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
  uptime_seconds: number;
  memory_usage_mb: number;
  cpu_percent: number;
  error_rate: number;
  avg_latency_ms: number;
  last_check: string;
}

interface HealthMetricsPopupProps {
  componentId: string;
  onClose: () => void;
}

/**
 * Format uptime seconds to human-readable string
 */
const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m ${seconds % 60}s`;
};

/**
 * Format timestamp to readable format
 */
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/**
 * HealthMetricsPopup Component
 */
export const HealthMetricsPopup: React.FC<HealthMetricsPopupProps> = ({
  componentId,
  onClose,
}) => {
  // Fetch health metrics for component
  const { data: metrics, isLoading, error } = useQuery<HealthMetrics>({
    queryKey: ['component-health', componentId],
    queryFn: async () => {
      const response = await fetch(`/api/topology/health/${componentId}`);
      if (!response.ok) throw new Error('Failed to fetch health metrics');
      return response.json();
    },
    refetchInterval: 5000, // Update every 5 seconds while popup is open
  });

  // Handle backdrop click to close
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.popup}>
        {/* Header */}
        <div className={styles.popupHeader}>
          <span className={styles.popupTitle}>
            {componentId.toUpperCase()} - HEALTH METRICS
          </span>
          <button className={styles.closeButton} onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Body */}
        <div className={styles.popupBody}>
          {isLoading && (
            <div className={styles.loadingContainer}>
              <TerminalSpinner style="arc" size={20} />
              <span className={styles.loadingText}>LOADING METRICS...</span>
            </div>
          )}

          {error && (
            <div className={styles.errorContainer}>
              <div className={styles.errorText}>FAILED TO LOAD METRICS</div>
              <div className={styles.errorSubtext}>
                {(error as Error).message}
              </div>
            </div>
          )}

          {metrics && (
            <>
              {/* Status */}
              <div className={styles.metric}>
                <span className={styles.metricLabel}>STATUS:</span>
                <span
                  className={`${styles.metricValue} ${
                    styles[`status-${metrics.status}`]
                  }`}
                >
                  {metrics.status.toUpperCase()}
                </span>
              </div>

              {/* Uptime */}
              <div className={styles.metric}>
                <span className={styles.metricLabel}>UPTIME:</span>
                <span className={styles.metricValue}>
                  {formatUptime(metrics.uptime_seconds)}
                </span>
              </div>

              {/* Memory Usage */}
              <div className={styles.metric}>
                <span className={styles.metricLabel}>MEMORY:</span>
                <span className={styles.metricValue}>
                  {metrics.memory_usage_mb.toFixed(1)} MB
                </span>
              </div>

              {/* CPU Percentage */}
              <div className={styles.metric}>
                <span className={styles.metricLabel}>CPU:</span>
                <span className={styles.metricValue}>
                  {metrics.cpu_percent.toFixed(1)}%
                </span>
              </div>

              {/* Error Rate */}
              <div className={styles.metric}>
                <span className={styles.metricLabel}>ERROR RATE:</span>
                <span
                  className={`${styles.metricValue} ${
                    metrics.error_rate > 0.05
                      ? styles.errorHighlight
                      : styles.successHighlight
                  }`}
                >
                  {(metrics.error_rate * 100).toFixed(2)}%
                </span>
              </div>

              {/* Average Latency */}
              <div className={styles.metric}>
                <span className={styles.metricLabel}>AVG LATENCY:</span>
                <span className={styles.metricValue}>
                  {metrics.avg_latency_ms.toFixed(0)}ms
                </span>
              </div>

              {/* Last Check */}
              <div className={styles.lastCheck}>
                Last checked: {formatTimestamp(metrics.last_check)}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className={styles.popupFooter}>
          <button className={styles.closeFooterButton} onClick={onClose}>
            CLOSE
          </button>
        </div>
      </div>
    </div>
  );
};
