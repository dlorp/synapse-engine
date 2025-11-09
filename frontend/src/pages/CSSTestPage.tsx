/**
 * CSS Test Page - WebTUI Component Showcase
 *
 * Demonstrates all WebTUI CSS components with phosphor orange theme.
 * Serves as visual test and component reference.
 *
 * Route: /css-test
 */

import React, { useState } from 'react';
import { CRTMonitor } from '../components/terminal';
import type { CRTIntensity } from '../components/terminal';

export const CSSTestPage: React.FC = () => {
  const [crtIntensity, setCrtIntensity] = useState<CRTIntensity>('medium');
  const [enableScanlines, setEnableScanlines] = useState(true);
  const [enableCurvature, setEnableCurvature] = useState(true);

  return (
    <div style={{ padding: '24px', maxWidth: '1920px', margin: '0 auto' }}>
      {/* CRT Controls */}
      <div style={{ marginBottom: '24px', padding: '16px', background: '#000', border: '1px solid #ff9500' }}>
        <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#ff9500' }}>CRT Effect Controls</h3>
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          <label style={{ color: '#ff9500' }}>
            Intensity:
            <select
              value={crtIntensity}
              onChange={(e) => setCrtIntensity(e.target.value as CRTIntensity)}
              style={{ marginLeft: '8px', background: '#000', color: '#ff9500', border: '1px solid #ff9500', padding: '4px' }}
            >
              <option value="subtle">Subtle</option>
              <option value="medium">Medium</option>
              <option value="intense">Intense</option>
            </select>
          </label>
          <label style={{ color: '#ff9500' }}>
            <input
              type="checkbox"
              checked={enableScanlines}
              onChange={(e) => setEnableScanlines(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            Enable Scanlines
          </label>
          <label style={{ color: '#ff9500' }}>
            <input
              type="checkbox"
              checked={enableCurvature}
              onChange={(e) => setEnableCurvature(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            Enable Screen Curvature
          </label>
        </div>
      </div>

      {/* Page Header - Wrapped in CRT */}
      <CRTMonitor
        intensity={crtIntensity}
        enableScanlines={enableScanlines}
        enableCurvature={enableCurvature}
      >
        <div style={{ padding: '24px' }}>
          <div className="synapse-banner">
{`███████╗██╗   ██╗███╗   ██╗ █████╗ ██████╗ ███████╗███████╗
██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝
███████╗ ╚████╔╝ ██╔██╗ ██║███████║██████╔╝███████╗█████╗
╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║██╔═══╝ ╚════██║██╔══╝
███████║   ██║   ██║ ╚████║██║  ██║██║     ███████║███████╗
╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝`}
      </div>

      <h1 style={{ marginTop: '32px', marginBottom: '8px' }}>
        WebTUI Component Showcase
      </h1>
      <p style={{ color: 'var(--webtui-accent)', marginBottom: '32px' }}>
        Testing WebTUI CSS framework integration with phosphor orange theme
      </p>

      {/* Section 1: Panels */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        1. Panel Components
      </h2>
      <div className="synapse-grid synapse-grid--3col">
        <div className="synapse-panel">
          <div className="synapse-panel__header">Basic Panel</div>
          <div className="synapse-panel__content">
            This is a basic panel with header and content. Notice the phosphor orange
            border and glow effect.
          </div>
        </div>

        <div className="synapse-panel">
          <div className="synapse-panel__header">Panel with Status</div>
          <div className="synapse-panel__content">
            <span className="synapse-status synapse-status--active">ACTIVE</span>
            <span className="synapse-status synapse-status--processing" style={{ marginLeft: '8px' }}>
              PROCESSING
            </span>
          </div>
        </div>

        <div className="synapse-panel">
          <div className="synapse-panel__header">Panel with Metrics</div>
          <div className="synapse-panel__content">
            <div className="synapse-metric">
              <div className="synapse-metric__label">CPU Usage</div>
              <div className="synapse-metric__value">
                87<span className="synapse-metric__unit">%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Section 2: Status Indicators */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        2. Status Indicators
      </h2>
      <div className="synapse-panel">
        <div className="synapse-panel__header">All Status States</div>
        <div className="synapse-panel__content" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <span className="synapse-status synapse-status--active">ACTIVE</span>
          <span className="synapse-status synapse-status--processing">PROCESSING</span>
          <span className="synapse-status synapse-status--error">ERROR</span>
          <span className="synapse-status synapse-status--idle">IDLE</span>
        </div>
      </div>

      {/* Section 3: Metrics Display */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        3. Metric Displays
      </h2>
      <div className="synapse-grid synapse-grid--4col">
        <div className="synapse-metric">
          <div className="synapse-metric__label">Queries/Sec</div>
          <div className="synapse-metric__value">
            45.2<span className="synapse-metric__unit">q/s</span>
          </div>
        </div>
        <div className="synapse-metric">
          <div className="synapse-metric__label">Avg Latency</div>
          <div className="synapse-metric__value">
            127<span className="synapse-metric__unit">ms</span>
          </div>
        </div>
        <div className="synapse-metric">
          <div className="synapse-metric__label">VRAM Usage</div>
          <div className="synapse-metric__value">
            6.4<span className="synapse-metric__unit">GB</span>
          </div>
        </div>
        <div className="synapse-metric">
          <div className="synapse-metric__label">Cache Hit Rate</div>
          <div className="synapse-metric__value">
            82<span className="synapse-metric__unit">%</span>
          </div>
        </div>
      </div>

      {/* Section 4: ASCII Charts */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        4. ASCII Chart Containers
      </h2>
      <div className="synapse-panel">
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
 10% ┤                                                │
  0% ┼────────────────────────────────────────────────╯
     0    5   10   15   20   25   30   35   40   45  50`}
          </div>
        </div>
      </div>

      {/* Section 5: Sparklines */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        5. Sparkline Displays
      </h2>
      <div className="synapse-grid synapse-grid--2col">
        <div className="synapse-panel">
          <div className="synapse-panel__header">Model Q2 Throughput</div>
          <div className="synapse-panel__content">
            <div className="synapse-sparkline">▁▂▃▅▆▇██████▇▆▅▃▂▁</div>
            <div style={{ marginTop: '8px', color: 'var(--webtui-accent)' }}>
              Trend: Increasing
            </div>
          </div>
        </div>
        <div className="synapse-panel">
          <div className="synapse-panel__header">Memory Allocation</div>
          <div className="synapse-panel__content">
            <div className="synapse-sparkline">████▇▆▅▄▃▂▁▁▁▂▃▄▅</div>
            <div style={{ marginTop: '8px', color: 'var(--webtui-accent)' }}>
              Trend: Stabilizing
            </div>
          </div>
        </div>
      </div>

      {/* Section 6: Combined Example */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        6. Real-World Example: Model Status Dashboard
      </h2>
      <div className="synapse-grid synapse-grid--3col">
        <div className="synapse-panel">
          <div className="synapse-panel__header">
            DeepSeek-V3 (Q2)
            <span className="synapse-status synapse-status--active" style={{ float: 'right', fontSize: '12px' }}>
              ACTIVE
            </span>
          </div>
          <div className="synapse-panel__content">
            <div className="synapse-metric">
              <div className="synapse-metric__label">Tokens/Sec</div>
              <div className="synapse-metric__value">
                142<span className="synapse-metric__unit">t/s</span>
              </div>
            </div>
            <div className="synapse-sparkline" style={{ marginTop: '8px' }}>
              ▃▅▆▇█████████▇▆▅
            </div>
            <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--webtui-accent)' }}>
              Port: 8080 | VRAM: 2.1GB
            </div>
          </div>
        </div>

        <div className="synapse-panel">
          <div className="synapse-panel__header">
            DeepSeek-V3 (Q3)
            <span className="synapse-status synapse-status--processing" style={{ float: 'right', fontSize: '12px' }}>
              PROCESSING
            </span>
          </div>
          <div className="synapse-panel__content">
            <div className="synapse-metric">
              <div className="synapse-metric__label">Tokens/Sec</div>
              <div className="synapse-metric__value">
                87<span className="synapse-metric__unit">t/s</span>
              </div>
            </div>
            <div className="synapse-sparkline" style={{ marginTop: '8px' }}>
              ▁▂▃▄▅▆▇████▇▆▅▄
            </div>
            <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--webtui-accent)' }}>
              Port: 8081 | VRAM: 4.2GB
            </div>
          </div>
        </div>

        <div className="synapse-panel">
          <div className="synapse-panel__header">
            DeepSeek-V3 (Q4)
            <span className="synapse-status synapse-status--idle" style={{ float: 'right', fontSize: '12px' }}>
              IDLE
            </span>
          </div>
          <div className="synapse-panel__content">
            <div className="synapse-metric">
              <div className="synapse-metric__label">Tokens/Sec</div>
              <div className="synapse-metric__value">
                0<span className="synapse-metric__unit">t/s</span>
              </div>
            </div>
            <div className="synapse-sparkline" style={{ marginTop: '8px' }}>
              ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
            </div>
            <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--webtui-accent)' }}>
              Port: 8082 | VRAM: 6.8GB
            </div>
          </div>
        </div>
      </div>

      {/* Section 7: Utility Classes */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        7. Utility Classes
      </h2>
      <div className="synapse-panel">
        <div className="synapse-panel__header">Text Colors & Effects</div>
        <div className="synapse-panel__content" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="synapse-text-primary">Primary Text (Phosphor Orange)</div>
          <div className="synapse-text-accent">Accent Text (Cyan)</div>
          <div className="synapse-text-success">Success Text (Green)</div>
          <div className="synapse-text-error">Error Text (Red)</div>
          <div className="synapse-text-processing">Processing Text (Cyan)</div>
          <div className="synapse-text-primary synapse-glow">Primary with Glow</div>
          <div className="synapse-text-primary synapse-glow-intense">Primary with Intense Glow</div>
          <div className="synapse-text-primary synapse-pulse">Primary with Pulse Animation</div>
          <div className="synapse-text-primary synapse-pulse-fast">Primary with Fast Pulse</div>
        </div>
      </div>

      {/* Section 8: Loading Indicators */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        8. Loading Indicators
      </h2>
      <div className="synapse-panel">
        <div className="synapse-panel__header">Loading States</div>
        <div className="synapse-panel__content" style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div className="synapse-loading">Loading...</div>
          <div className="synapse-loading synapse-loading--spinner">⟳</div>
          <span className="synapse-status synapse-status--processing">PROCESSING</span>
        </div>
      </div>

      {/* Section 9: Responsive Grid Test */}
      <h2 style={{ marginTop: '32px', marginBottom: '16px' }}>
        9. Responsive Grid System
      </h2>
      <p style={{ color: 'var(--webtui-accent)', marginBottom: '16px' }}>
        Resize browser to test responsive breakpoints (mobile &lt; 768px, tablet 768-1280px, desktop &gt; 1280px, wide &gt; 1920px)
      </p>
      <div className="synapse-grid synapse-grid--4col">
        {[1, 2, 3, 4, 5, 6, 7, 8].map(num => (
          <div key={num} className="synapse-panel">
            <div className="synapse-panel__header">Grid Item {num}</div>
            <div className="synapse-panel__content">
              This panel adapts to screen size automatically.
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={{ marginTop: '48px', padding: '16px', borderTop: '1px solid var(--webtui-border)', textAlign: 'center', color: 'var(--webtui-accent)' }}>
        <p>S.Y.N.A.P.S.E. ENGINE - WebTUI CSS Framework v0.1.5</p>
        <p style={{ fontSize: '12px', marginTop: '8px' }}>
          Phosphor Orange Theme (#ff9500) | CSS Layers: base → utils → components
        </p>
        <p style={{ fontSize: '12px', marginTop: '8px', color: '#00ffff' }}>
          CRT Effects: Enabled | Phosphor Glow, Scanlines, Chromatic Aberration, Vignette
        </p>
      </div>
        </div>
      </CRTMonitor>
    </div>
  );
};
