import React from 'react';
import { Divider } from '@/components/terminal';
import { SystemHealthOverview } from './SystemHealthOverview';
import { QueryAnalyticsPanel } from './QueryAnalyticsPanel';
import { TierComparisonPanel } from './TierComparisonPanel';
import { ResourceUtilizationPanel } from './ResourceUtilizationPanel';
import { RoutingAnalyticsPanel } from './RoutingAnalyticsPanel';
import styles from '../HomePage/HomePage.module.css';

/**
 * MetricsPage - Phase 2 Complete Implementation
 *
 * Displays 4 real-time metrics panels with ASCII visualizations:
 * 1. Query Analytics - Line/bar charts for query metrics
 * 2. Tier Comparison - Sparklines for Q2/Q3/Q4 performance
 * 3. Resource Utilization - 9-metric system resource grid
 * 4. Routing Analytics - Decision matrix and model availability
 *
 * All panels update at 1Hz via TanStack Query
 * Performance target: 60fps, <100ms API response
 */
export const MetricsPage: React.FC = () => {
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>S.Y.N.A.P.S.E. ENGINE - System Metrics</h1>

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
    </div>
  );
};
