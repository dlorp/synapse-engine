/**
 * ResourceUtilizationPanel Test Page
 * Visual testing and manual validation of component behavior
 * Simulates various resource states for testing
 */

import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Panel } from '@/components/terminal';
import { ResourceMetricCard } from '@/components/metrics';
import styles from './HomePage/HomePage.module.css';

const queryClient = new QueryClient();

// Mock data for testing different states
const MOCK_STATES = {
  healthy: {
    vram: { value: '8.2 GB', percent: 51, status: 'ok' as const, secondary: '16 GB total' },
    cpu: { value: '45.2%', percent: 45.2, status: 'ok' as const, secondary: '8 cores' },
    memory: { value: '12.4 GB', percent: 38, status: 'ok' as const, secondary: '32 GB total' },
  },
  warning: {
    vram: { value: '13.6 GB', percent: 85, status: 'warning' as const, secondary: '16 GB total' },
    cpu: { value: '78.5%', percent: 78.5, status: 'warning' as const, secondary: '8 cores' },
    memory: { value: '25.6 GB', percent: 80, status: 'warning' as const, secondary: '32 GB total' },
  },
  critical: {
    vram: { value: '15.2 GB', percent: 95, status: 'critical' as const, secondary: '16 GB total' },
    cpu: { value: '96.8%', percent: 96.8, status: 'critical' as const, secondary: '8 cores' },
    memory: { value: '30.4 GB', percent: 95, status: 'critical' as const, secondary: '32 GB total' },
  },
};

export const ResourcePanelTestPage: React.FC = () => {
  const [state, setState] = useState<'healthy' | 'warning' | 'critical'>('healthy');

  const currentState = MOCK_STATES[state];

  return (
    <QueryClientProvider client={queryClient}>
      <div className={styles.page}>
        <h1 className={styles.title}>ResourceUtilizationPanel Test Page</h1>

        {/* State Selector */}
        <Panel title="TEST CONTROLS" variant="accent">
          <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
            <button
              onClick={() => setState('healthy')}
              style={{
                padding: '8px 16px',
                background: state === 'healthy' ? '#00ff00' : 'transparent',
                color: state === 'healthy' ? '#000' : '#ff9500',
                border: '1px solid #ff9500',
                cursor: 'pointer',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                fontWeight: 700,
              }}
            >
              HEALTHY STATE
            </button>
            <button
              onClick={() => setState('warning')}
              style={{
                padding: '8px 16px',
                background: state === 'warning' ? '#ff9500' : 'transparent',
                color: state === 'warning' ? '#000' : '#ff9500',
                border: '1px solid #ff9500',
                cursor: 'pointer',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                fontWeight: 700,
              }}
            >
              WARNING STATE
            </button>
            <button
              onClick={() => setState('critical')}
              style={{
                padding: '8px 16px',
                background: state === 'critical' ? '#ff0000' : 'transparent',
                color: state === 'critical' ? '#000' : '#ff9500',
                border: '1px solid #ff9500',
                cursor: 'pointer',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                fontWeight: 700,
              }}
            >
              CRITICAL STATE
            </button>
          </div>
          <div style={{ color: '#ff9500', fontSize: '12px', opacity: 0.7 }}>
            Current State: <strong>{state.toUpperCase()}</strong>
          </div>
        </Panel>

        {/* Mock Resource Panel */}
        <Panel title="SYSTEM RESOURCE UTILIZATION" variant="default">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '16px',
            }}
          >
            {/* Row 1: Core Resources */}
            <ResourceMetricCard
              label="VRAM USAGE"
              value={currentState.vram.value}
              percent={currentState.vram.percent}
              status={currentState.vram.status}
              secondary={currentState.vram.secondary}
            />

            <ResourceMetricCard
              label="CPU USAGE"
              value={currentState.cpu.value}
              percent={currentState.cpu.percent}
              status={currentState.cpu.status}
              secondary={currentState.cpu.secondary}
            />

            <ResourceMetricCard
              label="MEMORY USAGE"
              value={currentState.memory.value}
              percent={currentState.memory.percent}
              status={currentState.memory.status}
              secondary={currentState.memory.secondary}
            />

            {/* Row 2: Data Stores */}
            <ResourceMetricCard
              label="FAISS INDEX"
              value="128.5 MB"
              status="ok"
            />

            <ResourceMetricCard
              label="REDIS CACHE"
              value="45.2 MB"
              status="ok"
            />

            <ResourceMetricCard
              label="CONNECTIONS"
              value={12}
              status="ok"
            />

            {/* Row 3: Throughput */}
            <ResourceMetricCard
              label="THREAD POOL"
              value="3 / 8"
              status="ok"
              secondary="no queue"
            />

            <ResourceMetricCard
              label="DISK I/O"
              value="12.3↓ 8.1↑"
              status="ok"
              secondary="MB/s"
            />

            <ResourceMetricCard
              label="NETWORK"
              value="5.4↓ 2.1↑"
              status="ok"
              secondary="MB/s"
            />
          </div>
        </Panel>

        {/* Performance Notes */}
        <Panel title="PERFORMANCE VALIDATION" variant="default">
          <div style={{ color: '#ff9500', fontSize: '12px', lineHeight: 1.6 }}>
            <p><strong>Visual Checks:</strong></p>
            <ul style={{ marginLeft: '20px' }}>
              <li>✓ All 9 metrics display correctly</li>
              <li>✓ Progress bars show correct percentage</li>
              <li>✓ Colors change based on status (green/amber/red)</li>
              <li>✓ Critical status has pulsing animation</li>
              <li>✓ Responsive grid layout (3 columns on desktop)</li>
              <li>✓ Phosphor glow effects visible</li>
            </ul>
            <p><strong>Performance Targets:</strong></p>
            <ul style={{ marginLeft: '20px' }}>
              <li>Render Time: &lt;16ms average (60fps)</li>
              <li>No jank during state changes</li>
              <li>Smooth progress bar transitions</li>
              <li>Stable memory (no leaks)</li>
            </ul>
            <p><strong>Testing Instructions:</strong></p>
            <ol style={{ marginLeft: '20px' }}>
              <li>Toggle between states using buttons above</li>
              <li>Observe smooth transitions (no flicker)</li>
              <li>Check browser DevTools Performance tab</li>
              <li>Verify no console errors or warnings</li>
              <li>Test responsive behavior (resize window)</li>
            </ol>
          </div>
        </Panel>
      </div>
    </QueryClientProvider>
  );
};
