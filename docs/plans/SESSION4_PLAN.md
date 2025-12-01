# Code Chat Mode - Session 4: Frontend UI Implementation Plan

**Date:** 2025-11-29
**Status:** Ready for Implementation
**Session:** 4 of 5
**Estimated Time:** 10-14 hours

---

## Executive Summary

Session 4 focuses on implementing the frontend UI components for Code Chat mode. Building on the foundation from Sessions 1-3 (backend models, tools, agent, and hooks), we will create the complete user interface including the main page, modal selectors, ReAct step visualization, and diff preview components.

**Key Deliverables:**
- CodeChatPage.tsx - Main page with configuration panel and chat interface
- WorkspaceSelector.tsx - TUI file browser modal for workspace selection
- ContextSelector.tsx - CGRAG index picker modal
- ReActStepViewer.tsx - Step-by-step agent visualization
- DiffPreview.tsx - File diff display component
- PresetSelector.tsx - Preset dropdown with override controls
- Complete CSS modules with terminal aesthetic

---

## Related Documentation

- [CODE_CHAT_IMPLEMENTATION.md](./CODE_CHAT_IMPLEMENTATION.md) - Full implementation specification
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Development history and context
- [CLAUDE.md](../../CLAUDE.md) - Project guidelines and patterns
- [tokens.css](../../frontend/src/assets/styles/tokens.css) - Design system variables

### Session 3 Artifacts (Dependencies)
- [codeChat.ts](../../frontend/src/types/codeChat.ts) - TypeScript types (370 lines)
- [useCodeChat.ts](../../frontend/src/hooks/useCodeChat.ts) - SSE streaming hook (312 lines)
- [useContexts.ts](../../frontend/src/hooks/useContexts.ts) - CGRAG context hooks (150 lines)
- [useWorkspaces.ts](../../frontend/src/hooks/useWorkspaces.ts) - Workspace hooks (100 lines)
- [usePresets.ts](../../frontend/src/hooks/usePresets.ts) - Preset management hooks (86 lines)
- [endpoints.ts](../../frontend/src/api/endpoints.ts) - API endpoint definitions

### Existing UI Patterns to Follow
- [AsciiPanel.tsx](../../frontend/src/components/terminal/AsciiPanel/AsciiPanel.tsx) - Panel container with title bar
- [Button.tsx](../../frontend/src/components/terminal/Button/Button.tsx) - Terminal-styled buttons
- [Input.tsx](../../frontend/src/components/terminal/Input/Input.tsx) - Form inputs
- [StatusIndicator.tsx](../../frontend/src/components/terminal/StatusIndicator/StatusIndicator.tsx) - Status dots and labels
- [HomePage.tsx](../../frontend/src/pages/HomePage/HomePage.tsx) - Page layout patterns

---

## Agent Consultations

### @frontend-engineer
**File:** [frontend-engineer.md](../../.claude/agents/frontend-engineer.md)
**Query:** "Component architecture and data flow patterns for Code Chat page"
**Key Insights:**
- Use TanStack Query for server state (already implemented in hooks)
- Implement proper loading/error states with existing terminal components
- Memoize expensive computations with useMemo/useCallback
- Follow existing page patterns (CRTMonitor wrapper, AsciiPanel sections)
- Use CSS modules, never inline styles

