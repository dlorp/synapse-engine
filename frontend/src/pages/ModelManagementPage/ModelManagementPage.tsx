import React, { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AsciiPanel } from '@/components/terminal';
import { ModelCardGrid } from '@/components/models/ModelCardGrid';
import { ModelSettings } from '@/components/models/ModelSettings';
import { useModelMetrics } from '@/hooks/useModelMetrics';
import { LogViewer } from '@/components/logs/LogViewer';
import { useSystemEventsContext } from '@/contexts/SystemEventsContext';
import {
  useModelRegistry,
  useRescanModels,
  useServerStatus,
  useRuntimeSettings,
  useUpdateModelPort,
  useUpdateModelRuntimeSettings,
  useExternalServerStatus,
} from '@/hooks/useModelManagement';
import {
  useInstanceList,
  useCreateInstance,
  useDeleteInstance,
  useStartInstance,
  useStopInstance,
} from '@/hooks/useInstances';
import type { RuntimeSettingsUpdateRequest } from '@/types/models';
import type { InstanceConfig } from '@/types/instances';
import { EditInstanceModal } from '@/components/instances/EditInstanceModal';
import styles from './ModelManagementPage.module.css';

/**
 * ModelManagementPage - PRAXIS Model Registry Management Interface
 *
 * CORE:INTERFACE - Primary interface for managing S.Y.N.A.P.S.E. ENGINE's model discovery system
 *
 * Features:
 * - View all discovered models from HUB directory
 * - Configure tier assignments (fast/balanced/powerful)
 * - Toggle thinking capability per model
 * - Enable/disable models for server startup
 * - Re-scan HUB for new models
 * - Real-time server status monitoring
 *
 * Terminal aesthetic with dense information display and real-time updates
 */
