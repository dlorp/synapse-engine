/**
 * Historical metrics hook with real-time polling
 *
 * Fetches lifetime/historical metrics from backend every 5 seconds.
 * Uses TanStack Query for caching and automatic refetching.
 *
 * @returns Historical metrics data including total requests, errors,
 *          latency percentiles, uptime, and cache performance.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface HistoricalMetrics {
  totalRequests: number;
  totalErrors: number;
  errorRate: number;
  avgLatencyMs: number;
  p95LatencyMs: number;
  p99LatencyMs: number;
  uptimeDays: number;
  uptimeHours: number;
  uptimeSeconds: number;
  totalCacheHits: number;
  totalCacheMisses: number;
  cacheHitRate: number;
}

const fetchHistoricalMetrics = async (): Promise<HistoricalMetrics> => {
  const response = await apiClient.get<HistoricalMetrics>('/metrics/historical');
  return response.data;
};

export const useHistoricalMetrics = () => {
  return useQuery<HistoricalMetrics, Error>({
    queryKey: ['metrics', 'historical'],
    queryFn: fetchHistoricalMetrics,
    refetchInterval: 5000, // 5 second updates (less frequent than real-time metrics)
    staleTime: 2500,
  });
};