### @terminal-ui-specialist
**File:** [terminal-ui-specialist.md](../../.claude/agents/terminal-ui-specialist.md)
**Query:** "TUI styling patterns for file browser and step visualization"
**Key Insights:**
- Phosphor orange (#ff9500) as primary, cyan (#00ffff) for accents
- Use box-drawing characters for borders and trees
- Implement proper ASCII art patterns for directories
- Add pulse animations for processing states
- Maintain 60fps with GPU-accelerated transforms

---

## Architecture Overview

```
CodeChatPage
    |
    +-- Configuration Panel (AsciiPanel)
    |       +-- WorkspaceDisplay + [CHANGE] button
    |       +-- ContextDisplay + [CHANGE] button
    |       +-- PresetSelector dropdown
    |       +-- Feature toggles (CGRAG, Web Search)
    |
    +-- State Indicator Bar
    |       +-- Current state badge ([IDLE] / [PLANNING] / etc.)
    |       +-- [CANCEL] button (when active)
    |
    +-- Query Input Section
    |       +-- Textarea with terminal styling
    |       +-- [EXECUTE] button
    |
    +-- ReAct Steps Container (scrollable)
    |       +-- ReActStepViewer (for each step)
    |               +-- Step header with number + tier badge
    |               +-- THOUGHT section
    |               +-- ACTION section (tool + args)
    |               +-- OBSERVATION section (collapsible)
    |
    +-- Final Answer Panel (when completed)
    |       +-- Markdown rendering
    |
    +-- Modals (conditional)
            +-- WorkspaceSelector (TUI file browser)
            +-- ContextSelector (radio button list)
```

---

## Files to Create

### Summary Table

| File | Lines (Est.) | Agent | Priority |
|------|--------------|-------|----------|
| `CodeChatPage.tsx` | 350-400 | @frontend-engineer | P0 |
| `CodeChatPage.module.css` | 250-300 | @terminal-ui-specialist | P0 |
| `WorkspaceSelector.tsx` | 200-250 | @frontend-engineer + @terminal-ui-specialist | P0 |
| `WorkspaceSelector.module.css` | 150-180 | @terminal-ui-specialist | P0 |
| `ContextSelector.tsx` | 150-180 | @frontend-engineer | P1 |
| `ContextSelector.module.css` | 100-120 | @terminal-ui-specialist | P1 |
| `ReActStepViewer.tsx` | 120-150 | @frontend-engineer | P0 |
| `ReActStepViewer.module.css` | 150-180 | @terminal-ui-specialist | P0 |
| `DiffPreview.tsx` | 180-220 | @frontend-engineer | P1 |
| `DiffPreview.module.css` | 120-150 | @terminal-ui-specialist | P1 |
| `PresetSelector.tsx` | 100-130 | @frontend-engineer | P2 |
| `PresetSelector.module.css` | 80-100 | @terminal-ui-specialist | P2 |
| `index.ts` | 10-15 | @frontend-engineer | P0 |

**Total Estimated:** 1,610-2,075 lines

---

## Phase 1: Core Page Structure (4-5 hours)

**Lead Agent:** @frontend-engineer
**Priority:** P0

### 1.1 CodeChatPage.tsx

Main page component integrating all sub-components.

**Props/State:**
```typescript
// Local state
const [query, setQuery] = useState('');
const [workspacePath, setWorkspacePath] = useState<string>('');
const [contextName, setContextName] = useState<string | null>(null);
const [preset, setPreset] = useState<string>('balanced');
const [showWorkspaceSelector, setShowWorkspaceSelector] = useState(false);
const [showContextSelector, setShowContextSelector] = useState(false);

// Hooks
const codeChat = useCodeChat();
const { data: workspaceInfo } = useWorkspaceValidation(workspacePath);
const { data: presets } = usePresets();
```

**Key Features:**
- Configuration panel with workspace/context/preset display
- State indicator bar showing current agent state
- Query input textarea with EXECUTE button
- ReAct steps container with scrolling
- Final answer display with markdown
- Modal triggers for selectors
- Error handling and loading states

**Integration Points:**
- Uses `useCodeChat` hook for SSE streaming
- Uses `useWorkspaceValidation` for workspace metadata
- Uses `usePresets` for preset options

### 1.2 CodeChatPage.module.css

Terminal aesthetic styling for the main page.

**Key Styles:**
```css
/* Layout */
.page { /* Full-width page container */ }
.configPanel { /* Configuration section */ }
.stateBar { /* State indicator row */ }
.inputSection { /* Query input area */ }
.stepsContainer { /* Scrollable steps list */ }
.answerPanel { /* Final answer display */ }

/* State variants */
.state-idle { color: var(--text-dim); }
.state-planning { color: var(--cyan); animation: pulse 2s infinite; }
.state-executing { color: var(--phosphor-orange); }
.state-observing { color: var(--cyan); }
.state-completed { color: var(--status-active); }
.state-error { color: var(--status-error); }
.state-cancelled { color: var(--text-dim); }
```

### 1.3 ReActStepViewer.tsx

Component for displaying individual ReAct steps.

**Props Interface:**
```typescript
interface ReActStepViewerProps {
  step: ReActStep;
  isExpanded?: boolean;
  onToggle?: () => void;
  className?: string;
}
```

**Structure:**
```
+--[ STEP 3 ]--[ POWERFUL ]------------------+
| THOUGHT: I need to read the config file    |
| to understand the current settings...      |
+--------------------------------------------+
| ACTION: read_file                          |
| path: "/project/config.json"               |
+--------------------------------------------+
| OBSERVATION: [expandable]                  |
| {                                          |
|   "version": "2.0.0",                      |
|   "settings": { ... }                      |
| }                                          |
+--------------------------------------------+
```

### 1.4 ReActStepViewer.module.css

**Key Styles:**
```css
.step { /* Step container with border */ }
.stepHeader { /* Step number + tier badge row */ }
.tierBadge { /* Model tier indicator */ }
.section { /* THOUGHT/ACTION/OBSERVATION sections */ }
.sectionLabel { /* Section title styling */ }
.observation { /* Pre-formatted output */ }
.collapsed { /* Collapsed state */ }
.expandToggle { /* Expand/collapse button */ }
```

---

## Phase 2: Modal Selectors (3-4 hours)

**Lead Agent:** @frontend-engineer + @terminal-ui-specialist
**Priority:** P0/P1

### 2.1 WorkspaceSelector.tsx

TUI file browser modal for workspace selection.

**Props Interface:**
```typescript
interface WorkspaceSelectorProps {
  currentWorkspace: string;
  onSelect: (path: string) => void;
  onClose: () => void;
}
```

**Structure:**
```
+--[ WORKSPACE SELECTION ]-------------------+
| Current: /home/user/projects/synapse       |
+--------------------------------------------+
| /home/user/projects                    [^] |
+--------------------------------------------+
|  +-- synapse/          [SELECTED]  Python  |
|  +-- other-project/                 Node   |
|  +-- experiments/                   --     |
|  +-- documentation/                 --     |
+--------------------------------------------+
| [SELECT]  [REFRESH]  [HOME]                |
+--------------------------------------------+
```

**Key Features:**
- Directory tree with ASCII art (+-- prefixes)
- Current path display with parent navigation
- Project type detection badges (Python, Node, etc.)
- Git repository indicator
- SELECT/REFRESH/HOME action buttons
- Loading states during directory fetching

### 2.2 WorkspaceSelector.module.css

**Key Styles:**
```css
.modal { /* Modal overlay */ }
.modalContent { /* Modal container */ }
.currentPath { /* Path display bar */ }
.directoryList { /* Scrollable directory list */ }
.directoryItem { /* Individual directory row */ }
.directoryIcon { /* Folder ASCII art */ }
.projectBadge { /* Project type badge */ }
.gitIndicator { /* Git repo indicator */ }
.actions { /* Button row */ }
.selected { /* Selected item highlight */ }
```

### 2.3 ContextSelector.tsx

CGRAG index picker modal.

**Props Interface:**
```typescript
interface ContextSelectorProps {
  selectedContext: string | null;
  onSelect: (contextName: string | null) => void;
  onClose: () => void;
}
```

**Structure:**
```
+--[ CONTEXT SELECTION ]---------------------+
| Available CGRAG Indexes:                   |
+--------------------------------------------+
| (*) synapse-engine    [42,156 chunks]      |
|     Indexed: 2025-11-29 10:30              |
|                                            |
| ( ) my-app            [8,234 chunks]       |
|     Indexed: 2025-11-28 15:00              |
|                                            |
| ( ) None (no context)                      |
+--------------------------------------------+
| [CREATE NEW INDEX]  [REFRESH INDEX]        |
+--------------------------------------------+
```

**Key Features:**
- Radio button selection (ASCII style)
- Chunk count display
- Last indexed timestamp
- "None" option for no context
- CREATE NEW INDEX button (opens nested modal)
- REFRESH INDEX button (triggers re-indexing)

### 2.4 ContextSelector.module.css

**Key Styles:**
```css
.contextList { /* Scrollable context list */ }
.contextItem { /* Individual context row */ }
.radio { /* ASCII radio button (*) / ( ) */ }
.contextName { /* Context name */ }
.chunkCount { /* Chunk count badge */ }
.indexedDate { /* Last indexed timestamp */ }
.noneOption { /* "None" option styling */ }
```

---

## Phase 3: Supporting Components (2-3 hours)

**Lead Agent:** @frontend-engineer
**Priority:** P1/P2

### 3.1 DiffPreview.tsx

File diff display component for showing changes before/after.

**Props Interface:**
```typescript
interface DiffPreviewProps {
  filePath: string;
  originalContent: string | null;
  newContent: string;
  changeType: 'create' | 'modify' | 'delete';
  viewMode?: 'unified' | 'side-by-side';
  className?: string;
}

interface DiffLine {
  lineNumber: number;
  type: 'add' | 'remove' | 'context';
  content: string;
}
```

**Structure (Unified View):**
```
+--[ DIFF: src/utils/helper.py ]--[ MODIFY ]-+
|  15   def calculate(x, y):                 |
| -16       return x + y                     |
| +16       # Enhanced calculation           |
| +17       result = x + y                   |
| +18       logger.debug(f"Result: {result}")|
| +19       return result                    |
|  20   def validate(data):                  |
+--------------------------------------------+
```

**Key Features:**
- Unified or side-by-side view toggle
- Line-by-line highlighting (green for add, red for remove)
- Line numbers
- File path header with change type badge
- Scrollable for large diffs

### 3.2 DiffPreview.module.css

**Key Styles:**
```css
.diffContainer { /* Main container */ }
.fileHeader { /* File path and change type */ }
.changeTypeBadge { /* CREATE/MODIFY/DELETE badge */ }
.diffContent { /* Diff lines container */ }
.lineNumber { /* Line number gutter */ }
.lineAdd { /* Added line (green) */ }
.lineRemove { /* Removed line (red) */ }
.lineContext { /* Context line (dim) */ }
.viewToggle { /* Unified/side-by-side toggle */ }
```

### 3.3 PresetSelector.tsx

Preset dropdown with override controls.

**Props Interface:**
```typescript
interface PresetSelectorProps {
  selectedPreset: string;
  onPresetChange: (preset: string) => void;
  toolOverrides?: Partial<Record<ToolName, ToolModelConfig>>;
  onOverrideChange?: (overrides: Partial<Record<ToolName, ToolModelConfig>>) => void;
  showOverrides?: boolean;
}
```

**Structure:**
```
+--[ PRESET ]--------------------------------+
| [balanced v]                               |
+--------------------------------------------+
| [x] Show advanced options                  |
+--------------------------------------------+
| Planning:     [powerful v]                 |
| read_file:    [fast v]                     |
| write_file:   [powerful v]                 |
| search_code:  [balanced v]                 |
+--------------------------------------------+
```

**Key Features:**
- Preset dropdown (speed/balanced/quality/coding/research)
- Toggle for advanced per-tool overrides
- Per-tool tier dropdown when expanded
- Save custom preset button (future enhancement)

### 3.4 PresetSelector.module.css

**Key Styles:**
```css
.presetContainer { /* Main container */ }
.presetSelect { /* Main dropdown */ }
.advancedToggle { /* Show advanced checkbox */ }
.overrideGrid { /* Tool overrides grid */ }
.overrideRow { /* Individual tool row */ }
.toolName { /* Tool name label */ }
.tierSelect { /* Tier dropdown */ }
```

---

## Phase 4: Integration & Routing (1-2 hours)

**Lead Agent:** @frontend-engineer
**Priority:** P0

### 4.1 Update Route Configuration

**File:** `frontend/src/router/routes.tsx`

Add route for CodeChatPage:
```typescript
import { CodeChatPage } from '../pages/CodeChatPage/CodeChatPage';

// Add route:
{ path: 'code-chat', element: <CodeChatPage /> }
```

### 4.2 Update Mode Selector

**File:** `frontend/src/components/modes/ModeSelector.tsx`

Add code-chat mode:
```typescript
export type QueryMode = 'two-stage' | 'simple' | 'council' | 'benchmark' | 'code-chat';

const MODES: ModeDefinition[] = [
  // ... existing modes ...
  {
    id: 'code-chat',
    label: 'CODE CHAT',
    description: 'Agentic assistant with file ops & code execution',
    available: true,
  },
];
```

### 4.3 Create Index Export

**File:** `frontend/src/pages/CodeChatPage/index.ts`

```typescript
export { CodeChatPage } from './CodeChatPage';
export { WorkspaceSelector } from './WorkspaceSelector';
export { ContextSelector } from './ContextSelector';
export { ReActStepViewer } from './ReActStepViewer';
export { DiffPreview } from './DiffPreview';
export { PresetSelector } from './PresetSelector';
```

---

## CSS Design System Requirements

### Color Palette (from tokens.css)

```css
/* Primary brand color */
--phosphor-orange: #ff9500;
--text-primary: #ff9500;
--border-primary: #ff9500;

/* Accent colors */
--cyan: #00ffff;
--text-accent: #00ffff;
--border-accent: #00ffff;

/* Status colors */
--status-active: #ff9500;
--status-idle: #ff950066;
--status-processing: #00ffff;
--status-error: #ff0000;

/* Backgrounds */
--bg-primary: #000000;
--bg-panel: #0a0a0a;
--bg-hover: #151515;
--bg-input: #050505;
```

### Typography

```css
/* Fonts */
--font-mono: 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', monospace;
--font-display: 'Share Tech Mono', monospace;

/* Sizes */
--text-xs: 10px;
--text-sm: 12px;
--text-md: 14px;
--text-lg: 16px;
```

### Animation Patterns

```css
/* Breathing animation for panels */
@keyframes panel-breathe {
  0%, 100% { border-color: var(--border-primary); }
  50% { border-color: rgba(255, 149, 0, 0.8); box-shadow: 0 0 15px rgba(255, 149, 0, 0.2); }
}

/* Pulse for processing states */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Section title pulse */
@keyframes section-pulse {
  0%, 100% { color: var(--cyan); text-shadow: 0 0 3px var(--cyan); }
  50% { color: rgba(0, 255, 255, 0.8); text-shadow: 0 0 6px var(--cyan); }
}
```

### ASCII Art Characters

```
/* Directory tree */
+-- directory/
|   +-- subdirectory/
|   +-- file.txt

/* Radio buttons */
(*) Selected
( ) Unselected

/* Box drawing */
+--[ TITLE ]---------------------+
|  Content                       |
+--------------------------------+

/* Status indicators */
[ACTIVE] [IDLE] [PROCESSING] [ERROR]
```

---

## Testing Checklist

### Unit Tests

- [ ] CodeChatPage renders configuration panel
- [ ] CodeChatPage handles query submission
- [ ] CodeChatPage displays ReAct steps correctly
- [ ] WorkspaceSelector navigates directories
- [ ] WorkspaceSelector selects workspace
- [ ] ContextSelector displays available contexts
- [ ] ContextSelector handles selection
- [ ] ReActStepViewer renders all sections
- [ ] ReActStepViewer toggles expansion
- [ ] DiffPreview highlights changes correctly
- [ ] PresetSelector changes preset

### Integration Tests

- [ ] Full query flow (submit -> steps -> answer)
- [ ] Workspace selection and validation
- [ ] Context selection with API
- [ ] Cancellation mid-execution
- [ ] Error state handling

### Visual/A11y Tests

- [ ] All components match terminal aesthetic
- [ ] Proper ARIA labels on interactive elements
- [ ] Keyboard navigation works
- [ ] Focus states visible
- [ ] Color contrast meets WCAG AA

---

## Implementation Order

1. **Phase 1.1-1.2** - CodeChatPage skeleton + basic styles
2. **Phase 1.3-1.4** - ReActStepViewer component
3. **Phase 2.1-2.2** - WorkspaceSelector modal
4. **Phase 2.3-2.4** - ContextSelector modal
5. **Phase 4** - Route integration (can test basic flow)
6. **Phase 3.1-3.2** - DiffPreview component
7. **Phase 3.3-3.4** - PresetSelector component
8. **Testing** - Unit and integration tests

---

## Definition of Done

- [ ] All files created and properly typed (TypeScript strict mode)
- [ ] CSS modules follow design system (tokens.css)
- [ ] Components use existing terminal UI patterns
- [ ] All hooks from Session 3 integrated
- [ ] Route added and accessible via navigation
- [ ] Loading states show TerminalSpinner
- [ ] Error states display properly
- [ ] Basic end-to-end flow works (submit query -> see steps -> see answer)
- [ ] Code follows project conventions (no inline styles, proper ARIA)
- [ ] No TypeScript errors
- [ ] No console errors

---

## Risks & Mitigation

### Risk: SSE Parsing Edge Cases
**Mitigation:** The useCodeChat hook already handles buffer management and event parsing. Test with multi-step queries to verify step accumulation.

### Risk: Modal Focus Management
**Mitigation:** Use focus trap pattern. When modal opens, focus first interactive element. When modal closes, return focus to trigger button.

### Risk: Large Observation Output
**Mitigation:** Implement virtual scrolling or max-height with overflow for observation sections. Consider collapsing by default.

### Risk: Diff Algorithm Complexity
**Mitigation:** Start with simple line-by-line diff display. If server provides pre-computed diff lines, use those directly rather than computing client-side.

---

## Next Steps (Session 5)

After Session 4 completion:
1. End-to-end testing of full Code Chat flow
2. Performance optimization (memoization, virtual scrolling)
3. Error boundary implementation
4. Accessibility audit
5. Documentation updates

---

## Appendix: Component Signatures

### CodeChatPage
```typescript
export const CodeChatPage: React.FC = () => { ... }
```

### WorkspaceSelector
```typescript
export const WorkspaceSelector: React.FC<{
  currentWorkspace: string;
  onSelect: (path: string) => void;
  onClose: () => void;
}> = ({ currentWorkspace, onSelect, onClose }) => { ... }
```

### ContextSelector
```typescript
export const ContextSelector: React.FC<{
  selectedContext: string | null;
  onSelect: (contextName: string | null) => void;
  onClose: () => void;
}> = ({ selectedContext, onSelect, onClose }) => { ... }
```

### ReActStepViewer
```typescript
export const ReActStepViewer: React.FC<{
  step: ReActStep;
  isExpanded?: boolean;
  onToggle?: () => void;
  className?: string;
}> = ({ step, isExpanded = false, onToggle, className }) => { ... }
```

### DiffPreview
```typescript
export const DiffPreview: React.FC<{
  filePath: string;
  originalContent: string | null;
  newContent: string;
  changeType: 'create' | 'modify' | 'delete';
  viewMode?: 'unified' | 'side-by-side';
  className?: string;
}> = ({ filePath, originalContent, newContent, changeType, viewMode = 'unified', className }) => { ... }
```

### PresetSelector
```typescript
export const PresetSelector: React.FC<{
  selectedPreset: string;
  onPresetChange: (preset: string) => void;
  toolOverrides?: Partial<Record<ToolName, ToolModelConfig>>;
  onOverrideChange?: (overrides: Partial<Record<ToolName, ToolModelConfig>>) => void;
  showOverrides?: boolean;
}> = ({ selectedPreset, onPresetChange, toolOverrides, onOverrideChange, showOverrides = false }) => { ... }
```
