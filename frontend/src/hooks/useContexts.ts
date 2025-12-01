/**
 * React hooks for CGRAG context management.
 *
 * Provides TanStack Query hooks for:
 * - Fetching available CGRAG contexts
 * - Creating new CGRAG indexes
 * - Refreshing existing indexes
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { ContextInfo, CreateContextRequest } from '@/types/codeChat';

/**
 * Hook for fetching available CGRAG contexts.
 *
 * Retrieves all CGRAG indexes with metadata including chunk count,
 * last indexed timestamp, source path, and embedding model used.
 *
 * Results are cached for 1 minute since indexes don't change frequently.
 *
 * @returns Query result with list of contexts
 *
 * @example
 * const { data: contexts, isLoading, error } = useContexts();
 * if (contexts) {
 *   contexts.forEach(ctx => {
 *     console.log(ctx.name, ctx.chunkCount, ctx.lastIndexed);
 *   });
 * }
 */
export const useContexts = (): UseQueryResult<ContextInfo[], Error> => {
  return useQuery<ContextInfo[], Error>({
    queryKey: ['contexts'],
    queryFn: async (): Promise<ContextInfo[]> => {
      try {
        const response = await apiClient.get<ContextInfo[]>(endpoints.codeChat.contexts);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch contexts:', error);
        throw error;
      }
    },
    staleTime: 60000, // Cache for 1 minute
    gcTime: 120000, // Keep in cache for 2 minutes
  });
};

/**
 * Hook for creating a new CGRAG context.
 *
 * Creates a new CGRAG index from a source directory. Indexes all code files
 * using the specified embedding model (defaults to all-MiniLM-L6-v2).
 *
 * Automatically invalidates the contexts cache on success to reflect the
 * new index in the UI.
 *
 * @returns Mutation for creating context
 *
 * @example
 * const createMutation = useCreateContext();
 * createMutation.mutate(
 *   {
 *     name: 'my-project',
 *     sourcePath: '/home/user/my-project',
 *     embeddingModel: 'all-MiniLM-L6-v2'
 *   },
 *   {
 *     onSuccess: (data) => {
 *       console.log('Created context:', data.name);
 *       console.log('Indexed chunks:', data.chunkCount);
 *     },
 *     onError: (error) => {
 *       console.error('Failed to create context:', error);
 *     }
 *   }
 * );
 */
export const useCreateContext = (): UseMutationResult<
  ContextInfo,
  Error,
  CreateContextRequest
> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: CreateContextRequest): Promise<ContextInfo> => {
      try {
        const response = await apiClient.post<ContextInfo>(
          endpoints.codeChat.createContext,
          request
        );
        return response.data;
      } catch (error) {
        console.error('Failed to create context:', error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate contexts cache to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['contexts'] });
    },
  });
};

/**
 * Hook for refreshing an existing CGRAG context.
 *
 * Re-scans the source directory and updates the index with any new or
 * modified files. Useful for keeping indexes in sync with codebase changes.
 *
 * Automatically invalidates the contexts cache on success.
 *
 * @returns Mutation for refreshing context
 *
 * @example
 * const refreshMutation = useRefreshContext();
 * refreshMutation.mutate('my-project', {
 *   onSuccess: (data) => {
 *     console.log('Refreshed context:', data.name);
 *     console.log('New chunk count:', data.chunkCount);
 *   },
 *   onError: (error) => {
 *     console.error('Failed to refresh context:', error);
 *   }
 * });
 */
export const useRefreshContext = (): UseMutationResult<ContextInfo, Error, string> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (name: string): Promise<ContextInfo> => {
      try {
        const response = await apiClient.post<ContextInfo>(
          endpoints.codeChat.refreshContext(name)
        );
        return response.data;
      } catch (error) {
        console.error('Failed to refresh context:', error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate contexts cache to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['contexts'] });
    },
  });
};
