/**
 * EditInstanceModal - Form for editing existing model instances.
 *
 * Provides a terminal-styled modal for editing instances with:
 * - Display name input (pre-populated)
 * - System prompt textarea (pre-populated)
 * - Preset selector for common system prompts
 * - Web search toggle (pre-populated)
 * - Loading states during update
 * - Error display with detailed messages
 */

import React, { useState, useEffect, useCallback } from 'react';
import { AsciiPanel } from '@/components/terminal/AsciiPanel/AsciiPanel';
import { Button } from '@/components/terminal/Button/Button';
import { useUpdateInstance, useSystemPromptPresets } from '@/hooks/useInstances';
import type { InstanceConfig, UpdateInstanceRequest } from '@/types/instances';
import styles from './CreateInstanceModal.module.css'; // Reuse same styles

export interface EditInstanceModalProps {
  /** Instance to edit */
  instance: InstanceConfig;
  /** Model display name */
  modelDisplayName?: string;
  /** Callback to close modal */
  onClose: () => void;
  /** Callback after successful update */
  onSuccess?: () => void;
}

export const EditInstanceModal: React.FC<EditInstanceModalProps> = ({
  instance,
  modelDisplayName,
  onClose,
  onSuccess,
}) => {
  // Form state (pre-populated from instance)
  const [displayName, setDisplayName] = useState(instance.displayName);
  const [systemPrompt, setSystemPrompt] = useState(instance.systemPrompt || '');
  const [webSearchEnabled, setWebSearchEnabled] = useState(instance.webSearchEnabled);
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  // Validation state
  const [nameError, setNameError] = useState<string | null>(null);
  const [promptError, setPromptError] = useState<string | null>(null);

  // Data fetching
  const { data: presetsResponse } = useSystemPromptPresets();
  const updateMutation = useUpdateInstance();

  // Track if changes were made
  const hasChanges =
    displayName !== instance.displayName ||
    systemPrompt !== (instance.systemPrompt || '') ||
    webSearchEnabled !== instance.webSearchEnabled;

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
      onSuccess?.();
    } catch (error) {
      console.error('Failed to update instance:', error);
    }
  }, [displayName, systemPrompt, webSearchEnabled, instance, validateName, validatePrompt, updateMutation, onSuccess]);

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
        <AsciiPanel title="EDIT INSTANCE" variant="default">
          <form onSubmit={handleSubmit} className={styles.form}>
            {/* Instance Info (Read-only) */}
            <div className={styles.formGroup}>
              <label className={styles.label}>INSTANCE ID</label>
              <div className={styles.readOnlyValue}>{instance.instanceId}</div>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>BASE MODEL</label>
              <div className={styles.readOnlyValue}>
                {modelDisplayName || instance.modelId}
              </div>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>PORT</label>
              <div className={styles.readOnlyValue}>{instance.port}</div>
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
                <option value="">Custom / Keep Current</option>
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
            {updateMutation.isError && (
              <div className={styles.errorBanner}>
                <span className={styles.errorIcon}>!</span>
                <span className={styles.errorMessage}>
                  {updateMutation.error instanceof Error
                    ? updateMutation.error.message
                    : 'Failed to update instance'}
                </span>
              </div>
            )}

            {/* Success Message */}
            {updateMutation.isSuccess && (
              <div className={styles.successBanner}>
                <span className={styles.successIcon}>✓</span>
                <span className={styles.successMessage}>Instance updated successfully!</span>
              </div>
            )}

            {/* Actions */}
            <div className={styles.actions}>
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                disabled={updateMutation.isPending}
              >
                CANCEL
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={updateMutation.isPending || !hasChanges}
              >
                {updateMutation.isPending ? 'SAVING...' : 'SAVE CHANGES'}
              </Button>
            </div>
          </form>
        </AsciiPanel>
      </div>
    </div>
  );
};

EditInstanceModal.displayName = 'EditInstanceModal';
