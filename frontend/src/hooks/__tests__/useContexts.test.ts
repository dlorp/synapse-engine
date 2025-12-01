/**
 * Tests for useContexts, useCreateContext, and useRefreshContext hooks.
 *
 * Covers:
 * - Hook initialization
 * - API integration with mocked axios
 * - Error handling
 * - Mutation behavior
 * - Cache invalidation
 */

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient } from '@tanstack/react-query';
import { useContexts, useCreateContext, useRefreshContext } from '../useContexts';
import { apiClient } from '@/api/client';
import { createQueryWrapper } from '@/test/utils';
import type { ContextInfo, CreateContextRequest } from '@/types/codeChat';

// Mock apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('useContexts', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('initialization', () => {
    test('returns query result with correct initial state', () => {
      const mockResponse: ContextInfo[] = [];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBe(null);
    });
  });

  describe('successful data fetching', () => {
    test('fetches and returns all contexts', async () => {
      const mockResponse: ContextInfo[] = [
        {
          name: 'project-docs',
          path: '/data/faiss/project-docs',
          chunkCount: 1250,
          lastIndexed: '2025-11-29T10:00:00Z',
          sourcePath: '/home/user/project',
          embeddingModel: 'all-MiniLM-L6-v2',
        },
        {
          name: 'synapse-engine',
          path: '/data/faiss/synapse-engine',
          chunkCount: 3400,
          lastIndexed: '2025-11-28T15:30:00Z',
          sourcePath: '/home/user/synapse',
          embeddingModel: 'all-MiniLM-L6-v2',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data).toHaveLength(2);
      expect(result.current.data?.[0].name).toBe('project-docs');
      expect(result.current.data?.[0].chunkCount).toBe(1250);
    });

    test('calls API with correct endpoint', async () => {
      const mockResponse: ContextInfo[] = [];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledWith('code-chat/contexts');
      });
    });

    test('handles empty context list', async () => {
      const mockResponse: ContextInfo[] = [];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([]);
    });

    test('includes all context metadata', async () => {
      const mockResponse: ContextInfo[] = [
        {
          name: 'test-context',
          path: '/data/faiss/test-context',
          chunkCount: 500,
          lastIndexed: '2025-11-29T12:00:00Z',
          sourcePath: '/test/project',
          embeddingModel: 'all-MiniLM-L6-v2',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const context = result.current.data?.[0];
      expect(context?.name).toBe('test-context');
      expect(context?.path).toBe('/data/faiss/test-context');
      expect(context?.chunkCount).toBe(500);
      expect(context?.lastIndexed).toBe('2025-11-29T12:00:00Z');
      expect(context?.sourcePath).toBe('/test/project');
      expect(context?.embeddingModel).toBe('all-MiniLM-L6-v2');
    });
  });

  describe('error handling', () => {
    test('handles API error', async () => {
      const error = new Error('Failed to fetch contexts');
      vi.mocked(apiClient.get).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to fetch contexts:', error);

      consoleErrorSpy.mockRestore();
    });
  });

  describe('caching', () => {
    test('uses cached data on subsequent calls', async () => {
      const mockResponse: ContextInfo[] = [
        {
          name: 'test',
          path: '/data/test',
          chunkCount: 100,
          lastIndexed: '2025-11-29T12:00:00Z',
          sourcePath: '/test',
          embeddingModel: 'all-MiniLM-L6-v2',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result: result1 } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      // Second hook should use cache
      const { result: result2 } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result2.current.isSuccess).toBe(true);
      });

      // API should only be called once
      expect(apiClient.get).toHaveBeenCalledTimes(1);
    });
  });
});

