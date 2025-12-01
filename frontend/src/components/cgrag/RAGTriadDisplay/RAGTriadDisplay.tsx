/**
 * RAGTriadDisplay - Display RAG quality metrics (Context/Groundedness/Answer)
 *
 * Based on French research (Mistral AI RAG Triad):
 * 1. Context Relevance: Were retrieved documents relevant?
 * 2. Groundedness: Is response grounded in context?
 * 3. Answer Relevance: Does answer address the question?
 *
 * Shows three-metric display with color-coded quality indicators
 * and historical trend sparklines.
 */

import React from 'react';
import clsx from 'clsx';
import { RAGTriadMetrics, RAGQualityTrend } from '../../../types/cgrag';
import { Panel } from '../../terminal/Panel/Panel';
import { Sparkline } from '../../terminal/Sparkline/Sparkline';
import styles from './RAGTriadDisplay.module.css';

export interface RAGTriadDisplayProps {
  metrics: RAGTriadMetrics;
  trend?: RAGQualityTrend;
  className?: string;
}

/**
 * Get quality level from score.
 */
const getQualityLevel = (
  score: number
): 'excellent' | 'good' | 'fair' | 'poor' => {
  if (score >= 0.8) return 'excellent';
  if (score >= 0.6) return 'good';
  if (score >= 0.4) return 'fair';
  return 'poor';
};

/**
 * Get quality color class.
 */
const getQualityColor = (level: string): string => {
  switch (level) {
    case 'excellent':
      return styles.excellent;
    case 'good':
      return styles.good;
    case 'fair':
      return styles.fair;
    case 'poor':
      return styles.poor;
    default:
      return '';
  }
};

/**
 * Get trend indicator.
 */
const getTrendIndicator = (trend?: RAGQualityTrend): string => {
  if (!trend) return '—';
  switch (trend.trend) {
    case 'improving':
      return '↗';
    case 'declining':
      return '↘';
    case 'stable':
      return '→';
    default:
      return '—';
  }
};

/**
 * Get trend color.
 */
const getTrendColor = (trend?: RAGQualityTrend): string => {
  if (!trend) return '';
  switch (trend.trend) {
    case 'improving':
      return styles.trendImproving;
    case 'declining':
      return styles.trendDeclining;
    case 'stable':
      return styles.trendStable;
    default:
      return '';
  }
};

/**
 * Single metric card.
 */
const MetricCard: React.FC<{
  label: string;
  score: number;
  trendData?: number[];
  avgScore?: number;
}> = ({ label, score, trendData, avgScore }) => {
  const level = getQualityLevel(score);
  const colorClass = getQualityColor(level);

  return (
    <div className={styles.metricCard}>
      <div className={styles.metricHeader}>
        <span className={styles.metricLabel}>{label}</span>
        {avgScore !== undefined && (
          <span className={styles.metricAvg}>AVG: {(avgScore * 100).toFixed(0)}%</span>
        )}
      </div>

      <div className={clsx(styles.metricScore, colorClass)}>
        {(score * 100).toFixed(1)}%
      </div>

      <div className={clsx(styles.metricLevel, colorClass)}>
        {level.toUpperCase()}
      </div>

      {trendData && trendData.length > 0 && (
        <div className={styles.metricTrend}>
          <Sparkline data={trendData} width={20} color="accent" />
        </div>
      )}

      {/* Visual bar */}
      <div className={styles.metricBar}>
        <div
          className={clsx(styles.metricBarFill, colorClass)}
          style={{ width: `${score * 100}%` }}
        />
      </div>
    </div>
  );
};

export const RAGTriadDisplay: React.FC<RAGTriadDisplayProps> = ({
  metrics,
  trend,
  className,
}) => {
  // Extract trend data for sparklines
  const contextTrendData = trend
    ? trend.history.map((m) => m.contextRelevance)
    : [];
  const groundednessTrendData = trend
    ? trend.history.map((m) => m.groundedness)
    : [];
  const answerTrendData = trend
    ? trend.history.map((m) => m.answerRelevance)
    : [];

  const overallLevel = getQualityLevel(metrics.overallQuality);
  const overallColor = getQualityColor(overallLevel);
  const trendIndicator = getTrendIndicator(trend);
  const trendColor = getTrendColor(trend);

  return (
    <Panel
      title="RAG QUALITY TRIAD"
      titleRight={`OVERALL: ${(metrics.overallQuality * 100).toFixed(0)}%`}
      variant="accent"
      className={className}
    >
      <div className={styles.container}>
        {/* Overall status */}
        <div className={styles.overall}>
          <div className={clsx(styles.overallScore, overallColor)}>
            {(metrics.overallQuality * 100).toFixed(1)}%
          </div>
          <div className={clsx(styles.overallLevel, overallColor)}>
            {overallLevel.toUpperCase()}
          </div>
          {trend && (
            <div className={clsx(styles.overallTrend, trendColor)}>
              {trendIndicator} {trend.trend.toUpperCase()}
            </div>
          )}
        </div>

        {/* Three metrics */}
        <div className={styles.metrics}>
          <MetricCard
            label="CONTEXT RELEVANCE"
            score={metrics.contextRelevance}
            trendData={contextTrendData}
            avgScore={trend?.avgContextRelevance}
          />

          <MetricCard
            label="GROUNDEDNESS"
            score={metrics.groundedness}
            trendData={groundednessTrendData}
            avgScore={trend?.avgGroundedness}
          />

          <MetricCard
            label="ANSWER RELEVANCE"
            score={metrics.answerRelevance}
            trendData={answerTrendData}
            avgScore={trend?.avgAnswerRelevance}
          />
        </div>

        {/* Explanation */}
        <div className={styles.explanation}>
          <div className={styles.explanationItem}>
            <span className={styles.explanationLabel}>CONTEXT:</span>
            <span className={styles.explanationText}>
              Retrieved docs relevant to query?
            </span>
          </div>
          <div className={styles.explanationItem}>
            <span className={styles.explanationLabel}>GROUNDED:</span>
            <span className={styles.explanationText}>
              Response based on context?
            </span>
          </div>
          <div className={styles.explanationItem}>
            <span className={styles.explanationLabel}>ANSWER:</span>
            <span className={styles.explanationText}>
              Addresses original question?
            </span>
          </div>
        </div>
      </div>
    </Panel>
  );
};
