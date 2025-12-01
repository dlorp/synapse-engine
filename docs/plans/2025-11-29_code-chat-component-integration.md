# Code Chat Component Integration Plan

**Date:** 2025-11-29
**Status:** Implementation Plan
**Estimated Time:** 1-2 hours

---

## Executive Summary

The CodeChatPage (`/code-chat`) is currently showing placeholder modals for the WorkspaceSelector and ContextSelector instead of using the actual components that were built in Session 4. The page also uses a basic `<select>` dropdown for presets instead of the more feature-rich `PresetSelector` component with tool override support.

**Key Issues:**
1. Lines 336-352: WorkspaceSelector modal shows placeholder content
2. Lines 355-372: ContextSelector modal shows placeholder content
3. Lines 217-229: Uses basic `<select>` instead of `PresetSelector` component
4. Missing state setters for `workspacePath` and `contextName` (currently destructured without setters)
5. `DiffPreview` component built but not integrated (awaiting backend diff events)

**Solution:**
Replace placeholder modals with actual components and wire up the state management.

---

## Related Documentation

- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Session 4 development context
- [SESSION4_PLAN.md](./SESSION4_PLAN.md) - Original Session 4 implementation plan
- [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) - Feature specification
- [codeChat.ts](../../frontend/src/types/codeChat.ts) - TypeScript types

---

## Current State Analysis

### CodeChatPage.tsx (Lines 336-372) - Placeholder Modals

```tsx
{/* Modal Placeholders (Phase 2) */}
{showWorkspaceSelector && (
  <div
    className={styles.modalPlaceholder}
    onClick={() => setShowWorkspaceSelector(false)}
    role="dialog"
    aria-label="Workspace Selector Modal"
  >
    <div className={styles.modalContent}>
      <AsciiPanel title="WORKSPACE SELECTOR [PLACEHOLDER]">
        <p>WorkspaceSelector component will be implemented in Phase 2.</p>
        <p>For now, manually set workspace path in config.</p>
        <Button onClick={() => setShowWorkspaceSelector(false)}>
          CLOSE
        </Button>
      </AsciiPanel>
    </div>
  </div>
)}
```

### Actual WorkspaceSelector Component (298 lines)

The component is fully built with:
- Props: `currentWorkspace: string`, `onSelect: (path: string) => void`, `onClose: () => void`
- TUI file browser with directory navigation
- Project type detection (Python, Node, Rust, Go)
- Git repository indicators
- Workspace metadata display
- Keyboard navigation (ESC to close, Enter to select)

### Actual ContextSelector Component (277 lines)

The component is fully built with:
- Props: `selectedContext: string | null`, `onSelect: (contextName: string | null) => void`, `onClose: () => void`
- Radio button selection with ASCII indicators
- Context metadata (chunk count, last indexed)
- "None" option for clearing context
- Refresh functionality for re-indexing

### PresetSelector Component (172 lines)

The component is fully built with:
- Props: `selectedPreset: string`, `onPresetChange: (preset: string) => void`, `toolOverrides?`, `onOverrideChange?`
- Compact preset dropdown
- Optional per-tool tier overrides (collapsible advanced section)
- Terminal aesthetic styling

---

## Implementation Plan

### Phase 1: Fix State Management (Lines 39-43)

**File:** `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/CodeChatPage.tsx`

**Current Code (Lines 39-43):**
```tsx
/** Selected workspace directory path */
const [workspacePath] = useState<string>('');

/** Selected CGRAG context name */
const [contextName] = useState<string | null>(null);
```

**New Code:**
```tsx
/** Selected workspace directory path */
const [workspacePath, setWorkspacePath] = useState<string>('');

/** Selected CGRAG context name */
const [contextName, setContextName] = useState<string | null>(null);
```

**Rationale:** The state setters are needed to actually update the selected workspace and context from the modal components.

---

### Phase 2: Add Component Imports (Lines 18-19)

**File:** `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/CodeChatPage.tsx`

**Current Code (Lines 18-19):**
```tsx
import { ReActStepViewer } from './ReActStepViewer';
import { useCodeChat } from '@/hooks/useCodeChat';
```

**New Code:**
```tsx
import { ReActStepViewer } from './ReActStepViewer';
import { WorkspaceSelector } from './WorkspaceSelector';
import { ContextSelector } from './ContextSelector';
import { PresetSelector } from './PresetSelector';
import { useCodeChat } from '@/hooks/useCodeChat';
```

**Rationale:** Import the actual components that were built in Session 4.

---

### Phase 3: Add Tool Override State (After Line 56)

**File:** `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/CodeChatPage.tsx`

