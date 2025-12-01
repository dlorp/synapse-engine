/**
 * ReActStepViewer Component - Individual ReAct Step Display
 *
 * Visualizes a single step in the ReAct loop including:
 * - Step number and model tier badge
 * - Thought (agent reasoning)
 * - Action (tool call with arguments)
 * - Observation (tool execution result, collapsible)
 *
 * Uses terminal aesthetic with bordered sections and monospace fonts.
 */

import React, { useState } from 'react';
import type { ReActStep, ModelTier } from '@/types/codeChat';
import styles from './ReActStepViewer.module.css';

/**
 * Props for ReActStepViewer component.
 */
export interface ReActStepViewerProps {
  /** ReAct step to display */
  step: ReActStep;
  /** Whether observation should be expanded by default */
  isExpanded?: boolean;
  /** Callback when expand/collapse is toggled */
  onToggle?: () => void;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Individual ReAct step viewer component.
 *
 * Displays thought, action, and observation with collapsible observation section.
 * Color-codes model tier badges (fast=cyan, balanced=orange, powerful=amber).
 */
export const ReActStepViewer: React.FC<ReActStepViewerProps> = ({
  step,
  isExpanded: controlledExpanded,
  onToggle,
  className = '',
}) => {
  // Internal expansion state (used when not controlled)
  const [internalExpanded, setInternalExpanded] = useState(false);

  // Use controlled state if provided, otherwise use internal state
  const isExpanded = controlledExpanded !== undefined ? controlledExpanded : internalExpanded;

  /**
   * Toggle observation expansion.
   */
  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalExpanded(!internalExpanded);
    }
  };

  /**
   * Get CSS class for model tier badge.
   */
  const getTierClass = (tier: ModelTier): string => {
    const tierMap: Record<ModelTier, string> = {
      fast: styles.tierFast || '',
      balanced: styles.tierBalanced || '',
      powerful: styles.tierPowerful || '',
    };
    return tierMap[tier] || styles.tierBalanced || '';
  };

  /**
   * Get tier badge label.
   */
  const getTierLabel = (tier: ModelTier): string => {
    return tier.toUpperCase();
  };

  return (
    <div className={`${styles.step} ${className}`} data-testid="react-step">
      {/* Step Header */}
      <div className={styles.stepHeader}>
        <span className={styles.stepNumber}>STEP {step.stepNumber}</span>
        <span className={`${styles.tierBadge} ${getTierClass(step.modelTier)}`}>
          {getTierLabel(step.modelTier)}
        </span>
      </div>

      {/* Thought Section */}
      <div className={styles.section}>
        <div className={styles.sectionLabel}>THOUGHT:</div>
        <div className={styles.sectionContent}>
          <p className={styles.thoughtText}>{step.thought}</p>
        </div>
      </div>

      {/* Action Section (if present) */}
      {step.action && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>ACTION:</div>
          <div className={styles.sectionContent}>
            <div className={styles.actionHeader}>
              <span className={styles.toolName}>{step.action.tool}</span>
            </div>
            <div className={styles.actionArgs}>
              {Object.entries(step.action.args).map(([key, value]) => (
                <div key={key} className={styles.argRow}>
                  <span className={styles.argKey}>{key}:</span>
                  <span className={styles.argValue}>
                    {typeof value === 'string' ? value : JSON.stringify(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Observation Section (if present, collapsible) */}
      {step.observation && (
        <div className={styles.section}>
          <div className={styles.observationHeader}>
            <div className={styles.sectionLabel}>OBSERVATION:</div>
            <button
              onClick={handleToggle}
              className={styles.expandToggle}
              aria-label={isExpanded ? 'Collapse observation' : 'Expand observation'}
              aria-expanded={isExpanded}
            >
              {isExpanded ? '[-]' : '[+]'}
            </button>
          </div>
          {isExpanded && (
            <div className={styles.sectionContent}>
              <pre className={styles.observation}>{step.observation}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

ReActStepViewer.displayName = 'ReActStepViewer';
