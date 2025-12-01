/**
 * CreateInstanceModal - Form for creating new model instances.
 *
 * Provides a terminal-styled modal for creating instances with:
 * - Model selector dropdown (from available models)
 * - Display name input (required)
 * - System prompt textarea (optional, 4096 char limit)
 * - Preset selector for common system prompts
 * - Web search toggle
 * - Loading states during creation
 * - Error display with detailed messages
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { AsciiPanel } from '@/components/terminal/AsciiPanel/AsciiPanel';
import { Button } from '@/components/terminal/Button/Button';
import { useModelRegistry } from '@/hooks/useModelManagement';
import { useCreateInstance, useSystemPromptPresets } from '@/hooks/useInstances';
import type { CreateInstanceRequest, SystemPromptPreset } from '@/types/instances';
import type { DiscoveredModel } from '@/types/models';
import styles from './CreateInstanceModal.module.css';

export interface CreateInstanceModalProps {
  /** Callback to close modal */
  onClose: () => void;
  /** Callback after successful creation */
  onSuccess?: () => void;
  /** Pre-selected model ID (optional) */
  preSelectedModelId?: string;
}

export const CreateInstanceModal: React.FC<CreateInstanceModalProps> = ({
  onClose,
  onSuccess,
  preSelectedModelId,
}) => {
  // Form state
  const [modelId, setModelId] = useState(preSelectedModelId || '');
  const [displayName, setDisplayName] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  // Validation state
  const [modelError, setModelError] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);
  const [promptError, setPromptError] = useState<string | null>(null);

  // Data fetching
  const { data: registry } = useModelRegistry();
  const { data: presetsResponse } = useSystemPromptPresets();
  const createMutation = useCreateInstance();

  // Available models (enabled only)
  const availableModels = useMemo((): DiscoveredModel[] => {
    if (!registry?.models) return [];
    return Object.values(registry.models).filter(m => m.enabled);
  }, [registry]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Validate model selection
  const validateModel = useCallback((value: string): boolean => {
    if (!value) {
      setModelError('Model is required');
      return false;
    }
    setModelError(null);
    return true;
  }, []);

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

  // Handle model selection
  const handleModelChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    setModelId(value);
    validateModel(value);

    // Auto-generate display name if empty
    if (!displayName && value) {
      const model = availableModels.find(m => m.modelId === value);
      if (model) {
        setDisplayName(`${model.filename} Instance`);
      }
    }
  }, [validateModel, displayName, availableModels]);

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
    const modelValid = validateModel(modelId);
    const nameValid = validateName(displayName);
    const promptValid = validatePrompt(systemPrompt);

    if (!modelValid || !nameValid || !promptValid) {
      return;
    }

    // Build request
    const request: CreateInstanceRequest = {
      modelId,
      displayName: displayName.trim(),
      systemPrompt: systemPrompt.trim() || undefined,
      webSearchEnabled,
    };

    try {
      await createMutation.mutateAsync(request);
      onSuccess?.();
    } catch (error) {
      console.error('Failed to create instance:', error);
    }
  }, [modelId, displayName, systemPrompt, webSearchEnabled, validateModel, validateName, validatePrompt, createMutation, onSuccess]);

  // Handle overlay click
  const handleOverlayClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  }, [onClose]);

  // Character count for system prompt
  const promptCharCount = systemPrompt.length;
  const promptCharRemaining = 4096 - promptCharCount;

  return (
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div className={styles.modal}>
        <AsciiPanel title="CREATE INSTANCE" variant="default">
          <form onSubmit={handleSubmit} className={styles.form}>
            {/* Model Selector */}
            <div className={styles.formGroup}>
              <label className={styles.label}>
                BASE MODEL <span className={styles.required}>*</span>
              </label>
              <select
                className={`${styles.select} ${modelError ? styles.inputError : ''}`}
                value={modelId}
                onChange={handleModelChange}
                disabled={!!preSelectedModelId}
              >
                <option value="">Select a model...</option>
                {availableModels.map(model => (
                  <option key={model.modelId} value={model.modelId}>
                    {model.filename} ({model.assignedTier.toUpperCase()})
                  </option>
                ))}
              </select>
              {modelError && <span className={styles.errorText}>{modelError}</span>}
              {availableModels.length === 0 && (
                <span className={styles.hintText}>No models available. Enable models in Model Management first.</span>
              )}
            </div>

            {/* Display Name */}
            <div className={styles.formGroup}>
              <label className={styles.label}>
                DISPLAY NAME <span className={styles.required}>*</span>
              </label>
              <input
                type="text"
                className={`${styles.input} ${nameError ? styles.inputError : ''}`}
                value={displayName}
                onChange={handleNameChange}
                placeholder="e.g., Research Assistant"
                maxLength={64}
              />
              {nameError && <span className={styles.errorText}>{nameError}</span>}
            </div>

            {/* System Prompt Preset */}
            <div className={styles.formGroup}>
              <label className={styles.label}>SYSTEM PROMPT PRESET</label>
              <select
                className={styles.select}
                value={selectedPreset}
                onChange={handlePresetChange}
              >
                <option value="">Custom / None</option>
                {presetsResponse?.presets.map(preset => (
                  <option key={preset.id} value={preset.id}>
                    {preset.name} - {preset.description}
                  </option>
                ))}
              </select>
            </div>

            {/* System Prompt Textarea */}
            <div className={styles.formGroup}>
              <label className={styles.label}>
                SYSTEM PROMPT
                <span className={styles.charCount}>
                  {promptCharRemaining} chars remaining
                </span>
              </label>
              <textarea
                className={`${styles.textarea} ${promptError ? styles.inputError : ''}`}
                value={systemPrompt}
                onChange={handlePromptChange}
                placeholder="Optional system prompt for this instance..."
                rows={6}
                maxLength={4096}
              />
              {promptError && <span className={styles.errorText}>{promptError}</span>}
            </div>

            {/* Web Search Toggle */}
            <div className={styles.formGroup}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  className={styles.checkbox}
                  checked={webSearchEnabled}
                  onChange={handleWebSearchToggle}
                />
                <span className={styles.checkboxText}>ENABLE WEB SEARCH</span>
              </label>
              <span className={styles.hintText}>
                Enable SearXNG web search for this instance
              </span>
            </div>

            {/* Error Message */}
            {createMutation.isError && (
              <div className={styles.errorBanner}>
                <span className={styles.errorIcon}>!</span>
                <span className={styles.errorMessage}>
                  {createMutation.error instanceof Error
                    ? createMutation.error.message
                    : 'Failed to create instance'}
                </span>
              </div>
            )}

            {/* Success Message */}
            {createMutation.isSuccess && (
              <div className={styles.successBanner}>
                <span className={styles.successIcon}>✓</span>
                <span className={styles.successMessage}>Instance created successfully!</span>
              </div>
            )}

            {/* Actions */}
            <div className={styles.actions}>
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                disabled={createMutation.isPending}
              >
                CANCEL
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={createMutation.isPending || availableModels.length === 0}
              >
                {createMutation.isPending ? 'CREATING...' : 'CREATE INSTANCE'}
              </Button>
            </div>
          </form>
        </AsciiPanel>
      </div>
    </div>
  );
};

CreateInstanceModal.displayName = 'CreateInstanceModal';