**Add after line 56 (after `const [showContextSelector, setShowContextSelector] = useState(false);`):**

```tsx
/** Per-tool model tier overrides */
const [toolOverrides, setToolOverrides] = useState<Partial<Record<ToolName, ToolModelConfig>>>({});
```

**Also add to imports at top (line 22):**
```tsx
import type { AgentState, CodeChatRequest, ToolName, ToolModelConfig } from '@/types/codeChat';
```

**Rationale:** The PresetSelector component supports per-tool overrides which need state management.

---

### Phase 4: Replace WorkspaceSelector Placeholder (Lines 336-352)

**File:** `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/CodeChatPage.tsx`

**Current Code (Lines 336-352):**
```tsx
{showWorkspaceSelector && (
  <div
    className={styles.modalPlaceholder}
    onClick={() => setShowWorkspaceSelector(false)}
    role="dialog"
    aria-label="Workspace Selector Modal"
  >
    <div className={styles.modalContent}>
      <AsciiPanel title="WORKSPACE SELECTOR [PLACEHOLDER]">
        <p>WorkspaceSelector component will be implemented in Phase 2.</p>
        <p>For now, manually set workspace path in config.</p>
        <Button onClick={() => setShowWorkspaceSelector(false)}>
          CLOSE
        </Button>
      </AsciiPanel>
    </div>
  </div>
)}
```

**New Code:**
```tsx
{showWorkspaceSelector && (
  <WorkspaceSelector
    currentWorkspace={workspacePath}
    onSelect={setWorkspacePath}
    onClose={() => setShowWorkspaceSelector(false)}
  />
)}
```

**Rationale:** The WorkspaceSelector component handles all modal styling, overlay behavior, and keyboard events internally. No wrapper div needed.

---

### Phase 5: Replace ContextSelector Placeholder (Lines 354-372)

**File:** `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/CodeChatPage.tsx`

**Current Code (Lines 354-372):**
```tsx
{showContextSelector && (
  <div
    className={styles.modalPlaceholder}
    onClick={() => setShowContextSelector(false)}
    role="dialog"
    aria-label="Context Selector Modal"
  >
    <div className={styles.modalContent}>
      <AsciiPanel title="CONTEXT SELECTOR [PLACEHOLDER]">
        <p>ContextSelector component will be implemented in Phase 2.</p>
        <p>For now, manually set context name in config.</p>
        <Button onClick={() => setShowContextSelector(false)}>
          CLOSE
        </Button>
      </AsciiPanel>
    </div>
  </div>
)}
```

**New Code:**
```tsx
{showContextSelector && (
  <ContextSelector
    selectedContext={contextName}
    onSelect={setContextName}
    onClose={() => setShowContextSelector(false)}
  />
)}
```

**Rationale:** The ContextSelector component handles all modal styling, overlay behavior, and keyboard events internally. No wrapper div needed.

---

### Phase 6: Replace Preset Select with PresetSelector (Lines 213-241)

**File:** `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/CodeChatPage.tsx`

**Current Code (Lines 213-241):**
```tsx
{/* Preset Selection */}
<div className={styles.configRow}>
  <label className={styles.configLabel}>PRESET:</label>
  <div className={styles.configValue}>
    <select
      value={preset}
      onChange={(e) => setPreset(e.target.value)}
      disabled={isLoading || presetsLoading}
      className={styles.presetSelect}
    >
      {presetsLoading && <option>Loading...</option>}
      {presets?.map((p) => (
        <option key={p.name} value={p.name}>
          {p.name.toUpperCase()} - {p.description}
        </option>
      ))}
    </select>
    <label className={styles.checkboxLabel}>
      <input
        type="checkbox"
        checked={useWebSearch}
        onChange={(e) => setUseWebSearch(e.target.checked)}
        disabled={isLoading}
        className={styles.checkbox}
      />
      WEB SEARCH
    </label>
  </div>
</div>
```

**New Code:**
```tsx
{/* Preset Selection */}
<div className={styles.configRow}>
  <label className={styles.configLabel}>PRESET:</label>
  <div className={styles.configValue}>
    <PresetSelector
      selectedPreset={preset}
      onPresetChange={setPreset}
      toolOverrides={toolOverrides}
      onOverrideChange={setToolOverrides}
    />
    <label className={styles.checkboxLabel}>
      <input
        type="checkbox"
        checked={useWebSearch}
        onChange={(e) => setUseWebSearch(e.target.checked)}
        disabled={isLoading}
        className={styles.checkbox}
      />
      WEB SEARCH
    </label>
  </div>
</div>
```

