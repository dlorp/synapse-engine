# MAGI Codebase Exploration Report

**Date:** 2025-11-04  
**Purpose:** Understand current implementation before implementing Council Mode and SearXNG integration  
**Status:** Complete - Ready for Implementation Planning

---

## Executive Summary

The MAGI system is a **production-ready Multi-Model Orchestration WebUI** with:
- ✅ **Two working query modes:** `simple` and `two-stage`
- ✅ **Tier-based model routing:** fast, balanced, powerful
- ✅ **CGRAG integration:** Full FAISS-based retrieval working
- ✅ **Profile system:** Development, production, fast-only
- ✅ **Dynamic model management:** Discovery, registry, server lifecycle
- ✅ **Complete UI:** Terminal-aesthetic React frontend with WebSocket support
- ❌ **No web search integration** (opportunity for SearXNG)
- ❌ **Council/Debate/Chat modes** marked as "COMING SOON"

**Key Finding:** System architecture is well-suited for adding Council Mode and SearXNG with minimal refactoring.

---

## 1. Current Mode System

### Frontend: ModeSelector Component
**File:** `/frontend/src/components/modes/ModeSelector.tsx`

**Lines 5-49:** Mode definitions
```typescript
export type QueryMode = 'two-stage' | 'simple' | 'council' | 'debate' | 'chat';

const MODES: ModeConfig[] = [
  {
    id: 'two-stage',
    label: 'TWO-STAGE',
    description: 'Fast model + CGRAG → Powerful refinement',
    available: true  // ✅ WORKING
  },
  {
    id: 'simple',
    label: 'SIMPLE',
    description: 'Single model query',
    available: true  // ✅ WORKING
  },
  {
    id: 'council',
    label: 'COUNCIL',
    description: 'Multiple LLMs discuss to consensus',
    available: false  // ❌ NOT IMPLEMENTED
  },
  {
    id: 'debate',
    label: 'DEBATE',
    description: 'Models argue opposing viewpoints',
    available: false  // ❌ NOT IMPLEMENTED
  },
  {
    id: 'chat',
    label: 'MULTI-CHAT',
    description: 'Models converse with each other',
    available: false  // ❌ NOT IMPLEMENTED
  }
];
```

**Integration Point:** Lines 52-84 - ModeSelector renders buttons, passes mode to HomePage

---

### Backend: Query Router
**File:** `/backend/app/routers/query.py`

**Lines 41-743:** Main query processing endpoint

**Mode Handling Logic:**
- **Line 52:** `mode: Literal["simple", "two-stage", "council", "debate", "chat"]` (Pydantic validation)
- **Lines 113-116:** Mode extraction from request
- **Lines 116-397:** Two-stage implementation (WORKING)
- **Lines 399-628:** Simple mode implementation (WORKING)
- **Lines 630-637:** Future modes handler (raises HTTPException 400)

**Two-Stage Workflow (Lines 116-397):**
1. Stage 1: FAST tier (b2-7) + CGRAG context → initial response
2. Complexity assessment → select Stage 2 tier (balanced/powerful)
3. Stage 2: Refinement prompt with Stage 1 response
4. Return refined response with both stages' metadata

**Simple Workflow (Lines 399-628):**
1. Default to FAST tier
2. Optional CGRAG context retrieval
3. Single model call
4. Return response with metadata

**Gap:** No council/debate/chat implementation yet

---

## 2. Query Processing Pipeline

### Request Flow
```
Frontend QueryInput → HomePage.handleQuerySubmit → useQuerySubmit hook → 
apiClient.post('/api/query') → FastAPI query.router → process_query() → 
ModelManager.call_model() → LlamaCppClient → llama-server
```

### Key Components

#### QueryRequest Model
**File:** `/backend/app/models/query.py` Lines 29-86
```python
class QueryRequest(BaseModel):
    query: str  # 1-10000 chars
    mode: Literal["simple", "two-stage", "council", "debate", "chat"]
    use_context: bool = True  # Enable CGRAG
    max_tokens: int = 256
    temperature: float = 0.7
```

