/**
 * Context utilization hook with real-time polling
 *
 * Fetches context window utilization metrics from backend every 2 seconds.
 * Uses TanStack Query for caching and automatic refetching.
 *
 * @returns Context utilization data including percentage, tokens used/total,
 *          and number of active queries with context allocation.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface ContextUtilization {
  percentage: number;
  tokensUsed: number;
  tokensTotal: number;
  activeQueries: number;
}

const fetchContextUtilization = async (): Promise<ContextUtilization> => {
  const response = await apiClient.get<ContextUtilization>('/metrics/context-utilization');
  return response.data;
};

export const useContextUtilization = () => {
  return useQuery<ContextUtilization, Error>({
    queryKey: ['metrics', 'context-utilization'],
    queryFn: fetchContextUtilization,
    refetchInterval: 2000, // 2 second updates
    staleTime: 1000,
  });
};
