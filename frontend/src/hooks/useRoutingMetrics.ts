/**
 * Routing metrics hook with real-time polling
 *
 * Fetches query routing analytics from backend every 1 second for real-time visualization.
 * Uses TanStack Query for caching and automatic refetching.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { RoutingMetrics } from '@/types/metrics';

const fetchRoutingMetrics = async (): Promise<RoutingMetrics> => {
  const response = await apiClient.get<RoutingMetrics>('/metrics/routing');
  return response.data;
};

export const useRoutingMetrics = () => {
  return useQuery<RoutingMetrics, Error>({
    queryKey: ['metrics', 'routing'],
    queryFn: fetchRoutingMetrics,
    refetchInterval: 1000,  // 1Hz updates
    staleTime: 500,
  });
};
