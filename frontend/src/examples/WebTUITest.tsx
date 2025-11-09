import React from 'react';

/**
 * WebTUI Integration Test Page
 * Validates complete CSS foundation for S.Y.N.A.P.S.E. ENGINE
 * Tests: layers, theme, components, responsive grid, animations
 */
const WebTUITest: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      {/* ASCII Banner */}
      <div className="synapse-banner">
{`███████╗██╗   ██╗███╗   ██╗ █████╗ ██████╗ ███████╗███████╗
██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝
███████╗ ╚████╔╝ ██╔██╗ ██║███████║██████╔╝███████╗█████╗
╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║██╔═══╝ ╚════██║██╔══╝
███████║   ██║   ██║ ╚████║██║  ██║██║     ███████║███████╗
╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝`}
      </div>

      <h1>WebTUI Integration Test Page</h1>
      <p className="synapse-text-accent">
        Testing CSS layers, phosphor orange theme, and component styles
      </p>

      {/* Status Indicators */}
      <section className="synapse-panel">
        <div className="synapse-panel__header">Status Indicators</div>
        <div className="synapse-panel__content" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <span className="synapse-status synapse-status--active">ACTIVE</span>
          <span className="synapse-status synapse-status--processing">PROCESSING</span>
          <span className="synapse-status synapse-status--error">ERROR</span>
          <span className="synapse-status synapse-status--idle">IDLE</span>
        </div>
      </section>

      {/* Metrics Grid */}
      <section className="synapse-panel">
        <div className="synapse-panel__header">System Metrics</div>
        <div className="synapse-panel__content">
          <div className="synapse-grid synapse-grid--4col">
            <div className="synapse-metric">
              <div className="synapse-metric__label">Queries/Sec</div>
              <div className="synapse-metric__value">
                12.5<span className="synapse-metric__unit">q/s</span>
              </div>
            </div>
            <div className="synapse-metric">
              <div className="synapse-metric__label">Active Models</div>
              <div className="synapse-metric__value">3</div>
            </div>
            <div className="synapse-metric">
              <div className="synapse-metric__label">Cache Hit Rate</div>
              <div className="synapse-metric__value">
                87<span className="synapse-metric__unit">%</span>
              </div>
            </div>
            <div className="synapse-metric">
              <div className="synapse-metric__label">Uptime</div>
              <div className="synapse-metric__value">
                99.9<span className="synapse-metric__unit">%</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ASCII Chart Test */}
      <section className="synapse-panel">
        <div className="synapse-panel__header">ASCII Chart Container</div>
        <div className="synapse-panel__content">
          <div className="synapse-chart">
{`  100│     ╭─╮
   80│  ╭──╯ ╰╮
   60│ ╭╯     │
   40│╭╯      ╰──╮
   20││         ╰╮
    0└┴──────────┴─
     0    5    10`}
          </div>
        </div>
      </section>

      {/* Sparkline Test */}
      <section className="synapse-panel">
        <div className="synapse-panel__header">Sparkline Test</div>
        <div className="synapse-panel__content">
          <div>
            <span className="synapse-metric__label">Performance Trend: </span>
            <span className="synapse-sparkline">▁▂▃▄▅▆▇█▇▆▅▄▃▂▁</span>
          </div>
          <div style={{ marginTop: '8px' }}>
            <span className="synapse-metric__label">Token Generation: </span>
            <span className="synapse-sparkline">▁▁▂▃▅▇█████▇▅▃▂</span>
          </div>
        </div>
      </section>

      {/* Utility Classes Test */}
      <section className="synapse-panel">
        <div className="synapse-panel__header">Utility Classes</div>
        <div className="synapse-panel__content" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <p className="synapse-text-primary">Primary text color (phosphor orange)</p>
          <p className="synapse-text-accent">Accent text color (cyan)</p>
          <p className="synapse-text-success">Success text color (green)</p>
          <p className="synapse-text-error">Error text color (red)</p>
          <p className="synapse-text-processing">Processing text color (cyan)</p>
          <p className="synapse-text-primary synapse-glow">Text with glow effect</p>
          <p className="synapse-text-primary synapse-glow-intense">Text with intense glow</p>
          <p className="synapse-text-primary synapse-pulse">Pulsing text</p>
          <p className="synapse-text-primary synapse-pulse-fast">Fast pulsing text</p>
        </div>
      </section>

      {/* Responsive Grid Test */}
      <section className="synapse-panel">
        <div className="synapse-panel__header">Responsive Grid (4-column)</div>
        <div className="synapse-panel__content">
          <div className="synapse-grid synapse-grid--4col">
            {[1, 2, 3, 4, 5, 6, 7, 8].map(num => (
              <div key={num} className="synapse-panel" style={{ margin: 0, padding: '12px' }}>
                <div className="synapse-text-accent">Grid Item {num}</div>
                <div className="synapse-sparkline">▁▂▃▄▅</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Loading States */}
      <section className="synapse-panel">
        <div className="synapse-panel__header">Loading Indicators</div>
        <div className="synapse-panel__content" style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <span className="synapse-loading">Loading...</span>
          <span className="synapse-loading synapse-loading--spinner">⟳</span>
        </div>
      </section>

      {/* Color Palette Reference */}
      <section className="synapse-panel">
        <div className="synapse-panel__header">Color Palette</div>
        <div className="synapse-panel__content">
          <div className="synapse-grid synapse-grid--3col">
            <div>
              <div className="synapse-metric__label">Primary</div>
              <div style={{ background: '#ff9500', height: '40px', border: '1px solid #ff9500' }}></div>
              <div className="synapse-metric__value" style={{ fontSize: '12px' }}>#ff9500</div>
            </div>
            <div>
              <div className="synapse-metric__label">Accent</div>
              <div style={{ background: '#00ffff', height: '40px', border: '1px solid #00ffff' }}></div>
              <div className="synapse-metric__value" style={{ fontSize: '12px' }}>#00ffff</div>
            </div>
            <div>
              <div className="synapse-metric__label">Background</div>
              <div style={{ background: '#000000', height: '40px', border: '1px solid #ff9500' }}></div>
              <div className="synapse-metric__value" style={{ fontSize: '12px' }}>#000000</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default WebTUITest;
