/**
 * Query metrics hook with real-time polling
 *
 * Fetches query analytics from backend every 1 second for real-time visualization.
 * Uses TanStack Query for caching and automatic refetching.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { QueryMetrics } from '@/types/metrics';

const fetchQueryMetrics = async (): Promise<QueryMetrics> => {
  const response = await apiClient.get<QueryMetrics>('/metrics/queries');
  return response.data;
};

export const useQueryMetrics = () => {
  return useQuery<QueryMetrics, Error>({
    queryKey: ['metrics', 'queries'],
    queryFn: fetchQueryMetrics,
    refetchInterval: 1000,  // 1Hz updates
    staleTime: 500,
  });
};
