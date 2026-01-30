/**
 * PresetEditor Component
 *
 * Modal dialog for creating and editing custom presets.
 * Provides a rich form for configuring:
 * - Preset name and description
 * - Planning tier (model used for reasoning)
 * - Per-tool tier configurations
 *
 * Features:
 * - Create new custom presets
 * - Edit existing custom presets
 * - Delete custom presets (with confirmation)
 * - Validation (name conflicts, required fields)
 * - Terminal aesthetic styling
 * - Keyboard navigation (Esc to close)
 *
 * Cannot edit or delete built-in presets (speed, balanced, quality, coding, research).
 */

import React, { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import type { ModelPreset, ModelTier, ToolName, ToolModelConfig } from '@/types/codeChat';
import { BUILT_IN_PRESETS } from '@/types/codeChat';
import { useCreatePreset, useUpdatePreset, useDeletePreset } from '@/hooks/usePresets';
import styles from './PresetEditor.module.css';

// ============================================================================
// Types & Constants
// ============================================================================

export interface PresetEditorProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Callback to close modal */
  onClose: () => void;
  /** Preset to edit (undefined for new preset) */
  preset?: ModelPreset;
  /** Mode: 'create' or 'edit' */
  mode: 'create' | 'edit';
  /** Callback on successful save */
  onSuccess?: (preset: ModelPreset) => void;
}

/** Available model tiers */
const TIERS: ModelTier[] = ['fast', 'balanced', 'powerful'];

/* All tool names (kept for reference, may be used in future expansion)
const ALL_TOOLS: ToolName[] = [
  'read_file',
  'write_file',
  'list_directory',
  'delete_file',
  'search_code',
  'grep_files',
  'web_search',
  'run_python',
  'run_shell',
  'git_status',
  'git_diff',
  'git_log',
  'git_commit',
  'git_branch',
  'get_diagnostics',
  'get_definitions',
  'get_references',
  'get_project_info',
];
*/

/** Human-readable tool names */
const TOOL_LABELS: Record<ToolName, string> = {
  read_file: 'Read File',
  write_file: 'Write File',
  list_directory: 'List Directory',
  delete_file: 'Delete File',
  search_code: 'Search Code',
  grep_files: 'Grep Files',
  web_search: 'Web Search',
  run_python: 'Run Python',
  run_shell: 'Run Shell',
  git_status: 'Git Status',
  git_diff: 'Git Diff',
  git_log: 'Git Log',
  git_commit: 'Git Commit',
  git_branch: 'Git Branch',
  get_diagnostics: 'Get Diagnostics',
  get_definitions: 'Get Definitions',
  get_references: 'Get References',
  get_project_info: 'Get Project Info',
};

/** Tool categories for grouping */
const TOOL_CATEGORIES = {
  'File Operations': ['read_file', 'write_file', 'list_directory', 'delete_file'] as ToolName[],
  'Code Search': ['search_code', 'grep_files'] as ToolName[],
  'Web': ['web_search'] as ToolName[],
  'Execution': ['run_python', 'run_shell'] as ToolName[],
  'Git': ['git_status', 'git_diff', 'git_log', 'git_commit', 'git_branch'] as ToolName[],
  'LSP/IDE': ['get_diagnostics', 'get_definitions', 'get_references', 'get_project_info'] as ToolName[],
};

// ============================================================================
// Component
// ============================================================================

