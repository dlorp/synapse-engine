import React from 'react';
import { SpinnerShowcase } from '@/examples/SpinnerShowcase';
import { CRTMonitor } from '@/components/terminal';

/**
 * SpinnerTestPage - Dedicated test page for Terminal Spinner component
 *
 * Navigate to /spinner-test to view all spinner animations
 */
export const SpinnerTestPage: React.FC = () => {
  return (
    <CRTMonitor intensity="high">
      <div style={{
        minHeight: '100vh',
        background: '#000',
        padding: '40px 20px',
        color: '#ff9500',
        fontFamily: 'JetBrains Mono, monospace',
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
        }}>
          <h1 style={{
            fontSize: '28px',
            fontWeight: 'bold',
            marginBottom: '8px',
            textShadow: '0 0 8px #ff9500',
          }}>
            TERMINAL SPINNER TEST PAGE
          </h1>
          <p style={{
            fontSize: '14px',
            color: 'rgba(255, 149, 0, 0.6)',
            marginBottom: '40px',
          }}>
            Validation page for all 4 spinner animation styles
          </p>

          <SpinnerShowcase />

          <div style={{
            marginTop: '40px',
            padding: '20px',
            border: '1px solid rgba(255, 149, 0, 0.3)',
            borderRadius: '4px',
            fontSize: '12px',
            lineHeight: '1.6',
          }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: 'bold',
              marginBottom: '12px',
            }}>
              PERFORMANCE VALIDATION
            </h3>
            <ul style={{ paddingLeft: '20px', color: 'rgba(255, 149, 0, 0.8)' }}>
              <li>Open Chrome DevTools (Cmd+Opt+I)</li>
              <li>Navigate to Performance tab</li>
              <li>Record for 5 seconds</li>
              <li>Verify: FPS should be 60fps consistently</li>
              <li>Verify: No frame drops or jank</li>
              <li>Verify: Memory stable (no growth)</li>
            </ul>

            <h3 style={{
              fontSize: '14px',
              fontWeight: 'bold',
              marginTop: '20px',
              marginBottom: '12px',
            }}>
              VISUAL VALIDATION
            </h3>
            <ul style={{ paddingLeft: '20px', color: 'rgba(255, 149, 0, 0.8)' }}>
              <li>All 4 spinners should rotate smoothly</li>
              <li>Phosphor glow visible on all spinners</li>
              <li>Pulse animation subtle but present</li>
              <li>No flickering or artifacts</li>
              <li>Characters render correctly (no boxes)</li>
            </ul>

            <h3 style={{
              fontSize: '14px',
              fontWeight: 'bold',
              marginTop: '20px',
              marginBottom: '12px',
            }}>
              CLEANUP VALIDATION
            </h3>
            <ul style={{ paddingLeft: '20px', color: 'rgba(255, 149, 0, 0.8)' }}>
              <li>Navigate away from this page</li>
              <li>Check DevTools Memory tab</li>
              <li>Verify: No detached DOM nodes</li>
              <li>Verify: No active intervals remaining</li>
            </ul>
          </div>
        </div>
      </div>
    </CRTMonitor>
  );
};
