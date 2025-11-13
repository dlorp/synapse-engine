import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AsciiPanel, Input, Button, Divider, ProgressBar } from '@/components/terminal';
import {
  useSettings,
  useUpdateSettings,
  useResetSettings,
  useVRAMEstimate,
  useRestartServers,
} from '@/hooks/useSettings';
import { useUpdatePortRange } from '@/hooks/useModelManagement';
import type { RuntimeSettings } from '@/types/settings';
import { CTX_SIZE_PRESETS, EMBEDDING_MODELS } from '@/types/settings';
import styles from './SettingsPage.module.css';

interface ModelRegistry {
  models: Record<string, any>;
  portRange: [number, number];
  scanPath: string;
  lastScan: string;
}

interface ValidationErrors {
  [key: string]: string;
}

export const SettingsPage: React.FC = () => {
  // API hooks
  const { data: settingsResponse, isLoading: isLoadingSettings, refetch } = useSettings();
  const updateMutation = useUpdateSettings();
  const resetMutation = useResetSettings();
  const restartServersMutation = useRestartServers();
  const updatePortRangeMutation = useUpdatePortRange();

  // Fetch model registry for port range information
  const { data: registry } = useQuery<ModelRegistry>({
    queryKey: ['model-registry'],
    queryFn: async () => {
      const response = await fetch('/api/models/registry');
      if (!response.ok) throw new Error('Failed to fetch model registry');
      return response.json();
    },
  });

  // Local state for pending changes
  const [pendingChanges, setPendingChanges] = useState<Partial<RuntimeSettings>>({});
  const [restartRequired, setRestartRequired] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [useDefaultCache, setUseDefaultCache] = useState(true);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [showRestartModal, setShowRestartModal] = useState(false);

  // Tooltip toggle state (persisted to localStorage)
  const [showTooltips, setShowTooltips] = useState(() => {
    const stored = localStorage.getItem('synapse_show_tooltips');
    return stored !== null ? stored === 'true' : true; // Default to true
  });

  // Current settings (merge saved with pending)
  const currentSettings = useMemo(() => {
    if (!settingsResponse?.settings) return null;
    return { ...settingsResponse.settings, ...pendingChanges };
  }, [settingsResponse?.settings, pendingChanges]);

  // VRAM estimate based on current GPU settings
  const { data: vramEstimate } = useVRAMEstimate(
    8.0, // Assuming 8B model (could be made dynamic)
    'Q4_K_M' // Could be made dynamic based on model selection
  );

  // Calculate assigned ports from registry
  const assignedPorts = useMemo(() => {
    if (!registry?.models) return [];
    return Object.values(registry.models)
      .map((model: any) => model.port)
      .filter((port): port is number => port != null);
  }, [registry]);

  // Port range state (editable)
  const [portRangeStart, setPortRangeStart] = useState(registry?.portRange?.[0] || 8080);
  const [portRangeEnd, setPortRangeEnd] = useState(registry?.portRange?.[1] || 8099);

  // Update port range state when registry changes
  useEffect(() => {
    if (registry?.portRange) {
      setPortRangeStart(registry.portRange[0]);
      setPortRangeEnd(registry.portRange[1]);
    }
  }, [registry?.portRange]);

  // Track if port range changed (only if registry is loaded)
  const portRangeChanged = registry?.portRange
    ? portRangeStart !== registry.portRange[0] || portRangeEnd !== registry.portRange[1]
    : false;

  // Track if settings changed vs saved values
  const hasChanges = useMemo(
    () => Object.keys(pendingChanges).length > 0 || portRangeChanged,
    [pendingChanges, portRangeChanged]
  );

  // GPU-related fields that require restart
  const GPU_RESTART_FIELDS = [
    'n_gpu_layers',
    'ctx_size',
    'threads',
    'batch_size',
    'ubatch_size',
    'flash_attn',
    'no_mmap',
  ];

  /**
   * Update pending changes and track if restart required
   */
  const handleFieldChange = useCallback(
    (field: keyof RuntimeSettings, value: any) => {
      // Only add to pending changes if value actually changed
      if (currentSettings && currentSettings[field] === value) {
        return; // No change, don't mark as unsaved
      }

      setPendingChanges((prev) => ({ ...prev, [field]: value }));

      // Check if this field requires restart
      if (GPU_RESTART_FIELDS.includes(field)) {
        setRestartRequired(true);
      }

      // Clear validation error for this field
      setValidationErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    },
    [GPU_RESTART_FIELDS, currentSettings]
  );

  /**
   * Validate all pending changes
   */
  const validateChanges = useCallback((): boolean => {
    if (!currentSettings) return false;

    const errors: ValidationErrors = {};

    // Validate ubatch_size <= batch_size
    if (currentSettings.ubatch_size > currentSettings.batch_size) {
      errors.ubatch_size = 'Must be ≤ batch_size';
    }

    // Validate chunk_overlap < chunk_size
    if (currentSettings.cgrag_chunk_overlap >= currentSettings.cgrag_chunk_size) {
      errors.cgrag_chunk_overlap = 'Must be < chunk size';
    }

    // Validate ranges
    if (currentSettings.n_gpu_layers < 0 || currentSettings.n_gpu_layers > 99) {
      errors.n_gpu_layers = 'Must be between 0-99 (99 = max GPU offload)';
    }

    if (currentSettings.threads < 1 || currentSettings.threads > 64) {
      errors.threads = 'Must be between 1-64';
    }

    if (
      currentSettings.cgrag_min_relevance < 0 ||
      currentSettings.cgrag_min_relevance > 1
    ) {
      errors.cgrag_min_relevance = 'Must be between 0.0-1.0';
    }

    if (currentSettings.benchmark_parallel_max_models > 5) {
      errors.benchmark_parallel_max_models = 'Warning: High VRAM usage';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [currentSettings]);

  /**
   * Save settings to backend
   */
  const handleSave = useCallback(async () => {
    if (!validateChanges()) {
      return;
    }

    try {
      // Save runtime settings if changed
      if (Object.keys(pendingChanges).length > 0) {
        await updateMutation.mutateAsync(pendingChanges);
        setPendingChanges({});
      }

      // Save port range if changed
      if (portRangeChanged) {
        if (portRangeStart >= portRangeEnd) {
          console.error('Invalid port range: start must be less than end');
          return;
        }
        await updatePortRangeMutation.mutateAsync({
          start: portRangeStart,
          end: portRangeEnd,
        });
      }

      console.log('Settings saved successfully');
      setRestartRequired(true); // Port range changes require restart
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  }, [
    pendingChanges,
    portRangeChanged,
    portRangeStart,
    portRangeEnd,
    validateChanges,
    updateMutation,
    updatePortRangeMutation,
  ]);

  /**
   * Reset settings to defaults
   */
  const handleReset = useCallback(() => {
    resetMutation.mutate(undefined, {
      onSuccess: () => {
        setPendingChanges({});
        setRestartRequired(true); // Assume reset requires restart
        setShowResetDialog(false);
        refetch();
      },
      onError: (error) => {
        console.error('Failed to reset settings:', error);
      },
    });
  }, [resetMutation, refetch]);

  /**
   * Discard pending changes
   */
  const handleDiscard = useCallback(() => {
    setPendingChanges({});
    setValidationErrors({});
    setRestartRequired(false);
    // Reset port range to registry values
    if (registry?.portRange) {
      setPortRangeStart(registry.portRange[0]);
      setPortRangeEnd(registry.portRange[1]);
    }
  }, [registry]);

  /**
   * Set max GPU offload preset
   */
  const handleMaxGPUOffload = useCallback(() => {
    handleFieldChange('n_gpu_layers', 99);
  }, [handleFieldChange]);

  // Format context size display
  const formatCtxSize = (size: number): string => {
    if (size >= 1024) {
      return `${(size / 1024).toFixed(0)}K (${size.toLocaleString()} tokens)`;
    }
    return `${size} tokens`;
  };

  // Format relevance as percentage
  const formatRelevance = (value: number): string => {
    return `${(value * 100).toFixed(0)}%`;
  };

  // Format token budget
  const formatTokenBudget = (value: number): string => {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(0)}K tokens`;
    }
    return `${value} tokens`;
  };

  // Render tooltip helper
  const renderTooltip = (text: string) => {
    if (!showTooltips) return null;
    return (
      <span className={styles.tooltip} data-tooltip={text}>
        ⓘ
      </span>
    );
  };

  // Validate on change
  useEffect(() => {
    if (hasChanges) {
      validateChanges();
    }
  }, [hasChanges, validateChanges]);

  // Handle embedding cache path checkbox
  useEffect(() => {
    if (useDefaultCache && currentSettings) {
      handleFieldChange('embedding_model_cache_path', null);
    }
  }, [useDefaultCache, handleFieldChange, currentSettings]);

  // Persist tooltip preference to localStorage
  useEffect(() => {
    localStorage.setItem('synapse_show_tooltips', String(showTooltips));
  }, [showTooltips]);

  if (isLoadingSettings || !currentSettings) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>LOADING SETTINGS...</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>SYSTEM CONFIGURATION</h1>

      {/* System Configuration Section with ASCII Border */}
      <AsciiPanel title="SYSTEM CONFIGURATION">
        <label className={styles.terminalCheckbox}>
          <input
            type="checkbox"
            checked={showTooltips}
            onChange={(e) => setShowTooltips(e.target.checked)}
          />
          <span className={styles.checkboxLabel}>SHOW HELP TOOLTIPS</span>
          {showTooltips && <span className={styles.checkboxStatus}>⚪ ENABLED</span>}
        </label>
        <p className={styles.helpText}>
          Display contextual help when hovering over interface elements
        </p>
      </AsciiPanel>

      {/* Restart Required Banner */}
      {restartRequired && (
        <div className={styles.restartBanner}>
          <div className={styles.restartContent}>
            <div className={styles.restartIcon}>⚠</div>
            <div className={styles.restartText}>
              <div className={styles.restartTitle}>SERVER RESTART REQUIRED</div>
              <div className={styles.restartMessage}>
                GPU/VRAM changes require server restart to take effect
              </div>
            </div>
            <button
              onClick={() => setShowRestartModal(true)}
              className={styles.restartButton}
              disabled={restartServersMutation.isPending}
            >
              {restartServersMutation.isPending ? 'RESTARTING...' : 'RESTART NOW'}
            </button>
          </div>
        </div>
      )}

      {/* Pending Changes Badge */}
      {hasChanges && (
        <div className={styles.pendingBadge}>
          <span className={styles.pendingCount}>{Object.keys(pendingChanges).length}</span>
          <span className={styles.pendingText}>UNSAVED CHANGES</span>
        </div>
      )}

      {/* Section 1: Port Configuration with ASCII Border */}
      <AsciiPanel title="PORT CONFIGURATION">
        <p className={styles.sectionDescription}>
          Configure the port range for llama.cpp model servers. Individual models can be
          assigned specific ports in Model Management.
        </p>

        <div className={styles.portRangeGrid}>
          <div className={styles.field}>
            <label className={styles.label}>
              PORT RANGE START
              {renderTooltip(
                'Starting port number for llama.cpp model servers. Must be between 1024-65535. Each model requires one unique port.'
              )}
              <span className={styles.hint}>⚠ Minimum: 1024</span>
            </label>
            <Input
              type="number"
              min={1024}
              max={65535}
              value={portRangeStart}
              onChange={(e) => {
                setPortRangeStart(parseInt(e.target.value, 10) || 1024);
                setRestartRequired(true);
              }}
              className={styles.numericInput}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>
              PORT RANGE END
              {renderTooltip(
                'Ending port number for llama.cpp model servers. The total range determines how many models can run simultaneously.'
              )}
              <span className={styles.hint}>⚠ Maximum: 65535</span>
            </label>
            <Input
              type="number"
              min={1024}
              max={65535}
              value={portRangeEnd}
              onChange={(e) => {
                setPortRangeEnd(parseInt(e.target.value, 10) || 65535);
                setRestartRequired(true);
              }}
              className={styles.numericInput}
            />
          </div>
        </div>

        {/* Status Display Box */}
        <AsciiPanel title="STATUS">
          <div className={styles.portStatus}>
            <span className={styles.portLabel}>AVAILABLE PORTS:</span>
            <span className={`${styles.portValue} ${styles.available}`}>
              {portRangeEnd - portRangeStart + 1} ports ({portRangeStart}-{portRangeEnd}) ✓
            </span>
            {portRangeStart >= portRangeEnd && (
              <span className={styles.errorText}> ⚠ Start port must be less than end port</span>
            )}
          </div>

          {assignedPorts.length > 0 && (
            <div className={styles.portStatus}>
              <span className={styles.portLabel}>ASSIGNED PORTS:</span>
              <span className={`${styles.portValue} ${styles.assigned}`}>
                {assignedPorts.length} in use (
                {assignedPorts.sort((a, b) => a - b).join(', ')})
              </span>
            </div>
          )}
        </AsciiPanel>
      </AsciiPanel>

      <Divider spacing="lg" />

      {/* Section 2: Global Model Runtime Defaults with ASCII Border */}
      <AsciiPanel title="GLOBAL MODEL RUNTIME DEFAULTS">
        <p className={styles.sectionDescription}>
          These settings apply to all models unless overridden individually.
        </p>

        {/* 3-Column Grid: GPU / Context / Performance */}
        <div className={styles.settingsGrid}>
          {/* GPU Acceleration Column */}
          <div className={styles.settingsColumn}>
            <AsciiPanel title="GPU ACCELERATION">
              <div className={styles.columnBody}>
                <div className={styles.field}>
                  <label className={styles.label}>
                    GPU LAYERS
                    {renderTooltip(
                      'Number of model layers offloaded to GPU. Higher = more VRAM usage but faster inference. Use 99 for max GPU offload.'
                    )}
                  </label>
                  <div className={styles.sliderGroup}>
                    <input
                      type="range"
                      min="0"
                      max="99"
                      value={currentSettings.n_gpu_layers}
                      onChange={(e) =>
                        handleFieldChange('n_gpu_layers', parseInt(e.target.value, 10))
                      }
                      className={styles.slider}
                    />
                    <Input
                      type="number"
                      min="0"
                      max="99"
                      value={currentSettings.n_gpu_layers}
                      onChange={(e) =>
                        handleFieldChange('n_gpu_layers', parseInt(e.target.value, 10))
                      }
                      className={styles.numericInput}
                      error={validationErrors.n_gpu_layers}
                    />
                  </div>
                  <div className={styles.fieldInfo}>⚡ Metal acceleration</div>
                </div>
              </div>
            </AsciiPanel>
          </div>

          {/* Context Column */}
          <div className={styles.settingsColumn}>
            <AsciiPanel title="CONTEXT">
              <div className={styles.columnBody}>
                <div className={styles.field}>
                  <label className={styles.label}>
                    CONTEXT SIZE
                    {renderTooltip(
                      'Maximum number of tokens the model can process at once. Larger contexts use more VRAM.'
                    )}
                  </label>
                  <select
                    value={currentSettings.ctx_size}
                    onChange={(e) =>
                      handleFieldChange('ctx_size', parseInt(e.target.value, 10))
                    }
                    className={styles.select}
                  >
                    {CTX_SIZE_PRESETS.map((size) => (
                      <option key={size} value={size}>
                        {formatCtxSize(size)}
                      </option>
                    ))}
                  </select>
                  <div className={styles.fieldInfo}>🧠 Tokens in memory</div>
                </div>
              </div>
            </AsciiPanel>
          </div>

          {/* Performance Column */}
          <div className={styles.settingsColumn}>
            <AsciiPanel title="PERFORMANCE">
              <div className={styles.columnBody}>
                <div className={styles.field}>
                  <label className={styles.label}>
                    THREADS
                    {renderTooltip(
                      'Number of CPU threads for inference. Higher values improve speed but increase CPU usage.'
                    )}
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max="64"
                    value={currentSettings.threads}
                    onChange={(e) =>
                      handleFieldChange('threads', parseInt(e.target.value, 10))
                    }
                    error={validationErrors.threads}
                  />
                  <div className={styles.fieldInfo}>⚙ CPU threads</div>
                </div>
              </div>
            </AsciiPanel>
          </div>
        </div>

        {/* Batch Settings Row */}
        <AsciiPanel title="BATCH SETTINGS">
          <div className={styles.batchBody}>
              <div className={styles.batchGrid}>
                <div className={styles.field}>
                  <label className={styles.label}>
                    BATCH SIZE
                    {renderTooltip(
                      'Maximum number of tokens processed in parallel during prompt evaluation. Higher values improve throughput but increase VRAM usage. Recommended: 512-2048.'
                    )}
                  </label>
                  <Input
                    type="number"
                    min="32"
                    max="2048"
                    step="32"
                    value={currentSettings.batch_size}
                    onChange={(e) =>
                      handleFieldChange('batch_size', parseInt(e.target.value, 10))
                    }
                    className={styles.numericInput}
                  />
                </div>

                <div className={styles.field}>
                  <label className={styles.label}>
                    UBATCH SIZE
                    {renderTooltip(
                      'Micro-batch size for token generation. Must be ≤ batch_size. Lower values reduce VRAM usage with minimal performance impact. Recommended: 256-512.'
                    )}
                  </label>
                  <Input
                    type="number"
                    min="32"
                    max="1024"
                    step="32"
                    value={currentSettings.ubatch_size}
                    onChange={(e) =>
                      handleFieldChange('ubatch_size', parseInt(e.target.value, 10))
                    }
                    error={validationErrors.ubatch_size}
                    className={styles.numericInput}
                  />
                </div>

                <label className={styles.terminalCheckbox}>
                  <input
                    type="checkbox"
                    checked={currentSettings.flash_attn}
                    onChange={(e) => handleFieldChange('flash_attn', e.target.checked)}
                  />
                  <span className={styles.checkboxLabel}>
                    FLASH ATTENTION
                    {renderTooltip(
                      'Enable Flash Attention 2 algorithm for faster, more memory-efficient attention computation. Requires compatible GPU and model.'
                    )}
                  </span>
                  {currentSettings.flash_attn && <span className={styles.checkboxStatus}>⚪ ENABLED</span>}
                </label>

                <label className={styles.terminalCheckbox}>
                  <input
                    type="checkbox"
                    checked={currentSettings.no_mmap}
                    onChange={(e) => handleFieldChange('no_mmap', e.target.checked)}
                  />
                  <span className={styles.checkboxLabel}>
                    NO MMAP
                    {renderTooltip(
                      'Disable memory-mapped file I/O for model loading. Increases RAM usage but may improve performance on some systems. Leave disabled for optimal memory efficiency.'
                    )}
                  </span>
                  {currentSettings.no_mmap && <span className={styles.checkboxStatus}>⚪ ENABLED</span>}
                </label>
              </div>
            </div>
        </AsciiPanel>

        {/* Action Buttons Row */}
        <div className={styles.actionRow}>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={
                !hasChanges ||
                Object.keys(validationErrors).length > 0 ||
                updateMutation.isPending
              }
              loading={updateMutation.isPending}
            >
              {updateMutation.isPending ? 'APPLYING...' : '● APPLY CHANGES'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setShowResetDialog(true)}
              disabled={resetMutation.isPending}
            >
              ○ RESET TO DEFAULTS
            </Button>
            <Button
              variant="secondary"
              onClick={() => refetch()}
            >
              ⟳ RELOAD CONFIG
            </Button>
        </div>
      </AsciiPanel>

      <Divider spacing="lg" />

      {/* Section 3: Embedding Configuration with ASCII Border */}
      <AsciiPanel title="EMBEDDING CONFIGURATION">
          <p className={styles.sectionDescription}>
            Configuration for HuggingFace sentence transformer models used in CGRAG retrieval.
          </p>

          {/* Embedding Model */}
          <div className={styles.field}>
            <label className={styles.label}>
              EMBEDDING MODEL
              {renderTooltip(
                'Sentence transformer model for semantic search. Changing this requires re-indexing CGRAG data.'
              )}
            </label>
            <select
              value={currentSettings.embedding_model_name}
              onChange={(e) =>
                handleFieldChange('embedding_model_name', e.target.value)
              }
              className={styles.select}
            >
              {EMBEDDING_MODELS.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>

          {/* Embedding Dimension */}
          <div className={styles.field}>
            <label className={styles.label}>
              EMBEDDING DIMENSION
              {renderTooltip('Must match model output dimension')}
            </label>
            <Input
              type="number"
              min="128"
              max="1536"
              value={currentSettings.embedding_dimension}
              onChange={(e) =>
                handleFieldChange('embedding_dimension', parseInt(e.target.value, 10))
              }
              className={styles.numericInput}
            />
          </div>

          {/* Embedding Cache Path */}
          <div className={styles.field}>
            <label className={styles.terminalCheckbox}>
              <input
                type="checkbox"
                checked={useDefaultCache}
                onChange={(e) => setUseDefaultCache(e.target.checked)}
              />
              <span className={styles.checkboxLabel}>Use default cache location (~/.cache/huggingface)</span>
              {useDefaultCache && <span className={styles.checkboxStatus}>⚪ ENABLED</span>}
            </label>
            {renderTooltip(
              'Store HuggingFace models in default cache directory. Uncheck to specify custom location.'
            )}
            {!useDefaultCache && (
              <Input
                type="text"
                value={currentSettings.embedding_model_cache_path || ''}
                onChange={(e) =>
                  handleFieldChange('embedding_model_cache_path', e.target.value)
                }
                placeholder="/custom/cache/path"
                className={styles.pathInput}
              />
            )}
          </div>
      </AsciiPanel>

      <Divider spacing="lg" />

      {/* Section 4: CGRAG Configuration with ASCII Border */}
      <AsciiPanel title="CGRAG CONFIGURATION">
          <p className={styles.sectionDescription}>
            Contextually-Guided Retrieval Augmented Generation settings for semantic search and
            context retrieval.
          </p>

          {/* 2-Column Grid: Top K Results & Min Relevance */}
          <div className={styles.cgragTopGrid}>
            {/* Top K Results */}
            <div className={styles.field}>
              <label className={styles.label}>
                TOP K RESULTS
                {renderTooltip(
                  'Maximum number of CGRAG results to retrieve. Higher values provide more context but increase token usage.'
                )}
              </label>
              <Input
                type="number"
                min="1"
                max="100"
                value={currentSettings.cgrag_max_results}
                onChange={(e) =>
                  handleFieldChange('cgrag_max_results', parseInt(e.target.value, 10))
                }
                className={styles.numericInput}
              />
            </div>

            {/* Minimum Relevance Score */}
            <div className={styles.field}>
              <label className={styles.label}>
                MIN RELEVANCE SCORE
                {renderTooltip(
                  'Minimum similarity threshold for CGRAG results. Higher values return only highly relevant context.'
                )}
              </label>
              <Input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={currentSettings.cgrag_min_relevance}
                onChange={(e) =>
                  handleFieldChange('cgrag_min_relevance', parseFloat(e.target.value))
                }
                className={styles.numericInput}
              />
              <div className={styles.fieldInfo}>
                {formatRelevance(currentSettings.cgrag_min_relevance)}
              </div>
            </div>
          </div>

          {/* Token Budget */}
          <div className={styles.field}>
            <label className={styles.label}>
              TOKEN BUDGET
              {renderTooltip(
                'Maximum tokens allocated for CGRAG context retrieval. Higher values provide more context but reduce available tokens for generation.'
              )}
            </label>
            <Input
              type="number"
              min="1000"
              max="32000"
              step="1000"
              value={currentSettings.cgrag_token_budget}
              onChange={(e) =>
                handleFieldChange('cgrag_token_budget', parseInt(e.target.value, 10))
              }
            />
            <div className={styles.fieldInfo}>
              {formatTokenBudget(currentSettings.cgrag_token_budget)}
            </div>
            <ProgressBar
              current={currentSettings.cgrag_token_budget}
              max={32000}
              variant="accent"
            />
          </div>

          {/* Chunk Settings Grid */}
          <div className={styles.cgragChunkGrid}>
            <div className={styles.field}>
              <label className={styles.label}>
                CHUNK SIZE (tokens)
                {renderTooltip(
                  'Number of tokens per document chunk for CGRAG indexing. Larger chunks preserve context but reduce granularity.'
                )}
              </label>
              <Input
                type="number"
                min="128"
                max="2048"
                step="64"
                value={currentSettings.cgrag_chunk_size}
                onChange={(e) =>
                  handleFieldChange('cgrag_chunk_size', parseInt(e.target.value, 10))
                }
                className={styles.numericInput}
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                CHUNK OVERLAP (tokens)
                {renderTooltip(
                  'Overlapping tokens between adjacent chunks. Prevents context loss at chunk boundaries.'
                )}
              </label>
              <Input
                type="number"
                min="0"
                max="512"
                step="32"
                value={currentSettings.cgrag_chunk_overlap}
                onChange={(e) =>
                  handleFieldChange('cgrag_chunk_overlap', parseInt(e.target.value, 10))
                }
                error={validationErrors.cgrag_chunk_overlap}
                className={styles.numericInput}
              />
            </div>
          </div>

          {/* Index Directory */}
          <div className={styles.field}>
            <label className={styles.label}>
              CGRAG INDEX DIRECTORY
              {renderTooltip(
                'Directory path containing CGRAG FAISS indexes, relative to project root. Default: data/faiss_indexes'
              )}
            </label>
            <Input
              type="text"
              value={currentSettings.cgrag_index_directory}
              onChange={(e) =>
                handleFieldChange('cgrag_index_directory', e.target.value)
              }
              placeholder="data/faiss_indexes"
              className={styles.pathInput}
            />
          </div>
      </AsciiPanel>

      <Divider spacing="lg" />

      {/* Section 5: Benchmark & Web Search Configuration with ASCII Border */}
      <AsciiPanel title="BENCHMARK & WEB SEARCH CONFIGURATION">
          <p className={styles.sectionDescription}>
            Default settings for benchmark mode and web search integration.
          </p>

          {/* Benchmark Settings Grid */}
          <div className={styles.benchmarkGrid}>
            {/* Benchmark Max Tokens */}
            <div className={styles.field}>
              <label className={styles.label}>
                BENCHMARK MAX TOKENS
                {renderTooltip('Token limit per model in benchmark mode')}
              </label>
              <Input
                type="number"
                min="128"
                max="4096"
                step="128"
                value={currentSettings.benchmark_default_max_tokens}
                onChange={(e) =>
                  handleFieldChange(
                    'benchmark_default_max_tokens',
                    parseInt(e.target.value, 10)
                  )
                }
                className={styles.numericInput}
              />
            </div>

            {/* Benchmark Parallel Models */}
            <div className={styles.field}>
              <label className={styles.label}>
                PARALLEL MAX MODELS
                {renderTooltip(
                  'Maximum models to run simultaneously in parallel benchmark mode. Higher values increase VRAM usage.'
                )}
              </label>
              <Input
                type="number"
                min="1"
                max="10"
                value={currentSettings.benchmark_parallel_max_models}
                onChange={(e) =>
                  handleFieldChange(
                    'benchmark_parallel_max_models',
                    parseInt(e.target.value, 10)
                  )
                }
                error={validationErrors.benchmark_parallel_max_models}
                className={styles.numericInput}
              />
              {currentSettings.benchmark_parallel_max_models > 5 && (
                <div className={styles.warning}>Warning: High VRAM usage</div>
              )}
            </div>
          </div>

          {/* Web Search Settings Grid */}
          <div className={styles.webSearchGrid}>
            {/* WebSearch Max Results */}
            <div className={styles.field}>
              <label className={styles.label}>
                WEB SEARCH MAX RESULTS
                {renderTooltip('Maximum number of web search results to retrieve and process.')}
              </label>
              <Input
                type="number"
                min="1"
                max="20"
                value={currentSettings.websearch_max_results}
                onChange={(e) =>
                  handleFieldChange('websearch_max_results', parseInt(e.target.value, 10))
                }
                className={styles.numericInput}
              />
            </div>

            {/* WebSearch Timeout */}
            <div className={styles.field}>
              <label className={styles.label}>
                WEB SEARCH TIMEOUT (seconds)
                {renderTooltip(
                  'Maximum time in seconds to wait for web search results before timing out.'
                )}
              </label>
              <Input
                type="number"
                min="5"
                max="30"
                value={currentSettings.websearch_timeout_seconds}
                onChange={(e) =>
                  handleFieldChange(
                    'websearch_timeout_seconds',
                    parseInt(e.target.value, 10)
                  )
                }
                className={styles.numericInput}
              />
            </div>
          </div>
      </AsciiPanel>


      {/* Reset Confirmation Dialog */}
      {showResetDialog && (
        <div className={styles.dialog}>
          <AsciiPanel title="CONFIRM RESET">
            <div className={styles.dialogContent}>
              <p className={styles.dialogText}>
                Are you sure you want to reset all settings to defaults? This action
                cannot be undone.
              </p>
              <div className={styles.dialogActions}>
                <Button
                  variant="danger"
                  onClick={handleReset}
                  loading={resetMutation.isPending}
                >
                  {resetMutation.isPending ? 'RESETTING...' : 'CONFIRM RESET'}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setShowResetDialog(false)}
                  disabled={resetMutation.isPending}
                >
                  CANCEL
                </Button>
              </div>
            </div>
          </AsciiPanel>
        </div>
      )}

      {/* Restart Confirmation Modal */}
      {showRestartModal && (
        <div className={styles.modalOverlay} onClick={() => setShowRestartModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>CONFIRM SERVER RESTART</div>
            <div className={styles.modalBody}>
              This will restart all running model servers. Any active queries will be interrupted.
              <br /><br />
              Continue?
            </div>
            <div className={styles.modalActions}>
              <button
                onClick={() => setShowRestartModal(false)}
                className={styles.modalCancel}
              >
                CANCEL
              </button>
              <button
                onClick={async () => {
                  try {
                    await restartServersMutation.mutateAsync();
                    setShowRestartModal(false);
                    setRestartRequired(false); // Auto-clear restart warning
                  } catch (error) {
                    console.error('Failed to restart servers:', error);
                    // Keep modal open on error
                  }
                }}
                className={styles.modalConfirm}
                disabled={restartServersMutation.isPending}
              >
                {restartServersMutation.isPending ? 'RESTARTING...' : 'RESTART SERVERS'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
