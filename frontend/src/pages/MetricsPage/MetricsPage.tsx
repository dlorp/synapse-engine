import React from 'react';
import { Divider } from '@/components/terminal';
import { SystemHealthOverview } from './SystemHealthOverview';
import { QueryAnalyticsPanel } from './QueryAnalyticsPanel';
import { TierComparisonPanel } from './TierComparisonPanel';
import { ResourceUtilizationPanel } from './ResourceUtilizationPanel';
import { RoutingAnalyticsPanel } from './RoutingAnalyticsPanel';
import { HistoricalMetricsPanel } from './HistoricalMetricsPanel';
import styles from '../HomePage/HomePage.module.css';

/**
 * MetricsPage - Phase 2 Complete Implementation + Conditional Rendering
 *
 * Displays 6 metrics panels with ASCII visualizations:
 * 0. System Health Overview - 4 sparklines for aggregate system metrics (conditional)
 * 1. Query Analytics - Line/bar charts for query metrics (conditional)
 * 2. Tier Comparison - Sparklines for Q2/Q3/Q4 performance (conditional, tier-filtered)
 * 3. Resource Utilization - 9-metric system resource grid (conditional)
 * 4. Routing Analytics - Decision matrix and model availability (conditional)
 * 5. Historical Metrics - Lifetime statistics (collapsible)
 *
 * Panels 0-4 only show when models are running (conditional rendering)
 * Panel 5 shows historical data (collapsible by default)
 * All panels update at 1Hz via TanStack Query
 * Performance target: 60fps, <100ms API response
 */
export const MetricsPage: React.FC = () => {
  return (
    <div className={styles.page}>
      {/* Header - Matches AdminPage format */}
      <div className={styles.header}>
        <h1 className={styles.title}>SYSTEM METRICS</h1>
        <div className={styles.subtitle}>Real-time analytics and performance monitoring</div>
      </div>

      {/* Panel 0: System Health Overview - Aggregate system performance trends */}
      <SystemHealthOverview />

      <Divider spacing="lg" />

      {/* Panel 1: Query Analytics - Real-time query rate and tier distribution */}
      <QueryAnalyticsPanel />

      <Divider spacing="lg" />

      {/* Panel 2: Tier Performance Comparison - Real-time sparklines for Q2/Q3/Q4 */}
      <TierComparisonPanel />

      <Divider spacing="lg" />

      {/* Panel 3: Resource Utilization - System resource monitoring (9 metrics) */}
      <ResourceUtilizationPanel />

      <Divider spacing="lg" />

      {/* Panel 4: Routing Analytics - Decision matrix and model availability */}
      <RoutingAnalyticsPanel />

      <Divider spacing="lg" />

      {/* Panel 5: Historical Metrics - Lifetime statistics (collapsible) */}
      <HistoricalMetricsPanel />
    </div>
  );
};
