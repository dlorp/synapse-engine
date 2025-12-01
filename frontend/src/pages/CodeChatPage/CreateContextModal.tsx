/**
 * CreateContextModal - Form for creating new CGRAG indexes.
 *
 * Provides a terminal-styled modal for creating CGRAG contexts with:
 * - Name validation (alphanumeric + hyphens only)
 * - Source path selection via WorkspaceSelector
 * - Optional description field
 * - Loading states during index creation
 * - Error display with detailed messages
 */

import React, { useState, useEffect, useCallback } from 'react';
import { AsciiPanel } from '@/components/terminal/AsciiPanel/AsciiPanel';
import { Button } from '@/components/terminal/Button/Button';
import { useCreateContext } from '@/hooks/useContexts';
import { WorkspaceSelector } from './WorkspaceSelector';
import styles from './CreateContextModal.module.css';

export interface CreateContextModalProps {
  /** Callback to close modal */
  onClose: () => void;
  /** Callback after successful creation */
  onSuccess?: () => void;
}

/**
 * Modal component for creating new CGRAG indexes.
 *
 * Features:
 * - Name input with validation (alphanumeric + hyphens, 1-64 chars)
 * - Source path selection using WorkspaceSelector modal
 * - Optional description textarea
 * - Real-time validation feedback
 * - Loading state during index creation
 * - Error display for API failures
 * - ESC key to close
 *
 * @example
 * const [showCreateModal, setShowCreateModal] = useState(false);
 *
 * {showCreateModal && (
 *   <CreateContextModal
 *     onClose={() => setShowCreateModal(false)}
 *     onSuccess={() => {
 *       setShowCreateModal(false);
 *       // Contexts list will auto-refresh via TanStack Query cache invalidation
 *     }}
 *   />
 * )}
 */
