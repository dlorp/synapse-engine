/**
 * HomePage Component - S.Y.N.A.P.S.E. ENGINE Main Interface
 *
 * CORE:INTERFACE - Mission Control query interface with terminal aesthetic.
 * Integrates query input, response display, and essential system metrics.
 *
 * UI CONSOLIDATION (PHASE 1 COMPLETE ✅ 2025-11-09):
 * - Simplified System Status Panel (5 essential metrics, zero sparklines) ✅
 * - Removed metricsHistory dependency (trends moved to MetricsPage) ✅
 * - Faster page load time (<2s target) ✅
 * - Integrated Quick Actions into System Status Panel ✅
 *
 * PHASE 1 ENHANCEMENTS (COMPLETE ✅):
 * - Dot Matrix LED Display banner ✅
 * - OrchestratorStatusPanel (real-time routing visualization) ✅
 * - LiveEventFeed (8-event rolling window with WebSocket) ✅
 * - Enhanced CRT effects (bloom, curvature, scanlines) ✅
 * - Terminal spinners for loading states ✅
 * - System Status moved to bottom with Quick Actions footer ✅
 *
 * Backend Integration Complete:
 * - /api/orchestrator/status endpoint providing real metrics
 * - Event bus emitting system events via /ws/events WebSocket
 */

import React, { useState, useMemo, useCallback } from 'react';
import { toast } from 'react-toastify';
import { useRescanModels, useToggleEnabled, useModelRegistry } from '@/hooks/useModelManagement';
import {
  Panel,
  AsciiPanel,
  StatusIndicator,
  CRTMonitor,
  DotMatrixDisplay,
  TerminalSpinner,
  SystemStatusPanelEnhanced,
} from '@/components/terminal';
import { OrchestratorStatusPanel, LiveEventFeed, ProcessingPipelinePanel, ContextWindowPanel, AdvancedMetricsPanel, SystemArchitectureDiagram } from '@/components/dashboard';
import { useSystemEventsContext } from '@/contexts/SystemEventsContext';
import { useModelStatus } from '@/hooks/useModelStatus';
import { useQuerySubmit } from '@/hooks/useQuery';
import { QueryInput, ResponseDisplay, Timer } from '@/components/query';
import { QueryResponse, QueryMode } from '@/types/query';
import { ModeSelector, ModeConfig } from '@/components/modes/ModeSelector';
import styles from './HomePage.module.css';

