/**
 * Query Analytics Test Page
 * Standalone test page for QueryAnalyticsPanel component
 */

import React from 'react';
import { QueryAnalyticsPanel } from './MetricsPage/QueryAnalyticsPanel';

export const QueryAnalyticsTestPage: React.FC = () => {
  return (
    <div style={{
      padding: '20px',
      background: '#000000',
      minHeight: '100vh',
    }}>
      <h1 style={{
        color: '#ff9500',
        fontFamily: 'var(--webtui-font-family)',
        marginBottom: '20px',
      }}>
        QUERY ANALYTICS PANEL TEST
      </h1>

      <QueryAnalyticsPanel />
    </div>
  );
};
