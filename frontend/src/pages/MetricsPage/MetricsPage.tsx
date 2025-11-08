import React from 'react';
import { Panel, MetricDisplay, Divider } from '@/components/terminal';
import styles from '../HomePage/HomePage.module.css';

export const MetricsPage: React.FC = () => {
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>System Metrics</h1>

      <Panel title="Performance Overview" variant="accent">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px' }}>
          <MetricDisplay
            label="Total Queries"
            value={0}
            trend="neutral"
          />
          <MetricDisplay
            label="Avg Response Time"
            value="0.00"
            unit="s"
            trend="neutral"
          />
          <MetricDisplay
            label="Cache Hit Rate"
            value="0.0"
            unit="%"
            trend="neutral"
          />
          <MetricDisplay
            label="Error Rate"
            value="0.0"
            unit="%"
            status="active"
          />
        </div>
      </Panel>

      <Divider spacing="lg" />

      <Panel title="Model Distribution" variant="default">
        <p style={{ color: '#ff9500', fontSize: '14px', margin: '0' }}>
          Tier-specific query metrics will be available once the query routing system is fully integrated.
          Currently, only total query counts are tracked across all discovered models.
        </p>
      </Panel>

      <Divider spacing="lg" />

      <Panel title="Resource Utilization" variant="default">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px' }}>
          <MetricDisplay label="Total Memory" value="14.4" unit="GB" />
          <MetricDisplay label="CPU Usage" value="12" unit="%" />
          <MetricDisplay label="Network I/O" value="0.0" unit="MB/s" />
          <MetricDisplay label="Disk Usage" value="45" unit="GB" />
        </div>
      </Panel>

      <Panel title="Charts Placeholder" noPadding>
        <div className={styles.placeholder} style={{ padding: '48px', textAlign: 'center' }}>
          Chart visualizations will be implemented with Chart.js
        </div>
      </Panel>
    </div>
  );
};