export const PresetEditor: React.FC<PresetEditorProps> = ({
  isOpen,
  onClose,
  preset,
  mode,
  onSuccess,
}) => {
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [planningTier, setPlanningTier] = useState<ModelTier>('balanced');
  const [toolConfigs, setToolConfigs] = useState<Partial<Record<ToolName, ToolModelConfig>>>({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Mutations
  const createPreset = useCreatePreset();
  const updatePreset = useUpdatePreset();
  const deletePreset = useDeletePreset();

  // Initialize form from preset
  useEffect(() => {
    if (preset && mode === 'edit') {
      setName(preset.name);
      setDescription(preset.description);
      setPlanningTier(preset.planningTier);
      setToolConfigs(preset.toolConfigs || {});
    } else {
      // Reset for create mode
      setName('');
      setDescription('');
      setPlanningTier('balanced');
      setToolConfigs({});
    }
    setValidationError(null);
    setShowDeleteConfirm(false);
  }, [preset, mode, isOpen]);

  // Keyboard handler (Esc to close)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  /**
   * Validate form data.
   */
  const validate = useCallback((): string | null => {
    // Name required
    if (!name.trim()) {
      return 'Preset name is required';
    }

    // Name format (alphanumeric, underscore, hyphen only)
    if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
      return 'Preset name can only contain letters, numbers, underscores, and hyphens';
    }

    // Cannot use built-in names (only when creating or renaming)
    if (mode === 'create' || (mode === 'edit' && name !== preset?.name)) {
      if (BUILT_IN_PRESETS.includes(name as any)) {
        return `Cannot use built-in preset name: ${name}`;
      }
    }

    // Description required
    if (!description.trim()) {
      return 'Description is required';
    }

    return null;
  }, [name, description, mode, preset]);

  /**
   * Handle save (create or update).
   */
  const handleSave = useCallback(() => {
    // Validate
    const error = validate();
    if (error) {
      setValidationError(error);
      return;
    }

    // Build preset object
    const presetData: ModelPreset = {
      name: name.trim(),
      description: description.trim(),
      planningTier,
      toolConfigs: toolConfigs as Record<ToolName, ToolModelConfig>,
      isCustom: true,
    };

    if (mode === 'create') {
      createPreset.mutate(presetData, {
        onSuccess: (created) => {
          onSuccess?.(created);
          onClose();
        },
        onError: (error) => {
          setValidationError(error.message || 'Failed to create preset');
        },
      });
    } else {
      updatePreset.mutate(
        { name: preset!.name, preset: presetData },
        {
          onSuccess: (updated) => {
            onSuccess?.(updated);
            onClose();
          },
          onError: (error) => {
            setValidationError(error.message || 'Failed to update preset');
          },
        }
      );
    }
  }, [
    name,
    description,
    planningTier,
    toolConfigs,
    mode,
    preset,
    validate,
    createPreset,
    updatePreset,
    onSuccess,
    onClose,
  ]);

  /**
   * Handle delete (with confirmation).
   */
  const handleDelete = useCallback(() => {
    if (!preset) return;

    deletePreset.mutate(preset.name, {
      onSuccess: () => {
        onClose();
      },
      onError: (error) => {
        setValidationError(error.message || 'Failed to delete preset');
        setShowDeleteConfirm(false);
      },
    });
  }, [preset, deletePreset, onClose]);

  /**
   * Handle tool tier change.
   */
  const handleToolTierChange = useCallback((tool: ToolName, tier: ModelTier) => {
    setToolConfigs((prev) => ({
      ...prev,
      [tool]: { tier },
    }));
  }, []);

  /**
   * Get current tier for a tool.
   */
  const getToolTier = useCallback(
    (tool: ToolName): ModelTier => {
      return toolConfigs[tool]?.tier || 'balanced';
    },
    [toolConfigs]
  );

  /**
   * Handle close.
   */
  const handleClose = useCallback(() => {
    setShowDeleteConfirm(false);
    onClose();
  }, [onClose]);

  if (!isOpen) return null;

  const isBuiltIn = preset && !preset.isCustom;
  const isPending =
    createPreset.isPending || updatePreset.isPending || deletePreset.isPending;

  return (
    <div className={styles.overlay} onClick={handleClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.header}>
          <h2 className={styles.title}>
            {mode === 'create' ? 'CREATE PRESET' : 'EDIT PRESET'}
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className={styles.closeButton}
            aria-label="Close dialog"
          >
            ×
          </button>
        </div>

        {/* Warning for built-in presets */}
        {isBuiltIn && (
          <div className={styles.warning}>
            This is a built-in preset and cannot be modified. Create a custom preset instead.
          </div>
        )}

        {/* Form */}
        <div className={styles.form}>
          {/* Name */}
          <div className={styles.field}>
            <label htmlFor="preset-name" className={styles.label}>
              Name
            </label>
            <input
              id="preset-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={styles.input}
              placeholder="my_custom_preset"
              disabled={isBuiltIn || isPending}
              autoFocus
            />
          </div>

          {/* Description */}
          <div className={styles.field}>
            <label htmlFor="preset-description" className={styles.label}>
              Description
            </label>
            <input
              id="preset-description"
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={styles.input}
              placeholder="Optimized for..."
              disabled={isBuiltIn || isPending}
            />
          </div>

          {/* Planning Tier */}
          <div className={styles.field}>
            <label htmlFor="planning-tier" className={styles.label}>
              Planning Tier
            </label>
            <select
              id="planning-tier"
              value={planningTier}
              onChange={(e) => setPlanningTier(e.target.value as ModelTier)}
              className={styles.select}
              disabled={isBuiltIn || isPending}
            >
              {TIERS.map((tier) => (
                <option key={tier} value={tier}>
                  {tier.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Tool Configurations */}
          <div className={styles.toolConfigsSection}>
            <h3 className={styles.sectionTitle}>Tool Configurations</h3>
            <p className={styles.sectionHint}>
              Configure model tier for each tool (defaults to 'balanced' if not set)
            </p>

            <div className={styles.toolConfigs}>
              {Object.entries(TOOL_CATEGORIES).map(([category, tools]) => (
                <div key={category} className={styles.category}>
                  <h4 className={styles.categoryTitle}>{category}</h4>
                  {tools.map((tool) => (
                    <div key={tool} className={styles.toolRow}>
                      <label htmlFor={`tool-${tool}`} className={styles.toolLabel}>
                        {TOOL_LABELS[tool]}
                      </label>
                      <select
                        id={`tool-${tool}`}
                        value={getToolTier(tool)}
                        onChange={(e) => handleToolTierChange(tool, e.target.value as ModelTier)}
                        className={styles.toolSelect}
                        disabled={isBuiltIn || isPending}
                      >
                        {TIERS.map((tier) => (
                          <option key={tier} value={tier}>
                            {tier.toUpperCase()}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Validation Error */}
          {validationError && (
            <div className={styles.error} role="alert">
              {validationError}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className={styles.footer}>
          {/* Delete button (only for custom presets in edit mode) */}
          {mode === 'edit' && preset?.isCustom && !showDeleteConfirm && (
            <button
              type="button"
              onClick={() => setShowDeleteConfirm(true)}
              className={clsx(styles.button, styles.deleteButton)}
              disabled={isPending}
            >
              DELETE
            </button>
          )}

          {/* Delete confirmation */}
          {showDeleteConfirm && (
            <div className={styles.deleteConfirm}>
              <span className={styles.deleteConfirmText}>Confirm delete?</span>
              <button
                type="button"
                onClick={handleDelete}
                className={clsx(styles.button, styles.confirmDeleteButton)}
                disabled={isPending}
              >
                YES, DELETE
              </button>
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(false)}
                className={clsx(styles.button, styles.cancelButton)}
                disabled={isPending}
              >
                CANCEL
              </button>
            </div>
          )}

          {/* Main actions */}
          {!showDeleteConfirm && (
            <>
              <button
                type="button"
                onClick={handleClose}
                className={clsx(styles.button, styles.cancelButton)}
                disabled={isPending}
              >
                CANCEL
              </button>
              <button
                type="button"
                onClick={handleSave}
                className={clsx(styles.button, styles.saveButton)}
                disabled={isBuiltIn || isPending}
              >
                {isPending ? 'SAVING...' : mode === 'create' ? 'CREATE' : 'SAVE'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
