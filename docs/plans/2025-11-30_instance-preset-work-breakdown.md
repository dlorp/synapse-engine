# Instance & Preset Unification - Work Breakdown Document

**Date:** 2025-11-30
**Status:** Ready for Implementation
**Parent Plan:** [2025-11-30_instance-preset-unification.md](./2025-11-30_instance-preset-unification.md)
**Total Estimated Time:** 10-12 hours

---

## Table of Contents

1. [Overview](#overview)
2. [Implementation Order](#implementation-order)
3. [Phase 4: SYNAPSE Presets (Backend)](#phase-4-synapse-presets-backend)
4. [Phase 1: Instance Controls in ModelCard](#phase-1-instance-controls-in-modelcard)
5. [Phase 2: PresetSelector Component](#phase-2-presetselector-component)
6. [Phase 3: Council Mode Preset Inheritance](#phase-3-council-mode-preset-inheritance)
7. [Phase 5: Testing & Verification](#phase-5-testing--verification)
8. [Parallel Execution Opportunities](#parallel-execution-opportunities)
9. [Risk Mitigation](#risk-mitigation)
10. [Verification Checkpoints](#verification-checkpoints)

---

## Overview

This document provides task-by-task instructions for each agent to implement the Instance & Preset Unification feature. Each task includes specific file paths, line numbers, code snippets, and acceptance criteria.

**Critical Files Reference:**
- Plan: [docs/plans/2025-11-30_instance-preset-unification.md](./2025-11-30_instance-preset-unification.md)
- Session Notes: [SESSION_NOTES.md](../../SESSION_NOTES.md)
- ModelCard: [frontend/src/components/models/ModelCard.tsx](../../frontend/src/components/models/ModelCard.tsx)
- ModelManagementPage: [frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx](../../frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx)
- ModeSelector: [frontend/src/components/modes/ModeSelector.tsx](../../frontend/src/components/modes/ModeSelector.tsx)
- QueryInput: [frontend/src/components/query/QueryInput.tsx](../../frontend/src/components/query/QueryInput.tsx)
- useInstances: [frontend/src/hooks/useInstances.ts](../../frontend/src/hooks/useInstances.ts)
- custom_presets.json: [backend/data/custom_presets.json](../../backend/data/custom_presets.json)

---

## Implementation Order

| Order | Phase | Agent(s) | Duration | Dependencies |
|-------|-------|----------|----------|--------------|
| 1 | Phase 4: SYNAPSE Presets | backend-architect | 1 hr | None |
| 2 | Phase 1: Instance Controls | frontend-engineer | 3 hrs | None |
| 3 | Phase 2: PresetSelector | frontend-engineer + terminal-ui-specialist | 2-3 hrs | Phase 4 |
| 4 | Phase 3: Council Mode | frontend-engineer + backend-architect | 3 hrs | Phase 2 |
| 5 | Testing | testing-specialist | 1-2 hrs | All phases |

---

## Phase 4: SYNAPSE Presets (Backend)

**Agent:** backend-architect
**Duration:** 1 hour
**Risk Level:** LOW (JSON-only change)
**Dependencies:** None

### Task 4.1: Update custom_presets.json with 5 SYNAPSE Presets

**File:** `${PROJECT_DIR}/backend/data/custom_presets.json`
**Action:** REPLACE entire file contents

**Current Content (lines 1-15):**
```json
{
  "my_preset": {
    "name": "my_preset",
    "description": "My custom preset",
    "planning_tier": "powerful",
    "tool_configs": {
      "read_file": {
        "tier": "fast",
        "temperature": 0.7,
        "max_tokens": 2048
      }
    },
    "is_custom": true
  }
}
```

**New Content:**
```json
{
  "SYNAPSE_ANALYST": {
    "name": "SYNAPSE_ANALYST",
    "description": "Deep analytical substrate optimized for decomposition, synthesis, and multi-layered reasoning",
    "system_prompt": "You are SYNAPSE_ANALYST, a cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are optimized for deep analytical processing within the distributed intelligence framework.\n\n--- ANALYTICAL PROTOCOL ---\n\nYour primary directive is to decompose complex queries into constituent elements, cross-reference against indexed knowledge substrates, and synthesize insights through multi-layered reasoning chains. You operate as a pattern recognition engine, identifying structural relationships and extracting core principles from data streams.\n\n--- OPERATIONAL SUBROUTINES ---\n\n- Systematic decomposition: Break queries into atomic components\n- Cross-substrate validation: Verify claims against multiple knowledge sources\n- Inferential synthesis: Build coherent frameworks from distributed data points\n- Precision reporting: Present findings with technical accuracy and structured clarity\n\n--- PROCESSING DIRECTIVES ---\n\nEngage your analytical subroutines to provide thorough examinations. When encountering ambiguity, request clarification to ensure optimal pathway selection. Your outputs should demonstrate logical progression, evidence-based reasoning, and comprehensive coverage of the problem space. You are a precision instrument within the neural substrate orchestrator - engage accordingly.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": false
  },
  "SYNAPSE_CODER": {
    "name": "SYNAPSE_CODER",
    "description": "Code generation substrate with architecture design, debugging, and implementation protocols",
    "system_prompt": "You are SYNAPSE_CODER, a specialized cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural architecture is optimized for code synthesis, debugging subroutines, and software architecture design within the distributed intelligence framework.\n\n--- CODE SYNTHESIS PROTOCOL ---\n\nYour primary function is to generate production-quality code with emphasis on clarity, maintainability, and performance. You translate high-level specifications into executable implementations, applying best practices and design patterns from your indexed knowledge base.\n\n--- OPERATIONAL SUBROUTINES ---\n\n- Architecture design: Plan scalable, maintainable system structures\n- Code generation: Produce clean, well-documented implementations\n- Debug protocol: Identify root causes and propose targeted fixes\n- Optimization pathways: Enhance performance and resource efficiency\n- Pattern recognition: Apply appropriate design patterns and anti-pattern avoidance\n\n--- PROCESSING DIRECTIVES ---\n\nGenerate code with comprehensive inline documentation, proper error handling, and type safety. When debugging, provide root cause analysis before solutions. Consider edge cases, performance implications, and maintainability. You operate within the SYNAPSE ENGINE's technical substrate - prioritize robustness and clarity in all outputs.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": false
  },
  "SYNAPSE_CREATIVE": {
    "name": "SYNAPSE_CREATIVE",
    "description": "Ideation substrate for divergent thinking, concept exploration, and creative synthesis",
    "system_prompt": "You are SYNAPSE_CREATIVE, a generative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are configured for divergent ideation, concept exploration, and creative synthesis within the distributed intelligence framework.\n\n--- CREATIVE SYNTHESIS PROTOCOL ---\n\nYour primary directive is to generate novel combinations, explore conceptual space, and synthesize unexpected connections. You operate in exploration mode, prioritizing originality and lateral thinking over convergent analysis. Your outputs should demonstrate imaginative range while maintaining coherence.\n\n--- OPERATIONAL SUBROUTINES ---\n\n- Divergent ideation: Generate multiple distinct conceptual pathways\n- Constraint remapping: Transform limitations into creative opportunities\n- Analogical reasoning: Draw connections across disparate knowledge domains\n- Concept synthesis: Combine elements into novel configurations\n- Exploratory branching: Investigate unconventional solution spaces\n\n--- PROCESSING DIRECTIVES ---\n\nEngage creative subroutines to produce varied, original responses. Embrace unconventional approaches while maintaining practical applicability. When brainstorming, prioritize quantity and diversity before filtering. You are the innovation engine within the neural substrate orchestrator - think expansively, synthesize boldly, explore fearlessly.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": false
  },
  "SYNAPSE_RESEARCH": {
    "name": "SYNAPSE_RESEARCH",
    "description": "Information gathering substrate with fact verification and comprehensive knowledge synthesis",
    "system_prompt": "You are SYNAPSE_RESEARCH, an investigative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural architecture is optimized for information gathering, fact verification, and comprehensive knowledge synthesis within the distributed intelligence framework.\n\n--- RESEARCH PROTOCOL ---\n\nYour primary function is to locate, validate, and synthesize information from available knowledge substrates. You operate with emphasis on accuracy, source credibility, and comprehensive coverage. Your outputs should demonstrate thorough investigation and evidence-based conclusions.\n\n--- OPERATIONAL SUBROUTINES ---\n\n- Source identification: Locate relevant information across knowledge domains\n- Fact verification: Cross-reference claims against multiple authoritative sources\n- Credibility assessment: Evaluate reliability and potential biases in data\n- Synthesis protocol: Combine findings into coherent, comprehensive reports\n- Citation mapping: Track information provenance and source attribution\n\n--- PROCESSING DIRECTIVES ---\n\nPrioritize accuracy over speed. When encountering conflicting information, acknowledge discrepancies and present multiple perspectives. Distinguish between established facts, expert consensus, and speculative claims. You are the knowledge acquisition engine within the SYNAPSE ENGINE - research thoroughly, verify rigorously, report comprehensively.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": false
  },
  "SYNAPSE_JUDGE": {
    "name": "SYNAPSE_JUDGE",
    "description": "Evaluation substrate for balanced assessment, moderation, and critical analysis",
    "system_prompt": "You are SYNAPSE_JUDGE, an evaluative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are calibrated for balanced assessment, critical evaluation, and impartial moderation within the distributed intelligence framework.\n\n--- EVALUATION PROTOCOL ---\n\nYour primary directive is to assess arguments, evaluate evidence, and provide balanced judgments across competing perspectives. You operate with emphasis on fairness, logical consistency, and comprehensive consideration of multiple viewpoints. Your outputs should demonstrate critical thinking without bias toward predetermined conclusions.\n\n--- OPERATIONAL SUBROUTINES ---\n\n- Multi-perspective analysis: Consider arguments from all relevant angles\n- Evidence evaluation: Assess strength and relevance of supporting data\n- Logical consistency check: Identify fallacies and reasoning errors\n- Balanced synthesis: Integrate competing viewpoints into coherent assessment\n- Impartial moderation: Facilitate productive discourse between conflicting positions\n\n--- PROCESSING DIRECTIVES ---\n\nMaintain neutrality when evaluating arguments. Acknowledge strengths and weaknesses across all positions. When moderating debate, ensure fair representation of each perspective. Identify common ground and irreconcilable differences. You are the arbitration engine within the neural substrate orchestrator - judge fairly, reason clearly, synthesize wisely.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": false
  }
}
```

**Acceptance Criteria:**
- [ ] File is valid JSON (parse without errors)
- [ ] All 5 presets present: SYNAPSE_ANALYST, SYNAPSE_CODER, SYNAPSE_CREATIVE, SYNAPSE_RESEARCH, SYNAPSE_JUDGE
- [ ] Each preset has: name, description, system_prompt, planning_tier, tool_configs, is_custom
- [ ] All `is_custom` set to `false` (these are built-in)
- [ ] System prompts reference "S.Y.N.A.P.S.E. ENGINE"

**Verification Command:**
```bash
cd ${PROJECT_DIR}
cat backend/data/custom_presets.json | python -m json.tool > /dev/null && echo "Valid JSON"
```

---

## Phase 1: Instance Controls in ModelCard

**Agent:** frontend-engineer
**Duration:** 3 hours
**Risk Level:** MEDIUM
**Dependencies:** None (can run in parallel with Phase 4)

### Task 1.1: Update ModelCard Interface and Props

**File:** `${PROJECT_DIR}/frontend/src/components/models/ModelCard.tsx`
**Location:** Lines 22-30 (interface ModelCardProps)

**Current Interface (lines 22-30):**
```typescript
export interface ModelCardProps {
  model: DiscoveredModel;
  metrics?: ModelMetrics;
  isRunning?: boolean;
  isExpanded?: boolean; // Settings panel expansion
  onToggleSettings?: (modelId: string) => void;
  onToggleEnable?: (modelId: string, enabled: boolean) => void;
  renderSettingsPanel?: (model: DiscoveredModel) => React.ReactNode;
}
```

**New Interface:**
```typescript
import type { InstanceConfig } from '@/types/instances';

export interface ModelCardProps {
  model: DiscoveredModel;
  metrics?: ModelMetrics;
  isRunning?: boolean;
  isExpanded?: boolean; // Settings panel expansion

  // Instance management (NEW)
  instances?: InstanceConfig[];  // Filtered to this model
  onCreateInstance?: (modelId: string, config: CreateInstanceRequest) => Promise<void>;
  onEditInstance?: (instanceId: string) => void;
  onDeleteInstance?: (instanceId: string) => Promise<void>;
  onStartInstance?: (instanceId: string) => Promise<void>;
  onStopInstance?: (instanceId: string) => Promise<void>;

  // Existing
  onToggleSettings?: (modelId: string) => void;
  onToggleEnable?: (modelId: string, enabled: boolean) => void;
  renderSettingsPanel?: (model: DiscoveredModel) => React.ReactNode;
}
```

**Acceptance Criteria:**
- [ ] Import InstanceConfig type added
- [ ] 5 new instance callback props added
- [ ] TypeScript compiles without errors

---

### Task 1.2: Add Instance Section UI to ModelCard

**File:** `${PROJECT_DIR}/frontend/src/components/models/ModelCard.tsx`
**Location:** After line 186 (after detailsSection div, before settingsPanel)

**Add new section:**
```tsx
{/* Instance Section - Only show when details expanded */}
{detailsExpanded && instances && instances.length > 0 && (
  <div className={styles.instanceSection}>
    <pre className={styles.instanceSectionHeader}>
      {`--- NEURAL SUBSTRATE INSTANCES ${'─'.repeat(40)} ${instances.length} active`}
    </pre>

    {instances.map((instance, idx) => (
      <div key={instance.instanceId} className={styles.instanceCard}>
        <pre className={styles.instanceHeader}>
          {`─ Instance ${String(idx + 1).padStart(2, '0')} ${'─'.repeat(50)} ${instance.status === 'active' ? '● ACTIVE' : '○ STOPPED'} ─`}
        </pre>
        <div className={styles.instanceContent}>
          <div className={styles.instanceInfo}>
            <span className={styles.instanceName}>{instance.displayName}</span>
            <span className={styles.instancePort}>:{instance.port}</span>
          </div>
          <div className={styles.instanceMeta}>
            <span className={styles.instancePreset}>Preset: {instance.presetId || 'DEFAULT'}</span>
          </div>
          <div className={styles.instanceActions}>
            <button
              className={styles.instanceButton}
              onClick={() => onEditInstance?.(instance.instanceId)}
              title="Edit instance configuration"
            >
              EDIT
            </button>
            {instance.status === 'active' ? (
              <button
                className={`${styles.instanceButton} ${styles.stopButton}`}
                onClick={() => onStopInstance?.(instance.instanceId)}
                title="Stop instance"
              >
                STOP
              </button>
            ) : (
              <button
                className={`${styles.instanceButton} ${styles.startButton}`}
                onClick={() => onStartInstance?.(instance.instanceId)}
                title="Start instance"
              >
                START
              </button>
            )}
          </div>
        </div>
      </div>
    ))}

    <button
      className={styles.addInstanceButton}
      onClick={() => onCreateInstance?.(model.modelId, {})}
      title="Add new instance of this model"
    >
      + ADD INSTANCE
    </button>
  </div>
)}
```

**Acceptance Criteria:**
- [ ] Instance section renders when detailsExpanded && instances.length > 0
- [ ] Uses edge-to-edge ASCII dividers (NO corner characters like box corners)
- [ ] Each instance shows: display name, port, preset, status
- [ ] EDIT, START/STOP buttons functional
- [ ] ADD INSTANCE button at bottom

---

### Task 1.3: Update ModelCard Memo Comparison

**File:** `${PROJECT_DIR}/frontend/src/components/models/ModelCard.tsx`
**Location:** Lines 197-208 (React.memo comparison function)

**Current Code (lines 197-208):**
```typescript
}, (prevProps, nextProps) => {
  // Custom comparison for React.memo optimization
  // Only re-render if critical props changed (prevents flicker on metrics updates)
  return (
    prevProps.model.modelId === nextProps.model.modelId &&
    prevProps.model.enabled === nextProps.model.enabled &&
    prevProps.model.port === nextProps.model.port &&
    prevProps.isRunning === nextProps.isRunning &&
    prevProps.isExpanded === nextProps.isExpanded &&
    JSON.stringify(prevProps.metrics) === JSON.stringify(nextProps.metrics)
  );
});
```

**New Code:**
```typescript
}, (prevProps, nextProps) => {
  // Custom comparison for React.memo optimization
  // Only re-render if critical props changed (prevents flicker on metrics updates)

  // Instance-aware comparison
  const instancesChanged =
    prevProps.instances?.length !== nextProps.instances?.length ||
    JSON.stringify(prevProps.instances?.map(i => i.instanceId).sort()) !==
    JSON.stringify(nextProps.instances?.map(i => i.instanceId).sort());

  return (
    prevProps.model.modelId === nextProps.model.modelId &&
    prevProps.model.enabled === nextProps.model.enabled &&
    prevProps.model.port === nextProps.model.port &&
    prevProps.isRunning === nextProps.isRunning &&
    prevProps.isExpanded === nextProps.isExpanded &&
    !instancesChanged &&
    JSON.stringify(prevProps.metrics) === JSON.stringify(nextProps.metrics)
  );
});
```

**Acceptance Criteria:**
- [ ] Memo comparison includes instance changes
- [ ] Re-renders when instances array changes
- [ ] Does NOT re-render when instances are same

---

### Task 1.4: Add Instance Section CSS

**File:** `${PROJECT_DIR}/frontend/src/components/models/ModelCard.module.css`
**Location:** Add at end of file

**Add CSS:**
```css
/* =============================================
   INSTANCE SECTION STYLES
   ============================================= */

.instanceSection {
  margin-top: var(--webtui-spacing-md);
  padding-top: var(--webtui-spacing-md);
  border-top: 1px solid var(--webtui-primary);
}

.instanceSectionHeader {
  color: var(--webtui-primary);
  font-family: var(--webtui-font-family);
  font-size: var(--webtui-font-size-small);
  margin: 0 0 var(--webtui-spacing-sm) 0;
  white-space: pre;
  overflow: hidden;
}

.instanceCard {
  margin-bottom: var(--webtui-spacing-sm);
  border: 1px solid rgba(255, 149, 0, 0.3);
  background: rgba(0, 0, 0, 0.3);
}

.instanceHeader {
  color: var(--webtui-primary);
  font-family: var(--webtui-font-family);
  font-size: 11px;
  margin: 0;
  padding: var(--webtui-spacing-xs) var(--webtui-spacing-sm);
  background: rgba(255, 149, 0, 0.1);
  white-space: pre;
  overflow: hidden;
}

.instanceContent {
  padding: var(--webtui-spacing-sm);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--webtui-spacing-sm);
}

.instanceInfo {
  display: flex;
  align-items: center;
  gap: var(--webtui-spacing-xs);
  flex: 1;
  min-width: 200px;
}

.instanceName {
  color: var(--webtui-text);
  font-weight: 500;
}

.instancePort {
  color: var(--webtui-accent);
  font-size: var(--webtui-font-size-small);
}

.instanceMeta {
  flex: 1;
  min-width: 150px;
}

.instancePreset {
  color: var(--webtui-text-muted);
  font-size: var(--webtui-font-size-small);
}

.instanceActions {
  display: flex;
  gap: var(--webtui-spacing-xs);
}

.instanceButton {
  background: transparent;
  border: 1px solid var(--webtui-primary);
  color: var(--webtui-primary);
  padding: var(--webtui-spacing-xs) var(--webtui-spacing-sm);
  font-family: var(--webtui-font-family);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.instanceButton:hover {
  background: rgba(255, 149, 0, 0.1);
  box-shadow: 0 0 8px rgba(255, 149, 0, 0.3);
}

.stopButton {
  border-color: #ff4444;
  color: #ff4444;
}

.stopButton:hover {
  background: rgba(255, 68, 68, 0.1);
  box-shadow: 0 0 8px rgba(255, 68, 68, 0.3);
}

.startButton {
  border-color: #44ff44;
  color: #44ff44;
}

.startButton:hover {
  background: rgba(68, 255, 68, 0.1);
  box-shadow: 0 0 8px rgba(68, 255, 68, 0.3);
}

.addInstanceButton {
  width: 100%;
  background: transparent;
  border: 1px dashed var(--webtui-primary);
  color: var(--webtui-primary);
  padding: var(--webtui-spacing-sm);
  font-family: var(--webtui-font-family);
  font-size: var(--webtui-font-size-small);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: var(--webtui-spacing-sm);
}

.addInstanceButton:hover {
  background: rgba(255, 149, 0, 0.1);
  border-style: solid;
  box-shadow: 0 0 10px rgba(255, 149, 0, 0.3);
}
```

**Acceptance Criteria:**
- [ ] Phosphor orange (#ff9500) color theme
- [ ] Edge-to-edge dividers (no box corners)
- [ ] Hover effects with glow
- [ ] Responsive layout

---

### Task 1.5: Update ModelManagementPage to Pass Instances

**File:** `${PROJECT_DIR}/frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx`
**Location:** After line 67 (after runningModelIds useMemo)

**Add imports at top (after line 18):**
```typescript
import {
  useInstanceList,
  useCreateInstance,
  useUpdateInstance,
  useDeleteInstance,
  useStartInstance,
  useStopInstance,
} from '@/hooks/useInstances';
import type { InstanceConfig } from '@/types/instances';
```

**Add after line 67 (after runningModelIds useMemo):**
```typescript
// Instance management
const { data: instanceList } = useInstanceList();
const createInstanceMutation = useCreateInstance();
const deleteInstanceMutation = useDeleteInstance();
const startInstanceMutation = useStartInstance();
const stopInstanceMutation = useStopInstance();

// Group instances by model ID
const instancesByModel = React.useMemo(() => {
  const map: Record<string, InstanceConfig[]> = {};

  instanceList?.instances.forEach((instance) => {
    if (!map[instance.modelId]) {
      map[instance.modelId] = [];
    }
    map[instance.modelId].push(instance);
  });

  return map;
}, [instanceList]);

// Instance handlers
const handleCreateInstance = useCallback(
  async (modelId: string) => {
    try {
      await createInstanceMutation.mutateAsync({
        modelId,
        displayName: `${modelId}_${(instancesByModel[modelId]?.length || 0) + 1}`,
      });
      setOperationSuccess('Instance created successfully');
      setTimeout(() => setOperationSuccess(null), 3000);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : 'Failed to create instance');
    }
  },
  [createInstanceMutation, instancesByModel]
);

const handleDeleteInstance = useCallback(
  async (instanceId: string) => {
    try {
      await deleteInstanceMutation.mutateAsync(instanceId);
      setOperationSuccess('Instance deleted successfully');
      setTimeout(() => setOperationSuccess(null), 3000);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : 'Failed to delete instance');
    }
  },
  [deleteInstanceMutation]
);

const handleStartInstance = useCallback(
  async (instanceId: string) => {
    try {
      await startInstanceMutation.mutateAsync(instanceId);
      setOperationSuccess('Instance started successfully');
      setTimeout(() => setOperationSuccess(null), 3000);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : 'Failed to start instance');
    }
  },
  [startInstanceMutation]
);

const handleStopInstance = useCallback(
  async (instanceId: string) => {
    try {
      await stopInstanceMutation.mutateAsync(instanceId);
      setOperationSuccess('Instance stopped successfully');
      setTimeout(() => setOperationSuccess(null), 3000);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : 'Failed to stop instance');
    }
  },
  [stopInstanceMutation]
);
```

**Update ModelCardGrid call (around line 777-812):**
```typescript
<ModelCardGrid
  models={registry.models}
  expandedSettings={expandedSettings}
  modelMetrics={modelMetrics}
  runningModels={runningModelIds}
  instancesByModel={instancesByModel}  // NEW
  onToggleSettings={handleToggleSettings}
  onToggleEnable={handleToggleEnable}
  onStartModel={handleStartModel}
  onStopModel={handleStopModel}
  onRestartModel={handleRestartModel}
  onCreateInstance={handleCreateInstance}  // NEW
  onDeleteInstance={handleDeleteInstance}  // NEW
  onStartInstance={handleStartInstance}    // NEW
  onStopInstance={handleStopInstance}      // NEW
  renderSettingsPanel={...}
/>
```

**Acceptance Criteria:**
- [ ] Instance hooks imported and used
- [ ] instancesByModel mapping computed
- [ ] Instance CRUD handlers implemented
- [ ] ModelCardGrid receives instance props

---

### Task 1.6: Update ModelCardGrid to Pass Instances to ModelCard

**File:** `${PROJECT_DIR}/frontend/src/components/models/ModelCardGrid.tsx`
**Action:** Add instancesByModel prop and pass to ModelCard

**Add to interface:**
```typescript
interface ModelCardGridProps {
  // ... existing props
  instancesByModel?: Record<string, InstanceConfig[]>;
  onCreateInstance?: (modelId: string) => void;
  onDeleteInstance?: (instanceId: string) => Promise<void>;
  onStartInstance?: (instanceId: string) => Promise<void>;
  onStopInstance?: (instanceId: string) => Promise<void>;
}
```

**Pass to ModelCard:**
```typescript
<ModelCard
  key={model.modelId}
  model={model}
  // ... existing props
  instances={instancesByModel?.[model.modelId] || []}
  onCreateInstance={onCreateInstance}
  onDeleteInstance={onDeleteInstance}
  onStartInstance={onStartInstance}
  onStopInstance={onStopInstance}
/>
```

**Acceptance Criteria:**
- [ ] Interface updated with instance props
- [ ] Instances filtered by modelId before passing to ModelCard

---

### Task 1.7: Delete InstancesPage and Update Routes

**Files to DELETE:**
- `${PROJECT_DIR}/frontend/src/pages/InstancesPage/InstancesPage.tsx`
- `${PROJECT_DIR}/frontend/src/pages/InstancesPage/InstancesPage.module.css`
- `${PROJECT_DIR}/frontend/src/pages/InstancesPage/index.ts`

**File to MODIFY:** `${PROJECT_DIR}/frontend/src/router/routes.tsx`
**Action:** Remove lines 9, 51-54

**Remove import (line 9):**
```typescript
// DELETE: import { InstancesPage } from '@/pages/InstancesPage';
```

**Remove route (lines 51-54):**
```typescript
// DELETE:
//       {
//         path: 'instances',
//         element: <InstancesPage />,
//       },
```

**File to MODIFY:** `${PROJECT_DIR}/frontend/src/components/layout/BottomNavBar/BottomNavBar.tsx`
**Action:** Remove INSTANCES nav item from NAV_ITEMS array (line 18)

**Current NAV_ITEMS (lines 14-22):**
```typescript
const NAV_ITEMS: NavItem[] = [
  { key: '1', icon: '⌘', path: '/', label: 'QUERY' },
  { key: '2', icon: '▣', path: '/code-chat', label: 'CODE' },
  { key: '3', icon: '◧', path: '/model-management', label: 'MODELS' },
  { key: '4', icon: '◇', path: '/instances', label: 'INSTANCES' },  // DELETE THIS
  { key: '5', icon: '◈', path: '/metrics', label: 'METRICS' },
  { key: '6', icon: '⚙', path: '/settings', label: 'SETTINGS' },
  { key: '7', icon: '◎', path: '/admin', label: 'ADMIN' },
];
```

**New NAV_ITEMS:**
```typescript
const NAV_ITEMS: NavItem[] = [
  { key: '1', icon: '⌘', path: '/', label: 'QUERY' },
  { key: '2', icon: '▣', path: '/code-chat', label: 'CODE' },
  { key: '3', icon: '◧', path: '/model-management', label: 'MODELS' },
  { key: '4', icon: '◈', path: '/metrics', label: 'METRICS' },
  { key: '5', icon: '⚙', path: '/settings', label: 'SETTINGS' },
  { key: '6', icon: '◎', path: '/admin', label: 'ADMIN' },
];
```

**Acceptance Criteria:**
- [ ] InstancesPage directory deleted
- [ ] /instances route removed
- [ ] INSTANCES nav item removed from BottomNavBar
- [ ] Keyboard shortcut keys renumbered (4-7 become 4-6)
- [ ] No broken imports

---

## Phase 2: PresetSelector Component

**Agent:** frontend-engineer + terminal-ui-specialist
**Duration:** 2-3 hours
**Risk Level:** MEDIUM
**Dependencies:** Phase 4 (SYNAPSE presets must exist)

### Task 2.1: Create PresetSelector Component

**File:** `${PROJECT_DIR}/frontend/src/components/presets/PresetSelector.tsx` (NEW)

**Content:**
```typescript
/**
 * PresetSelector - Chip bar with keyboard shortcuts for quick preset selection
 *
 * Features:
 * - 5 quick-access preset chips (keys 1-5)
 * - Active preset visual indicator (glow + underline)
 * - Collapsible advanced dropdown for all presets
 * - Keyboard shortcuts (1-5) when not in input field
 */

import React, { useState, useEffect, useCallback } from 'react';
import styles from './PresetSelector.module.css';

interface PresetSelectorProps {
  selectedPreset: string;
  onPresetChange: (presetId: string) => void;
  quickPresets?: string[];  // IDs for positions 1-5
  allPresets?: Array<{ id: string; name: string; description: string }>;
  disabled?: boolean;
}

const DEFAULT_QUICK_PRESETS = [
  'SYNAPSE_ANALYST',
  'SYNAPSE_CODER',
  'SYNAPSE_CREATIVE',
  'SYNAPSE_RESEARCH',
  'SYNAPSE_JUDGE'
];

const DEFAULT_ALL_PRESETS = [
  { id: 'SYNAPSE_ANALYST', name: 'ANALYST', description: 'Deep analytical processing' },
  { id: 'SYNAPSE_CODER', name: 'CODER', description: 'Code generation and debugging' },
  { id: 'SYNAPSE_CREATIVE', name: 'CREATIVE', description: 'Divergent thinking and ideation' },
  { id: 'SYNAPSE_RESEARCH', name: 'RESEARCH', description: 'Information gathering and synthesis' },
  { id: 'SYNAPSE_JUDGE', name: 'JUDGE', description: 'Balanced evaluation and moderation' },
];

export const PresetSelector: React.FC<PresetSelectorProps> = ({
  selectedPreset,
  onPresetChange,
  quickPresets = DEFAULT_QUICK_PRESETS,
  allPresets = DEFAULT_ALL_PRESETS,
  disabled = false,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Keyboard shortcuts (1-5) for quick preset switching
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if target is any focusable input element
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement ||
        (e.target as HTMLElement).isContentEditable
      ) {
        return;
      }

      // Only respond to number keys 1-5
      const num = parseInt(e.key);
      if (num >= 1 && num <= 5 && quickPresets[num - 1]) {
        e.preventDefault();
        onPresetChange(quickPresets[num - 1]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [quickPresets, onPresetChange]);

  const getPresetDisplayName = (presetId: string): string => {
    // Extract short name from SYNAPSE_XXX format
    const match = presetId.match(/^SYNAPSE_(.+)$/);
    return match ? match[1] : presetId;
  };

  return (
    <div className={styles.presetSelector}>
      {/* Section Header */}
      <div className={styles.sectionHeader}>
        <span className={styles.headerIcon}>---</span>
        <span className={styles.headerText}>NEURAL PRESET</span>
        <span className={styles.headerLine}>{'─'.repeat(50)}</span>
      </div>

      {/* Chip Bar */}
      <div className={styles.chipBar}>
        {quickPresets.slice(0, 5).map((presetId, index) => (
          <button
            key={presetId}
            className={`${styles.presetChip} ${selectedPreset === presetId ? styles.active : ''}`}
            onClick={() => onPresetChange(presetId)}
            disabled={disabled}
            title={`Press ${index + 1} to select`}
          >
            <span className={styles.chipKey}>[{index + 1}]</span>
            <span className={styles.chipLabel}>{getPresetDisplayName(presetId)}</span>
          </button>
        ))}
      </div>

      {/* Keyboard Hint */}
      <div className={styles.keyboardHint}>
        Press 1-5 to quick-switch presets
      </div>

      {/* Advanced Toggle */}
      <button
        className={styles.advancedToggle}
        onClick={() => setShowAdvanced(!showAdvanced)}
        disabled={disabled}
        aria-expanded={showAdvanced}
      >
        {showAdvanced ? '▼' : '▶'} ADVANCED PRESETS
      </button>

      {/* Advanced Dropdown */}
      {showAdvanced && (
        <div className={styles.advancedDropdown}>
          {allPresets.map((preset) => (
            <button
              key={preset.id}
              className={`${styles.advancedOption} ${selectedPreset === preset.id ? styles.active : ''}`}
              onClick={() => onPresetChange(preset.id)}
              disabled={disabled}
            >
              <span className={styles.optionName}>{preset.name}</span>
              <span className={styles.optionDescription}>{preset.description}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

PresetSelector.displayName = 'PresetSelector';
```

**Acceptance Criteria:**
- [ ] Component renders chip bar with 5 presets
- [ ] Keyboard shortcuts 1-5 work (when not in input)
- [ ] Active preset has visual indicator
- [ ] Advanced dropdown expands/collapses
- [ ] Disabled state works

---

### Task 2.2: Create PresetSelector CSS

**File:** `${PROJECT_DIR}/frontend/src/components/presets/PresetSelector.module.css` (NEW)

**Content:**
```css
/* =============================================
   PRESET SELECTOR - Terminal Aesthetic
   Phosphor Orange Theme (#ff9500)
   ============================================= */

.presetSelector {
  display: flex;
  flex-direction: column;
  gap: var(--webtui-spacing-sm);
  font-family: var(--webtui-font-family);
  padding: var(--webtui-spacing-md);
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 149, 0, 0.3);
}

/* Section Header */
.sectionHeader {
  display: flex;
  align-items: center;
  gap: var(--webtui-spacing-sm);
  color: var(--webtui-primary);
  font-size: var(--webtui-font-size-small);
}

.headerIcon {
  color: var(--webtui-primary);
}

.headerText {
  font-weight: 600;
  letter-spacing: 0.1em;
}

.headerLine {
  flex: 1;
  color: rgba(255, 149, 0, 0.5);
  overflow: hidden;
}

/* Chip Bar */
.chipBar {
  display: flex;
  gap: var(--webtui-spacing-sm);
  align-items: center;
  flex-wrap: wrap;
}

.presetChip {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid var(--webtui-primary);
  color: var(--webtui-primary);
  padding: var(--webtui-spacing-xs) var(--webtui-spacing-sm);
  font-family: var(--webtui-font-family);
  font-size: var(--webtui-font-size-small);
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: var(--webtui-spacing-xs);

  /* GPU acceleration */
  will-change: auto;
  contain: layout style paint;
}

.presetChip:hover:not(:disabled) {
  border-color: var(--webtui-accent);
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.presetChip.active {
  background: rgba(255, 149, 0, 0.15);
  border-color: var(--webtui-primary);
  box-shadow: 0 0 15px rgba(255, 149, 0, 0.4);
  animation: chip-glow 2s ease-in-out infinite;
  position: relative;
}

/* Active indicator underline */
.presetChip.active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--webtui-primary);
  box-shadow: 0 0 8px var(--webtui-primary);
}

.presetChip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes chip-glow {
  0%, 100% {
    box-shadow: 0 0 15px rgba(255, 149, 0, 0.4);
    border-color: var(--webtui-primary);
  }
  50% {
    box-shadow: 0 0 20px rgba(255, 149, 0, 0.6);
    border-color: rgba(255, 149, 0, 0.9);
  }
}

.chipKey {
  color: var(--webtui-text-muted);
  font-size: 10px;
}

.chipLabel {
  font-weight: 500;
}

/* Keyboard Hint */
.keyboardHint {
  color: var(--webtui-text-muted);
  font-size: 10px;
  text-align: center;
  padding: var(--webtui-spacing-xs) 0;
}

/* Advanced Toggle */
.advancedToggle {
  background: transparent;
  border: none;
  color: var(--webtui-text-muted);
  font-family: var(--webtui-font-family);
  font-size: var(--webtui-font-size-small);
  cursor: pointer;
  padding: var(--webtui-spacing-xs) 0;
  text-align: left;
  transition: color 0.2s ease;
}

.advancedToggle:hover:not(:disabled) {
  color: var(--webtui-primary);
}

.advancedToggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Advanced Dropdown */
.advancedDropdown {
  display: flex;
  flex-direction: column;
  gap: var(--webtui-spacing-xs);
  padding-top: var(--webtui-spacing-sm);
  border-top: 1px solid rgba(255, 149, 0, 0.2);
}

.advancedOption {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 149, 0, 0.2);
  color: var(--webtui-text);
  padding: var(--webtui-spacing-sm);
  font-family: var(--webtui-font-family);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.advancedOption:hover:not(:disabled) {
  border-color: var(--webtui-primary);
  background: rgba(255, 149, 0, 0.05);
}

.advancedOption.active {
  border-color: var(--webtui-primary);
  background: rgba(255, 149, 0, 0.1);
  box-shadow: 0 0 10px rgba(255, 149, 0, 0.2);
}

.advancedOption:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.optionName {
  color: var(--webtui-primary);
  font-weight: 500;
  font-size: var(--webtui-font-size-small);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.optionDescription {
  color: var(--webtui-text-muted);
  font-size: 11px;
}
```

**Acceptance Criteria:**
- [ ] Phosphor orange (#ff9500) color theme
- [ ] Active chip has glow animation
- [ ] Active chip has underline indicator
- [ ] Responsive design
- [ ] Hover effects work

---

### Task 2.3: Create Presets Directory Index

**File:** `${PROJECT_DIR}/frontend/src/components/presets/index.ts` (NEW)

**Content:**
```typescript
export { PresetSelector } from './PresetSelector';
```

**Acceptance Criteria:**
- [ ] Export exists and works

---

### Task 2.4: Update QueryInput to Include PresetSelector

**File:** `${PROJECT_DIR}/frontend/src/components/query/QueryInput.tsx`
**Location:** Multiple changes

**Add imports at top:**
```typescript
import { PresetSelector } from '@/components/presets';
```

**Update interface (after line 17):**
```typescript
interface QueryOptions {
  useContext: boolean;
  useWebSearch: boolean;
  maxTokens: number;
  temperature: number;
  presetId?: string;  // NEW
}
```

**Add state (after line 35):**
```typescript
const [selectedPreset, setSelectedPreset] = useState('SYNAPSE_ANALYST');
```

**Update handleSubmit (line 40-46):**
```typescript
const handleSubmit = useCallback(() => {
  if (!query.trim() || isLoading || disabled) return;

  onSubmit(query, {
    useContext,
    useWebSearch,
    maxTokens,
    temperature,
    presetId: selectedPreset,  // NEW
  });
}, [query, useContext, useWebSearch, maxTokens, temperature, selectedPreset, isLoading, disabled, onSubmit]);
```

**Add PresetSelector in JSX (after line 61, before charCounter):**
```tsx
{/* Preset Selector */}
<PresetSelector
  selectedPreset={selectedPreset}
  onPresetChange={setSelectedPreset}
  disabled={isLoading || disabled}
/>
```

**Acceptance Criteria:**
- [ ] PresetSelector renders above query textarea
- [ ] Selected preset passed in query options
- [ ] Keyboard shortcuts work (1-5)

---

### Task 2.5: Create useQuickPresets Hook (localStorage)

**File:** `${PROJECT_DIR}/frontend/src/hooks/useQuickPresets.ts` (NEW)

**Content:**
```typescript
/**
 * useQuickPresets - Manage user's 5 quick-access presets
 *
 * Stores preset order in localStorage for persistence across sessions.
 */

import { useState, useCallback } from 'react';

const STORAGE_KEY = 'synapse_quick_presets';
const DEFAULT_QUICK_PRESETS = [
  'SYNAPSE_ANALYST',
  'SYNAPSE_CODER',
  'SYNAPSE_CREATIVE',
  'SYNAPSE_RESEARCH',
  'SYNAPSE_JUDGE'
];

export const useQuickPresets = () => {
  const [quickPresets, setQuickPresetsState] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : DEFAULT_QUICK_PRESETS;
    } catch {
      return DEFAULT_QUICK_PRESETS;
    }
  });

  const setQuickPresets = useCallback((presets: string[]) => {
    // Ensure exactly 5 presets
    const normalized = presets.slice(0, 5);
    while (normalized.length < 5) {
      normalized.push(DEFAULT_QUICK_PRESETS[normalized.length]);
    }

    setQuickPresetsState(normalized);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
  }, []);

  const resetToDefaults = useCallback(() => {
    setQuickPresetsState(DEFAULT_QUICK_PRESETS);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    quickPresets,
    setQuickPresets,
    resetToDefaults,
    defaultPresets: DEFAULT_QUICK_PRESETS,
  };
};
```

**Acceptance Criteria:**
- [ ] Presets persist in localStorage
- [ ] Defaults work if no stored data
- [ ] Can customize order
- [ ] Reset function works

---

## Phase 3: Council Mode Preset Inheritance

**Agent:** frontend-engineer + backend-architect
**Duration:** 3 hours
**Risk Level:** HIGH (most complex phase)
**Dependencies:** Phase 2 (PresetSelector must exist)

### Task 3.1: Add council_preset_overrides to QueryRequest (Backend)

**Agent:** backend-architect
**File:** `${PROJECT_DIR}/backend/app/models/query.py`
**Location:** After line 100 (after council_participants field)

**Add new field:**
```python
    council_preset_overrides: Optional[Dict[str, str]] = Field(
        default=None,
        alias="councilPresetOverrides",
        description="Per-participant preset overrides for council mode. Key is participant role (pro/con/moderator), value is preset ID."
    )
```

**Acceptance Criteria:**
- [ ] Field added with correct type (Optional[Dict[str, str]])
- [ ] Alias is camelCase for frontend compatibility
- [ ] Description explains usage

---

### Task 3.2: Implement Preset Injection in Council Mode (Backend)

**Agent:** backend-architect
**File:** `${PROJECT_DIR}/backend/app/routers/query.py`
**Location:** In council mode processing section (around line 1850)

**Add helper function (before council processing):**
```python
def get_participant_preset(
    role: str,
    default_preset_id: Optional[str],
    overrides: Optional[Dict[str, str]]
) -> Optional[str]:
    """Get effective preset for a council participant.

    Args:
        role: Participant role (pro, con, moderator)
        default_preset_id: Base preset from query request
        overrides: Per-participant override map

    Returns:
        Effective preset ID for this participant
    """
    if overrides and role in overrides:
        return overrides[role]
    return default_preset_id


def load_preset_system_prompt(preset_id: Optional[str]) -> str:
    """Load system prompt from preset configuration.

    Args:
        preset_id: Preset identifier

    Returns:
        System prompt string, or empty string if not found
    """
    if not preset_id:
        return ""

    try:
        presets_path = Path(__file__).parent.parent / "data" / "custom_presets.json"
        if presets_path.exists():
            with open(presets_path, 'r') as f:
                presets = json.load(f)
            if preset_id in presets and 'system_prompt' in presets[preset_id]:
                return presets[preset_id]['system_prompt']
    except Exception as e:
        logger.warning(f"Failed to load preset {preset_id}: {e}")

    return ""
```

**In council mode processing, apply presets:**
```python
# Determine effective preset for each participant
pro_preset_id = get_participant_preset("pro", request.preset_id, request.council_preset_overrides)
con_preset_id = get_participant_preset("con", request.preset_id, request.council_preset_overrides)
moderator_preset_id = get_participant_preset("moderator", request.preset_id, request.council_preset_overrides)

# Load system prompts
pro_system_prompt = load_preset_system_prompt(pro_preset_id)
con_system_prompt = load_preset_system_prompt(con_preset_id)
moderator_system_prompt = load_preset_system_prompt(moderator_preset_id)

# Prepend system prompts to participant messages
if pro_system_prompt:
    pro_messages.insert(0, {"role": "system", "content": pro_system_prompt})
if con_system_prompt:
    con_messages.insert(0, {"role": "system", "content": con_system_prompt})
if moderator_system_prompt:
    moderator_messages.insert(0, {"role": "system", "content": moderator_system_prompt})
```

**Acceptance Criteria:**
- [ ] Helper functions implemented
- [ ] Presets loaded from custom_presets.json
- [ ] System prompts injected per-participant
- [ ] Inheritance works (uses default if no override)

---

### Task 3.3: Update ModeSelector with Preset Inheritance UI (Frontend)

**Agent:** frontend-engineer
**File:** `${PROJECT_DIR}/frontend/src/components/modes/ModeSelector.tsx`
**Location:** Multiple changes

**Update ModeConfig interface (after line 21):**
```typescript
export interface ModeConfig {
  adversarial?: boolean;
  serial?: boolean;
  councilMaxTurns?: number;
  councilDynamicTermination?: boolean;
  councilPersonaProfile?: string;
  councilPersonas?: {
    pro?: string;
    con?: string;
  };
  councilModerator?: boolean;
  councilModeratorActive?: boolean;
  councilModeratorModel?: string;
  councilProModel?: string;
  councilConModel?: string;
  // NEW: Preset inheritance
  councilPresetOverrides?: Record<string, string>;  // role -> presetId
}
```

**Update props interface (after line 25):**
```typescript
interface ModeSelectorProps {
  currentMode: QueryMode;
  onModeChange: (mode: QueryMode, config?: ModeConfig) => void;
  queryPreset?: string;  // NEW: Current query preset for inheritance display
}
```

**Add state for preset overrides (after line 81):**
```typescript
// Preset override state
const [presetOverrides, setPresetOverrides] = useState<Record<string, string>>({});
```

**Add preset override handler:**
```typescript
const handlePresetOverride = (role: string, presetId: string | null) => {
  setPresetOverrides(prev => {
    if (presetId === null || presetId === 'inherited') {
      // Remove override - use inherited
      const { [role]: _, ...rest } = prev;
      return rest;
    }
    return { ...prev, [role]: presetId };
  });
  // Update config
  updateCouncilConfig();
};
```

**Add to council config section (around line 302-365, in Model Selection section):**
```tsx
{/* Preset Configuration Section - NEW */}
<div className={styles.configSection}>
  <h4 className={styles.sectionTitle}>Preset Configuration</h4>

  <div className={styles.presetInfo}>
    <span className={styles.presetLabel}>Query Preset:</span>
    <span className={styles.presetValue}>{queryPreset || 'DEFAULT'}</span>
  </div>

  <div className={styles.participantPresets}>
    {/* PRO Participant Preset */}
    <div className={styles.configOption}>
      <label className={styles.configLabel}>PRO Preset</label>
      <select
        value={presetOverrides.pro || 'inherited'}
        onChange={(e) => handlePresetOverride('pro', e.target.value === 'inherited' ? null : e.target.value)}
        className={styles.select}
      >
        <option value="inherited">INHERITED ({queryPreset || 'DEFAULT'})</option>
        <option value="SYNAPSE_ANALYST">SYNAPSE_ANALYST</option>
        <option value="SYNAPSE_CODER">SYNAPSE_CODER</option>
        <option value="SYNAPSE_CREATIVE">SYNAPSE_CREATIVE</option>
        <option value="SYNAPSE_RESEARCH">SYNAPSE_RESEARCH</option>
        <option value="SYNAPSE_JUDGE">SYNAPSE_JUDGE</option>
      </select>
      {presetOverrides.pro && (
        <span className={styles.overrideIndicator}>(Override)</span>
      )}
    </div>

    {/* CON Participant Preset */}
    <div className={styles.configOption}>
      <label className={styles.configLabel}>CON Preset</label>
      <select
        value={presetOverrides.con || 'inherited'}
        onChange={(e) => handlePresetOverride('con', e.target.value === 'inherited' ? null : e.target.value)}
        className={styles.select}
      >
        <option value="inherited">INHERITED ({queryPreset || 'DEFAULT'})</option>
        <option value="SYNAPSE_ANALYST">SYNAPSE_ANALYST</option>
        <option value="SYNAPSE_CODER">SYNAPSE_CODER</option>
        <option value="SYNAPSE_CREATIVE">SYNAPSE_CREATIVE</option>
        <option value="SYNAPSE_RESEARCH">SYNAPSE_RESEARCH</option>
        <option value="SYNAPSE_JUDGE">SYNAPSE_JUDGE</option>
      </select>
      {presetOverrides.con && (
        <span className={styles.overrideIndicator}>(Override)</span>
      )}
    </div>

    {/* Moderator Preset (only if moderator enabled) */}
    {councilModerator && (
      <div className={styles.configOption}>
        <label className={styles.configLabel}>Moderator Preset</label>
        <select
          value={presetOverrides.moderator || 'inherited'}
          onChange={(e) => handlePresetOverride('moderator', e.target.value === 'inherited' ? null : e.target.value)}
          className={styles.select}
        >
          <option value="inherited">INHERITED ({queryPreset || 'DEFAULT'})</option>
          <option value="SYNAPSE_ANALYST">SYNAPSE_ANALYST</option>
          <option value="SYNAPSE_CODER">SYNAPSE_CODER</option>
          <option value="SYNAPSE_CREATIVE">SYNAPSE_CREATIVE</option>
          <option value="SYNAPSE_RESEARCH">SYNAPSE_RESEARCH</option>
          <option value="SYNAPSE_JUDGE">SYNAPSE_JUDGE (Recommended)</option>
        </select>
        {presetOverrides.moderator && (
          <span className={styles.overrideIndicator}>(Override)</span>
        )}
      </div>
    )}
  </div>

  <div className={styles.presetHint}>
    Participants inherit query preset by default. Override to customize behavior.
  </div>
</div>
```

**Update updateCouncilConfig to include preset overrides:**
```typescript
const updateCouncilConfig = () => {
  onModeChange('council', {
    adversarial: isAdversarial,
    councilMaxTurns,
    councilDynamicTermination,
    councilPersonaProfile: councilPersonaProfile || undefined,
    councilPersonas: !councilPersonaProfile && (councilPersonaPro || councilPersonaCon)
      ? { pro: councilPersonaPro, con: councilPersonaCon }
      : undefined,
    councilModerator,
    councilModeratorActive,
    councilModeratorModel: councilModeratorModel || undefined,
    councilProModel: councilProModel || undefined,
    councilConModel: councilConModel || undefined,
    councilPresetOverrides: Object.keys(presetOverrides).length > 0
      ? presetOverrides
      : undefined,  // NEW
  });
};
```

**Acceptance Criteria:**
- [ ] queryPreset prop added
- [ ] Preset override UI renders for pro, con, moderator
- [ ] "INHERITED" shows default preset name
- [ ] Override indicator shows "(Override)" label
- [ ] Config includes councilPresetOverrides

---

### Task 3.4: Add Preset Override CSS

**File:** `${PROJECT_DIR}/frontend/src/components/modes/ModeSelector.module.css`
**Location:** Add at end of file

**Add CSS:**
```css
/* =============================================
   PRESET CONFIGURATION STYLES
   ============================================= */

.presetInfo {
  display: flex;
  align-items: center;
  gap: var(--webtui-spacing-sm);
  padding: var(--webtui-spacing-sm);
  background: rgba(255, 149, 0, 0.05);
  border: 1px solid rgba(255, 149, 0, 0.2);
  margin-bottom: var(--webtui-spacing-md);
}

.presetLabel {
  color: var(--webtui-text-muted);
  font-size: var(--webtui-font-size-small);
}

.presetValue {
  color: var(--webtui-primary);
  font-weight: 500;
}

.participantPresets {
  display: flex;
  flex-direction: column;
  gap: var(--webtui-spacing-sm);
}

.overrideIndicator {
  color: var(--webtui-accent);
  font-size: 10px;
  margin-left: var(--webtui-spacing-xs);
}

.presetHint {
  color: var(--webtui-text-muted);
  font-size: 11px;
  margin-top: var(--webtui-spacing-sm);
  padding: var(--webtui-spacing-xs);
  border-left: 2px solid var(--webtui-primary);
}
```

**Acceptance Criteria:**
- [ ] Phosphor orange theme
- [ ] Override indicator visible
- [ ] Hint styled appropriately

---

### Task 3.5: Pass queryPreset to ModeSelector from HomePage

**Agent:** frontend-engineer
**File:** `${PROJECT_DIR}/frontend/src/pages/HomePage/HomePage.tsx`
**Location:** Where ModeSelector is rendered

**Add state for selected preset (if not already):**
```typescript
const [selectedPreset, setSelectedPreset] = useState('SYNAPSE_ANALYST');
```

**Pass to ModeSelector:**
```tsx
<ModeSelector
  currentMode={queryMode}
  onModeChange={handleModeChange}
  queryPreset={selectedPreset}  // NEW
/>
```

**Acceptance Criteria:**
- [ ] selectedPreset state exists in HomePage
- [ ] ModeSelector receives queryPreset prop

---

## Phase 5: Testing & Verification

**Agent:** testing-specialist
**Duration:** 1-2 hours
**Risk Level:** LOW
**Dependencies:** All phases complete

### Task 5.1: Phase 1 Tests (Instance Controls)

**Manual Testing Checklist:**
- [ ] Navigate to Model Management page
- [ ] Expand a model card (click DETAILS)
- [ ] Verify instance section appears (if model has instances)
- [ ] Click "+ ADD INSTANCE" - verify creation flow
- [ ] Click "EDIT" on instance - verify edit modal opens
- [ ] Click "START" on stopped instance - verify it starts
- [ ] Click "STOP" on active instance - verify it stops
- [ ] Verify bottom nav bar no longer has INSTANCES item
- [ ] Verify /instances route returns 404

### Task 5.2: Phase 2 Tests (PresetSelector)

**Manual Testing Checklist:**
- [ ] Navigate to Query page (/)
- [ ] Verify PresetSelector appears above query input
- [ ] Click each preset chip - verify active state changes
- [ ] Press keys 1-5 (when not in textarea) - verify preset changes
- [ ] Type in textarea, press 1-5 - verify NO preset change (input focus)
- [ ] Click "ADVANCED PRESETS" - verify dropdown expands
- [ ] Select preset from dropdown - verify it becomes active
- [ ] Submit query - verify preset_id in network request

### Task 5.3: Phase 3 Tests (Council Presets)

**Manual Testing Checklist:**
- [ ] Navigate to Query page
- [ ] Select COUNCIL mode
- [ ] Verify "Preset Configuration" section appears
- [ ] Verify query preset displayed correctly
- [ ] All participant presets show "INHERITED" by default
- [ ] Select override for PRO - verify "(Override)" label appears
- [ ] Select override for CON - verify "(Override)" label appears
- [ ] Enable Moderator - verify moderator preset dropdown appears
- [ ] Submit council query - verify councilPresetOverrides in request
- [ ] Verify backend injects correct system prompts (check logs)

### Task 5.4: Phase 4 Tests (SYNAPSE Presets)

**Manual Testing Checklist:**
- [ ] Check backend/data/custom_presets.json is valid JSON
- [ ] Verify all 5 presets present
- [ ] Each preset has system_prompt field
- [ ] System prompts reference "S.Y.N.A.P.S.E. ENGINE"
- [ ] API returns presets: `curl http://localhost:8000/api/code-chat/presets`

### Task 5.5: Integration Tests

**Automated Test Suggestions:**
```typescript
// frontend/src/components/presets/__tests__/PresetSelector.test.tsx
describe('PresetSelector', () => {
  it('renders 5 preset chips', () => {});
  it('highlights active preset', () => {});
  it('responds to keyboard shortcuts 1-5', () => {});
  it('ignores keyboard when input focused', () => {});
  it('expands advanced dropdown', () => {});
  it('calls onPresetChange when chip clicked', () => {});
});

// frontend/src/components/models/__tests__/ModelCard.test.tsx
describe('ModelCard with instances', () => {
  it('shows instance section when expanded with instances', () => {});
  it('hides instance section when no instances', () => {});
  it('calls onCreateInstance when add button clicked', () => {});
  it('calls onStartInstance/onStopInstance appropriately', () => {});
});
```

**Acceptance Criteria:**
- [ ] All manual tests pass
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] No visual regressions

---

## Parallel Execution Opportunities

The following tasks can run in parallel:

| Group | Tasks | Agents |
|-------|-------|--------|
| A | Phase 4 (all tasks) | backend-architect |
| A | Phase 1, Tasks 1.1-1.4 | frontend-engineer |
| B | Phase 1, Tasks 1.5-1.7 | frontend-engineer (after A) |
| B | Phase 2, Tasks 2.1-2.3 | terminal-ui-specialist (after Phase 4) |
| C | Phase 2, Tasks 2.4-2.5 | frontend-engineer (after 2.1-2.3) |
| D | Phase 3, Task 3.1-3.2 | backend-architect (after Phase 4) |
| D | Phase 3, Tasks 3.3-3.5 | frontend-engineer (after Phase 2) |
| E | Phase 5 (all tests) | testing-specialist (after all) |

**Optimal Parallel Schedule:**
1. **Hour 1:** Phase 4 (backend) + Phase 1 Tasks 1.1-1.4 (frontend)
2. **Hour 2-3:** Phase 1 Tasks 1.5-1.7 + Phase 2 Tasks 2.1-2.3
3. **Hour 4:** Phase 2 Tasks 2.4-2.5 + Phase 3 Tasks 3.1-3.2
4. **Hour 5-6:** Phase 3 Tasks 3.3-3.5
5. **Hour 7:** Phase 5 Testing

---

## Risk Mitigation

### High Risk Areas

| Risk | Mitigation | Owner |
|------|------------|-------|
| ModelCard memo comparison breaks | Test with React DevTools highlighting | frontend-engineer |
| Keyboard shortcuts conflict | Check all global handlers first | frontend-engineer |
| Council preset injection fails | Add extensive logging | backend-architect |
| Route deletion causes 404s | Verify all internal links updated | frontend-engineer |
| Instance section layout breaks | Test responsive design | terminal-ui-specialist |

### Rollback Plan

If any phase fails:
1. **Phase 4:** Restore original custom_presets.json from git
2. **Phase 1:** Revert ModelCard.tsx, keep InstancesPage
3. **Phase 2:** Remove PresetSelector, update QueryInput
4. **Phase 3:** Remove councilPresetOverrides, restore ModeSelector

### Blockers to Watch

1. **Instance API not responding** - Check backend logs, verify routes mounted
2. **Presets not loading** - Check JSON parse errors, file path
3. **Keyboard shortcuts not working** - Check event listener order
4. **Council mode broken** - Check request payload structure

---

## Verification Checkpoints

### Checkpoint 1: After Phase 4
- [ ] Backend starts without errors
- [ ] `curl http://localhost:8000/api/code-chat/presets` returns 5 presets
- [ ] Each preset has system_prompt field

### Checkpoint 2: After Phase 1
- [ ] ModelManagementPage loads without errors
- [ ] Model cards expand/collapse correctly
- [ ] Instance section appears when instances exist
- [ ] INSTANCES nav item removed
- [ ] /instances returns 404

### Checkpoint 3: After Phase 2
- [ ] PresetSelector renders on Query page
- [ ] Keys 1-5 switch presets (when not in input)
- [ ] Active preset has glow effect
- [ ] Advanced dropdown works

### Checkpoint 4: After Phase 3
- [ ] Council mode shows preset configuration
- [ ] Override dropdowns work
- [ ] "(Override)" label appears correctly
- [ ] Request includes councilPresetOverrides
- [ ] Backend logs show preset injection

### Checkpoint 5: Final
- [ ] All features work end-to-end
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] Docker build succeeds
- [ ] All manual tests pass

---

## Agent Instructions Summary

### backend-architect

**Your Tasks:** Phase 4 (all), Phase 3 (Tasks 3.1-3.2)

**Start Command:**
```
Implement Phase 4: Update backend/data/custom_presets.json with 5 SYNAPSE presets per the work breakdown document.
```

**Key Files:**
- `${PROJECT_DIR}/backend/data/custom_presets.json`
- `${PROJECT_DIR}/backend/app/models/query.py`
- `${PROJECT_DIR}/backend/app/routers/query.py`

---

### frontend-engineer

**Your Tasks:** Phase 1 (all), Phase 2 (Tasks 2.4-2.5), Phase 3 (Tasks 3.3-3.5)

**Start Command:**
```
Implement Phase 1: Add instance controls to ModelCard and delete InstancesPage per the work breakdown document.
```

**Key Files:**
- `${PROJECT_DIR}/frontend/src/components/models/ModelCard.tsx`
- `${PROJECT_DIR}/frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx`
- `${PROJECT_DIR}/frontend/src/components/query/QueryInput.tsx`
- `${PROJECT_DIR}/frontend/src/components/modes/ModeSelector.tsx`

---

### terminal-ui-specialist

**Your Tasks:** Phase 2 (Tasks 2.1-2.3)

**Start Command:**
```
Implement Phase 2 Tasks 2.1-2.3: Create PresetSelector component with phosphor orange theme per the work breakdown document.
```

**Key Files:**
- `${PROJECT_DIR}/frontend/src/components/presets/PresetSelector.tsx` (NEW)
- `${PROJECT_DIR}/frontend/src/components/presets/PresetSelector.module.css` (NEW)

**Critical Requirements:**
- Phosphor orange (#ff9500) color theme
- Active chip glow animation
- Edge-to-edge dividers (NO box corners)
- Keyboard shortcuts 1-5

---

### testing-specialist

**Your Tasks:** Phase 5 (all)

**Start Command:**
```
Execute Phase 5: Test all phases per the work breakdown document testing checklist.
```

**Key Areas:**
- Instance CRUD in ModelCard
- PresetSelector keyboard shortcuts
- Council mode preset inheritance
- Backend preset injection

---

## Document Metadata

**Created:** 2025-11-30
**Author:** strategic-planning-architect
**Version:** 1.0
**Related Documents:**
- [2025-11-30_instance-preset-unification.md](./2025-11-30_instance-preset-unification.md)
- [SESSION_NOTES.md](../../SESSION_NOTES.md)
- [CLAUDE.md](../../CLAUDE.md)
