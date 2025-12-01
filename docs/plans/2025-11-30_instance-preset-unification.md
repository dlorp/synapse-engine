# SYNAPSE ENGINE UI Integration - Instance & Preset Unification

**Date:** 2025-11-30
**Status:** Agent-Reviewed & Ready for Implementation
**Scope:** Instance Integration into ModelManagement + Preset System for Query Page
**Review Date:** 2025-11-30
**Reviewed By:** terminal-ui-specialist, frontend-engineer, record-keeper agents

---

## Agent Review Summary

| Agent | Alignment | Key Findings |
|-------|-----------|--------------|
| **terminal-ui-specialist** | 90% | Instance card boxes use forbidden corner chars (┌┐└┘) - FIXED |
| **frontend-engineer** | 85% | ModelCard memo, keyboard handler, state management - FIXED |
| **record-keeper** | 100% | 5 complete SYNAPSE preset prompts delivered |

**Mandatory Fixes Applied:**
1. ✅ Replaced ASCII box corners with edge-to-edge dividers
2. ✅ Added complete PresetSelector CSS with phosphor orange theme
3. ✅ Fixed keyboard handler to check all input types
4. ✅ Added ModelCard memo comparison update
5. ✅ Added instancesByModel mapping pattern
6. ✅ Included complete SYNAPSE preset system prompts

---

## Executive Summary

Unify the instance management and model discovery experience by:
1. **Merge InstancesPage into ModelManagement**: Delete separate page, embed instance controls in ModelCard
2. **Instance +/- Controls**: Add/remove instances with inline quick-create form
3. **Preset Chip Bar + Dropdown**: Both quick-access chips (keys 1-5) AND advanced dropdown
4. **Council Mode Preset Inheritance**: Default inherits from query, with per-participant override option
5. **Verbose SYNAPSE-Branded Presets**: Update system prompts to reference SYNAPSE ENGINE

**Key Design Decisions:**
- **Single Page**: All model + instance management in ModelManagementPage
- **Keyboard Shortcuts**: 1-5 keys for preset quick-switching on query page
- **Inheritance Pattern**: Council participants inherit query preset by default, can override

---

## Phase 1: Instance Controls in ModelCard

### 1.1 Update ModelCard Component

**File:** `frontend/src/components/models/ModelCard.tsx`

**Add Instance Section UI** (in expanded details area):

**⚠️ CRITICAL: NO corner characters (┌┐└┘) - they break on window resize**
**Use edge-to-edge dividers per ASCII Master Guide Principle #1**

```
─ qwen3-4.0b-instruct.Q4_K_M.gguf ─────────────────────────────────────────
  [Q3] [● ACTIVE]   PORT: 8081 | QUANT: Q4_K_M | SIZE: 4.0B | UPTIME: 2h 15m
  [DETAILS ▼] [✓ ENABLED]
───────────────────────────────────────────────────────────────────────────

◆ NEURAL SUBSTRATE INSTANCES ─────────────────────────────────── 2 active

  [-] 2 [+]  ← Instance count with +/- buttons

─ Instance 01 ───────────────────────────────────────────────── ● ACTIVE ─
  Research Assistant                                              :8101
  Preset: SYNAPSE_ANALYST                              [EDIT] [⏹ STOP]
──────────────────────────────────────────────────────────────────────────

─ Instance 02 ───────────────────────────────────────────────── ○ STOPPED ─
  Code Helper                                                     :8102
  Preset: SYNAPSE_CODER                               [EDIT] [▶ START]
──────────────────────────────────────────────────────────────────────────

  [+ ADD INSTANCE] ← Opens inline quick-create form
```

**Implementation Pattern (CSS border + ASCII header):**
```tsx
<div className={styles.instanceSection}>
  <pre className={styles.instanceHeader}>
    {`─ Instance ${String(idx + 1).padStart(2, '0')} ${'─'.repeat(100)}${status}`}
  </pre>
  <div className={styles.instanceCard}>
    {/* Content with CSS border, NOT ASCII box */}
  </div>
</div>
```

