/**
 * Model status hook with real-time polling
 *
 * Fetches model status from backend every 5 seconds.
 * Backend response already uses camelCase (Pydantic aliases), so no conversion needed.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { ModelStatusResponse } from '@/types/models';

const fetchModelStatus = async (): Promise<ModelStatusResponse> => {
  try {
    const response = await apiClient.get<ModelStatusResponse>(endpoints.models.status);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch model status:', error);
    throw error;
  }
};

export const useModelStatus = () => {
  return useQuery<ModelStatusResponse, Error>({
    queryKey: ['modelStatus'],
    queryFn: fetchModelStatus,
    refetchInterval: 5000, // Refetch every 5 seconds
    staleTime: 3000,
  });
};
