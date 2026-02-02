# Synapse Engine Query Modes

## Overview

Synapse Engine supports multiple query processing modes, each optimized for different use cases.

## Available Modes

### ✅ Two-Stage Mode (Implemented)

**Purpose:** Balance speed and quality through sequential refinement with intelligent tier selection

**Workflow:**
1. Fast model (FAST tier, 2B-7B) with CGRAG context generates initial response (500 tokens)
2. System assesses query complexity
3. Balanced model (8B-14B) OR Powerful model (>14B) refines the initial response based on complexity
4. Returns refined response with both stages' metadata

**Best for:**
- Complex queries requiring depth
- Questions benefiting from context retrieval
- Balanced speed/quality trade-off

**Performance:**
- Simple queries: <8 seconds (FAST → BALANCED)
- Complex queries: <15 seconds (FAST → POWERFUL)

**How it works:**
```
Query submitted
  ↓
Stage 1: FAST tier (2B-7B)
  - CGRAG retrieves context (<100ms)
  - Fast model processes query with context
  - Generates initial 500-token response
  - Completes in <3 seconds
  ↓
Complexity Assessment
  - Analyzes query structure and keywords
  - Scores complexity (0-15 scale)
  - Selects Stage 2 tier
  ↓
Stage 2: BALANCED (8B-14B) or POWERFUL (>14B)
  - Receives original query + Stage 1 response
  - Refines and expands initial response
  - Adds depth, examples, context
  - Completes in 5-12 seconds
  ↓
Final refined response returned
```

**Configuration:**
- Stage 1: Always FAST tier
- Stage 2: Complexity score < 7.0 → BALANCED, ≥ 7.0 → POWERFUL
- Stage 1 token limit: 500 tokens
- Stage 2 token limit: Configurable (default 2048)

---

### ✅ Simple Mode (Implemented)

**Purpose:** Single model query for straightforward requests

**Workflow:**
1. Single FAST tier model processes query directly
2. Optional CGRAG context retrieval
3. Returns response with standard metadata

**Best for:**
- Simple queries
- When speed is critical (<2 seconds)
- Testing individual models
- Quick fact lookups

**Performance:** <2 seconds

**How it works:**
```
Query submitted
  ↓
CGRAG retrieval (optional)
  - Retrieves context if enabled
  - <100ms overhead
  ↓
FAST tier model (2B-7B)
  - Processes query with optional context
  - Generates full response
  - Completes in <2 seconds
  ↓
Response returned
```

**Configuration:**
- Tier: FAST (2B-7B models)
- Context: Optional CGRAG retrieval
- Token limit: Configurable (default 2048)

---

### ✅ Council Mode (Implemented)

**Purpose:** Multiple models collaborate or debate through TRUE MULTI-CHAT dialogue

Council Mode has **two sub-modes** controlled by the `councilAdversarial` checkbox:

---

#### Consensus Sub-Mode (`councilAdversarial = false`)

**Current Implementation:** 2-round parallel refinement
**Status:** ✅ Implemented (awaiting multi-chat upgrade in Phase 2)

**Workflow:**
1. Round 1: 3+ models generate independent responses
2. Round 2: Each model reviews others' responses and refines
3. Synthesis: Most powerful model combines refined responses into consensus

**Best for:**
- Critical decisions requiring multiple perspectives
- Complex analysis benefiting from diversity
- Reducing single-model bias
- Collaborative problem-solving

**Performance:** <20 seconds (depends on model count)

**Future Enhancement (Phase 2):** Sequential multi-chat dialogue with 5-10 turns, round-robin speaker selection, and consensus detection.

---

#### Adversarial Sub-Mode (`councilAdversarial = true`) ✨ **NEW: True Multi-Chat**

**Status:** ✅ Implemented with TRUE sequential dialogue (v3.1)

**Workflow:**
1. **Turn 1:** Model PRO argues in favor
2. **Turn 2:** Model CON responds TO PRO's specific points
3. **Turn 3:** Model PRO counters CON's challenges
4. **Turn 4:** Model CON addresses PRO's rebuttals
5. **Turn N:** Continue sequentially until stalemate, concession, or max turns
6. **Synthesis:** Neutral summary presenting both positions fairly

**What Changed from v3.0:**
- ❌ **Old:** 2-round parallel refinement (opening → rebuttal → done)
- ✅ **New:** Sequential turn-taking dialogue (2-20 turns, dynamic termination)
- ✅ **New:** Models directly address each other ("Model PRO, your point about X...")
- ✅ **New:** Persona-driven responses with 6 named profiles
- ✅ **New:** Dynamic termination (stalemate or concession detection)

**Best for:**
- Exploring trade-offs and pros/cons
- Understanding opposing viewpoints
- Identifying argument weaknesses
- Complex issues with multiple angles

**Performance:** <25 seconds (typical 6-8 turns)

**Configuration Options:**
```json
{
  "mode": "council",
  "councilAdversarial": true,
  "councilMaxTurns": 10,
  "councilDynamicTermination": true,
  "councilPersonaProfile": "technical",
  "councilPersonas": {
    "pro": "custom persona description",
    "con": "custom persona description"
  }
}
```

**Named Persona Profiles:**
- **classic:** Optimistic advocate vs. Skeptical critic
- **technical:** Solution architect vs. Senior engineer
- **business:** Product manager vs. Risk analyst
- **scientific:** Research scientist vs. Peer reviewer
- **ethical:** Ethicist vs. Pragmatist
- **political:** Progressive reformer vs. Conservative defender

**Custom Personas:** Define your own roles (e.g., "environmental advocate" vs. "fiscal conservative")

