/**
 * RetrievalPipelineViz - Animated visualization of CGRAG retrieval pipeline
 *
 * Shows the flow: Query → Vector Search → BM25 → Fusion → Rerank → Results
 * with live updates via WebSocket and smooth 60fps animations.
 */

import React, { useMemo } from 'react';
import clsx from 'clsx';
import {
  RetrievalPipeline,
  PipelineStage,
  RetrievalStage,
  StageStatus,
} from '../../../types/cgrag';
import styles from './RetrievalPipelineViz.module.css';

export interface RetrievalPipelineVizProps {
  pipeline: RetrievalPipeline;
  className?: string;
}

/**
 * Stage display metadata.
 */
interface StageConfig {
  label: string;
  icon: string;
  color: string;
}

const STAGE_CONFIGS: Record<RetrievalStage, StageConfig> = {
  embedding: { label: 'EMBED', icon: '⚡', color: 'cyan' },
  vector_search: { label: 'VECTOR', icon: '🔍', color: 'orange' },
  bm25_search: { label: 'BM25', icon: '📊', color: 'orange' },
  fusion: { label: 'FUSION', icon: '🔗', color: 'cyan' },
  coarse_rerank: { label: 'RERANK-1', icon: '⬆', color: 'orange' },
  fine_rerank: { label: 'RERANK-2', icon: '⬆⬆', color: 'cyan' },
  kg_expansion: { label: 'KG-EXP', icon: '🕸', color: 'orange' },
  filtering: { label: 'FILTER', icon: '✓', color: 'cyan' },
  complete: { label: 'DONE', icon: '✓', color: 'green' },
};

/**
 * Get status indicator character.
 */
const getStatusChar = (status: StageStatus): string => {
  switch (status) {
    case 'pending':
      return '○';
    case 'active':
      return '◉';
    case 'complete':
      return '●';
    case 'error':
      return '✗';
    default:
      return '?';
  }
};

/**
 * Format execution time.
 */
const formatTime = (ms?: number): string => {
  if (ms === undefined) return '--ms';
  if (ms < 1) return '<1ms';
  if (ms < 100) return `${ms.toFixed(0)}ms`;
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
};

export const RetrievalPipelineViz: React.FC<RetrievalPipelineVizProps> = ({
  pipeline,
  className,
}) => {
  // Calculate progress percentage
  const progressPercent = useMemo(() => {
    const completedStages = pipeline.stages.filter(
      (s) => s.status === 'complete'
    ).length;
    return (completedStages / pipeline.stages.length) * 100;
  }, [pipeline.stages]);

  return (
    <div className={clsx(styles.container, className)}>
      {/* Pipeline header */}
      <div className={styles.header}>
        <span className={styles.title}>RETRIEVAL PIPELINE</span>
        <span className={styles.status}>
          {pipeline.status === 'running' && (
            <span className={styles.statusRunning}>RUNNING</span>
          )}
          {pipeline.status === 'complete' && (
            <span className={styles.statusComplete}>COMPLETE</span>
          )}
          {pipeline.status === 'error' && (
            <span className={styles.statusError}>ERROR</span>
          )}
        </span>
        <span className={styles.time}>{formatTime(pipeline.totalTimeMs)}</span>
      </div>

      {/* Progress bar */}
      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${progressPercent}%` }}
          role="progressbar"
          aria-valuenow={progressPercent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      {/* Stage flow visualization */}
      <div className={styles.stageFlow}>
        {pipeline.stages.map((stage, index) => {
          const config = STAGE_CONFIGS[stage.stage];
          const isActive = stage.status === 'active';
          const isComplete = stage.status === 'complete';
          const isError = stage.status === 'error';

          return (
            <React.Fragment key={stage.stage}>
              {/* Stage node */}
              <div
                className={clsx(styles.stageNode, {
                  [styles.stageActive]: isActive,
                  [styles.stageComplete]: isComplete,
                  [styles.stageError]: isError,
                  [styles.stagePending]: stage.status === 'pending',
                })}
              >
                {/* Status indicator */}
                <div className={styles.stageStatus}>
                  {getStatusChar(stage.status)}
                </div>

                {/* Stage label */}
                <div className={styles.stageLabel}>{config.label}</div>

                {/* Candidate count */}
                <div className={styles.candidateCount}>
                  {stage.candidateCount > 0 ? stage.candidateCount : '-'}
                </div>

                {/* Execution time */}
                {stage.executionTimeMs !== undefined && (
                  <div className={styles.stageTime}>
                    {formatTime(stage.executionTimeMs)}
                  </div>
                )}

                {/* Error indicator */}
                {isError && stage.error && (
                  <div className={styles.errorTooltip}>{stage.error}</div>
                )}

                {/* Active pulse animation */}
                {isActive && <div className={styles.activePulse} />}
              </div>

              {/* Connector arrow */}
              {index < pipeline.stages.length - 1 && (
                <div
                  className={clsx(styles.connector, {
                    [styles.connectorActive]: isComplete,
                  })}
                >
                  →
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Stage details (for active/error stages) */}
      {pipeline.stages.map((stage) => {
        if (stage.status !== 'active' && stage.status !== 'error') return null;

        const config = STAGE_CONFIGS[stage.stage];

        return (
          <div key={`detail-${stage.stage}`} className={styles.stageDetail}>
            <span className={styles.detailIcon}>{config.icon}</span>
            <span className={styles.detailLabel}>{config.label}</span>
            {stage.status === 'active' && (
              <span className={styles.detailStatus}>Processing...</span>
            )}
            {stage.status === 'error' && stage.error && (
              <span className={styles.detailError}>{stage.error}</span>
            )}
          </div>
        );
      })}
    </div>
  );
};
