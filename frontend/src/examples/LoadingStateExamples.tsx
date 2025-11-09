import React from 'react';
import { TerminalSpinner, Panel } from '@/components/terminal';

/**
 * LoadingStateExamples - Practical examples of TerminalSpinner usage
 *
 * These patterns can be copied directly into production components
 */

// Example 1: Simple loading state
export const SimpleLoadingExample: React.FC = () => {
  const [isLoading, setIsLoading] = React.useState(true);

  return (
    <div style={{ padding: '20px', fontFamily: 'JetBrains Mono, monospace' }}>
      {isLoading ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: '#ff9500',
        }}>
          <TerminalSpinner style="arc" size={20} />
          <span>Loading system status...</span>
        </div>
      ) : (
        <div style={{ color: '#00ff00' }}>✓ System ready</div>
      )}
    </div>
  );
};

// Example 2: Multi-stage loading with different spinners
export const MultiStageLoadingExample: React.FC = () => {
  const [stage, setStage] = React.useState<'idle' | 'connecting' | 'processing' | 'complete'>('connecting');

  return (
    <Panel title="QUERY PROCESSING">
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        padding: '20px',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: '14px',
      }}>
        {/* Stage 1: Connecting */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: stage === 'connecting' ? '#ff9500' : '#555',
        }}>
          {stage === 'connecting' && <TerminalSpinner style="dots" size={16} speed={0.5} />}
          {stage === 'connecting' ? '●' : '✓'} Connecting to model...
        </div>

        {/* Stage 2: Processing */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: stage === 'processing' ? '#ff9500' : stage === 'complete' ? '#00ff00' : '#555',
        }}>
          {stage === 'processing' && <TerminalSpinner style="bar" size={16} />}
          {stage === 'complete' ? '✓' : stage === 'processing' ? '●' : '○'} Processing query...
        </div>

        {/* Stage 3: Complete */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: stage === 'complete' ? '#00ff00' : '#555',
        }}>
          {stage === 'complete' ? '✓' : '○'} Response ready
        </div>
      </div>
    </Panel>
  );
};

// Example 3: Inline spinner in status bar
export const StatusBarExample: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      padding: '12px 20px',
      background: 'rgba(255, 149, 0, 0.1)',
      borderBottom: '1px solid #ff9500',
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: '12px',
      color: '#ff9500',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <TerminalSpinner style="block" size={14} />
        <span>CGRAG INDEX: UPDATING</span>
      </div>

      <div>
        <span style={{ opacity: 0.6 }}>UPTIME: 02:34:12</span>
      </div>
    </div>
  );
};

// Example 4: Model initialization grid
export const ModelGridExample: React.FC = () => {
  const models = [
    { name: 'Q2_FAST_1', status: 'active' },
    { name: 'Q2_FAST_2', status: 'initializing' },
    { name: 'Q3_BALANCED', status: 'idle' },
    { name: 'Q4_POWERFUL', status: 'initializing' },
  ];

  return (
    <Panel title="MODEL SUBSTRATE STATUS">
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '16px',
        padding: '20px',
        fontFamily: 'JetBrains Mono, monospace',
      }}>
        {models.map((model) => (
          <div
            key={model.name}
            style={{
              padding: '16px',
              border: '1px solid rgba(255, 149, 0, 0.3)',
              borderRadius: '4px',
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px',
            }}>
              <span style={{
                fontWeight: 'bold',
                color: '#ff9500',
                fontSize: '14px',
              }}>
                {model.name}
              </span>
              {model.status === 'initializing' && (
                <TerminalSpinner style="arc" size={16} />
              )}
              {model.status === 'active' && (
                <span style={{ color: '#00ff00' }}>●</span>
              )}
              {model.status === 'idle' && (
                <span style={{ color: '#555' }}>○</span>
              )}
            </div>
            <div style={{
              fontSize: '12px',
              color: 'rgba(255, 149, 0, 0.6)',
            }}>
              {model.status === 'initializing' && 'Initializing...'}
              {model.status === 'active' && 'Ready'}
              {model.status === 'idle' && 'Idle'}
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
};

// Example 5: Data fetch with retry
export const DataFetchExample: React.FC = () => {
  const [status, setStatus] = React.useState<'loading' | 'error' | 'success'>('loading');
  const [retryCount, setRetryCount] = React.useState(0);

  return (
    <div style={{
      padding: '20px',
      fontFamily: 'JetBrains Mono, monospace',
    }}>
      {status === 'loading' && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: '#ff9500',
        }}>
          <TerminalSpinner style="dots" size={20} speed={0.6} />
          <div>
            <div>Fetching metrics data...</div>
            {retryCount > 0 && (
              <div style={{
                fontSize: '12px',
                color: 'rgba(255, 149, 0, 0.6)',
                marginTop: '4px',
              }}>
                Retry attempt {retryCount}/3
              </div>
            )}
          </div>
        </div>
      )}

      {status === 'error' && (
        <div style={{ color: '#ff0000' }}>
          ✗ Failed to fetch data
        </div>
      )}

      {status === 'success' && (
        <div style={{ color: '#00ff00' }}>
          ✓ Data loaded successfully
        </div>
      )}
    </div>
  );
};

// Example 6: Custom colored spinner
export const CustomColorExample: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      gap: '24px',
      padding: '20px',
      fontFamily: 'JetBrains Mono, monospace',
    }}>
      {/* Orange (default) */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
      }}>
        <TerminalSpinner style="arc" size={32} color="#ff9500" />
        <span style={{ fontSize: '12px', color: '#ff9500' }}>Standard</span>
      </div>

      {/* Cyan (accent) */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
      }}>
        <TerminalSpinner style="dots" size={32} color="#00ffff" />
        <span style={{ fontSize: '12px', color: '#00ffff' }}>Accent</span>
      </div>

      {/* Red (error) */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
      }}>
        <TerminalSpinner style="bar" size={32} color="#ff0000" />
        <span style={{ fontSize: '12px', color: '#ff0000' }}>Error</span>
      </div>

      {/* Green (success) */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
      }}>
        <TerminalSpinner style="block" size={32} color="#00ff00" />
        <span style={{ fontSize: '12px', color: '#00ff00' }}>Success</span>
      </div>
    </div>
  );
};

/**
 * USAGE PATTERNS SUMMARY
 *
 * 1. Simple Loading State:
 *    - Use 'arc' style for general purpose
 *    - Size 20-24px for inline text
 *    - Default phosphor orange color
 *
 * 2. Multi-Stage Processing:
 *    - Different spinner for each stage
 *    - 'dots' for fast operations
 *    - 'bar' for data-heavy operations
 *    - 'block' for system initialization
 *
 * 3. Status Indicators:
 *    - Small size (14-16px) for compact areas
 *    - Slower speed (1.0-1.2s) for less distraction
 *    - Match color to status severity
 *
 * 4. Model Management:
 *    - 'arc' style for model initialization
 *    - Position in corner of card
 *    - Combine with status text
 *
 * 5. Error States:
 *    - Show retry count with spinner
 *    - Use 'dots' for retry operations
 *    - Speed 0.6s for urgency indication
 *
 * 6. Custom Branding:
 *    - Cyan (#00ffff) for accent operations
 *    - Red (#ff0000) for critical operations
 *    - Green (#00ff00) for success confirmations
 */
