/**
 * Metrics History Hook
 *
 * Tracks historical metrics data for sparkline visualizations.
 * Maintains a rolling window of the last N data points.
 */

import { useState, useEffect } from 'react';
import { useModelStatus } from './useModelStatus';

export interface MetricsHistory {
  queriesPerSec: number[];
  tokenGenRate: number[];
  cacheHitRate: number[];
  avgLatency: number[];
}

const MAX_HISTORY_LENGTH = 30; // Keep last 30 data points (2.5 minutes at 5s intervals)

/**
 * Calculate queries per second from total queries
 */
const calculateQueriesPerSec = (
  currentTotal: number,
  previousTotal: number,
  intervalSeconds: number
): number => {
  const delta = Math.max(0, currentTotal - previousTotal);
  return delta / intervalSeconds;
};

/**
 * Calculate average token generation rate from active models
 */
const calculateTokenGenRate = (models: any[]): number => {
  const activeModels = models.filter(
    (m) => m.state === 'active' || m.state === 'processing'
  );

  if (activeModels.length === 0) return 0;

  // Estimate tokens/sec based on response times and request counts
  // This is a rough estimate: assume average response is 100 tokens
  const avgTokensPerResponse = 100;
  const totalRate = activeModels.reduce((sum, model) => {
    if (model.avgResponseTime > 0) {
      return sum + (avgTokensPerResponse / (model.avgResponseTime / 1000));
    }
    return sum;
  }, 0);

  return totalRate;
};

export const useMetricsHistory = () => {
  const { data: modelStatus } = useModelStatus();
  const [history, setHistory] = useState<MetricsHistory>({
    queriesPerSec: [],
    tokenGenRate: [],
    cacheHitRate: [],
    avgLatency: [],
  });
  const [previousTotalQueries, setPreviousTotalQueries] = useState<number>(0);
  const [lastUpdateTime, setLastUpdateTime] = useState<number>(Date.now());

  useEffect(() => {
    if (!modelStatus) return;

    const now = Date.now();
    const intervalSeconds = (now - lastUpdateTime) / 1000;

    // Calculate new metrics
    const queriesPerSec = calculateQueriesPerSec(
      modelStatus.totalRequests,
      previousTotalQueries,
      intervalSeconds
    );

    const tokenGenRate = calculateTokenGenRate(modelStatus.models);

    const cacheHitRate = modelStatus.cacheHitRate * 100; // Convert to percentage

    // Calculate average latency from all active models
    const activeModels = modelStatus.models.filter(
      (m) => m.state === 'active' || m.state === 'processing'
    );
    const avgLatency =
      activeModels.length > 0
        ? activeModels.reduce((sum, m) => sum + m.avgResponseTime, 0) / activeModels.length
        : 0;

    // Update history with new data points
    setHistory((prev) => ({
      queriesPerSec: [...prev.queriesPerSec, queriesPerSec].slice(-MAX_HISTORY_LENGTH),
      tokenGenRate: [...prev.tokenGenRate, tokenGenRate].slice(-MAX_HISTORY_LENGTH),
      cacheHitRate: [...prev.cacheHitRate, cacheHitRate].slice(-MAX_HISTORY_LENGTH),
      avgLatency: [...prev.avgLatency, avgLatency].slice(-MAX_HISTORY_LENGTH),
    }));

    // Update tracking values
    setPreviousTotalQueries(modelStatus.totalRequests);
    setLastUpdateTime(now);
  }, [modelStatus]); // Only depend on modelStatus, not the derived values

  return history;
};
