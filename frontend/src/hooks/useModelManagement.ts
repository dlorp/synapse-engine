import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type {
  ModelRegistry,
  ServerStatusResponse,
  Profile,
  ModelTier,
  RuntimeSettingsUpdateRequest,
  PortUpdateRequest,
  GlobalRuntimeSettings,
  ExternalServerStatusResponse
} from '@/types/models';

/**
 * Fetch the complete model registry with all discovered models
 * Refetches every 30 seconds to stay in sync with backend
 */
export const useModelRegistry = () => {
  return useQuery<ModelRegistry>({
    queryKey: ['modelRegistry'],
    queryFn: async () => {
      const response = await apiClient.get('/models/registry');
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30s
    staleTime: 10000, // Consider data stale after 10s
  });
};

/**
 * Trigger a re-scan of the HUB directory for new models
 * Invalidates the registry cache on success
 */
export const useRescanModels = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/models/rescan');
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch the registry after successful scan
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
    },
  });
};

/**
 * Update a model's assigned tier (fast/balanced/powerful)
 * Sets a tier override that persists in the registry
 */
export const useUpdateTier = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ modelId, tier }: { modelId: string; tier: ModelTier }) => {
      const response = await apiClient.put(`/models/${modelId}/tier`, { tier });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
    },
  });
};

/**
 * Toggle a model's thinking capability
 * Sets a thinking override that persists in the registry
 */
export const useUpdateThinking = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ modelId, thinking }: { modelId: string; thinking: boolean }) => {
      const response = await apiClient.put(`/models/${modelId}/thinking`, { thinking });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
    },
  });
};

/**
 * Enable or disable a model
 * Disabled models won't be started by the server manager
 */
export const useToggleEnabled = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ modelId, enabled }: { modelId: string; enabled: boolean }) => {
      const response = await apiClient.put(`/models/${modelId}/enabled`, { enabled });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
      // Also invalidate server status since this affects running servers
      queryClient.invalidateQueries({ queryKey: ['serverStatus'] });
    },
  });
};

/**
 * Fetch real-time status of all running model servers
 * Refetches every 5 seconds for live updates
 */
export const useServerStatus = () => {
  return useQuery<ServerStatusResponse>({
    queryKey: ['serverStatus'],
    queryFn: async () => {
      const response = await apiClient.get('/models/servers');
      return response.data;
    },
    refetchInterval: 5000, // Refetch every 5s for real-time updates
    staleTime: 2000, // Consider data stale after 2s
  });
};

/**
 * Fetch list of available profile names
 */
export const useProfiles = () => {
  return useQuery<string[]>({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await apiClient.get('/models/profiles');
      return response.data;
    },
  });
};

/**
 * Fetch detailed configuration for a specific profile
 * Only fetches if a profile name is provided
 */
export const useProfile = (name?: string) => {
  return useQuery<Profile>({
    queryKey: ['profile', name],
    queryFn: async () => {
      if (!name) throw new Error('Profile name required');
      const response = await apiClient.get(`/models/profiles/${name}`);
      return response.data;
    },
    enabled: !!name, // Only run query if name is provided
  });
};

/**
 * Phase 2: Fetch global runtime settings (defaults)
 * These are the fallback values when per-model overrides are not set
 */
export const useRuntimeSettings = () => {
  return useQuery<GlobalRuntimeSettings>({
    queryKey: ['runtimeSettings'],
    queryFn: async () => {
      const response = await apiClient.get('/settings');
      return response.data;
    },
    staleTime: 60000, // Consider data stale after 1 minute
  });
};

/**
 * Phase 2: Update a model's port assignment
 * Invalidates registry cache on success
 */
export const useUpdateModelPort = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ modelId, port }: { modelId: string; port: number }) => {
      const payload: PortUpdateRequest = { port };
      const response = await apiClient.put(`/models/${modelId}/port`, payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
    },
  });
};

/**
 * Phase 2: Update a model's runtime settings (per-model overrides)
 * All fields are optional - only include fields to update
 * Set fields to null to revert to global defaults
 * Invalidates registry cache on success
 */
export const useUpdateModelRuntimeSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      modelId,
      settings,
    }: {
      modelId: string;
      settings: RuntimeSettingsUpdateRequest;
    }) => {
      const response = await apiClient.put(`/models/${modelId}/runtime-settings`, settings);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
    },
  });
};

/**
 * Update the port range for model servers
 * Invalidates registry cache on success
 * Requires server restart for changes to take effect
 */
export const useUpdatePortRange = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ start, end }: { start: number; end: number }) => {
      const response = await apiClient.put('/models/port-range', { start, end });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelRegistry'] });
    },
  });
};

/**
 * Check the status of external Metal servers
 * Polls every 10 seconds to monitor server health
 * Only relevant when USE_EXTERNAL_SERVERS=true
 */
export const useExternalServerStatus = () => {
  return useQuery<ExternalServerStatusResponse>({
    queryKey: ['externalServerStatus'],
    queryFn: async () => {
      const response = await apiClient.get(endpoints.admin.externalServersStatus);
      return response.data;
    },
    refetchInterval: 10000, // Check every 10 seconds
    staleTime: 5000, // Consider data stale after 5 seconds
    retry: 1, // Only retry once on failure (external servers may not exist)
  });
};
