# MAGI Next-Generation Features

**Date:** 2025-11-04
**Status:** In Progress - Phase 1 & 2 Complete
**Version:** 1.2
**Current Project Completion:** ~40% (Council Mode + Web Search Complete)

---

## 🚀 Implementation Progress

### ✅ Phase 1 Complete: SearXNG Web Search Integration

**Completed:** 2025-11-04
**Estimated Time:** 4-6 hours
**Actual Time:** ~4 hours

**Overview:**
Successfully integrated SearXNG metasearch engine to provide privacy-respecting web search capabilities. System now combines real-time web results with local CGRAG documentation for comprehensive query responses.

**Files Created/Modified:**

1. **docker-compose.yml** (Lines 94-150, 155-186)
   - Added SearXNG service container on port 8888
   - Configured backend environment variables for web search
   - Added service dependencies and health checks

2. **backend/app/services/websearch.py** (New File - 282 lines)
   - Implemented `WebSearchResult` and `WebSearchResponse` Pydantic models
   - Created `SearXNGClient` with async HTTP requests (httpx)
   - Singleton pattern with `get_searxng_client()`
   - Full error handling, timeout management, and graceful degradation

3. **backend/app/models/query.py** (Lines 65-68, 83-96, 287-335)
   - Extended `QueryRequest` with `use_web_search` field
   - Added `council_adversarial` and `benchmark_serial` for future phases
   - Changed mode Literal to include 'benchmark', remove 'debate'
   - Extended `QueryMetadata` with web search results and metadata

4. **backend/app/routers/query.py** (Lines 36, 137-181, 281-325, etc.)
   - Integrated web search execution before CGRAG in both modes
   - Combined web + CGRAG results in prompts (web first, docs second)
   - Added web search metadata to `QueryResponse`
   - Graceful degradation if web search fails

5. **frontend/src/types/query.ts** (Lines 5-16, 32-39, 63-77)
   - Updated `QueryMode` type to remove 'debate'/'chat', add 'benchmark'
   - Created `WebSearchResult` interface
   - Extended `QueryRequest` and `QueryMetadata` with web search fields

6. **frontend/src/components/query/QueryInput.tsx** (Lines 12-17, 32, 88-99)
   - Added `useWebSearch` state and checkbox to UI
   - Updated `QueryOptions` interface
   - Integrated into submit callback

7. **frontend/src/pages/HomePage/HomePage.tsx** (Lines 30-53)
   - Updated `handleQuerySubmit` to pass `useWebSearch` to API

**Key Architectural Decisions:**

1. **Context Integration Pattern**: Web search executes before CGRAG, results combined in prompt
   - Web results appear first (current/recent information)
   - CGRAG appears second (technical documentation)
   - Clear separators and labeled sections for model clarity

2. **Error Handling Strategy**: Graceful degradation
   - Web search failures log warnings but continue with CGRAG only
   - System remains functional without web search service

3. **Performance Characteristics**:
   - Web search timeout: 10s (configurable via env)
   - Max results: 5 (configurable via env)
   - Async/await throughout for non-blocking I/O

4. **Docker Service Dependencies**:
   - Backend depends on both Redis and SearXNG health checks
   - Prevents backend from starting before required services ready

**Testing Status:**
- ⏳ **Pending**: Display web search results in ResponseDisplay component
- ⏳ **Pending**: End-to-end Docker testing with real queries

**Next Steps for Engineer:**
1. Build UI component to display web search results in ResponseDisplay
2. Test complete workflow: frontend toggle → backend → SearXNG → response
3. Verify graceful degradation when SearXNG unavailable
4. Move to Phase 2: Mode System Redesign

---

### ✅ Phase 1 Complete: Council Mode (Consensus & Adversarial)

**Completed:** 2025-11-04
**Estimated Time:** 14-20 hours
**Actual Time:** ~28 hours (includes Mode UX redesign + backend + frontend + testing)

**Overview:**
Successfully implemented multi-model council orchestration with two operational modes: **Consensus Mode** (3+ models collaborate through deliberation rounds) and **Adversarial/Debate Mode** (2 models argue opposing viewpoints). Both modes integrate CGRAG and web search, with full frontend visualizations showing per-model responses and deliberation rounds.

**Key Features Implemented:**

1. **Council Consensus Mode** - 3+ models collaborate to reach agreement
   - Round 1: Each model generates independent response to query
   - Round 2: Each model reviews others' responses and refines their answer
   - Synthesis: Most powerful model combines refined responses into consensus
   - Flexible tier selection: Falls back to any 3 enabled models if preferred tiers unavailable

2. **Council Adversarial/Debate Mode** - 2 models argue opposing viewpoints
   - Round 1: Model A argues "pro", Model B argues "con"
   - Round 2: Model A counters B's argument, Model B counters A's argument
   - Synthesis: Most powerful model summarizes debate with key points from both sides
   - Works with any 2 enabled models

3. **Frontend Visualizations**
   - Collapsible deliberation round panels showing each model's contribution
   - Per-model response displays with model names and token counts
   - Processing time metrics for each round
   - Council metadata showing participants, mode type, and total processing time

4. **Mode Selector UX**
   - Removed separate "Debate" mode button
   - Added adversarial toggle checkbox to Council mode configuration panel
   - Dynamic description text explaining current mode (consensus vs adversarial)
   - Terminal-aesthetic styling consistent with MAGI design system

**Files Created/Modified:**

1. **backend/app/routers/query.py** (Lines 48-67, 103-750)
   - Added `_call_model_direct()` helper for direct model calls via LlamaCppClient
   - Implemented `_process_consensus_mode()` function (Lines 103-402)
   - Implemented `_process_debate_mode()` function (Lines 405-750)
   - Fixed Docker networking: `127.0.0.1` → `host.docker.internal` for macOS
   - Flexible model selection with fallback logic
   - Full integration with CGRAG and web search context

2. **backend/app/main.py** (Lines 117-124)
   - Exposed `model_registry` to query router for council mode access
   - Wired up module-level variable for model discovery integration

3. **backend/app/models/query.py** (Lines 84-108, 287-335)
   - Added `council_adversarial` field to QueryRequest
   - Added `council_profile` and `council_participants` for future profile support
   - Extended QueryMetadata with council-specific fields
   - Added `benchmark_serial` field for future VRAM management

4. **frontend/src/components/modes/ModeSelector.tsx** (Lines 18-24, 78-115)
   - Added adversarial toggle state management
   - Created council configuration panel with checkbox
   - Dynamic mode descriptions (consensus vs adversarial)
   - Integrated mode config into parent callback

5. **frontend/src/components/modes/ModeSelector.module.css** (Lines 140-195)
   - Added `.councilConfig` panel styling
   - Added `.adversarialCheckbox` and `.configDescription` styles
   - Terminal-aesthetic consistent with MAGI design system

6. **frontend/src/pages/HomePage/HomePage.tsx** (Lines 22, 42-43, 57-62)
   - Added `modeConfig` state for tracking adversarial/serial settings
   - Updated `handleQuerySubmit` to pass council configuration to API
   - Added `handleModeChange` to capture mode config from selector

7. **frontend/src/components/response/ResponseDisplay.tsx** (Lines 127-288)
   - Created `CouncilResponsePanel` component for collapsible rounds
   - Per-model response rendering with token counts
   - Synthesis display with special formatting
   - Round timing metadata display

**Key Architectural Decisions:**

1. **Model Registry Integration**: Used `model_registry` instead of legacy `ModelManager`
   - Direct model calls via LlamaCppClient for cleaner architecture
   - Access to discovered models with metadata (tier, quantization, enabled status)

2. **Docker Networking Fix**: `host.docker.internal` for container-to-host communication
   - Resolves macOS Docker Desktop networking constraints
   - Backend container can now reach llama-server instances on host

3. **Flexible Model Selection**: Automatic fallback when preferred tiers unavailable
   - Consensus mode: Try fast/balanced/powerful → fallback to any 3 enabled models
   - Adversarial mode: Try balanced + powerful → fallback to any 2 enabled models
   - Graceful degradation prevents mode failures due to model availability

4. **Two-Round Deliberation**: Balance between depth and latency
   - Round 1: Independent responses provide diverse initial perspectives
   - Round 2: Cross-review and refinement incorporates peer feedback
   - Synthesis: Final consolidation by most capable model

5. **Mode UX Consolidation**: Single "Council" mode with adversarial toggle
   - Reduces UI clutter (removed separate "Debate" button)
   - Clear visual indication of current mode behavior
   - Configuration panel appears contextually when Council mode active

**Testing Status:**
- ✅ **Complete**: End-to-end council consensus mode testing (3 models)
- ✅ **Complete**: Docker networking verified (host.docker.internal works)
- ✅ **Complete**: Model registry integration tested successfully
- ✅ **Complete**: Frontend visualization rendering correctly
- ⏳ **Pending**: Adversarial/debate mode end-to-end testing (not yet tested with live models)
- ⏳ **Pending**: Profile-based model selection (feature implemented but not tested)

**Performance Metrics (Consensus Mode Test):**
- Total processing time: ~74 seconds (3 models × 2 rounds + synthesis)
- Tokens generated: 1104 total
- Models tested: DeepSeek-R1-8B (Q4_K_M), Qwen3-4B (Q4_K_M), Qwen3-VL-4B (Q4_K_M)
- CGRAG + Web Search: Both successfully integrated

**Known Issues & Workarounds:**
- **Issue**: Legacy ModelManager has 0 models registered
  - **Root Cause**: ModelManager initialized with empty `config.models` dict
  - **Workaround**: Council mode uses `model_registry` directly instead
  - **Long-term fix**: Deprecate ModelManager in favor of unified model_registry

- **Issue**: Enum .value AttributeError in llama_server_manager.py
  - **Root Cause**: Pydantic enums are already strings, don't need `.value`
  - **Fix**: Removed `.value` accessors from all Pydantic enum usage

**Next Steps for Engineer:**
1. Test adversarial/debate mode end-to-end with live models
2. Implement profile-based model selection (e.g., "fast-consensus", "reasoning-debate")
3. Add user-specified participant selection UI
4. Move to Phase 2: Benchmark/Comparison Mode
5. Consider deprecating legacy ModelManager entirely

---

## Executive Summary

This document provides a comprehensive implementation plan for MAGI's next-generation features, focusing on advanced multi-model orchestration capabilities that leverage the existing infrastructure while addressing practical limitations of local LLMs.

### Features Approved for Implementation

✅ **SearXNG Web Search Integration** - Privacy-respecting web search with CGRAG (COMPLETED 2025-11-04, 4h actual)
✅ **Mode System Redesign** - Consolidate Council/Debate into unified interface (COMPLETED 2025-11-04, included in Phase 1)
✅ **Council Mode (Consensus)** - Multiple models discuss to reach agreement (COMPLETED 2025-11-04, 28h actual for both modes)
✅ **Debate Mode (Adversarial)** - Two models argue opposing viewpoints (COMPLETED 2025-11-04, included in Council Mode)
⏳ **Benchmark/Comparison Mode** - Side-by-side model evaluation (20-24h estimated)
⏳ **Code Chat Mode** - Q&A for codebases using CGRAG (8-12h estimated)
❌ **Full Coding Assistant** - Backburnered due to context window limitations

### Implementation Timeline

- ✅ **Phase 0** (Completed 2025-11-04): SearXNG Web Search Integration → 4 hours actual (est. 4-6h)
- ✅ **Phase 1** (Completed 2025-11-04): Mode UX + Council Mode (Consensus & Adversarial) → 28 hours actual (est. 14-20h)
- ⏳ **Phase 2** (In Progress): Benchmark/Comparison Mode → 20-24 hours estimated
- ⏳ **Phase 3** (Future): Code Chat + Multi-Chat → 20-28 hours estimated

**Total Estimated Effort:** 74-96 hours (~2-3 months part-time)
**Completed:** 32 hours (~40% of estimated 74-96h range)

---

## Table of Contents

