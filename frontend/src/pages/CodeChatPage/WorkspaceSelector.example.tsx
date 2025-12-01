/**
 * WorkspaceSelector Usage Example
 *
 * This example shows how to integrate WorkspaceSelector into a Code Chat page.
 * Demonstrates state management, modal toggling, and workspace selection.
 */

import React, { useState } from 'react';
import { WorkspaceSelector } from './WorkspaceSelector';
import { Button } from '@/components/terminal/Button/Button';

export const WorkspaceSelectorExample: React.FC = () => {
  const [workspace, setWorkspace] = useState<string>('');
  const [showSelector, setShowSelector] = useState(false);

  const handleSelectWorkspace = (path: string) => {
    setWorkspace(path);
    console.log('Selected workspace:', path);
    // Additional logic: validate workspace, load CGRAG index, etc.
  };

  return (
    <div style={{ padding: '20px' }}>
      {/* Workspace display */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
          CURRENT WORKSPACE:
        </div>
        <div style={{ color: 'var(--text-primary)', fontSize: '14px' }}>
          {workspace || 'None selected'}
        </div>
      </div>

      {/* Button to open selector */}
      <Button onClick={() => setShowSelector(true)}>
        BROWSE WORKSPACES
      </Button>

      {/* Workspace selector modal */}
      {showSelector && (
        <WorkspaceSelector
          currentWorkspace={workspace}
          onSelect={handleSelectWorkspace}
          onClose={() => setShowSelector(false)}
        />
      )}
    </div>
  );
};

/**
 * Integration with Code Chat Configuration
 */
export const CodeChatIntegrationExample: React.FC = () => {
  const [config, setConfig] = useState({
    workspace: '',
    contextName: null as string | null,
    preset: 'balanced',
  });

  const [showWorkspaceSelector, setShowWorkspaceSelector] = useState(false);

  const handleWorkspaceSelect = (path: string) => {
    setConfig(prev => ({
      ...prev,
      workspace: path,
    }));

    // Auto-detect CGRAG index for workspace
    // This would call useWorkspaceValidation and check hasCgragIndex
    console.log('Workspace selected:', path);
  };

  return (
    <div>
      {/* Configuration panel */}
      <div style={{ padding: '20px', backgroundColor: '#0a0a0a' }}>
        <h3 style={{ color: 'var(--text-primary)' }}>CODE CHAT CONFIG</h3>

        {/* Workspace field */}
        <div style={{ marginBottom: '15px' }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
            Workspace:
          </label>
          <div style={{ display: 'flex', gap: '10px', marginTop: '5px' }}>
            <input
              type="text"
              value={config.workspace}
              readOnly
              placeholder="No workspace selected"
              style={{
                flex: 1,
                backgroundColor: '#050505',
                border: '1px solid #ff950066',
                color: '#ff9500',
                padding: '8px',
                fontFamily: 'monospace',
              }}
            />
            <Button
              onClick={() => setShowWorkspaceSelector(true)}
              variant="secondary"
            >
              BROWSE
            </Button>
          </div>
        </div>

        {/* Other config fields (preset, context, etc.) */}
      </div>

      {/* Workspace selector */}
      {showWorkspaceSelector && (
        <WorkspaceSelector
          currentWorkspace={config.workspace}
          onSelect={handleWorkspaceSelect}
          onClose={() => setShowWorkspaceSelector(false)}
        />
      )}
    </div>
  );
};
