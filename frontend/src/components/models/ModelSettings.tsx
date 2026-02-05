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
 * Pad ASCII line to fixed width for terminal aesthetic
 * Ensures consistent frame width across all screen sizes (150 chars)
 */
const padLine = (content: string, width: number = 150): string => {
  if (content.length >= width) {
    return content.substring(0, width);
  }
  return content.padEnd(width, '─');
};

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
 * - Responsive ASCII borders (150-char width)
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
          <div className={styles.headerBorder}>
            {padLine('─ MODEL CONFIGURATION ')}
          </div>
          <div className={styles.headerContent}>
            <span className={styles.modelInfo}>
              {model.family.toUpperCase()} {model.sizeParams}B
            </span>
            {isServerRunning && (
              <div className={styles.warning}>
                <span className={styles.warningIcon}>⚠</span>
                <span>SERVER ACTIVE - RESTART REQUIRED</span>
              </div>
            )}
          </div>
        </div>

        {/* Port Assignment Section */}
        <div className={styles.section}>
          <div className={styles.sectionBorder}>
            {padLine('─ PORT ASSIGNMENT ')}
          </div>
          <div className={styles.sectionContent}>
            <div className={styles.portRow}>
              <span className={styles.portLabel}>ASSIGNED PORT:</span>
              <PortSelector
                model={model}
                allModels={allModels}
                portRange={portRange}
                isServerRunning={isServerRunning}
                onPortChange={onPortChange}
              />
              {model.port !== null && (
                <span className={styles.overrideBadge}>OVERRIDE</span>
              )}
            </div>
          </div>
        </div>

        {/* Runtime Settings Grid */}
        <div className={styles.section}>
          <div className={styles.sectionBorder}>
            {padLine('─ RUNTIME SETTINGS ')}
          </div>
          <div className={styles.runtimeGrid}>
            {/* GPU Layers */}
            <div className={styles.runtimeField}>
              <div className={styles.fieldHeader}>
                <span className={styles.fieldLabel}>GPU LAYERS</span>
                {isOverride(gpuLayers) && (
                  <span className={styles.overrideBadge}></span>
                )}
              </div>
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
                    OVERRIDE → {getEffectiveValue(gpuLayers, globalDefaults.nGpuLayers)}
                  </span>
                ) : (
                  <span className={styles.defaultText}>
                    DEFAULT → {globalDefaults.nGpuLayers}
                  </span>
                )}
              </div>
            </div>

            {/* Vertical Separator */}
            <div className={styles.verticalSeparator}>│</div>

            {/* Context Size */}
            <div className={styles.runtimeField}>
              <div className={styles.fieldHeader}>
                <span className={styles.fieldLabel}>CTX SIZE</span>
                {isOverride(ctxSize) && (
                  <span className={styles.overrideBadge}></span>
                )}
              </div>
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
                    OVERRIDE → {getEffectiveValue(ctxSize, globalDefaults.ctxSize)}
                  </span>
                ) : (
                  <span className={styles.defaultText}>
                    DEFAULT → {globalDefaults.ctxSize}
                  </span>
                )}
              </div>
            </div>

            {/* Threads */}
            <div className={styles.runtimeField}>
              <div className={styles.fieldHeader}>
                <span className={styles.fieldLabel}>THREADS</span>
                {isOverride(threads) && (
                  <span className={styles.overrideBadge}></span>
                )}
              </div>
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
                    OVERRIDE → {getEffectiveValue(threads, globalDefaults.nThreads)}
                  </span>
                ) : (
                  <span className={styles.defaultText}>
                    DEFAULT → {globalDefaults.nThreads}
                  </span>
                )}
              </div>
            </div>

            {/* Vertical Separator */}
            <div className={styles.verticalSeparator}>│</div>

            {/* Batch Size */}
            <div className={styles.runtimeField}>
              <div className={styles.fieldHeader}>
                <span className={styles.fieldLabel}>BATCH SIZE</span>
                {isOverride(batchSize) && (
                  <span className={styles.overrideBadge}></span>
                )}
              </div>
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
                    OVERRIDE → {getEffectiveValue(batchSize, globalDefaults.batchSize)}
                  </span>
                ) : (
                  <span className={styles.defaultText}>
                    DEFAULT → {globalDefaults.batchSize}
                  </span>
                )}
              </div>
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
            <span className={styles.buttonIcon}>●</span>
            {isSaving ? 'APPLYING...' : 'APPLY CHANGES'}
          </button>
          <button
            onClick={handleReset}
            disabled={isSaving}
            className={`${styles.button} ${styles.resetButton}`}
            aria-label="Reset to Defaults"
          >
            <span className={styles.buttonIcon}>○</span>
            RESET TO DEFAULTS
          </button>
        </div>
      </div>
    </div>
  );
};