1. [Mode System Redesign](#mode-system-redesign)
2. [Council Mode Implementation](#council-mode-implementation)
3. [Debate Mode Implementation](#debate-mode-implementation)
4. [Benchmark/Comparison Mode](#benchmarkcomparison-mode)
5. [Code Chat Mode](#code-chat-mode)
6. [Coding Assistant Analysis (Backburner)](#coding-assistant-analysis)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Technical Specifications](#technical-specifications)
9. [Testing & Validation](#testing--validation)

---

## Mode System Redesign

### Current State Problems

- **5 mode buttons** - Cluttered interface (Two-Stage, Simple, Council, Debate, Multi-Chat)
- **Debate and Council are similar** - Both involve multiple models, just different orchestration
- **3 modes show "COMING SOON"** - Looks incomplete

### Proposed Solution: Unified Council Mode with Adversarial Toggle

**UI Mockup:**

```
┌─────────────────────────────────────────────────────────────┐
│ ▓▓▓ QUERY MODE SELECTION ▓▓▓                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │TWO-STAGE  │ │  SIMPLE   │ │  COUNCIL  │ │ BENCHMARK │  │
│  │  ● ACTIVE │ │           │ │           │ │           │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ▓ COUNCIL MODE CONFIGURATION                        │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  ☐ Enable Adversarial Debate                        │   │
│  │                                                      │   │
│  │  Default: Consensus-seeking discussion              │   │
│  │  - Multiple models collaborate to agreement         │   │
│  │  - Sequential refinement rounds                     │   │
│  │  - Synthesized final answer                         │   │
│  │                                                      │   │
│  │  Checked: Opposing viewpoints debate                │   │
│  │  - Two models argue pro vs. con                     │   │
│  │  - Alternating counterarguments                     │   │
│  │  - User judges or system synthesizes                │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Steps

#### Step 1: Update ModeSelector Component (1-2 hours)

**File:** `frontend/src/components/modes/ModeSelector.tsx`

**Changes:**
1. Remove `'debate'` from MODES array
2. Add `'benchmark'` to MODES array
3. Add state for adversarial toggle: `const [isAdversarial, setIsAdversarial] = useState(false)`
4. Add config panel that appears when Council mode is active

**Code Snippet:**

```typescript
const MODES: ModeConfig[] = [
  {
    id: 'two-stage',
    label: 'TWO-STAGE',
    description: 'Fast model + CGRAG → Powerful refinement',
    available: true
  },
  {
    id: 'simple',
    label: 'SIMPLE',
    description: 'Single model query',
    available: true
  },
  {
    id: 'council',
    label: 'COUNCIL',
    description: 'Multiple models collaborate or debate',
    available: true  // Changed from false
  },
  {
    id: 'benchmark',
    label: 'BENCHMARK',
    description: 'Compare all models side-by-side',
    available: false  // Coming soon
  }
];

export const ModeSelector: React.FC<ModeSelectorProps> = ({
  currentMode,
  onModeChange
}) => {
  const [isAdversarial, setIsAdversarial] = useState(false);

  const handleModeChange = (mode: QueryMode) => {
    onModeChange(mode, isAdversarial);
  };

  return (
    <Panel title="QUERY MODE SELECTION" variant="accent">
      <div className={styles.modeGrid}>
        {MODES.map(mode => (
          <button key={mode.id} /* ... existing button code ... */>
            {/* ... */}
          </button>
        ))}
      </div>

      {/* NEW: Council configuration panel */}
      {currentMode === 'council' && (
        <div className={styles.councilConfig}>
          <div className={styles.configHeader}>
            ▓ COUNCIL MODE CONFIGURATION
          </div>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={isAdversarial}
              onChange={(e) => setIsAdversarial(e.target.checked)}
              className={styles.adversarialCheckbox}
            />
            Enable Adversarial Debate
          </label>
          <div className={styles.configDescription}>
            {isAdversarial ? (
              <>
                <strong>Adversarial Mode:</strong> Two models argue opposing viewpoints
                with alternating counterarguments.
              </>
            ) : (
              <>
                <strong>Consensus Mode:</strong> Multiple models collaborate through
                sequential refinement to reach agreement.
              </>
            )}
          </div>
        </div>
      )}
    </Panel>
  );
};
```

#### Step 2: Add CSS Styling (30 min)

**File:** `frontend/src/components/modes/ModeSelector.module.css`

**Add:**

```css
.councilConfig {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--color-bg-secondary);
  border: 2px solid var(--color-accent);
  border-radius: 4px;
}

.configHeader {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-accent);
  letter-spacing: 0.05em;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.checkboxLabel {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text);
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.checkboxLabel:hover {
  background: var(--color-bg-hover);
}

.adversarialCheckbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-accent);
}

.configDescription {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  padding: 0.75rem;
  background: var(--color-bg);
  border-left: 3px solid var(--color-accent);
}

.configDescription strong {
  color: var(--color-primary);
  display: block;
  margin-bottom: 0.25rem;
}
```

#### Step 3: Update Query Request Type (15 min)

**File:** `backend/app/models/query.py`

**Update QueryRequest model:**

```python
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query text")

    mode: Literal["simple", "two-stage", "council", "benchmark"] = Field(
        default="two-stage",
        description="Query processing mode"
    )

    # NEW: Council mode configuration
    council_adversarial: bool = Field(
        default=False,
        description="Use adversarial debate in council mode (vs consensus)"
    )

    use_context: bool = Field(default=True, description="Enable CGRAG context retrieval")
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
```

**Update QueryMetadata:**

```python
class QueryMetadata(BaseModel):
    # ... existing fields ...

    # Council mode metadata
    council_mode: Optional[Literal["consensus", "adversarial"]] = None
    council_participants: Optional[List[str]] = None  # Model IDs
    council_rounds: Optional[int] = None
    council_responses: Optional[List[Dict[str, Any]]] = None  # Per-model responses
```

---

## Council Mode Implementation

### Consensus Algorithm Design

**Flow:**

```
User Query
    ↓
CGRAG Retrieval (if enabled)
    ↓
Round 1: Initial Responses
├─ Model A (FAST tier)     → Response A1
├─ Model B (BALANCED tier) → Response B1
└─ Model C (POWERFUL tier) → Response C1
    ↓
Round 2: Cross-Review & Refinement
├─ Model A reviews B1 & C1 → Refined A2
├─ Model B reviews A1 & C1 → Refined B2
└─ Model C reviews A1 & B1 → Refined C2
    ↓
Synthesis: Meta-Model or Voting
    ↓
Final Consensus Answer
```

**Key Design Decisions:**
- **3 models** - Optimal for consensus (avoids ties)
- **2 rounds** - Balance depth vs latency
- **Tier diversity** - FAST + BALANCED + POWERFUL for varied perspectives
- **Synthesis method** - Use most powerful model to combine refined responses

### Backend Implementation (8-10 hours)

#### Step 1: Add Council Routing to query.py

**File:** `backend/app/routers/query.py`

**Add after two-stage implementation (around line 1035):**

```python
elif query_mode == "council":
    # ========================================================================
    # COUNCIL MODE: CONSENSUS OR ADVERSARIAL
    # ========================================================================
    is_adversarial = request.council_adversarial
    logger.info(f"🏛️ Council mode: {'Adversarial' if is_adversarial else 'Consensus'}")

    if is_adversarial:
        # Debate mode: 2 models, opposing arguments
        response = await _process_debate_mode(
            request=request,
            model_manager=model_manager,
            cgrag_context=cgrag_context,
            complexity_score=complexity_score
        )
    else:
        # Consensus mode: 3+ models, collaborative refinement
        response = await _process_consensus_mode(
            request=request,
            model_manager=model_manager,
            cgrag_context=cgrag_context,
            complexity_score=complexity_score
        )

    return response
```

#### Step 2: Implement Consensus Mode Function

**Add new function in query.py:**

```python
async def _process_consensus_mode(
    request: QueryRequest,
    model_manager: ModelManager,
    cgrag_context: str,
    complexity_score: float
) -> QueryResponse:
    """Process query using collaborative consensus approach.

    Workflow:
    1. Round 1: 3 models generate independent responses
    2. Round 2: Each model reviews others' responses and refines
    3. Synthesis: Most powerful model combines refined responses

    Args:
        request: Query request with parameters
        model_manager: Model manager instance
        cgrag_context: Retrieved context from CGRAG
        complexity_score: Query complexity score

    Returns:
        QueryResponse with consensus answer and metadata
    """
    council_start = time.time()

    # Select 3 models from different tiers for diverse perspectives
    try:
        fast_model = await model_manager.select_model("fast")
        balanced_model = await model_manager.select_model("balanced")
        powerful_model = await model_manager.select_model("powerful")
    except Exception as e:
        logger.error(f"Failed to select council models: {e}")
        raise HTTPException(
            status_code=503,
            detail="Council mode requires at least 3 enabled models across tiers"
        )

    participants = [fast_model, balanced_model, powerful_model]
    logger.info(f"Council participants: {participants}")

    # Build initial prompt with context
    initial_prompt = cgrag_context + "\\n\\n" + request.query if cgrag_context else request.query

    # ========================================================================
    # ROUND 1: Independent responses from all models
    # ========================================================================
    logger.info("🗣️ Council Round 1: Initial independent responses")
    round1_start = time.time()

    round1_responses = {}
    round1_tasks = []

    for model_id in participants:
        task = model_manager.call_model(
            model_id=model_id,
            prompt=initial_prompt,
            max_tokens=500,  # Limit Round 1 responses
            temperature=request.temperature
        )
        round1_tasks.append((model_id, task))

    # Execute all Round 1 calls in parallel
    for model_id, task in round1_tasks:
        try:
            response = await task
            round1_responses[model_id] = response
            logger.info(f"  ✅ {model_id}: {len(response)} chars")
        except Exception as e:
            logger.error(f"  ❌ {model_id} failed: {e}")
            # Continue with remaining models

    round1_time = int((time.time() - round1_start) * 1000)
    logger.info(f"Round 1 complete: {len(round1_responses)}/{len(participants)} models ({round1_time}ms)")

    if len(round1_responses) < 2:
        raise HTTPException(
            status_code=500,
            detail="Consensus failed: Insufficient Round 1 responses"
        )

    # ========================================================================
    # ROUND 2: Cross-review and refinement
    # ========================================================================
    logger.info("🔄 Council Round 2: Cross-review and refinement")
    round2_start = time.time()

    round2_responses = {}
    round2_tasks = []

    for model_id in round1_responses.keys():
        # Build cross-review prompt
        other_responses = "\\n\\n".join([
            f"Model {other_id}'s response:\\n{response}"
            for other_id, response in round1_responses.items()
            if other_id != model_id
        ])

        refinement_prompt = f\"\"\"You are participating in a collaborative discussion to answer the following query:

Query: {request.query}

Your initial response:
{round1_responses[model_id]}

Other participants' responses:
{other_responses}

Review the other responses and refine your answer. You may:
- Incorporate good points from others
- Correct any errors you notice
- Add missing details
- Maintain your unique perspective while building consensus

Provide your refined response:\"\"\"

        task = model_manager.call_model(
            model_id=model_id,
            prompt=refinement_prompt,
            max_tokens=700,  # Allow longer Round 2 responses
            temperature=request.temperature
        )
        round2_tasks.append((model_id, task))

    # Execute Round 2 calls in parallel
    for model_id, task in round2_tasks:
        try:
            response = await task
            round2_responses[model_id] = response
            logger.info(f"  ✅ {model_id} refined: {len(response)} chars")
        except Exception as e:
            logger.error(f"  ❌ {model_id} refinement failed: {e}")
            # Fallback to Round 1 response
            round2_responses[model_id] = round1_responses[model_id]

    round2_time = int((time.time() - round2_start) * 1000)
    logger.info(f"Round 2 complete: {len(round2_responses)} refinements ({round2_time}ms)")

    # ========================================================================
    # SYNTHESIS: Combine refined responses into consensus
    # ========================================================================
    logger.info("🎯 Synthesizing consensus answer")
    synthesis_start = time.time()

    # Use most powerful model for synthesis
    synthesizer_model = powerful_model

    all_refined = "\\n\\n".join([
        f"Model {model_id}'s refined response:\\n{response}"
        for model_id, response in round2_responses.items()
    ])

    synthesis_prompt = f\"\"\"You are synthesizing multiple expert responses into a single consensus answer.

Original Query:
{request.query}

Expert Responses (after collaborative refinement):
{all_refined}

Your task:
1. Identify common themes and agreements across responses
2. Incorporate unique insights from each expert
3. Resolve any contradictions by favoring the most supported viewpoints
4. Provide a comprehensive, well-reasoned consensus answer
5. Maintain accuracy and completeness

Consensus Answer:\"\"\"

    try:
        consensus_answer = await model_manager.call_model(
            model_id=synthesizer_model,
            prompt=synthesis_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature * 0.8  # Slightly lower temp for synthesis
        )
        synthesis_time = int((time.time() - synthesis_start) * 1000)
        logger.info(f"✅ Consensus synthesized: {len(consensus_answer)} chars ({synthesis_time}ms)")
    except Exception as e:
        logger.error(f"Synthesis failed: {e}, falling back to best Round 2 response")
        # Fallback: Use longest/most detailed Round 2 response
        consensus_answer = max(round2_responses.values(), key=len)
        synthesis_time = 0

    total_time = round1_time + round2_time + synthesis_time

    # Build council metadata
    council_metadata = {
        "participants": participants,
        "rounds": 2,
        "responses": [
            {
                "model_id": model_id,
                "round1": round1_responses.get(model_id, ""),
                "round2": round2_responses.get(model_id, ""),
                "tokens": len(round2_responses.get(model_id, "").split())
            }
            for model_id in participants
        ]
    }

    return QueryResponse(
        response=consensus_answer,
        metadata=QueryMetadata(
            model_tier="council",
            model_id=synthesizer_model,  # Synthesis model
            processing_time_ms=total_time,
            complexity_score=complexity_score,
            cgrag_artifacts=len(cgrag_artifacts) if cgrag_context else 0,
            cgrag_artifacts_info=cgrag_artifacts if cgrag_context else [],
            query_mode="council",
            council_mode="consensus",
            council_participants=participants,
            council_rounds=2,
            council_responses=council_metadata["responses"]
        )
    )
```

### Frontend Display (4-6 hours)

#### Update ResponseDisplay Component

**File:** `frontend/src/components/query/ResponseDisplay.tsx`

**Add council mode visualization after two-stage section:**

```typescript
{metadata.queryMode === 'council' && metadata.councilResponses && (
  <Panel title="COUNCIL DELIBERATION" variant="accent">
    <div className={styles.councilInfo}>
      {/* Header */}
      <div className={styles.councilHeader}>
        <span className={styles.councilLabel}>
          MODE: {metadata.councilMode?.toUpperCase() || 'CONSENSUS'}
        </span>
        <span className={styles.councilParticipants}>
          PARTICIPANTS: {metadata.councilParticipants?.length || 0}
        </span>
        <span className={styles.councilRounds}>
          ROUNDS: {metadata.councilRounds || 2}
        </span>
      </div>

      {/* Participant responses */}
      <div className={styles.participantGrid}>
        {metadata.councilResponses.map((participant, idx) => (
          <div key={participant.model_id} className={styles.participant}>
            <div className={styles.participantHeader}>
              <span className={styles.participantLabel}>
                MODEL {String.fromCharCode(65 + idx)}
              </span>
              <span className={styles.participantModel}>
                {participant.model_id}
              </span>
            </div>

            {/* Round 1 */}
            <details className={styles.round}>
              <summary className={styles.roundSummary}>
                Round 1: Initial Response ({participant.round1?.split(' ').length || 0} words)
              </summary>
              <pre className={styles.roundResponse}>
                {participant.round1}
              </pre>
            </details>

            {/* Round 2 */}
            <details className={styles.round}>
              <summary className={styles.roundSummary}>
                Round 2: Refined Response ({participant.round2?.split(' ').length || 0} words)
              </summary>
              <pre className={styles.roundResponse}>
                {participant.round2}
              </pre>
            </details>
          </div>
        ))}
      </div>

      {/* Consensus note */}
      <div className={styles.consensusNote}>
        ✓ Final consensus answer shown above (synthesized from all refined responses)
      </div>
    </div>
  </Panel>
)}
```

**Add corresponding CSS:**

```css
.councilInfo {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
}

.councilHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--color-bg-secondary);
  border-left: 4px solid var(--color-accent);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.councilLabel {
  color: var(--color-accent);
}

.councilParticipants,
.councilRounds {
  color: var(--color-text-secondary);
}

.participantGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.participant {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 1rem;
}

.participantHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.participantLabel {
  font-weight: 700;
  color: var(--color-primary);
  font-size: 0.875rem;
}

.participantModel {
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  font-family: var(--font-mono);
}

.round {
  margin-top: 0.75rem;
}

.roundSummary {
  cursor: pointer;
  padding: 0.5rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 0.75rem;
  color: var(--color-primary);
  transition: background 0.2s;
}

.roundSummary:hover {
  background: var(--color-bg-hover);
}

.roundResponse {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

.consensusNote {
  text-align: center;
  padding: 0.75rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-accent);
  border-radius: 4px;
  font-size: 0.875rem;
  color: var(--color-accent);
  font-weight: 600;
}
```

---

## Debate Mode Implementation

### Adversarial Debate Algorithm

**Flow:**

```
User Query
    ↓
CGRAG Retrieval (if enabled)
    ↓
Position Assignment
├─ Model A: Argue PRO
└─ Model B: Argue CON
    ↓
Round 1: Opening Arguments
├─ Model A → Pro Argument A1
└─ Model B → Con Argument B1
    ↓
Round 2: Rebuttals
├─ Model A reviews B1 → Counter-argument A2
└─ Model B reviews A1 → Counter-argument B2
    ↓
Round 3 (Optional): Final Statements
├─ Model A → Closing A3
└─ Model B → Closing B3
    ↓
Synthesis or User Judgment
```

### Backend Implementation (6-8 hours)

**Add to query.py:**

```python
async def _process_debate_mode(
    request: QueryRequest,
    model_manager: ModelManager,
    cgrag_context: str,
    complexity_score: float
) -> QueryResponse:
    """Process query using adversarial debate approach.

    Workflow:
    1. Round 1: Two models present opposing arguments
    2. Round 2: Each model rebuts the other's argument
    3. Synthesis: Neutral model summarizes both positions

    Args:
        request: Query request with parameters
        model_manager: Model manager instance
        cgrag_context: Retrieved context from CGRAG
        complexity_score: Query complexity score

    Returns:
        QueryResponse with debate summary and metadata
    """
    debate_start = time.time()

    # Select 2 models from different tiers
    try:
        model_a = await model_manager.select_model("balanced")
        model_b = await model_manager.select_model("powerful")
    except Exception as e:
        logger.error(f"Failed to select debate models: {e}")
        raise HTTPException(
            status_code=503,
            detail="Debate mode requires at least 2 enabled models"
        )

    logger.info(f"⚔️ Debate: {model_a} (PRO) vs {model_b} (CON)")

    # Build context-enhanced query
    base_query = cgrag_context + "\\n\\n" + request.query if cgrag_context else request.query

    # ========================================================================
    # ROUND 1: Opening arguments
    # ========================================================================
    logger.info("🗣️ Round 1: Opening arguments")
    round1_start = time.time()

    pro_prompt = f\"\"\"You are debating the following topic. Your role is to argue FOR/PRO the position.

Topic: {request.query}

Context: {cgrag_context if cgrag_context else "No additional context"}

Provide a strong, well-reasoned argument in favor of the topic. Use evidence, logic, and persuasive language.

Your PRO argument:\"\"\"

    con_prompt = f\"\"\"You are debating the following topic. Your role is to argue AGAINST/CON the position.

Topic: {request.query}

Context: {cgrag_context if cgrag_context else "No additional context"}

Provide a strong, well-reasoned argument against the topic. Use evidence, logic, and persuasive language.

Your CON argument:\"\"\"

    # Execute Round 1 in parallel
    try:
        pro_arg_1, con_arg_1 = await asyncio.gather(
            model_manager.call_model(model_a, pro_prompt, max_tokens=500, temperature=request.temperature),
            model_manager.call_model(model_b, con_prompt, max_tokens=500, temperature=request.temperature)
        )
        round1_time = int((time.time() - round1_start) * 1000)
        logger.info(f"✅ Round 1 complete ({round1_time}ms)")
    except Exception as e:
        logger.error(f"Round 1 failed: {e}")
        raise HTTPException(status_code=500, detail=f"Debate Round 1 failed: {str(e)}")

    # ========================================================================
    # ROUND 2: Rebuttals
    # ========================================================================
    logger.info("🔄 Round 2: Rebuttals")
    round2_start = time.time()

    pro_rebuttal_prompt = f\"\"\"Opponent's CON argument:
{con_arg_1}

Your original PRO argument:
{pro_arg_1}

Rebut your opponent's argument. Point out flaws, provide counter-evidence, strengthen your position.

Your rebuttal:\"\"\"

    con_rebuttal_prompt = f\"\"\"Opponent's PRO argument:
{pro_arg_1}

Your original CON argument:
{con_arg_1}

Rebut your opponent's argument. Point out flaws, provide counter-evidence, strengthen your position.

Your rebuttal:\"\"\"

    try:
        pro_arg_2, con_arg_2 = await asyncio.gather(
            model_manager.call_model(model_a, pro_rebuttal_prompt, max_tokens=500, temperature=request.temperature),
            model_manager.call_model(model_b, con_rebuttal_prompt, max_tokens=500, temperature=request.temperature)
        )
        round2_time = int((time.time() - round2_start) * 1000)
        logger.info(f"✅ Round 2 complete ({round2_time}ms)")
    except Exception as e:
        logger.error(f"Round 2 failed: {e}")
        # Fallback: Use Round 1 arguments
        pro_arg_2 = pro_arg_1
        con_arg_2 = con_arg_1
        round2_time = 0

    # ========================================================================
    # SYNTHESIS: Neutral summary of both positions
    # ========================================================================
    logger.info("⚖️ Synthesizing debate summary")
    synthesis_start = time.time()

    synthesis_prompt = f\"\"\"You are a neutral moderator summarizing a debate on the following topic:

Topic: {request.query}

PRO Position (Model A):
Opening: {pro_arg_1}
Rebuttal: {pro_arg_2}

CON Position (Model B):
Opening: {con_arg_1}
Rebuttal: {con_arg_2}

Provide a balanced summary that:
1. Presents the strongest points from each side
2. Identifies areas of agreement (if any)
3. Highlights the key points of disagreement
4. Helps the reader understand both perspectives fairly

Neutral Summary:\"\"\"

    try:
        # Use a third model for synthesis if available, else use model_b
        synthesis_model = await model_manager.select_model("fast")
        summary = await model_manager.call_model(
            synthesis_model,
            synthesis_prompt,
            max_tokens=request.max_tokens,
            temperature=0.5  # Lower temp for neutrality
        )
        synthesis_time = int((time.time() - synthesis_start) * 1000)
    except Exception as e:
        logger.warning(f"Synthesis failed: {e}, using Model B for summary")
        summary = f\"\"\"PRO Argument Summary:
{pro_arg_2}

CON Argument Summary:
{con_arg_2}

Both positions presented above. Please evaluate based on evidence and reasoning.\"\"\"
        synthesis_time = 0

    total_time = round1_time + round2_time + synthesis_time

    debate_metadata = {
        "pro_model": model_a,
        "con_model": model_b,
        "rounds": 2,
        "arguments": {
            "pro": {
                "round1": pro_arg_1,
                "round2": pro_arg_2
            },
            "con": {
                "round1": con_arg_1,
                "round2": con_arg_2
            }
        }
    }

    return QueryResponse(
        response=summary,
        metadata=QueryMetadata(
            model_tier="council",
            model_id=f"{model_a} vs {model_b}",
            processing_time_ms=total_time,
            complexity_score=complexity_score,
            cgrag_artifacts=len(cgrag_artifacts) if cgrag_context else 0,
            cgrag_artifacts_info=cgrag_artifacts if cgrag_context else [],
            query_mode="council",
            council_mode="adversarial",
            council_participants=[model_a, model_b],
            council_rounds=2,
            council_responses=[
                {
                    "model_id": model_a,
                    "position": "PRO",
                    "round1": pro_arg_1,
                    "round2": pro_arg_2,
                    "tokens": len(pro_arg_2.split())
                },
                {
                    "model_id": model_b,
                    "position": "CON",
                    "round1": con_arg_1,
                    "round2": con_arg_2,
                    "tokens": len(con_arg_2.split())
                }
            ]
        )
    )
```

### Frontend Display (4-6 hours)

**Add to ResponseDisplay.tsx (inside council mode section):**

```typescript
{metadata.councilMode === 'adversarial' && (
  <div className={styles.debateView}>
    <div className={styles.debateHeader}>
      <span className={styles.debateTitle}>⚔️ ADVERSARIAL DEBATE</span>
      <span className={styles.debateRounds}>
        {metadata.councilRounds || 2} ROUNDS
      </span>
    </div>

    <div className={styles.debateGrid}>
      {/* PRO Side */}
      <div className={styles.debateSide}>
        <div className={styles.sideHeader} style={{borderColor: 'var(--color-success)'}}>
          <span className={styles.sideLabel}>PRO POSITION</span>
          <span className={styles.sideModel}>
            {metadata.councilResponses?.[0]?.model_id}
          </span>
        </div>

        <details className={styles.debateRound} open>
          <summary className={styles.debateRoundSummary}>
            Round 1: Opening Argument
          </summary>
          <pre className={styles.debateArgument}>
            {metadata.councilResponses?.[0]?.round1}
          </pre>
        </details>

        <details className={styles.debateRound}>
          <summary className={styles.debateRoundSummary}>
            Round 2: Rebuttal
          </summary>
          <pre className={styles.debateArgument}>
            {metadata.councilResponses?.[0]?.round2}
          </pre>
        </details>
      </div>

      {/* CON Side */}
      <div className={styles.debateSide}>
        <div className={styles.sideHeader} style={{borderColor: 'var(--color-error)'}}>
          <span className={styles.sideLabel}>CON POSITION</span>
          <span className={styles.sideModel}>
            {metadata.councilResponses?.[1]?.model_id}
          </span>
        </div>

        <details className={styles.debateRound} open>
          <summary className={styles.debateRoundSummary}>
            Round 1: Opening Argument
          </summary>
          <pre className={styles.debateArgument}>
            {metadata.councilResponses?.[1]?.round1}
          </pre>
        </details>

        <details className={styles.debateRound}>
          <summary className={styles.debateRoundSummary}>
            Round 2: Rebuttal
          </summary>
          <pre className={styles.debateArgument}>
            {metadata.councilResponses?.[1]?.round2}
          </pre>
        </details>
      </div>
    </div>

    <div className={styles.debateSummary}>
      ⚖️ Neutral summary of debate shown above
    </div>
  </div>
)}
```

**CSS:**

```css
.debateView {
  padding: 1rem;
  background: var(--color-bg);
}

.debateHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--color-bg-secondary);
  border-left: 4px solid var(--color-warning);
  margin-bottom: 1.5rem;
}

.debateTitle {
  font-weight: 700;
  font-size: 0.875rem;
  color: var(--color-warning);
  letter-spacing: 0.05em;
}

.debateRounds {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.debateGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.debateSide {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 1rem;
}

.sideHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  margin-bottom: 1rem;
  border-bottom: 2px solid;
}

.sideLabel {
  font-weight: 700;
  font-size: 0.875rem;
  letter-spacing: 0.05em;
}

.sideModel {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
}

.debateRound {
  margin-bottom: 1rem;
}

.debateRoundSummary {
  cursor: pointer;
  padding: 0.5rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  transition: background 0.2s;
}

.debateRoundSummary:hover {
  background: var(--color-bg-hover);
}

.debateArgument {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.debateSummary {
  text-align: center;
  padding: 0.75rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-warning);
  border-radius: 4px;
  font-size: 0.875rem;
  color: var(--color-warning);
  font-weight: 600;
}
```

---

## Benchmark/Comparison Mode

### Overview

Benchmark mode provides side-by-side comparison of all enabled models on the same query. This is valuable for:
- Evaluating model quality across different quantizations
- Identifying which models excel at specific task types
- Testing prompt variations across models
- Verifying consistency and detecting hallucinations

### Key Features

1. **Flexible Execution** - Parallel (fastest) or Serial (VRAM-safe) execution modes
2. **Side-by-Side Display** - Grid layout showing all responses simultaneously
3. **Quantitative Metrics** - Response time, tokens, quality scores
4. **Hallucination Heuristics** - Hedging language, self-contradiction detection
5. **Comparative Analysis** - Semantic similarity matrix, winner identification

### Serial vs Parallel Execution Toggle

**Problem:** Running 3-5 models simultaneously can exceed available VRAM, especially with larger quantizations (Q4/Q8).

**Solution:** User-selectable execution mode via checkbox (similar to Council adversarial toggle).

**UI Mockup:**

```
┌─────────────────────────────────────────────────────────────┐
│ ▓▓▓ QUERY MODE SELECTION ▓▓▓                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │TWO-STAGE  │ │  SIMPLE   │ │  COUNCIL  │ │●BENCHMARK │  │
│  │           │ │           │ │           │ │   ACTIVE  │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ▓ BENCHMARK MODE CONFIGURATION                      │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  ☐ Use Serial Execution (VRAM-Constrained)          │   │
│  │                                                      │   │
│  │  Default: Parallel execution (fastest)              │   │
│  │  - All models run simultaneously                    │   │
│  │  - Total time ≈ slowest model                       │   │
│  │  - Requires sufficient VRAM for all models          │   │
│  │                                                      │   │
│  │  Checked: Sequential execution (VRAM-safe)          │   │
│  │  - Models run one at a time                         │   │
│  │  - Total time = sum of all models                   │   │
│  │  - Only one model loaded in VRAM at once            │   │
│  │  - Safe for systems with limited memory             │   │
│  │                                                      │   │
│  │  💡 Use serial if you have <8GB VRAM or see OOM     │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### Frontend Implementation

**File:** `frontend/src/components/modes/ModeSelector.tsx`

**Add state and config panel:**

```typescript
export const ModeSelector: React.FC<ModeSelectorProps> = ({
  currentMode,
  onModeChange
}) => {
  const [isAdversarial, setIsAdversarial] = useState(false);
  const [benchmarkSerial, setBenchmarkSerial] = useState(false); // NEW

  const handleModeChange = (mode: QueryMode) => {
    const config = {
      adversarial: isAdversarial,
      serial: benchmarkSerial
    };
    onModeChange(mode, config);
  };

  return (
    <Panel title="QUERY MODE SELECTION" variant="accent">
      {/* ... existing mode buttons ... */}

      {/* NEW: Benchmark configuration panel */}
      {currentMode === 'benchmark' && (
        <div className={styles.benchmarkConfig}>
          <div className={styles.configHeader}>
            ▓ BENCHMARK MODE CONFIGURATION
          </div>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={benchmarkSerial}
              onChange={(e) => setBenchmarkSerial(e.target.checked)}
              className={styles.serialCheckbox}
            />
            Use Serial Execution (VRAM-Constrained)
          </label>
          <div className={styles.configDescription}>
            {benchmarkSerial ? (
              <>
                <strong>Serial Mode:</strong> Models execute one at a time to conserve VRAM.
                Total time will be longer but memory-safe.
              </>
            ) : (
              <>
                <strong>Parallel Mode:</strong> All models execute simultaneously for fastest
                results. Requires sufficient VRAM for all models.
              </>
            )}
          </div>
          <div className={styles.vramHint}>
            💡 Use serial mode if you have &lt;8GB VRAM or experience OOM errors
          </div>
        </div>
      )}
    </Panel>
  );
};
```

**CSS additions use existing styles** (councilConfig, configHeader, checkboxLabel, configDescription)

#### Backend Implementation

**File:** `backend/app/models/query.py`

**Update QueryRequest:**

```python
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query text")

    mode: Literal["simple", "two-stage", "council", "benchmark"] = Field(
        default="two-stage",
        description="Query processing mode"
    )

    # Council mode configuration
    council_adversarial: bool = Field(
        default=False,
        description="Use adversarial debate in council mode (vs consensus)"
    )

    # NEW: Benchmark mode configuration
    benchmark_serial: bool = Field(
        default=False,
        description="Execute models sequentially (vs parallel) to conserve VRAM"
    )

    use_context: bool = Field(default=True, description="Enable CGRAG context retrieval")
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
```

**File:** `backend/app/routers/query.py`

**Add benchmark mode handler:**

```python
elif query_mode == "benchmark":
    # ========================================================================
    # BENCHMARK MODE: PARALLEL OR SERIAL COMPARISON
    # ========================================================================
    is_serial = request.benchmark_serial
    logger.info(f"📊 Benchmark mode: {'Serial' if is_serial else 'Parallel'} execution")

    # Get all enabled models
    enabled_models = [m for m in model_registry.models.values() if m.enabled]

    if len(enabled_models) < 2:
        raise HTTPException(
            status_code=400,
            detail="Benchmark mode requires at least 2 enabled models"
        )

    benchmark_results = []
    total_start = time.time()

    if is_serial:
        # ====================================================================
        # SERIAL EXECUTION: One model at a time (VRAM-safe)
        # ====================================================================
        logger.info(f"Running {len(enabled_models)} models sequentially...")

        for idx, model_config in enumerate(enabled_models, 1):
            model_start = time.time()
            logger.info(f"  [{idx}/{len(enabled_models)}] Starting {model_config.model_id}...")

            try:
                response_text = await model_manager.call_model(
                    model_id=model_config.model_id,
                    prompt=initial_prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
                model_time = int((time.time() - model_start) * 1000)

                benchmark_results.append({
                    "model_id": model_config.model_id,
                    "model_tier": model_config.tier,
                    "response": response_text,
                    "response_time_ms": model_time,
                    "token_count": len(response_text.split()),
                    "char_count": len(response_text),
                    "success": True
                })
                logger.info(f"  ✅ {model_config.model_id}: {model_time}ms, {len(response_text)} chars")
            except Exception as e:
                logger.error(f"  ❌ {model_config.model_id} failed: {e}")
                benchmark_results.append({
                    "model_id": model_config.model_id,
                    "model_tier": model_config.tier,
                    "error": str(e),
                    "success": False
                })
    else:
        # ====================================================================
        # PARALLEL EXECUTION: All models simultaneously (fastest)
        # ====================================================================
        logger.info(f"Running {len(enabled_models)} models in parallel...")

        tasks = []
        for model_config in enabled_models:
            task_start = time.time()
            task = model_manager.call_model(
                model_id=model_config.model_id,
                prompt=initial_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            tasks.append((model_config, task, task_start))

        # Await all tasks in parallel
        results = await asyncio.gather(
            *[task for _, task, _ in tasks],
            return_exceptions=True
        )

        # Process results
        for (model_config, _, start_time), result in zip(tasks, results):
            model_time = int((time.time() - start_time) * 1000)

            if isinstance(result, Exception):
                logger.error(f"  ❌ {model_config.model_id} failed: {result}")
                benchmark_results.append({
                    "model_id": model_config.model_id,
                    "model_tier": model_config.tier,
                    "error": str(result),
                    "success": False
                })
            else:
                benchmark_results.append({
                    "model_id": model_config.model_id,
                    "model_tier": model_config.tier,
                    "response": result,
                    "response_time_ms": model_time,
                    "token_count": len(result.split()),
                    "char_count": len(result),
                    "success": True
                })
                logger.info(f"  ✅ {model_config.model_id}: {model_time}ms")

    total_time = int((time.time() - total_start) * 1000)
    successful_count = len([r for r in benchmark_results if r.get('success')])

    # Build comparison summary
    execution_mode = "sequential" if is_serial else "parallel"

    summary = f"""Benchmark Results ({execution_mode} execution):
- {successful_count}/{len(enabled_models)} models completed successfully
- Total time: {total_time}ms
- Fastest: {min([r['response_time_ms'] for r in benchmark_results if r.get('success')], default=0)}ms
- Slowest: {max([r['response_time_ms'] for r in benchmark_results if r.get('success')], default=0)}ms

See detailed comparison below."""

    return QueryResponse(
        response=summary,
        metadata=QueryMetadata(
            model_tier="benchmark",
            model_id=f"{len(enabled_models)} models ({execution_mode})",
            processing_time_ms=total_time,
            query_mode="benchmark",
            benchmark_results=benchmark_results,
            benchmark_execution_mode=execution_mode,
            cgrag_artifacts=len(cgrag_artifacts) if cgrag_context else 0
        )
    )
```

#### VRAM Estimation Guide

To help users choose between parallel and serial:

| Model Configuration | Parallel VRAM | Serial VRAM | Recommendation |
|---------------------|---------------|-------------|----------------|
| 3x Q2_K (8B) | ~4.5 GB | ~1.5 GB | Parallel (most GPUs) |
| 3x Q4_K_M (8B) | ~7.5 GB | ~2.5 GB | Parallel (8GB+ GPU) |
| 2x Q4 + 1x Q8 (8B) | ~9 GB | ~3 GB | Serial (<12GB VRAM) |
| 5x Q4_K_M (8B) | ~12.5 GB | ~2.5 GB | Serial (most systems) |
| 3x Q8 (14B) | ~18 GB | ~6 GB | Serial (consumer GPUs) |

**Formula:** VRAM per model ≈ model_size_GB × 1.2 (overhead)

### Computable Metrics

```python
class BenchmarkMetrics(BaseModel):
    """Metrics computed for each model in benchmark mode."""

    model_id: str
    model_tier: str
    response_time_ms: int
    token_count: int
    char_count: int

    # Quality metrics (computed post-processing)
    confidence_score: Optional[float] = None  # 0.0 to 1.0
    hedging_score: Optional[float] = None  # Count of uncertainty markers
    semantic_similarity: Optional[float] = None  # vs other responses

    # Status
    success: bool
    error: Optional[str] = None
```

### Implementation Effort

- **Frontend:** 2 hours (checkbox + config panel, reuse Council styles)
- **Backend:** 3-4 hours (serial execution logic, error handling)
- **Testing:** 1 hour (test with 2-5 models, both modes)
- **Total:** 6-7 hours

---

## Code Chat Mode

### Design Philosophy

**SCOPE:** Code Q&A + File Creation + File Editing (with preview/confirmation)

**Why This Approach:**
- Preview + confirmation workflow makes editing as safe as creation
- Drag-and-drop UX makes file selection intuitive
- Local models can generate good scaffolding and edits (70-80% quality)
- User ALWAYS reviews before applying → safety net
- Context window sufficient for single-file operations
- Provides real value: components, tests, configs, refactoring

**Key Difference from Full Coding Assistant:**
- ✅ Single-file operations with review
- ❌ NO auto-accept edits (always manual confirmation)
- ❌ NO multi-file refactoring (context limitations)

### Features

✅ **Code-specific Q&A**
- "How do I implement feature X?"
- "Explain this code pattern"
- "Where is function Y defined?"

✅ **CGRAG Integration**
- Index entire codebase (supports .py, .js, .ts, .md, etc.)
- Retrieve relevant code snippets with <100ms latency
- Show file paths and line numbers

✅ **Syntax Highlighting**
- Detect language from file extension
- Terminal-aesthetic code blocks
- Copy-to-clipboard buttons

✅ **File Creation** (NEW)
- Generate new components, modules, tests
- Create configuration files, schemas, interfaces
- Scaffold boilerplate with project patterns
- **User confirmation required before writing**
- Preview full file content before creation
- Prevent overwriting existing files

✅ **File Editing** (NEW)
- Drag-and-drop file to load for editing
- Request specific changes ("Add error handling to X")
- Preview diff before applying
- **User confirmation required**
- Revert option if edit breaks something

✅ **Example Generation**
- Provide copy-paste examples
- Explain design patterns
- Link to documentation

❌ **NOT Included:**
- Auto-accept edits without review (accuracy concerns)
- Multi-file refactoring (context window limitations)
- IDE integration (out of scope for WebUI)
- Background auto-fixes (too risky)

### File Operations Safety Model

**Critical Safeguards (applies to BOTH creation and editing):**

1. **Explicit Confirmation Required**
   - Never auto-create or auto-edit files
   - Show full preview/diff before applying
   - Clear action button: "Create File" or "Apply Edit"
   - NOT auto-executed

2. **File Existence Handling**
   - Creation: Error if file already exists
   - Editing: Load current content, show diff of changes
   - Drag-and-drop: Load file content into editor

3. **Path Validation**
   - Suggest file path based on project structure
   - Allow user to modify path before creation
   - Validate path is within project directory (prevent `../../../etc/passwd`)

4. **Content Review**
   - **Creation:** Display full file content with syntax highlighting
   - **Editing:** Display side-by-side diff (current vs proposed)
   - Allow user to copy/modify before applying
   - Option to reject and try again

5. **Clear Warnings**
   - "⚠️ Review generated code before applying"
   - "Local models may produce incorrect code - verify before use"
   - "Always test changes before committing"

6. **Backup & Revert**
   - Store original file content before edit
   - Provide "Undo Last Edit" button
   - Show edit history for session

### Implementation (16-22 hours)

#### Step 1: Add Code Chat Mode to Selector (1 hour)

Update MODES array to include:

```typescript
{
  id: 'code-chat',
  label: 'CODE CHAT',
  description: 'Code Q&A + File Create/Edit',
  available: true
}
```

#### Step 2: Create Code-Specific Prompts (2-3 hours)

**File:** `backend/app/services/prompts.py` (new file)

```python
CODE_CHAT_SYSTEM_PROMPT = \"\"\"You are a helpful coding assistant with access to the project codebase.

Guidelines:
- Provide clear, accurate answers about code
- Reference specific files and line numbers when relevant
- Explain patterns and design decisions
- Generate working code examples
- Cite documentation when applicable
- Admit uncertainty rather than guessing

Context:
{cgrag_context}

Code Question:
{user_query}

Answer:\"\"\"

FILE_CREATION_PROMPT = \"\"\"You are generating a new file for a software project.

Project Context:
{cgrag_context}

User Request:
{user_query}

Generate:
1. Suggested file path (relative to project root)
2. Complete file content (production-ready code)
3. Brief explanation of what the file does

Format your response as:
```path
suggested/file/path.ext
```

```code
[complete file content here]
```

```explanation
[brief explanation]
```

Important:
- Follow existing project patterns and conventions
- Include proper imports and dependencies
- Add inline comments for complex logic
- Ensure code is complete and runnable
\"\"\"

FILE_EDITING_PROMPT = \"\"\"You are editing an existing file in a software project.

Current File Content:
```{language}
{current_content}
```

Project Context:
{cgrag_context}

Edit Request:
{user_query}

Generate:
1. Modified file content (complete file, not just changes)
2. Summary of changes made
3. Explanation of why changes were made

Format your response as:
```code
[complete modified file content]
```

```changes
[bullet list of changes made]
```

```explanation
[brief explanation of changes]
```

Important:
- Maintain existing code style and patterns
- Only modify what's necessary for the request
- Preserve comments and docstrings
- Ensure imports are updated if needed
- Test logic remains intact
\"\"\"
```

#### Step 3: Drag-and-Drop File Loader (3-4 hours)

**Component:** `frontend/src/components/code/FileDropZone.tsx`

```typescript
interface FileDropZoneProps {
  onFileLoad: (file: File, content: string) => void;
  disabled?: boolean;
}

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileLoad, disabled }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;

    const file = files[0];

    // Only accept text files
    if (!file.type.startsWith('text/') && !file.name.match(/\.(js|ts|tsx|py|md|json|yaml|yml)$/)) {
      alert('Please drop a code file (.js, .py, .ts, etc.)');
      return;
    }

    try {
      const content = await file.text();
      onFileLoad(file, content);
    } catch (err) {
      console.error('Failed to read file:', err);
      alert('Failed to read file');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <div
      className={`${styles.dropZone} ${isDragging ? styles.dragging : ''} ${disabled ? styles.disabled : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <div className={styles.dropContent}>
        <span className={styles.dropIcon}>📁</span>
        <span className={styles.dropText}>
          {isDragging ? 'Drop file to edit' : 'Drag and drop a file here to edit it'}
        </span>
        <span className={styles.dropHint}>
          Supports: .js, .ts, .tsx, .py, .md, .json, .yaml
        </span>
      </div>
    </div>
  );
};
```

**CSS:** `FileDropZone.module.css`

```css
.dropZone {
  border: 2px dashed var(--color-border);
  border-radius: 8px;
  padding: 3rem 2rem;
  text-align: center;
  transition: all 0.2s;
  cursor: pointer;
  background: var(--color-bg-secondary);
}

