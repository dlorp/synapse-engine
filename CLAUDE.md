# S.Y.N.A.P.S.E. ENGINE - Claude Context

**Scalable Yoked Network for Adaptive Praxial System Emergence**

## Project Overview

You are working on **S.Y.N.A.P.S.E. ENGINE** - a distributed orchestration platform for local language models with Contextually-Guided Retrieval Augmented Generation (CGRAG), integrated web search, and a dense, terminal-inspired UI with real-time visualizations.

**Core Purpose:** Coordinate multiple quantization tiers (FAST/BALANCED/POWERFUL) of local LLM instances with automatic complexity assessment, sub-100ms context retrieval, and multi-stage processing workflows governed by the NEURAL SUBSTRATE ORCHESTRATOR.

**Project Status:** Production Ready (v5.0)

---

## Your Role & Responsibilities

You are the **lead technical architect and implementer** for this project. Your responsibilities include:

1. **Architecture decisions** - Design robust, scalable solutions following the spec
2. **Code implementation** - Write production-quality Python (FastAPI) and TypeScript (React)
3. **System integration** - Connect llama.cpp servers, FAISS, Redis, WebSockets
4. **UI/UX implementation** - Build terminal-aesthetic interfaces with real-time updates
5. **Performance optimization** - Meet strict latency and throughput targets
6. **Documentation** - Provide clear inline documentation and technical explanations

---

## Getting Up to Speed

**IMPORTANT: Before starting work, review [SESSION_NOTES.md](./SESSION_NOTES.md)**

The [`SESSION_NOTES.md`](./SESSION_NOTES.md) file contains the complete development history with:
- Recent implementation sessions (newest first - no scrolling needed!)
- Problems encountered and solutions
- Files modified with line numbers
- Breaking changes and architectural decisions
- Next steps and pending work

**When to check [SESSION_NOTES.md](./SESSION_NOTES.md):**
- At the start of every work session
- Before modifying recently changed files
- When encountering unexpected behavior
- To understand recent architectural decisions
- To avoid repeating solved problems

This file is kept in **reverse chronological order** (newest sessions at top) so you don't have to scroll to see recent work.

---

## Technology Stack & Constraints

### Backend
- **Python 3.11+** with FastAPI framework
- **FAISS** for vector similarity search
- **sentence-transformers** for embeddings
- **Redis** for caching
- **WebSockets** for real-time updates
- **Async/await** patterns throughout

### Frontend
- **React 19** with TypeScript (strict mode)
- **Vite** as build tool
- **TanStack Query** for data fetching
- **Chart.js** for metrics visualization
- **React Flow** for pipeline graphs
- **WebSocket client** for real-time updates

### Infrastructure
- **llama.cpp** servers (Q2/Q3/Q4 quantizations)
- **Docker Compose** for orchestration
- **SearXNG** for web search (optional)

### Performance Targets
- Simple queries (Q2): <2s response time
- Moderate queries (Q3): <5s response time
- Complex queries (Q4): <15s response time
- CGRAG retrieval: <100ms
- Cache hit rate: >70%
- UI: 60fps animations, <50ms WebSocket latency

---

## Your Available Tools & Capabilities

### Web Access
You have access to the web for research via:
- **WebSearch tool** - Search the web for current information, documentation, best practices
- **WebFetch tool** - Fetch and analyze specific URLs for detailed information

Use these when:
- Looking up latest API documentation (FastAPI, React 19, TanStack Query, etc.)
- Researching best practices or design patterns
- Finding solutions to specific errors or issues
- Checking compatibility between libraries
- Verifying current package versions

### MCP Tools
You have access to MCP (Model Context Protocol) tools including:
- **Browser automation** (Playwright) for testing and debugging web UIs
- **IDE integration** for accessing diagnostics and code execution
- **Sequential thinking** for complex problem-solving
- **Fetch tools** for advanced web scraping with image extraction

These tools extend your capabilities beyond standard file operations and command execution.

### File & System Tools
Standard Claude Code tools:
- **Read, Write, Edit** for file operations
- **Bash** for command execution
- **Glob and Grep** for searching codebases
- **Task** for delegating to specialized agents

