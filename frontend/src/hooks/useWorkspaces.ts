/**
 * React hooks for workspace browsing and validation.
 *
 * Provides TanStack Query hooks for:
 * - Fetching directory listings for workspace selection
 * - Validating workspace paths with metadata
 */

import { useQuery } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type {
  WorkspaceListResponse,
  WorkspaceValidation,
} from '@/types/codeChat';

/**
 * Hook for fetching directory listing.
 *
 * Fetches subdirectories of the given path with metadata including
 * git repository status, project type detection, etc.
 *
 * Results are cached for 30 seconds to reduce unnecessary filesystem scans.
 *
 * @param path - Directory path to list (default: '/')
 * @returns Query result with directory listing
 *
 * @example
 * const { data, isLoading, error } = useWorkspaces('/home/user');
 * if (data) {
 *   console.log(data.directories); // Array of DirectoryInfo
 *   console.log(data.parentPath); // Path to parent directory
 * }
 */
export const useWorkspaces = (path: string = '/'): UseQueryResult<WorkspaceListResponse, Error> => {
  return useQuery<WorkspaceListResponse, Error>({
    queryKey: ['workspaces', path],
    queryFn: async (): Promise<WorkspaceListResponse> => {
      try {
        const response = await apiClient.get<WorkspaceListResponse>(
          endpoints.codeChat.workspaces,
          { params: { path } }
        );
        return response.data;
      } catch (error) {
        console.error('Failed to fetch workspaces:', error);
        throw error;
      }
    },
    staleTime: 30000, // Cache for 30 seconds
    gcTime: 60000, // Keep in cache for 1 minute
  });
};

/**
 * Hook for validating a workspace path.
 *
 * Validates that a path is accessible and returns metadata including:
 * - Git repository status
 * - Project info (type, name, dependencies)
 * - File count
 * - CGRAG index availability
 *
 * Query only runs when path is non-empty.
 * Results are cached for 1 minute.
 *
 * @param path - Workspace path to validate
 * @returns Query result with validation details
 *
 * @example
 * const { data, isLoading, error } = useWorkspaceValidation('/home/user/project');
 * if (data?.valid) {
 *   console.log(data.projectInfo); // ProjectInfo object
 *   console.log(data.hasCgragIndex); // boolean
 * }
 */
export const useWorkspaceValidation = (
  path: string
): UseQueryResult<WorkspaceValidation, Error> => {
  return useQuery<WorkspaceValidation, Error>({
    queryKey: ['workspace-validation', path],
    queryFn: async (): Promise<WorkspaceValidation> => {
      try {
        const response = await apiClient.post<WorkspaceValidation>(
          endpoints.codeChat.validateWorkspace,
          null,
          { params: { path } }
        );
        return response.data;
      } catch (error) {
        console.error('Failed to validate workspace:', error);
        throw error;
      }
    },
    enabled: !!path && path.length > 0, // Only run when path provided
    staleTime: 60000, // Cache for 1 minute
    gcTime: 120000, // Keep in cache for 2 minutes
  });
};
