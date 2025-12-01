import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type {
  InstanceConfig,
  InstanceListResponse,
  InstanceStatusResponse,
  CreateInstanceRequest,
  UpdateInstanceRequest,
  SystemPromptPresetsResponse,
  BulkOperationResponse,
} from '@/types/instances';

/**
 * Fetch the complete list of instances with grouping by model
 * Refetches every 30 seconds to stay in sync with backend
 */
export const useInstanceList = () => {
  return useQuery<InstanceListResponse>({
    queryKey: ['instances'],
    queryFn: async () => {
      const response = await apiClient.get(endpoints.instances.list);
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30s
    staleTime: 10000, // Consider data stale after 10s
  });
};

/**
 * Fetch a specific instance by ID
 * Only fetches if an ID is provided
 */
export const useInstance = (instanceId?: string) => {
  return useQuery<InstanceConfig>({
    queryKey: ['instances', instanceId],
    queryFn: async () => {
      if (!instanceId) throw new Error('Instance ID required');
      const response = await apiClient.get(endpoints.instances.get(instanceId));
      return response.data;
    },
    enabled: !!instanceId, // Only run query if ID is provided
    staleTime: 5000,
  });
};

/**
 * Fetch detailed status of an instance including server info
 */
export const useInstanceStatus = (instanceId?: string) => {
  return useQuery<InstanceStatusResponse>({
    queryKey: ['instances', instanceId, 'status'],
    queryFn: async () => {
      if (!instanceId) throw new Error('Instance ID required');
      const response = await apiClient.get(endpoints.instances.status(instanceId));
      return response.data;
    },
    enabled: !!instanceId,
    refetchInterval: 5000, // Refetch every 5s for real-time updates
    staleTime: 2000,
  });
};

/**
 * Fetch available system prompt presets
 * These are predefined templates for common use cases
 */
export const useSystemPromptPresets = () => {
  return useQuery<SystemPromptPresetsResponse>({
    queryKey: ['instances', 'presets'],
    queryFn: async () => {
      const response = await apiClient.get(endpoints.instances.presets);
      return response.data;
    },
    staleTime: 60000, // Presets rarely change
  });
};

/**
 * Create a new instance of a model
 * Invalidates instance cache on success
 */
export const useCreateInstance = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: CreateInstanceRequest) => {
      const response = await apiClient.post(endpoints.instances.create, request);
      return response.data as InstanceConfig;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
    },
  });
};

/**
 * Update an existing instance's configuration
 * Only fields provided in the request will be updated
 * Invalidates instance cache on success
 */
export const useUpdateInstance = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      instanceId,
      request,
    }: {
      instanceId: string;
      request: UpdateInstanceRequest;
    }) => {
      const response = await apiClient.put(
        endpoints.instances.update(instanceId),
        request
      );
      return response.data as InstanceConfig;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
      queryClient.invalidateQueries({
        queryKey: ['instances', variables.instanceId],
      });
    },
  });
};

/**
 * Delete an instance
 * Instance must be stopped before deletion
 * Invalidates instance cache on success
 */
export const useDeleteInstance = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (instanceId: string) => {
      const response = await apiClient.delete(endpoints.instances.delete(instanceId));
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
    },
  });
};

/**
 * Start a specific instance's server
 * Invalidates instance cache on success
 */
export const useStartInstance = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (instanceId: string) => {
      const response = await apiClient.post(endpoints.instances.start(instanceId));
      return response.data as InstanceConfig;
    },
    onSuccess: (_data, instanceId) => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
      queryClient.invalidateQueries({
        queryKey: ['instances', instanceId, 'status'],
      });
    },
  });
};

/**
 * Stop a specific instance's server
 * Invalidates instance cache on success
 */
export const useStopInstance = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (instanceId: string) => {
      const response = await apiClient.post(endpoints.instances.stop(instanceId));
      return response.data as InstanceConfig;
    },
    onSuccess: (_data, instanceId) => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
      queryClient.invalidateQueries({
        queryKey: ['instances', instanceId, 'status'],
      });
    },
  });
};

/**
 * Start all stopped instances
 * Invalidates instance cache on success
 */
export const useStartAllInstances = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(endpoints.instances.startAll);
      return response.data as BulkOperationResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
    },
  });
};

/**
 * Stop all running instances
 * Invalidates instance cache on success
 */
export const useStopAllInstances = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(endpoints.instances.stopAll);
      return response.data as BulkOperationResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instances'] });
    },
  });
};