#### QueryMetadata Model
**File:** `/backend/app/models/query.py` Lines 146-263
```python
class QueryMetadata(BaseModel):
    model_tier: str
    model_id: str
    complexity: Optional[QueryComplexity]
    tokens_used: int
    processing_time_ms: float
    cgrag_artifacts: int
    cgrag_artifacts_info: List[ArtifactInfo]
    cache_hit: bool
    query_mode: str = "simple"
    
    # Two-stage fields (Lines 216-261)
    stage1_response: Optional[str]
    stage1_model_id: Optional[str]
    stage1_tier: Optional[str]
    stage1_processing_time: Optional[int]
    stage1_tokens: Optional[int]
    # ... stage2 fields
```

**Extensibility:** QueryMetadata already has optional fields pattern - perfect for adding council-specific metadata

---

### Model Selection Logic
**File:** `/backend/app/services/routing.py`

**Lines 67-175:** `assess_complexity()` function
- Pattern detection (simple/moderate/complex keywords)
- Structural analysis (multiple parts, conditionals, reasoning)
- Score calculation with weighted factors
- Tier mapping: fast (<3.0), balanced (<7.0), powerful (≥7.0)

**Lines 178-201:** Pattern detection helper
- SIMPLE_PATTERNS: "what is", "define", "list"
- MODERATE_PATTERNS: "explain", "compare", "summarize"
- COMPLEX_PATTERNS: "analyze", "evaluate", "design"

**Integration Opportunity:** Complexity assessment could drive Council Mode delegation logic

---

### CGRAG Integration Points
**File:** `/backend/app/routers/query.py`

**Lines 136-240:** CGRAG retrieval for two-stage (duplicated in simple mode Lines 440-542)

**Current Flow:**
1. Check if `request.use_context == True`
2. Load FAISS index from `/app/data/faiss_indexes/docs.index`
3. Create CGRAGRetriever with min_relevance from config
4. Retrieve artifacts within token_budget (8000 default)
5. Build context prompt prepending artifacts to query
6. Pass augmented prompt to model

**Performance:**
- Index load: ~50-100ms (cached after first load)
- Retrieval: ~20-80ms
- Total overhead: ~100-200ms

**Gap:** No web search integration - only local document retrieval

---

## 3. Frontend Component Structure

### ResponseDisplay Component
**File:** `/frontend/src/components/query/ResponseDisplay.tsx`

**Lines 1-420:** Sophisticated response display with:
- **Lines 23-122:** Reasoning/thinking parser (detects DeepSeek R1 verbose output)
- **Lines 176-260:** Response content with collapsible thinking section
- **Lines 262-358:** Metadata panel (model, tokens, time, complexity, CGRAG artifacts)
- **Lines 360-416:** Two-stage processing panel (shows Stage 1 response)

**Key Features:**
- Splits response into thinking + answer sections automatically
- Shows full vs. split view toggle
- Displays CGRAG artifact details with relevance scores
- Two-stage processing timeline visualization

**Extensibility Hooks:**
- Lines 166-174: Could add `queryMode === 'council'` conditional rendering
- Lines 360-416: Two-stage panel pattern reusable for multi-model visualization
- Lines 314-356: CGRAG artifacts pattern adaptable for web search results

---

### Terminal UI Components
**Directory:** `/frontend/src/components/terminal/`

**Available Components:**
- `Panel` - Boxed sections with titles (Lines 1-50 in Panel.tsx)
- `MetricDisplay` - Label/value pairs with status colors
- `StatusIndicator` - Colored dots with labels (active/idle/error)
- `Button` - Terminal-styled buttons
- `Input` - Terminal-styled inputs
- `ProgressBar` - Animated loading bars
- `Divider` - Section separators