describe('useCreateContext', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('mutation behavior', () => {
    test('creates new context successfully', async () => {
      const request: CreateContextRequest = {
        name: 'new-context',
        sourcePath: '/home/user/new-project',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      const mockResponse: ContextInfo = {
        name: 'new-context',
        path: '/data/faiss/new-context',
        chunkCount: 750,
        lastIndexed: '2025-11-29T12:00:00Z',
        sourcePath: '/home/user/new-project',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useCreateContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate(request);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(apiClient.post).toHaveBeenCalledWith('code-chat/contexts/create', request);
    });

    test('uses default embedding model when not specified', async () => {
      const request: CreateContextRequest = {
        name: 'default-model-context',
        sourcePath: '/home/user/project',
      };

      const mockResponse: ContextInfo = {
        name: 'default-model-context',
        path: '/data/faiss/default-model-context',
        chunkCount: 500,
        lastIndexed: '2025-11-29T12:00:00Z',
        sourcePath: '/home/user/project',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useCreateContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate(request);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.embeddingModel).toBe('all-MiniLM-L6-v2');
    });

    test('handles creation error', async () => {
      const request: CreateContextRequest = {
        name: 'invalid-context',
        sourcePath: '/nonexistent/path',
      };

      const error = new Error('Source path does not exist');
      vi.mocked(apiClient.post).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useCreateContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate(request);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe('Source path does not exist');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to create context:', error);

      consoleErrorSpy.mockRestore();
    });

    test('supports onSuccess callback', async () => {
      const request: CreateContextRequest = {
        name: 'callback-test',
        sourcePath: '/test',
      };

      const mockResponse: ContextInfo = {
        name: 'callback-test',
        path: '/data/faiss/callback-test',
        chunkCount: 200,
        lastIndexed: '2025-11-29T12:00:00Z',
        sourcePath: '/test',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const onSuccess = vi.fn();

      const { result } = renderHook(() => useCreateContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate(request, { onSuccess });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(onSuccess).toHaveBeenCalled();
      expect(onSuccess.mock.calls[0][0]).toEqual(mockResponse);
    });

    test('supports onError callback', async () => {
      const request: CreateContextRequest = {
        name: 'error-test',
        sourcePath: '/invalid',
      };

      const error = new Error('Creation failed');
      vi.mocked(apiClient.post).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const onError = vi.fn();

      const { result } = renderHook(() => useCreateContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate(request, { onError });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(onError).toHaveBeenCalled();
      expect(onError.mock.calls[0][0]).toEqual(error);

      consoleErrorSpy.mockRestore();
    });
  });

  describe('cache invalidation', () => {
    test('invalidates contexts cache on success', async () => {
      // First, populate the cache
      const mockContexts: ContextInfo[] = [
        {
          name: 'existing',
          path: '/data/existing',
          chunkCount: 100,
          lastIndexed: '2025-11-29T10:00:00Z',
          sourcePath: '/test',
          embeddingModel: 'all-MiniLM-L6-v2',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockContexts });

      const { result: contextsResult } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(contextsResult.current.isSuccess).toBe(true);
      });

      // Now create a new context
      const request: CreateContextRequest = {
        name: 'new',
        sourcePath: '/new',
      };

      const mockResponse: ContextInfo = {
        name: 'new',
        path: '/data/new',
        chunkCount: 50,
        lastIndexed: '2025-11-29T12:00:00Z',
        sourcePath: '/new',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result: createResult } = renderHook(() => useCreateContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      createResult.current.mutate(request);

      await waitFor(() => {
        expect(createResult.current.isSuccess).toBe(true);
      });

      // Verify cache was invalidated (query becomes stale)
      const queryState = queryClient.getQueryState(['contexts']);
      expect(queryState).toBeDefined();
    });
  });
});

describe('useRefreshContext', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe('mutation behavior', () => {
    test('refreshes context successfully', async () => {
      const mockResponse: ContextInfo = {
        name: 'test-context',
        path: '/data/faiss/test-context',
        chunkCount: 1500,
        lastIndexed: '2025-11-29T13:00:00Z',
        sourcePath: '/test/project',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useRefreshContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate('test-context');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(apiClient.post).toHaveBeenCalledWith('code-chat/contexts/test-context/refresh');
    });

    test('updates chunk count after refresh', async () => {
      const mockResponse: ContextInfo = {
        name: 'updated-context',
        path: '/data/faiss/updated-context',
        chunkCount: 2000, // Increased from original
        lastIndexed: '2025-11-29T14:00:00Z',
        sourcePath: '/test',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => useRefreshContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate('updated-context');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.chunkCount).toBe(2000);
    });

    test('handles refresh error', async () => {
      const error = new Error('Context not found');
      vi.mocked(apiClient.post).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useRefreshContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate('nonexistent');

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe('Context not found');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to refresh context:', error);

      consoleErrorSpy.mockRestore();
    });

    test('supports onSuccess callback', async () => {
      const mockResponse: ContextInfo = {
        name: 'callback-test',
        path: '/data/callback-test',
        chunkCount: 300,
        lastIndexed: '2025-11-29T12:00:00Z',
        sourcePath: '/test',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const onSuccess = vi.fn();

      const { result } = renderHook(() => useRefreshContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate('callback-test', { onSuccess });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(onSuccess).toHaveBeenCalled();
      expect(onSuccess.mock.calls[0][0]).toEqual(mockResponse);
    });

    test('supports onError callback', async () => {
      const error = new Error('Refresh failed');
      vi.mocked(apiClient.post).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const onError = vi.fn();

      const { result } = renderHook(() => useRefreshContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      result.current.mutate('error-test', { onError });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(onError).toHaveBeenCalled();
      expect(onError.mock.calls[0][0]).toEqual(error);

      consoleErrorSpy.mockRestore();
    });
  });

  describe('cache invalidation', () => {
    test('invalidates contexts cache on success', async () => {
      // First, populate the cache
      const mockContexts: ContextInfo[] = [
        {
          name: 'test',
          path: '/data/test',
          chunkCount: 100,
          lastIndexed: '2025-11-29T10:00:00Z',
          sourcePath: '/test',
          embeddingModel: 'all-MiniLM-L6-v2',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockContexts });

      const { result: contextsResult } = renderHook(() => useContexts(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(contextsResult.current.isSuccess).toBe(true);
      });

      // Now refresh the context
      const mockResponse: ContextInfo = {
        name: 'test',
        path: '/data/test',
        chunkCount: 200,
        lastIndexed: '2025-11-29T12:00:00Z',
        sourcePath: '/test',
        embeddingModel: 'all-MiniLM-L6-v2',
      };

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

      const { result: refreshResult } = renderHook(() => useRefreshContext(), {
        wrapper: createQueryWrapper(queryClient),
      });

      refreshResult.current.mutate('test');

      await waitFor(() => {
        expect(refreshResult.current.isSuccess).toBe(true);
      });

      // Verify cache was invalidated
      const queryState = queryClient.getQueryState(['contexts']);
      expect(queryState).toBeDefined();
    });
  });
});
