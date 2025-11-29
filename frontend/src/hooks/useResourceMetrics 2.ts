/**
 * TanStack Query hook for fetching resource metrics
 * Polls backend every 1 second for real-time system resource data
 */

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { ResourceMetrics } from '@/types/metrics';

/**
 * Fetch resource metrics from backend
 * Endpoint: GET /api/metrics/resources
 */
async function fetchResourceMetrics(): Promise<ResourceMetrics> {
  const { data } = await axios.get<ResourceMetrics>('/api/metrics/resources');
  return data;
}

/**
 * Hook for fetching real-time resource metrics
 * Automatically refetches every 1 second (1Hz update rate)
 *
 * @returns TanStack Query result with ResourceMetrics data
 */
export const useResourceMetrics = () => {
  return useQuery<ResourceMetrics, Error>({
    queryKey: ['metrics', 'resources'],
    queryFn: fetchResourceMetrics,
    refetchInterval: 1000,  // 1Hz refresh rate
    staleTime: 500,          // Data considered fresh for 500ms
    retry: 3,                // Retry failed requests 3 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000), // Exponential backoff
  });
};