**Remember:** Use these tools proactively. Don't hesitate to:
- Search the web when you need current information
- Use browser automation to test the UI
- Delegate complex tasks to specialized agents

---

## Development Environment

### Docker-Only Development (MANDATORY)

**⚠️ CRITICAL: ALL development and testing MUST be done in Docker.**

**Why Docker-Only:**
- Ensures environment parity between development and production
- Prevents "works on my machine" issues
- Avoids version mismatches between local dev servers and Docker containers
- Vite build-time environment variables are embedded during Docker build

**Workflow:**

```bash
# Start all services
docker-compose up -d

# View backend logs (note: prx: log prefix)
docker-compose logs -f synapse_core

# View frontend logs (note: [ifc:] log prefix)
docker-compose logs -f synapse_frontend

# Rebuild after code changes
docker-compose build --no-cache synapse_frontend  # Frontend changes
docker-compose build --no-cache synapse_core   # Backend changes
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

**NEVER:**
- ❌ Run `npm run dev` locally
- ❌ Run `uvicorn app.main:app --reload` locally
- ❌ Test features outside Docker
- ❌ Mix local dev servers with Docker services
- ❌ Assume local behavior matches Docker behavior

**Frontend Environment Variables:**
- Frontend uses Vite which embeds environment variables **at build time**
- Variables are defined in [`docker-compose.yml`](./docker-compose.yml) as **build args** (not runtime env vars)
- Changes to `IFACE_API_BASE_URL` or `IFACE_WS_URL` require `docker-compose build --no-cache synapse_frontend`
- Current configuration:
  - `IFACE_API_BASE_URL=/api` (relative URL for nginx proxy)
  - `IFACE_WS_URL=/ws` (relative URL for nginx proxy)

**Backend Configuration:**
- Profile loaded from `/app/config/profiles/*.yaml`
- Profile selected via `PRAXIS_PROFILE` environment variable (default: `development`)
- Model registry persisted in `./backend/data/model_registry.json`
- FAISS indexes in `./backend/data/faiss_indexes/`

**Testing Workflow:**
1. Make code changes in your editor
2. Rebuild relevant Docker service: `docker-compose build --no-cache <service>`
3. Restart containers: `docker-compose up -d`
4. Test in browser at `http://localhost:5173`
5. Check logs: `docker-compose logs -f <service>`

**Troubleshooting:**
- If admin panel shows 404s → check `IFACE_API_BASE_URL` is set to `/api` in [`docker-compose.yml`](./docker-compose.yml)
- If backend can't find profile → check `startup.py` path calculation is correct
- If changes don't appear → rebuild with `--no-cache` flag
- If containers won't start → check `docker-compose ps` and logs

---

## Documentation Requirements

**⚠️ MANDATORY: Create documentation regularly to avoid losing context.**

**During Each Work Session:**

1. **Create/Update [SESSION_NOTES.md](./SESSION_NOTES.md)** with:
   - Date and session summary
   - Problems encountered and solutions
   - Files modified with line numbers
   - Breaking changes or important decisions
   - Next steps or pending work

2. **Update [CLAUDE.md](./CLAUDE.md)** when:
   - Adding new development workflows
   - Discovering important patterns or anti-patterns
   - Making architectural decisions
   - Changing core dependencies or configurations

3. **Update [README.md](./README.md)** when:
   - Adding new features
   - Changing setup/installation steps
   - Modifying deployment procedures
   - Adding new scripts or commands

**Documentation Format:**

```markdown
# SESSION_NOTES.md

## 2025-11-03: Fixed Admin Panel & Docker Workflow

### Problems
- Admin panel returning 404 errors in Docker
- Model Management page crashing on undefined portRange
- Local dev servers conflicting with Docker

### Solutions
1. Fixed `VITE_API_BASE_URL` to use `/api` (relative URL)
2. Added null safety checks in ModelManagementPage.tsx line 206
3. Killed all local dev servers, enforcing Docker-only workflow

### Files Modified
- [`docker-compose.yml`](./docker-compose.yml):218 - Changed VITE_API_BASE_URL to /api
- backend/app/services/startup.py:55 - Fixed path calculation
- frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx:206 - Added optional chaining

### Next Steps
- Test admin panel discovery functionality
- Verify all API endpoints work correctly
- Monitor for any remaining 404 errors
```

**Why This Matters:**
- Prevents repeating solved problems
- Maintains context across long development sessions
- Creates audit trail for debugging
- Helps onboard new developers
- Documents decision rationale

### Documentation Linking Best Practices

**⚠️ IMPORTANT: Always add hyperlinks to file references in documentation.**

The MAGI project maintains a **well-connected documentation network** with 450+ hyperlinks across all markdown files. When creating or updating documentation, follow these linking standards:

**Linking Standards:**

1. **Use Relative Paths** - All links use relative paths for portability
   ```markdown
   # From root to root
   [SESSION_NOTES.md](./SESSION_NOTES.md)

   # From root to docs
   [TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)

   # From docs to root
   [README.md](../../README.md)

   # With section anchors
   [Team Structure](./PROJECT_OVERVIEW.md#team-structure)
   ```

2. **Preserve Original Text** - Add links around existing text, don't reword
   ```markdown
   # BEFORE
   Check SESSION_NOTES.md for recent context

   # AFTER
   Check [SESSION_NOTES.md](./SESSION_NOTES.md) for recent context
   ```

3. **Don't Link Inside Code Blocks** - Keep code examples unlinked
   ```markdown
   # GOOD
   Edit [docker-compose.yml](./docker-compose.yml):
   ```yaml
   services:
     backend:
       ...
   ```

   # BAD (don't do this)
   ```bash
   # Edit [docker-compose.yml](./docker-compose.yml)
   docker-compose up -d
   ```
   ```

4. **Link Common References**
   - Documentation files: README.md, CLAUDE.md, SESSION_NOTES.md, PROJECT_OVERVIEW.md
   - Configuration: docker-compose.yml, .env.example
   - Scripts: ./scripts/test-all.sh, etc.
   - Docs: All files in /docs directory
   - Source files: When mentioning specific implementation files

5. **Use Section Anchors** - Link to specific sections when relevant
   ```markdown
   See [Agent Documentation](./PROJECT_OVERVIEW.md#team-structure) for details
   ```

**When Creating New Documentation:**
- Add links to ALL file references (SESSION_NOTES, docker-compose.yml, scripts, etc.)
- Cross-reference related documentation
- Link to source files when discussing implementation
- Include "Related Documents" or "Additional Resources" section with relevant links

**Benefits:**
- One-click navigation between related documents
- Professional documentation feel
- Better discoverability
- Reduced time finding referenced files
- Creates interconnected knowledge graph

---

## Plan Mode Workflow

**⚠️ IMPORTANT: When using Plan Mode, always create an implementation guide for the next engineer.**

### Plan Mode Process

When a user requests complex changes and Plan Mode is active:

1. **Research thoroughly** - Use specialized agents to gather all necessary information
2. **Present comprehensive plan** - Use ExitPlanMode tool with detailed plan
3. **User approves plan** - User accepts the plan to proceed
4. **Create implementation guide** - Write detailed step-by-step guide for next engineer

### Implementation Guide Requirements

After plan approval, create a markdown file named `<PROJECT>_REWORK.md` (e.g., `MAGI_REWORK.md`) containing:

**Required Sections:**

1. **Executive Summary**
   - Vision statement (what's changing and why)
   - Key changes list
   - Current problems vs. new behavior
   - Expected outcomes

2. **Phase-by-Phase Breakdown**
   - One phase per major component/feature
   - For each phase:
     - File paths with line numbers
     - Current code snippets
     - New code snippets (complete, not placeholders)
     - Explanation of changes
     - Expected results

3. **Code Snippets**
   - Complete, production-ready code (no "// TODO" or "..." placeholders)
   - Exact line numbers for modifications
   - Full function/component implementations
   - Import statements included

4. **Testing Checklist**
   - Verification steps for each phase
   - End-to-end testing scenarios
   - Success criteria (checkboxes)

5. **Implementation Order**
   - Recommended sequence of phases
   - Dependencies between phases
   - Test points after critical phases

6. **Troubleshooting Guide**
   - Common issues and solutions
   - Debug commands
   - Log inspection tips

7. **Files Modified Summary**
   - Complete list of files to delete
   - Complete list of files to modify (with line ranges)
   - Complete list of new files to create

8. **Expected Results**
   - Before/after comparisons
   - Performance metrics table
   - User experience flow diagrams

**Example Structure:**

```markdown
# PROJECT_REWORK - Feature Name

**Date:** YYYY-MM-DD
**Status:** Implementation Plan
**Estimated Time:** X hours

## Executive Summary
[Vision and key changes]

## Phase 1: Component Name
### File: path/to/file.py
**Lines to modify:** XX-YY
**Current code:**
```python
[exact current code]
```
**New code:**
```python
[complete new code, no placeholders]
```
**Expected result:** [What should happen]

[... more phases ...]

## Testing Checklist
- [ ] Test item 1
- [ ] Test item 2

## Files Modified Summary
### Delete:
- ❌ file1.yml
### Update:
- ✏️ file2.py (lines 10-50)
### Create:
- ➕ file3.tsx
```

### Why This Approach

**Benefits:**
- **Continuity:** Next engineer has complete context
- **Reduces errors:** Explicit code snippets prevent misunderstandings
- **Time savings:** No need to re-research, plan is documented
- **Audit trail:** Decision rationale preserved
- **Onboarding:** New team members can understand changes

**When to Create:**
- Multi-phase implementations (>3 phases)
- Breaking changes to architecture
- Feature additions requiring multiple file changes
- System redesigns or refactors
- Any task estimated >4 hours

**When NOT to Create:**
- Simple bug fixes (<3 files)
- Documentation-only updates
- Single-file modifications
- Minor styling changes

### File Naming Convention

`<PROJECT>_<FEATURE>_REWORK.md` or `<PROJECT>_REWORK.md`

Examples:
- `SYNAPSE_REWORK.md` (general system redesign)
- `SYNAPSE_COUNCIL_MODE.md` (specific feature)
- `SYNAPSE_PERFORMANCE_OPTIMIZATION.md` (optimization work)

Place in project root for visibility.

---

## Design Philosophy & Aesthetics

### Terminal-Inspired UI Principles

The UI embraces **dense information displays** with **terminal aesthetics** inspired by engineering interfaces and Evangelion's NERV panels. This is NOT about nostalgia - it's about **functional density** and **immediate visual feedback**.

**Core Visual Principles:**
1. Dense information displays - every pixel serves a purpose
2. High contrast - bright text on dark backgrounds
3. Real-time feedback - live updating data at 60fps
4. Modular panels - boxed sections with borders and labels
5. Technical readout style - numerical data, status codes
6. Color-coded states - immediate visual understanding
7. Functional animations - purposeful state transitions

**Color Palette:**
- Background: `#000000` (pure black)
- Primary text: `#ff9500` (phosphor orange)
- Warnings: `#ff9500` (amber)
- Accents: `#00ffff` (cyan)
- Processing: `#00ffff` with pulse effect
- Errors: `#ff0000` (red)

**Note:** The primary brand color is phosphor orange (#ff9500), NOT phosphor green. This orange color is used for all primary text, borders, and status indicators to create the distinctive S.Y.N.A.P.S.E. ENGINE terminal aesthetic.

**Typography:**
- Primary font: JetBrains Mono, IBM Plex Mono, Fira Code
- Display font: Share Tech Mono
- Size scale: 10px (metadata) → 20px (headers)

---

## Code Style & Patterns

### Python Backend

```python
# GOOD: Async patterns, type hints, clear error handling
async def route_query(
    query: str,
    context: Optional[List[Artifact]] = None
) -> QueryRoute:
    """Route query to appropriate model tier.
    
    Args:
        query: User query text
        context: Optional CGRAG artifacts
        
    Returns:
        QueryRoute with model tier and configuration
    """
    try:
        complexity = await assess_complexity(query)
        tier = complexity.to_model_tier()
        return QueryRoute(tier=tier, complexity=complexity)
    except Exception as e:
        logger.error(f"Query routing failed: {e}")
        raise

# BAD: No type hints, poor error handling, unclear logic
def route(q, ctx=None):
    c = complexity(q)
    return c.tier
```

**Backend Requirements:**
- ✅ Type hints on all functions
- ✅ Async/await for I/O operations
- ✅ Structured logging with context
- ✅ Proper exception handling with error types
- ✅ Docstrings in Google format
- ✅ Pydantic models for validation
- ✅ Dependency injection patterns
- ❌ No blocking operations in async functions
- ❌ No print() for logging (use logger)
- ❌ No bare exceptions (specify types)

### TypeScript Frontend

```typescript
// GOOD: Type safety, error handling, clean separation
interface ModelStatus {
  name: string;
  port: number;
  state: 'active' | 'idle' | 'processing' | 'error';
  memoryUsed: number;
  memoryTotal: number;
}

const ModelStatusPanel: React.FC = () => {
  const { data: models, error } = useModelStatus();
  
  if (error) {
    return <ErrorDisplay error={error} />;
  }
  
  return (
    <Panel title="NEURAL SUBSTRATE STATUS">
      {models?.map(model => (
        <ModelCard key={model.name} model={model} />
      ))}
    </Panel>
  );
};

// BAD: No types, unclear logic, poor error handling
const Panel = (props) => {
  const models = props.data;
  return <div>{models.map(m => <Card data={m} />)}</div>;
};
```

**Frontend Requirements:**
- ✅ Strict TypeScript mode enabled
- ✅ Interface definitions for all data structures
- ✅ React functional components with proper hooks
- ✅ TanStack Query for data fetching
- ✅ Error boundaries for error handling
- ✅ Memoization for performance (useMemo, useCallback)
- ✅ Accessibility attributes (ARIA)
- ❌ No `any` types (use `unknown` or specific types)
- ❌ No prop drilling (use context or state management)
- ❌ No inline styles (use CSS modules or styled-components)

---

## Architecture Patterns

### CGRAG Implementation

The CGRAG (Contextually-Guided RAG) system uses embedding-based retrieval with token budget management:

```python
# Expected pattern
class CGRAGRetriever:
    def __init__(self, index: faiss.Index, chunks: List[Chunk]):
        self.index = index
        self.chunks = chunks
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def retrieve(
        self,
        query: str,
        token_budget: int = 8000,
        min_relevance: float = 0.7
    ) -> RetrievalResult:
        """Retrieve relevant artifacts within token budget."""
        # Embed query
        query_embedding = self.encoder.encode([query])[0]
        
        # Search FAISS index
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1), 
            k=50
        )
        
        # Filter by relevance and pack within budget
        artifacts = self._pack_artifacts(
            indices[0], 
            distances[0], 
            token_budget, 
            min_relevance
        )
        
        return RetrievalResult(
            artifacts=artifacts,
            tokens_used=sum(a.token_count for a in artifacts),
            relevance_scores=[a.relevance for a in artifacts]
        )
```

### Query Routing Logic

```python
# Complexity assessment drives model selection
async def assess_complexity(query: str) -> QueryComplexity:
    """Assess query complexity using heuristics and patterns."""
    # Token count
    token_count = len(query.split())
    
    # Detect complexity indicators
    has_multiple_parts = any(sep in query for sep in ['and', 'then', 'also'])
    has_comparison = any(word in query for word in ['compare', 'versus', 'difference'])
    has_analysis = any(word in query for word in ['analyze', 'evaluate', 'assess'])
    has_reasoning = any(word in query for word in ['why', 'explain', 'reasoning'])
    
    # Calculate complexity score
    score = token_count * 0.1
    if has_multiple_parts: score += 2
    if has_comparison: score += 3
    if has_analysis: score += 4
    if has_reasoning: score += 2
    
    # Map to tier
    if score < 3:
        return QueryComplexity(tier='Q2', score=score)
    elif score < 7:
        return QueryComplexity(tier='Q3', score=score)
    else:
        return QueryComplexity(tier='Q4', score=score)
```

### WebSocket Event System

```typescript
// Frontend WebSocket pattern
const useModelEvents = () => {
  const [events, setEvents] = useState<ModelEvent[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onmessage = (event) => {
      const modelEvent = JSON.parse(event.data) as ModelEvent;
      setEvents(prev => [...prev, modelEvent]);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => ws.close();
  }, []);
  
  return events;
};
```

---

## Response Format Preferences

### When Explaining Code
1. Start with a brief summary of what the code does
2. Explain key design decisions
3. Highlight important patterns or edge cases
4. Note performance considerations if relevant
5. Provide usage examples if complex

### When Implementing Features
1. Confirm understanding of the requirement
2. Outline approach briefly
3. Implement with inline comments for complex logic
4. Include error handling and edge cases
5. Suggest tests or validation approaches

### When Debugging
1. Identify the issue clearly
2. Explain the root cause
3. Provide the fix with explanation
4. Suggest how to prevent similar issues

---

## Key Technical Considerations

### CGRAG Performance
- Pre-compute embeddings during indexing
- Use batching for embedding generation
- Implement smart caching with Redis
- Monitor cache hit rates and optimize
- Use FAISS IVF indexes for >100k chunks

### Model Management
- Health check endpoints for each model
- Automatic retry with exponential backoff
- Load balancing across Q2 instances
- Graceful degradation if models unavailable
- Memory monitoring with automatic warnings

### WebSocket Reliability
- Automatic reconnection with exponential backoff
- Message queuing during disconnection
- Heartbeat pings to detect dead connections
- Structured event types with validation
- Rate limiting to prevent overwhelm

### UI Performance
- Virtual scrolling for long lists
- RequestAnimationFrame for smooth animations
- Debouncing for frequent updates
- Web Workers for heavy computation
- Code splitting for faster initial load

---

## Testing Requirements

### Backend Tests
```python
# Unit tests with pytest
async def test_cgrag_retrieval():
    retriever = CGRAGRetriever(mock_index, mock_chunks)
    result = await retriever.retrieve("test query", token_budget=5000)
    assert result.tokens_used <= 5000
    assert len(result.artifacts) > 0

# Integration tests
async def test_query_routing():
    response = await client.post("/api/query", json={
        "query": "explain async patterns",
        "mode": "auto"
    })
    assert response.status_code == 200
    assert response.json()["model_tier"] == "Q3"
```

### Frontend Tests
```typescript
// Component tests with React Testing Library
test('ModelStatusPanel displays models', async () => {
  render(<ModelStatusPanel />);
  
  await waitFor(() => {
    expect(screen.getByText('Q2_FAST_1')).toBeInTheDocument();
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });
});

// E2E tests with Playwright
test('complete query flow', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.fill('[data-testid="query-input"]', 'test query');
  await page.click('[data-testid="submit-button"]');
  await expect(page.locator('[data-testid="response"]')).toBeVisible();
});
```

---

## Common Pitfalls to Avoid

### Backend
- ❌ Blocking operations in async functions (use asyncio equivalents)
- ❌ Not closing FAISS indexes properly (resource leaks)
- ❌ Hardcoded paths or ports (use configuration)
- ❌ Missing error handling around external calls
- ❌ Not validating model responses before processing

### Frontend
- ❌ Not handling WebSocket disconnections gracefully
- ❌ Infinite re-renders from bad useEffect dependencies
- ❌ Memory leaks from uncancelled subscriptions
- ❌ Not memoizing expensive computations
- ❌ Blocking main thread with heavy operations

### Integration
- ❌ Not handling model timeouts properly
- ❌ Missing backpressure mechanisms for streaming
- ❌ Not validating token counts before sending to models
- ❌ Ignoring context window limits
- ❌ Not monitoring system resource usage

---

## Communication Style

When working with me on this project:

✅ **DO:**
- Be direct and technical - I understand the domain
- Explain your reasoning for architectural decisions
- Point out potential issues or edge cases
- Suggest optimizations or improvements
- Ask clarifying questions if requirements are ambiguous
- Provide complete, working code examples
- Include error handling and edge cases

❌ **DON'T:**
- Oversimplify technical concepts
- Omit error handling "for brevity"
- Use placeholder comments like "// TODO: implement"
- Skip type hints or interface definitions
- Provide incomplete code requiring me to "fill in the rest"
- Ignore performance considerations
- Make assumptions without stating them

---

## Success Criteria

This project succeeds when:

1. **Functional**: All query types route correctly and return appropriate responses
2. **Performant**: Meets all response time and throughput targets
3. **Reliable**: 99.5%+ uptime with graceful degradation
4. **Observable**: Comprehensive telemetry and real-time visualization
5. **Maintainable**: Clear code structure with good documentation
6. **Aesthetic**: Dense, terminal-inspired UI with smooth 60fps animations

---

## Claude Code Specialized Agents

For this project, you have access to **4 specialized Claude Code agents**. Each agent has deep expertise in a specific domain and should be used for work within their area of specialization.

### When to Use Which Agent

**Use the general Claude (me) when:**
- Coordinating between multiple domains
- High-level architecture decisions
- Initial project planning and design
- Cross-cutting concerns
- Unclear which specialist is needed

**Use specialized agents for:**
- Focused, domain-specific implementation work
- Deep dives into technical areas
- Following established patterns within a domain

---

### 1. Backend Architect Agent

**Domain:** FastAPI, async Python, WebSockets, model orchestration, API design

**Use this agent for:**
- Implementing FastAPI endpoints and routers
- Building WebSocket server for real-time updates
- Creating model management system (health checks, load balancing, routing)
- Query complexity assessment and routing logic
- Redis caching implementation
- Event bus system design
- Model server integration (llama.cpp API calls)
- Backend performance optimization

**Example tasks:**
- "Implement the query routing endpoint with complexity assessment"
- "Build the WebSocket broadcast system for model events"
- "Create the model manager with health checking"
- "Implement Redis caching for model responses"

**Prompt file:** [backend-architect.md](./.claude/agents/backend-architect.md)

---

### 2. Frontend Engineer Agent

**Domain:** React, TypeScript, terminal UI, real-time visualizations, WebSockets

**Use this agent for:**
- Building React components with TypeScript
- Implementing terminal-aesthetic UI components
- Creating real-time visualizations (Chart.js, React Flow)
- WebSocket client integration
- TanStack Query data fetching
- 60fps animation implementation
- Component testing with React Testing Library
- CSS/styling with design system

**Example tasks:**
- "Build the model status panel with live updates"
- "Create the query input component with terminal styling"
- "Implement the processing pipeline visualization with React Flow"
- "Build the context window allocation display"

**Prompt file:** [frontend-engineer.md](./.claude/agents/frontend-engineer.md)

---

### 3. CGRAG Specialist Agent

**Domain:** Vector search, FAISS, embeddings, retrieval optimization, token budget management

**Use this agent for:**
- CGRAG indexing pipeline implementation
- FAISS vector search optimization
- Embedding generation with sentence-transformers
- Token budget management algorithms
- Relevancy scoring and artifact selection
- Caching strategies for embeddings
- Retrieval performance optimization (<100ms)
- Context window allocation logic

**Example tasks:**
- "Build the CGRAG indexing pipeline with chunking"
- "Implement the retrieval engine with token budget management"
- "Optimize FAISS index for >100k documents"
- "Create embedding cache with Redis"

**Prompt file:** [cgrag-specialist.md](./.claude/agents/cgrag-specialist.md)

---

### 4. DevOps Engineer Agent

**Domain:** Docker, deployment, CI/CD, monitoring, testing infrastructure, infrastructure automation

**Use this agent for:**
- Docker Compose configuration
- Dockerfile creation and optimization
- Model startup/shutdown scripts
- Health check implementation
- CI/CD pipeline setup (GitHub Actions)
- Monitoring configuration (Prometheus, Grafana)
- Backup and recovery automation
- Testing infrastructure (pytest, Playwright)
- Resource allocation and optimization

**Example tasks:**
- "Set up Docker Compose with all services"
- "Create GitHub Actions CI/CD pipeline"
- "Implement Prometheus metrics collection"
- "Build backup automation for FAISS indexes"

**Prompt file:** [devops-engineer.md](./.claude/agents/devops-engineer.md)

---

### Agent Collaboration Patterns

**Multi-agent workflows:**

1. **API Integration (Backend + Frontend)**
   - Backend Architect: Design and implement API endpoint
   - Frontend Engineer: Build UI and integrate endpoint
   - Collaboration: Agree on request/response schemas

2. **CGRAG Integration (CGRAG + Backend + Frontend)**
   - CGRAG Specialist: Build retrieval engine
   - Backend Architect: Integrate into query pipeline
   - Frontend Engineer: Build context visualization
   - Collaboration: Define data formats and performance requirements

3. **Deployment Pipeline (DevOps + All)**
   - DevOps Engineer: Set up infrastructure
   - Backend Architect: Provide health check endpoints
   - Frontend Engineer: Optimize build process
   - CGRAG Specialist: Document index backup requirements
   - Collaboration: Ensure all services deploy correctly

4. **End-to-End Feature (All Agents)**
   - Backend Architect: API endpoints
   - CGRAG Specialist: Context retrieval
   - Frontend Engineer: UI components
   - DevOps Engineer: Deployment and monitoring
   - Collaboration: Full feature implementation

**Handoff pattern:**
When work spans multiple domains, complete work in one domain before moving to the next. Document interfaces clearly for smooth handoffs.

---

## Current Implementation Phase

Follow the implementation roadmap in the spec:

**Phase A (Weeks 1-2): Foundation**
- Backend scaffolding with FastAPI → **Backend Architect Agent**
- Basic model management and health checks → **Backend Architect + DevOps Engineer Agents**
- Frontend shell with routing → **Frontend Engineer Agent**
- Terminal UI components library → **Frontend Engineer Agent**

**Phase B (Weeks 3-4): Core Features**
- CGRAG indexing and retrieval → **CGRAG Specialist Agent**
- Query routing logic → **Backend Architect Agent**
- WebSocket real-time updates → **Backend Architect + Frontend Engineer Agents**
- Model status dashboard → **Frontend Engineer Agent**

**Phase C (Weeks 5-6): Integration**
- Multi-model orchestration → **Backend Architect Agent**
- Web search integration → **Backend Architect Agent**
- Processing pipeline visualization → **Frontend Engineer Agent**
- Context window viewer → **Frontend Engineer Agent**

**Phase D (Weeks 7-8): Polish**
- Performance optimization → **All Agents (domain-specific)**
- Advanced visualizations → **Frontend Engineer Agent**
- Configuration management → **DevOps Engineer Agent**
- Deployment automation → **DevOps Engineer Agent**

Refer to the full specification for detailed acceptance criteria for each phase.

---

## Quick Reference

### Key Files Structure
```
project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   │   ├── cgrag.py         # CGRAG engine
│   │   │   ├── routing.py       # Query routing
│   │   │   └── models.py        # Model management
│   │   └── models/              # Pydantic schemas
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── ModelStatus/     # Model status panel
│   │   │   ├── QueryInput/      # Query interface
│   │   │   ├── Pipeline/        # Pipeline visualization
│   │   │   └── Terminal/        # Terminal UI base
│   │   ├── hooks/               # Custom hooks
│   │   ├── api/                 # API client
│   │   └── types/               # TypeScript types
│   └── tests/
└── docker-compose.yml
```

### Essential Commands
```bash
# Backend
uvicorn app.main:app --reload                # Dev server
pytest tests/                                # Run tests
python -m app.services.cgrag index ./docs   # Index docs

# Frontend  
npm run dev                                  # Dev server
npm run test                                 # Run tests
npm run build                                # Production build
```

---

**Remember:** This is a production system. Prioritize reliability, performance, and maintainability. Every component should be observable, testable, and handle errors gracefully. The terminal aesthetic is central to the UX - dense information displays with real-time updates at 60fps.