**Design System:**
- Colors: `#00ff41` (green), `#ff9500` (amber), `#00ffff` (cyan), `#ff0000` (red)
- Font: JetBrains Mono, IBM Plex Mono
- Aesthetic: Dense information displays, high contrast, real-time updates

**Reusable for Council Mode:** All components are mode-agnostic and composable

---

### HomePage Integration
**File:** `/frontend/src/pages/HomePage/HomePage.tsx`

**Lines 18-146:** Main query interface

**State Management:**
- Line 19: `latestResponse` - stores QueryResponse
- Line 20-21: `currentQueryMode`, `queryMode` - tracks selected mode
- Lines 30-52: `handleQuerySubmit()` - mutation with onSuccess/onError

**Mode Flow:**
1. User selects mode in ModeSelector (Line 102-105)
2. `setQueryMode()` updates state
3. On submit, mode passed to mutation (Line 37)
4. Timer component shows expected time based on mode (Line 122)
5. ResponseDisplay renders response (Line 134)

**Integration Point:** Lines 30-52 - handleQuerySubmit can be extended for council-specific preprocessing

---

## 4. Backend Models and Types

### Pydantic Models
**File:** `/backend/app/models/config.py`

**Key Models:**
- **Lines 8-47:** `ModelConfig` - llama-server configuration
- **Lines 49-75:** `RoutingConfig` - complexity thresholds, scoring weights
- **Lines 77-98:** `RedisConfig` - caching configuration
- **Lines 140-161:** `CGRAGIndexingConfig` - chunking, embeddings
- **Lines 162-180:** `CGRAGRetrievalConfig` - token budget, relevance
- **Lines 225-276:** `ModelManagementConfig` - scan paths, port ranges
- **Lines 278-323:** `AppConfig` - top-level application config

**Configuration Pattern:**
- YAML-based config with environment variable substitution
- Profile system: `config/profiles/{development,production,fast-only}.yaml`
- Pydantic validation ensures type safety

**Extensibility:** Add `CouncilConfig` model to `AppConfig` (Line 320+)

---

### TypeScript Types
**File:** `/frontend/src/types/query.ts`

**Lines 5-58:** Complete type definitions

```typescript
export type QueryMode = 'two-stage' | 'simple' | 'council' | 'debate' | 'chat';

export interface QueryRequest { /* ... */ }
export interface QueryComplexity { /* ... */ }
export interface ArtifactInfo { /* ... */ }
export interface QueryMetadata {
  // Lines 29-49: Standard fields
  modelTier: string;
  modelId: string;
  complexity: QueryComplexity | null;
  tokensUsed: number;
  processingTimeMs: number;
  cgragArtifacts: number;
  cgragArtifactsInfo: ArtifactInfo[];
  cacheHit: boolean;
  
  // Lines 40-49: Mode-specific fields (two-stage example)
  queryMode?: string;
  stage1Response?: string;
  stage1ModelId?: string;
  // ... etc
}
export interface QueryResponse { /* ... */ }
```

**Pattern:** Optional fields for mode-specific metadata - perfect for council additions

---

## 5. SearXNG Integration Opportunities

### Current State
**Finding:** No web search integration exists
- CGRAG only searches local indexed documents
- No SearXNG container in docker-compose.yml
- No web search service in backend

### Integration Points

#### 1. Backend Service Layer
**Location:** Create `/backend/app/services/websearch.py`

**Pattern to Follow:** CGRAGRetriever (Lines 404-565 in cgrag.py)
```python
class WebSearchClient:
    def __init__(self, searxng_url: str, timeout: int = 10):
        self.base_url = searxng_url
        self.timeout = timeout
    
    async def search(
        self,
        query: str,
        num_results: int = 5,
        categories: List[str] = ["general"]
    ) -> List[SearchResult]:
        # Search via SearXNG API
        # Format results similar to CGRAG artifacts
        pass
```

