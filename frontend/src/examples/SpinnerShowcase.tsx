import React from 'react';
import { TerminalSpinner, Panel, SpinnerStyle } from '@/components/terminal';

/**
 * SpinnerShowcase - Demonstrates all 4 Terminal Spinner styles
 *
 * This component can be used:
 * 1. As a reference implementation
 * 2. For visual testing of spinner animations
 * 3. As a component library preview
 */
export const SpinnerShowcase: React.FC = () => {
  const spinnerStyles: Array<{ style: SpinnerStyle; description: string }> = [
    { style: 'arc', description: 'Arc - Rotating corner characters ◜ ◝ ◞ ◟' },
    { style: 'dots', description: 'Dots - Braille dot animation ⠋ ⠙ ⠹ ⠸' },
    { style: 'bar', description: 'Bar - Block height progression ▁ ▂ ▃ ▄' },
    { style: 'block', description: 'Block - Corner block rotation ▖ ▘ ▝ ▗' },
  ];

  return (
    <Panel title="TERMINAL SPINNER SHOWCASE">
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        padding: '20px',
        fontFamily: 'JetBrains Mono, monospace',
      }}>
        {spinnerStyles.map(({ style, description }) => (
          <div key={style} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            padding: '12px',
            borderBottom: '1px solid rgba(255, 149, 0, 0.2)',
          }}>
            <TerminalSpinner style={style} size={32} />
            <div style={{ flex: 1 }}>
              <div style={{
                color: '#ff9500',
                fontWeight: 'bold',
                marginBottom: '4px',
              }}>
                {style.toUpperCase()}
              </div>
              <div style={{
                color: 'rgba(255, 149, 0, 0.6)',
                fontSize: '12px',
              }}>
                {description}
              </div>
            </div>
          </div>
        ))}

        <div style={{ marginTop: '20px' }}>
          <h3 style={{
            color: '#ff9500',
            marginBottom: '16px',
            fontSize: '14px',
            fontWeight: 'bold',
          }}>
            USAGE EXAMPLES
          </h3>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            fontSize: '12px',
            color: 'rgba(255, 149, 0, 0.8)',
          }}>
            {/* Loading state example */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px',
              border: '1px solid rgba(255, 149, 0, 0.3)',
              borderRadius: '4px',
            }}>
              <TerminalSpinner style="arc" size={20} />
              <span>Loading system status...</span>
            </div>

            {/* Processing example */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px',
              border: '1px solid rgba(255, 149, 0, 0.3)',
              borderRadius: '4px',
            }}>
              <TerminalSpinner style="dots" size={20} speed={0.5} />
              <span>Processing query...</span>
            </div>

            {/* Uploading example */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px',
              border: '1px solid rgba(255, 149, 0, 0.3)',
              borderRadius: '4px',
            }}>
              <TerminalSpinner style="bar" size={20} />
              <span>Uploading data chunks...</span>
            </div>

            {/* Initializing example */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px',
              border: '1px solid rgba(255, 149, 0, 0.3)',
              borderRadius: '4px',
            }}>
              <TerminalSpinner style="block" size={20} speed={1.2} />
              <span>Initializing model...</span>
            </div>
          </div>
        </div>
      </div>
    </Panel>
  );
};

/**
 * INTEGRATION GUIDE
 *
 * Import the TerminalSpinner component:
 * ```typescript
 * import { TerminalSpinner } from '@/components/terminal';
 * ```
 *
 * Basic usage:
 * ```typescript
 * <TerminalSpinner style="arc" />
 * ```
 *
 * With customization:
 * ```typescript
 * <TerminalSpinner
 *   style="dots"
 *   size={32}
 *   color="#00ffff"
 *   speed={0.5}
 * />
 * ```
 *
 * In loading states:
 * ```typescript
 * {isLoading && (
 *   <div className="loading-state">
 *     <TerminalSpinner style="arc" size={24} />
 *     <span>Processing...</span>
 *   </div>
 * )}
 * ```
 *
 * PROPS REFERENCE:
 * - style: 'arc' | 'dots' | 'bar' | 'block' (default: 'arc')
 * - size: number in pixels (default: 24)
 * - color: CSS color string (default: '#ff9500')
 * - speed: seconds per full rotation (default: 0.8)
 */
