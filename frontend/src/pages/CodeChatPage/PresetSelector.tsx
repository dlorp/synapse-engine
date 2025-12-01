/**
 * PresetSelector Component
 *
 * Preset dropdown with optional per-tool override controls for Code Chat.
 * Allows users to select a named preset (speed/balanced/quality/coding/research)
 * and optionally override model tiers for specific tools.
 *
 * Features:
 * - Compact preset selection dropdown
 * - Optional advanced per-tool tier overrides
 * - Terminal aesthetic styling with phosphor orange
 * - Smooth toggle animation for advanced controls
 */

import React, { useState } from 'react';
import clsx from 'clsx';
import { ToolName, ToolModelConfig, ModelTier, ModelPreset } from '@/types/codeChat';
import styles from './PresetSelector.module.css';

// ============================================================================
// Types & Constants
// ============================================================================

export interface PresetSelectorProps {
  /** Currently selected preset name */
  selectedPreset: string;
  /** Callback when preset changes */
  onPresetChange: (preset: string) => void;
  /** Full configuration of the selected preset (for displaying actual tier values) */
  presetConfig?: ModelPreset;
  /** Per-tool tier overrides (optional) */
  toolOverrides?: Partial<Record<ToolName, ToolModelConfig>>;
  /** Callback when overrides change (optional) */
  onOverrideChange?: (overrides: Partial<Record<ToolName, ToolModelConfig>>) => void;
  /** Initial state of advanced controls visibility */
  showOverrides?: boolean;
  /** Additional CSS class */
  className?: string;
}

/** Available preset names */
const PRESETS = ['speed', 'balanced', 'quality', 'coding', 'research'] as const;

/** Available model tiers */
const TIERS: ModelTier[] = ['fast', 'balanced', 'powerful'];

/** Tools to display in override controls (most commonly used) */
const DISPLAY_TOOLS: ToolName[] = [
  'read_file',
  'write_file',
  'search_code',
  'web_search',
  'run_python',
];

/** Human-readable tool names */
const TOOL_LABELS: Record<ToolName, string> = {
  read_file: 'read file',
  write_file: 'write file',
  list_directory: 'list dir',
  delete_file: 'delete file',
  search_code: 'search code',
  grep_files: 'grep files',
  web_search: 'web search',
  run_python: 'run python',
  run_shell: 'run shell',
  git_status: 'git status',
  git_diff: 'git diff',
  git_log: 'git log',
  git_commit: 'git commit',
  git_branch: 'git branch',
  get_diagnostics: 'diagnostics',
  get_definitions: 'definitions',
  get_references: 'references',
  get_project_info: 'project info',
};

// ============================================================================
// Component
// ============================================================================

export const PresetSelector: React.FC<PresetSelectorProps> = ({
  selectedPreset,
  onPresetChange,
  presetConfig,
  toolOverrides,
  onOverrideChange,
  showOverrides = false,
  className,
}) => {
  const [advancedOpen, setAdvancedOpen] = useState(showOverrides);

  /**
   * Handle tier change for a specific tool.
   */
  const handleOverrideChange = (tool: ToolName, tier: ModelTier) => {
    if (onOverrideChange) {
      onOverrideChange({
        ...toolOverrides,
        [tool]: { tier },
      });
    }
  };

  /**
   * Clear override for a specific tool (reset to preset default).
   */
  const handleClearOverride = (tool: ToolName) => {
    if (onOverrideChange && toolOverrides) {
      const newOverrides = { ...toolOverrides };
      delete newOverrides[tool];
      onOverrideChange(newOverrides);
    }
  };

  /**
   * Get the preset's default tier for a tool.
   */
  const getPresetTier = (tool: ToolName): ModelTier => {
    if (presetConfig?.toolConfigs?.[tool]?.tier) {
      return presetConfig.toolConfigs[tool].tier;
    }
    // Debug: Log when preset config is missing or tool not found
    if (!presetConfig) {
      console.debug(`[PresetSelector] No presetConfig available for preset: ${selectedPreset}`);
    } else if (!presetConfig.toolConfigs[tool]) {
      console.debug(`[PresetSelector] Tool '${tool}' not found in toolConfigs for preset '${selectedPreset}'`, {
        availableTools: Object.keys(presetConfig.toolConfigs),
        presetConfig,
      });
    }
    // Fallback to 'balanced' if preset config not available
    return 'balanced';
  };

  /**
   * Check if a tool has a user override (vs using preset default).
   */
  const hasUserOverride = (tool: ToolName): boolean => {
    return toolOverrides?.[tool]?.tier !== undefined;
  };

  /**
   * Get current tier for a tool.
   * Priority: user override > preset default > 'balanced' fallback
   */
  const getCurrentTier = (tool: ToolName): ModelTier => {
    // User override takes priority
    if (toolOverrides?.[tool]?.tier) {
      return toolOverrides[tool]!.tier;
    }
    // Preset default
    return getPresetTier(tool);
  };

  return (
    <div className={clsx(styles.container, className)}>
      {/* Main preset dropdown */}
      <div className={styles.presetRow}>
        <label className={styles.label} htmlFor="preset-select">
          PRESET:
        </label>
        <select
          id="preset-select"
          value={selectedPreset}
          onChange={(e) => onPresetChange(e.target.value)}
          className={styles.select}
          aria-label="Model preset selection"
        >
          {PRESETS.map((preset) => (
            <option key={preset} value={preset}>
              {preset.toUpperCase()}
            </option>
          ))}
        </select>
      </div>

      {/* Advanced toggle (only show if override callback provided) */}
      {onOverrideChange && (
        <label className={styles.advancedToggle}>
          <input
            type="checkbox"
            checked={advancedOpen}
            onChange={(e) => setAdvancedOpen(e.target.checked)}
            className={styles.checkbox}
            aria-label="Show per-tool overrides"
          />
          <span className={styles.checkboxLabel}>Show per-tool overrides</span>
        </label>
      )}

      {/* Per-tool overrides (collapsible) */}
      {advancedOpen && onOverrideChange && (
        <div className={styles.overrides} role="group" aria-label="Per-tool tier overrides">
          {DISPLAY_TOOLS.map((tool) => {
            const isOverridden = hasUserOverride(tool);
            return (
              <div
                key={tool}
                className={clsx(styles.overrideRow, isOverridden && styles.overrideRowModified)}
              >
                <label className={styles.toolName} htmlFor={`tier-${tool}`}>
                  {TOOL_LABELS[tool]}:
                  {isOverridden && <span className={styles.overrideIndicator}>*</span>}
                </label>
                <select
                  id={`tier-${tool}`}
                  value={getCurrentTier(tool)}
                  onChange={(e) => handleOverrideChange(tool, e.target.value as ModelTier)}
                  className={clsx(styles.tierSelect, isOverridden && styles.tierSelectOverridden)}
                  aria-label={`Model tier for ${TOOL_LABELS[tool]}${isOverridden ? ' (overridden)' : ' (preset default)'}`}
                >
                  {TIERS.map((tier) => (
                    <option key={tier} value={tier}>
                      {tier.toUpperCase()}
                    </option>
                  ))}
                </select>
                {isOverridden && (
                  <button
                    type="button"
                    className={styles.resetButton}
                    onClick={() => handleClearOverride(tool)}
                    aria-label={`Reset ${TOOL_LABELS[tool]} to preset default`}
                    title="Reset to preset default"
                  >
                    ×
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
