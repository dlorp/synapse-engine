import React from 'react';
import type { DiscoveredModel, ModelTier } from '@/types/models';
import { useUpdateTier, useUpdateThinking, useToggleEnabled } from '@/hooks/useModelManagement';
import styles from './ModelTable.module.css';

interface ModelTableProps {
  models: Record<string, DiscoveredModel>;
  expandedSettings?: Record<string, boolean>;
  onToggleSettings?: (modelId: string) => void;
  renderSettingsPanel?: (model: DiscoveredModel) => React.ReactNode;
}

/**
 * ModelTable displays all discovered models in a dense, terminal-styled table
 * with inline editing for tier, thinking capability, and enable/disable state.
 *
 * Features:
 * - Real-time inline editing with optimistic updates
 * - Visual override indicators for user-modified settings
 * - Color-coded status indicators
 * - Dense information display with badges
 * - Terminal aesthetic with monospace fonts and high contrast
 * - Expandable settings panel per model (Phase 2)
 */
export const ModelTable: React.FC<ModelTableProps> = ({
  models,
  expandedSettings = {},
  onToggleSettings,
  renderSettingsPanel,
}) => {
  const updateTier = useUpdateTier();
  const updateThinking = useUpdateThinking();
  const toggleEnabled = useToggleEnabled();

  const handleTierChange = (modelId: string, tier: ModelTier) => {
    updateTier.mutate({ modelId, tier });
  };

  const handleThinkingToggle = (modelId: string, thinking: boolean) => {
    updateThinking.mutate({ modelId, thinking });
  };

  const handleEnabledToggle = (modelId: string, enabled: boolean) => {
    toggleEnabled.mutate({ modelId, enabled });
  };

  /**
   * Get the effective tier (considers user override)
   */
  const getEffectiveTier = (model: DiscoveredModel): ModelTier => {
    return model.tierOverride || model.assignedTier;
  };

  /**
   * Get the effective thinking status (considers user override)
   */
  const isThinking = (model: DiscoveredModel): boolean => {
    return model.thinkingOverride ?? model.isThinkingModel;
  };

  const modelArray = Object.values(models);

  // Sort models by tier (fast > balanced > powerful), then by size
  const sortedModels = [...modelArray].sort((a, b) => {
    const tierOrder = { fast: 0, balanced: 1, powerful: 2 };
    const tierA = getEffectiveTier(a);
    const tierB = getEffectiveTier(b);

    if (tierOrder[tierA] !== tierOrder[tierB]) {
      return tierOrder[tierA] - tierOrder[tierB];
    }

    return a.sizeParams - b.sizeParams;
  });

  return (
    <div className={styles.tableContainer}>
      <table className={styles.modelTable}>
        <thead>
          <tr>
            <th className={styles.checkboxHeader}>ENABLED</th>
            {onToggleSettings && <th className={styles.actionsHeader}>CONFIG</th>}
            <th className={styles.modelHeader}>MODEL</th>
            <th className={styles.sizeHeader}>SIZE</th>
            <th className={styles.quantHeader}>QUANT</th>
            <th className={styles.tierHeader}>TIER</th>
            <th className={styles.thinkingHeader}>THINKING</th>
            <th className={styles.portHeader}>PORT</th>
            <th className={styles.statusHeader}>STATUS</th>
          </tr>
        </thead>
        <tbody>
          {sortedModels.map((model) => {
            const effectiveTier = getEffectiveTier(model);
            const thinkingStatus = isThinking(model);

            const isExpanded = expandedSettings[model.modelId] || false;

            return (
              <React.Fragment key={model.modelId}>
                <tr
                  className={`${styles.modelRow} ${model.enabled ? styles.enabled : styles.disabled}`}
                >
                  {/* Enable/Disable Checkbox */}
                  <td className={styles.checkboxCell}>
                    <input
                      type="checkbox"
                      checked={model.enabled}
                      onChange={(e) => handleEnabledToggle(model.modelId, e.target.checked)}
                      className={styles.checkbox}
                      aria-label={`Enable ${model.family} ${model.sizeParams}B`}
                    />
                  </td>

                  {/* Configure Button (MOVED HERE) */}
                  {onToggleSettings && (
                    <td className={styles.actionsCell}>
                      <button
                        onClick={() => onToggleSettings(model.modelId)}
                        className={`${styles.configButton} ${isExpanded ? styles.expanded : ''}`}
                        aria-label={`Configure ${model.family} ${model.sizeParams}B`}
                        aria-expanded={isExpanded}
                      >
                        <span className={styles.expandIcon}>
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      </button>
                    </td>
                  )}

                  {/* Model Name with Badges */}
                  <td className={styles.modelName}>
                    <div className={styles.modelInfo}>
                      <span className={styles.family}>
                        {model.family.toUpperCase()}
                      </span>
                      {model.version && (
                        <span className={styles.version}>v{model.version}</span>
                      )}
                      {model.isCoder && <span className={styles.badge}>CODER</span>}
                      {model.isInstruct && <span className={styles.badge}>INSTRUCT</span>}
                      {thinkingStatus && (
                        <span className={styles.thinkingBadge} title="Thinking model">
                          
                        </span>
                      )}
                    </div>
                    <div className={styles.filename}>{model.filename}</div>
                  </td>

                  {/* Size */}
                  <td className={styles.sizeCell}>
                    {model.sizeParams ? `${model.sizeParams.toFixed(1)}B` : '-'}
                  </td>

                  {/* Quantization */}
                  <td className={styles.quantCell}>{model.quantization}</td>

                  {/* Tier Select */}
                  <td className={styles.tierCell}>
                    <div className={styles.tierWrapper}>
                      <select
                        value={effectiveTier}
                        onChange={(e) => handleTierChange(model.modelId, e.target.value as ModelTier)}
                        className={`${styles.tierSelect} ${styles[`tier${effectiveTier}`]}`}
                        disabled={!model.enabled}
                        aria-label={`Tier for ${model.family} ${model.sizeParams}B`}
                      >
                        <option value="fast">FAST</option>
                        <option value="balanced">BALANCED</option>
                        <option value="powerful">POWERFUL</option>
                      </select>
                      {model.tierOverride && (
                        <span className={styles.overrideIndicator} title="User override">
                          *
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Thinking Toggle */}
                  <td className={styles.thinkingCell}>
                    <div className={styles.toggleWrapper}>
                      <label className={styles.toggleLabel}>
                        <input
                          type="checkbox"
                          checked={thinkingStatus}
                          onChange={(e) => handleThinkingToggle(model.modelId, e.target.checked)}
                          className={styles.toggleInput}
                          disabled={!model.enabled}
                          aria-label={`Thinking mode for ${model.family} ${model.sizeParams}B`}
                        />
                        <span className={styles.toggleSlider} />
                      </label>
                      {model.thinkingOverride !== undefined && (
                        <span className={styles.overrideIndicator} title="User override">
                          *
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Port */}
                  <td className={styles.portCell}>
                    {model.port ? (
                      <span className={styles.portNumber}>{model.port}</span>
                    ) : (
                      <span className={styles.portEmpty}>AUTO</span>
                    )}
                  </td>

                  {/* Status */}
                  <td className={styles.statusCell}>
                    <span
                      className={model.enabled ? styles.statusActive : styles.statusInactive}
                    >
                      {model.enabled ? 'ACTIVE' : 'IDLE'}
                    </span>
                  </td>
                </tr>

                {/* Expanded Settings Panel Row */}
                {isExpanded && renderSettingsPanel && (
                  <tr className={styles.settingsRow}>
                    <td colSpan={onToggleSettings ? 9 : 8} className={styles.settingsCell}>
                      {renderSettingsPanel(model)}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>

      {modelArray.length === 0 && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>⚠</div>
          <div className={styles.emptyText}>NO MODELS DISCOVERED</div>
          <div className={styles.emptyHint}>Run discovery scan to detect models in HUB directory</div>
        </div>
      )}
    </div>
  );
};
