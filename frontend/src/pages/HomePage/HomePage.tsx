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

import React, { useState, useMemo } from 'react';
import {
  Panel,
  StatusIndicator,
  CRTMonitor,
  DotMatrixDisplay,
  TerminalSpinner,
  SystemStatusPanelEnhanced,
} from '@/components/terminal';
import { OrchestratorStatusPanel, LiveEventFeed } from '@/components/dashboard';
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
  const { data: modelStatus } = useModelStatus();
  const queryMutation = useQuerySubmit();

  // Calculate number of available models (active, idle, or processing = ready to use)
  const activeModels = modelStatus?.models.filter(
    (m) => m.state === 'active' || m.state === 'idle' || m.state === 'processing'
  ).length ?? 0;

  // Stable effects array to prevent animation restart on re-renders
  const dotMatrixEffects = useMemo(() => ['pulsate' as const], []);

  const handleQuerySubmit = (query: string, options: any) => {
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
          setLatestResponse(data);
        },
        onError: (error: any) => {
          console.error('Query failed:', error);
          // TODO: Implement toast notification system
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
  const handleRescan = async () => {
    // TODO: Implement API call to /api/admin/discover or /api/models/rescan
    console.log('Rescanning models...');
  };

  const handleEnableAll = async () => {
    // TODO: Implement API call to enable all models
    console.log('Enabling all models...');
  };

  const handleDisableAll = async () => {
    // TODO: Implement API call to disable all models
    console.log('Disabling all models...');
  };

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
            width={600}
            height={60}
            pattern="wave"
            effects={dotMatrixEffects}
            reactive={dotMatrixReactive}
          />
        </div>

        {/* Query Interface - Primary Interaction Point */}
        <div className={styles.content}>
          <Panel title="NEURAL SUBSTRATE ORCHESTRATOR INTERFACE">
            <div className={styles.inputSection}>
              <ModeSelector
                currentMode={queryMode}
                onModeChange={handleModeChange}
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
          </Panel>
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

          <ResponseDisplay response={latestResponse} />
          </div>
        </div>

        {/* Orchestrator Status & Live Events - 2 Column Grid */}
        <div className={styles.dashboardGrid}>
          <OrchestratorStatusPanel />
          <LiveEventFeed maxEvents={8} />
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