export const ModelManagementPage: React.FC = () => {
  // ALL HOOKS MUST BE CALLED FIRST (Rules of Hooks - unconditional)
  const { ensureConnected } = useSystemEventsContext();
  const queryClient = useQueryClient();
  const { data: registry, isLoading, error, refetch } = useModelRegistry();
  const { data: serverStatus } = useServerStatus();
  const { data: runtimeSettings } = useRuntimeSettings();
  const { data: externalServerStatus } = useExternalServerStatus();
  const { data: modelMetrics } = useModelMetrics(); // Phase 3: Per-model metrics for sparklines
  const rescanModels = useRescanModels();
  const updatePortMutation = useUpdateModelPort();
  const updateSettingsMutation = useUpdateModelRuntimeSettings();

  // Instance management
  const { data: instanceList } = useInstanceList();
  const createInstanceMutation = useCreateInstance();
  const deleteInstanceMutation = useDeleteInstance();
  const startInstanceMutation = useStartInstance();
  const stopInstanceMutation = useStopInstance();

  const [isRescanning, setIsRescanning] = useState(false);
  const [isStartingAll, setIsStartingAll] = useState(false);
  const [isStoppingAll, setIsStoppingAll] = useState(false);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [operationSuccess, setOperationSuccess] = useState<string | null>(null);
  const [expandedSettings, setExpandedSettings] = useState<Record<string, boolean>>({});
  const [editingInstance, setEditingInstance] = useState<InstanceConfig | null>(null);

  // Phase 3: Calculate running model IDs set for ModelCardGrid
  // IMPORTANT: This useMemo MUST be called before early returns to maintain consistent hook order
  const runningModelIds = React.useMemo(() => {
    const ids = new Set<string>();
    serverStatus?.servers?.forEach((server) => {
      if (server.isRunning) {
        ids.add(server.modelId);
      }
    });
    return ids;
  }, [serverStatus]);

  // Group instances by model ID
  const instancesByModel = React.useMemo(() => {
    const map: Record<string, InstanceConfig[]> = {};

    instanceList?.instances.forEach((instance) => {
      const existing = map[instance.modelId];
      if (!existing) {
        map[instance.modelId] = [instance];
      } else {
        existing.push(instance);
      }
    });

    return map;
  }, [instanceList]);

  /**
   * Trigger a re-scan of the HUB directory for new models
   */
  const handleRescan = async () => {
    setIsRescanning(true);
    setOperationError(null);
    // Ensure WebSocket is connected to receive discovery events
    ensureConnected();
    try {
      await rescanModels.mutateAsync();
      await refetch();
    } catch (err) {
      console.error('Rescan failed:', err);
      setOperationError(err instanceof Error ? err.message : 'Rescan failed');
    } finally {
      setIsRescanning(false);
    }
  };

  /**
   * Start all enabled model servers
   */
  const handleStartAll = async () => {
    setIsStartingAll(true);
    setOperationError(null);
    setOperationSuccess(null);
    // Ensure WebSocket is connected to receive model state events
    ensureConnected();
    try {
      // Show initial progress message
      setOperationSuccess('🚀 Starting Metal-accelerated servers... (10-15 seconds)');

      const response = await fetch('/api/models/servers/start-all', {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || response.statusText);
      }

      const result = await response.json();

      // Show appropriate message based on results
      if (result.started === 0) {
        // NO servers started - this is an ERROR
        if (result.total === 0) {
          setOperationError('No enabled servers to start. Enable models in the table below.');
        } else {
          setOperationError(
            `Failed to start all ${result.total} server${result.total !== 1 ? 's' : ''}. Check logs for details.`
          );
        }
      } else if (result.started < result.total) {
        // PARTIAL success - show warning
        const failed = result.total - result.started;
        setOperationSuccess(
          `Started ${result.started}/${result.total} servers (${failed} failed to start)`
        );
      } else {
        // FULL success
        setOperationSuccess(
          `✅ Successfully started ${result.started}/${result.total} Metal-accelerated server${result.total !== 1 ? 's' : ''}`
        );
      }

      // Refresh both registry AND server status
      await Promise.all([
        refetch(),
        queryClient.invalidateQueries({ queryKey: ['serverStatus'] })
      ]);
    } catch (err) {
      console.error('Failed to start servers:', err);
      setOperationError(err instanceof Error ? err.message : 'Failed to start servers');
    } finally {
      setIsStartingAll(false);
    }
  };

  /**
   * Stop all running model servers
   */
  const handleStopAll = async () => {
    setIsStoppingAll(true);
    setOperationError(null);
    // Ensure WebSocket is connected to receive model state events
    ensureConnected();
    try {
      const response = await fetch('/api/models/servers/stop-all', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to stop servers: ${response.statusText}`);
      }

      const result = await response.json();
      console.log(`Stopped ${result.stopped} servers`);

      // Refresh registry
      await refetch();
    } catch (err) {
      console.error('Failed to stop servers:', err);
      setOperationError(err instanceof Error ? err.message : 'Failed to stop servers');
    } finally {
      setIsStoppingAll(false);
    }
  };

  /**
   * Phase 2: Toggle settings panel expansion
   */
  const handleToggleSettings = useCallback((modelId: string) => {
    setExpandedSettings((prev) => ({
      ...prev,
      [modelId]: !prev[modelId],
    }));
  }, []);

  /**
   * Phase 2: Handle port change
   */
  const handlePortChange = useCallback(
    async (modelId: string, port: number) => {
      try {
        await updatePortMutation.mutateAsync({ modelId, port });
        setOperationSuccess(`Port updated to ${port} for model ${modelId}`);
        setTimeout(() => setOperationSuccess(null), 3000);
      } catch (err) {
        console.error('Failed to update port:', err);
        setOperationError(err instanceof Error ? err.message : 'Failed to update port');
      }
    },
    [updatePortMutation]
  );

  /**
   * Phase 2: Handle runtime settings save
   */
  const handleSettingsSave = useCallback(
    async (modelId: string, settings: RuntimeSettingsUpdateRequest) => {
      try {
        await updateSettingsMutation.mutateAsync({ modelId, settings });
        setOperationSuccess(`Settings updated for model ${modelId}`);
        setTimeout(() => setOperationSuccess(null), 3000);
      } catch (err) {
        console.error('Failed to update settings:', err);
        setOperationError(err instanceof Error ? err.message : 'Failed to update settings');
      }
    },
    [updateSettingsMutation]
  );

  // Instance handlers
  const handleCreateInstance = useCallback(
    async (_modelId: string, config: import('@/types/instances').CreateInstanceRequest) => {
      try {
        await createInstanceMutation.mutateAsync(config);
        setOperationSuccess('Instance created successfully');
        setTimeout(() => setOperationSuccess(null), 3000);
      } catch (err) {
        setOperationError(err instanceof Error ? err.message : 'Failed to create instance');
      }
    },
    [createInstanceMutation]
  );

  const handleDeleteInstance = useCallback(
    async (instanceId: string) => {
      try {
        await deleteInstanceMutation.mutateAsync(instanceId);
        setOperationSuccess('Instance deleted successfully');
        setTimeout(() => setOperationSuccess(null), 3000);
      } catch (err) {
        setOperationError(err instanceof Error ? err.message : 'Failed to delete instance');
      }
    },
    [deleteInstanceMutation]
  );

  const handleStartInstance = useCallback(
    async (instanceId: string) => {
      try {
        await startInstanceMutation.mutateAsync(instanceId);
        setOperationSuccess('Instance started successfully');
        setTimeout(() => setOperationSuccess(null), 3000);
      } catch (err) {
        setOperationError(err instanceof Error ? err.message : 'Failed to start instance');
      }
    },
    [startInstanceMutation]
  );

  const handleStopInstance = useCallback(
    async (instanceId: string) => {
      try {
        await stopInstanceMutation.mutateAsync(instanceId);
        setOperationSuccess('Instance stopped successfully');
        setTimeout(() => setOperationSuccess(null), 3000);
      } catch (err) {
        setOperationError(err instanceof Error ? err.message : 'Failed to stop instance');
      }
    },
    [stopInstanceMutation]
  );

  const handleEditInstance = useCallback(
    (instanceId: string) => {
      // Find the instance from the list and open edit modal
      const instance = instanceList?.instances.find(i => i.instanceId === instanceId);
      if (instance) {
        setEditingInstance(instance);
      } else {
        setOperationError('Instance not found');
      }
    },
    [instanceList]
  );

  /**
   * Phase 3: Start individual model
   */
  const handleStartModel = useCallback(
    async (modelId: string) => {
      setOperationError(null);
      setOperationSuccess(null);
      ensureConnected();
      try {
        const response = await fetch(`/api/models/servers/start/${modelId}`, {
          method: 'POST',
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(errorData.detail || response.statusText);
        }

        setOperationSuccess(`Started model ${modelId}`);
        setTimeout(() => setOperationSuccess(null), 3000);

        await Promise.all([
          refetch(),
          queryClient.invalidateQueries({ queryKey: ['serverStatus'] }),
        ]);
      } catch (err) {
        console.error('Failed to start model:', err);
        setOperationError(err instanceof Error ? err.message : 'Failed to start model');
      }
    },
    [refetch, queryClient, ensureConnected]
  );

  /**
   * Phase 3: Stop individual model
   */
  const handleStopModel = useCallback(
    async (modelId: string) => {
      setOperationError(null);
      setOperationSuccess(null);
      ensureConnected();
      try {
        const response = await fetch(`/api/models/servers/stop/${modelId}`, {
          method: 'POST',
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(errorData.detail || response.statusText);
        }

        setOperationSuccess(`Stopped model ${modelId}`);
        setTimeout(() => setOperationSuccess(null), 3000);

        await Promise.all([
          refetch(),
          queryClient.invalidateQueries({ queryKey: ['serverStatus'] }),
        ]);
      } catch (err) {
        console.error('Failed to stop model:', err);
        setOperationError(err instanceof Error ? err.message : 'Failed to stop model');
      }
    },
    [refetch, queryClient, ensureConnected]
  );

  /**
   * Phase 3: Restart individual model
   */
  const handleRestartModel = useCallback(
    async (modelId: string) => {
      try {
        await handleStopModel(modelId);
        setTimeout(() => handleStartModel(modelId), 1000); // Wait 1s between stop and start
      } catch (err) {
        console.error('Failed to restart model:', err);
        setOperationError(err instanceof Error ? err.message : 'Failed to restart model');
      }
    },
    [handleStartModel, handleStopModel]
  );

  /**
   * Toggle model enabled status (triggers auto start/stop)
   */
  const handleToggleEnable = useCallback(
    async (modelId: string, enabled: boolean) => {
      setOperationError(null);
      setOperationSuccess(null);
      ensureConnected();
      try {
        const response = await fetch(`/api/models/${modelId}/enabled`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ enabled }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail?.message || 'Failed to toggle model');
        }

        const result = await response.json();
        console.log(`Model ${modelId} ${enabled ? 'enabled' : 'disabled'}. Registry: ${result.serverStatus}`);

        const statusMsg = enabled ? 'enabled (use START ALL to activate)' : 'disabled';
        setOperationSuccess(`✓ Model ${statusMsg}`);
        setTimeout(() => setOperationSuccess(null), 3000);

        // Refresh registry to show updated enabled status
        await refetch();
      } catch (err) {
        console.error('Failed to toggle model:', err);
        setOperationError(err instanceof Error ? err.message : 'Failed to toggle model');
        setTimeout(() => setOperationError(null), 5000);
      }
    },
    [refetch, queryClient, ensureConnected]
  );

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>PRAXIS MODEL REGISTRY</h1>
        </div>
        <AsciiPanel title="MODEL DISCOVERY" variant="accent">
          <div className={styles.scanningRegistry}>
            <div className={styles.scanningHeader}>SCANNING MODEL REGISTRY</div>

            <div className={styles.fileSystemTree}>
              <div className={styles.treeLine}>┌─ HUGGINGFACE CACHE</div>
              <div className={styles.treeLine}>│</div>
              <div className={styles.treeLine}>├─── models/</div>
              <div className={styles.treeBranch}>
                │&nbsp;&nbsp;&nbsp;&nbsp;├─ TheBloke/ <span className={styles.breathingDots}>░░░</span>
              </div>
              <div className={styles.treeBranch}>
                │&nbsp;&nbsp;&nbsp;&nbsp;├─ Meta-Llama/ <span className={styles.breathingDots}>░░░</span>
              </div>
              <div className={styles.treeBranch}>
                │&nbsp;&nbsp;&nbsp;&nbsp;└─ Qwen/ <span className={styles.breathingDots}>░░░</span>
              </div>
              <div className={styles.treeLine}>│</div>
              <div className={styles.treeLine}>└─── [Scanning for GGUF files<span className={styles.animatedEllipsis}>...</span>]</div>
            </div>

            <div className={styles.scanningProgress}>
              <div className={styles.progressWave}>▁▂▃▄▅▆▇█▇▆▅▄▃▂▁</div>
              <div className={styles.progressLabel}>PROGRESS</div>
              <div className={styles.progressWave}>▁▂▃▄▅▆▇█▇▆▅▄▃▂▁</div>
            </div>
          </div>
        </AsciiPanel>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>PRAXIS MODEL REGISTRY</h1>
        </div>
        <AsciiPanel title="SYSTEM ERROR" variant="error">
          <div className={styles.errorContainer}>
            <div className={styles.errorIcon}>⚠</div>
            <div className={styles.errorText}>
              FAILED TO LOAD MODEL REGISTRY
            </div>
            <div className={styles.errorDetail}>
              {error instanceof Error
                ? (error as any)?.response?.data?.detail?.message || error.message
                : 'Request failed with status code 404'}
            </div>
            <button className={styles.retryButton} onClick={() => refetch()}>
              RETRY
            </button>
          </div>
        </AsciiPanel>
      </div>
    );
  }

  // No registry found
  if (!registry) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>PRAXIS MODEL REGISTRY</h1>
        </div>
        <AsciiPanel title="MODEL REGISTRY" variant="warning">
          <div className={styles.emptyRegistry}>
            <div className={styles.emptyHeader}>MODEL REGISTRY UNINITIALIZED</div>

            <div className={styles.emptyFileSystem}>
              <div className={styles.fsBox}>
                <div className={styles.fsPath}>/models/</div>
                <div className={styles.fsTree}>│</div>
                <div className={styles.fsEmpty}>
                  └─ <span className={styles.emptyBrackets}>[</span> empty <span className={styles.emptyBrackets}>]</span>
                </div>
                <div className={styles.fsMessage}>
                  No GGUF models<br />discovered yet
                </div>
              </div>
            </div>

            <div className={styles.emptyHint}>
              ◆ Initialize registry to begin discovery
            </div>

            <button className={styles.scanButton} onClick={handleRescan}>
              ▶ RUN DISCOVERY SCAN
            </button>
          </div>
        </AsciiPanel>
      </div>
    );
  }

  // Calculate statistics
  const modelCount = Object.keys(registry.models).length;
  const enabledCount = Object.values(registry.models).filter((m) => m.enabled).length;
  const runningServers = serverStatus?.totalServers || 0;
  const readyServers = serverStatus?.readyServers || 0;

  // Count models by tier
  const tierCounts = Object.values(registry.models).reduce(
    (acc, model) => {
      const tier = model.tierOverride || model.assignedTier;
      acc[tier] = (acc[tier] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className={styles.page}>
      {/* Header with Title and Registry Controls - Matches AdminPage format */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>PRAXIS MODEL REGISTRY</h1>
          <div className={styles.subtitle}>Neural substrate model discovery and lifecycle management</div>
        </div>

        <div className={styles.headerControls}>
          <button
            className={`${styles.controlButton} ${isRescanning ? styles.active : ''}`}
            onClick={handleRescan}
            disabled={isRescanning}
            aria-label="Re-scan HUB directory for models"
          >
            <span className={styles.buttonIcon}>{isRescanning ? '◌' : '⟳'}</span>
            <span className={styles.buttonLabel}>{isRescanning ? 'SCANNING' : 'RE-SCAN'}</span>
          </button>

          <button
            className={`${styles.controlButton} ${isStartingAll ? styles.active : ''}`}
            onClick={handleStartAll}
            disabled={isStartingAll}
            aria-label="Start all enabled model servers"
          >
            <span className={styles.buttonIcon}>{isStartingAll ? '◌' : '▶'}</span>
            <span className={styles.buttonLabel}>{isStartingAll ? 'STARTING' : 'START ALL'}</span>
          </button>

          <button
            className={`${styles.controlButton} ${isStoppingAll ? styles.active : ''}`}
            onClick={handleStopAll}
            disabled={isStoppingAll}
            aria-label="Stop all running model servers"
          >
            <span className={styles.buttonIcon}>{isStoppingAll ? '◌' : '⏹'}</span>
            <span className={styles.buttonLabel}>{isStoppingAll ? 'STOPPING' : 'STOP ALL'}</span>
          </button>
        </div>
      </div>

      {/* External Metal Servers Status Banner */}
      {externalServerStatus && externalServerStatus.useExternalServers && (
        <AsciiPanel
          title="EXTERNAL METAL SERVERS"
          variant={externalServerStatus.areReachable ? 'accent' : 'error'}
        >
          <div className={styles.externalServersEnhanced}>
            <div className={styles.connectionDiagram}>
              <div className={styles.connectionHeader}>CONNECTION TOPOLOGY</div>
              <div className={styles.topologyLine}>
                HOST MACHINE ─────→ DOCKER NETWORK
              </div>
            </div>

            <div className={styles.portStatusList}>
              {externalServerStatus.servers.map((server) => (
                <div key={server.port} className={styles.portStatusRow}>
                  <span className={styles.portLabel}>Port {server.port}:</span>
                  <div className={styles.statusBarContainer}>
                    {server.status === 'online' ? (
                      <>
                        <span className={styles.statusIndicator}>ONLINE</span>
                        <span className={styles.breathingBarOnline}>████</span>
                        <span className={styles.responseTime}>
                          ({server.responseTimeMs}ms)
                        </span>
                      </>
                    ) : (
                      <>
                        <span className={styles.statusIndicator}>OFFLINE</span>
                        <span className={styles.breathingBarOffline}>░░░░</span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className={styles.serversSummary}>
              <span className={styles.summaryIcon}>
                {externalServerStatus.areReachable ? '✓' : '✗'}
              </span>
              <span className={styles.summaryText}>
                {externalServerStatus.servers.filter((s) => s.status === 'online').length}/
                {externalServerStatus.servers.length} reachable
              </span>
            </div>
          </div>
        </AsciiPanel>
      )}

      {/* Operation Success Display */}
      {operationSuccess && (
        <AsciiPanel title="OPERATION SUCCESS" variant="accent">
          <div className={styles.operationSuccess}>
            <div className={styles.successIcon}>✓</div>
            <div className={styles.successText}>{operationSuccess}</div>
            <button
              className={styles.dismissButton}
              onClick={() => setOperationSuccess(null)}
              aria-label="Dismiss success message"
            >
              DISMISS
            </button>
          </div>
        </AsciiPanel>
      )}

      {/* Operation Error Display */}
      {operationError && (
        <AsciiPanel title="OPERATION ERROR" variant="error">
          <div className={styles.operationError}>
            <div className={styles.errorIcon}>⚠</div>
            <div className={styles.errorText}>{operationError}</div>
            <button
              className={styles.dismissButton}
              onClick={() => setOperationError(null)}
              aria-label="Dismiss error message"
            >
              DISMISS
            </button>
          </div>
        </AsciiPanel>
      )}

      {/* System Status Panel - Enhanced with ASCII */}
      <AsciiPanel title="SYSTEM STATUS">
        <div className={styles.neuralSubstrateStatus}>
          <div className={styles.statusHeader}>NEURAL SUBSTRATE REGISTRY</div>

          {/* Tier Distribution */}
          <div className={styles.tierDistribution}>
            <div className={styles.distributionHeader}>{`${'─ TIER DISTRIBUTION '}${'─'.repeat(150)}`}</div>

            <div className={styles.tierBar}>
              <span className={styles.tierLabel}>Q2 [FAST]</span>
              <div className={styles.barContainer}>
                <div
                  className={styles.barFilled}
                  style={{ width: `${modelCount > 0 ? ((tierCounts.fast || 0) / modelCount) * 100 : 0}%` }}
                >
                  <span className={styles.barBlocks}>
                    {'█'.repeat(Math.max(0, Math.min(10, Math.ceil(modelCount > 0 ? ((tierCounts.fast || 0) / modelCount) * 10 : 0))))}
                  </span>
                </div>
                <div className={styles.barEmpty}>
                  <span className={styles.emptyBlocks}>
                    {'░'.repeat(Math.max(0, 10 - Math.max(0, Math.min(10, Math.ceil(modelCount > 0 ? ((tierCounts.fast || 0) / modelCount) * 10 : 0)))))}
                  </span>
                </div>
              </div>
              <span className={styles.tierCount}>
                {tierCounts.fast || 0}/{modelCount}
              </span>
            </div>

            <div className={styles.tierBar}>
              <span className={styles.tierLabel}>Q3 [BALANCED]</span>
              <div className={styles.barContainer}>
                <div
                  className={styles.barFilled}
                  style={{
                    width: `${modelCount > 0 ? ((tierCounts.balanced || 0) / modelCount) * 100 : 0}%`,
                  }}
                >
                  <span className={styles.barBlocks}>
                    {'█'.repeat(Math.max(0, Math.min(10, Math.ceil(modelCount > 0 ? ((tierCounts.balanced || 0) / modelCount) * 10 : 0))))}
                  </span>
                </div>
                <div className={styles.barEmpty}>
                  <span className={styles.emptyBlocks}>
                    {'░'.repeat(Math.max(0, 10 - Math.max(0, Math.min(10, Math.ceil(modelCount > 0 ? ((tierCounts.balanced || 0) / modelCount) * 10 : 0)))))}
                  </span>
                </div>
              </div>
              <span className={styles.tierCount}>
                {tierCounts.balanced || 0}/{modelCount}
              </span>
            </div>

            <div className={styles.tierBar}>
              <span className={styles.tierLabel}>Q4 [POWERFUL]</span>
              <div className={styles.barContainer}>
                <div
                  className={styles.barFilled}
                  style={{
                    width: `${modelCount > 0 ? ((tierCounts.powerful || 0) / modelCount) * 100 : 0}%`,
                  }}
                >
                  <span className={styles.barBlocks}>
                    {'█'.repeat(Math.max(0, Math.min(10, Math.ceil(modelCount > 0 ? ((tierCounts.powerful || 0) / modelCount) * 10 : 0))))}
                  </span>
                </div>
                <div className={styles.barEmpty}>
                  <span className={styles.emptyBlocks}>
                    {'░'.repeat(Math.max(0, 10 - Math.max(0, Math.min(10, Math.ceil(modelCount > 0 ? ((tierCounts.powerful || 0) / modelCount) * 10 : 0)))))}
                  </span>
                </div>
              </div>
              <span className={styles.tierCount}>
                {tierCounts.powerful || 0}/{modelCount}
              </span>
            </div>

            <div className={styles.distributionFooter}>
              <span>TOTAL: {modelCount} models</span>
              <span>ENABLED: {enabledCount} models</span>
            </div>
          </div>

          {/* Server Status */}
          <div className={styles.serverStatusBox}>
            <div className={styles.distributionHeader}>{`${'─ SERVER STATUS '}${'─'.repeat(150)}`}</div>

            <div className={styles.serverBar}>
              <span className={styles.serverLabel}>RUNNING:</span>
              <div className={styles.barContainer}>
                <div
                  className={styles.barFilled}
                  style={{
                    width: `${enabledCount > 0 ? (runningServers / enabledCount) * 100 : 0}%`,
                  }}
                >
                  <span className={styles.breathingBarActive}>
                    {'█'.repeat(Math.max(0, Math.min(10, Math.ceil(enabledCount > 0 ? (runningServers / enabledCount) * 10 : 0))))}
                  </span>
                </div>
                <div className={styles.barEmpty}>
                  <span className={styles.emptyBlocks}>
                    {'░'.repeat(Math.max(0, 10 - Math.max(0, Math.min(10, Math.ceil(enabledCount > 0 ? (runningServers / enabledCount) * 10 : 0)))))}
                  </span>
                </div>
              </div>
              <span className={styles.serverCount}>
                {runningServers}/{enabledCount}
              </span>
            </div>

            <div className={styles.serverBar}>
              <span className={styles.serverLabel}>READY:</span>
              <div className={styles.barContainer}>
                <div
                  className={styles.barFilled}
                  style={{
                    width: `${runningServers > 0 ? (readyServers / runningServers) * 100 : 0}%`,
                  }}
                >
                  <span className={styles.breathingBarActive}>
                    {'█'.repeat(Math.max(0, Math.min(10, Math.ceil(runningServers > 0 ? (readyServers / runningServers) * 10 : 0))))}
                  </span>
                </div>
                <div className={styles.barEmpty}>
                  <span className={styles.emptyBlocks}>
                    {'░'.repeat(Math.max(0, 10 - Math.max(0, Math.min(10, Math.ceil(runningServers > 0 ? (readyServers / runningServers) * 10 : 0)))))}
                  </span>
                </div>
              </div>
              <span className={styles.serverCount}>
                {readyServers}/{runningServers}
              </span>
            </div>
          </div>

          {/* Registry Info (compact) */}
          <div className={styles.registryInfoCompact}>
            <div className={styles.infoLine}>
              <span className={styles.infoIcon}>📁</span>
              <span className={styles.infoText}>{registry.scanPath}</span>
            </div>
            <div className={styles.infoLine}>
              <span className={styles.infoIcon}>⏱</span>
              <span className={styles.infoText}>
                {registry.lastScan ? new Date(registry.lastScan).toLocaleString() : 'Never'}
              </span>
            </div>
            <div className={styles.infoLine}>
              <span className={styles.infoIcon}>⚡</span>
              <span className={styles.infoText}>
                Ports {registry.portRange?.[0] ?? 'N/A'} - {registry.portRange?.[1] ?? 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </AsciiPanel>

      {/* Discovered Models Card Grid */}
      <AsciiPanel title="DISCOVERED MODELS">
        {modelCount === 0 ? (
          <div className={styles.emptyModelsGrid}>
            <div className={styles.emptyHeader}>NO GGUF MODELS FOUND</div>
            <div className={styles.emptySubheader}>FILESYSTEM SCAN COMPLETE</div>

            <div className={styles.scanResults}>
              <div className={styles.resultBox}>
                <div className={styles.resultLabel}>Searched:</div>
                <div className={styles.searchedPath}>• TheBloke/ ✓</div>
                <div className={styles.searchedPath}>• Meta-Llama/ ✓</div>
                <div className={styles.searchedPath}>• Qwen/ ✓</div>
                <div className={styles.resultSummary}>GGUF files: 0</div>
              </div>
            </div>

            <div className={styles.emptyBreathingBar}>
              ░░░░░░░░░░░░░░░░░░░░░░░░
            </div>

            <div className={styles.emptyHint}>
              → Download models to HuggingFace cache<br />
              &nbsp;&nbsp;then run discovery scan
            </div>
          </div>
        ) : (
          <ModelCardGrid
            models={registry.models}
            expandedSettings={expandedSettings}
            modelMetrics={modelMetrics}
            runningModels={runningModelIds}
            instancesByModel={instancesByModel}
            onToggleSettings={handleToggleSettings}
            onToggleEnable={handleToggleEnable}
            onStartModel={handleStartModel}
            onStopModel={handleStopModel}
            onRestartModel={handleRestartModel}
            onCreateInstance={handleCreateInstance}
            onEditInstance={handleEditInstance}
            onDeleteInstance={handleDeleteInstance}
            onStartInstance={handleStartInstance}
            onStopInstance={handleStopInstance}
            renderSettingsPanel={(model) => {
              // Check if this model's server is running
              const serverInfo = serverStatus?.servers.find((s) => s.modelId === model.modelId);
              const isServerRunning = serverInfo?.isRunning || false;

              // Provide default values if runtime settings haven't loaded yet
              const defaults = runtimeSettings || {
                nGpuLayers: 99,
                ctxSize: 8192,
                nThreads: 8,
                batchSize: 512,
              };

              return (
                <ModelSettings
                  model={model}
                  allModels={Object.values(registry.models)}
                  portRange={registry.portRange}
                  isServerRunning={isServerRunning}
                  globalDefaults={defaults}
                  onSave={handleSettingsSave}
                  onPortChange={handlePortChange}
                />
              );
            }}
          />
        )}
      </AsciiPanel>

      {/* Real-time Log Viewer */}
      <LogViewer
        modelIds={Object.keys(registry.models)}
        maxLines={500}
      />

      {/* Edit Instance Modal */}
      {editingInstance && (
        <EditInstanceModal
          instance={editingInstance}
          modelDisplayName={registry?.models[editingInstance.modelId]?.filename}
          onClose={() => setEditingInstance(null)}
          onSuccess={() => setEditingInstance(null)}
        />
      )}
    </div>
  );
};
