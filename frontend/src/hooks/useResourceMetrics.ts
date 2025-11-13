/**
 * Resource metrics hook with real-time polling
 *
 * Fetches resource utilization metrics from backend every 1 second for real-time visualization.
 * Uses TanStack Query for caching and automatic refetching.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { ResourceMetrics } from '@/types/metrics';

const fetchResourceMetrics = async (): Promise<ResourceMetrics> => {
  const response = await apiClient.get<ResourceMetrics>('/metrics/resources');
  return response.data;
};

export const useResourceMetrics = () => {
  return useQuery<ResourceMetrics, Error>({
    queryKey: ['metrics', 'resources'],
    queryFn: fetchResourceMetrics,
    refetchInterval: 1000,  // 1Hz updates
    staleTime: 500,
  });
};