#### 2. Query Router Integration
**Location:** `/backend/app/routers/query.py`

**Integration Point:** Lines 142-240 (CGRAG section)
```python
# After CGRAG retrieval
if request.use_web_search:  # New parameter
    web_results = await web_search_client.search(
        query=request.query,
        num_results=5
    )
    # Merge with CGRAG results
    # Add to context prompt
```

#### 3. Configuration
**Location:** `/config/default.yaml`

**Add Section (after Line 92):**
```yaml
web_search:
  enabled: true
  searxng_url: "http://searxng:8080"
  timeout: 10
  max_results: 5
  categories:
    - general
    - science
```

#### 4. Docker Compose Service
**Location:** `/docker-compose.yml`

**Add Service (after Line 286):**
```yaml
searxng:
  image: searxng/searxng:latest
  container_name: magi_searxng
  restart: unless-stopped
  ports:
    - "8080:8080"
  environment:
    - BASE_URL=http://localhost:8080
  networks:
    - magi_net
```

#### 5. Frontend Types
**Location:** `/frontend/src/types/query.ts`

**Extend QueryRequest (Line 7+):**
```typescript
export interface QueryRequest {
  query: string;
  mode: QueryMode;
  useContext: boolean;
  useWebSearch?: boolean;  // NEW
  maxTokens: number;
  temperature: number;
}
```

**Extend QueryMetadata (Line 49+):**
```typescript
export interface QueryMetadata {
  // ... existing fields
  webSearchResults?: number;
  webSearchInfo?: WebSearchResult[];
}
```

#### 6. UI Integration
**Location:** `/frontend/src/components/query/QueryInput.tsx`

**Add Toggle (Line 86+):**
```tsx
<label className={styles.checkbox}>
  <input
    type="checkbox"
    checked={useWebSearch}
    onChange={(e) => setUseWebSearch(e.target.checked)}
    disabled={isLoading || disabled}
  />
  <span>WEB SEARCH</span>
</label>
```

---

## 6. Recommendations for Council Mode

### Architecture Design

#### 1. Backend Service: CouncilOrchestrator
**File:** Create `/backend/app/services/council.py`

**Responsibilities:**
- Manage multi-model discussion rounds
- Track conversation state (rounds, participants, consensus tracking)
- Aggregation strategies (majority vote, confidence-weighted, meta-model synthesis)
- Termination conditions (max rounds, consensus threshold, timeout)

**Suggested Structure:**
```python
class CouncilOrchestrator:
    def __init__(
        self,
        model_manager: ModelManager,
        max_rounds: int = 3,
        consensus_threshold: float = 0.7
    ):
        pass
    
    async def deliberate(
        self,
        query: str,
        participants: List[str],  # model_ids
        context: Optional[str] = None
    ) -> CouncilResult:
        # Round 1: Independent responses
        # Round 2+: Models see others' responses
        # Check consensus after each round
        # Return final aggregated response
        pass
```

#### 2. Query Router Extension
**File:** `/backend/app/routers/query.py`

**Add Branch (Line 638+):**
```python
elif query_mode == "council":
    # Council Mode Implementation
    from app.services.council import CouncilOrchestrator
    
    orchestrator = CouncilOrchestrator(
        model_manager=model_manager,
        max_rounds=config.council.max_rounds,
        consensus_threshold=config.council.consensus_threshold
    )
    
    # Select participant models (e.g., one per tier)
    participants = await _select_council_participants(model_manager)
    
    # Optional: CGRAG/Web Search context
    context = await _build_council_context(request, config)
    
    # Run deliberation
    result = await orchestrator.deliberate(
        query=request.query,
        participants=participants,
        context=context
    )
    
    # Build response with council metadata
    metadata = QueryMetadata(
        model_tier="council",
        model_id="+".join(participants),
        tokens_used=result.total_tokens,
        processing_time_ms=result.total_time_ms,
        query_mode="council",
        council_rounds=result.rounds,
        council_participants=result.participants,
        council_responses=result.all_responses,
        council_consensus_score=result.consensus_score
    )
    
    return QueryResponse(
        id=query_id,
        query=request.query,
        response=result.final_answer,
        metadata=metadata
    )
```