.dropZone.dragging {
  border-color: var(--color-primary);
  background: var(--color-bg);
  transform: scale(1.02);
}

.dropZone.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dropContent {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.dropIcon {
  font-size: 3rem;
}

.dropText {
  font-size: 1rem;
  color: var(--color-text);
  font-weight: 600;
}

.dropHint {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}
```

#### Step 4: Add Syntax Highlighting (2 hours)

**Install library:**
```bash
npm install react-syntax-highlighter @types/react-syntax-highlighter
```

**Component:**
```typescript
import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const CodeBlock: React.FC<{code: string; language: string}> = ({code, language}) => (
  <div className={styles.codeBlock}>
    <div className={styles.codeHeader}>
      <span className={styles.codeLang}>{language.toUpperCase()}</span>
      <button
        className={styles.copyButton}
        onClick={() => navigator.clipboard.writeText(code)}
      >
        COPY
      </button>
    </div>
    <SyntaxHighlighter
      language={language}
      style={atomOneDark}
      customStyle={{
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border)',
        borderRadius: '4px',
        padding: '1rem',
        fontSize: '0.875rem',
        fontFamily: 'var(--font-mono)'
      }}
    >
      {code}
    </SyntaxHighlighter>
  </div>
);
```

#### Step 5: File Editing/Creation UI with Diff Preview (6-8 hours)

**Component:** `frontend/src/components/code/FileOperationPanel.tsx`

```typescript
import { diffLines } from 'diff'; // npm install diff @types/diff

