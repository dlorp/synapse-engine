/**
 * InstanceCard - Compact Instance Status Card with Actions
 *
 * Displays instance info (name, model, port, status) with:
 * - Start/Stop button with loading state
 * - Edit button to open modal
 * - Delete button with confirmation
 * - Status indicator (color-coded)
 * - Collapsible details showing system prompt preview
 *
 * Design follows ModelCard patterns but with instance-specific actions.
 */

import React, { useState, useCallback } from 'react';
import type { InstanceConfig } from '@/types/instances';
import { useStartInstance, useStopInstance, useDeleteInstance } from '@/hooks/useInstances';
import styles from './InstanceCard.module.css';

export interface InstanceCardProps {
  instance: InstanceConfig;
  modelDisplayName?: string;
  onEdit?: (instance: InstanceConfig) => void;
}

export const InstanceCard: React.FC<InstanceCardProps> = React.memo(({
  instance,
  modelDisplayName,
  onEdit,
}) => {
  // Details expansion state
  const [detailsExpanded, setDetailsExpanded] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  // Mutations
  const startMutation = useStartInstance();
  const stopMutation = useStopInstance();
  const deleteMutation = useDeleteInstance();

  // Derived state
  const isRunning = instance.status === 'active';
  const isLoading = instance.status === 'starting' || instance.status === 'stopping';
  const isMutating = startMutation.isPending || stopMutation.isPending || deleteMutation.isPending;

  // Handlers
  const handleToggleDetails = useCallback(() => {
    setDetailsExpanded(prev => !prev);
  }, []);

  const handleStartStop = useCallback(async () => {
    if (isRunning) {
      await stopMutation.mutateAsync(instance.instanceId);
    } else {
      await startMutation.mutateAsync(instance.instanceId);
    }
  }, [isRunning, instance.instanceId, startMutation, stopMutation]);

  const handleEdit = useCallback(() => {
    onEdit?.(instance);
  }, [instance, onEdit]);

  const handleDelete = useCallback(async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      // Auto-reset confirmation after 3 seconds
      setTimeout(() => setConfirmDelete(false), 3000);
      return;
    }

    await deleteMutation.mutateAsync(instance.instanceId);
    setConfirmDelete(false);
  }, [confirmDelete, instance.instanceId, deleteMutation]);

  // Truncate system prompt for preview
  const systemPromptPreview = instance.systemPrompt
    ? instance.systemPrompt.length > 100
      ? instance.systemPrompt.substring(0, 100) + '...'
      : instance.systemPrompt
    : 'No system prompt configured';

  return (
    <div
      className={styles.instanceCard}
      data-status={instance.status}
      data-running={isRunning}
    >
      {/* Header Row */}
      <div className={styles.header}>
        <h3 className={styles.displayName} title={instance.displayName}>
          {instance.displayName}
        </h3>

        <div className={styles.instanceId}>
          {instance.instanceId}
        </div>

        <div className={styles.statusSection}>
          <span className={`${styles.statusDot} ${styles[`status${instance.status.charAt(0).toUpperCase() + instance.status.slice(1)}`]}`}>
            {isRunning ? '●' : isLoading ? '◐' : '○'}
          </span>
          <span className={styles.statusLabel}>
            {instance.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Info Row */}
      <div className={styles.infoRow}>
        <span className={styles.infoItem}>
          <span className={styles.infoLabel}>PORT:</span>
          <span className={styles.infoValue}>{instance.port}</span>
        </span>
        <span className={styles.infoDivider}>│</span>
        <span className={styles.infoItem}>
          <span className={styles.infoLabel}>MODEL:</span>
          <span className={styles.infoValue}>{modelDisplayName || instance.modelId}</span>
        </span>
        {instance.webSearchEnabled && (
          <>
            <span className={styles.infoDivider}>│</span>
            <span className={styles.webSearchBadge}>WEB</span>
          </>
        )}
      </div>

      {/* Actions Row */}
      <div className={styles.actions}>
        <button
          className={`${styles.actionButton} ${styles.detailsButton}`}
          onClick={handleToggleDetails}
          aria-expanded={detailsExpanded}
          title={detailsExpanded ? 'Hide details' : 'Show details'}
        >
          <span className={styles.buttonIcon}>{detailsExpanded ? '▲' : '▼'}</span>
          <span className={styles.buttonLabel}>DETAILS</span>
        </button>

        <button
          className={`${styles.actionButton} ${isRunning ? styles.stopButton : styles.startButton}`}
          onClick={handleStartStop}
          disabled={isLoading || isMutating}
          title={isRunning ? 'Stop instance' : 'Start instance'}
        >
          <span className={styles.buttonIcon}>{isRunning ? '■' : '▶'}</span>
          <span className={styles.buttonLabel}>
            {isMutating ? 'WAIT...' : isRunning ? 'STOP' : 'START'}
          </span>
        </button>

        <button
          className={`${styles.actionButton} ${styles.editButton}`}
          onClick={handleEdit}
          disabled={isMutating}
          title="Edit instance configuration"
        >
          <span className={styles.buttonIcon}>✎</span>
          <span className={styles.buttonLabel}>EDIT</span>
        </button>

        <button
          className={`${styles.actionButton} ${confirmDelete ? styles.confirmDeleteButton : styles.deleteButton}`}
          onClick={handleDelete}
          disabled={isRunning || isMutating}
          title={isRunning ? 'Stop instance before deleting' : confirmDelete ? 'Click again to confirm' : 'Delete instance'}
        >
          <span className={styles.buttonIcon}>{confirmDelete ? '!' : '×'}</span>
          <span className={styles.buttonLabel}>
            {confirmDelete ? 'CONFIRM?' : 'DELETE'}
          </span>
        </button>
      </div>

      {/* Expandable Details Section */}
      {detailsExpanded && (
        <div className={styles.detailsSection}>
          <div className={styles.detailGroup}>
            <span className={styles.detailLabel}>SYSTEM PROMPT:</span>
            <div className={styles.systemPromptPreview}>
              {systemPromptPreview}
            </div>
          </div>

          <div className={styles.detailGroup}>
            <span className={styles.detailLabel}>WEB SEARCH:</span>
            <span className={styles.detailValue}>
              {instance.webSearchEnabled ? 'ENABLED' : 'DISABLED'}
            </span>
          </div>

          <div className={styles.detailGroup}>
            <span className={styles.detailLabel}>CREATED:</span>
            <span className={styles.detailValue}>
              {new Date(instance.createdAt).toLocaleString()}
            </span>
          </div>

          {instance.updatedAt && (
            <div className={styles.detailGroup}>
              <span className={styles.detailLabel}>UPDATED:</span>
              <span className={styles.detailValue}>
                {new Date(instance.updatedAt).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  return (
    prevProps.instance.instanceId === nextProps.instance.instanceId &&
    prevProps.instance.status === nextProps.instance.status &&
    prevProps.instance.displayName === nextProps.instance.displayName &&
    prevProps.instance.systemPrompt === nextProps.instance.systemPrompt &&
    prevProps.instance.webSearchEnabled === nextProps.instance.webSearchEnabled &&
    prevProps.modelDisplayName === nextProps.modelDisplayName
  );
});

InstanceCard.displayName = 'InstanceCard';