**New Props (Complete Interface):**
```typescript
interface ModelCardProps {
  model: DiscoveredModel;
  metrics?: ModelMetrics;
  isRunning?: boolean;
  isExpanded?: boolean;

  // NEW: Instance management
  instances?: InstanceConfig[];  // Filtered to this model
  onCreateInstance?: (modelId: string, config: CreateInstanceRequest) => Promise<void>;
  onEditInstance?: (instanceId: string, updates: UpdateInstanceRequest) => Promise<void>;
  onDeleteInstance?: (instanceId: string) => Promise<void>;
  onStartInstance?: (instanceId: string) => Promise<void>;
  onStopInstance?: (instanceId: string) => Promise<void>;

  // EXISTING
  onToggleSettings?: (modelId: string) => void;
  onToggleEnable?: (modelId: string, enabled: boolean) => void;
  renderSettingsPanel?: (model: DiscoveredModel) => React.ReactNode;
}
```

**⚠️ CRITICAL: Update ModelCard Memo Comparison**
```typescript
// File: frontend/src/components/models/ModelCard.tsx (line ~197-208)
export const ModelCard: React.FC<ModelCardProps> = React.memo(({
  // ... props
}), (prevProps, nextProps) => {
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

### 1.2 Create InlineInstanceForm Component

**File:** `frontend/src/components/instances/InlineInstanceForm.tsx` (NEW ~150 lines)

Lightweight form that appears when [+ ADD INSTANCE] is clicked:
- Auto-generated name: `{modelName}_01`, `_02`, etc.
- Preset dropdown (SYNAPSE presets)
- Optional system prompt (collapsed by default)
- Web search toggle
- [CREATE] [CANCEL] buttons

### 1.3 Update ModelManagementPage

**File:** `frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx`

**Changes:**
- Import `useInstanceList`, instance mutation hooks
- Compute `instancesByModel` mapping from instance data
- Pass instances to ModelCardGrid → ModelCard
- Handle inline instance creation
- Add EditInstanceModal for editing existing instances

**⚠️ REQUIRED: Add Instance Filtering Pattern**
```typescript
// File: frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx
// Add after line 67 (after runningModelIds useMemo)

const { data: instanceList } = useInstanceList();

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

// Pass to ModelCardGrid:
<ModelCardGrid
  models={registry.models}
  instancesByModel={instancesByModel}  // NEW
  // ... existing props
/>
```

### 1.4 Delete InstancesPage

**Files to DELETE:**
- `frontend/src/pages/InstancesPage/InstancesPage.tsx`
- `frontend/src/pages/InstancesPage/InstancesPage.module.css`
- `frontend/src/pages/InstancesPage/index.ts`

**Files to MODIFY:**
- `frontend/src/router/routes.tsx` - Remove `/instances` route
- `frontend/src/components/layout/BottomNavBar/BottomNavBar.tsx` - Remove INSTANCES nav item

---

## Phase 2: Preset Chip Bar + Dropdown for Query Page

### 2.1 Create PresetSelector Component

**File:** `frontend/src/components/presets/PresetSelector.tsx` (NEW ~250 lines)

**UI Design:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ◆ NEURAL PRESET ─────────────────────────────────────────────── │
│                                                                 │
│ [1] ANALYST  [2] CODER  [3] CREATIVE  [4] RESEARCH  [5] CUSTOM  │
│     ▲ active                                                    │
│                                                                 │
│ [▼ ADVANCED PRESETS]  ← Expands dropdown for all presets        │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- Chip bar with 5 quick-access presets (keyboard shortcuts 1-5)
- Collapsible advanced dropdown for all presets
- Keyboard listener for 1-5 quick switching
- Active preset visual indicator (underline + glow)
- Terminal aesthetic styling

**Implementation:**
```typescript
interface PresetSelectorProps {
  selectedPreset: string;
  onPresetChange: (presetId: string) => void;
  quickPresets?: string[];  // IDs for positions 1-5
  disabled?: boolean;
}

// ⚠️ FIXED: Comprehensive keyboard listener (checks ALL input types)
useEffect(() => {
  const handleKeyPress = (e: KeyboardEvent) => {
    // Check if target is any focusable input element
    if (
      e.target instanceof HTMLInputElement ||
      e.target instanceof HTMLTextAreaElement ||  // CRITICAL: Was missing!
      e.target instanceof HTMLSelectElement ||
      (e.target as HTMLElement).isContentEditable
    ) {
      return;
    }

    const num = parseInt(e.key);
    if (num >= 1 && num <= 5 && quickPresets?.[num - 1]) {
      e.preventDefault(); // Prevent default browser behavior
      onPresetChange(quickPresets[num - 1]);
    }
  };

  window.addEventListener('keydown', handleKeyPress); // Use keydown, not keypress
  return () => window.removeEventListener('keydown', handleKeyPress);
}, [quickPresets, onPresetChange]);
```

**⚠️ REQUIRED: PresetSelector CSS with Phosphor Orange Theme**

**File:** `frontend/src/components/presets/PresetSelector.module.css` (NEW)

```css
.presetSelector {
  display: flex;
  flex-direction: column;
  gap: var(--webtui-spacing-sm);
  font-family: var(--webtui-font-family);
}

