/**
 * CRAGDecisionDisplay - Display Corrective RAG decisions
 *
 * Shows when CRAG actions are applied:
 * - Query reformulation
 * - Web search fallback
 * - Context filtering
 * - Knowledge graph expansion
 */

import React from 'react';
import clsx from 'clsx';
import { CRAGDecision, CRAGAction } from '../../../types/cgrag';
import styles from './CRAGDecisionDisplay.module.css';

export interface CRAGDecisionDisplayProps {
  decision: CRAGDecision;
  className?: string;
}

/**
 * Action metadata.
 */
interface ActionConfig {
  icon: string;
  label: string;
  color: string;
  description: string;
}

const ACTION_CONFIGS: Record<CRAGAction, ActionConfig> = {
  none: {
    icon: '✓',
    label: 'NO CORRECTION',
    color: 'green',
    description: 'Retrieved context is sufficient',
  },
  query_rewrite: {
    icon: '✎',
    label: 'QUERY REWRITE',
    color: 'cyan',
    description: 'Reformulated query for better retrieval',
  },
  web_fallback: {
    icon: '🌐',
    label: 'WEB FALLBACK',
    color: 'orange',
    description: 'Insufficient local context, used web search',
  },
  context_filter: {
    icon: '⧉',
    label: 'CONTEXT FILTER',
    color: 'amber',
    description: 'Filtered low-relevance chunks',
  },
  kg_expansion: {
    icon: '🕸',
    label: 'KG EXPANSION',
    color: 'cyan',
    description: 'Expanded context via knowledge graph',
  },
};

export const CRAGDecisionDisplay: React.FC<CRAGDecisionDisplayProps> = ({
  decision,
  className,
}) => {
  const config = ACTION_CONFIGS[decision.action];

  // Don't render if no correction needed
  if (decision.action === 'none') {
    return null;
  }

  return (
    <div className={clsx(styles.container, styles[config.color], className)}>
      {/* Action header */}
      <div className={styles.header}>
        <span className={styles.icon}>{config.icon}</span>
        <span className={styles.label}>{config.label}</span>
        <span className={styles.timestamp}>
          {new Date(decision.timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* Reason */}
      <div className={styles.reason}>{decision.reason}</div>

      {/* Action-specific details */}
      {decision.action === 'query_rewrite' && decision.rewrittenQuery && (
        <div className={styles.detail}>
          <div className={styles.detailLabel}>ORIGINAL:</div>
          <div className={styles.detailValue}>{decision.originalQuery}</div>
          <div className={styles.detailLabel}>REWRITTEN:</div>
          <div className={styles.detailValueHighlight}>
            {decision.rewrittenQuery}
          </div>
        </div>
      )}

      {decision.action === 'context_filter' && decision.filteredCount !== undefined && (
        <div className={styles.detail}>
          <div className={styles.detailLabel}>FILTERED CHUNKS:</div>
          <div className={styles.detailValue}>{decision.filteredCount}</div>
        </div>
      )}

      {decision.action === 'web_fallback' && decision.webResultsCount !== undefined && (
        <div className={styles.detail}>
          <div className={styles.detailLabel}>WEB RESULTS:</div>
          <div className={styles.detailValue}>{decision.webResultsCount}</div>
        </div>
      )}

      {/* Description */}
      <div className={styles.description}>{config.description}</div>
    </div>
  );
};
