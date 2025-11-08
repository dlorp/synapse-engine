import React, { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Panel } from '@/components/terminal';
import { StatusIndicator } from '@/components/terminal';
import { ModelTable } from '@/components/models/ModelTable';
import { ModelSettings } from '@/components/models/ModelSettings';
import { LogViewer } from '@/components/logs/LogViewer';
import {
  useModelRegistry,
  useRescanModels,
  useServerStatus,
  useRuntimeSettings,
  useUpdateModelPort,
  useUpdateModelRuntimeSettings,
  useExternalServerStatus,
} from '@/hooks/useModelManagement';
import type { RuntimeSettingsUpdateRequest } from '@/types/models';
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
  const queryClient = useQueryClient();
  const { data: registry, isLoading, error, refetch } = useModelRegistry();
  const { data: serverStatus } = useServerStatus();
  const { data: runtimeSettings } = useRuntimeSettings();
  const { data: externalServerStatus } = useExternalServerStatus();
  const rescanModels = useRescanModels();
  const updatePortMutation = useUpdateModelPort();
  const updateSettingsMutation = useUpdateModelRuntimeSettings();

  const [isRescanning, setIsRescanning] = useState(false);
  const [isStartingAll, setIsStartingAll] = useState(false);
  const [isStoppingAll, setIsStoppingAll] = useState(false);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [operationSuccess, setOperationSuccess] = useState<string | null>(null);
  const [expandedSettings, setExpandedSettings] = useState<Record<string, boolean>>({});

  /**
   * Trigger a re-scan of the HUB directory for new models
   */
  const handleRescan = async () => {
    setIsRescanning(true);
    setOperationError(null);
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

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>PRAXIS MODEL REGISTRY</h1>
        </div>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <div className={styles.loadingText}>SCANNING MODEL REGISTRY...</div>
        </div>
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
        <Panel title="SYSTEM ERROR" variant="error">
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
        </Panel>
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
        <Panel title="NO REGISTRY FOUND" variant="warning">
          <div className={styles.emptyContainer}>
            <div className={styles.emptyText}>
              NO REGISTRY FOUND. RUN DISCOVERY FIRST.
            </div>
            <button className={styles.scanButton} onClick={handleRescan}>
              RUN DISCOVERY SCAN
            </button>
          </div>
        </Panel>
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
      {/* Header with Title and Control Buttons */}
      <div className={styles.header}>
        <h1 className={styles.title}>PRAXIS MODEL REGISTRY</h1>
        <div className={styles.actions}>
          <button
            className={`${styles.rescanButton} ${isRescanning ? styles.rescanning : ''}`}
            onClick={handleRescan}
            disabled={isRescanning}
            aria-label="Re-scan HUB directory for models"
          >
            {isRescanning ? (
              <>
                <span className={styles.scanIcon}></span>
                SCANNING...
              </>
            ) : (
              <>
                <span className={styles.scanIcon}>⟳</span>
                RE-SCAN HUB
              </>
            )}
          </button>

          <button
            className={styles.startAllButton}
            onClick={handleStartAll}
            disabled={isStartingAll}
            aria-label="Start all enabled model servers"
          >
            {isStartingAll ? 'STARTING...' : 'START ALL ENABLED'}
          </button>

          <button
            className={styles.stopAllButton}
            onClick={handleStopAll}
            disabled={isStoppingAll}
            aria-label="Stop all running model servers"
          >
            {isStoppingAll ? 'STOPPING...' : 'STOP ALL SERVERS'}
          </button>
        </div>
      </div>

      {/* External Metal Servers Status Banner */}
      {externalServerStatus && externalServerStatus.useExternalServers && (
        <Panel
          title="EXTERNAL METAL SERVERS"
          variant={externalServerStatus.areReachable ? 'accent' : 'error'}
        >
          <div className={styles.externalServerStatus}>
            <StatusIndicator
              status={externalServerStatus.areReachable ? 'active' : 'offline'}
              label={externalServerStatus.message}
              pulse={!externalServerStatus.areReachable}
            />
            {externalServerStatus.servers.length > 0 && (
              <div className={styles.serverList}>
                {externalServerStatus.servers.map((server) => (
                  <div key={server.port} className={styles.serverItem}>
                    <span className={styles.serverPort}>Port {server.port}:</span>
                    <span className={
                      server.status === 'online'
                        ? styles.serverOnline
                        : styles.serverOffline
                    }>
                      {server.status.toUpperCase()}
                    </span>
                    {server.responseTimeMs && (
                      <span className={styles.responseTime}>
                        ({server.responseTimeMs}ms)
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </Panel>
      )}

      {/* Operation Success Display */}
      {operationSuccess && (
        <Panel title="OPERATION SUCCESS" variant="accent">
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
        </Panel>
      )}

      {/* Operation Error Display */}
      {operationError && (
        <Panel title="OPERATION ERROR" variant="error">
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
        </Panel>
      )}

      {/* System Status Panel */}
      <Panel title="SYSTEM STATUS" variant="accent">
        <div className={styles.statusGrid}>
          <div className={styles.statusItem}>
            <div className={styles.statusLabel}>MODELS DISCOVERED</div>
            <div className={styles.statusValue}>{modelCount}</div>
          </div>

          <div className={styles.statusItem}>
            <div className={styles.statusLabel}>MODELS ENABLED</div>
            <div className={styles.statusValue}>{enabledCount}</div>
          </div>

          <div className={styles.statusItem}>
            <div className={styles.statusLabel}>SERVERS RUNNING</div>
            <div className={styles.statusValue}>{runningServers}</div>
          </div>

          <div className={styles.statusItem}>
            <div className={styles.statusLabel}>SERVERS READY</div>
            <div
              className={`${styles.statusValue} ${
                readyServers === runningServers && runningServers > 0
                  ? styles.statusGood
                  : styles.statusWarning
              }`}
            >
              {readyServers}/{runningServers}
            </div>
          </div>
        </div>

        <div className={styles.tierGrid}>
          <div className={styles.tierItem}>
            <div className={styles.tierLabel}>FAST TIER</div>
            <div className={styles.tierValue}>{tierCounts.fast || 0}</div>
          </div>

          <div className={styles.tierItem}>
            <div className={styles.tierLabel}>BALANCED TIER</div>
            <div className={styles.tierValue}>{tierCounts.balanced || 0}</div>
          </div>

          <div className={styles.tierItem}>
            <div className={styles.tierLabel}>POWERFUL TIER</div>
            <div className={styles.tierValue}>{tierCounts.powerful || 0}</div>
          </div>
        </div>

        <div className={styles.registryInfo}>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>SCAN PATH:</span>
            <span className={styles.infoValue}>{registry.scanPath}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>LAST SCAN:</span>
            <span className={styles.infoValue}>
              {registry.lastScan ? new Date(registry.lastScan).toLocaleString() : 'Never'}
            </span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>PORT RANGE:</span>
            <span className={styles.infoValue}>
              {registry.portRange?.[0] ?? 'N/A'} - {registry.portRange?.[1] ?? 'N/A'}
            </span>
          </div>
        </div>
      </Panel>

      {/* Discovered Models Table */}
      <Panel title="DISCOVERED MODELS" variant="default" noPadding>
        <ModelTable
          models={registry.models}
          expandedSettings={expandedSettings}
          onToggleSettings={handleToggleSettings}
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
      </Panel>

      {/* Real-time Log Viewer */}
      <LogViewer
        modelIds={Object.keys(registry.models)}
        maxLines={500}
      />
    </div>
  );
};
