/**
 * OrchestratorStatusPanel - Real-time NEURAL SUBSTRATE ORCHESTRATOR visualization
 *
 * Displays:
 * - Tier utilization with ASCII bar charts
 * - Recent routing decisions with complexity reasoning
 * - Query complexity distribution
 * - Real-time decision flow
 *
 * Updates every 1 second for live visualization.
 */

import React, { useMemo } from 'react';
import { Panel } from '@/components/terminal/Panel';
import { useOrchestratorStatus } from '@/hooks/useOrchestratorStatus';
import type { ModelTierLabel, ComplexityLevel, TierUtilization } from '@/types/orchestrator';
import styles from './OrchestratorStatusPanel.module.css';

/**
 * Generate ASCII bar chart using block characters
 * Returns string like: "████████░░" (80%)
 */
const generateAsciiBar = (percent: number, width: number = 10): string => {
  const filled = Math.round((percent / 100) * width);
  const empty = width - filled;
  return '█'.repeat(filled) + '░'.repeat(empty);
};

/**
 * Get color class for model tier
 */
const getTierColorClass = (tier: ModelTierLabel): string => {
  switch (tier) {
    case 'Q2': return styles.tierQ2;
    case 'Q3': return styles.tierQ3;
    case 'Q4': return styles.tierQ4;
    default: return '';
  }
};

/**
 * Get color class for complexity level
 */
const getComplexityColorClass = (complexity: ComplexityLevel): string => {
  switch (complexity) {
    case 'SIMPLE': return styles.complexitySimple;
    case 'MODERATE': return styles.complexityModerate;
    case 'COMPLEX': return styles.complexityComplex;
    default: return '';
  }
};

/**
 * Format tier name for display
 */
const formatTierName = (tier: ModelTierLabel): string => {
  const names = {
    Q2: 'Q2 FAST    ',
    Q3: 'Q3 BALANCED',
    Q4: 'Q4 DEEP    ',
  };
  return names[tier];
};

/**
 * Truncate query text to fit display
 */
const truncateQuery = (query: string, maxLength: number = 35): string => {
  if (query.length <= maxLength) return query;
  return query.slice(0, maxLength - 3) + '...';
};

/**
 * TierUtilizationRow - Single tier utilization bar
 */
interface TierUtilizationRowProps {
  tier: TierUtilization;
}

const TierUtilizationRow: React.FC<TierUtilizationRowProps> = ({ tier }) => {
  const bar = useMemo(() => generateAsciiBar(tier.utilizationPercent), [tier.utilizationPercent]);
  const colorClass = getTierColorClass(tier.tier);

  return (
    <div className={styles.utilizationRow}>
      <span className={colorClass}>{formatTierName(tier.tier)}</span>
      <span className={styles.bar}>{bar}</span>
      <span className={styles.percent}>{tier.utilizationPercent}%</span>
    </div>
  );
};

/**
 * RoutingDecisionRow - Single routing decision entry
 */
interface RoutingDecisionRowProps {
  decision: {
    tier: ModelTierLabel;
    query: string;
    complexity: ComplexityLevel;
  };
}

const RoutingDecisionRow: React.FC<RoutingDecisionRowProps> = ({ decision }) => {
  const tierColor = getTierColorClass(decision.tier);
  const complexityColor = getComplexityColorClass(decision.complexity);
  const truncated = truncateQuery(decision.query);

  return (
    <div className={styles.decisionRow}>
      <span className={styles.arrow}>→</span>
      <span className={tierColor}>{decision.tier}:</span>
      <span className={styles.query}>"{truncated}"</span>
      <span className={complexityColor}>[{decision.complexity}]</span>
    </div>
  );
};

/**
 * ComplexityDistributionBar - Horizontal stacked bar chart
 */
interface ComplexityDistributionBarProps {
  simple: number;
  moderate: number;
  complex: number;
}

const ComplexityDistributionBar: React.FC<ComplexityDistributionBarProps> = ({
  simple,
  moderate,
  complex,
}) => {
  return (
    <div className={styles.distributionContainer}>
      <div className={styles.distributionBar}>
        <div
          className={`${styles.segment} ${styles.complexitySimple}`}
          style={{ width: `${simple}%` }}
          title={`Simple: ${simple}%`}
        />
        <div
          className={`${styles.segment} ${styles.complexityModerate}`}
          style={{ width: `${moderate}%` }}
          title={`Moderate: ${moderate}%`}
        />
        <div
          className={`${styles.segment} ${styles.complexityComplex}`}
          style={{ width: `${complex}%` }}
          title={`Complex: ${complex}%`}
        />
      </div>
      <div className={styles.distributionLabels}>
        <span className={styles.complexitySimple}>Simple: {simple}%</span>
        <span className={styles.separator}>|</span>
        <span className={styles.complexityModerate}>Moderate: {moderate}%</span>
        <span className={styles.separator}>|</span>
        <span className={styles.complexityComplex}>Complex: {complex}%</span>
      </div>
    </div>
  );
};

/**
 * Main OrchestratorStatusPanel component
 */
export const OrchestratorStatusPanel: React.FC = () => {
  const { data: status, error, isLoading } = useOrchestratorStatus();

  if (isLoading) {
    return (
      <Panel title="NEURAL SUBSTRATE ORCHESTRATOR">
        <div className={styles.loading}>Initializing orchestrator telemetry...</div>
      </Panel>
    );
  }

  if (error) {
    return (
      <Panel title="NEURAL SUBSTRATE ORCHESTRATOR" variant="error">
        <div className={styles.error}>
          ORCHESTRATOR TELEMETRY OFFLINE
          <div className={styles.errorDetail}>{error.message}</div>
        </div>
      </Panel>
    );
  }

  if (!status) {
    return (
      <Panel title="NEURAL SUBSTRATE ORCHESTRATOR">
        <div className={styles.noData}>No orchestrator data available</div>
      </Panel>
    );
  }

  return (
    <Panel
      title="NEURAL SUBSTRATE ORCHESTRATOR"
      titleRight={`AVG ${status.avgDecisionTimeMs.toFixed(1)}ms`}
    >
      <div className={styles.container}>
        {/* Tier Utilization Section */}
        <section className={styles.section}>
          <div className={styles.sectionTitle}>TIER UTILIZATION</div>
          <div className={styles.utilizationGrid}>
            {status.tierUtilization.map((tier) => (
              <TierUtilizationRow key={tier.tier} tier={tier} />
            ))}
          </div>
        </section>

        {/* Recent Routing Decisions */}
        <section className={styles.section}>
          <div className={styles.sectionTitle}>
            ROUTING DECISIONS (LAST {status.recentDecisions.length})
          </div>
          <div className={styles.decisionsGrid}>
            {status.recentDecisions.map((decision) => (
              <RoutingDecisionRow key={decision.id} decision={decision} />
            ))}
          </div>
        </section>

        {/* Complexity Distribution */}
        <section className={styles.section}>
          <div className={styles.sectionTitle}>COMPLEXITY DISTRIBUTION</div>
          <ComplexityDistributionBar
            simple={status.complexityDistribution.simple}
            moderate={status.complexityDistribution.moderate}
            complex={status.complexityDistribution.complex}
          />
        </section>

        {/* Footer Stats */}
        <div className={styles.footer}>
          <span>TOTAL DECISIONS: {status.totalDecisions.toLocaleString()}</span>
          <span className={styles.separator}>|</span>
          <span>LAST UPDATE: {new Date(status.timestamp).toLocaleTimeString()}</span>
        </div>
      </div>
    </Panel>
  );
};