#### 3. Frontend Visualization
**File:** Create `/frontend/src/components/query/CouncilDisplay.tsx`

**Features:**
- Tabbed interface showing each model's response per round
- Consensus tracker (animated progress bar)
- Round-by-round timeline
- Participant avatars with status indicators
- Final aggregated response with confidence score

**Integration:**
```tsx
// In ResponseDisplay.tsx Line 416+
{metadata.queryMode === 'council' && (
  <CouncilDisplay councilData={metadata} />
)}
```

#### 4. Configuration
**File:** `/config/default.yaml`

**Add Section (Line 92+):**
```yaml
council:
  enabled: true
  max_rounds: 3
  consensus_threshold: 0.7
  min_participants: 2
  max_participants: 4
  participant_selection: "tier_diverse"  # or "all_tiers", "same_tier"
  aggregation_strategy: "confidence_weighted"
  timeout_per_round: 30
```

#### 5. Extended Types
**Backend:** `/backend/app/models/query.py` (Line 261+)
```python
# Add to QueryMetadata
council_rounds: Optional[int] = Field(default=None, alias="councilRounds")
council_participants: Optional[List[str]] = Field(default=None, alias="councilParticipants")
council_responses: Optional[List[Dict]] = Field(default=None, alias="councilResponses")
council_consensus_score: Optional[float] = Field(default=None, alias="councilConsensusScore")
```

**Frontend:** `/frontend/src/types/query.ts` (Line 49+)
```typescript
export interface QueryMetadata {
  // ... existing fields
  councilRounds?: number;
  councilParticipants?: string[];
  councilResponses?: CouncilRoundResponse[];
  councilConsensusScore?: number;
}

export interface CouncilRoundResponse {
  round: number;
  modelId: string;
  response: string;
  confidence: number;
  agreementScore: number;
}
```

---

## 7. Implementation Order

### Phase 1: SearXNG Integration (Low Risk)
**Estimated Time:** 4-6 hours

1. Add SearXNG service to docker-compose.yml (30 min)
2. Create `/backend/app/services/websearch.py` (1 hour)
3. Add configuration to `default.yaml` and AppConfig (30 min)
4. Integrate into query router (simple + two-stage modes) (1.5 hours)
5. Add frontend toggle in QueryInput (30 min)
6. Display web search results in ResponseDisplay (1 hour)
7. Testing and refinement (1 hour)

**Dependencies:** None - purely additive

**Risks:** Low - does not touch mode logic

---

### Phase 2: Council Mode Backend (Medium Risk)
**Estimated Time:** 8-12 hours

1. Create `/backend/app/services/council.py` with CouncilOrchestrator (3 hours)
2. Implement deliberation logic (rounds, consensus tracking) (2 hours)
3. Add council branch to `/backend/app/routers/query.py` (1.5 hours)
4. Extend QueryMetadata with council fields (30 min)
5. Add configuration to `default.yaml` (30 min)
6. Unit tests for CouncilOrchestrator (2 hours)
7. Integration testing with real models (2 hours)
8. Documentation (1 hour)

**Dependencies:** None - mode routing already supports extensibility

**Risks:** Medium - multi-model coordination complexity

---

### Phase 3: Council Mode Frontend (Low Risk)
**Estimated Time:** 6-8 hours

1. Create `/frontend/src/components/query/CouncilDisplay.tsx` (3 hours)
2. Design round-by-round visualization (2 hours)
3. Add consensus tracker UI (1 hour)
4. Integrate into ResponseDisplay (30 min)
5. Update TypeScript types (30 min)
6. Enable council mode in ModeSelector (change `available: true`) (5 min)
7. Testing and UX refinement (2 hours)

