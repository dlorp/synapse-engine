/**
 * RoutingAnalyticsPanel Component
 *
 * Displays routing decision analytics and model availability matrix.
 * Shows orchestrator routing decisions with complexity → tier mapping.
 *
 * Features:
 * - Summary stats (total decisions, avg time, fallback rate)
 * - Decision matrix with ASCII table
 * - Model availability with progress bars
 * - Real-time updates at 1Hz
 *
 * Performance: <5ms render time for matrix calculations
 */

import React from 'react';
import { useRoutingMetrics } from '@/hooks/useRoutingMetrics';
import { DecisionMatrix, AvailabilityHeatmap } from '@/components/charts';
import { TerminalSpinner } from '@/components/terminal/TerminalSpinner';
import styles from './RoutingAnalyticsPanel.module.css';

export const RoutingAnalyticsPanel: React.FC = () => {
  const { data: metrics, isLoading, error } = useRoutingMetrics();

  // Loading state
  if (isLoading) {
    return (
      <div className="webtui-panel">
        <div className="webtui-panel-header">
          <h2>ROUTING ANALYTICS</h2>
        </div>
        <div className={styles.loading}>
          <TerminalSpinner style="dots" size={24} />
          <span>LOADING ROUTING METRICS...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="webtui-panel">
        <div className="webtui-panel-header">
          <h2>ROUTING ANALYTICS</h2>
        </div>
        <div className={styles.error}>
          <span className={styles.errorIcon}>✖</span>
          <div className={styles.errorMessage}>
            <div className={styles.errorTitle}>ROUTING METRICS UNAVAILABLE</div>
            <div className={styles.errorDetail}>
              {error.message || 'Failed to fetch routing analytics'}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // No data state
  if (!metrics) {
    return (
      <div className="webtui-panel">
        <div className="webtui-panel-header">
          <h2>ROUTING ANALYTICS</h2>
        </div>
        <div className={styles.noData}>
          <span>NO ROUTING DATA AVAILABLE</span>
        </div>
      </div>
    );
  }

  const { decisionMatrix, accuracyMetrics, modelAvailability } = metrics;

  // Check if any models are available (running state check)
  const hasAvailableModels = modelAvailability.some(tier => tier.available > 0);

  // No models running state
  if (!hasAvailableModels) {
    return (
      <div className="webtui-panel">
        <div className="webtui-panel-header">
          <h2>ROUTING ANALYTICS</h2>
        </div>
        <div className={styles.awaitingModels}>
          <div className={styles.emptyHeader}>NEURAL SUBSTRATE STATUS</div>
          <div className={styles.tierStructure}>
            <div className={styles.tierRow}>
              <span className={styles.tierLabel}>Q2:</span>
              <span className={styles.emptyBar}>[░░░░░░░░░░░░░░░░░░░░]</span>
              <span className={styles.tierStatus}>0/0 OFFLINE</span>
            </div>
            <div className={styles.tierRow}>
              <span className={styles.tierLabel}>Q3:</span>
              <span className={styles.emptyBar}>[░░░░░░░░░░░░░░░░░░░░]</span>
              <span className={styles.tierStatus}>0/0 OFFLINE</span>
            </div>
            <div className={styles.tierRow}>
              <span className={styles.tierLabel}>Q4:</span>
              <span className={styles.emptyBar}>[░░░░░░░░░░░░░░░░░░░░]</span>
              <span className={styles.tierStatus}>0/0 OFFLINE</span>
            </div>
          </div>
          <div className={styles.emptyHint}>
            → Deploy models via Model Management to begin processing
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="webtui-panel">
      <div className="webtui-panel-header">
        <h2>ROUTING ANALYTICS</h2>
      </div>

      <div className={styles.content}>
        {/* Summary Stats */}
        <div className={styles.summaryStats}>
          <div className={styles.stat}>
            <div className={styles.statLabel}>Total Decisions</div>
            <div className={styles.statValue}>
              {accuracyMetrics.totalDecisions.toLocaleString()}
            </div>
          </div>

          <div className={styles.stat}>
            <div className={styles.statLabel}>Avg Decision Time</div>
            <div className={styles.statValue}>
              {accuracyMetrics.avgDecisionTimeMs.toFixed(1)}
              <span className={styles.statUnit}>ms</span>
            </div>
          </div>

          <div className={styles.stat}>
            <div className={styles.statLabel}>Fallback Rate</div>
            <div className={`${styles.statValue} ${
              accuracyMetrics.fallbackRate > 0.1 ? styles.warning : ''
            }`}>
              {(accuracyMetrics.fallbackRate * 100).toFixed(1)}
              <span className={styles.statUnit}>%</span>
            </div>
          </div>
        </div>

        {/* Decision Matrix Section */}
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h3>ROUTING DECISION MATRIX</h3>
            <div className={styles.sectionSubtitle}>
              Query complexity → Model tier distribution
            </div>
          </div>
          <div className={styles.sectionContent}>
            <DecisionMatrix decisionMatrix={decisionMatrix} />
          </div>
        </div>

        {/* Model Availability Section */}
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h3>MODEL AVAILABILITY</h3>
            <div className={styles.sectionSubtitle}>
              Real-time model instance status per tier
            </div>
          </div>
          <div className={styles.sectionContent}>
            <AvailabilityHeatmap modelAvailability={modelAvailability} />
          </div>
        </div>
      </div>
    </div>
  );
};
