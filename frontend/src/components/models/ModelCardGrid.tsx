/**
 * ModelCardGrid - Responsive Grid Container for Model Cards
 *
 * Auto-fit CSS Grid layout with 3/2/1 column breakpoints.
 * Replaces table-based ModelTable component with dense card grid.
 *
 * Breakpoints:
 * - Wide (>1400px): 3 columns
 * - Medium (900-1399px): 2 columns
 * - Narrow (<900px): 1 column
 */

import React, { useMemo } from 'react';
import { ModelCard } from './ModelCard';
import type { DiscoveredModel } from '@/types/models';
import type { ModelMetrics } from '@/hooks/useModelMetrics';
import styles from './ModelCardGrid.module.css';

export interface ModelCardGridProps {
  models: Record<string, DiscoveredModel>;
  expandedSettings: Record<string, boolean>;
  modelMetrics?: Record<string, ModelMetrics>;
  runningModels?: Set<string>;
  onToggleSettings: (modelId: string) => void;
  onToggleEnable?: (modelId: string, enabled: boolean) => void;
  onStartModel?: (modelId: string) => void;
  onStopModel?: (modelId: string) => void;
  onRestartModel?: (modelId: string) => void;
  renderSettingsPanel: (model: DiscoveredModel) => React.ReactNode;
}

export const ModelCardGrid: React.FC<ModelCardGridProps> = ({
  models,
  expandedSettings,
  modelMetrics = {},
  runningModels = new Set(),
  onToggleSettings,
  onToggleEnable,
  onStartModel,
  onStopModel,
  onRestartModel,
  renderSettingsPanel
}) => {
  // Convert models object to sorted array
  // Sort by: tier (fast > balanced > powerful), then alphabetically by filename
  const modelArray = useMemo(() => {
    const tierOrder: Record<string, number> = {
      fast: 0,
      balanced: 1,
      powerful: 2
    };

    return Object.values(models).sort((a, b) => {
      // Get effective tier (override takes precedence)
      const aTier = a.tierOverride || a.assignedTier;
      const bTier = b.tierOverride || b.assignedTier;

      // Sort by tier first
      const tierDiff = tierOrder[aTier] - tierOrder[bTier];
      if (tierDiff !== 0) return tierDiff;

      // Then sort alphabetically by filename
      return a.filename.localeCompare(b.filename);
    });
  }, [models]);

  // Empty state
  if (modelArray.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No models discovered. Run discovery scan to find models.</p>
      </div>
    );
  }

  return (
    <div className={styles.gridContainer}>
      {modelArray.map((model) => (
        <ModelCard
          key={model.modelId}
          model={model}
          metrics={modelMetrics[model.modelId]}
          isRunning={runningModels.has(model.modelId)}
          isExpanded={expandedSettings[model.modelId]}
          onToggleSettings={onToggleSettings}
          onToggleEnable={onToggleEnable}
          onStart={onStartModel}
          onStop={onStopModel}
          onRestart={onRestartModel}
          renderSettingsPanel={renderSettingsPanel}
        />
      ))}
    </div>
  );
};