**Rationale:** The PresetSelector component provides the same dropdown functionality plus optional per-tool override controls. The component is self-contained and handles its own disabled states via parent isLoading prop (we may want to add this prop to PresetSelector in a future enhancement).

---

### Phase 7: Update CodeChatRequest to Include Tool Overrides (Line 103-111)

**File:** `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/CodeChatPage.tsx`

**Current Code (Lines 103-111):**
```tsx
const request: CodeChatRequest = {
  query: query.trim(),
  workspacePath,
  contextName,
  useCgrag,
  useWebSearch,
  preset,
  maxIterations: 10,
};
```

**New Code:**
```tsx
const request: CodeChatRequest = {
  query: query.trim(),
  workspacePath,
  contextName,
  useCgrag,
  useWebSearch,
  preset,
  toolOverrides: Object.keys(toolOverrides).length > 0 ? toolOverrides : undefined,
  maxIterations: 10,
};
```

**Rationale:** Pass tool overrides to the backend when the user has customized per-tool model tiers.

---

### Phase 8: Remove Unused Presets Hook (Optional Cleanup)

After integrating the PresetSelector, the `presetsLoading` variable on line 79 is no longer needed for the select disabled state, but the `usePresets` hook may still be useful if we want to display preset descriptions elsewhere. For now, we can keep it.

However, note that the PresetSelector component has its own hardcoded PRESETS list. If we want dynamic presets from the backend, we would need to modify PresetSelector to accept a `presets` prop.

---

## Complete Modified Code

Here is the complete modified `CodeChatPage.tsx`:

```tsx
/**
 * CodeChatPage Component - Agentic Code Assistant with ReAct Loop Visualization
 *
 * Multi-model orchestrated coding assistant with:
 * - Workspace and context selection
 * - Real-time ReAct step visualization
 * - Tool execution tracking
 * - Markdown-rendered final answers
 *
 * This page provides a terminal-aesthetic interface for the Code Chat mode,
 * displaying the agent's reasoning process (thoughts), tool executions (actions),
 * and observations in real-time as they stream from the backend.
 */

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { CRTMonitor, AsciiPanel, Button } from '@/components/terminal';
import { ReActStepViewer } from './ReActStepViewer';
import { WorkspaceSelector } from './WorkspaceSelector';
import { ContextSelector } from './ContextSelector';
import { PresetSelector } from './PresetSelector';
import { useCodeChat } from '@/hooks/useCodeChat';
import { useWorkspaceValidation } from '@/hooks/useWorkspaces';
import { usePresets } from '@/hooks/usePresets';
import type { AgentState, CodeChatRequest, ToolName, ToolModelConfig } from '@/types/codeChat';
import styles from './CodeChatPage.module.css';

/**
 * Main Code Chat page component.
 *
 * Manages configuration state (workspace, context, preset), query submission,
 * and real-time ReAct step visualization from the streaming API.
 */
export const CodeChatPage: React.FC = () => {
  // ============================================================================
  // Local State
  // ============================================================================

  /** User's query input */
  const [query, setQuery] = useState('');

  /** Selected workspace directory path */
  const [workspacePath, setWorkspacePath] = useState<string>('');

  /** Selected CGRAG context name */
  const [contextName, setContextName] = useState<string | null>(null);

  /** Selected preset (balanced, coding, quality, etc.) */
  const [preset, setPreset] = useState<string>('balanced');

  /** Per-tool model tier overrides */
  const [toolOverrides, setToolOverrides] = useState<Partial<Record<ToolName, ToolModelConfig>>>({});

  /** Enable CGRAG context retrieval */
  const [useCgrag, setUseCgrag] = useState(false);

  /** Enable web search */
  const [useWebSearch, setUseWebSearch] = useState(false);

  /** Modal visibility state */
  const [showWorkspaceSelector, setShowWorkspaceSelector] = useState(false);
  const [showContextSelector, setShowContextSelector] = useState(false);

  // ============================================================================
  // Hooks
  // ============================================================================

  /** Code Chat streaming hook */
  const {
    steps,
    currentState,
    answer,
    error,
    context,
    isLoading,
    submit,
    cancel,
    reset,
  } = useCodeChat();

  /** Workspace validation hook */
  const { data: workspaceInfo } = useWorkspaceValidation(workspacePath);

  /** Presets hook (kept for potential future use) */
  const { data: _presets } = usePresets();

  // ============================================================================
  // Computed State
  // ============================================================================

  /** Whether agent is currently active (planning, executing, or observing) */
  const isActive = ['planning', 'executing', 'observing'].includes(currentState);

  /** Whether submit button should be enabled */
  const canSubmit = query.trim().length > 0 && workspacePath.length > 0 && !isLoading;

  // ============================================================================
  // Event Handlers
  // ============================================================================

  /**
   * Handle query submission.
   *
   * Validates configuration and submits query to the Code Chat API via SSE.
   */
  const handleSubmit = async () => {
    if (!canSubmit) return;

    const request: CodeChatRequest = {
      query: query.trim(),
      workspacePath,
      contextName,
      useCgrag,
      useWebSearch,
      preset,
      toolOverrides: Object.keys(toolOverrides).length > 0 ? toolOverrides : undefined,
      maxIterations: 10,
    };

    await submit(request);
  };

  /**
   * Handle cancel button click.
   *
   * Aborts the current query and notifies the backend.
   */
  const handleCancel = () => {
    cancel();
  };

  /**
   * Handle reset button click.
   *
   * Clears all steps, answer, and error state for a new query.
   */
  const handleReset = () => {
    reset();
    setQuery('');
  };

  /**
   * Get CSS class for current agent state.
   */
  const getStateClass = (state: AgentState): string => {
    const stateKey = `state${state.charAt(0).toUpperCase() + state.slice(1)}` as keyof typeof styles;
    return (styles[stateKey] as string | undefined) || (styles.stateIdle as string) || '';
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <CRTMonitor bloomIntensity={0.3} scanlinesEnabled curvatureEnabled>
      <div className={styles.page}>
        {/* Configuration Panel */}
        <AsciiPanel title="CODE CHAT CONFIGURATION">
          <div className={styles.configPanel}>
            {/* Workspace Selection */}
            <div className={styles.configRow}>
              <label className={styles.configLabel}>WORKSPACE:</label>
              <div className={styles.configValue}>
                {workspacePath ? (
                  <>
                    <span className={styles.workspacePath}>{workspacePath}</span>
                    {workspaceInfo?.valid && workspaceInfo.projectInfo && (
                      <span className={styles.projectType}>
                        [{workspaceInfo.projectInfo.type.toUpperCase()}]
                      </span>
                    )}
                    {workspaceInfo?.isGitRepo && (
                      <span className={styles.gitIndicator}>[GIT]</span>
                    )}
                  </>
                ) : (
                  <span className={styles.notSelected}>NOT SELECTED</span>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowWorkspaceSelector(true)}
                  disabled={isLoading}
                >
                  SELECT
                </Button>
              </div>
            </div>

            {/* Context Selection */}
            <div className={styles.configRow}>
              <label className={styles.configLabel}>CONTEXT:</label>
              <div className={styles.configValue}>
                {contextName ? (
                  <span className={styles.contextName}>{contextName}</span>
                ) : (
                  <span className={styles.notSelected}>NONE</span>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowContextSelector(true)}
                  disabled={isLoading}
                >
                  SELECT
                </Button>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={useCgrag}
                    onChange={(e) => setUseCgrag(e.target.checked)}
                    disabled={!contextName || isLoading}
                    className={styles.checkbox}
                  />
                  USE CGRAG
                </label>
              </div>
            </div>

            {/* Preset Selection */}
            <div className={styles.configRow}>
              <label className={styles.configLabel}>PRESET:</label>
              <div className={styles.configValue}>
                <PresetSelector
                  selectedPreset={preset}
                  onPresetChange={setPreset}
                  toolOverrides={toolOverrides}
                  onOverrideChange={setToolOverrides}
                />
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={useWebSearch}
                    onChange={(e) => setUseWebSearch(e.target.checked)}
                    disabled={isLoading}
                    className={styles.checkbox}
                  />
                  WEB SEARCH
                </label>
              </div>
            </div>
          </div>
        </AsciiPanel>

        {/* State Indicator Bar */}
        <div className={styles.stateBar}>
          <div className={styles.stateIndicator}>
            <span className={getStateClass(currentState)}>
              [{currentState.toUpperCase()}]
            </span>
            {steps.length > 0 && (
              <span className={styles.stepCount}>STEP {steps.length}</span>
            )}
          </div>
          <div className={styles.stateActions}>
            {isActive && (
              <Button onClick={handleCancel} variant="danger" size="sm">
                CANCEL
              </Button>
            )}
            {(currentState === 'completed' || currentState === 'error' || currentState === 'cancelled') && (
              <Button onClick={handleReset} variant="secondary" size="sm">
                RESET
              </Button>
            )}
          </div>
        </div>

        {/* Query Input */}
        <AsciiPanel title="QUERY">
          <div className={styles.inputSection}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your coding task or question..."
              disabled={isLoading}
              className={styles.queryTextarea}
              rows={4}
              aria-label="Code Chat query input"
            />
            <div className={styles.inputActions}>
              <Button
                onClick={handleSubmit}
                disabled={!canSubmit}
                variant="primary"
              >
                EXECUTE
              </Button>
            </div>
          </div>
        </AsciiPanel>

        {/* Error Display */}
        {error && (
          <AsciiPanel title="ERROR" variant="error">
            <div className={styles.errorMessage}>
              <pre>{error}</pre>
            </div>
          </AsciiPanel>
        )}

        {/* CGRAG Context Display */}
        {context && (
          <AsciiPanel title="RETRIEVED CONTEXT">
            <div className={styles.contextPreview}>
              <pre className={styles.contextText}>{context.slice(0, 500)}...</pre>
            </div>
          </AsciiPanel>
        )}

        {/* ReAct Steps Container */}
        {steps.length > 0 && (
          <div className={styles.stepsContainer}>
            <AsciiPanel title="REACT EXECUTION TRACE">
              <div className={styles.stepsInner}>
                {steps.map((step) => (
                  <ReActStepViewer key={step.stepNumber} step={step} />
                ))}
              </div>
            </AsciiPanel>
          </div>
        )}

        {/* Final Answer */}
        {answer && (
          <AsciiPanel title="ANSWER" variant="accent">
            <div className={styles.answerPanel}>
              <ReactMarkdown>
                {answer}
              </ReactMarkdown>
            </div>
          </AsciiPanel>
        )}

        {/* Modal Components */}
        {showWorkspaceSelector && (
          <WorkspaceSelector
            currentWorkspace={workspacePath}
            onSelect={setWorkspacePath}
            onClose={() => setShowWorkspaceSelector(false)}
          />
        )}

        {showContextSelector && (
          <ContextSelector
            selectedContext={contextName}
            onSelect={setContextName}
            onClose={() => setShowContextSelector(false)}
          />
        )}
      </div>
    </CRTMonitor>
  );
};

CodeChatPage.displayName = 'CodeChatPage';
```