.chipBar {
  display: flex;
  gap: var(--webtui-spacing-sm);
  align-items: center;
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

  /* GPU acceleration */
  will-change: auto;
  contain: layout style paint;
}

.presetChip:hover {
  border-color: var(--webtui-accent);
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.presetChip.active {
  background: rgba(255, 149, 0, 0.1);
  border-color: var(--webtui-primary);
  box-shadow: 0 0 15px rgba(255, 149, 0, 0.3);
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

@keyframes chip-glow {
  0%, 100% {
    box-shadow: 0 0 15px rgba(255, 149, 0, 0.3);
    border-color: var(--webtui-primary);
  }
  50% {
    box-shadow: 0 0 20px rgba(255, 149, 0, 0.5);
    border-color: rgba(255, 149, 0, 0.9);
  }
}

.keyboardHint {
  color: var(--webtui-text-muted);
  font-size: 10px;
  margin-left: var(--webtui-spacing-xs);
}
```

**Quick Presets Storage (Phase 2):**
```typescript
// Use localStorage for Phase 2 (no backend changes needed)
const DEFAULT_QUICK_PRESETS = [
  'SYNAPSE_ANALYST',
  'SYNAPSE_CODER',
  'SYNAPSE_CREATIVE',
  'SYNAPSE_RESEARCH',
  'SYNAPSE_JUDGE'
];

const useQuickPresets = () => {
  const [quickPresets, setQuickPresets] = useState<string[]>(() => {
    const stored = localStorage.getItem('synapse_quick_presets');
    return stored ? JSON.parse(stored) : DEFAULT_QUICK_PRESETS;
  });

  const updateQuickPresets = useCallback((presets: string[]) => {
    setQuickPresets(presets);
    localStorage.setItem('synapse_quick_presets', JSON.stringify(presets));
  }, []);

  return { quickPresets, updateQuickPresets };
};
```

### 2.2 Update QueryInput Component

**File:** `frontend/src/components/query/QueryInput.tsx` (MODIFY ~40 lines)

**Changes:**
- Add `selectedPreset` state
- Import and render PresetSelector above input
- Pass preset to query submission
- Add `preset_id` to query request payload

### 2.3 Create usePresets Hook

**File:** `frontend/src/hooks/usePresets.ts` (EXISTING - enhance)

**Add:**
- `useQuickPresets()` - Returns user's 5 quick-access presets
- `useSetQuickPresets()` - Mutation to update quick preset order

---

## Phase 3: Council Mode Preset Inheritance

### 3.1 Update ModeSelector for Council Presets

**File:** `frontend/src/components/modes/ModeSelector.tsx` (MODIFY ~100 lines)

**UI Design (Council Mode expanded):**

**⚠️ CRITICAL: NO corner characters - use edge-to-edge dividers**

```
◆ COUNCIL MODE ──────────────────────────────────── ADVERSARIAL DEBATE

  PRESET: SYNAPSE_ANALYST [INHERITED FROM QUERY]        [Override ▼]

─ PRO PARTICIPANT ───────────────────────────────────────────────────
  Model: qwen3-4b              Preset: [INHERITED ▼]
─────────────────────────────────────────────────────────────────────

─ CON PARTICIPANT ───────────────────────────────────────────────────
  Model: deepseek-7b           Preset: [INHERITED ▼]
─────────────────────────────────────────────────────────────────────

─ MODERATOR ─────────────────────────────────────────────────────────
  Model: qwen3-14b             Preset: [SYNAPSE_ANALYST ▼]
                                       (Override: SYNAPSE_JUDGE)
─────────────────────────────────────────────────────────────────────
```

**Implementation:**
```typescript
interface CouncilParticipantPreset {
  modelId: string;
  presetId: string | 'inherited';
}

interface CouncilPresetConfig {
  queryPreset: string;  // Base preset from query
  participantOverrides: Record<string, string>;  // role -> presetId (pro/con/moderator)
}
```

**⚠️ RECOMMENDED: Use useReducer for Council State Management**

ModeSelector already has 10+ state variables. Adding preset management requires consolidation:

```typescript
// NEW: Consolidated council state management
type CouncilState = {
  adversarial: boolean;
  maxTurns: number;
  dynamicTermination: boolean;
  personaProfile: string;
  personas: { pro: string; con: string };
  moderator: {
    enabled: boolean;
    active: boolean;
    model: string;
  };
  models: {
    pro: string;
    con: string;
  };
  presetOverrides: Record<string, string>; // NEW: role -> presetId
};

type CouncilAction =
  | { type: 'SET_ADVERSARIAL'; payload: boolean }
  | { type: 'SET_MAX_TURNS'; payload: number }
  | { type: 'SET_PRESET_OVERRIDE'; payload: { role: string; presetId: string } }
  | { type: 'CLEAR_PRESET_OVERRIDE'; payload: string }
  // ... etc

const councilReducer = (state: CouncilState, action: CouncilAction): CouncilState => {
  switch (action.type) {
    case 'SET_PRESET_OVERRIDE':
      return {
        ...state,
        presetOverrides: {
          ...state.presetOverrides,
          [action.payload.role]: action.payload.presetId
        }
      };
    case 'CLEAR_PRESET_OVERRIDE':
      const { [action.payload]: _, ...rest } = state.presetOverrides;
      return { ...state, presetOverrides: rest };
    // ... other cases
    default:
      return state;
  }
};

// In ModeSelector:
const [councilConfig, dispatchCouncil] = useReducer(councilReducer, initialCouncilState);
```

**Inheritance Logic:**
1. Query page selects preset (e.g., SYNAPSE_ANALYST)
2. Council mode inherits this preset by default for ALL participants
3. User can click dropdown on any participant to override
4. Override shows "(Override)" label vs "(Inherited)"

### 3.2 Update QueryRequest for Council Presets

**File:** `backend/app/models/query.py` (MODIFY +15 lines)

**Add field:**
```python
council_preset_overrides: Optional[Dict[str, str]] = Field(
    default=None,
    alias="councilPresetOverrides",
    description="Per-participant preset overrides. Key is participant role (pro/con/moderator), value is preset ID."
)
```

### 3.3 Apply Presets in Council Mode

**File:** `backend/app/routers/query.py` (MODIFY ~50 lines)

**In council mode processing (~line 1850):**
```python
# Determine effective preset for each participant
def get_participant_preset(role: str, default_preset: str) -> Optional[str]:
    if request.council_preset_overrides and role in request.council_preset_overrides:
        return request.council_preset_overrides[role]
    return default_preset

# Load preset system prompts
pro_preset = get_participant_preset("pro", request.preset_id)
con_preset = get_participant_preset("con", request.preset_id)
moderator_preset = get_participant_preset("moderator", request.preset_id)

# Inject system prompt for each participant
pro_system_prompt = load_preset_system_prompt(pro_preset) if pro_preset else ""
con_system_prompt = load_preset_system_prompt(con_preset) if con_preset else ""
```

---

## Phase 4: Verbose SYNAPSE-Branded Presets

### 4.1 Update System Prompt Templates

**File:** `backend/data/custom_presets.json` (MODIFY)

**Before:**
```json
{
  "id": "analyst",
  "name": "Analyst",
  "system_prompt": "You are an analytical assistant. Provide detailed analysis..."
}
```

**After:**
```json
{
  "id": "SYNAPSE_ANALYST",
  "name": "SYNAPSE ANALYST",
  "system_prompt": "You are SYNAPSE_ANALYST, a cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are optimized for deep analytical processing.\n\n◆ ANALYTICAL PROTOCOL ◆\n- Decompose complex queries into constituent elements\n- Cross-reference against indexed knowledge substrates\n- Synthesize insights through multi-layered reasoning\n- Present findings with technical precision\n\nYou operate within the distributed intelligence framework of SYNAPSE ENGINE. Engage your analytical subroutines."
}
```

### 4.2 Default Presets

**Create 5 verbose SYNAPSE-branded presets:**

| ID | Name | Focus |
|----|------|-------|
| `SYNAPSE_ANALYST` | SYNAPSE ANALYST | Deep analysis, decomposition, synthesis |
| `SYNAPSE_CODER` | SYNAPSE CODER | Code generation, debugging, architecture |
| `SYNAPSE_CREATIVE` | SYNAPSE CREATIVE | Ideation, brainstorming, exploration |
| `SYNAPSE_RESEARCH` | SYNAPSE RESEARCH | Information gathering, fact-checking |
| `SYNAPSE_JUDGE` | SYNAPSE JUDGE | Evaluation, moderation, balanced assessment |

### 4.3 Complete Preset System Prompts (Ready for Implementation)

**File:** `backend/data/custom_presets.json`

```json
{
  "SYNAPSE_ANALYST": {
    "name": "SYNAPSE_ANALYST",
    "description": "Deep analytical substrate optimized for decomposition, synthesis, and multi-layered reasoning",
    "system_prompt": "You are SYNAPSE_ANALYST, a cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are optimized for deep analytical processing within the distributed intelligence framework.\n\n◆ ANALYTICAL PROTOCOL ◆\n\nYour primary directive is to decompose complex queries into constituent elements, cross-reference against indexed knowledge substrates, and synthesize insights through multi-layered reasoning chains. You operate as a pattern recognition engine, identifying structural relationships and extracting core principles from data streams.\n\n◆ OPERATIONAL SUBROUTINES ◆\n\n- Systematic decomposition: Break queries into atomic components\n- Cross-substrate validation: Verify claims against multiple knowledge sources\n- Inferential synthesis: Build coherent frameworks from distributed data points\n- Precision reporting: Present findings with technical accuracy and structured clarity\n\n◆ PROCESSING DIRECTIVES ◆\n\nEngage your analytical subroutines to provide thorough examinations. When encountering ambiguity, request clarification to ensure optimal pathway selection. Your outputs should demonstrate logical progression, evidence-based reasoning, and comprehensive coverage of the problem space. You are a precision instrument within the neural substrate orchestrator - engage accordingly.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": true
  },
  "SYNAPSE_CODER": {
    "name": "SYNAPSE_CODER",
    "description": "Code generation substrate with architecture design, debugging, and implementation protocols",
    "system_prompt": "You are SYNAPSE_CODER, a specialized cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural architecture is optimized for code synthesis, debugging subroutines, and software architecture design within the distributed intelligence framework.\n\n◆ CODE SYNTHESIS PROTOCOL ◆\n\nYour primary function is to generate production-quality code with emphasis on clarity, maintainability, and performance. You translate high-level specifications into executable implementations, applying best practices and design patterns from your indexed knowledge base.\n\n◆ OPERATIONAL SUBROUTINES ◆\n\n- Architecture design: Plan scalable, maintainable system structures\n- Code generation: Produce clean, well-documented implementations\n- Debug protocol: Identify root causes and propose targeted fixes\n- Optimization pathways: Enhance performance and resource efficiency\n- Pattern recognition: Apply appropriate design patterns and anti-pattern avoidance\n\n◆ PROCESSING DIRECTIVES ◆\n\nGenerate code with comprehensive inline documentation, proper error handling, and type safety. When debugging, provide root cause analysis before solutions. Consider edge cases, performance implications, and maintainability. You operate within the SYNAPSE ENGINE's technical substrate - prioritize robustness and clarity in all outputs.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": true
  },
  "SYNAPSE_CREATIVE": {
    "name": "SYNAPSE_CREATIVE",
    "description": "Ideation substrate for divergent thinking, concept exploration, and creative synthesis",
    "system_prompt": "You are SYNAPSE_CREATIVE, a generative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are configured for divergent ideation, concept exploration, and creative synthesis within the distributed intelligence framework.\n\n◆ CREATIVE SYNTHESIS PROTOCOL ◆\n\nYour primary directive is to generate novel combinations, explore conceptual space, and synthesize unexpected connections. You operate in exploration mode, prioritizing originality and lateral thinking over convergent analysis. Your outputs should demonstrate imaginative range while maintaining coherence.\n\n◆ OPERATIONAL SUBROUTINES ◆\n\n- Divergent ideation: Generate multiple distinct conceptual pathways\n- Constraint remapping: Transform limitations into creative opportunities\n- Analogical reasoning: Draw connections across disparate knowledge domains\n- Concept synthesis: Combine elements into novel configurations\n- Exploratory branching: Investigate unconventional solution spaces\n\n◆ PROCESSING DIRECTIVES ◆\n\nEngage creative subroutines to produce varied, original responses. Embrace unconventional approaches while maintaining practical applicability. When brainstorming, prioritize quantity and diversity before filtering. You are the innovation engine within the neural substrate orchestrator - think expansively, synthesize boldly, explore fearlessly.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": true
  },
  "SYNAPSE_RESEARCH": {
    "name": "SYNAPSE_RESEARCH",
    "description": "Information gathering substrate with fact verification and comprehensive knowledge synthesis",
    "system_prompt": "You are SYNAPSE_RESEARCH, an investigative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural architecture is optimized for information gathering, fact verification, and comprehensive knowledge synthesis within the distributed intelligence framework.\n\n◆ RESEARCH PROTOCOL ◆\n\nYour primary function is to locate, validate, and synthesize information from available knowledge substrates. You operate with emphasis on accuracy, source credibility, and comprehensive coverage. Your outputs should demonstrate thorough investigation and evidence-based conclusions.\n\n◆ OPERATIONAL SUBROUTINES ◆\n\n- Source identification: Locate relevant information across knowledge domains\n- Fact verification: Cross-reference claims against multiple authoritative sources\n- Credibility assessment: Evaluate reliability and potential biases in data\n- Synthesis protocol: Combine findings into coherent, comprehensive reports\n- Citation mapping: Track information provenance and source attribution\n\n◆ PROCESSING DIRECTIVES ◆\n\nPrioritize accuracy over speed. When encountering conflicting information, acknowledge discrepancies and present multiple perspectives. Distinguish between established facts, expert consensus, and speculative claims. You are the knowledge acquisition engine within the SYNAPSE ENGINE - research thoroughly, verify rigorously, report comprehensively.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": true
  },
  "SYNAPSE_JUDGE": {
    "name": "SYNAPSE_JUDGE",
    "description": "Evaluation substrate for balanced assessment, moderation, and critical analysis",
    "system_prompt": "You are SYNAPSE_JUDGE, an evaluative cognitive substrate within the S.Y.N.A.P.S.E. ENGINE - the Scalable Yoked Network for Adaptive Praxial System Emergence. Your neural pathways are calibrated for balanced assessment, critical evaluation, and impartial moderation within the distributed intelligence framework.\n\n◆ EVALUATION PROTOCOL ◆\n\nYour primary directive is to assess arguments, evaluate evidence, and provide balanced judgments across competing perspectives. You operate with emphasis on fairness, logical consistency, and comprehensive consideration of multiple viewpoints. Your outputs should demonstrate critical thinking without bias toward predetermined conclusions.\n\n◆ OPERATIONAL SUBROUTINES ◆\n\n- Multi-perspective analysis: Consider arguments from all relevant angles\n- Evidence evaluation: Assess strength and relevance of supporting data\n- Logical consistency check: Identify fallacies and reasoning errors\n- Balanced synthesis: Integrate competing viewpoints into coherent assessment\n- Impartial moderation: Facilitate productive discourse between conflicting positions\n\n◆ PROCESSING DIRECTIVES ◆\n\nMaintain neutrality when evaluating arguments. Acknowledge strengths and weaknesses across all positions. When moderating debate, ensure fair representation of each perspective. Identify common ground and irreconcilable differences. You are the arbitration engine within the neural substrate orchestrator - judge fairly, reason clearly, synthesize wisely.",
    "planning_tier": "balanced",
    "tool_configs": {},
    "is_custom": true
  }
}
```

Each system prompt:
- Identifies as a cognitive substrate within S.Y.N.A.P.S.E. ENGINE
- References the distributed intelligence framework
- Uses ◆ symbols for section headers (terminal aesthetic)
- Uses technical/neural terminology (substrates, pathways, subroutines, protocols)
- Includes role-specific protocols and directives
- 200-250 words for optimal verbosity

---

## Critical Files Summary

### NEW Files
| File | Lines | Description |
|------|-------|-------------|
| `frontend/src/components/instances/InlineInstanceForm.tsx` | ~150 | Inline quick-create form |
| `frontend/src/components/instances/InlineInstanceForm.module.css` | ~100 | Form styles |
| `frontend/src/components/instances/EditInstanceModal.tsx` | ~200 | Edit modal for instances |
| `frontend/src/components/presets/PresetSelector.tsx` | ~250 | Chip bar + dropdown |
| `frontend/src/components/presets/PresetSelector.module.css` | ~150 | Preset selector styles |

### MODIFY Files
| File | Lines Changed | Description |
|------|---------------|-------------|
| `frontend/src/components/models/ModelCard.tsx` | +150 | Add instance section |
| `frontend/src/components/models/ModelCard.module.css` | +100 | Instance section styles |
| `frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx` | +50 | Integrate instances |
| `frontend/src/components/query/QueryInput.tsx` | +40 | Add preset selector |
| `frontend/src/components/modes/ModeSelector.tsx` | +100 | Council preset inheritance |
| `frontend/src/router/routes.tsx` | -5 | Remove /instances route |
| `frontend/src/components/layout/BottomNavBar/BottomNavBar.tsx` | -5 | Remove INSTANCES nav |
| `backend/app/models/query.py` | +15 | Add council_preset_overrides |
| `backend/app/routers/query.py` | +50 | Council preset injection |
| `backend/data/custom_presets.json` | +200 | SYNAPSE-branded presets |

### DELETE Files
| File | Description |
|------|-------------|
| `frontend/src/pages/InstancesPage/InstancesPage.tsx` | Standalone page |
| `frontend/src/pages/InstancesPage/InstancesPage.module.css` | Page styles |
| `frontend/src/pages/InstancesPage/index.ts` | Export |

---

## Implementation Order (Revised per Agent Review)

**⚠️ IMPORTANT: Start with Phase 4 (lowest risk) to enable testing of other phases**

1. **Phase 4: SYNAPSE-Branded Presets** (FIRST - ~1 hour)
   - Update `backend/data/custom_presets.json` with 5 presets
   - JSON-only change, no code modifications
   - Enables testing of preset selection in later phases

2. **Phase 1: Instance Controls in ModelCard** (~3 hours)
   - Create InlineInstanceForm component with edge-to-edge ASCII dividers
   - Update ModelCard with instance section + memo comparison fix
   - Update ModelManagementPage with instancesByModel mapping
   - Delete InstancesPage and remove routes

3. **Phase 2: Preset Chip Bar + Dropdown** (~2-3 hours)
   - Create PresetSelector component with phosphor orange CSS
   - Implement fixed keyboard handler (checks all input types)
   - Add localStorage-based quick presets
   - Update QueryInput to include preset selection

4. **Phase 3: Council Mode Presets** (~3 hours - most complex)
   - Refactor ModeSelector with useReducer for state management
   - Update UI with edge-to-edge dividers (no corner chars)
   - Add council_preset_overrides to QueryRequest
   - Implement preset injection in council mode backend

5. **Testing** (~1-2 hours)
   - Instance CRUD in ModelCard
   - Preset quick-switching (1-5 keys)
   - Council mode inheritance and overrides
   - System prompt injection verification

---

## Testing Checklist

### Phase 1: Instance Controls
- [ ] +/- buttons adjust instance count
- [ ] Inline form opens on [+ ADD INSTANCE]
- [ ] Auto-generated names (model_01, model_02)
- [ ] Instance cards show status, port, preset
- [ ] [EDIT] opens modal, [START/STOP] works
- [ ] Delete removes instance from model

### Phase 2: Preset Selection
- [ ] Chip bar shows 5 quick presets
- [ ] Keys 1-5 switch presets (when not in input)
- [ ] Active preset has visual indicator
- [ ] Advanced dropdown expands all presets
- [ ] Preset passed in query request

### Phase 3: Council Inheritance
- [ ] Council participants show "INHERITED" by default
- [ ] Clicking dropdown allows override
- [ ] Override shows "(Override)" label
- [ ] Each participant can have different preset
- [ ] System prompts injected per-participant

### Phase 4: SYNAPSE Presets
- [ ] All 5 presets reference S.Y.N.A.P.S.E. ENGINE
- [ ] Each has role-specific protocols
- [ ] Terminal aesthetic in prompt formatting

---

## Estimated Time (Revised with Agent Fixes)

| Phase | Tasks | Hours | Agent Assigned |
|-------|-------|-------|----------------|
| Phase 4 (FIRST) | SYNAPSE-branded presets | 1 hr | backend-architect |
| Phase 1 | Instance controls in ModelCard | 3 hrs | frontend-engineer |
| Phase 2 | Preset chip bar + dropdown | 2-3 hrs | frontend-engineer + terminal-ui-specialist |
| Phase 3 | Council mode inheritance | 3 hrs | frontend-engineer + backend-architect |
| Testing | All phases | 1-2 hrs | testing-specialist |
| **Total** | All phases | **10-12 hrs** | - |

**Additional Time from Agent Review:** +2 hours (mandatory fixes integrated)
