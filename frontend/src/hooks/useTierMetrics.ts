/**
 * Tier metrics hook with real-time polling
 *
 * Fetches model tier performance metrics from backend every 1 second for real-time visualization.
 * Uses TanStack Query for caching and automatic refetching.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { TierMetrics } from '@/types/metrics';

const fetchTierMetrics = async (): Promise<TierMetrics> => {
  const response = await apiClient.get<TierMetrics>('/metrics/tiers');
  return response.data;
};

export const useTierMetrics = () => {
  return useQuery<TierMetrics, Error>({
    queryKey: ['metrics', 'tiers'],
    queryFn: fetchTierMetrics,
    refetchInterval: 1000,  // 1Hz updates
    staleTime: 500,
  });
};