---

## Testing Checklist

After implementing the changes:

- [ ] Navigate to `/code-chat` route
- [ ] Click "SELECT" button for workspace - verify WorkspaceSelector modal opens
- [ ] Browse directories in WorkspaceSelector
- [ ] Select a workspace - verify path updates in main UI
- [ ] Press ESC - verify modal closes
- [ ] Click "SELECT" button for context - verify ContextSelector modal opens
- [ ] Select a context - verify context name updates in main UI
- [ ] Select "None" option - verify context is cleared
- [ ] Verify preset dropdown works with PresetSelector
- [ ] Toggle "Show per-tool overrides" checkbox in PresetSelector
- [ ] Change per-tool tier settings
- [ ] Submit a query with workspace selected
- [ ] Verify tool overrides are sent in request (check Network tab)
- [ ] Verify ReAct steps display correctly
- [ ] Verify cancel and reset buttons work

---

## Files Modified Summary

### Update:
- `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/CodeChatPage.tsx`
  - Line 18-19: Add imports for WorkspaceSelector, ContextSelector, PresetSelector
  - Line 22: Update type imports to include ToolName, ToolModelConfig
  - Lines 39-43: Add setters to workspacePath and contextName state
  - After line 56: Add toolOverrides state
  - Lines 103-111: Add toolOverrides to CodeChatRequest
  - Lines 213-241: Replace basic select with PresetSelector component
  - Lines 336-352: Replace placeholder with actual WorkspaceSelector
  - Lines 354-372: Replace placeholder with actual ContextSelector

### No Changes Needed:
- `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/WorkspaceSelector.tsx` - Already complete
- `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/ContextSelector.tsx` - Already complete
- `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/PresetSelector.tsx` - Already complete
- `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/ReActStepViewer.tsx` - Already integrated
- `${PROJECT_DIR}/frontend/src/pages/CodeChatPage/DiffPreview.tsx` - Built but not yet integrated (awaiting backend diff events)

---

## Future Enhancements

1. **DiffPreview Integration:** Once the backend sends `diff_preview` events, add a `diffs` state array and render DiffPreview components for file changes.

2. **Dynamic Presets:** Modify PresetSelector to accept presets from the usePresets hook instead of hardcoded PRESETS array.

3. **Disabled State for PresetSelector:** Add `disabled` prop to PresetSelector component to disable during loading.

4. **Workspace History:** Add recent workspaces to localStorage for quick selection.

5. **Context Auto-Enable:** Automatically enable "USE CGRAG" checkbox when a context is selected.
