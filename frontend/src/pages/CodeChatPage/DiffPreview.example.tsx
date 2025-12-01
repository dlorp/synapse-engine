/**
 * DiffPreview Component Usage Examples
 *
 * This file demonstrates how to use the DiffPreview component
 * in various scenarios within the Code Chat interface.
 */

import React, { useState } from 'react';
import { DiffPreview } from './DiffPreview';
import type { DiffLine } from './DiffPreview';

// ============================================================================
// Example 1: New File Creation
// ============================================================================

export const ExampleNewFile: React.FC = () => {
  const newContent = `import React from 'react';

export const HelloWorld: React.FC = () => {
  return <div>Hello, World!</div>;
};`;

  return (
    <DiffPreview
      filePath="src/components/HelloWorld.tsx"
      originalContent={null}
      newContent={newContent}
      changeType="create"
    />
  );
};

// ============================================================================
// Example 2: File Modification
// ============================================================================

export const ExampleModifiedFile: React.FC = () => {
  const originalContent = `def calculate(x, y):
    return x + y

def validate(data):
    return data is not None`;

  const newContent = `def calculate(x, y):
    # Enhanced calculation with logging
    result = x + y
    logger.debug(f"Result: {result}")
    return result

def validate(data):
    return data is not None`;

  return (
    <DiffPreview
      filePath="src/utils/helper.py"
      originalContent={originalContent}
      newContent={newContent}
      changeType="modify"
    />
  );
};

// ============================================================================
// Example 3: File Deletion
// ============================================================================

export const ExampleDeletedFile: React.FC = () => {
  const originalContent = `// Deprecated utility
export function oldHelper() {
  console.log('This is deprecated');
}`;

  return (
    <DiffPreview
      filePath="src/utils/deprecated.ts"
      originalContent={originalContent}
      newContent=""
      changeType="delete"
    />
  );
};

// ============================================================================
// Example 4: Pre-computed Diff from Server
// ============================================================================

export const ExampleWithServerDiff: React.FC = () => {
  const serverDiff: DiffLine[] = [
    { lineNumber: 1, type: 'context', content: 'import React from "react";' },
    { lineNumber: 2, type: 'context', content: '' },
    { lineNumber: 3, type: 'remove', content: 'export const Button = () => {' },
    { lineNumber: 3, type: 'add', content: 'export const Button: React.FC = () => {' },
    { lineNumber: 4, type: 'add', content: '  // Updated component with TypeScript' },
    { lineNumber: 5, type: 'context', content: '  return <button>Click me</button>;' },
    { lineNumber: 6, type: 'context', content: '};' },
  ];

  return (
    <DiffPreview
      filePath="src/components/Button.tsx"
      originalContent="" // Not needed when diffLines provided
      newContent="" // Not needed when diffLines provided
      changeType="modify"
      diffLines={serverDiff}
    />
  );
};

// ============================================================================
// Example 5: With Close Button
// ============================================================================

export const ExampleWithCloseButton: React.FC = () => {
  const [isVisible, setIsVisible] = useState(true);

  const newContent = `console.log('New feature added');`;

  if (!isVisible) {
    return <div>Diff preview closed</div>;
  }

  return (
    <DiffPreview
      filePath="src/features/new-feature.js"
      originalContent={null}
      newContent={newContent}
      changeType="create"
      onClose={() => setIsVisible(false)}
    />
  );
};

// ============================================================================
// Example 6: Integration in CodeChatPage
// ============================================================================

export const ExampleCodeChatIntegration: React.FC = () => {
  // Simulated ReAct step with file changes
  const fileChanges = [
    {
      filePath: 'src/api/endpoints.ts',
      originalContent: `export const API_URL = '/api';`,
      newContent: `export const API_URL = '/api';
export const WS_URL = '/ws';`,
      changeType: 'modify' as const,
    },
    {
      filePath: 'src/types/websocket.ts',
      originalContent: null,
      newContent: `export interface WSMessage {
  type: string;
  payload: unknown;
}`,
      changeType: 'create' as const,
    },
  ];

  return (
    <div>
      <h3>File Changes in ReAct Step #3</h3>
      {fileChanges.map((change, index) => (
        <DiffPreview
          key={index}
          filePath={change.filePath}
          originalContent={change.originalContent}
          newContent={change.newContent}
          changeType={change.changeType}
        />
      ))}
    </div>
  );
};

// ============================================================================
// Example 7: Large Diff with Scrolling
// ============================================================================

export const ExampleLargeDiff: React.FC = () => {
  const originalLines = Array.from({ length: 50 }, (_, i) => `line ${i + 1}`);
  const newLines = [...originalLines];
  newLines.splice(10, 0, 'inserted line A', 'inserted line B');
  newLines.splice(25, 1);
  newLines[30] = 'modified line';

  return (
    <DiffPreview
      filePath="src/data/large-file.txt"
      originalContent={originalLines.join('\n')}
      newContent={newLines.join('\n')}
      changeType="modify"
    />
  );
};
