import React, { useState, useCallback } from 'react';
import type {
  DiscoveredModel,
  GlobalRuntimeSettings,
  RuntimeSettingsUpdateRequest
} from '@/types/models';
import { PortSelector } from './PortSelector';
import styles from './ModelSettings.module.css';

export interface ModelSettingsProps {
  model: DiscoveredModel;
  allModels: DiscoveredModel[];
  portRange: [number, number];
  isServerRunning: boolean;
  globalDefaults: GlobalRuntimeSettings;
  onSave: (modelId: string, settings: RuntimeSettingsUpdateRequest) => Promise<void>;
  onPortChange: (modelId: string, port: number) => Promise<void>;
}

/**
 * ModelSettings - Expandable panel for per-model configuration
 *
 * Features:
 * - Port selector with conflict detection
 * - GPU layers slider + input
 * - Context size, threads, batch size inputs
 * - Shows global defaults when field is null
 * - Apply/Reset buttons
 * - Restart warning when server is running
 * - Terminal aesthetic with override indicators
 */
export const ModelSettings: React.FC<ModelSettingsProps> = ({
  model,
  allModels,
  portRange,
  isServerRunning,
  globalDefaults,
  onSave,
  onPortChange,
}) => {
  // Local form state (null = use global default)
  const [gpuLayers, setGpuLayers] = useState<number | null>(model.nGpuLayers);
  const [ctxSize, setCtxSize] = useState<number | null>(model.ctxSize);
  const [threads, setThreads] = useState<number | null>(model.nThreads);
  const [batchSize, setBatchSize] = useState<number | null>(model.batchSize);
  const [isSaving, setIsSaving] = useState(false);

  // Check if any changes have been made
  const hasChanges =
    gpuLayers !== model.nGpuLayers ||
    ctxSize !== model.ctxSize ||
    threads !== model.nThreads ||
    batchSize !== model.batchSize;

  /**
   * Apply settings changes
   */
  const handleSave = useCallback(async () => {
    if (!hasChanges) return;

    setIsSaving(true);
    try {
      await onSave(model.modelId, {
        nGpuLayers: gpuLayers,
        ctxSize: ctxSize,
        nThreads: threads,
        batchSize: batchSize,
      });
    } finally {
      setIsSaving(false);
    }
  }, [model.modelId, gpuLayers, ctxSize, threads, batchSize, hasChanges, onSave]);

  /**
   * Reset all fields to global defaults (null)
   */
  const handleReset = useCallback(() => {
    setGpuLayers(null);
    setCtxSize(null);
    setThreads(null);
    setBatchSize(null);
  }, []);

  /**
   * Get effective value (override or default)
   */
  const getEffectiveValue = (override: number | null, defaultValue: number): number => {
    return override ?? defaultValue;
  };

  /**
   * Check if field is using override
   */
  const isOverride = (value: number | null): boolean => {
    return value !== null;
  };

  return (
    <div className={styles.container}>
      <div className={styles.panel}>
        {/* Header */}
        <div className={styles.header}>
          <h3 className={styles.title}>
            MODEL CONFIGURATION: {model.family.toUpperCase()} {model.sizeParams}B
          </h3>
          {isServerRunning && (
            <div className={styles.warning}>
              ⚠ SERVER RUNNING - CHANGES REQUIRE RESTART
            </div>
          )}
        </div>

        {/* Settings Grid */}
        <div className={styles.grid}>
          {/* Port Selector */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>
              PORT ASSIGNMENT
              {model.port !== null && (
                <span className={styles.overrideBadge}>OVERRIDE</span>
              )}
            </label>
            <PortSelector
              model={model}
              allModels={allModels}
              portRange={portRange}
              isServerRunning={isServerRunning}
              onPortChange={onPortChange}
            />
          </div>

          {/* GPU Layers */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>
              GPU LAYERS
              {isOverride(gpuLayers) && (
                <span className={styles.overrideBadge}>OVERRIDE</span>
              )}
            </label>
            <div className={styles.fieldGroup}>
              <input
                type="range"
                min="0"
                max="99"
                value={getEffectiveValue(gpuLayers, globalDefaults.nGpuLayers)}
                onChange={(e) => setGpuLayers(parseInt(e.target.value, 10))}
                className={styles.slider}
                aria-label="GPU Layers"
              />
              <input
                type="number"
                min="0"
                max="99"
                value={getEffectiveValue(gpuLayers, globalDefaults.nGpuLayers)}
                onChange={(e) => setGpuLayers(parseInt(e.target.value, 10) || 0)}
                className={styles.numberInput}
                aria-label="GPU Layers Value"
              />
            </div>
            <div className={styles.fieldHint}>
              {isOverride(gpuLayers) ? (
                <span className={styles.overrideText}>
                  [{getEffectiveValue(gpuLayers, globalDefaults.nGpuLayers)}] (override)
                </span>
              ) : (
                <span className={styles.defaultText}>
                  [{globalDefaults.nGpuLayers}] (global default)
                </span>
              )}
            </div>
          </div>

          {/* Context Size */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>
              CONTEXT SIZE
              {isOverride(ctxSize) && (
                <span className={styles.overrideBadge}>OVERRIDE</span>
              )}
            </label>
            <input
              type="number"
              min="512"
              max="131072"
              step="512"
              value={getEffectiveValue(ctxSize, globalDefaults.ctxSize)}
              onChange={(e) => setCtxSize(parseInt(e.target.value, 10) || 512)}
              className={styles.input}
              aria-label="Context Size"
            />
            <div className={styles.fieldHint}>
              {isOverride(ctxSize) ? (
                <span className={styles.overrideText}>
                  [{getEffectiveValue(ctxSize, globalDefaults.ctxSize)}] (override)
                </span>
              ) : (
                <span className={styles.defaultText}>
                  [{globalDefaults.ctxSize}] (global default)
                </span>
              )}
            </div>
          </div>

          {/* Threads */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>
              THREADS
              {isOverride(threads) && (
                <span className={styles.overrideBadge}>OVERRIDE</span>
              )}
            </label>
            <input
              type="number"
              min="1"
              max="128"
              value={getEffectiveValue(threads, globalDefaults.nThreads)}
              onChange={(e) => setThreads(parseInt(e.target.value, 10) || 1)}
              className={styles.input}
              aria-label="Threads"
            />
            <div className={styles.fieldHint}>
              {isOverride(threads) ? (
                <span className={styles.overrideText}>
                  [{getEffectiveValue(threads, globalDefaults.nThreads)}] (override)
                </span>
              ) : (
                <span className={styles.defaultText}>
                  [{globalDefaults.nThreads}] (global default)
                </span>
              )}
            </div>
          </div>

          {/* Batch Size */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>
              BATCH SIZE
              {isOverride(batchSize) && (
                <span className={styles.overrideBadge}>OVERRIDE</span>
              )}
            </label>
            <input
              type="number"
              min="1"
              max="4096"
              value={getEffectiveValue(batchSize, globalDefaults.batchSize)}
              onChange={(e) => setBatchSize(parseInt(e.target.value, 10) || 1)}
              className={styles.input}
              aria-label="Batch Size"
            />
            <div className={styles.fieldHint}>
              {isOverride(batchSize) ? (
                <span className={styles.overrideText}>
                  [{getEffectiveValue(batchSize, globalDefaults.batchSize)}] (override)
                </span>
              ) : (
                <span className={styles.defaultText}>
                  [{globalDefaults.batchSize}] (global default)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className={styles.actions}>
          <button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            className={`${styles.button} ${styles.saveButton}`}
            aria-label="Apply Changes"
          >
            {isSaving ? 'APPLYING...' : 'APPLY CHANGES'}
          </button>
          <button
            onClick={handleReset}
            disabled={isSaving}
            className={`${styles.button} ${styles.resetButton}`}
            aria-label="Reset to Defaults"
          >
            RESET TO DEFAULTS
          </button>
        </div>
      </div>
    </div>
  );
};
