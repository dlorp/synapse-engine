/**
 * Tests for useWorkspaces and useWorkspaceValidation hooks.
 *
 * Covers:
 * - Hook initialization
 * - API integration with mocked axios
 * - Error handling
 * - Caching behavior
 * - Query enabling/disabling
 */

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient } from '@tanstack/react-query';
import { useWorkspaces, useWorkspaceValidation } from '../useWorkspaces';
import { apiClient } from '@/api/client';
import { createQueryWrapper } from '@/test/utils';
import type { WorkspaceListResponse, WorkspaceValidation } from '@/types/codeChat';

// Mock apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('useWorkspaces', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('initialization', () => {
    test('returns query result with correct initial state', () => {
      const mockResponse: WorkspaceListResponse = {
        currentPath: '/home/user',
        directories: [],
        parentPath: '/home',
        isGitRepo: false,
        projectType: null,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useWorkspaces('/home/user'), {
        wrapper: createQueryWrapper(queryClient),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBe(null);
    });

    test('uses default path "/" when no path provided', async () => {
      const mockResponse: WorkspaceListResponse = {
        currentPath: '/',
        directories: [],
        parentPath: null,
        isGitRepo: false,
        projectType: null,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useWorkspaces(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(apiClient.get).toHaveBeenCalledWith('code-chat/workspaces', {
        params: { path: '/' },
      });
    });
  });

  describe('successful data fetching', () => {
    test('fetches and returns workspace listing', async () => {
      const mockResponse: WorkspaceListResponse = {
        currentPath: '/home/user/projects',
        directories: [
          {
            name: 'project1',
            path: '/home/user/projects/project1',
            isDirectory: true,
            isGitRepo: true,
            projectType: 'node',
          },
          {
            name: 'project2',
            path: '/home/user/projects/project2',
            isDirectory: true,
            isGitRepo: false,
            projectType: 'python',
          },
        ],
        parentPath: '/home/user',
        isGitRepo: false,
        projectType: null,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useWorkspaces('/home/user/projects'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data?.directories).toHaveLength(2);
      expect(result.current.data?.directories[0].name).toBe('project1');
      expect(result.current.data?.directories[0].isGitRepo).toBe(true);
    });

    test('calls API with correct endpoint and params', async () => {
      const mockResponse: WorkspaceListResponse = {
        currentPath: '/test/path',
        directories: [],
        parentPath: '/test',
        isGitRepo: false,
        projectType: null,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      renderHook(() => useWorkspaces('/test/path'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledWith('code-chat/workspaces', {
          params: { path: '/test/path' },
        });
      });
    });

    test('detects git repository', async () => {
      const mockResponse: WorkspaceListResponse = {
        currentPath: '/home/user/my-repo',
        directories: [],
        parentPath: '/home/user',
        isGitRepo: true,
        projectType: 'node',
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useWorkspaces('/home/user/my-repo'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.isGitRepo).toBe(true);
      expect(result.current.data?.projectType).toBe('node');
    });

    test('handles empty directory listing', async () => {
      const mockResponse: WorkspaceListResponse = {
        currentPath: '/empty/dir',
        directories: [],
        parentPath: '/empty',
        isGitRepo: false,
        projectType: null,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useWorkspaces('/empty/dir'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.directories).toEqual([]);
    });
  });

  describe('error handling', () => {
    test('handles API error', async () => {
      const error = new Error('Failed to list workspaces');
      vi.mocked(apiClient.get).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useWorkspaces('/invalid/path'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to fetch workspaces:', error);

      consoleErrorSpy.mockRestore();
    });

    test('handles network error', async () => {
      const networkError = new Error('Network error');
      vi.mocked(apiClient.get).mockRejectedValue(networkError);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useWorkspaces('/test'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe('Network error');

      consoleErrorSpy.mockRestore();
    });
  });

  describe('caching', () => {
    test('uses cached data for same path', async () => {
      const mockResponse: WorkspaceListResponse = {
        currentPath: '/test',
        directories: [],
        parentPath: null,
        isGitRepo: false,
        projectType: null,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result: result1 } = renderHook(() => useWorkspaces('/test'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      // Second hook with same path should use cache
      const { result: result2 } = renderHook(() => useWorkspaces('/test'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result2.current.isSuccess).toBe(true);
      });

      // API should only be called once
      expect(apiClient.get).toHaveBeenCalledTimes(1);
    });

    test('makes separate requests for different paths', async () => {
      const mockResponse1: WorkspaceListResponse = {
        currentPath: '/test1',
        directories: [],
        parentPath: null,
        isGitRepo: false,
        projectType: null,
      };

      const mockResponse2: WorkspaceListResponse = {
        currentPath: '/test2',
        directories: [],
        parentPath: null,
        isGitRepo: false,
        projectType: null,
      };

      vi.mocked(apiClient.get)
        .mockResolvedValueOnce({ data: mockResponse1 })
        .mockResolvedValueOnce({ data: mockResponse2 });

      renderHook(() => useWorkspaces('/test1'), {
        wrapper: createQueryWrapper(queryClient),
      });

      renderHook(() => useWorkspaces('/test2'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledTimes(2);
      });

      expect(apiClient.get).toHaveBeenCalledWith('code-chat/workspaces', {
        params: { path: '/test1' },
      });
      expect(apiClient.get).toHaveBeenCalledWith('code-chat/workspaces', {
        params: { path: '/test2' },
      });
    });
  });
});

describe('useWorkspaceValidation', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('initialization', () => {
    test('does not fetch when path is empty', () => {
      renderHook(() => useWorkspaceValidation(''), {
        wrapper: createQueryWrapper(queryClient),
      });

      expect(apiClient.post).not.toHaveBeenCalled();
    });

    test('fetches when path is provided', async () => {
      const mockResponse: WorkspaceValidation = {
        valid: true,
        isGitRepo: false,
        projectInfo: null,
        fileCount: 0,
        hasCgragIndex: false,
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      renderHook(() => useWorkspaceValidation('/test'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.post).toHaveBeenCalled();
      });
    });
  });

  describe('successful validation', () => {
    test('validates workspace successfully', async () => {
      const mockResponse: WorkspaceValidation = {
        valid: true,
        isGitRepo: true,
        projectInfo: {
          type: 'node',
          name: 'my-project',
          version: '1.0.0',
          dependencies: ['react', 'axios'],
          devDependencies: ['vite', 'typescript'],
          scripts: { dev: 'vite', build: 'tsc && vite build' },
          entryPoints: ['src/main.tsx'],
        },
        fileCount: 150,
        hasCgragIndex: true,
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useWorkspaceValidation('/home/user/my-project'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data?.valid).toBe(true);
      expect(result.current.data?.projectInfo?.name).toBe('my-project');
      expect(result.current.data?.projectInfo?.dependencies).toContain('react');
    });

    test('calls API with correct endpoint and params', async () => {
      const mockResponse: WorkspaceValidation = {
        valid: true,
        isGitRepo: false,
        projectInfo: null,
        fileCount: 0,
        hasCgragIndex: false,
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      renderHook(() => useWorkspaceValidation('/test/path'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.post).toHaveBeenCalledWith('code-chat/workspaces/validate', null, {
          params: { path: '/test/path' },
        });
      });
    });

    test('detects invalid workspace', async () => {
      const mockResponse: WorkspaceValidation = {
        valid: false,
        isGitRepo: false,
        projectInfo: null,
        fileCount: 0,
        hasCgragIndex: false,
        error: 'Path does not exist',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useWorkspaceValidation('/invalid/path'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.valid).toBe(false);
      expect(result.current.data?.error).toBe('Path does not exist');
    });

    test('detects CGRAG index availability', async () => {
      const mockResponse: WorkspaceValidation = {
        valid: true,
        isGitRepo: true,
        projectInfo: null,
        fileCount: 250,
        hasCgragIndex: true,
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useWorkspaceValidation('/indexed/project'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.hasCgragIndex).toBe(true);
    });
  });

  describe('error handling', () => {
    test('handles API error', async () => {
      const error = new Error('Failed to validate workspace');
      vi.mocked(apiClient.post).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useWorkspaceValidation('/test'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to validate workspace:', error);

      consoleErrorSpy.mockRestore();
    });
  });

  describe('query enabling/disabling', () => {
    test('disables query when path is empty string', () => {
      renderHook(() => useWorkspaceValidation(''), {
        wrapper: createQueryWrapper(queryClient),
      });

      expect(apiClient.post).not.toHaveBeenCalled();
    });

    test('enables query when path becomes non-empty', async () => {
      const mockResponse: WorkspaceValidation = {
        valid: true,
        isGitRepo: false,
        projectInfo: null,
        fileCount: 0,
        hasCgragIndex: false,
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { rerender } = renderHook(({ path }) => useWorkspaceValidation(path), {
        wrapper: createQueryWrapper(queryClient),
        initialProps: { path: '' },
      });

      expect(apiClient.post).not.toHaveBeenCalled();

      // Change path to non-empty
      rerender({ path: '/test' });

      await waitFor(() => {
        expect(apiClient.post).toHaveBeenCalled();
      });
    });
  });

  describe('caching', () => {
    test('uses cached validation result', async () => {
      const mockResponse: WorkspaceValidation = {
        valid: true,
        isGitRepo: false,
        projectInfo: null,
        fileCount: 0,
        hasCgragIndex: false,
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result: result1 } = renderHook(() => useWorkspaceValidation('/test'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      // Second hook should use cache
      const { result: result2 } = renderHook(() => useWorkspaceValidation('/test'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result2.current.isSuccess).toBe(true);
      });

      // API should only be called once
      expect(apiClient.post).toHaveBeenCalledTimes(1);
    });
  });
});