export const CreateContextModal: React.FC<CreateContextModalProps> = ({
  onClose,
  onSuccess,
}) => {
  // Form state
  const [name, setName] = useState('');
  const [sourcePath, setSourcePath] = useState('');
  const [description, setDescription] = useState('');

  // Validation state
  const [nameError, setNameError] = useState<string | null>(null);
  const [pathError, setPathError] = useState<string | null>(null);

  // WorkspaceSelector state
  const [showWorkspaceSelector, setShowWorkspaceSelector] = useState(false);

  // Create context mutation
  const createMutation = useCreateContext();

  /**
   * Handle ESC key to close modal.
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !showWorkspaceSelector) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, showWorkspaceSelector]);

  /**
   * Validate context name.
   * Rules: 1-64 characters, alphanumeric + hyphens only
   */
  const validateName = useCallback((value: string): boolean => {
    if (!value) {
      setNameError('Name is required');
      return false;
    }

    if (value.length < 1 || value.length > 64) {
      setNameError('Name must be 1-64 characters');
      return false;
    }

    if (!/^[a-zA-Z0-9-]+$/.test(value)) {
      setNameError('Name can only contain letters, numbers, and hyphens');
      return false;
    }

    setNameError(null);
    return true;
  }, []);

  /**
   * Validate source path.
   */
  const validatePath = useCallback((value: string): boolean => {
    if (!value) {
      setPathError('Source path is required');
      return false;
    }

    setPathError(null);
    return true;
  }, []);

  /**
   * Handle name input change.
   */
  const handleNameChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      setName(value);
      validateName(value);
    },
    [validateName]
  );

  /**
   * Handle source path selection from WorkspaceSelector.
   */
  const handlePathSelect = useCallback(
    (path: string) => {
      setSourcePath(path);
      validatePath(path);
      setShowWorkspaceSelector(false);
    },
    [validatePath]
  );

  /**
   * Handle description change.
   */
  const handleDescriptionChange = useCallback(
    (event: React.ChangeEvent<HTMLTextAreaElement>) => {
      setDescription(event.target.value);
    },
    []
  );

  /**
   * Handle form submission.
   */
  const handleSubmit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();

      // Validate all fields
      const nameValid = validateName(name);
      const pathValid = validatePath(sourcePath);

      if (!nameValid || !pathValid) {
        return;
      }

      // Submit to API
      try {
        await createMutation.mutateAsync({
          name,
          sourcePath,
          embeddingModel: 'all-MiniLM-L6-v2', // Default model
        });

        // Success - call onSuccess callback
        if (onSuccess) {
          onSuccess();
        }
      } catch (error) {
        // Error is handled by mutation error state
        console.error('Failed to create context:', error);
      }
    },
    [name, sourcePath, validateName, validatePath, createMutation, onSuccess]
  );

  /**
   * Handle overlay click (close modal).
   */
  const handleOverlayClick = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      if (event.target === event.currentTarget && !showWorkspaceSelector) {
        onClose();
      }
    },
    [onClose, showWorkspaceSelector]
  );

  /**
   * Handle modal content click (prevent overlay close).
   */
  const handleModalClick = useCallback((event: React.MouseEvent) => {
    event.stopPropagation();
  }, []);

  return (
    <>
      <div
        className={styles.overlay}
        onClick={handleOverlayClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-context-title"
      >
        <div className={styles.modal} onClick={handleModalClick}>
          <AsciiPanel title="CREATE NEW CGRAG INDEX" variant="accent">
            <form className={styles.form} onSubmit={handleSubmit}>
              {/* Name Field */}
              <div className={styles.formGroup}>
                <label htmlFor="context-name" className={styles.label}>
                  NAME:
                </label>
                <input
                  id="context-name"
                  type="text"
                  value={name}
                  onChange={handleNameChange}
                  placeholder="my-project"
                  className={styles.input}
                  disabled={createMutation.isPending}
                  aria-invalid={!!nameError}
                  aria-describedby={nameError ? 'name-error' : undefined}
                  autoFocus
                />
                {nameError && (
                  <div id="name-error" className={styles.error} role="alert">
                    <span className={styles.errorIcon}>[ERR]</span>
                    <span>{nameError}</span>
                  </div>
                )}
                <div className={styles.hint}>
                  Alphanumeric + hyphens only (1-64 chars)
                </div>
              </div>

              {/* Source Path Field */}
              <div className={styles.formGroup}>
                <label htmlFor="source-path" className={styles.label}>
                  SOURCE PATH:
                </label>
                <div className={styles.pathInputGroup}>
                  <input
                    id="source-path"
                    type="text"
                    value={sourcePath}
                    readOnly
                    placeholder="/workspace/my-project"
                    className={styles.input}
                    disabled={createMutation.isPending}
                    aria-invalid={!!pathError}
                    aria-describedby={pathError ? 'path-error' : undefined}
                  />
                  <Button
                    type="button"
                    onClick={() => setShowWorkspaceSelector(true)}
                    variant="secondary"
                    size="md"
                    disabled={createMutation.isPending}
                    className={styles.browseButton}
                  >
                    BROWSE...
                  </Button>
                </div>
                {pathError && (
                  <div id="path-error" className={styles.error} role="alert">
                    <span className={styles.errorIcon}>[ERR]</span>
                    <span>{pathError}</span>
                  </div>
                )}
                <div className={styles.hint}>
                  Directory containing code files to index
                </div>
              </div>

              {/* Description Field (Optional) */}
              <div className={styles.formGroup}>
                <label htmlFor="description" className={styles.label}>
                  DESCRIPTION: <span className={styles.optional}>(optional)</span>
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={handleDescriptionChange}
                  placeholder="Python project for data analysis..."
                  className={styles.textarea}
                  disabled={createMutation.isPending}
                  rows={3}
                />
              </div>

              {/* API Error Display */}
              {createMutation.isError && (
                <div className={styles.apiError} role="alert">
                  <div className={styles.apiErrorHeader}>
                    <span className={styles.errorIcon}>[API ERROR]</span>
                  </div>
                  <div className={styles.apiErrorMessage}>
                    {createMutation.error instanceof Error
                      ? createMutation.error.message
                      : 'Failed to create context. Please try again.'}
                  </div>
                </div>
              )}

              {/* Success Display */}
              {createMutation.isSuccess && (
                <div className={styles.success} role="status">
                  <span className={styles.successIcon}>[OK]</span>
                  <span>Context created successfully! Indexed {createMutation.data?.chunkCount ?? 0} chunks.</span>
                </div>
              )}

              {/* Action Buttons */}
              <div className={styles.actions}>
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  disabled={createMutation.isPending || !!nameError || !!pathError}
                >
                  {createMutation.isPending ? 'CREATING INDEX...' : 'CREATE'}
                </Button>
                <Button
                  type="button"
                  onClick={onClose}
                  variant="ghost"
                  size="md"
                  disabled={createMutation.isPending}
                >
                  CANCEL
                </Button>
              </div>
            </form>
          </AsciiPanel>
        </div>
      </div>

      {/* Nested WorkspaceSelector Modal */}
      {showWorkspaceSelector && (
        <WorkspaceSelector
          currentWorkspace={sourcePath}
          onSelect={handlePathSelect}
          onClose={() => setShowWorkspaceSelector(false)}
        />
      )}
    </>
  );
};
