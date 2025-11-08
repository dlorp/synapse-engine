/**
 * React hooks for query submission and management
 */

import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { endpoints } from '../api/endpoints';
import { QueryRequest, QueryResponse } from '../types/query';
import { getQueryTimeout } from '../utils/queryTimeouts';

/**
 * Hook for submitting queries to the backend with tier-specific timeouts
 *
 * Automatically applies appropriate timeout based on query mode:
 * - simple (Q2): 45s
 * - moderate (Q3): 90s
 * - complex (Q4): 180s
 * - auto: 90s (defaults to Q3)
 *
 * @returns Mutation object with submit function and state
 *
 * @example
 * const queryMutation = useQuerySubmit();
 * queryMutation.mutate({
 *   query: "What is Python?",
 *   mode: "auto",
 *   useContext: true,
 *   maxTokens: 512,
 *   temperature: 0.7
 * });
 */
export const useQuerySubmit = (): UseMutationResult<
  QueryResponse,
  Error,
  QueryRequest
> => {
  return useMutation({
    mutationFn: async (request: QueryRequest): Promise<QueryResponse> => {
      // Determine timeout based on query mode
      const timeout = getQueryTimeout(request.mode);

      // Make request with tier-specific timeout
      const response = await apiClient.post<QueryResponse>(
        endpoints.query.execute,
        request,
        {
          timeout, // Override default timeout with tier-specific value
        }
      );

      return response.data;
    },
  });
};
