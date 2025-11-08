import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Panel, Input, Button, Divider, ProgressBar } from '@/components/terminal';
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

  // Track if port range changed
  const portRangeChanged =
    portRangeStart !== (registry?.portRange?.[0] || 8080) ||
    portRangeEnd !== (registry?.portRange?.[1] || 8099);

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

      {/* Tooltip Toggle */}
      <div className={styles.tooltipToggle}>
        <input
          type="checkbox"
          id="tooltip_toggle"
          checked={showTooltips}
          onChange={(e) => setShowTooltips(e.target.checked)}
          className={styles.checkbox}
        />
        <label htmlFor="tooltip_toggle" className={styles.checkboxLabel}>
          Show Help Tooltips ⓘ
        </label>
      </div>

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

      {/* Section 1: Port Configuration */}
      <Panel title="PORT CONFIGURATION" variant="default">
        <div className={`${styles.section} ${styles.systemConfig}`}>
          <p className={styles.sectionDescription}>
            Configure the port range for llama.cpp model servers. Individual models can be
            assigned specific ports in Model Management.
          </p>

          <div className={styles.portRangeGrid}>
            <div className={styles.field}>
              <label className={styles.label}>
                Port Range Start
                <span className={styles.required}>*</span>
                <span className={styles.hint}>Minimum: 1024</span>
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
                Port Range End
                <span className={styles.required}>*</span>
                <span className={styles.hint}>Maximum: 65535</span>
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

          <div className={styles.portSummary}>
            <span className={styles.portLabel}>Available Ports:</span>
            <span className={styles.portValue}>
              {portRangeEnd - portRangeStart + 1} ports ({portRangeStart}-{portRangeEnd})
            </span>
            {portRangeStart >= portRangeEnd && (
              <span className={styles.errorText}> ⚠ Start port must be less than end port</span>
            )}
          </div>

          {assignedPorts.length > 0 && (
            <div className={styles.portSummary}>
              <span className={styles.portLabel}>Assigned Ports:</span>
              <span className={styles.portValue}>
                {assignedPorts.length} in use (
                {assignedPorts.sort((a, b) => a - b).join(', ')})
              </span>
            </div>
          )}
        </div>
      </Panel>

      <Divider spacing="lg" />

      {/* Section 2: Global Model Runtime Defaults */}
      <Panel title="GLOBAL MODEL RUNTIME DEFAULTS" variant="default">
        <div className={`${styles.section} ${styles.globalDefaults}`}>
          <p className={styles.sectionDescription}>
            Default settings for all models. Individual models can override these in Model
            Management.
          </p>

          <div className={styles.infoBox}>
            ℹ These settings apply to all models unless overridden. To configure per-model
            settings, go to Model Management → CONFIGURE button.
          </div>

          {/* VRAM Estimate Display */}
          {vramEstimate?.success && (
            <div className={styles.vramEstimate}>
              <div className={styles.vramLabel}>ESTIMATED VRAM:</div>
              <div className={styles.vramValue}>
                {vramEstimate.vram_gb.toFixed(2)} GB
              </div>
              <div className={styles.vramDetails}>
                (Q4_K_M, 8B model, {currentSettings.n_gpu_layers} GPU layers)
              </div>
            </div>
          )}

          {/* GPU Layers */}
          <div className={styles.field}>
            <div className={styles.fieldHeader}>
              <label className={styles.label}>
                GPU Layers (n_gpu_layers)
                {renderTooltip(
                  'Number of model layers offloaded to GPU. Higher = more VRAM usage but faster inference. Use 99 for max GPU offload.'
                )}
              </label>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleMaxGPUOffload}
                className={styles.presetButton}
              >
                Max GPU Offload
              </Button>
            </div>
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
            <div className={styles.currentValue}>
              Current: {currentSettings.n_gpu_layers}
            </div>
          </div>

          {/* Context Size */}
          <div className={styles.field}>
            <label className={styles.label}>
              Context Size (ctx_size)
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
          </div>

          {/* Threads */}
          <div className={styles.field}>
            <label className={styles.label}>
              CPU Threads
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
          </div>

          {/* Batch Size */}
          <div className={styles.field}>
            <label className={styles.label}>
              Batch Size
              {renderTooltip(
                'Number of tokens processed in parallel. Higher values improve throughput but increase VRAM usage.'
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
            />
          </div>

          {/* Micro Batch Size */}
          <div className={styles.field}>
            <label className={styles.label}>
              Micro Batch Size (ubatch_size)
              {renderTooltip(
                'Internal batch size for processing. Must be ≤ batch_size. Lower values reduce VRAM usage.'
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
            />
          </div>

          {/* Flash Attention */}
          <div className={styles.checkboxField}>
            <input
              type="checkbox"
              id="flash_attn"
              checked={currentSettings.flash_attn}
              onChange={(e) => handleFieldChange('flash_attn', e.target.checked)}
              className={styles.checkbox}
            />
            <label htmlFor="flash_attn" className={styles.checkboxLabel}>
              Enable Flash Attention (GPU only)
              {renderTooltip(
                'Optimized attention mechanism for GPUs. Reduces VRAM and improves speed on compatible hardware.'
              )}
            </label>
          </div>

          {/* No Memory Mapping */}
          <div className={styles.checkboxField}>
            <input
              type="checkbox"
              id="no_mmap"
              checked={currentSettings.no_mmap}
              onChange={(e) => handleFieldChange('no_mmap', e.target.checked)}
              className={styles.checkbox}
            />
            <label htmlFor="no_mmap" className={styles.checkboxLabel}>
              Disable Memory Mapping (recommended for GPU)
              {renderTooltip(
                'Disables memory-mapped model loading. Recommended for GPU inference to avoid slowdowns.'
              )}
            </label>
          </div>
        </div>
      </Panel>

      <Divider spacing="lg" />

      {/* Section 3: Embeddings Configuration */}
      <Panel title="EMBEDDING CONFIGURATION" variant="default">
        <div className={`${styles.section} ${styles.serviceConfig}`}>
          <p className={styles.sectionDescription}>
            Configuration for HuggingFace sentence transformer models used in CGRAG retrieval.
          </p>
          {/* Embedding Model */}
          <div className={styles.field}>
            <label className={styles.label}>
              Embedding Model
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

          {/* Embedding Cache Path */}
          <div className={styles.field}>
            <div className={styles.checkboxField}>
              <input
                type="checkbox"
                id="use_default_cache"
                checked={useDefaultCache}
                onChange={(e) => setUseDefaultCache(e.target.checked)}
                className={styles.checkbox}
              />
              <label htmlFor="use_default_cache" className={styles.checkboxLabel}>
                Use default cache location (~/.cache/huggingface)
                {renderTooltip(
                  'Store HuggingFace models in default cache directory. Uncheck to specify custom location.'
                )}
              </label>
            </div>
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

          {/* Embedding Dimension */}
          <div className={styles.field}>
            <label className={styles.label}>
              Embedding Dimension
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
            />
          </div>
        </div>
      </Panel>

      <Divider spacing="lg" />

      {/* Section 4: CGRAG Configuration */}
      <Panel title="CGRAG CONFIGURATION" variant="default">
        <div className={`${styles.section} ${styles.serviceConfig}`}>
          <p className={styles.sectionDescription}>
            Contextually-Guided Retrieval Augmented Generation settings for semantic search and
            context retrieval.
          </p>
          {/* Token Budget */}
          <div className={styles.field}>
            <label className={styles.label}>
              Token Budget: {formatTokenBudget(currentSettings.cgrag_token_budget)}
              {renderTooltip(
                'Maximum tokens allocated for CGRAG context retrieval. Higher values provide more context but reduce available tokens for generation.'
              )}
            </label>
            <div className={styles.sliderGroup}>
              <input
                type="range"
                min="1000"
                max="32000"
                step="1000"
                value={currentSettings.cgrag_token_budget}
                onChange={(e) =>
                  handleFieldChange('cgrag_token_budget', parseInt(e.target.value, 10))
                }
                className={styles.slider}
              />
              <div className={styles.sliderValue}>
                {currentSettings.cgrag_token_budget}
              </div>
            </div>
            <ProgressBar
              current={currentSettings.cgrag_token_budget}
              max={32000}
              variant="accent"
            />
          </div>

          {/* Minimum Relevance */}
          <div className={styles.field}>
            <label className={styles.label}>
              Minimum Relevance: {formatRelevance(currentSettings.cgrag_min_relevance)}
              {renderTooltip(
                'Minimum similarity threshold for CGRAG results. Higher values return only highly relevant context.'
              )}
            </label>
            <div className={styles.sliderGroup}>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={currentSettings.cgrag_min_relevance}
                onChange={(e) =>
                  handleFieldChange('cgrag_min_relevance', parseFloat(e.target.value))
                }
                className={styles.slider}
              />
              <div className={styles.sliderValue}>
                {formatRelevance(currentSettings.cgrag_min_relevance)}
              </div>
            </div>
            <ProgressBar
              current={currentSettings.cgrag_min_relevance * 100}
              max={100}
              variant="default"
            />
          </div>

          {/* Chunk Size */}
          <div className={styles.field}>
            <label className={styles.label}>
              Chunk Size (tokens)
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
            />
          </div>

          {/* Chunk Overlap */}
          <div className={styles.field}>
            <label className={styles.label}>
              Chunk Overlap (tokens)
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
            />
          </div>

          {/* Max Results */}
          <div className={styles.field}>
            <label className={styles.label}>
              Max Results
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
            />
          </div>

          {/* Index Directory */}
          <div className={styles.field}>
            <label className={styles.label}>
              CGRAG Index Directory
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
        </div>
      </Panel>

      <Divider spacing="lg" />

      {/* Section 5: Benchmark & Search Configuration */}
      <Panel title="BENCHMARK & WEB SEARCH CONFIGURATION" variant="default">
        <div className={`${styles.section} ${styles.serviceConfig}`}>
          <p className={styles.sectionDescription}>
            Default settings for benchmark mode and web search integration.
          </p>
          {/* Benchmark Max Tokens */}
          <div className={styles.field}>
            <label className={styles.label}>
              Benchmark Default Max Tokens
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
            />
          </div>

          {/* Benchmark Parallel Models */}
          <div className={styles.field}>
            <label className={styles.label}>
              Benchmark Parallel Max Models
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
            />
            {currentSettings.benchmark_parallel_max_models > 5 && (
              <div className={styles.warning}>Warning: High VRAM usage</div>
            )}
          </div>

          {/* WebSearch Max Results */}
          <div className={styles.field}>
            <label className={styles.label}>
              Web Search Max Results
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
            />
          </div>

          {/* WebSearch Timeout */}
          <div className={styles.field}>
            <label className={styles.label}>
              Web Search Timeout (seconds)
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
            />
          </div>
        </div>
      </Panel>

      {/* Actions Panel */}
      <div className={styles.actions}>
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
          {updateMutation.isPending ? 'SAVING...' : 'SAVE SETTINGS'}
        </Button>
        <Button
          variant="secondary"
          onClick={handleDiscard}
          disabled={!hasChanges || updateMutation.isPending}
        >
          DISCARD CHANGES
        </Button>
        <Button
          variant="danger"
          onClick={() => setShowResetDialog(true)}
          disabled={resetMutation.isPending}
        >
          RESET TO DEFAULTS
        </Button>
      </div>

      {/* Reset Confirmation Dialog */}
      {showResetDialog && (
        <div className={styles.dialog}>
          <Panel title="CONFIRM RESET" variant="default">
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
          </Panel>
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