**Dependencies:** Phase 2 must be complete

**Risks:** Low - UI is independent of backend logic

---

### Phase 4: Polish and Optimization (Optional)
**Estimated Time:** 4-6 hours

1. Streaming responses for Council Mode (WebSockets)
2. Caching for council deliberations
3. Advanced aggregation strategies
4. Performance optimization (parallel model calls)
5. Edge case handling (model failures during council)

---

## 8. Files Requiring Modification

### SearXNG Integration
**New Files:**
- ✏️ `/backend/app/services/websearch.py` (create)
- ✏️ `/frontend/src/types/websearch.ts` (create)

**Modified Files:**
- ✏️ `/docker-compose.yml` (add searxng service)
- ✏️ `/config/default.yaml` (add web_search section)
- ✏️ `/backend/app/models/config.py` (add WebSearchConfig)
- ✏️ `/backend/app/models/query.py` (extend QueryRequest, QueryMetadata)
- ✏️ `/backend/app/routers/query.py` (integrate web search calls)
- ✏️ `/frontend/src/types/query.ts` (extend types)
- ✏️ `/frontend/src/components/query/QueryInput.tsx` (add toggle)
- ✏️ `/frontend/src/components/query/ResponseDisplay.tsx` (display results)

---

### Council Mode Implementation
**New Files:**
- ✏️ `/backend/app/services/council.py` (create)
- ✏️ `/frontend/src/components/query/CouncilDisplay.tsx` (create)
- ✏️ `/backend/tests/test_council.py` (create)

**Modified Files:**
- ✏️ `/config/default.yaml` (add council section)
- ✏️ `/backend/app/models/config.py` (add CouncilConfig)
- ✏️ `/backend/app/models/query.py` (extend QueryMetadata)
- ✏️ `/backend/app/routers/query.py` (add council mode branch)
- ✏️ `/frontend/src/types/query.ts` (extend types)
- ✏️ `/frontend/src/components/modes/ModeSelector.tsx` (set available: true)
- ✏️ `/frontend/src/components/query/ResponseDisplay.tsx` (add CouncilDisplay)

---

## 9. Testing Strategy

### SearXNG Integration Tests
**Unit Tests:**
- `test_websearch_client_search()` - verify API calls
- `test_websearch_result_formatting()` - verify result parsing
- `test_websearch_timeout_handling()` - verify timeout behavior

**Integration Tests:**
- `test_query_with_web_search()` - end-to-end query with web results
- `test_web_search_and_cgrag_merge()` - combined context building

**Manual Testing:**
- SearXNG container starts correctly
- Web search toggle works in UI
- Results display with proper formatting
- Errors handled gracefully (SearXNG down, no results)

---

### Council Mode Tests
**Unit Tests:**
- `test_council_orchestrator_single_round()` - basic deliberation
- `test_council_consensus_detection()` - consensus tracking
- `test_council_participant_selection()` - model selection logic
- `test_council_aggregation_strategies()` - vote/weighted/meta-model

**Integration Tests:**
- `test_council_mode_query()` - full end-to-end council query
- `test_council_with_cgrag_context()` - council + CGRAG
- `test_council_max_rounds_timeout()` - termination conditions

**Manual Testing:**
- Council mode UI displays correctly
- Round-by-round responses visible
- Consensus tracker animates properly
- Final response aggregation is sensible
- Performance is acceptable (<30s for 3 rounds)

---

## 10. Key Observations

### Strengths
✅ **Clean Architecture:** Service layer separation, dependency injection  
✅ **Type Safety:** Pydantic (backend) + TypeScript (frontend)  
✅ **Extensibility:** Mode-based routing with optional metadata fields  
✅ **Observability:** Structured logging, request IDs, performance metrics  
✅ **Docker-First:** All services containerized, hot reload enabled  
✅ **Configuration Management:** YAML + env vars + profiles  

