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

import type { InstanceConfig, CreateInstanceRequest, UpdateInstanceRequest } from '@/types/instances';
import { useUpdateInstance, useSystemPromptPresets } from '@/hooks/useInstances';

/**
 * InstanceEditForm - Inline edit form for instance configuration
 * Appears within the instance card when EDIT is clicked
 */
interface InstanceEditFormProps {
  instance: InstanceConfig;
  onCancel: () => void;
}

const InstanceEditForm: React.FC<InstanceEditFormProps> = ({ instance, onCancel }) => {
  // Form state (pre-populated from instance)
  const [displayName, setDisplayName] = React.useState(instance.displayName);
  const [systemPrompt, setSystemPrompt] = React.useState(instance.systemPrompt || '');
  const [webSearchEnabled, setWebSearchEnabled] = React.useState(instance.webSearchEnabled);
  const [selectedPreset, setSelectedPreset] = React.useState<string>('');

  // Validation state
  const [nameError, setNameError] = React.useState<string | null>(null);
  const [promptError, setPromptError] = React.useState<string | null>(null);

  // Data fetching
  const { data: presetsResponse } = useSystemPromptPresets();
  const updateMutation = useUpdateInstance();

  // Track if changes were made
  const hasChanges =
    displayName !== instance.displayName ||
    systemPrompt !== (instance.systemPrompt || '') ||
    webSearchEnabled !== instance.webSearchEnabled;

  // Validate display name
  const validateName = useCallback((value: string): boolean => {
    if (!value.trim()) {
      setNameError('Display name is required');
      return false;
    }
    if (value.length > 64) {
      setNameError('Display name must be 64 characters or less');
      return false;
    }
    setNameError(null);
    return true;
  }, []);

  // Validate system prompt
  const validatePrompt = useCallback((value: string): boolean => {
    if (value.length > 4096) {
      setPromptError('System prompt must be 4096 characters or less');
      return false;
    }
    setPromptError(null);
    return true;
  }, []);

  // Handle display name change
  const handleNameChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setDisplayName(value);
    validateName(value);
  }, [validateName]);

  // Handle system prompt change
  const handlePromptChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = event.target.value;
    setSystemPrompt(value);
    validatePrompt(value);
    setSelectedPreset(''); // Clear preset selection when manually editing
  }, [validatePrompt]);

  // Handle preset selection
  const handlePresetChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const presetId = event.target.value;
    setSelectedPreset(presetId);

    if (presetId && presetsResponse?.presets) {
      const preset = presetsResponse.presets.find(p => p.id === presetId);
      if (preset) {
        setSystemPrompt(preset.prompt);
        validatePrompt(preset.prompt);
      }
    }
  }, [presetsResponse, validatePrompt]);

  // Handle web search toggle
  const handleWebSearchToggle = useCallback(() => {
    setWebSearchEnabled(prev => !prev);
  }, []);

  // Handle form submission
  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();

    // Validate all fields
    const nameValid = validateName(displayName);
    const promptValid = validatePrompt(systemPrompt);

    if (!nameValid || !promptValid) {
      return;
    }

    // Build request with only changed fields
    const request: UpdateInstanceRequest = {};

    if (displayName !== instance.displayName) {
      request.displayName = displayName.trim();
    }
    if (systemPrompt !== (instance.systemPrompt || '')) {
      request.systemPrompt = systemPrompt.trim() || undefined;
    }
    if (webSearchEnabled !== instance.webSearchEnabled) {
      request.webSearchEnabled = webSearchEnabled;
    }

    try {
      await updateMutation.mutateAsync({
        instanceId: instance.instanceId,
        request,
      });
      onCancel(); // Close form on success
    } catch (error) {
      console.error('Failed to update instance:', error);
    }
  }, [displayName, systemPrompt, webSearchEnabled, instance, validateName, validatePrompt, updateMutation, onCancel]);

  // Character count for system prompt
  const promptCharCount = systemPrompt.length;
  const promptCharRemaining = 4096 - promptCharCount;

  return (
    <div className={styles.instanceEditForm}>
      <div className={styles.instanceEditHeader}>
        <span className={styles.instanceEditTitle}>EDIT INSTANCE CONFIGURATION</span>
      </div>
      <form onSubmit={handleSubmit} className={styles.instanceEditContent}>
        {/* Display Name */}
        <div className={styles.instanceFormGroup}>
          <label className={styles.instanceFormLabel}>
            DISPLAY NAME <span className={styles.instanceFormRequired}>*</span>
          </label>
          <input
            type="text"
            className={`${styles.instanceFormInput} ${nameError ? styles.instanceFormInputError : ''}`}
            value={displayName}
            onChange={handleNameChange}
            placeholder="e.g., Research Assistant"
            maxLength={64}
          />
          {nameError && <span className={styles.instanceFormError}>{nameError}</span>}
        </div>

        {/* System Prompt Preset */}
        <div className={styles.instanceFormGroup}>
          <label className={styles.instanceFormLabel}>SYSTEM PROMPT PRESET</label>
          <select
            className={styles.instanceFormSelect}
            value={selectedPreset}
            onChange={handlePresetChange}
          >
            <option value="">Custom / Keep Current</option>
            {presetsResponse?.presets.map(preset => (
              <option key={preset.id} value={preset.id}>
                {preset.name} - {preset.description}
              </option>
            ))}
          </select>
        </div>

        {/* System Prompt Textarea */}
        <div className={styles.instanceFormGroup}>
          <label className={styles.instanceFormLabel}>
            SYSTEM PROMPT
            <span className={styles.instanceFormCharCount}>
              {promptCharRemaining} chars remaining
            </span>
          </label>
          <textarea
            className={`${styles.instanceFormTextarea} ${promptError ? styles.instanceFormInputError : ''}`}
            value={systemPrompt}
            onChange={handlePromptChange}
            placeholder="Optional system prompt for this instance..."
            rows={4}
            maxLength={4096}
          />
          {promptError && <span className={styles.instanceFormError}>{promptError}</span>}
        </div>

        {/* Web Search Toggle */}
        <div className={styles.instanceFormGroup}>
          <label className={styles.instanceFormCheckboxLabel}>
            <input
              type="checkbox"
              className={styles.instanceFormCheckbox}
              checked={webSearchEnabled}
              onChange={handleWebSearchToggle}
            />
            <span className={styles.instanceFormCheckboxText}>ENABLE WEB SEARCH</span>
          </label>
        </div>

        {/* Error Message */}
        {updateMutation.isError && (
          <div className={styles.instanceFormErrorBanner}>
            <span className={styles.instanceFormErrorIcon}>!</span>
            <span className={styles.instanceFormErrorMessage}>
              {updateMutation.error instanceof Error
                ? updateMutation.error.message
                : 'Failed to update instance'}
            </span>
          </div>
        )}

        {/* Actions */}
        <div className={styles.instanceFormActions}>
          <button
            type="button"
            className={`${styles.instanceButton} ${styles.instanceFormCancelButton}`}
            onClick={onCancel}
            disabled={updateMutation.isPending}
          >
            CANCEL
          </button>
          <button
            type="submit"
            className={`${styles.instanceButton} ${styles.instanceFormSaveButton}`}
            disabled={updateMutation.isPending || !hasChanges}
          >
            {updateMutation.isPending ? 'SAVING...' : 'SAVE CHANGES'}
          </button>
        </div>
      </form>
    </div>
  );
};

