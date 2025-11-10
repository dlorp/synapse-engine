/**
 * TanStack Query hook for fetching per-model metrics
 * Polls backend every 1 second for real-time model performance data
 *
 * Backend provides metrics array in /api/models/status response
 * This hook transforms that array into a keyed object for O(1) lookups
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';

/**
 * Per-model metrics time-series data
 */
export interface ModelMetrics {
  tokensPerSecond: number[];
  memoryGb: number[];
  latencyMs: number[];
}

/**
 * Backend response structure for metrics array
 */
export interface ModelMetricsSnapshot {
  modelId: string;
  tokensPerSecond: number[];
  currentTokensPerSecond: number;
  memoryGb: number[];
  currentMemoryGb: number;
  latencyMs: number[];
  currentLatencyMs: number;
}

/**
 * Backend API response structure (extends ModelStatusResponse)
 */
interface MetricsResponse {
  metrics: ModelMetricsSnapshot[];
  metricsTimestamp: string;
}

/**
 * Fetch per-model metrics from backend
 * Endpoint: GET /api/models/status (extended with metrics field in Phase 3.4)
 */
async function fetchModelMetrics(): Promise<Record<string, ModelMetrics>> {
  try {
    const response = await apiClient.get<MetricsResponse>(endpoints.models.status);

    // Transform array to keyed object for easy lookup in components
    const metricsMap: Record<string, ModelMetrics> = {};

    response.data.metrics?.forEach((metric) => {
      metricsMap[metric.modelId] = {
        tokensPerSecond: metric.tokensPerSecond,
        memoryGb: metric.memoryGb,
        latencyMs: metric.latencyMs
      };
    });

    return metricsMap;
  } catch (error) {
    console.error('Failed to fetch model metrics:', error);
    // Return empty object on error (graceful degradation)
    return {};
  }
}

/**
 * Hook for fetching real-time per-model metrics
 * Automatically refetches every 1 second (1Hz update rate)
 *
 * Usage:
 * ```typescript
 * const { data: modelMetrics, isLoading } = useModelMetrics();
 * const metricsForModel = modelMetrics?.[modelId];
 * ```
 *
 * @returns TanStack Query result with ModelMetrics data keyed by modelId
 */
export const useModelMetrics = () => {
  return useQuery<Record<string, ModelMetrics>, Error>({
    queryKey: ['metrics', 'models'],
    queryFn: fetchModelMetrics,
    refetchInterval: 1000,  // 1Hz refresh rate (matches Phase 2 pattern)
    staleTime: 500,          // Data considered fresh for 500ms
    retry: 3,                // Retry failed requests 3 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000), // Exponential backoff
  });
};
