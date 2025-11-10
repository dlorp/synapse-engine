/**
 * ModelSparkline Component Test Page
 *
 * Tests the ModelSparkline wrapper component with sample data
 * for all three metric types (tokens, memory, latency).
 */

import React from 'react';
import { ModelSparkline } from '@/components/models/ModelSparkline';

const ModelSparklineTestPage: React.FC = () => {
  // Sample data for testing (20 datapoints as expected)
  const tokensData = [42.3, 45.1, 43.2, 48.5, 50.2, 47.8, 49.1, 51.3, 48.7, 46.2,
                      44.5, 47.2, 49.8, 52.1, 50.5, 48.3, 46.9, 45.5, 47.1, 48.8];

  const memoryData = [2.1, 2.15, 2.18, 2.22, 2.25, 2.28, 2.31, 2.35, 2.32, 2.29,
                      2.26, 2.23, 2.20, 2.17, 2.14, 2.11, 2.08, 2.05, 2.03, 2.01];

  const latencyData = [85, 82, 88, 90, 87, 84, 86, 83, 81, 79,
                       77, 80, 82, 85, 88, 91, 89, 86, 84, 82];

  // Empty data for edge case testing
  const emptyData: number[] = [];

  return (
    <div style={{
      padding: '2rem',
      background: '#000',
      color: '#ff9500',
      fontFamily: 'JetBrains Mono, monospace',
      minHeight: '100vh'
    }}>
      <h1 style={{
        fontSize: '1.5rem',
        marginBottom: '2rem',
        borderBottom: '2px solid #ff9500',
        paddingBottom: '0.5rem'
      }}>
        ModelSparkline Component Test
      </h1>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '2rem',
        marginBottom: '2rem'
      }}>
        {/* Tokens Metric */}
        <div style={{
          border: '1px solid #ff9500',
          padding: '1rem',
          background: 'rgba(255, 149, 0, 0.05)'
        }}>
          <h2 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#00ffff' }}>
            Tokens/sec (Cyan)
          </h2>
          <ModelSparkline
            data={tokensData}
            metricType="tokens"
            modelId="Q2_FAST_1"
          />
        </div>

        {/* Memory Metric */}
        <div style={{
          border: '1px solid #ff9500',
          padding: '1rem',
          background: 'rgba(255, 149, 0, 0.05)'
        }}>
          <h2 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#ff9500' }}>
            Memory (Phosphor Orange)
          </h2>
          <ModelSparkline
            data={memoryData}
            metricType="memory"
            modelId="Q3_BALANCED_1"
          />
        </div>

        {/* Latency Metric */}
        <div style={{
          border: '1px solid #ff9500',
          padding: '1rem',
          background: 'rgba(255, 149, 0, 0.05)'
        }}>
          <h2 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#00ff41' }}>
            Latency (Green)
          </h2>
          <ModelSparkline
            data={latencyData}
            metricType="latency"
            modelId="Q4_POWERFUL_1"
          />
        </div>

        {/* Empty Data Edge Case */}
        <div style={{
          border: '1px solid #ff0000',
          padding: '1rem',
          background: 'rgba(255, 0, 0, 0.05)'
        }}>
          <h2 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#ff0000' }}>
            Empty Data (Edge Case)
          </h2>
          <ModelSparkline
            data={emptyData}
            metricType="tokens"
            modelId="Q2_FAST_2"
          />
        </div>
      </div>

      <div style={{
        border: '1px solid #00ffff',
        padding: '1rem',
        background: 'rgba(0, 255, 255, 0.05)'
      }}>
        <h2 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Multiple Sparklines (Simulating Model Card)</h2>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem'
        }}>
          <ModelSparkline
            data={tokensData}
            metricType="tokens"
            modelId="Q2_FAST_1"
          />
          <ModelSparkline
            data={memoryData}
            metricType="memory"
            modelId="Q2_FAST_1"
          />
          <ModelSparkline
            data={latencyData}
            metricType="latency"
            modelId="Q2_FAST_1"
          />
        </div>
      </div>

      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        border: '1px solid rgba(255, 149, 0, 0.3)',
        background: 'rgba(255, 149, 0, 0.05)'
      }}>
        <h2 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Success Criteria</h2>
        <ul style={{ fontSize: '0.875rem', lineHeight: '1.6' }}>
          <li>✓ Component renders sparklines for all 3 metric types</li>
          <li>✓ Colors match specification (cyan/amber/green)</li>
          <li>✓ Value formatting includes proper units (t/s, GB, ms)</li>
          <li>✓ React.memo optimization applied</li>
          <li>✓ Handles empty data gracefully (no crashes)</li>
          <li>✓ Phosphor orange theme integration</li>
          <li>✓ No console errors or warnings</li>
        </ul>
      </div>
    </div>
  );
};

export default ModelSparklineTestPage;
