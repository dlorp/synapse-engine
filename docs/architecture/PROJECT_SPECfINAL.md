# Multi-Model Orchestration WebUI - Project Specification

**Version:** 3.0
**Last Updated:** 2025-11-02
**Status:** Ready for Implementation

**Quick Links:**
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Development roadmap
- [Project Status](PROJECT_STATUS.md) - Current status
- [Docker Infrastructure](DOCKER_INFRASTRUCTURE.md) - Docker setup
- [Testing Guide](../TESTING_GUIDE.md) - Testing procedures
- [README](../../README.md) - Getting started

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Scope & Goals](#2-project-scope--goals)
3. [Core Architecture](#3-core-architecture)
4. [Visual Design Language](#4-visual-design-language)
5. [Model Orchestration System](#5-model-orchestration-system)
6. [CGRAG Implementation](#6-cgrag-implementation)
7. [Web Search Integration](#7-web-search-integration)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Real-Time Visualizations](#9-real-time-visualizations)
10. [API Design](#10-api-design)
11. [Configuration System](#11-configuration-system)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [Testing & Quality Assurance](#13-testing--quality-assurance)
14. [Performance Targets](#14-performance-targets)
15. [Deployment](#15-deployment)

---

## 1. Executive Summary

A modern web interface for orchestrating multiple local LLM instances with Contextually-Guided Retrieval Augmented Generation (CGRAG), integrated web search, and a dense, terminal-inspired UI with real-time visualizations.

### Key Capabilities
- **Multi-tier model orchestration**: Q2 (fast extraction) → Q3 (synthesis) → Q4 (deep analysis)
- **Intelligent routing**: Automatic complexity assessment routes queries to optimal model tier
- **CGRAG retrieval**: Embedding-based context selection with 70%+ cache hit rates
- **Web search integration**: SearXNG meta-search with result filtering and synthesis
- **Real-time visualization**: Live token streaming, model status, processing pipeline graphs
- **Terminal aesthetics**: Dense information displays inspired by technical interfaces and Evangelion UIs

### Technology Stack
- **Backend**: FastAPI (Python 3.11+), FAISS, sentence-transformers, Redis
- **Frontend**: React 19 + TypeScript, Vite, TanStack Query, Chart.js, React Flow
- **Models**: llama.cpp servers with DeepSeek R1 Qwen3 8B (Q2/Q3/Q4 quantizations)
- **Infrastructure**: Docker Compose, WebSocket for real-time updates

---

## 2. Project Scope & Goals

### Goals
1. **Developer-friendly orchestration** of multiple local LLM instances for different query complexities
2. **Transparent CGRAG pipeline** with instrumentation showing retrieval decisions
3. **Rich telemetry** for debugging and driving live UI visualizations
4. **Dense, information-rich UI** with terminal aesthetics and progressive visual enhancements
5. **Self-hosted deployment** with privacy and control as primary concerns

### Non-Goals (Initial Release)
- Multi-tenant cloud orchestration (single-host first)
- Voice input/output (text-only initially)
- Mobile-first responsive design (desktop-optimized first)
- Fine-tuning workflows (inference only)

### Success Criteria
- Query response times: <2s (simple), <5s (moderate), <15s (complex)
- CGRAG cache hit rate: >70%
- UI frame rate: 60fps for animations
- Model uptime: >99%
- WebSocket latency: <50ms

---

## 3. Core Architecture

### System Overview

```
┌─────────────────────────────────────────────────────┐
│            Browser (React Frontend)                 │
│  ┌──────────────────────────────────────────────┐   │
│  │  Terminal UI + Real-time Visualizations     │   │
│  │  - Query Input & Response Streaming         │   │
│  │  - Model Status Dashboard                   │   │
│  │  - Processing Pipeline Graph                │   │
│  │  - Context Viewer + Metrics                 │   │
│  └──────────────────────────────────────────────┘   │
└───────────────────┬─────────────────────────────────┘
                    │ WebSocket + HTTP/REST
                    ▼
┌─────────────────────────────────────────────────────┐
│         FastAPI Backend (Orchestration)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │   Query      │  │   CGRAG      │  │  Model   │  │
│  │   Router     │──│   Engine     │──│ Manager  │  │
│  │              │  │  (FAISS +    │  │          │  │
│  │              │  │  Embeddings) │  │          │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
│         │                │                 │         │
│         └────────────────┼─────────────────┘         │
│                          │                           │
│  ┌──────────────┐  ┌────┴──────┐  ┌──────────────┐  │
│  │   Web        │  │   Redis   │  │   Event      │  │
│  │   Search     │  │   Cache   │  │   Bus        │  │
│  └──────────────┘  └───────────┘  └──────────────┘  │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP API calls
                    ▼
┌─────────────────────────────────────────────────────┐
│         llama.cpp Model Servers                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Q2:8080  │ │ Q2:8081  │ │ Q3:8082  │ │Q4:8083 │ │
│  │ 16k ctx  │ │ 16k ctx  │ │ 24k ctx  │ │32k ctx │ │
│  │ ~3GB RAM │ │ ~3GB RAM │ │ ~7GB RAM │ │~10GB   │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Frontend (React)**
- User interaction and query submission
- Real-time token streaming display
- Live model status and metrics visualization
- Processing pipeline animation
- Context artifact viewer

**Backend (FastAPI)**
- Query complexity assessment and routing
- CGRAG context retrieval and assembly
- Multi-model orchestration and collaboration
- Web search integration and result filtering
- WebSocket event broadcasting
- Model health monitoring

**CGRAG Engine**
- Document indexing and embedding
- Vector similarity search (FAISS)
- Relevancy scoring and artifact selection
- Token budget management
- Cache optimization

**Model Tier System**
- **Q2 instances (8080, 8081)**: Fast extraction, parallel processing, web search
- **Q3 instance (8082)**: Synthesis of multiple sources, moderate complexity
- **Q4 instance (8083)**: Deep analysis, complex reasoning, strategic planning

---

## 4. Visual Design Language

### Design Philosophy

The UI embraces **terminal aesthetics** with **dense information displays** inspired by technical interfaces, engineering CAD systems, and Evangelion's NERV operations panels. This is not purely retro - it's about **functional density** and **immediate visual feedback**.

### Core Principles
1. **Dense information displays** - Every pixel serves a purpose
2. **High contrast** - Bright text on dark backgrounds for readability
3. **Real-time feedback** - Live updating data with smooth 60fps animations
4. **Modular panels** - Boxed sections with clear borders and labels
5. **Technical readout style** - Numerical data, status codes, coordinate systems
6. **Color-coded states** - Immediate visual understanding through color
7. **Functional animations** - Purposeful transitions that communicate state changes

### Color Palette

```css
:root {
  /* Backgrounds */
  --bg-primary: #000000;        /* Pure black canvas */
  --bg-panel: #0a0a0a;          /* Panel backgrounds */
  --bg-input: #1a1a1a;          /* Input fields */
  
  /* Primary Colors */
  --phosphor-green: #00ff41;    /* Primary text, success */
  --amber: #ff9500;             /* Warnings, highlights */
  --cyan: #00ffff;              /* Accents, links */
  --blue: #3399ff;              /* Info, secondary */
  
  /* Status Colors */
  --status-active: #00ff41;     /* Model active */
  --status-processing: #00ffff; /* Processing with pulse */
  --status-idle: #ff9500;       /* Standby/idle */
  --status-error: #ff0000;      /* Errors/critical */
  --status-success: #00ff88;    /* Success states */
  
  /* Evangelion-inspired gradients */
  --gradient-eva: linear-gradient(to bottom, 
    #00ffff 0%,    /* Cyan */
    #0088ff 33%,   /* Blue */
    #6644ff 66%,   /* Purple */
    #ff00ff 100%   /* Magenta */
  );
  
  /* UI Elements */
  --border-primary: #00ff41;
  --border-warning: #ff9500;
  --grid-lines: #1a3a1a;
}
```

### Typography

```css
--font-mono: 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', 'Consolas', monospace;
--font-display: 'Share Tech Mono', monospace;

/* Size Scale */
--text-xl: 20px;   /* Headers */
--text-lg: 16px;   /* Subheaders */
--text-md: 14px;   /* Body */
--text-sm: 12px;   /* Details */
--text-xs: 10px;   /* Metadata */
```

### Key Visual Components

#### 1. Model Status Panel (Evangelion-Style)

```
╔═══════════════════════════════════════╗
║  ▓▓▓▓ NEURAL SUBSTRATE STATUS ▓▓▓▓   ║
╠═══════════════════════════════════════╣
║  Q2_FAST_1 [8080]                     ║
║  ████████████░░░░ ACTIVE   2.3/3.0GB  ║
║                                        ║
║  Q2_FAST_2 [8081]                     ║
║  ███░░░░░░░░░░░░ IDLE      0.4/3.0GB  ║
║                                        ║
║  Q3_SYNTH  [8082]                     ║
║  ██████████░░░░░ ACTIVE   5.1/7.0GB   ║
║                                        ║
║  Q4_DEEP   [8083]                     ║
║  ░░░░░░░░░░░░░░░ STANDBY  0.0/10.0GB  ║
╠═══════════════════════════════════════╣
║  TOTAL VRAM: [████████░░░░] 7.8/23GB  ║
║  CACHE HIT RATE: 87.4%                ║
║  QUERIES/SEC: 2.3                     ║
╚═══════════════════════════════════════╝
```

#### 2. Context Window Allocation

```
CONTEXT WINDOW ALLOCATION [24,576 tokens] ── USAGE: 65.3%

┌──────────────────────────────────────────────────┐
│██████████████████████████████████████▓▓▓▓░░░░░░░░│
└──────────────────────────────────────────────────┘

▓▓▓▓▓▓ USER QUERY          2,341 tokens  ( 9.5%)
██████ CGRAG ARTIFACTS     8,892 tokens  (36.2%)
██████ WEB SEARCH RESULTS  3,104 tokens  (12.6%)
██████ SYSTEM PROMPT       1,456 tokens  ( 5.9%)
██████ CONVERSATION HIST   1,234 tokens  ( 5.0%)
░░░░░░ AVAILABLE SPACE     7,549 tokens  (30.7%)
──────────────────────────────────────────────────
0        6k       12k      18k      24k
```

**3. Processing Pipeline Flowchart (Node-Based)**
```
        ┌─────────────────┐
        │   USER QUERY    │ ◄── [INPUT]
        │   "Analyze..."  │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  COMPLEXITY     │
        │  ASSESSMENT     │
        │  Score: 0.87    │
        └─┬──────┬───────┬┘
          │      │       │
  ┌───────▼─┐  ┌▼──────┐│
  │ CGRAG   │  │ WEB   ││
  │ SEARCH  │  │SEARCH ││
  │ 8 docs  │  │ 5 src ││
  └───┬─────┘  └┬──────┘│
      │         │       │
      └─────┬───┘       │
            │           │
       ┌────▼───────────▼──┐
       │  Q2_FAST_1 [8080] │ ◄── [EXTRACTING]
       │  Token: 2341/16k  │     ████░░░░░
       └────────┬──────────┘
                │
       ┌────────▼──────────┐
       │  Q2_FAST_2 [8081] │ ◄── [EXTRACTING]
       │  Token: 1876/16k  │     ███░░░░░░
       └────────┬──────────┘
                │
           ┌────▼─────┐
           │  Q3_SYNTH│ ◄── [SYNTHESIZING]
           │  [8082]  │     ██████░░░░
           └────┬─────┘
                │
           ┌────▼─────┐
           │  Q4_DEEP │ ◄── [ANALYZING]
           │  [8083]  │     ████████░░
           └────┬─────┘
                │
        ┌───────▼───────┐
        │   RESPONSE    │ ◄── [COMPLETE]
        │   Tokens: 847 │     ██████████
        └───────────────┘
```

### Implementation Notes

**Terminal Aesthetic Implementation Options:**
1. **Custom CSS approach** (recommended for flexibility)
   - Build terminal styling with utility classes
   - Use CSS custom properties for theming
   - Box-drawing characters for borders (Unicode)
   - Monospace fonts throughout

2. **Framework-assisted** (optional)
   - Terminalize CSS as reference/starting point
   - Customize extensively to match Evangelion palette
   - Consider as plugin for "retro mode" toggle

3. **Hybrid approach**
   - Core UI in custom CSS
   - Optional "classic terminal mode" using framework
   - User-toggleable aesthetic modes

**Key Point:** The terminal aesthetic is **central to the design**, but implementation flexibility is preserved. The critical elements are:
- Monospace fonts
- High contrast dark theme
- Box-drawing characters for structure
- Dense information layout
- Color-coded status indicators

---

## 5. Model Orchestration System

### Model Configuration

**DeepSeek R1 0528 Qwen3 8B** in multiple quantization levels:

| Model ID | Port | Quantization | Context | VRAM | Threads | Use Case |
|----------|------|--------------|---------|------|---------|----------|
| Q2_FAST_1 | 8080 | Q2_K | 16k | ~3GB | 6 | Fast extraction |
| Q2_FAST_2 | 8081 | Q2_K | 16k | ~3GB | 6 | Parallel queries |
| Q3_SYNTH | 8082 | Q3_K_M | 24k | ~7GB | 8 | Synthesis |
| Q4_DEEP | 8083 | Q4_K_M | 32k | ~10GB | 10 | Complex analysis |

### Server Launch Script

```bash
#!/bin/bash
set -euo pipefail

MODEL_DIR="/path/to/models"
MODEL_NAME="DeepSeek-R1-0528-Qwen3-8B"
LOG_DIR="/var/log/llama-servers"
mkdir -p "$LOG_DIR"

# Q2 instance 1 - Fast extraction
nohup llama-server -m "${MODEL_DIR}/${MODEL_NAME}-Q2_K.gguf" \
  -c 16384 -ngl 99 --host 0.0.0.0 --port 8080 -n -1 --threads 6 \
  > "$LOG_DIR/q2_8080.log" 2>&1 &

# Q2 instance 2 - Parallel processing
nohup llama-server -m "${MODEL_DIR}/${MODEL_NAME}-Q2_K.gguf" \
  -c 16384 -ngl 99 --host 0.0.0.0 --port 8081 -n -1 --threads 6 \
  > "$LOG_DIR/q2_8081.log" 2>&1 &

# Q3 instance - Synthesis
nohup llama-server -m "${MODEL_DIR}/${MODEL_NAME}-Q3_K_M.gguf" \
  -c 24576 -ngl 99 --host 0.0.0.0 --port 8082 -n -1 --threads 8 \
  > "$LOG_DIR/q3_8082.log" 2>&1 &

# Q4 instance - Deep analysis
nohup llama-server -m "${MODEL_DIR}/${MODEL_NAME}-Q4_K_M.gguf" \
  -c 32768 -ngl 99 --host 0.0.0.0 --port 8083 -n -1 --threads 10 \
  > "$LOG_DIR/q4_8083.log" 2>&1 &

echo "All models started. Logs in $LOG_DIR"
```

**Production Note:** Use systemd or supervisord for production deployments.

### Query Routing Logic

#### Complexity Assessment

```python
def assess_complexity(query: str, cgrag_context: dict) -> str:
    """
    Determine query complexity based on multiple factors.
    Returns: "simple" | "moderate" | "complex"
    """
    # Pattern matching
    simple_patterns = ["what is", "define", "explain", "who is"]
    complex_patterns = ["analyze", "design", "architect", "compare multiple", "synthesize"]
    
    # Context factors
    num_files = len(cgrag_context.get("files", []))
    has_conflicts = cgrag_context.get("conflicting_sources", False)
    token_budget = cgrag_context.get("estimated_tokens", 0)
    
    # Complexity indicators
    is_simple = any(p in query.lower() for p in simple_patterns)
    is_complex = any(p in query.lower() for p in complex_patterns)
    
    # Decision logic
    if is_complex or num_files > 10 or has_conflicts or token_budget > 20000:
        return "complex"
    elif is_simple and num_files < 3 and token_budget < 5000:
        return "simple"
    else:
        return "moderate"
```

#### Routing Tiers

**SIMPLE → Q2_FAST (8080/8081)**
- Direct fact lookup
- Single-file explanations
- Basic summarization
- Response time: <2 seconds
- Load balanced between Q2 instances

**MODERATE → Q3_SYNTH (8082)**
- Multi-file synthesis
- Refactoring tasks
- Comparing 2-3 approaches
- Response time: 3-5 seconds

**COMPLEX → Q4_DEEP (8083)**
- Architecture analysis
- Multi-source reasoning
- Strategic planning
- Response time: 5-15 seconds

### Multi-Model Collaboration

#### Collaborative Processing Pipeline

```python
class CollaborativeOrchestrator:
    """Orchestrates multi-model collaboration for complex queries"""
    
    async def process_complex_query(self, query: str, context: dict):
        """
        1. Decompose query into subtasks
        2. Parallel extraction with Q2 instances
        3. Synthesis with Q3
        4. Optional deep analysis with Q4
        """
        # 1. DECOMPOSITION
        subtasks = self.decompose_query(query)
        
        # 2. PARALLEL EXTRACTION (Q2 instances)
        q2_results = await asyncio.gather(*[
            self.call_model(f"q2_fast_{i%2+1}", task, context)
            for i, task in enumerate(subtasks)
        ])
        
        # Emit telemetry
        self.emit_event("extraction_complete", {
            "subtasks": len(subtasks),
            "results": q2_results
        })
        
        # 3. SYNTHESIS (Q3 instance)
        synthesis_prompt = self.create_synthesis_prompt(q2_results)
        synthesis = await self.call_model("q3_synth", synthesis_prompt, context)
        
        self.emit_event("synthesis_complete", {"synthesis": synthesis})
        
        # 4. DEEP ANALYSIS (Q4 - conditional)
        if self.needs_deep_reasoning(synthesis):
            final = await self.call_model("q4_deep", synthesis, context)
            self.emit_event("analysis_complete", {"final": final})
            return final
        
        return synthesis
    
    def decompose_query(self, query: str) -> list[str]:
        """Break complex query into manageable subtasks"""
        # Simple heuristic: split on "and", "also", "then"
        # More sophisticated: use Q2 to decompose
        pass
    
    def needs_deep_reasoning(self, synthesis: str) -> bool:
        """Determine if synthesis requires deep analysis"""
        # Check for uncertainty markers, conflicting info, etc.
        pass
```

#### Inter-Model Communication

- **Shared conversation history** across model switches
- **Context preservation** during handoffs
- **Attribution tracking** - which model provided which insight
- **Metadata passing** - confidence scores, source citations

---

## 6. CGRAG Implementation

### Overview

Contextually-Guided Retrieval Augmented Generation (CGRAG) efficiently selects relevant artifacts from local repositories and web searches before sending context to the LLM.

### Key Components

1. **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2` for speed)
2. **Vector DB**: FAISS with IndexHNSWFlat for <100k documents
3. **Scoring**: Cosine similarity + recency + artifact type boost
4. **Caching**: Redis for embedded queries and results

### Ingestion Pipeline

```python
# 1. Document Discovery
def scan_repository(root_path: str) -> list[Document]:
    """Recursively scan directory for files"""
    documents = []
    for path in Path(root_path).rglob("*"):
        if path.is_file() and not should_ignore(path):
            doc = Document(
                path=str(path),
                content=path.read_text(),
                language=detect_language(path),
                modified=path.stat().st_mtime
            )
            documents.append(doc)
    return documents

# 2. Chunking
def chunk_document(doc: Document, chunk_size=512, overlap=128) -> list[Chunk]:
    """Split document into overlapping chunks"""
    tokens = tokenize(doc.content)
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk_tokens = tokens[i:i + chunk_size]
        chunks.append(Chunk(
            doc_id=doc.id,
            text=detokenize(chunk_tokens),
            start=i,
            end=i + len(chunk_tokens)
        ))
    return chunks

# 3. Embedding
def embed_chunks(chunks: list[Chunk]) -> np.ndarray:
    """Generate embeddings for chunks"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

# 4. Index Building
def build_index(embeddings: np.ndarray) -> faiss.Index:
    """Build FAISS index"""
    dimension = embeddings.shape[1]
    index = faiss.IndexHNSWFlat(dimension, 32)  # 32 neighbors
    index.add(embeddings)
    return index
```

### Retrieval Workflow

```python
class CGRAGRetriever:
    def __init__(self, index: faiss.Index, chunks: list[Chunk], 
                 cosine_cutoff=0.3, max_artifacts=20):
        self.index = index
        self.chunks = chunks
        self.cosine_cutoff = cosine_cutoff
        self.max_artifacts = max_artifacts
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def retrieve(self, query: str, token_budget: int) -> dict:
        """Retrieve relevant artifacts for query"""
        # 1. Embed query
        query_embedding = self.embedder.encode([query])[0]
        
        # 2. Search FAISS (k = max_artifacts * 5 for filtering)
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1),
            self.max_artifacts * 5
        )
        
        # 3. Convert distances to cosine similarity
        scores = 1 / (1 + distances[0])  # Convert L2 to similarity
        
        # 4. Filter by cutoff and score
        candidates = []
        for idx, score in zip(indices[0], scores):
            if score >= self.cosine_cutoff:
                chunk = self.chunks[idx]
                candidates.append({
                    "chunk": chunk,
                    "score": score,
                    "recency": self._recency_score(chunk),
                    "type_boost": self._type_boost(chunk)
                })
        
        # 5. Rank by combined score
        candidates.sort(
            key=lambda x: x["score"] * 0.7 + x["recency"] * 0.2 + x["type_boost"] * 0.1,
            reverse=True
        )
        
        # 6. Select top artifacts within token budget
        selected = []
        tokens_used = 0
        for candidate in candidates[:self.max_artifacts]:
            chunk_tokens = count_tokens(candidate["chunk"].text)
            if tokens_used + chunk_tokens <= token_budget:
                selected.append(candidate)
                tokens_used += chunk_tokens
        
        # 7. Return with telemetry
        return {
            "artifacts": selected,
            "tokens_used": tokens_used,
            "candidates_considered": len(candidates),
            "cutoff_applied": self.cosine_cutoff,
            "retrieval_trace": self._build_trace(query, candidates, selected)
        }
    
    def _recency_score(self, chunk: Chunk) -> float:
        """Score based on file modification time"""
        age_days = (time.time() - chunk.modified) / 86400
        return 1 / (1 + age_days / 30)  # Decay over 30 days
    
    def _type_boost(self, chunk: Chunk) -> float:
        """Boost certain file types"""
        boosts = {
            "python": 1.2,
            "markdown": 1.1,
            "typescript": 1.2,
            "config": 0.9
        }
        return boosts.get(chunk.language, 1.0)
    
    def _build_trace(self, query, candidates, selected):
        """Build retrieval trace for telemetry"""
        return {
            "query": query,
            "candidates": len(candidates),
            "selected": len(selected),
            "top_scores": [c["score"] for c in candidates[:10]],
            "artifacts": [
                {"path": c["chunk"].doc_path, "score": c["score"]}
                for c in selected
            ]
        }
```

### Configuration Tunables

```python
# Retrieval parameters
ARTIFACT_COSINE_CUTOFF = 0.3        # Lower = more permissive
ARTIFACT_COSINE_CGRAG_CUTOFF = 0.5  # For final CGRAG assembly
MAX_ARTIFACTS = 20                   # Hard cap
CONTEXT_TOKEN_BUDGET = 12000         # Reserve for context

# Scoring weights
COSINE_WEIGHT = 0.7
RECENCY_WEIGHT = 0.2
TYPE_BOOST_WEIGHT = 0.1

# Cache configuration
CACHE_TTL = 3600  # 1 hour for query embeddings
```

### Cache Strategy

```python
async def retrieve_with_cache(query: str, token_budget: int) -> dict:
    """Retrieve artifacts with Redis caching"""
    cache_key = f"cgrag:{hash(query)}:{token_budget}"
    
    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        emit_metric("cgrag.cache.hit")
        return json.loads(cached)
    
    # Cache miss - retrieve
    emit_metric("cgrag.cache.miss")
    result = retriever.retrieve(query, token_budget)
    
    # Cache result
    await redis.setex(
        cache_key,
        CACHE_TTL,
        json.dumps(result, default=str)
    )
    
    return result
```

---

## 7. Web Search Integration

### SearXNG Configuration

**Self-hosted instance** at `http://localhost:8888` with:
- Engines: Google, DuckDuckGo, Brave
- JSON API enabled
- Privacy-focused (no tracking)
- Rate limiting configured

### Integration Workflow

```python
class WebSearchIntegrator:
    def __init__(self, searxng_url: str):
        self.searxng_url = searxng_url
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Perform web search via SearXNG"""
        try:
            response = await self.client.get(
                f"{self.searxng_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "engines": "google,duckduckgo,brave",
                    "limit": max_results
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            # Extract and parse results
            parsed_results = []
            for result in results:
                parsed = await self._parse_result(result)
                if parsed:
                    parsed_results.append(parsed)
            
            return parsed_results
        
        except Exception as e:
            emit_error("web_search.error", error=str(e))
            return []
    
    async def _parse_result(self, result: dict) -> dict:
        """Parse and extract content from search result"""
        url = result.get("url")
        title = result.get("title")
        snippet = result.get("content", "")
        
        # Fetch full content for top results
        try:
            content = await self._fetch_content(url)
            extracted = self._extract_text(content)
            
            return {
                "url": url,
                "title": title,
                "snippet": snippet,
                "content": extracted[:2000],  # Limit length
                "source": "web_search"
            }
        except Exception:
            # Fallback to snippet
            return {
                "url": url,
                "title": title,
                "snippet": snippet,
                "content": snippet,
                "source": "web_search"
            }
    
    async def _fetch_content(self, url: str) -> str:
        """Fetch webpage content"""
        response = await self.client.get(url, follow_redirects=True)
        return response.text
    
    def _extract_text(self, html: str) -> str:
        """Extract main text from HTML using Trafilatura"""
        import trafilatura
        extracted = trafilatura.extract(html)
        return extracted or ""
```

### CGRAG Filtering of Web Results

```python
async def search_and_filter(query: str, cgrag_retriever: CGRAGRetriever) -> list[dict]:
    """Search web and filter results through CGRAG"""
    # 1. Perform web search
    web_results = await web_search.search(query)
    
    # 2. Embed web results
    web_embeddings = embedder.encode([r["content"] for r in web_results])
    
    # 3. Score against query
    query_embedding = embedder.encode([query])[0]
    scores = cosine_similarity([query_embedding], web_embeddings)[0]
    
    # 4. Filter by threshold
    filtered = [
        {**result, "score": score}
        for result, score in zip(web_results, scores)
        if score >= 0.3
    ]
    
    # 5. Rank and return top results
    filtered.sort(key=lambda x: x["score"], reverse=True)
    return filtered[:5]
```

---

## 8. Frontend Architecture

### Technology Stack

- **Framework**: React 19 with TypeScript
- **Build**: Vite 6 for fast HMR
- **State**: Zustand for client state, TanStack Query for server state
- **Styling**: Tailwind CSS 4 + custom CSS for terminal aesthetics
- **Real-time**: Native WebSocket API
- **Visualizations**: Chart.js 4 (charts), React Flow (pipeline), D3.js (custom)
- **Animations**: Framer Motion for declarative animations

### Component Architecture

```
src/
├── components/
│   ├── QueryInput/          # Terminal-style input
│   │   ├── QueryInput.tsx
│   │   ├── CommandHistory.tsx
│   │   └── AutoComplete.tsx
│   ├── ModelStatus/         # Status dashboard
│   │   ├── ModelCard.tsx
│   │   ├── VRAMBar.tsx
│   │   └── StatusBadge.tsx
│   ├── ProcessingPipeline/  # Pipeline visualization
│   │   ├── PipelineGraph.tsx
│   │   ├── NodeRenderer.tsx
│   │   └── EdgeRenderer.tsx
│   ├── ContextViewer/       # Context artifacts
│   │   ├── ArtifactList.tsx
│   │   ├── ArtifactCard.tsx
│   │   └── SourceViewer.tsx
│   ├── ResponseDisplay/     # Streaming response
│   │   ├── TokenStream.tsx
│   │   ├── Attribution.tsx
│   │   └── ExportButton.tsx
│   └── MetricsPanel/        # Real-time metrics
│       ├── VRAMChart.tsx
│       ├── LatencyChart.tsx
│       └── CacheHitGauge.tsx
├── hooks/
│   ├── useWebSocket.ts      # WebSocket connection
│   ├── useModelStatus.ts    # Model state
│   ├── useQuerySubmit.ts    # Query submission
│   └── useMetrics.ts        # Metrics collection
├── stores/
│   ├── appStore.ts          # Global app state
│   ├── modelStore.ts        # Model state
│   └── queryStore.ts        # Query history
├── lib/
│   ├── api.ts               # API client
│   ├── websocket.ts         # WS client
│   └── types.ts             # TypeScript types
└── styles/
    ├── terminal.css         # Terminal aesthetics
    ├── animations.css       # Animation definitions
    └── components.css       # Component styles
```

### Key Components

#### QueryInput Component

```typescript
interface QueryInputProps {
  onSubmit: (query: string, options: QueryOptions) => void;
  disabled: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({ onSubmit, disabled }) => {
  const [query, setQuery] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  const handleSubmit = () => {
    if (!query.trim()) return;
    
    onSubmit(query, {
      enableWebSearch: true,
      enableCGRAG: true,
      mode: "auto"
    });
    
    setHistory([...history, query]);
    setQuery("");
    setHistoryIndex(-1);
  };
  
  const handleKeyDown = (e: KeyboardEvent) => {
    // Arrow up/down for history
    if (e.key === "ArrowUp" && history.length > 0) {
      const newIndex = Math.min(historyIndex + 1, history.length - 1);
      setHistoryIndex(newIndex);
      setQuery(history[history.length - 1 - newIndex]);
    } else if (e.key === "ArrowDown") {
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setQuery(history[history.length - 1 - newIndex]);
      } else {
        setHistoryIndex(-1);
        setQuery("");
      }
    }
    // Enter to submit (Shift+Enter for newline)
    else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  return (
    <div className="query-input terminal-panel">
      <div className="terminal-header">
        <span className="phosphor-green">$</span> QUERY TERMINAL
      </div>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="Enter query... (Shift+Enter for newline)"
        className="terminal-textarea"
      />
      <div className="terminal-actions">
        <button onClick={handleSubmit} disabled={disabled || !query.trim()}>
          EXECUTE
        </button>
      </div>
    </div>
  );
};
```

#### ModelStatus Component

```typescript
interface ModelStatusProps {
  models: ModelInfo[];
}

export const ModelStatus: React.FC<ModelStatusProps> = ({ models }) => {
  return (
    <div className="model-status terminal-panel">
      <div className="panel-header eva-style">
        ▓▓▓▓ NEURAL SUBSTRATE STATUS ▓▓▓▓
      </div>
      
      {models.map(model => (
        <motion.div
          key={model.id}
          className="model-card"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="model-header">
            <span className="model-name">{model.name}</span>
            <span className="model-port">[{model.port}]</span>
          </div>
          
          <VRAMBar
            used={model.vram_used}
            total={model.vram_total}
            status={model.status}
          />
          
          <div className="model-stats">
            <span className="stat-label">Status:</span>
            <StatusBadge status={model.status} />
            <span className="stat-value">
              {model.vram_used.toFixed(1)}/{model.vram_total.toFixed(1)}GB
            </span>
          </div>
        </motion.div>
      ))}
      
      <div className="panel-footer">
        <div className="total-vram">
          TOTAL VRAM: {getTotalVRAM(models)}
        </div>
        <div className="cache-rate">
          CACHE HIT RATE: {getCacheHitRate()}%
        </div>
      </div>
    </div>
  );
};
```

### WebSocket Integration

```typescript
// hooks/useWebSocket.ts
export const useWebSocket = (url: string) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const eventHandlers = useRef<Map<string, Set<Function>>>(new Map());
  
  useEffect(() => {
    const socket = new WebSocket(url);
    
    socket.onopen = () => {
      setConnected(true);
      // Subscribe to channels
      socket.send(JSON.stringify({
        type: "subscribe",
        channels: ["model_status", "query_progress", "metrics"]
      }));
    };
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const handlers = eventHandlers.current.get(data.type);
      if (handlers) {
        handlers.forEach(handler => handler(data.data));
      }
    };
    
    socket.onclose = () => {
      setConnected(false);
      // Reconnect after 2s
      setTimeout(() => {
        setWs(null);
      }, 2000);
    };
    
    setWs(socket);
    
    return () => {
      socket.close();
    };
  }, [url]);
  
  const on = (event: string, handler: Function) => {
    if (!eventHandlers.current.has(event)) {
      eventHandlers.current.set(event, new Set());
    }
    eventHandlers.current.get(event)!.add(handler);
    
    return () => {
      eventHandlers.current.get(event)?.delete(handler);
    };
  };
  
  const emit = (event: string, data: any) => {
    if (ws && connected) {
      ws.send(JSON.stringify({ type: event, data }));
    }
  };
  
  return { connected, on, emit };
};
```

---

## 9. Real-Time Visualizations

### Chart.js Configuration

```typescript
// Token usage over time (line chart)
const tokenUsageChartConfig: ChartConfiguration = {
  type: 'line',
  data: {
    labels: [], // Timestamps
    datasets: [
      {
        label: 'Tokens/sec',
        data: [],
        borderColor: '#00ff41',
        backgroundColor: 'rgba(0, 255, 65, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: '#1a3a1a' },
        ticks: { color: '#00ff41' }
      },
      x: {
        grid: { color: '#1a3a1a' },
        ticks: { color: '#00ff41' }
      }
    },
    plugins: {
      legend: { display: false }
    },
    animation: {
      duration: 750,
      easing: 'easeInOutQuart'
    }
  }
};

// VRAM usage (stacked bar chart)
const vramChartConfig: ChartConfiguration = {
  type: 'bar',
  data: {
    labels: ['Q2_1', 'Q2_2', 'Q3', 'Q4'],
    datasets: [
      {
        label: 'Used',
        data: [],
        backgroundColor: '#00ff41'
      },
      {
        label: 'Available',
        data: [],
        backgroundColor: '#1a3a1a'
      }
    ]
  },
  options: {
    indexAxis: 'y',
    scales: {
      x: {
        stacked: true,
        max: 100,
        ticks: { callback: (value) => `${value}%` }
      },
      y: { stacked: true }
    }
  }
};
```

### React Flow Pipeline

```typescript
// Processing pipeline visualization
const pipelineNodes: Node[] = [
  {
    id: 'query',
    type: 'input',
    data: { label: 'QUERY INPUT' },
    position: { x: 250, y: 0 }
  },
  {
    id: 'routing',
    data: { label: 'ROUTING ANALYSIS' },
    position: { x: 250, y: 100 }
  },
  {
    id: 'cgrag',
    data: { label: 'CGRAG\n8 artifacts' },
    position: { x: 100, y: 200 }
  },
  {
    id: 'web',
    data: { label: 'WEB SEARCH\n5 results' },
    position: { x: 400, y: 200 }
  },
  {
    id: 'q2_1',
    data: { label: 'Q2_FAST_1', status: 'active' },
    position: { x: 150, y: 300 }
  },
  {
    id: 'q3',
    data: { label: 'Q3_SYNTH', status: 'processing' },
    position: { x: 250, y: 400 }
  },
  {
    id: 'response',
    type: 'output',
    data: { label: 'RESPONSE' },
    position: { x: 250, y: 500 }
  }
];

const pipelineEdges: Edge[] = [
  { id: 'e1', source: 'query', target: 'routing', animated: true },
  { id: 'e2', source: 'routing', target: 'cgrag' },
  { id: 'e3', source: 'routing', target: 'web' },
  { id: 'e4', source: 'cgrag', target: 'q2_1' },
  { id: 'e5', source: 'q2_1', target: 'q3', animated: true },
  { id: 'e6', source: 'q3', target: 'response', animated: true }
];

// Custom node renderer
const CustomNode = ({ data }: NodeProps) => {
  const statusColor = {
    active: '#00ff41',
    processing: '#00ffff',
    idle: '#ff9500',
    error: '#ff0000'
  }[data.status || 'idle'];
  
  return (
    <div
      className="pipeline-node"
      style={{ borderColor: statusColor }}
    >
      <div className="node-label">{data.label}</div>
      {data.status && (
        <div className="node-status" style={{ color: statusColor }}>
          ● {data.status.toUpperCase()}
        </div>
      )}
    </div>
  );
};
```

### Animation Performance

```css
/* Optimize animations for 60fps */
.animate {
  will-change: transform, opacity;
  transform: translateZ(0); /* Force GPU acceleration */
}

/* Pulse animation for active states */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.status-active {
  animation: pulse 2s ease-in-out infinite;
}

/* Scanning line effect */
@keyframes scan {
  0% { transform: translateY(-100%); opacity: 0; }
  5% { opacity: 0.4; }
  50% { opacity: 0.2; }
  100% { transform: translateY(100%); opacity: 0; }
}

.scanline {
  animation: scan 3s linear infinite;
  pointer-events: none;
}

/* Token streaming typing effect */
@keyframes typing {
  from { width: 0; }
  to { width: 100%; }
}

.token-stream {
  overflow: hidden;
  white-space: nowrap;
  animation: typing 0.05s steps(1) forwards;
}
```

---

## 10. API Design

### REST Endpoints

#### POST /api/query

Submit a query for processing.

```typescript
// Request
interface QueryRequest {
  query: string;
  mode?: "auto" | "simple" | "moderate" | "complex";
  enable_web_search?: boolean;
  enable_cgrag?: boolean;
  max_context_tokens?: number;
  stream?: boolean;
}

// Response
interface QueryResponse {
  query_id: string;
  routed_to: string[];  // Model IDs used
  response: string;
  metadata: {
    models_used: string[];
    tokens_used: number;
    context_tokens: number;
    cgrag_artifacts: number;
    web_results: number;
    processing_time_ms: number;
    cache_hit: boolean;
    retrieval_trace: RetrievalTrace;
  };
}
```

#### GET /api/models/status

Get status of all model instances.

```typescript
interface ModelStatus {
  models: Array<{
    id: string;
    port: number;
    status: "active" | "idle" | "processing" | "error";
    current_load: number;
    context_size: number;
    context_used: number;
    vram_usage_gb: number;
    vram_total_gb: number;
    requests_per_second: number;
    uptime_seconds: number;
  }>;
  total_vram_gb: number;
  total_vram_used_gb: number;
  cache_hit_rate: number;
  active_queries: number;
}
```

#### POST /api/models/swap

Swap a model instance (hot reload).

```typescript
interface ModelSwapRequest {
  model_id: string;
  new_model_path: string;
  preserve_context?: boolean;
}

interface ModelSwapResponse {
  success: boolean;
  message: string;
  model_id: string;
  new_model: string;
  restart_time_ms: number;
}
```

#### GET /api/cgrag/artifacts

List indexed artifacts.

```typescript
interface ArtifactsResponse {
  artifacts: Array<{
    id: string;
    path: string;
    language: string;
    chunks: number;
    last_indexed: string;
  }>;
  total_documents: number;
  total_chunks: number;
  index_size_mb: number;
}
```

### WebSocket Events

#### Client → Server

```typescript
// Subscribe to channels
{
  type: "subscribe",
  channels: string[]  // ["model_status", "query_progress", "metrics"]
}

// Unsubscribe
{
  type: "unsubscribe",
  channels: string[]
}
```

#### Server → Client

```typescript
// Model status update
{
  type: "model_status_update",
  data: {
    model_id: string,
    status: string,
    vram_used: number,
    current_load: number
  }
}

// Token streaming
{
  type: "token_stream",
  data: {
    query_id: string,
    token: string,
    model: string,
    cumulative_tokens: number
  }
}

// Query progress
{
  type: "query_progress",
  data: {
    query_id: string,
    stage: "routing" | "extraction" | "synthesis" | "analysis" | "complete",
    progress: number,  // 0-100
    message: string
  }
}

// Metrics update
{
  type: "metrics_update",
  data: {
    timestamp: number,
    vram_usage: number,
    active_requests: number,
    tokens_per_second: number,
    cache_hit_rate: number
  }
}

// Retrieval trace
{
  type: "retrieval_trace",
  data: {
    query_id: string,
    artifacts_considered: number,
    artifacts_selected: number,
    scores: number[],
    execution_time_ms: number
  }
}
```

---

## 11. Configuration System

### Environment Variables

```bash
# .env.example

# Server
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# Models
MODELS_DIR=/path/to/models
MODEL_FAMILY=DeepSeek-R1-0528-Qwen3-8B

# CGRAG
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DB=faiss
ARTIFACT_COSINE_CUTOFF=0.3
ARTIFACT_COSINE_CGRAG_CUTOFF=0.5
MAX_ARTIFACTS=20

# Search
SEARXNG_URL=http://localhost:8888
SEARXNG_ENGINES=google,duckduckgo,brave
SEARXNG_MAX_RESULTS=10

# Redis
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_CACHE_TTL=3600

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### TOML Configuration

```toml
# config.toml

[orchestrator]
default_mode = "auto"
enable_cgrag = true
enable_web_search = true
max_concurrent_queries = 10
stream_tokens = true
token_streaming_delay_ms = 20

[models.q2_fast_1]
path = "/models/DeepSeek-R1-0528-Qwen3-8B-Q2_K.gguf"
port = 8080
context_size = 16384
ngl = 99
threads = 6
complexity_level = "simple"
max_load = 0.8

[models.q2_fast_2]
path = "/models/DeepSeek-R1-0528-Qwen3-8B-Q2_K.gguf"
port = 8081
context_size = 16384
ngl = 99
threads = 6
complexity_level = "simple"
max_load = 0.8

[models.q3_synth]
path = "/models/DeepSeek-R1-0528-Qwen3-8B-Q3_K_M.gguf"
port = 8082
context_size = 24576
ngl = 99
threads = 8
complexity_level = "moderate"
max_load = 0.9

[models.q4_deep]
path = "/models/DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf"
port = 8083
context_size = 32768
ngl = 99
threads = 10
complexity_level = "complex"
max_load = 0.95

[cgrag]
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
cosine_cutoff = 0.3
cosine_cgrag_cutoff = 0.5
max_artifacts = 20
vector_db = "faiss"
enable_cache = true
chunk_size = 512
chunk_overlap = 128

[cgrag.scoring_weights]
cosine = 0.7
recency = 0.2
type_boost = 0.1

[web_search]
engine = "searxng"
api_url = "http://localhost:8888"
max_results = 10
timeout = 5.0
engines = ["google", "duckduckgo", "brave"]
enable_content_extraction = true

[ui]
theme = "terminal"
enable_animations = true
fps_target = 60
show_token_stream = true
show_metrics = true
show_retrieval_trace = true
performance_mode = false  # Disable heavy animations
```

---

## 12. Implementation Roadmap

### Phase A: Core Backend (Week 1-2)

**Goal:** Working API with model orchestration

**Tasks:**
- [ ] Set up FastAPI project structure
- [ ] Create model configuration loader (TOML)
- [ ] Implement llama-server process management
- [ ] Build query routing logic with complexity assessment
- [ ] Create REST endpoints (`/api/query`, `/api/models/status`)
- [ ] Add health checking for model instances
- [ ] Implement logging and error handling
- [ ] Write unit tests for routing logic

**Deliverable:** API that routes queries to appropriate model tiers

**Success Criteria:**
- All models start reliably
- Query routing works correctly
- Basic error handling in place

---

### Phase B: CGRAG Core (Week 2-3)

**Goal:** Functional retrieval system with telemetry

**Tasks:**
- [ ] Integrate sentence-transformers
- [ ] Set up FAISS vector database
- [ ] Implement document indexing pipeline
- [ ] Build relevancy scoring with cosine similarity
- [ ] Create context assembly with token budgeting
- [ ] Add Redis caching layer
- [ ] Implement artifact filtering with cutoff thresholds
- [ ] Build retrieval trace for telemetry
- [ ] Test with sample code repository

**Deliverable:** CGRAG retrieves relevant context efficiently

**Success Criteria:**
- Cache hit rate >60%
- Retrieval latency <100ms (cached)
- Accurate artifact selection

---

### Phase C: Web Search Integration (Week 3-4)

**Goal:** SearXNG integration with result filtering

**Tasks:**
- [ ] Create SearXNG HTTP client (httpx)
- [ ] Implement search result parsing
- [ ] Add HTML content extraction (Trafilatura)
- [ ] Filter search results through CGRAG
- [ ] Build result synthesis logic
- [ ] Handle conflicting information
- [ ] Add rate limiting and caching
- [ ] Test with various query types

**Deliverable:** Web search augments local knowledge

**Success Criteria:**
- Search completes in <5s
- Results are relevant
- Graceful handling of search failures

---

### Phase D: Multi-Model Collaboration (Week 4-5)

**Goal:** Models work together on complex queries

**Tasks:**
- [ ] Implement query decomposition
- [ ] Build parallel extraction system (Q2 instances)
- [ ] Create synthesis pipeline (Q3)
- [ ] Add conditional deep analysis (Q4)
- [ ] Implement context handoffs
- [ ] Build attribution tracking
- [ ] Create conversation history management
- [ ] Test collaborative workflows

**Deliverable:** Complex queries use multi-model pipeline

**Success Criteria:**
- Parallel extraction works correctly
- Attribution is accurate
- Performance gains measurable

---

### Phase E: WebSocket & Real-Time (Week 5-6)

**Goal:** Live updates and token streaming

**Tasks:**
- [ ] Set up WebSocket endpoint
- [ ] Implement event subscription system
- [ ] Add token streaming for responses
- [ ] Create metrics collection
- [ ] Build real-time model status updates
- [ ] Implement reconnection handling
- [ ] Add rate limiting for events
- [ ] Test with multiple concurrent connections

**Deliverable:** Real-time communication between backend and frontend

**Success Criteria:**
- WebSocket latency <50ms
- Reconnection works reliably
- No message loss

---

### Phase F: Frontend Foundation (Week 6-7)

**Goal:** Functional UI with basic interactions

**Tasks:**
- [ ] Initialize Vite + React + TypeScript project
- [ ] Set up Tailwind CSS
- [ ] Create component structure
- [ ] Implement WebSocket client
- [ ] Build query input component
- [ ] Create response display with streaming
- [ ] Add basic routing
- [ ] Set up Zustand for state management

**Deliverable:** UI can send queries and display responses

**Success Criteria:**
- Query submission works
- Token streaming displays correctly
- WebSocket connection stable

---

### Phase G: Visualizations (Week 7-8)

**Goal:** Rich, real-time data visualizations

**Tasks:**
- [ ] Integrate Chart.js
- [ ] Create VRAM usage bar chart
- [ ] Build token usage line chart
- [ ] Implement context window visualization
- [ ] Add model performance gauges
- [ ] Create processing pipeline flowchart (React Flow)
- [ ] Build metrics dashboard
- [ ] Optimize for 60fps

**Deliverable:** Live data visualizations

**Success Criteria:**
- Charts update in real-time
- Performance is 60fps
- Visualizations are informative

---

### Phase H: Terminal Aesthetics (Week 8-9)

**Goal:** Dense, terminal-inspired UI

**Tasks:**
- [ ] Apply terminal color scheme
- [ ] Create ASCII art headers
- [ ] Build dense grid layouts
- [ ] Add box-drawing characters for structure
- [ ] Implement smooth animations (Framer Motion)
- [ ] Create loading states and transitions
- [ ] Polish responsive design
- [ ] Add keyboard shortcuts

**Deliverable:** Polished terminal aesthetic

**Success Criteria:**
- UI matches design language
- Animations are smooth
- Keyboard navigation works

---

### Phase I: Advanced Features (Week 9-10)

**Goal:** Production-ready features

**Tasks:**
- [ ] Build model swap UI
- [ ] Create query history browser
- [ ] Add conversation export/import
- [ ] Implement configuration editor
- [ ] Build prompt template system
- [ ] Add command palette (Cmd+K)
- [ ] Implement user preferences
- [ ] Create documentation

**Deliverable:** Feature-complete application

**Success Criteria:**
- All features functional
- User preferences persist
- Documentation complete

---

### Phase J: Testing & QA (Week 10-11)

**Goal:** Comprehensive testing

**Tasks:**
- [ ] Write unit tests (Vitest)
- [ ] Create E2E tests (Playwright)
- [ ] Add integration tests
- [ ] Performance testing
- [ ] Load testing
- [ ] Security audit
- [ ] Accessibility testing
- [ ] Bug fixes

**Deliverable:** Tested, reliable system

**Success Criteria:**
- >80% code coverage
- All critical paths tested
- Performance targets met

---

### Phase K: Deployment (Week 11-12)

**Goal:** Production deployment

**Tasks:**
- [ ] Create Docker Compose setup
- [ ] Set up reverse proxy (Caddy)
- [ ] Implement monitoring (Prometheus/Grafana)
- [ ] Add error tracking (Sentry)
- [ ] Create backup procedures
- [ ] Set up automated updates
- [ ] Document deployment
- [ ] Create troubleshooting guide

**Deliverable:** Production-ready, monitored system

**Success Criteria:**
- System is deployed
- Monitoring is active
- Documentation is complete

---

## 13. Testing & Quality Assurance

### Unit Testing

**Backend (pytest)**
```python
# tests/test_routing.py
def test_complexity_assessment():
    """Test query complexity assessment"""
    assert assess_complexity("what is python?", {}) == "simple"
    assert assess_complexity("analyze the architecture", {}) == "complex"
    
def test_model_selection():
    """Test model tier selection"""
    router = QueryRouter()
    model = router.select_model("simple")
    assert model in ["q2_fast_1", "q2_fast_2"]
```

**Frontend (Vitest)**
```typescript
// tests/components/QueryInput.test.tsx
describe('QueryInput', () => {
  it('submits query on Enter', async () => {
    const onSubmit = vi.fn();
    render(<QueryInput onSubmit={onSubmit} disabled={false} />);
    
    const input = screen.getByPlaceholderText(/enter query/i);
    await userEvent.type(input, 'test query{Enter}');
    
    expect(onSubmit).toHaveBeenCalledWith('test query', expect.any(Object));
  });
});
```

### Integration Testing

```python
# tests/test_cgrag_integration.py
async def test_cgrag_end_to_end():
    """Test full CGRAG pipeline"""
    # Index sample documents
    indexer = CGRAGIndexer()
    await indexer.index_directory("./test_data")
    
    # Retrieve artifacts
    retriever = CGRAGRetriever(indexer.index, indexer.chunks)
    results = retriever.retrieve("python async", token_budget=5000)
    
    assert len(results["artifacts"]) > 0
    assert results["tokens_used"] <= 5000
```

### E2E Testing

```typescript
// e2e/query-flow.spec.ts
test('complete query flow', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Submit query
  await page.fill('[data-testid="query-input"]', 'explain async/await');
  await page.click('[data-testid="submit-button"]');
  
  // Wait for response
  await page.waitForSelector('[data-testid="response-display"]');
  
  // Verify response appeared
  const response = await page.textContent('[data-testid="response-display"]');
  expect(response).toBeTruthy();
  
  // Verify model status updated
  const modelStatus = await page.textContent('[data-testid="model-status"]');
  expect(modelStatus).toContain('ACTIVE');
});
```

### Performance Testing

```python
# tests/test_performance.py
async def test_query_latency():
    """Test query response times"""
    client = TestClient(app)
    
    start = time.time()
    response = await client.post("/api/query", json={
        "query": "simple fact lookup",
        "mode": "simple"
    })
    latency = time.time() - start
    
    assert response.status_code == 200
    assert latency < 2.0  # Simple queries <2s

async def test_concurrent_queries():
    """Test system under load"""
    tasks = [
        submit_query(f"query {i}")
        for i in range(50)
    ]
    results = await asyncio.gather(*tasks)
    
    success_rate = sum(1 for r in results if r.status_code == 200) / len(results)
    assert success_rate > 0.95  # >95% success rate
```

---

## 14. Performance Targets

### Response Time Targets

| Query Type | Target | Max Acceptable |
|------------|--------|----------------|
| Simple (Q2) | <2s | 3s |
| Moderate (Q3) | <5s | 8s |
| Complex (Q4) | <15s | 20s |
| CGRAG retrieval | <100ms | 200ms |
| Web search | <3s | 5s |

### Throughput Targets

- **Concurrent queries**: Support 10+ simultaneous queries
- **Tokens/second**: 50+ (per model instance)
- **Cache hit rate**: >70%
- **Model uptime**: >99.5%

### UI Performance

- **Frame rate**: 60fps for animations
- **Initial load**: <2s
- **Time to interactive**: <3s
- **WebSocket latency**: <50ms
- **Chart update rate**: 1-2 updates/second

### Resource Limits

- **Total VRAM**: 24GB recommended (23GB for models)
- **CPU cores**: 8+ recommended
- **RAM**: 32GB+ recommended
- **Disk**: 50GB+ for models and indexes

---

## 15. Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    volumes:
      - ./backend:/app
      - ./models:/models:ro
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - MODELS_DIR=/models
    depends_on:
      - redis

  frontend:
    build: ./frontend
    command: npm run dev -- --host
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  redis_data:
```

### Production Considerations

1. **Reverse Proxy** (Caddy)
```caddyfile
orchestrator.example.com {
    reverse_proxy /api/* backend:8000
    reverse_proxy /ws backend:8000
    reverse_proxy * frontend:5173
    
    encode gzip
    
    log {
        output file /var/log/caddy/access.log
    }
}
```

2. **Monitoring** (Prometheus + Grafana)
- Expose metrics at `/metrics`
- Track: query latency, model status, cache hit rate, errors
- Alert on: model downtime, high latency, low cache hit rate

3. **Logging**
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized logging (optional: ELK stack)

4. **Backups**
- FAISS indexes: daily backups
- Configuration files: version controlled
- Redis persistence: RDB snapshots

---

## Appendix A: Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- llama.cpp compiled with CUDA
- 24GB+ VRAM
- Redis server

### Setup

```bash
# Clone repository
git clone <repo>
cd multi-model-orchestrator

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your paths

# Frontend setup
cd ../frontend
npm install

# Start models (adjust paths in script)
./scripts/start_models.sh

# Start Redis
redis-server

# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend
cd frontend
npm run dev
```

### Access
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Appendix B: References

**Core Dependencies:**
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Model inference
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [sentence-transformers](https://www.sbert.net/) - Embeddings
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [React](https://react.dev/) - Frontend framework
- [Chart.js](https://www.chartjs.org/) - Charting library
- [React Flow](https://reactflow.dev/) - Node graphs

**Models:**
- [DeepSeek R1 Models](https://huggingface.co/unsloth) - Model downloads

---

**End of Specification**

This balanced specification preserves the terminal aesthetic as central to the design while providing flexibility in implementation. It includes enough detail for developers to start coding immediately while maintaining a clear roadmap and performance targets.

For implementation, start with Phase A and work sequentially through the roadmap. Each phase has clear deliverables and success criteria.
