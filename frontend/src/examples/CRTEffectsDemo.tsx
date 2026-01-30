/**
 * CRT Effects Demo
 *
 * Demonstrates the CRTMonitor component with various configurations.
 * This file serves as a reference for how to use CRT effects in components.
 */

import React from 'react';
import { CRTMonitor } from '../components/terminal';

export const CRTEffectsDemo: React.FC = () => {
  return (
    <div style={{ padding: '24px', background: '#000' }}>
      <h1 style={{ color: '#ff9500', marginBottom: '32px' }}>
        CRT Effects Foundation - Implementation Examples
      </h1>

      {/* Example 1: Basic Usage */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ color: '#00ffff', marginBottom: '16px' }}>
          1. Basic Usage (Default Settings)
        </h2>
        <CRTMonitor>
          <div className="synapse-panel" style={{ padding: '24px' }}>
            <div className="synapse-panel__header">Default CRT Monitor</div>
            <div className="synapse-panel__content">
              <p>This panel is wrapped in a CRTMonitor with default settings:</p>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li>Intensity: medium</li>
                <li>Scanlines: enabled</li>
                <li>Screen curvature: enabled</li>
                <li>Chromatic aberration: enabled</li>
                <li>Vignette: enabled</li>
              </ul>
            </div>
          </div>
        </CRTMonitor>
      </section>

      {/* Example 2: Subtle Intensity */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ color: '#00ffff', marginBottom: '16px' }}>
          2. Subtle Intensity (Minimal Effects)
        </h2>
        <CRTMonitor intensity="subtle">
          <div className="synapse-panel" style={{ padding: '24px' }}>
            <div className="synapse-panel__header">Subtle CRT Effect</div>
            <div className="synapse-panel__content">
              <p>Lighter phosphor glow and scanlines for subtle aesthetics.</p>
              <div className="synapse-metric" style={{ marginTop: '16px' }}>
                <div className="synapse-metric__label">System Load</div>
                <div className="synapse-metric__value">
                  42<span className="synapse-metric__unit">%</span>
                </div>
              </div>
            </div>
          </div>
        </CRTMonitor>
      </section>

      {/* Example 3: Intense Mode */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ color: '#00ffff', marginBottom: '16px' }}>
          3. Intense Mode (Maximum Effects)
        </h2>
        <CRTMonitor intensity="intense" scanlineSpeed="fast">
          <div className="synapse-panel" style={{ padding: '24px' }}>
            <div className="synapse-panel__header">Intense CRT Effect</div>
            <div className="synapse-panel__content">
              <p>Maximum phosphor glow, bloom, and vignette for dramatic impact.</p>
              <div style={{ marginTop: '16px' }}>
                <span className="synapse-status synapse-status--active">ACTIVE</span>
                <span className="synapse-status synapse-status--processing" style={{ marginLeft: '8px' }}>
                  PROCESSING
                </span>
              </div>
            </div>
          </div>
        </CRTMonitor>
      </section>

      {/* Example 4: No Scanlines */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ color: '#00ffff', marginBottom: '16px' }}>
          4. Scanlines Disabled
        </h2>
        <CRTMonitor enableScanlines={false}>
          <div className="synapse-panel" style={{ padding: '24px' }}>
            <div className="synapse-panel__header">No Scanlines</div>
            <div className="synapse-panel__content">
              <p>Clean display without scanline overlay. Still has phosphor glow and vignette.</p>
            </div>
          </div>
        </CRTMonitor>
      </section>

      {/* Example 5: Flat Screen (No Curvature) */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ color: '#00ffff', marginBottom: '16px' }}>
          5. Flat Screen (No Curvature)
        </h2>
        <CRTMonitor enableCurvature={false}>
          <div className="synapse-panel" style={{ padding: '24px' }}>
            <div className="synapse-panel__header">Sharp Corners</div>
            <div className="synapse-panel__content">
              <p>No border-radius applied. Perfect for stacked panels or nested layouts.</p>
            </div>
          </div>
        </CRTMonitor>
      </section>

      {/* Example 6: Multi-Panel Grid */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ color: '#00ffff', marginBottom: '16px' }}>
          6. Multi-Panel Grid in CRT
        </h2>
        <CRTMonitor intensity="medium">
          <div style={{ padding: '24px' }}>
            <div className="synapse-grid synapse-grid--3col">
              <div className="synapse-panel">
                <div className="synapse-panel__header">Model Q2</div>
                <div className="synapse-panel__content">
                  <div className="synapse-metric">
                    <div className="synapse-metric__label">Tokens/Sec</div>
                    <div className="synapse-metric__value">
                      142<span className="synapse-metric__unit">t/s</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="synapse-panel">
                <div className="synapse-panel__header">Model Q3</div>
                <div className="synapse-panel__content">
                  <div className="synapse-metric">
                    <div className="synapse-metric__label">Tokens/Sec</div>
                    <div className="synapse-metric__value">
                      87<span className="synapse-metric__unit">t/s</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="synapse-panel">
                <div className="synapse-panel__header">Model Q4</div>
                <div className="synapse-panel__content">
                  <div className="synapse-metric">
                    <div className="synapse-metric__label">Tokens/Sec</div>
                    <div className="synapse-metric__value">
                      56<span className="synapse-metric__unit">t/s</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CRTMonitor>
      </section>

      {/* Example 7: ASCII Chart with CRT */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ color: '#00ffff', marginBottom: '16px' }}>
          7. ASCII Chart with CRT Effects
        </h2>
        <CRTMonitor intensity="medium">
          <div className="synapse-panel" style={{ padding: '24px' }}>
            <div className="synapse-panel__header">CPU Usage Over Time</div>
            <div className="synapse-panel__content">
              <div className="synapse-chart">
{`100% ┤                                             ╭─╮
 90% ┤                                         ╭───╯ ╰╮
 80% ┤                                   ╭─────╯      │
 70% ┤                           ╭───────╯            │
 60% ┤                     ╭─────╯                    │
 50% ┤               ╭─────╯                          │
 40% ┤         ╭─────╯                                │
 30% ┤   ╭─────╯                                      │
 20% ┤───╯                                            │
  0% ┼────────────────────────────────────────────────╯
     0    5   10   15   20   25   30   35   40   45  50`}
              </div>
            </div>
          </div>
        </CRTMonitor>
      </section>

      {/* Integration Guide */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ color: '#00ffff', marginBottom: '16px' }}>
          Integration Guide
        </h2>
        <CRTMonitor intensity="subtle" enableScanlines={false}>
          <div style={{ padding: '24px', color: '#ff9500' }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px' }}>
              How to Use CRTMonitor in Your Components
            </h3>

            <pre style={{ background: '#111', padding: '16px', borderRadius: '4px', overflowX: 'auto' }}>
{`import { CRTMonitor } from '@/components/terminal';

// Basic usage
<CRTMonitor>
  <YourComponent />
</CRTMonitor>

// Custom intensity
<CRTMonitor intensity="intense">
  <YourComponent />
</CRTMonitor>

// Disable specific effects
<CRTMonitor
  enableScanlines={false}
  enableCurvature={false}
>
  <YourComponent />
</CRTMonitor>`}
            </pre>

            <h4 style={{ marginTop: '24px', marginBottom: '8px' }}>Available Props:</h4>
            <ul style={{ paddingLeft: '20px' }}>
              <li><code>intensity</code>: 'subtle' | 'medium' | 'intense' (default: 'medium')</li>
              <li><code>enableScanlines</code>: boolean (default: true)</li>
              <li><code>enableCurvature</code>: boolean (default: true)</li>
              <li><code>enableAberration</code>: boolean (default: true)</li>
              <li><code>enableVignette</code>: boolean (default: true)</li>
              <li><code>scanlineSpeed</code>: 'slow' | 'medium' | 'fast' (default: 'medium')</li>
            </ul>

            <h4 style={{ marginTop: '24px', marginBottom: '8px' }}>Performance Notes:</h4>
            <ul style={{ paddingLeft: '20px' }}>
              <li>All effects are GPU-accelerated for 60fps performance</li>
              <li>Scanlines use CSS transforms (translateY) for smooth animation</li>
              <li>Effects automatically reduce on mobile for better performance</li>
              <li>Respects prefers-reduced-motion for accessibility</li>
            </ul>
          </div>
        </CRTMonitor>
      </section>
    </div>
  );
};

export default CRTEffectsDemo;
