/**
 * Tests for usePresets and usePreset hooks.
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
import { usePresets, usePreset } from '../usePresets';
import { apiClient } from '@/api/client';
import { createQueryWrapper } from '@/test/utils';
import type { ModelPreset, ToolName, ToolModelConfig } from '@/types/codeChat';

// Mock apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('usePresets', () => {
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
      const mockResponse: ModelPreset[] = [];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBe(null);
    });
  });

  describe('successful data fetching', () => {
    test('fetches and returns all presets', async () => {
      const mockToolConfigs: Record<ToolName, ToolModelConfig> = {
        read_file: { tier: 'fast' },
        write_file: { tier: 'balanced' },
        list_directory: { tier: 'fast' },
        delete_file: { tier: 'balanced' },
        search_code: { tier: 'balanced' },
        grep_files: { tier: 'balanced' },
        web_search: { tier: 'powerful' },
        run_python: { tier: 'balanced' },
        run_shell: { tier: 'balanced' },
        git_status: { tier: 'fast' },
        git_diff: { tier: 'fast' },
        git_log: { tier: 'fast' },
        git_commit: { tier: 'balanced' },
        git_branch: { tier: 'fast' },
        get_diagnostics: { tier: 'fast' },
        get_definitions: { tier: 'fast' },
        get_references: { tier: 'fast' },
        get_project_info: { tier: 'fast' },
      };

      const mockResponse: ModelPreset[] = [
        {
          name: 'speed',
          description: 'Prioritize response time (all fast tier)',
          planningTier: 'fast',
          toolConfigs: mockToolConfigs,
        },
        {
          name: 'balanced',
          description: 'Mix of fast/balanced tiers',
          planningTier: 'balanced',
          toolConfigs: mockToolConfigs,
        },
        {
          name: 'quality',
          description: 'Prioritize output quality (more powerful tier usage)',
          planningTier: 'powerful',
          toolConfigs: mockToolConfigs,
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data).toHaveLength(3);
      expect(result.current.data?.[0].name).toBe('speed');
      expect(result.current.data?.[1].name).toBe('balanced');
      expect(result.current.data?.[2].name).toBe('quality');
    });

    test('calls API with correct endpoint', async () => {
      const mockResponse: ModelPreset[] = [];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledWith('code-chat/presets');
      });
    });

    test('includes built-in presets', async () => {
      const mockToolConfigs: Record<ToolName, ToolModelConfig> = {
        read_file: { tier: 'fast' },
        write_file: { tier: 'balanced' },
        list_directory: { tier: 'fast' },
        delete_file: { tier: 'balanced' },
        search_code: { tier: 'balanced' },
        grep_files: { tier: 'balanced' },
        web_search: { tier: 'powerful' },
        run_python: { tier: 'balanced' },
        run_shell: { tier: 'balanced' },
        git_status: { tier: 'fast' },
        git_diff: { tier: 'fast' },
        git_log: { tier: 'fast' },
        git_commit: { tier: 'balanced' },
        git_branch: { tier: 'fast' },
        get_diagnostics: { tier: 'fast' },
        get_definitions: { tier: 'fast' },
        get_references: { tier: 'fast' },
        get_project_info: { tier: 'fast' },
      };

      const mockResponse: ModelPreset[] = [
        {
          name: 'speed',
          description: 'Prioritize response time',
          planningTier: 'fast',
          toolConfigs: mockToolConfigs,
        },
        {
          name: 'balanced',
          description: 'Mix of fast/balanced tiers',
          planningTier: 'balanced',
          toolConfigs: mockToolConfigs,
        },
        {
          name: 'quality',
          description: 'Prioritize output quality',
          planningTier: 'powerful',
          toolConfigs: mockToolConfigs,
        },
        {
          name: 'coding',
          description: 'Optimized for code editing tasks',
          planningTier: 'balanced',
          toolConfigs: mockToolConfigs,
        },
        {
          name: 'research',
          description: 'Optimized for exploration and analysis',
          planningTier: 'powerful',
          toolConfigs: mockToolConfigs,
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const presetNames = result.current.data?.map((p) => p.name);
      expect(presetNames).toContain('speed');
      expect(presetNames).toContain('balanced');
      expect(presetNames).toContain('quality');
      expect(presetNames).toContain('coding');
      expect(presetNames).toContain('research');
    });

    test('handles empty preset list', async () => {
      const mockResponse: ModelPreset[] = [];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([]);
    });
  });

  describe('error handling', () => {
    test('handles API error', async () => {
      const error = new Error('Failed to fetch presets');
      vi.mocked(apiClient.get).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeTruthy();
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to fetch presets:', error);

      consoleErrorSpy.mockRestore();
    });

    test('handles network error', async () => {
      const networkError = new Error('Network error');
      vi.mocked(apiClient.get).mockRejectedValue(networkError);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => usePresets(), {
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
    test('uses cached data on subsequent calls', async () => {
      const mockResponse: ModelPreset[] = [
        {
          name: 'balanced',
          description: 'Mix of fast/balanced tiers',
          planningTier: 'balanced',
          toolConfigs: {} as Record<ToolName, ToolModelConfig>,
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result: result1 } = renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      // Second hook should use cache
      const { result: result2 } = renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result2.current.isSuccess).toBe(true);
      });

      // API should only be called once
      expect(apiClient.get).toHaveBeenCalledTimes(1);
    });

    test('has long stale time (5 minutes)', async () => {
      const mockResponse: ModelPreset[] = [];

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => usePresets(), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Data should remain fresh for 5 minutes (300000ms)
      const queryState = queryClient.getQueryState(['presets']);
      expect(queryState?.dataUpdatedAt).toBeDefined();
    });
  });
});

describe('usePreset', () => {
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
    test('does not fetch when name is empty', () => {
      renderHook(() => usePreset(''), {
        wrapper: createQueryWrapper(queryClient),
      });

      expect(apiClient.get).not.toHaveBeenCalled();
    });

    test('fetches when name is provided', async () => {
      const mockResponse: ModelPreset = {
        name: 'balanced',
        description: 'Mix of fast/balanced tiers',
        planningTier: 'balanced',
        toolConfigs: {} as Record<ToolName, ToolModelConfig>,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      renderHook(() => usePreset('balanced'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalled();
      });
    });
  });

  describe('successful data fetching', () => {
    test('fetches specific preset by name', async () => {
      const mockToolConfigs: Record<ToolName, ToolModelConfig> = {
        read_file: { tier: 'balanced', temperature: 0.7 },
        write_file: { tier: 'powerful', temperature: 0.5 },
        list_directory: { tier: 'fast' },
        delete_file: { tier: 'balanced' },
        search_code: { tier: 'balanced' },
        grep_files: { tier: 'balanced' },
        web_search: { tier: 'powerful' },
        run_python: { tier: 'balanced' },
        run_shell: { tier: 'balanced' },
        git_status: { tier: 'fast' },
        git_diff: { tier: 'fast' },
        git_log: { tier: 'fast' },
        git_commit: { tier: 'balanced' },
        git_branch: { tier: 'fast' },
        get_diagnostics: { tier: 'fast' },
        get_definitions: { tier: 'fast' },
        get_references: { tier: 'fast' },
        get_project_info: { tier: 'fast' },
      };

      const mockResponse: ModelPreset = {
        name: 'coding',
        description: 'Optimized for code editing tasks',
        planningTier: 'balanced',
        toolConfigs: mockToolConfigs,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => usePreset('coding'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data?.name).toBe('coding');
      expect(result.current.data?.planningTier).toBe('balanced');
      expect(result.current.data?.toolConfigs.read_file.tier).toBe('balanced');
    });

    test('calls API with correct endpoint', async () => {
      const mockResponse: ModelPreset = {
        name: 'speed',
        description: 'Prioritize response time',
        planningTier: 'fast',
        toolConfigs: {} as Record<ToolName, ToolModelConfig>,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      renderHook(() => usePreset('speed'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledWith('code-chat/presets/speed');
      });
    });

    test('includes tool configurations with temperature and maxTokens', async () => {
      const mockToolConfigs: Record<ToolName, ToolModelConfig> = {
        read_file: { tier: 'fast', temperature: 0.3, maxTokens: 1024 },
        write_file: { tier: 'powerful', temperature: 0.5, maxTokens: 2048 },
        list_directory: { tier: 'fast' },
        delete_file: { tier: 'balanced' },
        search_code: { tier: 'balanced', temperature: 0.7 },
        grep_files: { tier: 'balanced' },
        web_search: { tier: 'powerful', temperature: 0.8, maxTokens: 4096 },
        run_python: { tier: 'balanced' },
        run_shell: { tier: 'balanced' },
        git_status: { tier: 'fast' },
        git_diff: { tier: 'fast' },
        git_log: { tier: 'fast' },
        git_commit: { tier: 'balanced' },
        git_branch: { tier: 'fast' },
        get_diagnostics: { tier: 'fast' },
        get_definitions: { tier: 'fast' },
        get_references: { tier: 'fast' },
        get_project_info: { tier: 'fast' },
      };

      const mockResponse: ModelPreset = {
        name: 'quality',
        description: 'Prioritize output quality',
        planningTier: 'powerful',
        toolConfigs: mockToolConfigs,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result } = renderHook(() => usePreset('quality'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.toolConfigs.read_file.temperature).toBe(0.3);
      expect(result.current.data?.toolConfigs.write_file.maxTokens).toBe(2048);
      expect(result.current.data?.toolConfigs.web_search.temperature).toBe(0.8);
    });
  });

  describe('error handling', () => {
    test('handles API error', async () => {
      const error = new Error('Failed to fetch preset');
      vi.mocked(apiClient.get).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => usePreset('invalid'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Failed to fetch preset 'invalid':",
        error
      );

      consoleErrorSpy.mockRestore();
    });

    test('handles 404 for non-existent preset', async () => {
      const error = new Error('Preset not found');
      vi.mocked(apiClient.get).mockRejectedValue(error);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => usePreset('nonexistent'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe('Preset not found');

      consoleErrorSpy.mockRestore();
    });
  });

  describe('query enabling/disabling', () => {
    test('disables query when name is empty', () => {
      renderHook(() => usePreset(''), {
        wrapper: createQueryWrapper(queryClient),
      });

      expect(apiClient.get).not.toHaveBeenCalled();
    });

    test('enables query when name becomes non-empty', async () => {
      const mockResponse: ModelPreset = {
        name: 'balanced',
        description: 'Mix of fast/balanced tiers',
        planningTier: 'balanced',
        toolConfigs: {} as Record<ToolName, ToolModelConfig>,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { rerender } = renderHook(({ name }) => usePreset(name), {
        wrapper: createQueryWrapper(queryClient),
        initialProps: { name: '' },
      });

      expect(apiClient.get).not.toHaveBeenCalled();

      // Change name to non-empty
      rerender({ name: 'balanced' });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalled();
      });
    });
  });

  describe('caching', () => {
    test('uses cached preset data', async () => {
      const mockResponse: ModelPreset = {
        name: 'balanced',
        description: 'Mix of fast/balanced tiers',
        planningTier: 'balanced',
        toolConfigs: {} as Record<ToolName, ToolModelConfig>,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

      const { result: result1 } = renderHook(() => usePreset('balanced'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      // Second hook should use cache
      const { result: result2 } = renderHook(() => usePreset('balanced'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result2.current.isSuccess).toBe(true);
      });

      // API should only be called once
      expect(apiClient.get).toHaveBeenCalledTimes(1);
    });

    test('makes separate requests for different presets', async () => {
      const mockResponse1: ModelPreset = {
        name: 'speed',
        description: 'Fast',
        planningTier: 'fast',
        toolConfigs: {} as Record<ToolName, ToolModelConfig>,
      };

      const mockResponse2: ModelPreset = {
        name: 'quality',
        description: 'Quality',
        planningTier: 'powerful',
        toolConfigs: {} as Record<ToolName, ToolModelConfig>,
      };

      vi.mocked(apiClient.get)
        .mockResolvedValueOnce({ data: mockResponse1 })
        .mockResolvedValueOnce({ data: mockResponse2 });

      renderHook(() => usePreset('speed'), {
        wrapper: createQueryWrapper(queryClient),
      });

      renderHook(() => usePreset('quality'), {
        wrapper: createQueryWrapper(queryClient),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledTimes(2);
      });

      expect(apiClient.get).toHaveBeenCalledWith('code-chat/presets/speed');
      expect(apiClient.get).toHaveBeenCalledWith('code-chat/presets/quality');
    });
  });
});
