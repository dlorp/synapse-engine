/**
 * PresetSelector Usage Examples
 *
 * This file demonstrates how to integrate PresetSelector into your Code Chat interface.
 */

import React, { useState } from 'react';
import { PresetSelector } from './PresetSelector';
import { ToolName, ToolModelConfig } from '@/types/codeChat';

// ============================================================================
// Example 1: Basic Usage (Preset Selection Only)
// ============================================================================

export const BasicExample: React.FC = () => {
  const [preset, setPreset] = useState('balanced');

  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <PresetSelector selectedPreset={preset} onPresetChange={setPreset} />

      <p style={{ marginTop: '20px', color: '#ff9500' }}>
        Selected preset: {preset.toUpperCase()}
      </p>
    </div>
  );
};

// ============================================================================
// Example 2: With Per-Tool Overrides
// ============================================================================

export const AdvancedExample: React.FC = () => {
  const [preset, setPreset] = useState('balanced');
  const [overrides, setOverrides] = useState<Partial<Record<ToolName, ToolModelConfig>>>({});

  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <PresetSelector
        selectedPreset={preset}
        onPresetChange={setPreset}
        toolOverrides={overrides}
        onOverrideChange={setOverrides}
      />

      <div style={{ marginTop: '20px', color: '#ff9500' }}>
        <p>Selected preset: {preset.toUpperCase()}</p>
        <p>Overrides: {JSON.stringify(overrides, null, 2)}</p>
      </div>
    </div>
  );
};

// ============================================================================
// Example 3: Integration with Code Chat Form
// ============================================================================

export const CodeChatConfigExample: React.FC = () => {
  const [query, setQuery] = useState('');
  const [workspace, setWorkspace] = useState('/path/to/project');
  const [preset, setPreset] = useState('balanced');
  const [overrides, setOverrides] = useState<Partial<Record<ToolName, ToolModelConfig>>>({});

  const handleSubmit = () => {
    const request = {
      query,
      workspacePath: workspace,
      preset,
      toolOverrides: overrides,
    };
    console.log('Submitting request:', request);
  };

  return (
    <div style={{ padding: '20px', background: '#000', color: '#ff9500' }}>
      <h2>Code Chat Configuration</h2>

      <div style={{ marginBottom: '20px' }}>
        <label>Workspace:</label>
        <input
          type="text"
          value={workspace}
          onChange={(e) => setWorkspace(e.target.value)}
          style={{
            display: 'block',
            width: '100%',
            padding: '8px',
            background: '#000',
            border: '2px solid #ff9500',
            color: '#ff9500',
            fontFamily: 'monospace',
          }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label>Query:</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            display: 'block',
            width: '100%',
            padding: '8px',
            background: '#000',
            border: '2px solid #ff9500',
            color: '#ff9500',
            fontFamily: 'monospace',
            minHeight: '100px',
          }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <PresetSelector
          selectedPreset={preset}
          onPresetChange={setPreset}
          toolOverrides={overrides}
          onOverrideChange={setOverrides}
        />
      </div>

      <button
        onClick={handleSubmit}
        style={{
          padding: '12px 24px',
          background: '#000',
          border: '2px solid #ff9500',
          color: '#ff9500',
          fontFamily: 'monospace',
          cursor: 'pointer',
        }}
      >
        SUBMIT QUERY
      </button>
    </div>
  );
};

// ============================================================================
// Example 4: Controlled Advanced State
// ============================================================================

export const ControlledAdvancedExample: React.FC = () => {
  const [preset, setPreset] = useState('balanced');
  const [showAdvanced] = useState(true); // Controlled externally for demo
  const [overrides, setOverrides] = useState<Partial<Record<ToolName, ToolModelConfig>>>({
    read_file: { tier: 'fast' },
    write_file: { tier: 'powerful' },
  });

  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <PresetSelector
        selectedPreset={preset}
        onPresetChange={setPreset}
        toolOverrides={overrides}
        onOverrideChange={setOverrides}
        showOverrides={showAdvanced} // Advanced controls open by default
      />

      <div style={{ marginTop: '20px' }}>
        <button
          onClick={() => setOverrides({})}
          style={{
            padding: '8px 16px',
            background: '#000',
            border: '1px solid #ff9500',
            color: '#ff9500',
            fontFamily: 'monospace',
            cursor: 'pointer',
          }}
        >
          CLEAR OVERRIDES
        </button>
      </div>
    </div>
  );
};