**Termination Reasons:**
- `max_turns_reached`: Dialogue reached configured maximum
- `concession_detected`: One model conceded the argument
- `stalemate_repetition`: Arguments became repetitive
- `stalemate_disengagement`: Models stopped engaging substantively

---

### 🔄 Multi-Chat Mode (Future - Phase 3)

**Purpose:** Extended conversational dialogue (distinct from Council Adversarial)

**Planned Workflow:**
1. User provides conversation topic
2. Models assigned different personas/roles
3. Models exchange messages (10-20 sequential turns)
4. User can moderate/steer discussion mid-conversation
5. Conversation summary generated

**Difference from Council Adversarial:**
- More turns (10-20 vs. 2-10)
- User moderation during conversation (not just setup)
- Free-form dialogue vs. structured debate
- Exploratory vs. adversarial framing

**Best for:**
- Extended brainstorming sessions
- Role-playing scenarios
- Creative writing and storytelling
- Exploring ideas through dynamic dialogue

**Planned Performance:** <40 seconds (depends on turn count)

**Status:** Not yet implemented (Phase 3 roadmap)

---

## Mode Selection

Use the Mode Selector in the WebUI Home page to choose your query mode.

### Decision Matrix

| Need | Recommended Mode | Why |
|------|------------------|-----|
| Fast answer | Simple | Single model, <2s response |
| Quality answer | Two-Stage | Refinement improves depth |
| Multiple perspectives | Council (Consensus) | Collaboration reduces bias |
| Explore trade-offs | Council (Adversarial) | Sequential debate surfaces pros/cons |
| Extended dialogue | Multi-Chat (future) | Dynamic conversation sparks creativity |

### Mode Comparison

| Mode | Models | Time | Best For | Status |
|------|--------|------|----------|--------|
| **Simple** | 1 | <2s | Quick facts | ✅ Available |
| **Two-Stage** | 2 | <15s | Quality answers | ✅ Available |
| **Council (Consensus)** | 3+ | <20s | Collaboration | ✅ Available |
| **Council (Adversarial)** | 2 | <25s | Debate (TRUE multi-chat) | ✅ Available ✨ |
| **Benchmark** | All | Varies | Model comparison | ✅ Available |
| **Multi-Chat** | 2-4 | <40s | Extended dialogue | 🔄 Future (Phase 3) |

---

## Implementation Status

### Phase 1 (Complete - v3.0-v3.1)
- ✅ Simple mode
- ✅ Two-stage mode with complexity-based routing
- ✅ Council mode (consensus sub-mode with 2-round refinement)
- ✅ Council mode (adversarial sub-mode with TRUE multi-chat dialogue) ✨ **NEW in v3.1**
- ✅ Benchmark mode
- ✅ CGRAG integration
- ✅ Mode selector UI with dialogue configuration

**v3.1 True Multi-Chat Features:**
- ✅ Sequential turn-taking (2-20 configurable turns)
- ✅ Dynamic termination (stalemate/concession detection)
- ✅ 6 named persona profiles + custom personas
- ✅ Addressable dialogue ("Model PRO, your point about X...")
- ✅ Chat-style UI with PRO/CON visual distinction

### Phase 2 (Planned - v3.2)
- 🔄 Apply true multi-chat to Council consensus mode (3+ models)
- 🔄 Round-robin turn selection for consensus
- 🔄 Consensus detection algorithm
- 🔄 Multi-speaker chat UI (3+ participants)

### Phase 3 (Future - v4.0+)
- 🔄 Multi-chat mode (extended free-form dialogue, 10-20+ turns)
- 🔄 User moderation during conversation
- 🔄 Custom mode parameters UI
- 🔄 Mode templates and presets
- 🔄 Streaming responses for all modes

---

## Future Enhancements

- **Custom mode parameters:** Adjust model count, iteration rounds, token limits per mode
- **Hybrid modes:** Combine multiple approaches (e.g., Council + Debate)
- **User-defined workflows:** Create custom multi-step reasoning patterns
- **Mode analytics:** Track performance and quality metrics per mode
- **A/B testing:** Compare modes side-by-side
- **Mode recommendations:** Suggest best mode based on query analysis

---

## Technical Details

### Mode Routing Logic

```python
# query.py - Mode selection
if request.mode == "simple":
    # Single FAST tier model
    tier = "fast"
    model = select_model(tier)
    response = call_model(model, query)

elif request.mode == "two-stage":
    # Stage 1: FAST tier
    stage1_model = select_model("fast")
    stage1_response = call_model(stage1_model, query, max_tokens=500)

    # Stage 2: Assess complexity, select BALANCED or POWERFUL
    complexity = assess_complexity(query)
    stage2_tier = "powerful" if complexity.score >= 7.0 else "balanced"
    stage2_model = select_model(stage2_tier)
    stage2_response = call_model(stage2_model, refinement_prompt)
```

### Metadata Structure

Each mode returns metadata specific to its workflow:

**Simple:**
```json
{
  "queryMode": "simple",
  "modelTier": "fast",
  "modelId": "qwen_7b_fast",
  "processingTimeMs": 1850
}
```

**Two-Stage:**
```json
{
  "queryMode": "two-stage",
  "stage1Tier": "fast",
  "stage1ModelId": "qwen_7b_fast",
  "stage1ProcessingTime": 2100,
  "stage2Tier": "balanced",
  "stage2ModelId": "deepseek_14b_balanced",
  "stage2ProcessingTime": 4500,
  "processingTimeMs": 6600
}
```

---

For more information, see [README.md](../../README.md) and [DYNAMIC_CONTROL.md](./DYNAMIC_CONTROL.md).
