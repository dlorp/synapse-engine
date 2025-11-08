/**
 * React Query hooks for settings management
 *
 * Provides hooks for fetching, updating, and resetting runtime settings
 * with proper cache invalidation and error handling.
 *
 * Settings are user-controlled and persisted to backend, so we don't auto-refetch.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type {
  RuntimeSettings,
  SettingsResponse,
  VRAMEstimateParams,
  VRAMEstimateResponse,
  SettingsSchemaResponse,
  SettingsExportResponse,
  SettingsImportRequest,
} from '@/types/settings';

/**
 * Fetch current runtime settings
 */
const fetchSettings = async (): Promise<SettingsResponse> => {
  try {
    const response = await apiClient.get<SettingsResponse>(endpoints.settings.get);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch settings:', error);
    throw error;
  }
};

/**
 * Hook to fetch current settings
 *
 * Settings are cached and do not auto-refresh since they are user-controlled.
 * Use refetch() to manually refresh if needed.
 *
 * @returns Query result with settings data
 *
 * @example
 * const { data: settingsResponse, isLoading, error } = useSettings();
 * if (settingsResponse?.success) {
 *   console.log(settingsResponse.settings.ctx_size);
 * }
 */
export const useSettings = (): UseQueryResult<SettingsResponse, Error> => {
  return useQuery<SettingsResponse, Error>({
    queryKey: ['settings'],
    queryFn: fetchSettings,
    staleTime: Infinity, // Settings don't auto-refresh (user-controlled)
    gcTime: 1000 * 60 * 30, // Keep in cache for 30 minutes
  });
};

/**
 * Hook to update runtime settings
 *
 * Automatically invalidates settings cache on success.
 * Response includes restart_required flag if changes require server restart.
 *
 * @returns Mutation object with mutate function
 *
 * @example
 * const updateMutation = useUpdateSettings();
 * updateMutation.mutate(
 *   { ctx_size: 8192, n_gpu_layers: 35 },
 *   {
 *     onSuccess: (data) => {
 *       if (data.restart_required) {
 *         alert('Restart required for changes to take effect');
 *       }
 *     }
 *   }
 * );
 */
export const useUpdateSettings = (): UseMutationResult<
  SettingsResponse,
  Error,
  Partial<RuntimeSettings>
> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (settings: Partial<RuntimeSettings>): Promise<SettingsResponse> => {
      try {
        const response = await apiClient.put<SettingsResponse>(
          endpoints.settings.update,
          { settings }
        );
        return response.data;
      } catch (error) {
        console.error('Failed to update settings:', error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate settings cache to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
};

/**
 * Hook to reset settings to defaults
 *
 * Automatically invalidates settings cache on success.
 *
 * @returns Mutation object with mutate function
 *
 * @example
 * const resetMutation = useResetSettings();
 * resetMutation.mutate(undefined, {
 *   onSuccess: () => {
 *     alert('Settings reset to defaults');
 *   }
 * });
 */
export const useResetSettings = (): UseMutationResult<SettingsResponse, Error, void> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (): Promise<SettingsResponse> => {
      try {
        const response = await apiClient.post<SettingsResponse>(endpoints.settings.reset);
        return response.data;
      } catch (error) {
        console.error('Failed to reset settings:', error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate settings cache to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
};

/**
 * Hook to validate settings without saving
 *
 * Useful for client-side validation before user commits changes.
 *
 * @returns Mutation object with mutate function
 *
 * @example
 * const validateMutation = useValidateSettings();
 * validateMutation.mutate(pendingSettings, {
 *   onSuccess: (data) => {
 *     if (!data.success) {
 *       console.log('Validation errors:', data.validation_errors);
 *     }
 *   }
 * });
 */
export const useValidateSettings = (): UseMutationResult<
  SettingsResponse,
  Error,
  Partial<RuntimeSettings>
> => {
  return useMutation({
    mutationFn: async (settings: Partial<RuntimeSettings>): Promise<SettingsResponse> => {
      try {
        const response = await apiClient.post<SettingsResponse>(
          endpoints.settings.validate,
          { settings }
        );
        return response.data;
      } catch (error) {
        console.error('Failed to validate settings:', error);
        throw error;
      }
    },
  });
};

/**
 * Fetch JSON schema for settings validation
 *
 * Schema is heavily cached as it rarely changes.
 * Useful for building dynamic forms with validation.
 *
 * @returns Query result with JSON schema
 *
 * @example
 * const { data: schemaResponse } = useSettingsSchema();
 * if (schemaResponse?.success) {
 *   console.log(schemaResponse.schema);
 * }
 */
export const useSettingsSchema = (): UseQueryResult<SettingsSchemaResponse, Error> => {
  return useQuery<SettingsSchemaResponse, Error>({
    queryKey: ['settingsSchema'],
    queryFn: async () => {
      try {
        const response = await apiClient.get<SettingsSchemaResponse>(endpoints.settings.schema);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch settings schema:', error);
        throw error;
      }
    },
    staleTime: 1000 * 60 * 60, // Cache for 1 hour (schema rarely changes)
    gcTime: 1000 * 60 * 60 * 2, // Keep in cache for 2 hours
  });
};

/**
 * Estimate VRAM requirements for a model configuration
 *
 * Query only runs when both modelSize and quantization are provided.
 * Does not cache results (always fresh calculation).
 *
 * @param modelSize Model size in billions (e.g., 8.0) - undefined to disable query
 * @param quantization Quantization type (e.g., "Q4_K_M") - undefined to disable query
 * @returns Query result with VRAM estimate
 *
 * @example
 * const { data: estimate, isLoading } = useVRAMEstimate(8.0, "Q4_K_M");
 * if (estimate?.success) {
 *   console.log(`Estimated VRAM: ${estimate.vram_gb} GB`);
 * }
 */
export const useVRAMEstimate = (
  modelSize?: number,
  quantization?: string
): UseQueryResult<VRAMEstimateResponse, Error> => {
  return useQuery<VRAMEstimateResponse, Error>({
    queryKey: ['vramEstimate', modelSize, quantization],
    queryFn: async () => {
      if (!modelSize || !quantization) {
        throw new Error('Model size and quantization are required');
      }

      try {
        const params: VRAMEstimateParams = {
          model_size_b: modelSize,
          quantization: quantization,
        };

        const response = await apiClient.get<VRAMEstimateResponse>(
          endpoints.settings.vramEstimate,
          { params }
        );
        return response.data;
      } catch (error) {
        console.error('Failed to estimate VRAM:', error);
        throw error;
      }
    },
    enabled: !!modelSize && !!quantization, // Only run when both params provided
    staleTime: 0, // Always fetch fresh (calculation is deterministic but cheap)
  });
};

/**
 * Export current settings as JSON string
 *
 * @returns Mutation object with mutate function
 *
 * @example
 * const exportMutation = useExportSettings();
 * exportMutation.mutate(undefined, {
 *   onSuccess: (data) => {
 *     if (data.success) {
 *       // Download or display JSON
 *       console.log(data.json_data);
 *     }
 *   }
 * });
 */
export const useExportSettings = (): UseMutationResult<SettingsExportResponse, Error, void> => {
  return useMutation({
    mutationFn: async (): Promise<SettingsExportResponse> => {
      try {
        const response = await apiClient.get<SettingsExportResponse>(endpoints.settings.export);
        return response.data;
      } catch (error) {
        console.error('Failed to export settings:', error);
        throw error;
      }
    },
  });
};

/**
 * Import settings from JSON string
 *
 * Validates the JSON and settings schema before importing.
 * Does NOT save automatically - use updateSettings to save.
 *
 * @returns Mutation object with mutate function
 *
 * @example
 * const importMutation = useImportSettings();
 * importMutation.mutate(jsonString, {
 *   onSuccess: (data) => {
 *     if (data.success) {
 *       // Settings validated, now save them
 *       updateSettings(data.settings);
 *     }
 *   }
 * });
 */
export const useImportSettings = (): UseMutationResult<
  SettingsResponse,
  Error,
  string
> => {
  return useMutation({
    mutationFn: async (jsonData: string): Promise<SettingsResponse> => {
      try {
        const request: SettingsImportRequest = { json_data: jsonData };
        const response = await apiClient.post<SettingsResponse>(
          endpoints.settings.import,
          request
        );
        return response.data;
      } catch (error) {
        console.error('Failed to import settings:', error);
        throw error;
      }
    },
  });
};

/**
 * Hook to restart all model servers
 *
 * Automatically invalidates server status and model registry queries on success.
 *
 * @returns Mutation object with mutate function
 *
 * @example
 * const restartMutation = useRestartServers();
 * restartMutation.mutate(undefined, {
 *   onSuccess: () => {
 *     alert('Servers restarting...');
 *   }
 * });
 */
export const useRestartServers = (): UseMutationResult<void, Error, void> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (): Promise<void> => {
      try {
        await apiClient.post(endpoints.admin.restartServers);
      } catch (error) {
        console.error('Failed to restart servers:', error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate queries that depend on server state
      queryClient.invalidateQueries({ queryKey: ['serverStatus'] });
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });
};
