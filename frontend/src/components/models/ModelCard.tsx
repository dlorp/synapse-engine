/**
 * ModelCard - Compact Model Status Card with Expandable Details
 *
 * Collapsed State: ~45px height - shows name, enable checkbox, tier, status
 * Expanded State: ~200px height - shows sparklines, stats, and settings button
 *
 * Design Philosophy:
 * - Enable checkbox only (no individual START/STOP buttons)
 * - All server control happens at page level (START ALL ENABLED / STOP ALL SERVERS)
 * - Details expand to show metrics and configuration
 * - 87% height reduction when collapsed (45px vs 350px old design)
 *
 * Performance: React.memo prevents unnecessary re-renders when displaying multiple cards
 */

import React, { useCallback, useMemo } from 'react';
import { ModelSparkline } from './ModelSparkline';
import type { DiscoveredModel } from '@/types/models';
import type { ModelMetrics } from '@/hooks/useModelMetrics';
import styles from './ModelCard.module.css';

export interface ModelCardProps {
  model: DiscoveredModel;
  metrics?: ModelMetrics;
  isRunning?: boolean;
  isExpanded?: boolean; // Settings panel expansion
  onToggleSettings?: (modelId: string) => void;
  onToggleEnable?: (modelId: string, enabled: boolean) => void;
  renderSettingsPanel?: (model: DiscoveredModel) => React.ReactNode;
}

export const ModelCard: React.FC<ModelCardProps> = React.memo(({
  model,
  metrics,
  isRunning = false,
  isExpanded = false,
  onToggleSettings,
  onToggleEnable,
  renderSettingsPanel
}) => {
  // State for details dropdown (separate from settings expansion)
  const [detailsExpanded, setDetailsExpanded] = React.useState(false);

  // Calculate uptime display (if running)
  const uptimeDisplay = useMemo(() => {
    if (!isRunning) return 'N/A';
    // Placeholder until backend provides startTime
    return 'Running';
  }, [isRunning]);

  // Determine status for indicator
  const status = isRunning ? 'active' : 'offline';

  // Get tier display badge
  const tierName = model.tierOverride || model.assignedTier;
  const tierBadge = tierName === 'fast' ? 'Q2' : tierName === 'balanced' ? 'Q3' : 'Q4';

  // Event handlers with useCallback for performance
  const handleToggleDetails = useCallback(() => {
    setDetailsExpanded(prev => !prev);
  }, []);

  const handleToggleEnable = useCallback(() => {
    onToggleEnable?.(model.modelId, !model.enabled);
  }, [model.modelId, model.enabled, onToggleEnable]);

  const handleToggleSettings = useCallback(() => {
    onToggleSettings?.(model.modelId);
  }, [model.modelId, onToggleSettings]);

  // Default metrics (empty arrays if not provided - graceful degradation)
  const metricsData = metrics || {
    tokensPerSecond: [],
    memoryGb: [],
    latencyMs: []
  };

  return (
    <div
      className={styles.modelCardCompact}
      data-tier={tierName}
      data-running={isRunning}
      data-details-expanded={detailsExpanded}
    >
      {/* Compact Header Row */}
      <div className={styles.compactHeader}>
        {/* Model Name */}
        <h3 className={styles.compactName} title={model.filename}>
          {model.filename}
        </h3>

        {/* Tier Badge */}
        <div className={styles.compactTier} data-tier={tierName}>
          {tierBadge}
        </div>

        {/* Status Indicator */}
        <div className={styles.compactStatus}>
          <span className={`${styles.statusDot} ${isRunning ? styles.statusActive : styles.statusOffline}`}>
            {isRunning ? '⚪' : '⚫'}
          </span>
          <span className={styles.statusLabel}>
            {status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Action Buttons Row - DETAILS and ENABLE side by side */}
      <div className={styles.compactActions}>
        <button
          className={`${styles.compactButton} ${styles.detailsButton}`}
          onClick={handleToggleDetails}
          aria-expanded={detailsExpanded}
          title={detailsExpanded ? 'Hide details' : 'Show metrics and settings'}
          aria-label={`${detailsExpanded ? 'Hide' : 'Show'} details for ${model.filename}`}
        >
          <span className={styles.buttonIcon}>{detailsExpanded ? '▲' : '▼'}</span>
          <span className={styles.buttonLabel}>DETAILS</span>
        </button>

        <button
          className={`${styles.compactButton} ${model.enabled ? styles.disableButton : styles.enableButton}`}
          onClick={handleToggleEnable}
          title={model.enabled ? 'Disable model (removes from START ALL)' : 'Enable model (includes in START ALL)'}
          aria-label={`${model.enabled ? 'Disable' : 'Enable'} ${model.filename}`}
        >
          <span className={styles.buttonIcon}>{model.enabled ? '✓' : '○'}</span>
          <span className={styles.buttonLabel}>{model.enabled ? 'ENABLED' : 'ENABLE'}</span>
        </button>
      </div>

      {/* Expandable Details Section */}
      {detailsExpanded && (
        <div className={styles.detailsSection}>
          {/* Sparklines (only show if running) */}
          {isRunning && (
            <div className={styles.metricsExpanded}>
              <ModelSparkline
                data={metricsData.tokensPerSecond}
                metricType="tokens"
                modelId={model.modelId}
              />
              <ModelSparkline
                data={metricsData.memoryGb}
                metricType="memory"
                modelId={model.modelId}
              />
              <ModelSparkline
                data={metricsData.latencyMs}
                metricType="latency"
                modelId={model.modelId}
              />
            </div>
          )}

          {/* Stats Grid */}
          <div className={styles.statsExpanded}>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>PORT:</span>
              <span className={styles.statValue}>{model.port || 'N/A'}</span>
              <span className={styles.statDivider}>│</span>
              <span className={styles.statLabel}>UPTIME:</span>
              <span className={styles.statValue}>{uptimeDisplay}</span>
            </div>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>QUANT:</span>
              <span className={styles.statValue}>{model.quantization}</span>
              <span className={styles.statDivider}>│</span>
              <span className={styles.statLabel}>SIZE:</span>
              <span className={styles.statValue}>{model.sizeParams}B</span>
            </div>
          </div>

          {/* Settings Button */}
          <div className={styles.settingsRow}>
            <button
              className={`${styles.compactButton} ${styles.settingsButtonCompact}`}
              onClick={handleToggleSettings}
              title="Configure model settings"
              aria-label={`Toggle settings for ${model.filename}`}
            >
              <span className={styles.buttonIcon}>⚙</span>
              <span className={styles.buttonLabel}>SETTINGS</span>
            </button>
          </div>
        </div>
      )}

      {/* Settings Panel (existing expandable panel) */}
      {isExpanded && renderSettingsPanel && (
        <div className={styles.settingsPanel}>
          {renderSettingsPanel(model)}
        </div>
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for React.memo optimization
  // Only re-render if critical props changed (prevents flicker on metrics updates)
  return (
    prevProps.model.modelId === nextProps.model.modelId &&
    prevProps.model.enabled === nextProps.model.enabled &&
    prevProps.model.port === nextProps.model.port &&
    prevProps.isRunning === nextProps.isRunning &&
    prevProps.isExpanded === nextProps.isExpanded &&
    JSON.stringify(prevProps.metrics) === JSON.stringify(nextProps.metrics)
  );
});

ModelCard.displayName = 'ModelCard';