interface FileOperationPanelProps {
  mode: 'create' | 'edit';
  filePath: string;
  originalContent?: string;  // For edit mode
  newContent: string;
  language: string;
  explanation: string;
  onPathChange: (path: string) => void;
  onApply: (path: string, content: string) => Promise<void>;
  onCancel: () => void;
}

export const FileOperationPanel: React.FC<FileOperationPanelProps> = ({
  mode,
  filePath,
  originalContent,
  newContent,
  language,
  explanation,
  onPathChange,
  onApply,
  onCancel
}) => {
  const [editedPath, setEditedPath] = useState(filePath);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleApply = async () => {
    setIsApplying(true);
    setError(null);

    try {
      await onApply(editedPath, newContent);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsApplying(false);
    }
  };

  // Generate diff for edit mode
  const diffLines = mode === 'edit' && originalContent
    ? computeDiff(originalContent, newContent)
    : null;

  return (
    <Panel title={`FILE ${mode.toUpperCase()} PREVIEW`} variant="warning">
      <div className={styles.operationPanel}>
        {/* Warning */}
        <div className={styles.warning}>
          ⚠️ Review generated code before {mode === 'create' ? 'creation' : 'applying edits'}.
          Local models may produce incorrect code.
        </div>

        {/* Explanation */}
        <div className={styles.explanation}>
          <strong>{mode === 'create' ? 'What this file does:' : 'Changes made:'}</strong>
          <p>{explanation}</p>
        </div>

        {/* File Path Input */}
        <div className={styles.pathInput}>
          <label>File Path (relative to project root)</label>
          <input
            type="text"
            value={editedPath}
            onChange={(e) => setEditedPath(e.target.value)}
            className={styles.input}
            placeholder="path/to/file.ext"
            disabled={mode === 'edit'}  // Can't change path when editing
          />
        </div>

        {/* Diff View for Edit Mode */}
        {mode === 'edit' && diffLines && (
          <div className={styles.diffView}>
            <div className={styles.diffHeader}>
              <span>CHANGES</span>
              <span className={styles.diffStats}>
                +{diffLines.additions} -{diffLines.deletions}
              </span>
            </div>
            <div className={styles.diffContent}>
              {diffLines.hunks.map((hunk, idx) => (
                <div key={idx} className={styles.diffHunk}>
                  {hunk.lines.map((line, lineIdx) => (
                    <div
                      key={lineIdx}
                      className={`${styles.diffLine} ${
                        line.added ? styles.added :
                        line.removed ? styles.removed :
                        styles.unchanged
                      }`}
                    >
                      <span className={styles.lineNumber}>{line.lineNumber}</span>
                      <span className={styles.lineContent}>{line.content}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Full Content Preview for Create Mode */}
        {mode === 'create' && (
          <div className={styles.codePreview}>
            <div className={styles.previewHeader}>
              <span>FILE CONTENT PREVIEW</span>
              <span className={styles.language}>{language.toUpperCase()}</span>
            </div>
            <CodeBlock code={newContent} language={language} />
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className={styles.error}>
            ❌ {error}
          </div>
        )}

        {/* Actions */}
        <div className={styles.actions}>
          <button
            onClick={handleApply}
            disabled={isApplying || !editedPath}
            className={styles.applyButton}
          >
            {isApplying ? 'APPLYING...' : mode === 'create' ? 'CREATE FILE' : 'APPLY EDIT'}
          </button>
          <button
            onClick={onCancel}
            disabled={isApplying}
            className={styles.cancelButton}
          >
            CANCEL
          </button>
        </div>
      </div>
    </Panel>
  );
};

// Helper to compute diff
function computeDiff(original: string, modified: string) {
  const changes = diffLines(original, modified);

  let additions = 0;
  let deletions = 0;
  const hunks = [];
  let currentHunk = { lines: [] };
  let lineNumber = 1;

  changes.forEach(change => {
    const lines = change.value.split('\n').filter(l => l.length > 0);

    if (change.added) {
      additions += lines.length;
      lines.forEach(line => {
        currentHunk.lines.push({
          added: true,
          removed: false,
          content: line,
          lineNumber: lineNumber++
        });
      });
    } else if (change.removed) {
      deletions += lines.length;
      lines.forEach(line => {
        currentHunk.lines.push({
          added: false,
          removed: true,
          content: line,
          lineNumber: lineNumber++
        });
      });
    } else {
      // Context lines
      lines.forEach(line => {
        currentHunk.lines.push({
          added: false,
          removed: false,
          content: line,
          lineNumber: lineNumber++
        });
      });
    }
  });

  if (currentHunk.lines.length > 0) {
    hunks.push(currentHunk);
  }

  return { additions, deletions, hunks };
}
```

**Diff Styling:**

```css
.diffView {
  margin-top: 1.5rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.diffHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  font-size: 0.875rem;
  font-weight: 600;
}

.diffStats {
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
}

.diffContent {
  max-height: 500px;
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

.diffLine {
  display: flex;
  padding: 0.25rem 1rem;
}

.diffLine.added {
  background: rgba(0, 255, 65, 0.1);
  border-left: 3px solid var(--color-success);
}

.diffLine.removed {
  background: rgba(255, 0, 0, 0.1);
  border-left: 3px solid var(--color-error);
}

.diffLine.unchanged {
  background: var(--color-bg);
}

.lineNumber {
  display: inline-block;
  width: 4rem;
  color: var(--color-text-secondary);
  user-select: none;
  padding-right: 1rem;
  text-align: right;
}

.lineContent {
  flex: 1;
  white-space: pre;
}
```

#### Step 6: Backend Endpoints (3-4 hours)

**File:** `backend/app/routers/code.py` (new file)

```python
from fastapi import APIRouter, HTTPException
from pathlib import Path
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/api/code", tags=["code"])

class FileOperationRequest(BaseModel):
    operation: Literal["create", "edit"]
    file_path: str
    content: str
    original_content: Optional[str] = None  # For edit validation

@router.post("/write-file")
async def write_file(request: FileOperationRequest) -> Dict[str, Any]:
    """Create or edit a file with generated content.

    Args:
        request: File operation request

    Returns:
        Success status and file path

    Raises:
        HTTPException: If file exists (create) or doesn't exist (edit) or path invalid
    """
    # Validate path is within project directory
    abs_path = Path(request.file_path).resolve()
    project_root = Path.cwd().resolve()

    if not str(abs_path).startswith(str(project_root)):
        raise HTTPException(
            status_code=400,
            detail="File path must be within project directory"
        )

    # Operation-specific validation
    if request.operation == "create":
        if abs_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"File already exists: {request.file_path}. Use edit mode to modify it."
            )
        # Create parent directories if needed
        abs_path.parent.mkdir(parents=True, exist_ok=True)

    elif request.operation == "edit":
        if not abs_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_path}. Use create mode for new files."
            )

    # Write file
    try:
        abs_path.write_text(request.content, encoding='utf-8')
        logger.info(f"{request.operation.capitalize()}d file: {request.file_path}")

        return {
            "success": True,
            "operation": request.operation,
            "file_path": request.file_path,
            "message": f"File {request.operation}d successfully"
        }
    except Exception as e:
        logger.error(f"Failed to {request.operation} file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to {request.operation} file: {str(e)}"
        )

@router.get("/read-file")
async def read_file(file_path: str) -> Dict[str, Any]:
    """Read file content for editing.

    Args:
        file_path: Relative path from project root

    Returns:
        File content and metadata
    """
    abs_path = Path(file_path).resolve()
    project_root = Path.cwd().resolve()

    if not str(abs_path).startswith(str(project_root)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = abs_path.read_text(encoding='utf-8')
        return {
            "file_path": file_path,
            "content": content,
            "language": detect_language(abs_path.suffix),
            "size_bytes": abs_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

def detect_language(suffix: str) -> str:
    """Map file extension to language for syntax highlighting."""
    mapping = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.md': 'markdown',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
    }
    return mapping.get(suffix.lower(), 'text')
```

#### Step 7: Testing (3-4 hours)

**Q&A Tests:**
- "Explain the CGRAG retrieval logic in cgrag.py"
- "How does model selection work in routing.py?"
- "Show me how to add a new query mode"

**File Creation Tests:**
- "Create a new React component for displaying model metrics"
- "Generate a test file for the CGRAG retriever"
- "Scaffold a new FastAPI router for user management"
- Verify overwrite protection works
- Test path validation prevents directory traversal

**File Editing Tests:**
- Drag-and-drop existing file
- Request: "Add error handling to the authenticate function"
- Verify diff preview shows additions/deletions correctly
- Apply edit and verify file updated
- Test undo functionality
- Ensure edits preserve existing code structure

---

## Coding Assistant Analysis (Backburner)

### Why NOT Recommended for v1.0

#### Context Window Math

| Requirement | Tokens Needed | Local Model Limit | Gap |
|-------------|---------------|-------------------|-----|
| Single file edit | 500-2000 | 8000-32000 | ✅ Fits |
| Related files (3-5) | 2000-10000 | 8000-32000 | ⚠️ Tight |
| Small codebase analysis | 20000-50000 | 8000-32000 | ❌ Doesn't fit |
| Enterprise monorepo | 500000+ | 8000-32000 | ❌ Impossible |

**Conclusion:** Even with CGRAG, multi-file operations exceed context limits.

#### Model Quality Concerns

| Feature | Required Accuracy | Local Model Reality | Feasible? |
|---------|------------------|---------------------|-----------|
| Code explanation | 60-70% | 70-80% | ✅ Yes |
| Single file edit | 85-90% | 70-80% | ⚠️ Manual review required |
| Multi-file refactor | 95%+ | 70-80% | ❌ Too risky |
| Auto-accept edits | 95%+ | 70-80% | ❌ Will break code |

**Conclusion:** Local models are good for Q&A, not safe for auto-edits.

### Alternative: Code Chat (Recommended)

Provides 70% of value with 20% of complexity:
- Answers "how to" questions
- Explains existing code
- Suggests approaches
- Generates examples to copy-paste
- **No file editing risk**

### When to Revisit

✅ **Conditions for full coding assistant:**
1. Local models reach 128K+ context windows
2. Model quality improves to 90%+ accuracy
3. MAGI core features are mature and stable
4. User demand for coding features is high

**Estimated Timeline:** 12-24 months (2026-2027)

---

## Two-Stage Coding Enhancement

### Overview: Solving Context Window Limitations

**Problem:** Local LLMs have limited context windows (8-32K tokens) making it impossible to provide full codebase context for coding tasks.

**Traditional Approach (Fails):**
```
User: "Add error handling to the auth module"
Model: 🤔 Which auth module? What's the current code? What's the pattern?
        [Needs 50K tokens, only has 8K available]
        Result: Generic, unhelpful answer
```

**Two-Stage Coding Solution (Works):**
```
Stage 1: Context Retrieval (FAST model + CGRAG)
  Input: User request + codebase index
  Output: Relevant code chunks (auth module, error patterns, imports)
  Tokens: 3-4K (fits in 8K window)

Stage 2: Code Generation (Coder-Specialized Model)
  Input: User request + Stage 1 focused context
  Output: Accurate code with correct patterns and imports
  Tokens: 4-5K context → generates quality code
```

**Why This Works:**
1. **Context Window Solved**: CGRAG distills 200K token codebase → 4K relevant chunks
2. **Model Specialization**: Use coding-specific model (with `coder: true` flag) for generation
3. **Accuracy Boost**: Focused context → 80-90% accuracy (vs 40-50% without context)
4. **Pattern Reuse**: Already have two-stage infrastructure, just adapt for coding

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ USER REQUEST: "Add error handling to authenticate function" │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: CONTEXT RETRIEVAL (FAST MODEL + CGRAG)            │
│─────────────────────────────────────────────────────────────│
│ • Analyze request to identify needs                        │
│ • Query CGRAG for relevant code:                           │
│   - auth module (authenticate function)                    │
│   - error handling patterns in project                     │
│   - related imports and dependencies                       │
│ • Extract 4K tokens of focused context                     │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
          [Focused Context]
          • Current authenticate() code
          • Project error handling pattern
          • Required imports (HTTPException, logger)
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: CODE GENERATION (CODER MODEL)                     │
│─────────────────────────────────────────────────────────────│
│ Model Selection: Auto-select model with `coder: true` flag │
│ Examples: DeepSeek Coder, Qwen2.5-Coder, CodeLlama         │
│                                                             │
│ Input:                                                      │
│ • User request                                              │
│ • Focused context from Stage 1                             │
│                                                             │
│ Output:                                                     │
│ • Modified authenticate() with error handling              │
│ • Preserves existing code style                            │
│ • Uses project patterns                                    │
│ • Includes correct imports                                 │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ FILE OPERATION (with preview/confirmation)                 │
│─────────────────────────────────────────────────────────────│
│ • Show diff preview                                         │
│ • User reviews changes                                      │
│ • User confirms → apply edit                                │
└─────────────────────────────────────────────────────────────┘
```

### Model Selection via `coder` Flag

Instead of hardcoding "Qwen 14B" or "DeepSeek Coder", use a flexible flag system in model configs.

**Model Config Schema Update:**

```yaml
# config/profiles/development.yaml

models:
  - model_id: deepseek_r1_14b_q4
    model_path: "/models/deepseek-r1-distill-qwen-14b.Q4_K_M.gguf"
    tier: "powerful"
    enabled: true
    flags:
      thinking: false
      coder: true      # ← MARKED AS CODER MODEL

  - model_id: qwen_coder_7b_q4
    model_path: "/models/qwen2.5-coder-7b-instruct.Q4_K_M.gguf"
    tier: "balanced"
    enabled: true
    flags:
      thinking: false
      coder: true      # ← MARKED AS CODER MODEL

  - model_id: llama_3_8b_q2
    model_path: "/models/llama-3.2-8b-instruct.Q2_K.gguf"
    tier: "fast"
    enabled: true
    flags:
      thinking: false
      coder: false     # ← NOT A CODER MODEL
```

**Auto-Selection Logic:**

```python
async def select_coder_model(model_manager: ModelManager) -> str:
    """Select best available model with coder flag.

    Returns:
        model_id of best coder model

    Raises:
        HTTPException: If no coder models available
    """
    # Get all enabled models with coder flag
    coder_models = [
        m for m in model_manager.models.values()
        if m.enabled and m.flags.get('coder', False)
    ]

    if not coder_models:
        raise HTTPException(
            status_code=503,
            detail="No coder models available. Enable a model with coder flag in config."
        )

    # Prefer higher-tier models for coding tasks
    tier_priority = {'powerful': 3, 'balanced': 2, 'fast': 1}

    best_model = max(
        coder_models,
        key=lambda m: tier_priority.get(m.tier, 0)
    )

    logger.info(f"Selected coder model: {best_model.model_id} (tier: {best_model.tier})")
    return best_model.model_id
```

### Code-Aware CGRAG Enhancements

Standard CGRAG retrieves by semantic similarity. Code-aware CGRAG adds code-specific intelligence:

**Enhancements:**

1. **Import Dependency Tracking**
   - When retrieving `auth.py`, also retrieve imported modules
   - Include `auth_utils.py`, `exceptions.py`, `models/user.py`

2. **File Structure Context**
   - Include relative file paths in chunks
   - Retrieve related files in same directory

3. **Recency Weighting**
   - Weight recently modified files higher (more likely to be relevant)

4. **Pattern Matching**
   - If user asks about "error handling", retrieve examples of error handling in project
   - If user asks about "auth", retrieve auth-related code even if not exact semantic match

**Implementation:**

```python
async def retrieve_code_context(
    query: str,
    cgrag_engine: CGRAGEngine,
    token_budget: int = 6000
) -> str:
    """Retrieve code-aware context for coding tasks.

    Args:
        query: User's coding request
        cgrag_engine: CGRAG retrieval engine
        token_budget: Max tokens for context

    Returns:
        Focused code context string
    """
    # Parse query for code-specific hints
    hints = extract_code_hints(query)
    # hints = {
    #     'file_patterns': ['auth.py', 'auth_*'],
    #     'keywords': ['authenticate', 'error', 'handling'],
    #     'imports': True  # User wants to see imports
    # }

    # Retrieve with code-aware ranking
    chunks = await cgrag_engine.retrieve_code(
        query=query,
        file_patterns=hints.get('file_patterns', []),
        keywords=hints.get('keywords', []),
        include_imports=hints.get('imports', False),
        token_budget=token_budget
    )

    # Format for coder model
    context = format_code_context(chunks)

    return context

def format_code_context(chunks: List[CodeChunk]) -> str:
    """Format retrieved code chunks for coder model."""
    sections = []

    for chunk in chunks:
        section = f"""
File: {chunk.file_path}
Lines: {chunk.start_line}-{chunk.end_line}
\n```{chunk.language}
{chunk.content}
\n```
"""
        sections.append(section)

    return "\n\n".join(sections)
```

### Integration with Code Chat File Operations

Two-stage coding enhancement integrates seamlessly with Code Chat's file creation/editing:

**Workflow:**

1. User requests coding task: "Add logging to the query processing pipeline"
2. Two-stage enhancement:
   - Stage 1: Retrieves query pipeline code + logging patterns
   - Stage 2: Generates code with logging added
3. File operation UI:
   - Shows diff preview (if editing)
   - Or shows full file (if creating)
   - User reviews and confirms
4. File written only after confirmation

**This combines:**
- **Two-stage coding**: Accurate code generation
- **File operations**: Safe preview/confirmation workflow
- **Result**: Best of both worlds

### Implementation (22-30 hours)

#### Step 1: Add `coder` Flag to Model Config (2 hours)

**File:** `backend/app/models/model.py`

```python
class ModelFlags(BaseModel):
    """Feature flags for models."""
    thinking: bool = False  # Supports chain-of-thought reasoning
    coder: bool = False     # Optimized for code generation
    # Future: vision, audio, etc.

class ModelConfig(BaseModel):
    model_id: str
    model_path: str
    tier: Literal["fast", "balanced", "powerful"]
    enabled: bool = True
    flags: ModelFlags = ModelFlags()  # NEW
    # ... existing fields ...
```

**Update profile YAML loading** to parse `flags` section.

#### Step 2: Implement Coder Model Selection (2-3 hours)

Add `select_coder_model()` function to `ModelManager` class.

#### Step 3: Enhance CGRAG for Code Retrieval (8-10 hours)

**File:** `backend/app/services/cgrag.py`

Add new methods:
- `retrieve_code()` - Code-aware retrieval with import tracking
- `extract_code_hints()` - Parse query for file patterns, keywords
- `rank_by_code_relevance()` - Custom ranking for code chunks

**Features:**
- Import dependency graph
- File proximity ranking
- Recency weighting
- Pattern-based retrieval

#### Step 4: Two-Stage Coding Mode Handler (6-8 hours)

**File:** `backend/app/routers/query.py`

```python
async def detect_coding_query(query: str) -> bool:
    """Detect if query is code-related."""
    coding_keywords = [
        'code', 'function', 'implement', 'refactor', 'add',
        'create', 'fix', 'bug', 'error', 'class', 'method',
        'module', 'import', 'test', 'debug'
    ]
    return any(kw in query.lower() for kw in coding_keywords)

# In main query handler:
if query_mode == "two-stage" and await detect_coding_query(request.query):
    # ========================================================================
    # TWO-STAGE CODING MODE
    # ========================================================================
    logger.info("🔧 Two-stage coding mode activated")

    # Stage 1: Context Retrieval with FAST model
    context_prompt = f"""Analyze this coding request and list what code context is needed:

Request: {request.query}

List:
1. Relevant file paths or patterns
2. Function/class names to retrieve
3. Related patterns or examples needed
4. Required imports or dependencies
"""

    fast_model = await model_manager.select_model("fast")
    context_plan = await model_manager.call_model(
        model_id=fast_model,
        prompt=context_prompt,
        max_tokens=500,
        temperature=0.3  # Lower temp for analysis
    )

    # Use context plan to guide CGRAG retrieval
    code_context = await cgrag_engine.retrieve_code(
        query=request.query,
        context_hints=context_plan,
        token_budget=6000
    )

    # Stage 2: Code Generation with Coder Model
    coder_model = await model_manager.select_coder_model()

    coding_prompt = f"""You are a coding assistant. Generate code for this request:

Request: {request.query}

Relevant Code Context:
{code_context}

Provide:
1. Complete, working code
2. Brief explanation of changes
3. File path if creating new file

Important:
- Follow existing project patterns
- Maintain code style
- Include necessary imports
- Add inline comments for complex logic
"""

    generated_code = await model_manager.call_model(
        model_id=coder_model,
        prompt=coding_prompt,
        max_tokens=request.max_tokens,
        temperature=0.4  # Moderate temp for code generation
    )

    # Return with coding metadata
    return QueryResponse(
        response=generated_code,
        metadata=QueryMetadata(
            query_mode="two-stage-coding",
            stage1_model=fast_model,
            stage2_model=coder_model,
            cgrag_artifacts=len(code_context_chunks),
            processing_time_ms=total_time
        )
    )
```

#### Step 5: Frontend Integration (4-6 hours)

**Detect coding queries** in frontend and show appropriate UI:
- Code syntax highlighting
- File operation buttons ("Create File", "Edit File")
- Link to Code Chat mode for iterative refinement

### Comparison: Two-Stage Coding vs Alternatives

| Approach | Context Window | Accuracy | Safety | Implementation |
|----------|---------------|----------|--------|----------------|
| **Single Model (no CGRAG)** | ❌ Insufficient | 40-50% | Low | Easy |
| **Single Model + CGRAG** | ⚠️ Limited | 65-75% | Medium | Medium |
| **Two-Stage + CGRAG** | ✅ Sufficient | **80-90%** | **High** | **Medium** |
| **Two-Stage + Coder + CGRAG** | ✅ Optimal | **85-95%** | **High** | **Medium** |
| **Full Coding Assistant** | ❌ Impossible | N/A | N/A | Hard |

**Conclusion:** Two-Stage Coding with Coder model is the sweet spot for local LLMs.

### Effort Estimate

- **Backend - Model Flags:** 2 hours
- **Backend - Coder Selection:** 2-3 hours
- **Backend - CGRAG Enhancements:** 8-10 hours
- **Backend - Two-Stage Handler:** 6-8 hours
- **Frontend - Integration:** 4-6 hours
- **Testing - End-to-End:** 4-6 hours

**Total:** 26-35 hours

---

## Model Flag Management UI

### Manual Flag Override

While auto-detection works most of the time, users should be able to manually override flags for experimentation.

**UI Design:**

In Model Management table, add a glyph/icon (⚙️) next to each model. Clicking opens a sidebar panel showing available flags.

**Component:** `frontend/src/components/models/ModelFlagEditor.tsx`

```typescript
interface ModelFlagEditorProps {
  modelId: string;
  currentFlags: ModelFlags;
  onSave: (modelId: string, newFlags: ModelFlags) => Promise<void>;
  onClose: () => void;
}

export const ModelFlagEditor: React.FC<ModelFlagEditorProps> = ({
  modelId,
  currentFlags,
  onSave,
  onClose
}) => {
  const [flags, setFlags] = useState(currentFlags);
  const [isSaving, setIsSaving] = useState(false);

  const handleToggle = (flag: keyof ModelFlags) => {
    setFlags(prev => ({ ...prev, [flag]: !prev[flag] }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(modelId, flags);
      onClose();
    } catch (err) {
      alert(`Failed to save: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Panel title={`MODEL FLAGS: ${modelId}`} variant="accent">
      <div className={styles.flagEditor}>
        <div className={styles.flagList}>
          {/* Thinking Flag */}
          <label className={styles.flagItem}>
            <input
              type="checkbox"
              checked={flags.thinking}
              onChange={() => handleToggle('thinking')}
            />
            <div className={styles.flagDetails}>
              <span className={styles.flagName}>🧠 Thinking (Chain-of-Thought)</span>
              <span className={styles.flagDesc}>
                Model supports reasoning chains and step-by-step analysis
              </span>
            </div>
          </label>

          {/* Coder Flag */}
          <label className={styles.flagItem}>
            <input
              type="checkbox"
              checked={flags.coder}
              onChange={() => handleToggle('coder')}
            />
            <div className={styles.flagDetails}>
              <span className={styles.flagName}>💻 Coder (Code Generation)</span>
              <span className={styles.flagDesc}>
                Optimized for code generation and technical tasks
              </span>
            </div>
          </label>
        </div>

        <div className={styles.hint}>
          💡 These flags control automatic model selection for specific tasks
        </div>

        <div className={styles.actions}>
          <button onClick={handleSave} disabled={isSaving} className={styles.saveButton}>
            {isSaving ? 'SAVING...' : 'SAVE FLAGS'}
          </button>
          <button onClick={onClose} disabled={isSaving} className={styles.cancelButton}>
            CANCEL
          </button>
        </div>
      </div>
    </Panel>
  );
};
```

**Integration into Model Table:**

```typescript
// In ModelTable.tsx
<td>
  <button
    className={styles.flagButton}
    onClick={() => setEditingFlags(model.model_id)}
    title="Edit model flags"
  >
    ⚙️
  </button>
</td>

{editingFlags === model.model_id && (
  <ModelFlagEditor
    modelId={model.model_id}
    currentFlags={model.flags}
    onSave={handleFlagSave}
    onClose={() => setEditingFlags(null)}
  />
)}
```

**Backend Endpoint:**

```python
@router.patch("/models/{model_id}/flags")
async def update_model_flags(
    model_id: str,
    flags: ModelFlags
) -> Dict[str, Any]:
    """Update model flags."""
    if model_id not in model_registry.models:
        raise HTTPException(status_code=404, detail="Model not found")

    # Update in-memory
    model_registry.models[model_id].flags = flags

    # Persist to registry file
    registry_path = Path("data/model_registry.json")
    save_registry(model_registry, registry_path)

    logger.info(f"Updated flags for {model_id}: {flags.dict()}")

    return {
        "success": True,
        "model_id": model_id,
        "flags": flags.dict()
    }
```

**Effort:** 4-6 hours (UI + backend + testing)

---

## Code Review Mode

### Overview: Smart Folder Review with CGRAG-Guided File Discovery

**Problem:** Traditional code review tools require manual file selection or blindly review entire folders, wasting context on irrelevant files.

**Solution:** User selects folder + describes intent (via preset checkboxes and/or custom prompt) → CGRAG + fast model discovers relevant files → Review with optional Council mode → Actionable results with fix suggestions.

**Key Innovation:** Let AI figure out which files matter based on user's intent, reducing 47 files to 5 relevant ones.

### Workflow Example

```
Step 1: Select Folder
  [Browse] → /project/backend/app

Step 2: Describe Intent (Flexible Options)

  Option A: Use Preset Checkboxes (quick)
    Review Focus:
    ☑ 🔒 Security
    ☑ ⚡ Performance
    ☐ 🐛 Debugging
    ☐ ✨ Code Quality
    ☐ 📚 Best Practices
    ☐ 📝 Documentation

  Option B: Custom Prompt (specific)
    Custom Intent: "Find race conditions in async worker pool"

  Option C: Both (guided + specific)
    ☑ Security  ☑ Performance
    + Custom: "Focus on SQL injection in API endpoints"

Step 3: CGRAG Discovers Relevant Files
  [████████░░] Analyzing folder structure...

  CGRAG indexed: 47 files
  Combined intent: "Security + Performance + SQL injection in API endpoints"
  Relevant files identified: 5

  ✓ app/routers/auth.py (authentication endpoint handlers)
  ✓ app/routers/users.py (user management API)
  ✓ app/services/database.py (DB query functions)
  ✓ app/middleware/auth_middleware.py (auth validation)
  ✓ app/models/user.py (user model with SQL queries)

  (User can ☑/☐ files before review)

Step 4: Configure Review Execution
  ☐ Enable Council Mode (3 models, more thorough)
  ☑ Run in series (VRAM-safe if council enabled)

  [START REVIEW - Est. 3 min]

Step 5: Live Progress
  REVIEWING: app/routers/auth.py
  [█████████████████░░░░░] 3/5 files (60%)

  Issues found so far: 7
  🔴 Critical: 1  🟡 Warning: 3  🔵 Info: 3

  Estimated time remaining: 1m 12s

Step 6: Aggregated Results
  ┌──────────────────────────────────────────┐
  │ FOLDER REVIEW COMPLETE                   │
  │ Files reviewed: 5 (in 2m 47s)            │
  │ Issues found: 12                         │
  │   🔴 Critical: 2                         │
  │   🟡 Warning: 5                          │
  │   🔵 Info: 5                             │
  │                                          │
  │ Top Issues:                              │
  │ 1. SQL injection - auth.py:45            │
  │    [View Details] [Apply Fix]            │
  │                                          │
  │ 2. Auth bypass - middleware.py:89        │
  │    [View Details] [Apply Fix]            │
  │                                          │
  │ 3. N+1 query - users.py:112              │
  │    [View Details]                        │
  │                                          │
  │ [Show All Issues] [Export Report (MD)]   │
  └──────────────────────────────────────────┘
```

### Context Math: Why This is Manageable

**Without smart file discovery:**
```
Folder: 47 files × 800 tokens/file = 37,600 tokens
❌ Exceeds most 32K context windows
❌ Wastes tokens on irrelevant files
❌ Models get confused by noise
```

**With CGRAG-guided discovery:**
```
Phase 1: File Discovery (one-time cost)
  - Folder scan: ~2K tokens
  - CGRAG query: ~1K tokens
  - Model identifies 5 files: ~500 tokens output
  Subtotal: ~3.5K tokens ✅ Fast!

Phase 2: Review Per File
  - File content: ~800 tokens
  - Review prompt: ~1K tokens
  - Model output: ~1.5K tokens
  Per file: ~3.3K tokens ✅ Fits easily!

Total for 5 files (sequential):
  - Discovery: 3.5K tokens (once)
  - Reviews: 5 × 3.3K = 16.5K tokens
  Grand total: ~20K tokens ✅ Well under 32K!

With Optional Council Mode:
  - Serial: Same 20K (3 models review sequentially)
  - Parallel: 3 × 16.5K = 49.5K for reviews
    (Still manageable with larger models or serial mode)

Conclusion: Totally manageable with smart discovery! ✅
```

### Review Categories (Preset Checkboxes + Custom Prompt)

Users can select from preset categories and/or write custom prompts:

**Preset Options (Checkboxes):**

- **🐛 Debugging**
  - Logic errors, edge cases
  - Null/undefined checks
  - Off-by-one errors
  - Incorrect conditionals

- **🔒 Security**
  - SQL injection, XSS, CSRF
  - Authentication/authorization bypass
  - Input validation failures
  - Hardcoded credentials
  - OWASP Top 10 violations

- **⚡ Performance**
  - O(n²) or worse algorithms
  - N+1 database queries
  - Memory leaks
  - Blocking operations in async code
  - Inefficient data structures

- **✨ Code Quality**
  - Code smells (long functions, god classes)
  - Naming inconsistencies
  - Magic numbers/strings
  - Duplicate code
  - Complex conditionals (high cyclomatic complexity)

- **📚 Best Practices**
  - Style guide violations
  - Anti-patterns
  - Improper error handling
  - Missing logging
  - Lack of defensive programming

- **📝 Documentation**
  - Missing docstrings
  - Unclear variable/function names
  - Insufficient comments
  - Outdated documentation

**Custom Prompt (Freeform):**
- "Find race conditions in the async worker pool"
- "Check for memory leaks in the caching layer"
- "Identify potential bottlenecks during high load"
- "Review compliance with PCI-DSS requirements"

**Combined Approach:**
```
Checkboxes: ☑ Security ☑ Performance
+ Custom: "Focus on SQL injection in user input handling"

→ Final intent sent to models:
  "Review for security and performance issues,
   with special focus on SQL injection in user input handling"
```

### Issue Severity & Auto-Fix

```python
class IssueSeverity(Enum):
    CRITICAL = "critical"  # 🔴 Must fix immediately
    WARNING = "warning"    # 🟡 Should fix soon
    INFO = "info"          # 🔵 Consider fixing

class CodeIssue(BaseModel):
    file_path: str
    line_number: int
    severity: IssueSeverity
    category: str  # "security", "performance", etc.
    title: str
    description: str
    code_snippet: str  # Problematic code
    suggested_fix: Optional[str] = None
    confidence: float  # 0.0-1.0
    auto_fixable: bool  # Can we auto-apply fix?

# Critical patterns trigger red alerts:
CRITICAL_PATTERNS = [
    "sql_injection": "Unsanitized user input in SQL query",
    "auth_bypass": "Authentication can be bypassed",
    "rce": "Remote code execution possible",
    "data_exposure": "Sensitive data exposed",
]
```

### Implementation (29-41 hours)

#### Step 1: Folder Selector + Intent Input UI (3-4 hours)

**Component:** `frontend/src/components/code/CodeReviewPanel.tsx`

```typescript
export const CodeReviewPanel: React.FC = () => {
  const [folderPath, setFolderPath] = useState('');
  const [focusAreas, setFocusAreas] = useState<string[]>([]);
  const [customIntent, setCustomIntent] = useState('');
  const [enableCouncil, setEnableCouncil] = useState(false);
  const [serialCouncil, setSerialCouncil] = useState(true);

  const FOCUS_OPTIONS = [
    { id: 'debugging', label: '🐛 Debugging', description: 'Logic errors, edge cases' },
    { id: 'security', label: '🔒 Security', description: 'Vulnerabilities, auth issues' },
    { id: 'performance', label: '⚡ Performance', description: 'Bottlenecks, inefficiencies' },
    { id: 'quality', label: '✨ Code Quality', description: 'Smells, naming, complexity' },
    { id: 'best_practices', label: '📚 Best Practices', description: 'Patterns, error handling' },
    { id: 'documentation', label: '📝 Documentation', description: 'Comments, docstrings' },
  ];

  const toggleFocus = (id: string) => {
    setFocusAreas(prev =>
      prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]
    );
  };

  return (
    <Panel title="CODE REVIEW" variant="accent">
      {/* Folder selection */}
      <div className={styles.section}>
        <label>Folder to Review:</label>
        <FolderSelector onFolderSelected={setFolderPath} />
      </div>

      {/* Preset focus areas (checkboxes) */}
      <div className={styles.section}>
        <label>Review Focus (select one or more):</label>
        <div className={styles.focusGrid}>
          {FOCUS_OPTIONS.map(option => (
            <label key={option.id} className={styles.focusOption}>
              <input
                type="checkbox"
                checked={focusAreas.includes(option.id)}
                onChange={() => toggleFocus(option.id)}
              />
              <div className={styles.focusLabel}>
                <span className={styles.focusName}>{option.label}</span>
                <span className={styles.focusDesc}>{option.description}</span>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Custom intent (optional) */}
      <div className={styles.section}>
        <label>Custom Intent (optional - adds specificity):</label>
        <textarea
          value={customIntent}
          onChange={(e) => setCustomIntent(e.target.value)}
          placeholder="E.g., 'Focus on SQL injection in API endpoints' or 'Find race conditions in worker pool'"
          className={styles.customIntentInput}
          rows={3}
        />
      </div>

      {/* Council mode options */}
      <div className={styles.section}>
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={enableCouncil}
            onChange={(e) => setEnableCouncil(e.target.checked)}
          />
          Enable Council Mode (3 models, more thorough)
        </label>

        {enableCouncil && (
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={serialCouncil}
              onChange={(e) => setSerialCouncil(e.target.checked)}
            />
            Run in series (VRAM-safe)
          </label>
        )}
      </div>

      {/* Start button */}
      <button
        onClick={handleStartReview}
        disabled={!folderPath || (focusAreas.length === 0 && !customIntent)}
        className={styles.startButton}
      >
        START REVIEW
      </button>
    </Panel>
  );
};
```

#### Step 2: File Discovery with CGRAG (4-6 hours)

**Backend:** `backend/app/services/code_review.py`

```python
async def discover_relevant_files(
    folder_path: str,
    focus_areas: List[str],
    custom_intent: Optional[str],
    cgrag_engine: CGRAGEngine,
    model_manager: ModelManager
) -> List[FileRelevance]:
    """Discover files relevant to review intent using CGRAG + fast model."""

    # Combine focus areas and custom intent
    focus_descriptions = {
        "debugging": "logic errors and bugs",
        "security": "security vulnerabilities",
        "performance": "performance issues and bottlenecks",
        "quality": "code quality and maintainability",
        "best_practices": "violations of best practices",
        "documentation": "documentation and clarity"
    }

    combined_intent_parts = [
        focus_descriptions[area] for area in focus_areas
    ]
    if custom_intent:
        combined_intent_parts.append(custom_intent)

    combined_intent = ", ".join(combined_intent_parts)

    logger.info(f"Discovery intent: {combined_intent}")

    # Scan folder
    code_files = scan_folder_for_code(folder_path)

    # CGRAG retrieval
    cgrag_results = await cgrag_engine.retrieve_code(
        query=f"Files related to: {combined_intent}",
        token_budget=3000
    )

    # Ask fast model to identify most relevant files
    # (Implementation similar to earlier design)
    ...
```

#### Step 3-7: Review, Progress, Results (20-28 hours)

Implementation follows the same pattern as described in the earlier design sections, with council mode support and live progress.

### Reusable LiveProgress Component

**This component benefits the entire app:**

```typescript
// Use cases across MAGI:
<LiveProgress current={3} total={5} label="Code Review" currentItem="auth.py" />
<LiveProgress current={2} total={3} label="Council Round" />
<LiveProgress current={8} total={15} label="Benchmark Mode" />
<LiveProgress current={1247} total={5000} label="CGRAG Indexing" />
<LiveProgress current={4} total={10} label="File Creation Batch" />
```

### Effort Estimate

- **Folder selector + intent UI:** 3-4 hours
- **File discovery (CGRAG + model):** 4-6 hours
- **Review logic with council:** 6-8 hours
- **Live progress component:** 3-4 hours
- **Results display UI:** 6-8 hours
- **Backend API endpoints:** 4-6 hours
- **Testing (E2E):** 4-6 hours

**Total:** 30-42 hours

---

## Implementation Roadmap

### ✅ Phase 1: Foundation (COMPLETED 2025-11-04) - 28 hours actual (est. 18-26h)

**Goal:** Unified mode system + basic Council mode + model flag management

#### Week 1: Mode UX Redesign (COMPLETED - 6-8 hours)
- [x] Update ModeSelector component (remove Debate, add config panel)
- [x] Add adversarial toggle checkbox
- [x] Update QueryRequest/QueryMetadata models
- [x] Add CSS styling for terminal aesthetic
- [x] Test mode selection and state management

#### Week 2: Council Mode (Consensus) (COMPLETED - 8-12 hours)
- [x] Implement `_process_consensus_mode()` function
- [x] Add parallel execution for Round 1 (3 models)
- [x] Add cross-review Round 2 logic
- [x] Implement synthesis algorithm
- [x] Add council response display UI
- [x] Test with 3+ enabled models
- [x] Verify metadata tracking

#### Debate Mode (Adversarial) (COMPLETED - included in Phase 1)
- [x] Implement `_process_debate_mode()` function
- [x] Add PRO/CON position assignment
- [x] Implement 2-round debate protocol
- [x] Add neutral synthesis
- [x] Build collapsible debate UI panel
- [x] Add per-model response tracking
- [x] Integrate with adversarial toggle

#### Model Flag Management UI (4-6 hours) - DEFERRED
- [ ] Add `thinking` and `coder` flags to ModelConfig schema
- [ ] Add flag glyph/icon to model cards
- [ ] Build ModelFlagEditor sidebar component
- [ ] Implement PATCH `/api/models/{id}/flags` endpoint
- [ ] Test auto-detection and manual override workflow
- **Note:** Deferred to focus on core council functionality. Model registry already includes `is_thinking_model` and `is_coder` fields.

**Deliverable:** ✅ Working Council mode (consensus + adversarial) with full frontend visualization

---

### Phase 2: Benchmark Mode + Runtime Settings ✅ COMPLETE - 8.5 hours actual

**Goal:** Side-by-side model comparison with performance metrics + WebUI-configurable runtime settings

#### Phase 2A: Runtime Settings System (COMPLETED - 4 hours)
- [x] Created RuntimeSettings Pydantic model with VRAM estimation
- [x] Built settings persistence service with atomic writes
- [x] Implemented 8 settings API endpoints (GET, PUT, reset, validate, import, export, VRAM estimate, schema)
- [x] Created comprehensive SettingsPage UI with 4 sections
- [x] Added React Query hooks for settings management
- [x] Implemented real-time validation and restart detection
- [x] Built terminal-aesthetic styling for settings UI

#### Phase 2B: Benchmark Mode Implementation (COMPLETED - 4.5 hours)
- [x] Implemented `_process_benchmark_mode()` function (~440 lines)
- [x] Added parallel execution for all enabled models (batched with asyncio.gather)
- [x] Added serial execution option with `benchmark_serial` toggle (VRAM-safe)
- [x] Implemented metric calculation (time, tokens, VRAM estimate, success/error)
- [x] Created per-model response tracking with error handling
- [x] Created side-by-side comparison grid UI component
- [x] Built summary panel with aggregate metrics
- [x] Enabled benchmark mode in ModeSelector
- [x] Added benchmark display panel with terminal aesthetic
- [x] Tested in Docker with settings API working
- [x] Verified VRAM management with serial execution

**Deliverable:** ✅ Complete mode system (Simple, Two-Stage, Council, Benchmark) + comprehensive runtime settings system

**Notes:**
- Scope expanded to include full runtime settings system per user request
- All configuration now adjustable via WebUI (GPU/VRAM, HuggingFace, CGRAG, benchmark defaults)
- Settings persist to `data/runtime_settings.json` with atomic writes
- Restart detection warns when GPU/VRAM changes require server restart
- VRAM estimation helps users configure models within hardware limits
- Deferred: semantic similarity computation, hallucination detection, LiveProgress component (not required for MVP)

---

### Phase 3: Code Chat Enhanced (Week 6-7) - 16-22 hours

**Goal:** Code assistance with file creation and editing

#### Code Chat Mode with File Operations (16-22 hours)
- [ ] Add Code Chat mode to selector
- [ ] Create code-specific prompts (FILE_CREATION, FILE_EDITING)
- [ ] Integrate syntax highlighting in response display
- [ ] **Build FileDropZone component with drag-and-drop (4 hours)**
- [ ] **Build FileOperationPanel with diff preview (6 hours)**
- [ ] **Implement file creation workflow with path suggestion**
- [ ] **Implement file editing workflow with diff comparison**
- [ ] **Add safety validation (path traversal, overwrite confirmation)**
- [ ] Add POST `/api/code/create` and `/api/code/edit` endpoints (4 hours)
- [ ] Index codebase with CGRAG for context retrieval
- [ ] Test file creation, editing, and drag-and-drop workflows

**Deliverable:** Code Chat with file creation, editing, and drag-and-drop support

---

### Phase 4: Two-Stage Coding Enhancement (Week 8-9) - 26-35 hours

**Goal:** Leverage CGRAG + coder models for advanced code generation

#### Two-Stage Coding Pipeline (26-35 hours)
- [ ] **Implement coder model selection logic (4 hours)**
- [ ] **Build code-aware CGRAG retrieval (8 hours)**
  - [ ] Extract code hints (imports, function names, file patterns)
  - [ ] Implement `retrieve_code_context()` function
  - [ ] Add token budget management (6K token limit)
- [ ] **Implement two-stage pipeline (8 hours)**
  - [ ] Stage 1: Fast model + CGRAG → code context
  - [ ] Stage 2: Coder model → final code with context
  - [ ] Add fallback logic if no coder models available
- [ ] **Build TwoStageCodingPanel UI component (6 hours)**
  - [ ] Show Stage 1 (context retrieval) progress
  - [ ] Show Stage 2 (code generation) progress
  - [ ] Display retrieved context artifacts
  - [ ] Display final code with syntax highlighting
- [ ] Add POST `/api/code/two-stage` endpoint (4 hours)
- [ ] Test with various coding prompts and model combinations (2-4 hours)

**Deliverable:** Two-stage coding with smart context retrieval and coder model integration

---

### Phase 5: Code Review Mode (Week 10-12) - 30-42 hours

**Goal:** Intelligent code review with smart file discovery and optional Council consensus

#### Code Review Mode (30-42 hours)
- [ ] **Build CodeReviewPanel UI component (8 hours)**
  - [ ] Add folder selection input
  - [ ] Add focus area checkboxes (6 presets)
  - [ ] Add custom intent text field
  - [ ] Add serial Council toggle
  - [ ] Integrate LiveProgress component
- [ ] **Implement smart file discovery (10 hours)**
  - [ ] Build `discover_relevant_files()` function
  - [ ] Combine focus areas + custom intent into unified query
  - [ ] Use CGRAG to identify relevant code chunks
  - [ ] Use fast model to score file relevance
  - [ ] Return top 5-10 files for review
- [ ] **Implement sequential file review (8 hours)**
  - [ ] Load file content with context
  - [ ] Call review model with focus areas
  - [ ] Parse issues (CRITICAL/WARNING/INFO)
  - [ ] Extract auto-fix suggestions
  - [ ] Track progress with LiveProgress
- [ ] **Add optional Council review (4 hours)**
  - [ ] Parallel mode: 3 models review simultaneously
  - [ ] Serial mode: 3 models review sequentially (VRAM-safe)
  - [ ] Synthesize consensus findings
- [ ] **Build CodeReviewResults component (6 hours)**
  - [ ] Display issues by severity
  - [ ] Show auto-fix suggestions
  - [ ] Add one-click copy for fixes
  - [ ] Display Council consensus if used
- [ ] **Backend API endpoints (4-6 hours)**
  - [ ] POST `/api/code/review/discover` - File discovery
  - [ ] POST `/api/code/review/analyze` - Review execution
  - [ ] WebSocket events for live progress

**Deliverable:** Code Review mode with smart folder review, CGRAG-guided discovery, and optional Council consensus

---

## Technical Specifications

### API Endpoints

#### POST /api/query (Updated)

**Request:**
```json
{
  "query": "Should we adopt microservices architecture?",
  "mode": "council",
  "council_adversarial": true,
  "use_context": true,
  "max_tokens": 2048,
  "temperature": 0.7
}
```

**Response (Council Mode):**
```json
{
  "response": "Neutral summary of debate...",
  "metadata": {
    "query_mode": "council",
    "council_mode": "adversarial",
    "council_participants": ["qwen_14b_balanced", "deepseek_32b_powerful"],
    "council_rounds": 2,
    "council_responses": [
      {
        "model_id": "qwen_14b_balanced",
        "position": "PRO",
        "round1": "Microservices offer...",
        "round2": "Rebutting the monolith argument...",
        "tokens": 523
      },
      {
        "model_id": "deepseek_32b_powerful",
        "position": "CON",
        "round1": "Monolithic architecture provides...",
        "round2": "Countering the microservices claims...",
        "tokens": 612
      }
    ],
    "processing_time_ms": 18234,
    "cgrag_artifacts": 3
  }
}
```

---

## Testing & Validation

### Council Mode Testing

**Test Cases:**
1. **3-Model Consensus** - Verify all 3 models participate in both rounds
2. **Synthesis Quality** - Check final answer incorporates all viewpoints
3. **Failure Handling** - Test with only 2 enabled models (should error gracefully)
4. **Round Tracking** - Verify metadata includes all responses
5. **Performance** - Measure total time (should be <30s for 3 models)

**Success Criteria:**
- ✅ All enabled models participate
- ✅ Final consensus is coherent and comprehensive
- ✅ Metadata tracks all rounds and participants
- ✅ Total time < 30 seconds
- ✅ Graceful error if <3 models available

### Debate Mode Testing

**Test Cases:**
1. **PRO/CON Balance** - Verify models take opposing positions
2. **Rebuttal Quality** - Check Round 2 responses address opponent's arguments
3. **Neutral Synthesis** - Ensure summary doesn't favor either side
4. **UI Display** - Verify side-by-side layout works
5. **Performance** - Measure total time (should be <20s)

**Success Criteria:**
- ✅ Clear PRO and CON positions
- ✅ Rebuttals directly address opponent
- ✅ Neutral summary presents both sides fairly
- ✅ UI clearly distinguishes sides
- ✅ Total time < 20 seconds

### Benchmark Mode Testing

**Test Cases:**
1. **Parallel Execution** - All models execute simultaneously
2. **Metric Accuracy** - Response times, token counts correct
3. **Semantic Similarity** - Matrix shows reasonable similarity scores (0.7-0.95)
4. **Grid Layout** - UI accommodates 2-5 models responsively
5. **Performance** - Parallel execution faster than sequential

**Success Criteria:**
- ✅ All enabled models execute in parallel
- ✅ Metrics are accurate and useful
- ✅ Similarity scores make sense
- ✅ UI scales to different model counts
- ✅ Total time ≈ slowest model (not sum of all)

---

## Quick Reference

### Effort Estimates Summary

| Feature | Backend | Frontend | Total | Status |
|---------|---------|----------|-------|--------|
| **Phase 0: Web Search** |
| SearXNG Integration | 2h | 2h | 4h | ✅ COMPLETE |
| **Phase 1: Foundation** |
| Mode UX Redesign | 1h | 5h | 6-8h | ✅ COMPLETE |
| Council Mode (Consensus) | 10h | 4h | 8-12h | ✅ COMPLETE |
| Debate Mode (Adversarial) | 8h | 6h | 12-16h | ✅ COMPLETE |
| Model Flag Management UI | 2h | 3h | 4-6h | ⏸️ DEFERRED |
| **Phase 1 Subtotal** | **21h** | **15h** | **~28h actual (est. 18-26h)** | ✅ COMPLETE |
| **Phase 2: Benchmark Mode** |
| Benchmark Mode + Serial Toggle | 16h | 12h | 20-24h | ⏳ NEXT |
| **Phase 2 Subtotal** | **16h** | **12h** | **20-24h** | ⏳ NEXT |
| **Phase 3: Code Chat Enhanced** |
| Code Chat with File Ops | 8h | 10h | 16-22h |
| **Phase 3 Subtotal** | **8h** | **10h** | **16-22h** |
| **Phase 4: Two-Stage Coding** |
| Two-Stage Coding Pipeline | 16h | 12h | 26-35h |
| **Phase 4 Subtotal** | **16h** | **12h** | **26-35h** |
| **Phase 5: Code Review Mode** |
| Code Review with Discovery | 18h | 16h | 30-42h |
| **Phase 5 Subtotal** | **18h** | **16h** | **30-42h** |
| **GRAND TOTAL** | **79h** | **70h** | **132-176h** |

### Priority Order

1. ✅ **Phase 0: Web Search** (4h) - COMPLETED 2025-11-04
   - SearXNG Integration - Privacy-respecting web search with CGRAG

2. ✅ **Phase 1: Foundation** (~28h actual) - COMPLETED 2025-11-04
   - Mode UX Redesign - Foundation for everything
   - Council Mode (Consensus) - Multiple models collaborate
   - Debate Mode (Adversarial) - Two models argue opposing views
   - Model Flag Management - DEFERRED (registry already has flags)

3. ⏳ **Phase 2: Benchmark Mode** (20-24h) - NEXT PRIORITY
   - Benchmark Mode + Serial Toggle - Side-by-side model comparison with VRAM safety

4. **Phase 3: Code Chat Enhanced** (16-22h) - Practical coding assistance
   - File creation and editing with drag-and-drop
   - Low complexity, high developer value

5. **Phase 4: Two-Stage Coding** (26-35h) - Advanced code generation
   - Leverages CGRAG for context-aware coding
   - Requires coder models with proper flags

6. **Phase 5: Code Review Mode** (30-42h) - Intelligent code analysis
   - Smart folder review with file discovery
   - Optional Council consensus for thorough review
   - Highest complexity, highest long-term value

### File Modification Checklist

**Backend:**
- [ ] `backend/app/models/query.py` - Add council fields to QueryRequest/QueryMetadata
- [ ] `backend/app/routers/query.py` - Add council/debate mode handlers
- [ ] `backend/app/services/prompts.py` - Add code-specific prompts (new file)

**Frontend:**
- [ ] `frontend/src/components/modes/ModeSelector.tsx` - Update modes, add config panel
- [ ] `frontend/src/components/modes/ModeSelector.module.css` - Style config panel
- [ ] `frontend/src/components/query/ResponseDisplay.tsx` - Add council/debate display
- [ ] `frontend/src/components/query/ResponseDisplay.module.css` - Style multi-model views
- [ ] `frontend/src/types/query.ts` - Update QueryMetadata interface

---

## Conclusion

This document provides a complete blueprint for implementing MAGI's next-generation features. The phased approach allows for:

1. ✅ **Phase 0** (COMPLETED) - SearXNG web search integration (4h actual)
2. ✅ **Phase 1** (COMPLETED) - Mode UX + Council + Debate modes (28h actual, ~2-3 weeks)
3. ⏳ **Phase 2** (NEXT) - Benchmark mode with serial toggle (20-24h estimated, ~2-3 weeks)
4. **Phase 3** - Code Chat with file creation/editing (16-22h estimated, ~2-3 weeks)
5. **Phase 4** - Two-stage coding with CGRAG (26-35h estimated, ~3-4 weeks)
6. **Phase 5** - Smart folder review with Council consensus (30-42h estimated, ~3-4 weeks)

**Key Decisions:**

1. **Flexible Model Configuration:** Using `coder` and `thinking` flags (not hardcoded model names) allows experimentation and adaptation as new models become available.

2. **VRAM Safety First:** Serial execution toggles in Benchmark and Council modes ensure systems with limited VRAM can still use all features, trading speed for memory efficiency.

3. **Smart File Discovery:** Code Review mode uses CGRAG-guided file discovery instead of manual file selection, reducing 47-file folders to 5 relevant files automatically.

4. **Context-Aware Coding:** Two-stage coding enhancement leverages CGRAG to provide relevant code context, enabling even smaller models to generate better code by working from examples.

5. **Universal LiveProgress:** Reusable progress component provides live feedback across all long-running operations (Benchmark, Council, Code Review), improving user experience.

**Scope Evolution:**

The original plan focused on multi-model orchestration (Council, Debate, Benchmark). User feedback revealed strong demand for coding features that respect local LLM limitations:
- **Not** a full coding assistant (context limits make this impractical)
- **Yes** to file creation/editing with preview/confirmation workflows
- **Yes** to smart code review with focused file discovery
- **Yes** to two-stage enhancement using CGRAG for context retrieval

This approach provides 80% of coding assistant value with 30% of the complexity - a better ROI for local LLMs.

**Next Steps:**

1. ✅ ~~**Phase 0:** SearXNG Web Search Integration (4h)~~ - COMPLETED 2025-11-04
2. ✅ ~~**Phase 1:** Mode UX + Council + Debate (28h actual)~~ - COMPLETED 2025-11-04
3. ⏳ **Phase 2:** Implement Benchmark mode with serial toggle (20-24h) - IN PROGRESS
4. **Phase 3:** Implement Code Chat with file operations (16-22h)
5. **Phase 4:** Build Two-Stage Coding Enhancement (26-35h)
6. **Phase 5:** Create Code Review Mode (30-42h)
7. **Test thoroughly** at each phase with real-world queries
8. **Iterate based on feedback** - local LLM behavior is unpredictable

---

**Document Version:** 1.2
**Last Updated:** 2025-11-04
**Status:** In Progress - Phase 1 Complete (32h completed / 74-96h total estimated)
**Completion:** ~40% complete (Phase 0 + Phase 1 done)
**Remaining Effort:** 42-64 hours across Phases 2-5