### Gaps
❌ **No Web Search:** CGRAG only searches local documents  
❌ **No Multi-Model Modes:** Council/debate/chat not implemented  
❌ **No Streaming:** Responses arrive all-at-once (no chunked streaming)  
❌ **No Prompt Library:** Prompts are inline strings (not reusable templates)  
❌ **Limited Caching:** Redis configured but not actively used for model responses  

### Risks
⚠️ **Council Latency:** 3 rounds × 3 models × 5s = 45s+ total time  
⚠️ **Token Budget:** Council mode could easily exceed context windows  
⚠️ **Model Availability:** Council requires multiple models to be healthy  
⚠️ **Consensus Detection:** Semantic similarity comparison is non-trivial  

---

## 11. Next Steps

1. **Review this report** with the team
2. **Prioritize features:** SearXNG vs. Council Mode first?
3. **Create implementation plan** using `MAGI_REWORK.md` format (as requested)
4. **Set up development branch** for feature work
5. **Begin Phase 1 implementation** (SearXNG recommended - lower risk, immediate value)

---

## Appendix: File Structure Overview

```
${PROJECT_DIR}/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # Configuration loader
│   │   │   ├── dependencies.py    # FastAPI dependencies
│   │   │   ├── exceptions.py      # Custom exceptions
│   │   │   └── logging.py         # Structured logging
│   │   ├── models/
│   │   │   ├── config.py          # Pydantic config models
│   │   │   ├── query.py           # Query request/response models
│   │   │   └── model.py           # Model status models
│   │   ├── routers/
│   │   │   ├── query.py           # Main query endpoint ⭐
│   │   │   ├── models.py          # Model management endpoints
│   │   │   ├── admin.py           # Admin endpoints
│   │   │   └── health.py          # Health check endpoints
│   │   ├── services/
│   │   │   ├── cgrag.py           # CGRAG implementation ⭐
│   │   │   ├── routing.py         # Complexity assessment ⭐
│   │   │   ├── models.py          # ModelManager
│   │   │   ├── llama_client.py    # llama.cpp HTTP client
│   │   │   └── websearch.py       # ❌ NOT IMPLEMENTED (opportunity)
│   │   └── main.py                # FastAPI app entrypoint ⭐
│   ├── data/
│   │   ├── faiss_indexes/         # CGRAG vector indexes
│   │   └── model_registry.json    # Discovered models
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── modes/
│   │   │   │   └── ModeSelector.tsx        # Mode selection UI ⭐
│   │   │   ├── query/
│   │   │   │   ├── QueryInput.tsx          # Query input form ⭐
│   │   │   │   ├── ResponseDisplay.tsx     # Response renderer ⭐
│   │   │   │   └── CouncilDisplay.tsx      # ❌ NOT IMPLEMENTED
│   │   │   └── terminal/                   # UI component library
│   │   ├── types/
│   │   │   └── query.ts                     # TypeScript types ⭐
│   │   ├── hooks/
│   │   │   └── useQuery.ts                  # Query mutation hook ⭐
│   │   ├── pages/
│   │   │   └── HomePage/
│   │   │       └── HomePage.tsx             # Main query page ⭐
│   │   └── api/
│   │       ├── client.ts                    # Axios client
│   │       └── endpoints.ts                 # API endpoints
│   └── Dockerfile.dev
├── config/
│   ├── default.yaml                # Default configuration ⭐
│   └── profiles/
│       ├── development.yaml        # Dev profile ⭐
│       ├── production.yaml         # Prod profile
│       └── fast-only.yaml          # Fast-tier-only profile
├── docker-compose.yml              # Service orchestration ⭐
└── docs/
    └── architecture/
        └── PROJECT_SPECFINAL.md    # Original spec

⭐ = Critical files for understanding/implementation
❌ = Gaps/opportunities for new features
```

---

**End of Report**

