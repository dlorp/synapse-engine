/**
 * React hooks for preset management.
 *
 * Provides TanStack Query hooks for:
 * - Fetching all available presets
 * - Fetching specific preset by name
 * - Creating custom presets
 * - Updating custom presets
 * - Deleting custom presets
 * - Managing quick-access presets (localStorage)
 */

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { ModelPreset, ToolName, ToolModelConfig } from '@/types/codeChat';

/**
 * Transform API response from snake_case to camelCase.
 * Backend returns tool_configs, frontend expects toolConfigs.
 */
interface ApiModelPreset {
  name: string;
  description: string;
  system_prompt?: string | null;
  planning_tier: string;
  tool_configs: Record<string, { tier: string; temperature?: number; max_tokens?: number }>;
  is_custom: boolean;
}

const transformPreset = (apiPreset: ApiModelPreset): ModelPreset => {
  const toolConfigs: Partial<Record<ToolName, ToolModelConfig>> = {};

  // Transform tool_configs from snake_case to camelCase
  for (const [toolName, config] of Object.entries(apiPreset.tool_configs)) {
    toolConfigs[toolName as ToolName] = {
      tier: config.tier as 'fast' | 'balanced' | 'powerful',
      temperature: config.temperature,
      maxTokens: config.max_tokens,
    };
  }

  return {
    name: apiPreset.name,
    description: apiPreset.description,
    systemPrompt: apiPreset.system_prompt,
    planningTier: apiPreset.planning_tier as 'fast' | 'balanced' | 'powerful',
    toolConfigs: toolConfigs as Record<ToolName, ToolModelConfig>,
    isCustom: apiPreset.is_custom,
  };
};

/**
 * Transform camelCase preset to snake_case for API.
 */
const transformPresetToApi = (preset: ModelPreset): ApiModelPreset => {
  const tool_configs: Record<string, { tier: string; temperature?: number; max_tokens?: number }> = {};

  // Transform toolConfigs from camelCase to snake_case
  for (const [toolName, config] of Object.entries(preset.toolConfigs)) {
    tool_configs[toolName] = {
      tier: config.tier,
      temperature: config.temperature,
      max_tokens: config.maxTokens,
    };
  }

  return {
    name: preset.name,
    description: preset.description,
    system_prompt: preset.systemPrompt,
    planning_tier: preset.planningTier,
    tool_configs,
    is_custom: preset.isCustom,
  };
};

/**
 * Hook for fetching all available presets.
 *
 * Retrieves both built-in presets (speed, balanced, quality, coding, research)
 * and any custom presets.
 *
 * Results are heavily cached (5 minutes) since presets rarely change.
 *
 * @returns Query result with list of presets
 *
 * @example
 * const { data: presets, isLoading, error } = usePresets();
 * if (presets) {
 *   presets.forEach(preset => {
 *     console.log(preset.name, preset.description);
 *     console.log('Planning tier:', preset.planningTier);
 *   });
 * }
 */
export const usePresets = (): UseQueryResult<ModelPreset[], Error> => {
  return useQuery<ModelPreset[], Error>({
    queryKey: ['presets'],
    queryFn: async (): Promise<ModelPreset[]> => {
      try {
        const response = await apiClient.get<ApiModelPreset[]>(endpoints.codeChat.presets);
        return response.data.map(transformPreset);
      } catch (error) {
        console.error('Failed to fetch presets:', error);
        throw error;
      }
    },
    staleTime: 300000, // Cache for 5 minutes (presets rarely change)
    gcTime: 600000, // Keep in cache for 10 minutes
  });
};

/**
 * Hook for fetching a specific preset.
 *
 * Retrieves configuration for a named preset. Useful for displaying
 * preset details or loading preset configuration for customization.
 *
 * Query only runs when name is provided.
 * Results are heavily cached (5 minutes).
 *
 * @param name - Preset name to fetch
 * @returns Query result with preset configuration
 *
 * @example
 * const { data: preset, isLoading, error } = usePreset('coding');
 * if (preset) {
 *   console.log('Planning tier:', preset.planningTier);
 *   console.log('Tool configs:', preset.toolConfigs);
 * }
 */
export const usePreset = (name: string): UseQueryResult<ModelPreset, Error> => {
  return useQuery<ModelPreset, Error>({
    queryKey: ['presets', name],
    queryFn: async (): Promise<ModelPreset> => {
      try {
        const response = await apiClient.get<ApiModelPreset>(endpoints.codeChat.preset(name));
        return transformPreset(response.data);
      } catch (error) {
        console.error(`Failed to fetch preset '${name}':`, error);
        throw error;
      }
    },
    enabled: !!name, // Only run when name provided
    staleTime: 300000, // Cache for 5 minutes
    gcTime: 600000, // Keep in cache for 10 minutes
  });
};

/**
 * Hook for creating a custom preset.
 *
 * Creates a new user-defined preset that will be persisted to disk.
 * Cannot create presets with names that conflict with built-in presets.
 *
 * Automatically invalidates preset queries on success.
 *
 * @returns Mutation result with create function
 *
 * @example
 * const createPreset = useCreatePreset();
 *
 * const newPreset = {
 *   name: 'fast_coding',
 *   description: 'Ultra-fast code edits',
 *   planningTier: 'fast',
 *   toolConfigs: {},
 *   isCustom: true,
 * };
 *
 * createPreset.mutate(newPreset, {
 *   onSuccess: (created) => {
 *     console.log('Created preset:', created.name);
 *   },
 *   onError: (error) => {
 *     console.error('Failed to create preset:', error.message);
 *   },
 * });
 */
