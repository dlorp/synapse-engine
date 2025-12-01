/**
 * HybridSearchPanel - Display hybrid search scores (Vector + BM25)
 *
 * Shows side-by-side comparison of vector similarity and BM25 keyword scores,
 * with Reciprocal Rank Fusion (RRF) final scores and visual weight indicators.
 */

import React, { useMemo } from 'react';
import clsx from 'clsx';
import { HybridSearchMetrics } from '../../../types/cgrag';
import { Panel } from '../../terminal/Panel/Panel';
import styles from './HybridSearchPanel.module.css';

export interface HybridSearchPanelProps {
  metrics: HybridSearchMetrics;
  className?: string;
}

/**
 * Format score as percentage.
 */
const formatScore = (score: number): string => {
  return (score * 100).toFixed(1);
};

/**
 * Get color class based on score.
 */
const getScoreColor = (score: number): string => {
  if (score >= 0.7) return styles.scoreHigh;
  if (score >= 0.4) return styles.scoreMed;
  return styles.scoreLow;
};

/**
 * Render a horizontal bar graph.
 */
const ScoreBar: React.FC<{ score: number; color: string }> = ({
  score,
  color,
}) => {
  const width = Math.max(0, Math.min(score * 100, 100));

  return (
    <div className={styles.scoreBar}>
      <div
        className={clsx(styles.scoreBarFill, color)}
        style={{ width: `${width}%` }}
      />
    </div>
  );
};

export const HybridSearchPanel: React.FC<HybridSearchPanelProps> = ({
  metrics,
  className,
}) => {
  // Calculate overlap percentage
  const overlapPercent = useMemo(() => {
    const totalCandidates = Math.max(
      metrics.vectorCandidates,
      metrics.bm25Candidates
    );
    return totalCandidates > 0
      ? (metrics.overlapCount / totalCandidates) * 100
      : 0;
  }, [metrics]);

  return (
    <Panel
      title="HYBRID SEARCH METRICS"
      titleRight={`RRF-${metrics.rrfConstant}`}
      className={className}
    >
      <div className={styles.container}>
        {/* Summary stats */}
        <div className={styles.summary}>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Vector</span>
            <span className={styles.statValue}>{metrics.vectorCandidates}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>BM25</span>
            <span className={styles.statValue}>{metrics.bm25Candidates}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Overlap</span>
            <span className={styles.statValue}>
              {metrics.overlapCount}
              <span className={styles.statPercent}>
                ({overlapPercent.toFixed(0)}%)
              </span>
            </span>
          </div>
        </div>

        {/* Average scores */}
        <div className={styles.averages}>
          <div className={styles.avgRow}>
            <span className={styles.avgLabel}>AVG VECTOR</span>
            <span className={clsx(styles.avgValue, styles.vectorColor)}>
              {formatScore(metrics.avgVectorScore)}%
            </span>
            <ScoreBar score={metrics.avgVectorScore} color={styles.vectorBar} />
          </div>
          <div className={styles.avgRow}>
            <span className={styles.avgLabel}>AVG BM25</span>
            <span className={clsx(styles.avgValue, styles.bm25Color)}>
              {formatScore(metrics.avgBm25Score)}%
            </span>
            <ScoreBar score={metrics.avgBm25Score} color={styles.bm25Bar} />
          </div>
        </div>

        {/* Top results table */}
        <div className={styles.resultsTable}>
          <div className={styles.tableHeader}>
            <span className={styles.colRank}>RNK</span>
            <span className={styles.colId}>CHUNK</span>
            <span className={styles.colScore}>VEC</span>
            <span className={styles.colScore}>BM25</span>
            <span className={styles.colScore}>FUSION</span>
          </div>

          {metrics.topResults.slice(0, 5).map((result, index) => (
            <div key={result.chunkId} className={styles.tableRow}>
              <span className={styles.colRank}>#{result.finalRank}</span>
              <span className={styles.colId} title={result.chunkId}>
                {result.chunkId.slice(0, 8)}...
              </span>
              <span
                className={clsx(
                  styles.colScore,
                  getScoreColor(result.vectorScore)
                )}
              >
                {formatScore(result.vectorScore)}
              </span>
              <span
                className={clsx(
                  styles.colScore,
                  getScoreColor(result.bm25Score)
                )}
              >
                {formatScore(result.bm25Score)}
              </span>
              <span
                className={clsx(
                  styles.colScore,
                  styles.fusionScore,
                  getScoreColor(result.fusionScore)
                )}
              >
                {formatScore(result.fusionScore)}
              </span>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className={styles.legend}>
          <div className={styles.legendItem}>
            <span className={clsx(styles.legendDot, styles.vectorColor)} />
            <span className={styles.legendLabel}>Vector Similarity</span>
          </div>
          <div className={styles.legendItem}>
            <span className={clsx(styles.legendDot, styles.bm25Color)} />
            <span className={styles.legendLabel}>BM25 Keyword</span>
          </div>
          <div className={styles.legendItem}>
            <span className={clsx(styles.legendDot, styles.fusionColor)} />
            <span className={styles.legendLabel}>RRF Fusion</span>
          </div>
        </div>
      </div>
    </Panel>
  );
};