export const HomePage: React.FC = () => {
  const { ensureConnected } = useSystemEventsContext();
  const [latestResponse, setLatestResponse] = useState<QueryResponse | null>(null);
  const [currentQueryMode, setCurrentQueryMode] = useState<QueryMode>('two-stage');
  const [queryMode, setQueryMode] = useState<QueryMode>('two-stage');
  const [modeConfig, setModeConfig] = useState<ModeConfig>({});
  const [selectedPreset, setSelectedPreset] = useState('SYNAPSE_ANALYST');
  const { data: modelStatus } = useModelStatus();
  const queryMutation = useQuerySubmit();
  
  // Quick action mutations
  const rescanMutation = useRescanModels();
  const toggleEnabledMutation = useToggleEnabled();
  const { data: modelRegistry } = useModelRegistry();

  // Calculate number of available models (active, idle, or processing = ready to use)
  const activeModels = modelStatus?.models.filter(
    (m) => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
  ).length ?? 0;

  // Stable effects array to prevent animation restart on re-renders
  const dotMatrixEffects = useMemo(() => ['pulsate' as const], []);

  const handleQuerySubmit = (query: string, options: any) => {
    // CRITICAL: Clear previous response to prevent showing stale data
    setLatestResponse(null);

    // Debug logging for response investigation
    console.log('[HomePage] Submitting query:', query.substring(0, 100));

    // Track the query mode for timer expected time display
    setCurrentQueryMode(queryMode);

    // Ensure WebSocket is connected to receive query events
    ensureConnected();

    queryMutation.mutate(
      {
        query,
        mode: queryMode,
        useContext: options.useContext,
        useWebSearch: options.useWebSearch,
        maxTokens: options.maxTokens,
        temperature: options.temperature,
        councilAdversarial: modeConfig.adversarial || false,
        benchmarkSerial: modeConfig.serial || false,
        // Multi-chat dialogue configuration
        councilMaxTurns: modeConfig.maxTurns,
        councilDynamicTermination: modeConfig.dynamicTermination,
        councilPersonaProfile: modeConfig.personaProfile,
        councilPersonas: modeConfig.personas,
        // Moderator configuration
        councilModerator: modeConfig.councilModerator || false,
        councilModeratorActive: modeConfig.councilModeratorActive || false,
        councilModeratorModel: modeConfig.councilModeratorModel,
        councilProModel: modeConfig.councilProModel,
        councilConModel: modeConfig.councilConModel,
      },
      {
        onSuccess: (data) => {
          // Debug logging for response investigation
          console.log('[HomePage] Response received for query:', data.query?.substring(0, 50));
          console.log('[HomePage] Response preview:', data.response?.substring(0, 100));
          setLatestResponse(data);
        },
        onError: (error: any) => {
          console.error('[HomePage] Query failed:', error);
          toast.error(`✗ Query failed: ${error?.message || 'Unknown error'}`, {
            position: 'bottom-right',
            autoClose: 5000,
          });
        },
      }
    );
  };

  const handleModeChange = (mode: QueryMode, config?: ModeConfig) => {
    setQueryMode(mode);
    if (config) {
      setModeConfig(config);
    }
  };

  // Quick action handlers
  const handleRescan = useCallback(async () => {
    toast.info('↻ Rescanning models...', { position: 'bottom-right', autoClose: 2000 });
    try {
      await rescanMutation.mutateAsync();
      toast.success('✓ Model rescan complete', { position: 'bottom-right', autoClose: 3000 });
    } catch (error: any) {
      toast.error(`✗ Rescan failed: ${error?.message || 'Unknown error'}`, {
        position: 'bottom-right',
        autoClose: 5000,
      });
    }
  }, [rescanMutation]);

  const handleEnableAll = useCallback(async () => {
    if (!modelRegistry?.models) {
      toast.warning('⚠ No models in registry', { position: 'bottom-right', autoClose: 3000 });
      return;
    }
    
    const disabledModels = Object.entries(modelRegistry.models)
      .filter(([_, model]) => !model.enabled)
      .map(([id]) => id);
    
    if (disabledModels.length === 0) {
      toast.info('ℹ All models already enabled', { position: 'bottom-right', autoClose: 2000 });
      return;
    }
    
    toast.info(`⚡ Enabling ${disabledModels.length} models...`, { position: 'bottom-right', autoClose: 2000 });
    try {
      await Promise.all(
        disabledModels.map(modelId => toggleEnabledMutation.mutateAsync({ modelId, enabled: true }))
      );
      toast.success(`✓ Enabled ${disabledModels.length} models`, { position: 'bottom-right', autoClose: 3000 });
    } catch (error: any) {
      toast.error(`✗ Failed to enable some models: ${error?.message || 'Unknown error'}`, {
        position: 'bottom-right',
        autoClose: 5000,
      });
    }
  }, [modelRegistry, toggleEnabledMutation]);

  const handleDisableAll = useCallback(async () => {
    if (!modelRegistry?.models) {
      toast.warning('⚠ No models in registry', { position: 'bottom-right', autoClose: 3000 });
      return;
    }
    
    const enabledModels = Object.entries(modelRegistry.models)
      .filter(([_, model]) => model.enabled)
      .map(([id]) => id);
    
    if (enabledModels.length === 0) {
      toast.info('ℹ All models already disabled', { position: 'bottom-right', autoClose: 2000 });
      return;
    }
    
    toast.warning(`⏸ Disabling ${enabledModels.length} models...`, { position: 'bottom-right', autoClose: 2000 });
    try {
      await Promise.all(
        enabledModels.map(modelId => toggleEnabledMutation.mutateAsync({ modelId, enabled: false }))
      );
      toast.success(`✓ Disabled ${enabledModels.length} models`, { position: 'bottom-right', autoClose: 3000 });
    } catch (error: any) {
      toast.error(`✗ Failed to disable some models: ${error?.message || 'Unknown error'}`, {
        position: 'bottom-right',
        autoClose: 5000,
      });
    }
  }, [modelRegistry, toggleEnabledMutation]);

  // Memoize reactive object to prevent animation restarts on re-renders
  const dotMatrixReactive = useMemo(
    () => ({
      enabled: true,
      isProcessing: queryMutation.isPending,
      hasError: queryMutation.isError,
    }),
    [queryMutation.isPending, queryMutation.isError]
  );

  return (
    <CRTMonitor bloomIntensity={0.3} scanlinesEnabled curvatureEnabled>
      <div className={styles.page}>
        {/* Dot Matrix LED Banner */}
        <div className={styles.bannerContainer}>
          <DotMatrixDisplay
            text="SYNAPSE ENGINE"
            revealSpeed={150}
            loop={false}
            height={60}
            pattern="wave"
            effects={dotMatrixEffects}
            reactive={dotMatrixReactive}
          />
        </div>

        {/* Query Interface - Primary Interaction Point */}
        <div className={styles.content}>
          <AsciiPanel title="NEURAL SUBSTRATE ORCHESTRATOR INTERFACE">
            <div className={styles.inputSection}>
              <ModeSelector
                currentMode={queryMode}
                onModeChange={handleModeChange}
                queryPreset={selectedPreset}
              />
              <QueryInput
                onSubmit={handleQuerySubmit}
                isLoading={queryMutation.isPending}
                disabled={activeModels === 0}
              />
              {activeModels === 0 && (
                <div className={styles.warningMessage}>
                  <StatusIndicator status="error" label="NO MODELS ACTIVE" showDot />
                  <span>Waiting for models to come online...</span>
                </div>
              )}
            </div>
          </AsciiPanel>
        </div>

        {/* Response Display Section */}
        <div className={styles.content}>
          <div className={styles.responseSection}>
          {queryMutation.isPending && (
            <div className={styles.loadingIndicator}>
              <TerminalSpinner style="arc" size={24} />
              <Timer mode={currentQueryMode} />
            </div>
          )}

          {queryMutation.isError && (
            <Panel title="ERROR" variant="error">
              <div className={styles.errorMessage}>
                {(queryMutation.error as any)?.message || 'Query failed. Please try again.'}
              </div>
            </Panel>
          )}

          {latestResponse && <ResponseDisplay response={latestResponse} />}
          </div>
        </div>

        {/* Orchestrator Status & Live Events - 2 Column Grid */}
        <div className={styles.dashboardGrid}>
          <OrchestratorStatusPanel />
          <LiveEventFeed maxEvents={8} />
        </div>

        {/* Processing Pipeline Visualization */}
        <div className={styles.content}>
          <ProcessingPipelinePanel />
        </div>

        {/* Context Window Allocation Viewer */}
        <div className={styles.content}>
          <ContextWindowPanel />
        </div>

        {/* Advanced Metrics Visualization */}
        <div className={styles.content}>
          <AdvancedMetricsPanel />
        </div>

        {/* System Architecture Diagram */}
        <div className={styles.content}>
          <SystemArchitectureDiagram />
        </div>

        {/* System Status Panel - MOVED TO BOTTOM with integrated Quick Actions */}
        {modelStatus ? (
          <div className={styles.statusPanelContainer}>
            <SystemStatusPanelEnhanced
              modelStatus={modelStatus}
              title="SYSTEM STATUS"
              onRescan={handleRescan}
              onEnableAll={handleEnableAll}
              onDisableAll={handleDisableAll}
              isLoading={queryMutation.isPending}
            />
          </div>
        ) : (
          <div className={styles.statusPanelContainer}>
            <Panel title="SYSTEM STATUS">
              <div style={{ padding: '40px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                <TerminalSpinner style="arc" size={24} />
                <div style={{ color: 'var(--phosphor-green, #ff9500)', fontFamily: 'var(--font-mono)' }}>
                  Loading system status...
                </div>
              </div>
            </Panel>
          </div>
        )}
      </div>
    </CRTMonitor>
  );
};