export const useCreatePreset = (): UseMutationResult<ModelPreset, Error, ModelPreset> => {
  const queryClient = useQueryClient();

  return useMutation<ModelPreset, Error, ModelPreset>({
    mutationFn: async (preset: ModelPreset): Promise<ModelPreset> => {
      try {
        const apiPreset = transformPresetToApi(preset);
        const response = await apiClient.post<ApiModelPreset>(
          endpoints.codeChat.presets,
          apiPreset
        );
        return transformPreset(response.data);
      } catch (error) {
        console.error('Failed to create preset:', error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate preset queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['presets'] });
    },
  });
};

/**
 * Hook for updating an existing custom preset.
 *
 * Updates the configuration of a user-created custom preset.
 * Cannot update built-in presets.
 *
 * Automatically invalidates preset queries on success.
 *
 * @returns Mutation result with update function
 *
 * @example
 * const updatePreset = useUpdatePreset();
 *
 * updatePreset.mutate({
 *   name: 'my_preset',
 *   preset: updatedConfig,
 * }, {
 *   onSuccess: (updated) => {
 *     console.log('Updated preset:', updated.name);
 *   },
 *   onError: (error) => {
 *     console.error('Failed to update preset:', error.message);
 *   },
 * });
 */
export const useUpdatePreset = (): UseMutationResult<
  ModelPreset,
  Error,
  { name: string; preset: ModelPreset }
> => {
  const queryClient = useQueryClient();

  return useMutation<ModelPreset, Error, { name: string; preset: ModelPreset }>({
    mutationFn: async ({ name, preset }): Promise<ModelPreset> => {
      try {
        const apiPreset = transformPresetToApi(preset);
        const response = await apiClient.put<ApiModelPreset>(
          endpoints.codeChat.preset(name),
          apiPreset
        );
        return transformPreset(response.data);
      } catch (error) {
        console.error(`Failed to update preset '${name}':`, error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate preset queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['presets'] });
    },
  });
};

/**
 * Hook for deleting a custom preset.
 *
 * Permanently deletes a user-created custom preset.
 * Cannot delete built-in presets.
 *
 * Automatically invalidates preset queries on success.
 *
 * @returns Mutation result with delete function
 *
 * @example
 * const deletePreset = useDeletePreset();
 *
 * deletePreset.mutate('my_preset', {
 *   onSuccess: () => {
 *     console.log('Preset deleted successfully');
 *   },
 *   onError: (error) => {
 *     console.error('Failed to delete preset:', error.message);
 *   },
 * });
 */
export const useDeletePreset = (): UseMutationResult<
  { success: boolean; name: string },
  Error,
  string
> => {
  const queryClient = useQueryClient();

  return useMutation<{ success: boolean; name: string }, Error, string>({
    mutationFn: async (name: string): Promise<{ success: boolean; name: string }> => {
      try {
        const response = await apiClient.delete<{ success: boolean; name: string }>(
          endpoints.codeChat.preset(name)
        );
        return response.data;
      } catch (error) {
        console.error(`Failed to delete preset '${name}':`, error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate preset queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['presets'] });
    },
  });
};

/**
 * Hook for managing quick-access presets (localStorage).
 *
 * Stores user's 5 quick-access presets in localStorage for persistence across sessions.
 * Quick presets appear in the chip bar with keyboard shortcuts 1-5.
 *
 * @returns Object with quick presets state and management functions
 *
 * @example
 * const { quickPresets, setQuickPresets, resetToDefaults } = useQuickPresets();
 *
 * // Display quick presets
 * quickPresets.forEach((presetId, index) => {
 *   console.log(`[${index + 1}] ${presetId}`);
 * });
 *
 * // Customize quick presets
 * setQuickPresets(['SYNAPSE_CODER', 'SYNAPSE_ANALYST', ...]);
 *
 * // Reset to defaults
 * resetToDefaults();
 */
export const useQuickPresets = () => {
  const STORAGE_KEY = 'synapse_quick_presets';
  const DEFAULT_QUICK_PRESETS = [
    'SYNAPSE_DEFAULT',
    'SYNAPSE_ANALYST',
    'SYNAPSE_CODER',
    'SYNAPSE_CREATIVE',
    'SYNAPSE_RESEARCH',
    'SYNAPSE_JUDGE'
  ];

  const [quickPresets, setQuickPresetsState] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : DEFAULT_QUICK_PRESETS;
    } catch {
      return DEFAULT_QUICK_PRESETS;
    }
  });

  const setQuickPresets = useCallback((presets: string[]) => {
    // Ensure exactly 6 presets
    const normalized = presets.slice(0, 6);
    while (normalized.length < 6) {
      normalized.push(DEFAULT_QUICK_PRESETS[normalized.length] ?? 'SYNAPSE_DEFAULT');
    }

    setQuickPresetsState(normalized);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
  }, []);

  const resetToDefaults = useCallback(() => {
    setQuickPresetsState(DEFAULT_QUICK_PRESETS);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    quickPresets,
    setQuickPresets,
    resetToDefaults,
    defaultPresets: DEFAULT_QUICK_PRESETS,
  };
};
