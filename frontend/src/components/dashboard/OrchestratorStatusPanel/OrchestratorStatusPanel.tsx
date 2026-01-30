/**
 * OrchestratorStatusPanel - Real-time NEURAL SUBSTRATE ORCHESTRATOR status
 *
 * MISSION CONTROL VIEW (HomePage) - Shows CURRENT routing state only
 *
 * Displays:
 * - Current routing status (IDLE vs ROUTING)
 * - Last routing decision (single most recent)
 * - Decision latency
 *
 * Analytics (tier utilization, decision history, complexity distribution)
 * are available on MetricsPage → RoutingAnalyticsPanel
 *
 * Updates every 1 second for live visualization.
 */

import React from 'react';
import { AsciiPanel } from '@/components/terminal/AsciiPanel';
import { useOrchestratorStatus } from '@/hooks/useOrchestratorStatus';
import type { ModelTierLabel, ComplexityLevel } from '@/types/orchestrator';
import styles from './OrchestratorStatusPanel.module.css';

/**
 * Get color class for model tier
 */
const getTierColorClass = (tier: ModelTierLabel): string => {
  switch (tier) {
    case 'Q2': return styles.tierQ2 ?? '';
    case 'Q3': return styles.tierQ3 ?? '';
    case 'Q4': return styles.tierQ4 ?? '';
    default: return '';
  }
};

/**
 * Get color class for complexity level
 */
const getComplexityColorClass = (complexity: ComplexityLevel): string => {
  switch (complexity) {
    case 'SIMPLE': return styles.complexitySimple ?? '';
    case 'MODERATE': return styles.complexityModerate ?? '';
    case 'COMPLEX': return styles.complexityComplex ?? '';
    default: return '';
  }
};

/**
 * Format tier name for display
 */
const formatTierName = (tier: ModelTierLabel): string => {
  const names: Record<ModelTierLabel, string> = {
    Q2: 'Q2 FAST',
    Q3: 'Q3 BALANCED',
    Q4: 'Q4 DEEP',
  };
  return names[tier] ?? tier;
};

/**
 * Main OrchestratorStatusPanel component
 *
 * SIMPLIFIED FOR MISSION CONTROL (HomePage)
 * Shows ONLY current routing state - no analytics
 */
export const OrchestratorStatusPanel: React.FC = () => {
  const { data: status, error, isLoading } = useOrchestratorStatus();

  if (isLoading) {
    return (
      <AsciiPanel title="NEURAL SUBSTRATE ORCHESTRATOR">
        <div className={styles.loading}>Initializing orchestrator telemetry...</div>
      </AsciiPanel>
    );
  }

  if (error) {
    return (
      <AsciiPanel title="NEURAL SUBSTRATE ORCHESTRATOR" variant="error">
        <div className={styles.error}>
          ORCHESTRATOR TELEMETRY OFFLINE
          <div className={styles.errorDetail}>{error.message}</div>
        </div>
      </AsciiPanel>
    );
  }

  if (!status) {
    return (
      <AsciiPanel title="NEURAL SUBSTRATE ORCHESTRATOR">
        <div className={styles.noData}>No orchestrator data available</div>
      </AsciiPanel>
    );
  }

  // Get most recent decision (if any)
  const lastDecision = status.recentDecisions.length > 0 ? status.recentDecisions[0] : null;

  // Determine current routing status
  const isRouting = status.avgDecisionTimeMs < 100; // Simplified heuristic
  const routingStatus = isRouting ? 'ROUTING' : 'IDLE';
  const statusClass = isRouting ? styles.statusRouting : styles.statusIdle;

  // Enhanced empty state when no decisions have been made yet
  if (!lastDecision || status.recentDecisions.length === 0) {
    return (
      <AsciiPanel
        title="NEURAL SUBSTRATE ORCHESTRATOR"
        titleRight={
          <span className={styles.statusIdle}>
            STATUS: IDLE
          </span>
        }
      >
        <div className={styles.emptyOrchestrator}>
          <div className={styles.flowDiagram}>
            Query → [ ? ] → Complexity → [ ? ] → Tier → [ ? ] → Model
          </div>
          <div className={styles.awaitingBar}>
            ░░░░░░░░░░░░░░░ AWAITING QUERY ░░░░░░░░░░░░░░░
          </div>
          <div className={styles.emptyStats}>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>ROUTING DECISIONS:</span>
              <span className={styles.statValue}>0</span>
            </div>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>AVG LATENCY:</span>
              <span className={styles.statValue}>--</span>
            </div>
          </div>
          <div className={styles.emptyHint}>
            → Submit query to begin orchestration
          </div>
        </div>
      </AsciiPanel>
    );
  }

  return (
    <AsciiPanel
      title="NEURAL SUBSTRATE ORCHESTRATOR"
      titleRight={
        <span className={statusClass}>
          STATUS: {routingStatus}
        </span>
      }
    >
      <div className={styles.container}>
        {/* Current Routing State (3 simple rows) */}
        <div className={styles.currentState}>
          {/* Row 1: Current Routing */}
          <div className={styles.stateRow}>
            <span className={styles.label}>CURRENT ROUTING:</span>
            <span className={styles.value}>
              {lastDecision ? (
                <>
                  <span className={getTierColorClass(lastDecision.tier)}>
                    {formatTierName(lastDecision.tier)}
                  </span>
                </>
              ) : (
                <span className={styles.idle}>None</span>
              )}
            </span>
          </div>

          {/* Row 2: Last Decision */}
          <div className={styles.stateRow}>
            <span className={styles.label}>LAST DECISION:</span>
            <span className={styles.value}>
              {lastDecision ? (
                <>
                  <span className={getTierColorClass(lastDecision.tier)}>
                    {lastDecision.tier}
                  </span>
                  {' '}
                  <span className={getComplexityColorClass(lastDecision.complexity)}>
                    [{lastDecision.complexity}]
                  </span>
                  {' - '}
                  <span className={styles.latency}>
                    {status.avgDecisionTimeMs.toFixed(0)}ms
                  </span>
                </>
              ) : (
                <span className={styles.idle}>No decisions yet</span>
              )}
            </span>
          </div>

          {/* Row 3: Analytics Link */}
          <div className={styles.stateRow}>
            <span className={styles.analyticsHint}>
              For detailed routing analytics, visit Metrics → Routing Analytics
            </span>
          </div>
        </div>
      </div>
    </AsciiPanel>
  );
};