export interface ModelCardProps {
  model: DiscoveredModel;
  metrics?: ModelMetrics;
  isRunning?: boolean;
  isExpanded?: boolean; // Settings panel expansion

  // Instance management
  instances?: InstanceConfig[];  // Filtered to this model
  onCreateInstance?: (modelId: string, config: CreateInstanceRequest) => Promise<void>;
  onEditInstance?: (instanceId: string) => void;
  onDeleteInstance?: (instanceId: string) => Promise<void>;
  onStartInstance?: (instanceId: string) => Promise<void>;
  onStopInstance?: (instanceId: string) => Promise<void>;

  // Existing
  onToggleSettings?: (modelId: string) => void;
  onToggleEnable?: (modelId: string, enabled: boolean) => void;
  renderSettingsPanel?: (model: DiscoveredModel) => React.ReactNode;
}

export const ModelCard: React.FC<ModelCardProps> = React.memo(({
  model,
  metrics,
  isRunning = false,
  isExpanded = false,
  instances,
  onToggleSettings,
  onToggleEnable,
  onCreateInstance,
  onEditInstance,
  onDeleteInstance,
  onStartInstance,
  onStopInstance,
  renderSettingsPanel
}) => {
  // State for details dropdown (separate from settings expansion)
  const [detailsExpanded, setDetailsExpanded] = React.useState(false);

  // State for inline instance editing
  const [editingInstanceId, setEditingInstanceId] = React.useState<string | null>(null);

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

  const handleEditInstanceClick = useCallback((instanceId: string) => {
    setEditingInstanceId(prevId => prevId === instanceId ? null : instanceId);
  }, []);

  const handleCancelEdit = useCallback(() => {
    setEditingInstanceId(null);
  }, []);

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

          {/* Settings Panel (INLINE - appears directly after SETTINGS button) */}
          {isExpanded && renderSettingsPanel && (
            <div className={styles.settingsPanel}>
              {renderSettingsPanel(model)}
            </div>
          )}
        </div>
      )}

      {/* Instance Section - Only show when details expanded and instances exist */}
      {detailsExpanded && instances && instances.length > 0 && (
        <div className={styles.instanceSection}>
          <pre className={styles.instanceSectionHeader}>
            {`◆ NEURAL SUBSTRATE INSTANCES ${'─'.repeat(40)} ${instances.length} active`}
          </pre>

          {instances.map((instance, idx) => (
            <div key={instance.instanceId} className={styles.instanceCard}>
              <pre className={styles.instanceHeader}>
                {`─ Instance ${String(idx + 1).padStart(2, '0')} ${'─'.repeat(50)}● ${instance.status === 'active' ? 'ACTIVE' : instance.status.toUpperCase()} ─`}
              </pre>
              <div className={styles.instanceContent}>
                <div className={styles.instanceInfo}>
                  <span className={styles.instanceName}>{instance.displayName}</span>
                  <span className={styles.instancePort}>:{instance.port}</span>
                </div>
                <div className={styles.instanceMeta}>
                  <span className={styles.instancePreset}>Web Search: {instance.webSearchEnabled ? 'ENABLED' : 'DISABLED'}</span>
                </div>
                <div className={styles.instanceActions}>
                  <button
                    className={styles.instanceButton}
                    onClick={() => handleEditInstanceClick(instance.instanceId)}
                    title="Edit instance configuration"
                    aria-expanded={editingInstanceId === instance.instanceId}
                  >
                    {editingInstanceId === instance.instanceId ? '✕' : 'EDIT'}
                  </button>
                  {instance.status === 'active' ? (
                    <button
                      className={`${styles.instanceButton} ${styles.stopButton}`}
                      onClick={() => onStopInstance?.(instance.instanceId)}
                      title="Stop instance"
                    >
                      STOP
                    </button>
                  ) : (
                    <button
                      className={`${styles.instanceButton} ${styles.startButton}`}
                      onClick={() => onStartInstance?.(instance.instanceId)}
                      title="Start instance"
                    >
                      START
                    </button>
                  )}
                  <button
                    className={`${styles.instanceButton} ${styles.deleteButton}`}
                    onClick={() => onDeleteInstance?.(instance.instanceId)}
                    title="Delete instance"
                  >
                    DELETE
                  </button>
                </div>
              </div>

              {/* Inline Edit Form */}
              {editingInstanceId === instance.instanceId && (
                <InstanceEditForm
                  instance={instance}
                  onCancel={handleCancelEdit}
                />
              )}
            </div>
          ))}

          <button
            className={styles.addInstanceButton}
            onClick={() => {
              const instanceCount = instances?.length || 0;
              const config: CreateInstanceRequest = {
                modelId: model.modelId,
                displayName: `${model.modelId}_${String(instanceCount + 1).padStart(2, '0')}`,
                webSearchEnabled: false,
              };
              onCreateInstance?.(model.modelId, config);
            }}
            title="Add new instance of this model"
          >
            + ADD INSTANCE
          </button>
        </div>
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for React.memo optimization
  // Only re-render if critical props changed (prevents flicker on metrics updates)

  // Instance-aware comparison
  const instancesChanged =
    prevProps.instances?.length !== nextProps.instances?.length ||
    JSON.stringify(prevProps.instances?.map(i => i.instanceId).sort()) !==
    JSON.stringify(nextProps.instances?.map(i => i.instanceId).sort());

  return (
    prevProps.model.modelId === nextProps.model.modelId &&
    prevProps.model.enabled === nextProps.model.enabled &&
    prevProps.model.port === nextProps.model.port &&
    prevProps.isRunning === nextProps.isRunning &&
    prevProps.isExpanded === nextProps.isExpanded &&
    !instancesChanged &&
    JSON.stringify(prevProps.metrics) === JSON.stringify(nextProps.metrics)
  );
});

ModelCard.displayName = 'ModelCard';
