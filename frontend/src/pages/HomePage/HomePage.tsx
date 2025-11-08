/**
 * HomePage Component - S.Y.N.A.P.S.E. ENGINE Main Interface
 *
 * CORE:INTERFACE - Main query interface with terminal aesthetic.
 * Integrates query input, response display, and system metrics.
 */

import React, { useState } from 'react';
import { Panel, MetricDisplay, StatusIndicator } from '@/components/terminal';
import { useModelStatus } from '@/hooks/useModelStatus';
import { useQuerySubmit } from '@/hooks/useQuery';
import { QueryInput, ResponseDisplay, Timer } from '@/components/query';
import { QueryResponse, QueryMode } from '@/types/query';
import { QuickActions } from '@/components/dashboard';
import { ModeSelector, ModeConfig } from '@/components/modes/ModeSelector';
import styles from './HomePage.module.css';

export const HomePage: React.FC = () => {
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

  const handleQuerySubmit = (query: string, options: any) => {
    // Track the query mode for timer expected time display
    setCurrentQueryMode(queryMode);

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

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          ▓▓▓▓ NEURAL SUBSTRATE ORCHESTRATOR ▓▓▓▓
        </h1>
        <div className={styles.systemStatus}>
          {modelStatus && (
            <>
              <MetricDisplay
                label="VRAM"
                value={`${modelStatus.totalVramUsedGb.toFixed(1)}/${modelStatus.totalVramGb.toFixed(1)}`}
                unit="GB"
              />
              <MetricDisplay
                label="QUERIES"
                value={modelStatus.activeQueries}
                status={modelStatus.activeQueries > 0 ? 'processing' : 'default'}
              />
              <MetricDisplay
                label="CACHE"
                value={(modelStatus.cacheHitRate * 100).toFixed(1)}
                unit="%"
                status={modelStatus.cacheHitRate > 0.7 ? 'active' : 'default'}
              />
            </>
          )}
        </div>
      </div>

      <div className={styles.content}>
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

        <div className={styles.responseSection}>
          {queryMutation.isPending && (
            <div className={styles.loadingIndicator}>
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

      <QuickActions
        onRescan={handleRescan}
        onEnableAll={handleEnableAll}
        onDisableAll={handleDisableAll}
        isLoading={queryMutation.isPending}
      />
    </div>
  );
};
