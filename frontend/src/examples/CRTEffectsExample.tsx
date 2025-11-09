/**
 * CRT Effects Example
 *
 * Demonstrates the enhanced CRTMonitor component with:
 * - Configurable bloom intensity (0-1)
 * - Screen curvature effect
 * - Enhanced scanline animation
 *
 * @module examples/CRTEffectsExample
 */

import React, { useState } from 'react';
import { CRTMonitor } from '../components/terminal';

export const CRTEffectsExample: React.FC = () => {
  const [bloomIntensity, setBloomIntensity] = useState(0.3);
  const [curvatureEnabled, setCurvatureEnabled] = useState(true);
  const [scanlinesEnabled, setScanlinesEnabled] = useState(true);

  return (
    <div style={{ padding: '20px', background: '#000', minHeight: '100vh' }}>
      <h1 style={{ color: '#ff9500', fontFamily: 'monospace', marginBottom: '20px' }}>
        S.Y.N.A.P.S.E. ENGINE - Enhanced CRT Effects Demo
      </h1>

      {/* Controls */}
      <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #ff9500' }}>
        <h2 style={{ color: '#ff9500', fontFamily: 'monospace', marginBottom: '15px' }}>
          Effect Controls
        </h2>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ color: '#ff9500', fontFamily: 'monospace', display: 'block', marginBottom: '5px' }}>
            Bloom Intensity: {bloomIntensity.toFixed(2)}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={bloomIntensity}
            onChange={(e) => setBloomIntensity(parseFloat(e.target.value))}
            style={{ width: '300px' }}
          />
        </div>

        <div style={{ marginBottom: '10px' }}>
          <label style={{ color: '#ff9500', fontFamily: 'monospace' }}>
            <input
              type="checkbox"
              checked={curvatureEnabled}
              onChange={(e) => setCurvatureEnabled(e.target.checked)}
              style={{ marginRight: '10px' }}
            />
            Enable Screen Curvature
          </label>
        </div>

        <div>
          <label style={{ color: '#ff9500', fontFamily: 'monospace' }}>
            <input
              type="checkbox"
              checked={scanlinesEnabled}
              onChange={(e) => setScanlinesEnabled(e.target.checked)}
              style={{ marginRight: '10px' }}
            />
            Enable Scanlines
          </label>
        </div>
      </div>

      {/* Example 1: Default Settings */}
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ color: '#00ffff', fontFamily: 'monospace', marginBottom: '10px' }}>
          Example 1: Custom Settings
        </h3>
        <CRTMonitor
          intensity="medium"
          bloomIntensity={bloomIntensity}
          curvatureEnabled={curvatureEnabled}
          scanlinesEnabled={scanlinesEnabled}
          scanlineSpeed="medium"
        >
          <div style={{
            padding: '40px',
            fontFamily: 'monospace',
            color: '#ff9500',
            fontSize: '18px',
            lineHeight: '1.6'
          }}>
            <h2 style={{ color: '#00ffff', marginBottom: '20px' }}>S.Y.N.A.P.S.E. ENGINE</h2>
            <p style={{ marginBottom: '10px' }}>Scalable Yoked Network for Adaptive Praxial System Emergence</p>
            <p style={{ marginBottom: '10px' }}>Bloom Intensity: {bloomIntensity.toFixed(2)}</p>
            <p style={{ marginBottom: '10px' }}>Curvature: {curvatureEnabled ? 'ENABLED' : 'DISABLED'}</p>
            <p>Scanlines: {scanlinesEnabled ? 'ACTIVE' : 'INACTIVE'}</p>
          </div>
        </CRTMonitor>
      </div>

      {/* Example 2: No Bloom */}
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ color: '#00ffff', fontFamily: 'monospace', marginBottom: '10px' }}>
          Example 2: No Bloom (bloomIntensity=0)
        </h3>
        <CRTMonitor
          intensity="medium"
          bloomIntensity={0}
          curvatureEnabled={true}
          scanlinesEnabled={true}
        >
          <div style={{
            padding: '40px',
            fontFamily: 'monospace',
            color: '#ff9500',
            fontSize: '16px'
          }}>
            <p>This panel has no bloom effect (bloomIntensity=0).</p>
            <p>Notice the lack of glow around the text.</p>
          </div>
        </CRTMonitor>
      </div>

      {/* Example 3: Maximum Bloom */}
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ color: '#00ffff', fontFamily: 'monospace', marginBottom: '10px' }}>
          Example 3: Maximum Bloom (bloomIntensity=1.0)
        </h3>
        <CRTMonitor
          intensity="intense"
          bloomIntensity={1.0}
          curvatureEnabled={true}
          scanlinesEnabled={true}
        >
          <div style={{
            padding: '40px',
            fontFamily: 'monospace',
            color: '#ff9500',
            fontSize: '16px'
          }}>
            <p>This panel has MAXIMUM bloom effect (bloomIntensity=1.0).</p>
            <p>Notice the strong glow around the text simulating phosphor bleeding.</p>
          </div>
        </CRTMonitor>
      </div>

      {/* Example 4: Moderate Bloom (Default) */}
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ color: '#00ffff', fontFamily: 'monospace', marginBottom: '10px' }}>
          Example 4: Default Bloom (bloomIntensity=0.3)
        </h3>
        <CRTMonitor
          intensity="medium"
          bloomIntensity={0.3}
          curvatureEnabled={true}
          scanlinesEnabled={true}
        >
          <div style={{
            padding: '40px',
            fontFamily: 'monospace',
            color: '#ff9500',
            fontSize: '16px'
          }}>
            <p>This panel uses the default bloom setting (bloomIntensity=0.3).</p>
            <p>This is the recommended setting for balanced aesthetics and readability.</p>
          </div>
        </CRTMonitor>
      </div>

      {/* Performance Note */}
      <div style={{ marginTop: '40px', padding: '20px', border: '1px dashed #00ffff' }}>
        <h3 style={{ color: '#00ffff', fontFamily: 'monospace', marginBottom: '10px' }}>
          Performance Notes
        </h3>
        <ul style={{ color: '#ff9500', fontFamily: 'monospace', lineHeight: '1.8' }}>
          <li>All effects are GPU-accelerated for 60fps performance</li>
          <li>Bloom uses CSS blur filter with screen blend mode</li>
          <li>Scanlines animate smoothly with will-change compositor hints</li>
          <li>Screen curvature uses subtle 15° perspective transform</li>
          <li>Reduced motion support automatically disables animations</li>
        </ul>
      </div>
    </div>
  );
};
