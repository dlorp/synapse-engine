/**
 * ContextSelector Modal - CGRAG index picker for Code Chat.
 *
 * Provides a terminal-styled modal for selecting CGRAG contexts with:
 * - Radio button selection interface with ASCII indicators
 * - Context metadata display (chunk count, last indexed)
 * - "None" option for clearing context
 * - Refresh functionality for re-indexing
 * - Placeholder for creating new indexes
 */

import React, { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { AsciiPanel } from '@/components/terminal/AsciiPanel/AsciiPanel';
import { Button } from '@/components/terminal/Button/Button';
import { useContexts, useRefreshContext } from '@/hooks/useContexts';
import { CreateContextModal } from './CreateContextModal';
import styles from './ContextSelector.module.css';

export interface ContextSelectorProps {
  /** Currently selected context name */
  selectedContext: string | null;
  /** Callback when context selection changes */
  onSelect: (contextName: string | null) => void;
  /** Callback to close modal */
  onClose: () => void;
}

/**
 * Modal component for selecting CGRAG indexes.
 *
 * Displays available contexts with metadata, allows selection via
 * ASCII-style radio buttons, and provides actions for refreshing
 * or creating indexes.
 *
 * @example
 * const [showSelector, setShowSelector] = useState(false);
 * const [context, setContext] = useState<string | null>(null);
 *
 * {showSelector && (
 *   <ContextSelector
 *     selectedContext={context}
 *     onSelect={(name) => {
 *       setContext(name);
 *     }}
 *     onClose={() => setShowSelector(false)}
 *   />
 * )}
 */
export const ContextSelector: React.FC<ContextSelectorProps> = ({
  selectedContext,
  onSelect,
  onClose,
}) => {
  // Local selection state (committed on confirm)
  const [localSelection, setLocalSelection] = useState<string | null>(selectedContext);

  // CreateContextModal state
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Fetch contexts and refresh mutation
  const { data: contexts, isLoading, error } = useContexts();
  const refreshMutation = useRefreshContext();

  /**
   * Handle ESC key to close modal.
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  /**
   * Commit selection and close modal.
   */
  const handleConfirm = useCallback(() => {
    onSelect(localSelection);
    onClose();
  }, [localSelection, onSelect, onClose]);

  /**
   * Refresh the selected context's index.
   */
  const handleRefresh = useCallback(async () => {
    if (!localSelection) return;

    try {
      await refreshMutation.mutateAsync(localSelection);
    } catch (err) {
      console.error('Failed to refresh context:', err);
    }
  }, [localSelection, refreshMutation]);

  /**
   * Open CreateContextModal.
   */
  const handleCreateNew = useCallback(() => {
    setShowCreateModal(true);
  }, []);

  /**
   * Handle successful context creation.
   */
  const handleCreateSuccess = useCallback(() => {
    setShowCreateModal(false);
    // Context list will auto-refresh via TanStack Query cache invalidation
  }, []);

  /**
   * Format ISO date string to human-readable format.
   */
  const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  /**
   * Format number with thousand separators.
   */
  const formatNumber = (num: number): string => {
    return num.toLocaleString('en-US');
  };

  /**
   * Handle context item click.
   */
  const handleContextClick = useCallback((contextName: string) => {
    setLocalSelection(contextName);
  }, []);

  /**
   * Handle "None" option click.
   */
  const handleNoneClick = useCallback(() => {
    setLocalSelection(null);
  }, []);

  /**
   * Handle overlay click (close modal).
   */
  const handleOverlayClick = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      if (event.target === event.currentTarget) {
        onClose();
      }
    },
    [onClose]
  );

  return (
    <>
      <div
        className={styles.overlay}
        onClick={handleOverlayClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="context-selector-title"
      >
        <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
          <AsciiPanel title="CONTEXT SELECTION" variant="accent">
            <div className={styles.content}>
              {/* Header */}
              <div className={styles.header} id="context-selector-title">
                Available CGRAG Indexes:
              </div>

              {/* Loading State */}
              {isLoading && (
                <div className={styles.loading}>
                  <div className={styles.loadingSpinner}></div>
                  <span>Loading contexts...</span>
                </div>
              )}

              {/* Error State */}
              {error && (
                <div className={styles.error}>
                  <span className={styles.errorIcon}>[ERR]</span>
                  <span>Failed to load contexts: {error.message}</span>
                </div>
              )}

              {/* Context List */}
              {!isLoading && !error && (
                <div className={styles.contextList} role="radiogroup">
                  {contexts && contexts.length > 0 ? (
                    <>
                      {contexts.map((ctx) => (
                        <div
                          key={ctx.name}
                          className={clsx(
                            styles.contextItem,
                            ctx.name === localSelection && styles.selected
                          )}
                          onClick={() => handleContextClick(ctx.name)}
                          role="radio"
                          aria-checked={ctx.name === localSelection}
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleContextClick(ctx.name);
                            }
                          }}
                        >
                          <span className={styles.radio}>
                            {ctx.name === localSelection ? '(*)' : '( )'}
                          </span>
                          <div className={styles.contextInfo}>
                            <div className={styles.contextMain}>
                              <span className={styles.contextName}>{ctx.name}</span>
                              <span className={styles.chunkCount}>
                                [{formatNumber(ctx.chunkCount)} chunks]
                              </span>
                            </div>
                            <div className={styles.contextMeta}>
                              Indexed: {formatDate(ctx.lastIndexed)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </>
                  ) : (
                    <div className={styles.empty}>
                      <span>No CGRAG indexes available</span>
                    </div>
                  )}

                  {/* None Option */}
                  <div
                    className={clsx(
                      styles.contextItem,
                      styles.noneOption,
                      localSelection === null && styles.selected
                    )}
                    onClick={handleNoneClick}
                    role="radio"
                    aria-checked={localSelection === null}
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleNoneClick();
                      }
                    }}
                  >
                    <span className={styles.radio}>
                      {localSelection === null ? '(*)' : '( )'}
                    </span>
                    <span className={styles.contextName}>None (no context)</span>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className={styles.actions}>
                <Button onClick={handleConfirm} variant="primary" size="md">
                  CONFIRM
                </Button>
                <Button
                  onClick={handleRefresh}
                  variant="secondary"
                  size="md"
                  disabled={!localSelection || refreshMutation.isPending}
                >
                  {refreshMutation.isPending ? 'REFRESHING...' : 'REFRESH INDEX'}
                </Button>
                <Button onClick={handleCreateNew} variant="secondary" size="md">
                  CREATE NEW INDEX
                </Button>
              </div>
            </div>
          </AsciiPanel>
        </div>
      </div>

      {/* CreateContextModal */}
      {showCreateModal && (
        <CreateContextModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleCreateSuccess}
        />
      )}
    </>
  );
};
