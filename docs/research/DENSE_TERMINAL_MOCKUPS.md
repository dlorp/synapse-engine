# S.Y.N.A.P.S.E. ENGINE - Dense Terminal Mockups

**Document Status:** Production Design Phase
**Last Updated:** 2025-11-08
**Terminal Aesthetic:** NGE NERV / S.Y.N.A.P.S.E. ENGINE Phosphor Orange (#ff9500)

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Design Philosophy](#design-philosophy)
3. [HomePage - Enhanced](#homepage---enhanced)
4. [MetricsPage - Complete Redesign](#metricspage---complete-redesign)
5. [ModelManagementPage - Enhanced](#modelmanagementpage---enhanced)
6. [NEURAL SUBSTRATE DASHBOARD - New](#neural-substrate-dashboard---new)
7. [ASCII Art Library & Tools](#ascii-art-library--tools)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Code Snippets & Components](#code-snippets--components)

---

## Current State Assessment

### Existing Components ✅
- **Panel** - Terminal-styled border container with title, variants (default/accent/warning/error)
- **MetricDisplay** - Label + Value + Unit with status indicators and trend arrows
- **ProgressBar** - Horizontal progress with percentage, color variants
- **StatusIndicator** - Dot + Label status display
- **Button** - Terminal-styled interactive elements

### Current Pages

#### HomePage (Functional ✅)
- NEURAL SUBSTRATE ORCHESTRATOR header with 3 metrics (VRAM, QUERIES, CACHE)
- ModeSelector for query routing modes
- QueryInput for user queries
- ResponseDisplay for results
- Timer for query duration
- QuickActions for model control
- **Issues**: Only 3 metrics shown, limited visibility into orchestrator internals, no event feed

#### MetricsPage (Placeholder ⚠️)
- Generic metric placeholders with hardcoded zeros
- No real data visualization
- No routing metrics or tier-specific breakdowns
- No charts or sparklines
- **Issue**: Needs complete rebuild with dense layout and ASCII charts

#### ModelManagementPage (Functional ✅)
- Model registry scanning and discovery
- Tier assignment UI
- Server start/stop controls
- Real-time log viewer
- **Issues**: No mini-dashboards per model, no sparklines, missing performance visualization

### Missing Enhancements
- Figlet banners for major sections
- ASCII charts and sparklines
- Real-time event feed
- NEURAL SUBSTRATE ORCHESTRATOR internals dashboard
- Query pipeline visualization
- Tier-specific performance metrics
- Model performance sparklines

---

## Design Philosophy

### Dense Information Display (Bloomberg Terminal Style)

Every pixel serves a purpose. The layout prioritizes:

1. **Information Density** - 8+ metrics per panel
2. **Visual Hierarchy** - Important metrics first, detailed breakdowns below
3. **Real-time Updates** - Status indicators with pulsing animations
4. **Color Coding** - Green (active), Orange (warning), Red (error)
5. **ASCII Art** - Borders, charts, sparklines using block characters
6. **Functional Aesthetics** - Effects enhance usability, not distract

### Color Palette

```
PHOSPHOR ORANGE (PRIMARY):  #ff9500  ← S.Y.N.A.P.S.E. ENGINE brand color
CYAN (ACCENT):              #00ffff  ← Highlights, processing status
RED (ALERT):                #ff0000  ← Errors, critical warnings
BLACK (BACKGROUND):         #000000  ← Terminal background
DARK ORANGE (SECONDARY):    #cc7700  ← Inactive, secondary text
```

### ASCII Characters for Density

**Box Drawing:**
```
┌─ ┐  │  ├─ ┤  ┼  Single line boxes
╔═ ╗  ║  ╠═ ╣  ╬  Double line boxes
╒═ ╕  │  ╞═ ╡  ╪  Mixed style boxes
```

**Block Elements:**
```
█ ▓ ▒ ░  ─ ▀ ▄  (progress bars, charts)
● ○ ◉  ◆ ◇  ■ □  (status indicators)
→ ← ↑ ↓  ⇒ ⇐  (directional indicators)
✓ ✗ ⚠ ⚡  (state markers)
```

---

## HomePage - Enhanced

### Mockup: Dense Multi-Panel Layout

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ SYNAPSE ENGINES                                                            v5.0 ║
║   ███████  ██    ██  ██████   ███████ ██ ██████  ███████                     ║
║       ██   ██    ██ ██          ██    ██ ██         ██  ███ ENGINE            ║
║     ██     ██    ██ ██  ███      ██    ██ ██  ███   ██                        ║
║    ██      ██    ██ ██    ██     ██    ██ ██    ██  ██                        ║
║    █████████████████ ██████      ██    ██ ██████   ██                         ║
║                                                                                ║
║ NEURAL SUBSTRATE ORCHESTRATOR :: COMMAND INTERFACE                             ║
╚════════════════════════════════════════════════════════════════════════════════╝

┌─ SYSTEM STATUS ────────────────────────────────────────────────────────────┐
│ VRAM: 14.2/16.0 GB [████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 88%  │
│ VRAM: [████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    │
│ ACTIVE: 2/8 ● ● ○ ○ ○ ○ ○ ○  IDLE: 4  PROCESSING: 1  OFFLINE: 1             │
│ QUERIES: 1,247 (↑ 8.3% since 6h)  CACHE HIT: 78.9%  ↑ 2.4%                  │
│ TEMP: Q2: 58°C  Q3: 62°C  Q4: 71°C  │  LATENCY: avg 1.24s  p95: 3.81s       │
│ THROUGHPUT: 8.3 q/min  CACHE: 2.4 GB / 4.0 GB (60%)                          │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ NEURAL SUBSTRATE ORCHESTRATOR STATUS ─────────────────────────────────────────┐
│ MODE: ● STANDARD  ○ COUNCIL  ○ MODERATOR                                      │
│ ROUTING LOGIC: ✓ ACTIVE  │ CGRAG: ✓ ACTIVE (8.2GB vectors)                   │
│ WEB SEARCH: ✓ ENABLED  │ CONTEXT WINDOW: Smart Allocation Active             │
│                                                                                │
│ QUERY PIPELINE STATUS:                                                         │
│ ┌─ INPUT PROCESSING ────┬─ COMPLEXITY ASSESSMENT ────┬─ ROUTING ───────────┐ │
│ │ ✓ TOKENIZATION        │ Score: 4.8 (MODERATE)       │ → Q3_BALANCED    ✓  │ │
│ │ ✓ EMBEDDING           │ Pattern: Multi-part query    │ Confidence: 95%  │  │ │
│ │ ○ CONTEXT RETRIEVAL   │ Factors: [7 tokens][2 sep]  │ Alternatives: --  │  │ │
│ └───────────────────────┴──────────────────────────────┴──────────────────┘  │
│                                                                                │
│ TIER STATUS:                                                                   │
│ Q2_FAST:     ● IDLE (1.2GB / 3.0GB)  │ Temp: 58°C   │ ⏱ Last: 340ms       │
│ Q3_BALANCED: ● PROCESSING (2.8GB / 4.0GB)  │ Temp: 62°C   │ ⏱ Last: 1.2s    │
│ Q4_POWERFUL: ● IDLE (2.2GB / 8.0GB)  │ Temp: 71°C   │ ⏱ Last: 4.3s       │
│                                                                                │
│ CONTEXT ALLOCATION:                                                            │
│ User Query: 180 tokens  │ CGRAG Artifacts: 1,240 tokens  │ System: 120 tokens │
│ Available: 2,560 tokens  │ Total Utilization: 65.6%  [████████████░░░░░░]  │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ LIVE EVENT FEED (LAST 8 EVENTS) ───────────────────────────────────────────────┐
│ [23:58:42] ◉ Q3_BALANCED started processing query (complexity: 4.8)             │
│ [23:58:39] ✓ CGRAG retrieved 12 artifacts (1,240 tokens)                        │
│ [23:58:35] ● Q2_FAST completed response (340ms) - cache: MISS                  │
│ [23:58:32] ► Web search engaged for current events context                     │
│ [23:58:28] ✓ Complexity assessment complete (4.8 score, confidence 95%)        │
│ [23:58:25] ◉ User query received: 180 tokens                                   │
│ [23:57:41] ✓ Q4_POWERFUL completed complex analysis (4.2s) - cache: MISS      │
│ [23:57:35] ● Model health check: All 6 models operational                     │
│ [23:54:21] ✓ Cache maintenance: freed 320MB (expired entries)                  │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ QUERY INPUT & PROCESSING ──────────────────────────────────────────────────────┐
│                                                                                │
│  MODE SELECTOR:  [  ✓ Standard  ] [  Council  ] [  Moderator  ]               │
│                                                                                │
│  Enter query: [_____________________________________________________________] │
│                                                                                │
│  OPTIONS: [Context ✓] [Web Search ✓] [Max Tokens: 4096] [Temp: 0.7]          │
│           [Advanced ▼]                                                         │
│                                                                                │
│                              [ ► SUBMIT QUERY ]                                │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ RESPONSE ──────────────────────────────────────────────────────────────────────┐
│                                                                                │
│  [Processing with Q3_BALANCED tier...]                                        │
│                                                                                │
│  PIPELINE PROGRESS:                                                            │
│  ► Tokenization         [████████████████████████████░░░░░░░░░░░░] 100%       │
│  ► Embedding            [████████████████████████████░░░░░░░░░░░░] 100%       │
│  ► CGRAG Retrieval      [████████████████░░░░░░░░░░░░░░░░░░░░░░░░]  52%       │
│  ► Model Processing     [████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  15%       │
│  ► Post-processing      [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0%      │
│                                                                                │
│  ETA: 3.2 seconds remaining                                                   │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Enhancements from Current State

| Aspect | Before | After |
|--------|--------|-------|
| **Metrics** | 3 basic metrics | 8+ metrics with real-time indicators |
| **Orchestrator Status** | Just header text | Full panel with tier status, allocation |
| **Events** | No event visibility | Live 8-event feed with timestamps |
| **Pipeline Viz** | None | Multi-stage visualization with progress |
| **Visual Impact** | Minimal ASCII | Figlet banner + dense layout |

### Implementation Details

**Figlet Banner:**
```typescript
// Use figlet.js library for dynamic ASCII art banner
// Font: 'Standard' or 'Slant' for compact display
const bannerText = figlet.textSync('SYNAPSE ENGINE', {
  horizontalLayout: 'default',
  verticalLayout: 'default',
});
```

**Component Changes:**
- ➕ New: `OrchestratorStatusPanel` - Multi-tier status display
- ➕ New: `LiveEventFeed` - Auto-scrolling event stream with 8-entry window
- ➕ New: `QueryPipelineVisualization` - Multi-stage progress with labels
- ✏️ Modify: `HomePage.tsx` - Add new panels, expand metrics section
- ✏️ Modify: `SYSTEM STATUS` - Add 8+ metrics instead of 3

**Real-time Updates:**
```typescript
// WebSocket event subscription for live updates
useEffect(() => {
  const ws = new WebSocket('/ws');

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'orchestrator_update') {
      setOrchestratorStatus(data.payload);
    }
    if (data.type === 'event') {
      addEventToFeed(data.payload); // Keep last 8 events
    }
  };
}, []);
```

**Complexity Rating:** ⭐⭐⭐ Medium (3 new components, WebSocket integration)

---

## MetricsPage - Complete Redesign

### Mockup: Dense 4-Panel Analytics Dashboard

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ SYSTEM METRICS & PERFORMANCE ANALYTICS                                    v5.0 ║
║                         ┌─ Last 24 Hours ─┐  ┌─ Last 7 Days ─┐               ║
╚════════════════════════════════════════════════════════════════════════════════╝

┌─ QUERY ANALYTICS ────────────────────────────────────────────────────────────┐
│ TOTAL QUERIES: 2,847 ↑ 12.3% │ AVG LATENCY: 1.24s │ P95: 3.81s │ P99: 7.2s │
│                                                                              │
│ QUERY RATE (queries/min):    RESPONSE TIME (seconds):    BY TIER:           │
│ ┌────────────────────────┐  ┌────────────────────────┐  ┌───────────────┐  │
│ │ 15 │                  │  │ 8 │                    │  │ Q2: 28% █████ │  │
│ │ 12 │    ╱╲      ╱╲    │  │ 6 │      ╱═╲            │  │ Q3: 52% ████░ │  │
│ │  9 │   ╱  ╲    ╱  ╲   │  │ 4 │     ╱   ╲      ╱╲  │  │ Q4: 20% ████░ │  │
│ │  6 │  ╱    ╲  ╱    ╲  │  │ 2 │    ╱     ╲    ╱  ╲ │  │           ▓▓▓▓ │  │
│ │  3 │ ╱      ╲╱      ╲ │  │ 0 ├────────────────────┤  └───────────────┘  │
│ │  0 └────────────────────┘  │ Now -6h  -12h  -18h │                     │
│ │ Now -4h  -8h  -12h      │  └────────────────────────┘                     │
│ │ MIN: 3.2 q/min          │  MIN: 0.23s  MAX: 8.1s  STDDEV: 1.8s         │
│ │ MAX: 14.8 q/min         │  Cache Impact: -0.34s avg when HIT             │
│ │ AVG: 8.3 q/min          │                                                │
│ └────────────────────────┘                                                 │
│                                                                              │
│ CACHE PERFORMANCE:      QUERY SUCCESS RATE:         ERROR BREAKDOWN:        │
│ Hit Rate: 78.9%         99.2%                      Timeout: 0.4%           │
│ █████████████░░░░░░░░   Errors: 0.8%              Network: 0.2%           │
│ +2.4% (24h trend)       Partial: 0.0%              Invalid: 0.2%           │
│                                                    API: 0.0%               │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ TIER-SPECIFIC METRICS ──────────────────────────────────────────────────────┐
│                                                                              │
│ ┌─ Q2_FAST TIER ─────────────────────┐  ┌─ Q3_BALANCED TIER ──────────────┐ │
│ │ COUNT:      801 queries (28%)      │  │ COUNT:    1,480 queries (52%)   │ │
│ │ AVG TIME:   0.34s  ▓▓▓░░░░░░░░░░  │  │ AVG TIME: 1.24s  ▓▓▓▓▓▓░░░░░░  │ │
│ │ SUCCESS:    99.7%  ▓▓▓▓▓▓▓▓▓▓▓░  │  │ SUCCESS: 99.1%  ▓▓▓▓▓▓▓▓▓░░░  │ │
│ │ CACHE HIT:  89.2%  ▓▓▓▓▓▓▓▓▓░░░  │  │ CACHE HIT: 79.3% ▓▓▓▓▓▓▓░░░░░  │ │
│ │ THROUGHPUT: 4.2 q/s │ TEMP: 58°C │  │ THROUGHPUT: 2.1 q/s │ TEMP: 62°C │ │
│ │ ├─ Model Distribution:             │  │ ├─ Model Distribution:          │ │
│ │ │  mistral-7b:   534 (67%)         │  │ │  llama2-13b:   1,021 (69%)   │ │
│ │ │  phi-2.8b:     267 (33%)         │  │ │  neural-7b:      459 (31%)   │ │
│ │ └────────────────────────────────────┘  └──────────────────────────────┘ │
│                                                                              │
│ ┌─ Q4_POWERFUL TIER ──────────────────────────────────────────────────────┐ │
│ │ COUNT:      566 queries (20%)  │  AVG TIME: 4.18s  ▓▓▓▓▓▓▓░░░░░░░░░░░  │ │
│ │ SUCCESS:    98.8% ▓▓▓▓▓▓▓▓░░░  │  CACHE HIT: 71.4% ▓▓▓▓▓▓░░░░░░░░░░░  │ │
│ │ THROUGHPUT: 0.3 q/s │ TEMP: 71°C  │  Peak Memory: 7.8GB / 8.0GB (97%) │ │
│ │ ├─ Model: llama2-70b instruct (566 queries)                             │ │
│ │ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ RESOURCE UTILIZATION & SYSTEM HEALTH ──────────────────────────────────────┐
│                                                                              │
│ GPU MEMORY:                  CPU USAGE:              DISK I/O:              │
│ [██████████████░░░░░░░░░] │ [███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
│ 14.2 / 16.0 GB (88%)      │ 12% (4 cores active)    │ 124 MB/s read        │
│ Q2: 3.0 GB | Q3: 4.0 GB   │ Peak: 28% (last 1h)     │ 89 MB/s write        │
│ Q4: 8.0 GB | Cache: 2.4GB │ Load Avg: 0.8, 1.1, 0.9 │ Cache ops: 4.2K ops/s│
│                                                                              │
│ FAISS INDEX STATUS:         NETWORK I/O:            UPTIME:                │
│ Vectors: 245,892           Bytes In: 3.2 MB/s      23 days, 14 hrs        │
│ Dims: 384 (all-MiniLM)      Bytes Out: 1.8 MB/s     Last restart: 2025-10-16│
│ Size: 1.8 GB                Latency: 0.8ms average  No errors              │
│ Indexing: IDLE              Connections: 24 active  Health: ✓ EXCELLENT    │
│                                                                              │
│ PERFORMANCE SCORE: ████████████░░░░░░ 88/100 (Excellent)                  │
│ └────────────────────────────────────────────────────────────────────────────┘

┌─ ORCHESTRATION & ROUTING DECISIONS ──────────────────────────────────────────┐
│                                                                              │
│ ROUTING ACCURACY:     COMPLEXITY DISTRIBUTION:    CONTEXT USAGE:           │
│ Correct tier:    97.8% │ Simple:    38% ███████   │ Avg words: 180        │
│ Over-provisioned: 1.2% │ Moderate:  48% █████████│ Avg artifacts: 8.3    │
│ Under-utilized:   1.0% │ Complex:   14% ███      │ Avg context: 1.2K    │
│                                                                              │
│ CGRAG PERFORMANCE:                                                          │
│ Queries w/ context: 67.2% (1,912 queries)  │ Retrieval time: avg 87ms     │
│ Avg artifacts per query: 8.3 (median: 7)   │ Relevance score: 0.84 avg    │
│ Context reuse efficiency: 71.3% (cache)    │ Token savings: 34.2K tokens  │
│                                                                              │
│ TOP COMPLEX QUERIES (Q4 Tier):              SLOWEST QUERIES (>3s):         │
│ 1. "Compare architectural patterns..."     1. Deep analysis query (8.1s)   │
│ 2. "Implement distributed system..."       2. Multi-doc synthesis (6.9s)   │
│ 3. "Design consensus algorithm..."         3. Complex reasoning (6.2s)     │
│ 4. "Explain quantum computing..."          4. Pattern matching (5.8s)      │
│ 5. "Build ML pipeline..."                  5. Literature review (5.1s)     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Enhancements from Current State

| Panel | Before | After |
|-------|--------|-------|
| **Query Analytics** | Hardcoded zeros | Real data with charts & trends |
| **Tier Metrics** | Placeholder text | 3 distinct panels, distribution viz |
| **Resource Usage** | 4 basic metrics | 9+ metrics with gauge visualizations |
| **Routing Insights** | Missing | Accuracy & decision analytics |
| **Charts** | "Will implement" | ASCII mini-charts and sparklines |

### Implementation Details

**Components to Create:**
- ➕ New: `QueryAnalyticsPanel` - Line chart of query rate, response time
- ➕ New: `TierComparisonPanel` - Side-by-side tier metrics with sparklines
- ➕ New: `ResourceUtilizationPanel` - 9 metrics with gauge bars
- ➕ New: `RoutingAnalyticsPanel` - Accuracy and CGRAG performance

**Chart Library Integration:**
```typescript
// Use simple-ascii-chart for terminal-style charts
import AsciiChart from 'asciichart';

const queryRateData = [3.2, 5.1, 8.3, 12.1, 10.4, 6.8, 4.2]; // Last 24h

const chart = AsciiChart.plot(queryRateData, {
  height: 6,
  width: 25,
  offset: 3,
  padding: '      ',
  precision: 1,
});
```

**Sparkline Rendering:**
```typescript
// Simple sparkline: ▁▂▃▄▅▆▇█
function renderSparkline(values: number[], max: number): string {
  const chars = '▁▂▃▄▅▆▇█';
  return values
    .map(v => chars[Math.floor((v / max) * (chars.length - 1))])
    .join('');
}
```

**Real-time Metrics Update:**
```typescript
// Metrics cache updated every 5 seconds via WebSocket
useEffect(() => {
  const interval = setInterval(async () => {
    const metrics = await fetch('/api/metrics/query-analytics').then(r => r.json());
    setQueryMetrics(metrics);
  }, 5000);
  return () => clearInterval(interval);
}, []);
```

**Complexity Rating:** ⭐⭐⭐⭐ High (4 new components, chart library integration, complex layouts)

---

## ModelManagementPage - Enhanced

### Mockup: Model Dashboard with Performance Sparklines

```
┌─ PRAXIS MODEL REGISTRY ───────────────────────────────────────────────────────┐
│ MODELS: 8  ENABLED: 7  RUNNING: 6  READY: 6  │  PORT RANGE: 5001-5008       │
│ [⟳ RE-SCAN HUB] [▶ START ALL ENABLED] [⏹ STOP ALL SERVERS]                  │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ TIER ALLOCATION ─────────────────────────────────────────┐  ┌─ SYSTEM HEALTH ─┐
│ ┌──────────────────────────────────────────────────────┐  │  │ Servers: 6/6 ✓  │
│ │ ■ Q2_FAST (3 models) [██████░░░░░░░░░░░░░░░░]  37% │  │  │ Memory: 88% ▓▓▓░ │
│ │ ■ Q3_BALANCED (3 models) [████████████░░░░░░░░░]  │  │  │ CPU: 12% ▓░░░░░░ │
│ │ ■ Q4_POWERFUL (1 model) [██░░░░░░░░░░░░░░░░░░░░] │  │  │ Temp: 62°C avg   │
│ │ ■ UNKNOWN (1 model) [░░░░░░░░░░░░░░░░░░░░░░░░░]  │  │  │ Uptime: 23d 14h  │
│ └──────────────────────────────────────────────────────┘  │  └──────────────────┘
│
│ DISCOVERED MODELS TABLE:
├─ mistral-7b-instruct                         [FAST TIER] [STATE: ACTIVE]    ─┤
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ Port: 5001  Memory: 2.8/3.0 GB (93%)  Temp: 58°C  │ Enabled ✓ Thinking ✓ │ │
│  │ Queries (24h): 534  │ Avg Time: 0.34s  │ Success: 99.7%  │ Cache Hit: 89.2% │ │
│  │ Last 6h Activity:  ▆▇█▇█▆▅▄▃▄▅▆▇█  (trending up 15%)                   │ │
│  │ Response Times:    ▂▂▃▃▃▄▄▄▅▅▅▆▆▇  (stable, max 1.2s)                 │ │
│  │ [⚙ Settings] [➕ Port] [✓ Toggle] [logs ▼]                                │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
├─ phi-2.8b                                    [FAST TIER] [STATE: ACTIVE]    ─┤
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ Port: 5002  Memory: 1.2/2.0 GB (60%)  Temp: 55°C  │ Enabled ✓ Thinking ✗ │ │
│  │ Queries (24h): 267  │ Avg Time: 0.31s  │ Success: 99.9%  │ Cache Hit: 91.8% │ │
│  │ Last 6h Activity:  ▄▄▅▅▆▆▇▇█▇▆▅▄▃  (stable)                            │ │
│  │ Response Times:    ▁▁▂▂▂▂▂▃▃▃▃▃▃▃  (very consistent)                   │ │
│  │ [⚙ Settings] [➕ Port] [✓ Toggle] [logs ▼]                                │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
├─ llama2-13b-chat                          [BALANCED TIER] [STATE: ACTIVE]   ─┤
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ Port: 5003  Memory: 3.2/4.0 GB (80%)  Temp: 62°C  │ Enabled ✓ Thinking ✓ │ │
│  │ Queries (24h): 1021  │ Avg Time: 1.24s  │ Success: 99.1%  │ Cache Hit: 79.3% │ │
│  │ Last 6h Activity:  ▅▆▇█████████▇▆▅▄  (high load)                       │ │
│  │ Response Times:    ▂▃▄▅▆▆▆▇▇██▇▆▆  (mild variance)                    │ │
│  │ [⚙ Settings] [➕ Port] [✓ Toggle] [logs ▼]                                │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
├─ neural-7b-v2                             [BALANCED TIER] [STATE: ACTIVE]   ─┤
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ Port: 5004  Memory: 2.1/3.5 GB (60%)  Temp: 60°C  │ Enabled ✓ Thinking ✓ │ │
│  │ Queries (24h): 459  │ Avg Time: 1.18s  │ Success: 98.9%  │ Cache Hit: 76.4% │ │
│  │ Last 6h Activity:  ▃▄▅▆▆▆▅▆▇█▇▆▅▃  (moderate)                        │ │
│  │ Response Times:    ▂▃▄▄▅▅▆▆▆▇▇▆▅▄  (stable)                          │ │
│  │ [⚙ Settings] [➕ Port] [✓ Toggle] [logs ▼]                                │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
├─ llama2-70b-instruct                        [POWERFUL TIER] [STATE: ACTIVE] ─┤
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ Port: 5005  Memory: 7.8/8.0 GB (97%)  Temp: 71°C  │ Enabled ✓ Thinking ✓ │ │
│  │ Queries (24h): 566  │ Avg Time: 4.18s  │ Success: 98.8%  │ Cache Hit: 71.4% │ │
│  │ Last 6h Activity:  ▁▂▃▃▄▅▆█████████  (sustained high)                  │ │
│  │ Response Times:    ▃▄▅▆▇█████████▇▆  (variable load)                   │ │
│  │ [⚙ Settings] [➕ Port] [✓ Toggle] [logs ▼]                                │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
├─ mistral-large                              [UNKNOWN TIER] [STATE: OFFLINE] ─┤
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ Port: 5006  Memory: 0/24 GB (—%)  Temp: — │ Disabled ✗ Thinking — │ │
│  │ Queries (24h): 0  │ Last seen: 2025-10-28 14:23:01                      │ │
│  │ Last 6h Activity:  ░░░░░░░░░░░░░░░░░░░░  (offline)                     │ │
│  │ [⚙ Settings] [➕ Port] [✓ Toggle] [logs ▼]                                │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ REAL-TIME SERVER LOGS (AUTO-SCROLLING) ──────────────────────────────────────┐
│ [23:58:42] [llama2-13b] ⟳ Processing query: "What is quantum computing?"    │
│ [23:58:40] [mistral-7b] ✓ Completed in 0.34s (cache miss)                  │
│ [23:58:38] [neural-7b] ✓ Completed in 1.12s (cache hit)                    │
│ [23:58:35] [llama2-70b] ⟳ Context: 1.2K tokens, ETA: 3.8s                  │
│ [23:58:32] [System] ⚡ Cache maintenance: freed 320MB                        │
│ [23:58:30] [llama2-70b] ✓ Completed in 4.23s (no cache)                    │
│ [23:58:25] [mistral-7b] ⟳ Processing: "Explain machine learning"            │
│ [23:58:22] [System] ✓ Health check: All 6 models operational               │
│ [23:58:18] [phi-2.8b] ✓ Completed in 0.31s (cache hit)                     │
│ [23:58:15] [neural-7b] ⟳ Loading context artifacts...                      │
│ [23:58:12] [llama2-13b] ✓ Completed in 1.24s (cache miss)                  │
│                                                                              │
│ Scroll: ▓▓▓▓▓▓▓▓▓█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (end visible) ▼   │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Enhancements from Current State

| Element | Before | After |
|---------|--------|-------|
| **Model Rows** | Basic info + settings button | 6 data points + 2 sparklines |
| **Performance Data** | None | 24h query count + activity/timing sparklines |
| **Status Visibility** | Minimal | Memory %, Temp, Health in header |
| **Tier View** | Listed in table | Top panel with distribution gauge |
| **Logs** | Separate panel | Bottom real-time feed with color coding |

### Implementation Details

**Component Changes:**
- ➕ New: `ModelSparkline` - Renders 14-char sparkline (▁▂▃▄▅▆▇█)
- ➕ New: `ModelDashboard` - Container for individual model cards
- ✏️ Modify: `ModelTable` - Replace with dense card layout instead of table
- ✏️ Modify: `LogViewer` - Add color coding, auto-scroll optimization

**Sparkline Data Collection:**
```typescript
// Each model stores hourly activity for last 6 hours (14 data points)
interface ModelMetrics {
  modelId: string;
  queryCount24h: number;
  lastHourActivity: number[]; // 14 hourly buckets
  responseTimesMs: number[]; // 14 samples
  cacheHitRate: number;
}

function renderActivitySparkline(activity: number[]): string {
  const max = Math.max(...activity);
  const chars = '▁▂▃▄▅▆▇█';
  return activity
    .map(v => chars[Math.floor((v / max) * (chars.length - 1))])
    .join('');
}
```

**Memory & Temp Tracking:**
```typescript
// WebSocket subscription for per-model metrics
useEffect(() => {
  const ws = new WebSocket('/ws');
  ws.onmessage = (event) => {
    const { modelId, memoryUsedGb, memoryTotalGb, tempC } = JSON.parse(event.data);
    updateModelMetrics(modelId, { memoryUsedGb, memoryTotalGb, tempC });
  };
}, []);
```

**Complexity Rating:** ⭐⭐⭐ Medium (2 new components, metric aggregation, sparkline rendering)

---

## NEURAL SUBSTRATE DASHBOARD - New

### Purpose
A dedicated orchestrator internals view showing query routing decisions, complexity assessment, context allocation, and CGRAG performance in real-time.

### Mockup: Multi-Panel Control Room

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ NEURAL SUBSTRATE ORCHESTRATOR - INTERNAL COMMAND INTERFACE               v5.0 ║
║                          Status: ✓ ALL SYSTEMS NOMINAL                        ║
╚════════════════════════════════════════════════════════════════════════════════╝

┌─ ACTIVE QUERY STREAMS (5 CONCURRENT) ─────────────────────────────────────────┐
│                                                                              │
│ QUERY #2847 [⟳ PROCESSING 8.2s / 15s budget]                               │
│ ├─ User Input: "Explain quantum computing" (4 tokens)                        │
│ ├─ Complexity Assessment: 5.2 (MODERATE) ► Routing to Q3_BALANCED           │
│ ├─ CGRAG Retrieval: ✓ 12 artifacts (1,240 tokens)  [██████████░░░░░░░░]   │
│ ├─ Model: llama2-13b-chat @ port 5003                                       │
│ └─ Progress: [Retrieve▓▓▓▓▓▓▓▓▓▓░░░░] [Process░░░░░░░░░░░░░░░░░░░░░░░]    │
│                                                                              │
│ QUERY #2846 [✓ COMPLETE (1.12s, Q3_BALANCED, CACHE HIT)]                   │
│ ├─ User Input: "Summarize the article" (3 tokens)                           │
│ ├─ Complexity: 3.1 (SIMPLE) - Decision: Could use Q2 but routed to Q3       │
│ ├─ CGRAG: 1 artifact (180 tokens) from cache                                │
│ └─ Result cached for 47 min (expires at 00:45 UTC)                          │
│                                                                              │
│ QUERY #2845 [✓ COMPLETE (4.28s, Q4_POWERFUL, NO CACHE)]                    │
│ ├─ User Input: "Design a distributed consensus algorithm" (6 tokens)        │
│ ├─ Complexity: 8.7 (COMPLEX) - Routed to Q4_POWERFUL (llama2-70b)          │
│ ├─ CGRAG: 18 artifacts (2,140 tokens) - token budget: 3,000 available       │
│ └─ Result pending cache (high variance = low cache probability)             │
│                                                                              │
│ QUERY #2844 [✓ COMPLETE (0.34s, Q2_FAST, CACHE HIT)]                       │
│ ├─ User Input: "What is REST?" (2 tokens)                                   │
│ ├─ Complexity: 1.2 (SIMPLE) - Routed to Q2_FAST (phi-2.8b)                 │
│ ├─ CGRAG: 0 artifacts (too simple for context)                              │
│ └─ Result: Immediate from cache (91.8% hit rate on simple queries)          │
│                                                                              │
│ [More queries...] ▼ (scroll to see queue)                                   │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ ROUTING DECISION MATRIX ─────────────────────────────────────────────────────┐
│                                                                              │
│ COMPLEXITY SCORE DISTRIBUTION:        TIER ASSIGNMENTS (Last 100 queries):  │
│ ┌─────────────────────────────┐       Q2: 28 decisions [████████░░░░░░░░░] │
│ │ 10 │                        │       Q3: 52 decisions [█████████████░░░░░] │
│ │  8 │           ╱╲           │       Q4: 20 decisions [█████░░░░░░░░░░░░░] │
│ │  6 │          ╱  ╲      ╱╲  │                                             │
│ │  4 │    ╱╲   ╱    ╲    ╱  ╲ │       COMPLEXITY VS. ACTUAL TIER:           │
│ │  2 │   ╱  ╲ ╱      ╲  ╱    │       Expected Q2: 28 | Actual Q2: 29 ✓    │
│ │  0 └─────────────────────────┘       Expected Q3: 52 | Actual Q3: 49 (−3) │
│ │ 0.0  2.5  5.0  7.5  10.0  │       Expected Q4: 20 | Actual Q4: 22 (+2) │
│ │ Trend: ↑ Complexity increasing       Accuracy: 97.8%  [█████████░]     │
│ └─────────────────────────────┘                                             │
│                                                                              │
│ ROUTING CONFIDENCE:           DECISION TIME HISTOGRAM:                      │
│ [████████████████░░░░░░░░░░░░] 93.2% avg  ┌────────────────────────┐      │
│ Last 100 decisions:           │  Median: 47ms                │      │
│ - Very High (>95%): 78        │  P95: 234ms  ╱╲              │      │
│ - High (80-95%): 18           │  P99: 521ms ╱  ╲             │      │
│ - Medium (60-80%): 3          │          ╱    ╲              │      │
│ - Low (<60%): 1               │        ╱      ╲     ╱╲       │      │
│                               │      ╱        ╲   ╱  ╲      │      │
│                               └────────────────────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ CONTEXT ALLOCATION & TOKEN BUDGET TRACKING ──────────────────────────────────┐
│                                                                              │
│ ACTIVE CONTEXT WINDOWS (5 concurrent):                                       │
│                                                                              │
│ Query #2847 (Q3_BALANCED @ llama2-13b):                                     │
│ └─ Budget: 6,000 tokens (half of 12K context window)                        │
│    ├─ System Prompt: 120 tokens  [██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    │
│    ├─ User Query: 4 tokens       [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
│    ├─ CGRAG Artifacts: 1,240 tokens [████████████░░░░░░░░░░░░░░░░░░░░░░░] │
│    └─ Available for generation: 4,636 tokens [██████████████████░░░░░░░░░░░] │
│       Allocation: 79.7% used, 20.3% reserved for output ✓                  │
│                                                                              │
│ Query #2845 (Q4_POWERFUL @ llama2-70b):                                     │
│ └─ Budget: 8,000 tokens (half of 16K context window)                        │
│    ├─ System Prompt: 120 tokens  [█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
│    ├─ User Query: 6 tokens       [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
│    ├─ CGRAG Artifacts: 2,140 tokens [██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
│    └─ Available for generation: 5,734 tokens [████████████████████░░░░░░░░░░] │
│       Allocation: 71.7% used, 28.3% reserved for output ✓                  │
│                                                                              │
│ CONTEXT ALLOCATION PATTERNS:                                                │
│ Avg tokens per query: 1,240  │ Longest context: 2,140 (Q4)                 │
│ Shortest context: 120 (cached simple)  │ Avg utilization: 74.2%            │
│ Spillover events (24h): 0 ✓  │ Token savings from cache: 34.2K ↑ 12.3%    │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ CGRAG PERFORMANCE & VECTOR SEARCH ────────────────────────────────────────────┐
│                                                                              │
│ FAISS INDEX STATE:                    RETRIEVAL QUALITY:                    │
│ Total vectors: 245,892                Top-K Distribution:                   │
│ Dimension: 384 (all-MiniLM-L6-v2)     Avg K retrieved: 8.3 (median: 7)    │
│ Size: 1.8 GB                          Relevance score: 0.84 avg             │
│ Indexing: IDLE (last build 15m ago)   - Top match: 0.91 avg                │
│ Query latency: 87ms avg (p95: 234ms)  - 5th match: 0.71 avg                │
│                                         - Cutoff: 0.62 (min relevance)      │
│ CURRENT QUERIES:                                                             │
│ Query #2847 vector: [ 0.12, -0.34, 0.89, ... 384 dims ]                   │
│ Search: IVF nprobe=16  ► Found 12 candidates in 82ms                       │
│ ├─ mistral-7b-query (0.94) ✓ SELECTED [██████████░░░░░░░░]                │
│ ├─ llama-embedding-doc (0.89) ✓ SELECTED [█████████░░░░░░░░░]              │
│ ├─ neural-context (0.81) ✓ SELECTED [████████░░░░░░░░░░░░]                │
│ ├─ phi-summary (0.76) ✓ SELECTED [███████░░░░░░░░░░░░░░░░]                │
│ ├─ old-reference (0.68) ○ SELECTED (low relevance but needed space)        │
│ ├─ deprecated-page (0.55) ✗ REJECTED (below cutoff)                        │
│ └─ [more...] ✗ NOT SELECTED                                                 │
│                                                                              │
│ CACHE HIT ANALYSIS:                   EMBEDDING CACHE:                      │
│ Exact matches: 73 cache hits (24h)    Size: 340 MB / 512 MB (66%)          │
│ Partial matches: 412 (used as seeds)  Entries: 4,821 embeddings            │
│ TTL-expired: 89 (refreshed)           Refresh rate: 2.3 entries/min        │
│ No match found: 1,363 new queries     Eviction rate: 0.8 entries/min       │
│ Cache effectiveness: 67.2% ↑ 3.1%    Hit rate: 78.9% (vectors cached)      │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ SYSTEM HEALTH & RESOURCE MONITORING ──────────────────────────────────────────┐
│                                                                              │
│ GPU MEMORY (PER TIER):              CPU ALLOCATION:   │ THERMAL STATUS:    │
│ Q2_FAST:   [███░░░░░░░░░░░░░░░░] 26% (2.8/3.0 GB)    │ Q2: 58°C ◜◜◜◜◜░░░ │
│ Q3_BALANCED:[████████░░░░░░░░░░░░░] 68% (2.8/4.0 GB)  │ Q3: 62°C ◜◜◜◜◜◜◜░░ │
│ Q4_POWERFUL:[██████████████░░░░░░░░] 97% (7.8/8.0 GB)  │ Q4: 71°C ◜◜◜◜◜◜◜░░ │
│ Cache:      [██████░░░░░░░░░░░░░░░░] 60% (2.4/4.0 GB)  │ Avg: 63.7°C ✓    │
│                                                                              │
│ QUEUE DEPTH (BY TIER):              WAIT TIMES:                            │
│ Q2_FAST:   0 waiting ✓              Q2: <100ms (immediate)                  │
│ Q3_BALANCED: 1 waiting ⟳           Q3: 280ms (peak load, 1 queued)        │
│ Q4_POWERFUL: 2 waiting ⟳           Q4: 1.2s (sustained load, 2 queued)    │
│                                                                              │
│ ANOMALIES DETECTED: NONE                                                    │
│ Last check: 5 seconds ago              Next check: in 5 seconds             │
│ System health score: 94/100 ✓ EXCELLENT                                     │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Implementation Details

**Route:**
```
GET /api/orchestrator/dashboard
- Returns: Real-time orchestrator state (active queries, routing decisions, context, CGRAG)
- Update frequency: 500ms (WebSocket push)
```

**Components to Create:**
- ➕ New: `ActiveQueryStreams` - 5-query carousel with progress
- ➕ New: `RoutingDecisionMatrix` - Complexity distribution + tier assignment chart
- ➕ New: `ContextAllocationPanel` - Token budget visualization per query
- ➕ New: `CGRAGPerformancePanel` - Vector search quality metrics
- ➕ New: `SystemHealthMonitor` - Real-time resource gauges

**WebSocket Messages:**
```typescript
interface OrchestratorUpdate {
  activeQueries: QueryStream[];
  routingStats: {
    lastHundredDecisions: RoutingDecision[];
    accuracy: number;
    avgConfidence: number;
  };
  contextAllocation: {
    [queryId: string]: {
      budgetTokens: number;
      usedTokens: number;
      available: number;
    };
  };
  cgragStats: {
    retrieval_latency_ms: number;
    avg_relevance: number;
    cache_hit_rate: number;
  };
  health: {
    queues: { [tier: string]: number };
    memory: { [tier: string]: number };
    temps: { [tier: string]: number };
  };
}
```

**Complexity Rating:** ⭐⭐⭐⭐⭐ Very High (5 complex panels, real-time data streams, WebSocket integration)

---

## ASCII Art Library & Tools

### Required NPM Packages

```json
{
  "asciichart": "^1.5.25",           // ASCII line charts
  "figlet": "^1.6.0",                // ASCII art text banners
  "chalk": "^5.3.0",                 // Terminal color styling
  "cli-table3": "^0.6.3",            // ASCII tables
  "sparkly": "^0.1.1"                // Sparkline generation
}
```

### Installation

```bash
npm install asciichart figlet chalk cli-table3 sparkly
```

### Usage Examples

#### Figlet Banner

```typescript
import figlet from 'figlet';

const banner = figlet.textSync('SYNAPSE', {
  horizontalLayout: 'default',
  verticalLayout: 'default',
  font: 'Standard'
});

// ███████ █   █ █   █ ███████ █████  ███████ █████
//    █    ██  █ █   █ █       █      █       █
//    █    █ █ █ █   █ █████   ████   █████   ████
//    █    █  ██ █   █ █       █      █       █
//    █    █   █  █ █  ███████ █████  █████   █████
```

#### ASCII Charts

```typescript
import AsciiChart from 'asciichart';

const data = [3, 5, 8, 12, 10, 6, 4, 7, 9, 11, 8, 5];
const chart = AsciiChart.plot(data, {
  height: 6,
  width: 30,
  offset: 3,
  padding: '  ',
});

// Output:
// 12  │           ╱╲
// 10  │         ╱  ╲╱╲
//  8  │      ╱╲╱    │ ╲
//  6  │╱╲  ╱        │  ╲╱
//  4  │  ╲╱         │
//  0  └──────────────────────
```

#### Sparklines

```typescript
function createSparkline(values: number[], width: number = 14): string {
  const chars = '▁▂▃▄▅▆▇█';
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;

  return values
    .map(v => {
      const normalized = (v - min) / range;
      const index = Math.floor(normalized * (chars.length - 1));
      return chars[Math.min(index, chars.length - 1)];
    })
    .join('');
}

// Example: 14 hours of activity
createSparkline([3, 5, 8, 12, 10, 6, 4, 7, 9, 11, 8, 5, 4, 3]);
// Output: ▁▂▄▆▅▃▂▃▄▆▄▂▂▁
```

#### Gauge Rendering

```typescript
function renderGauge(
  current: number,
  max: number,
  width: number = 20,
  label: string = ''
): string {
  const percentage = (current / max) * 100;
  const filled = Math.round((width / 100) * percentage);
  const empty = width - filled;

  const bar = '█'.repeat(filled) + '░'.repeat(empty);
  const displayValue = `${current.toFixed(1)}/${max.toFixed(1)}`;

  return `${label} [${bar}] ${percentage.toFixed(1)}%`;
}

// Output: VRAM [███████████░░░░░░░░] 61.5%
```

#### Color Coding with Chalk

```typescript
import chalk from 'chalk';

const status = {
  active: chalk.hex('#ff9500'), // Phosphor orange
  processing: chalk.hex('#00ffff'), // Cyan
  error: chalk.hex('#ff0000'), // Red
  success: chalk.green,
};

console.log(status.active('● ACTIVE'));
console.log(status.processing('◉ PROCESSING'));
console.log(status.error('✗ ERROR'));
```

---

## Implementation Roadmap

### Phase 1: HomePage Enhancements (Week 1)

**Priority:** High
**Estimated Time:** 8-10 hours
**Complexity:** Medium

**Tasks:**
1. Create figlet banner (3 lines of ASCII art)
2. Add 8+ metrics to SYSTEM STATUS panel
3. Create `OrchestratorStatusPanel` component
4. Create `LiveEventFeed` component (8-event window)
5. Create `QueryPipelineVisualization` component
6. Integrate WebSocket for real-time updates
7. Update `HomePage.tsx` layout

**Deliverables:**
- Dense 4-section homepage with 50+ data points visible
- Real-time event feed updating every 500ms
- Query pipeline progress visualization

---

### Phase 2: MetricsPage Redesign (Week 2)

**Priority:** High
**Estimated Time:** 12-14 hours
**Complexity:** High

**Tasks:**
1. Create `QueryAnalyticsPanel` (AsciiChart integration)
2. Create `TierComparisonPanel` (3 sparkline comparisons)
3. Create `ResourceUtilizationPanel` (9 metrics)
4. Create `RoutingAnalyticsPanel` (routing accuracy)
5. Integrate real-time metrics via REST API
6. Implement 5-second refresh interval
7. Wire up all panels to `/api/metrics/` endpoints

**Deliverables:**
- Complete metrics dashboard with 4 dense panels
- 8+ charts and sparklines
- Real-time data updates every 5 seconds

---

### Phase 3: ModelManagementPage Enhancements (Week 2-3)

**Priority:** Medium
**Estimated Time:** 8-10 hours
**Complexity:** Medium

**Tasks:**
1. Create `ModelSparkline` component
2. Create `ModelDashboard` card layout
3. Refactor `ModelTable` to use card layout
4. Add per-model metrics aggregation
5. Integrate 6-hour activity tracking
6. Create colored log feed in bottom panel
7. Add model performance sparklines

**Deliverables:**
- Model management with per-model dashboards
- 2 sparklines per model (activity + response times)
- Color-coded real-time log feed

---

### Phase 4: NEURAL SUBSTRATE DASHBOARD (Week 3-4)

**Priority:** High
**Estimated Time:** 16-20 hours
**Complexity:** Very High

**Tasks:**
1. Create `ActiveQueryStreams` carousel
2. Create `RoutingDecisionMatrix` component
3. Create `ContextAllocationPanel` component
4. Create `CGRAGPerformancePanel` component
5. Create `SystemHealthMonitor` component
6. Implement `/api/orchestrator/dashboard` endpoint
7. Wire WebSocket 500ms push updates
8. Create new route `/admin/orchestrator`

**Deliverables:**
- Full orchestrator internal command center
- 5 concurrent query stream visualization
- Real-time routing decision matrix
- Context allocation per query
- CGRAG vector search metrics

---

## Code Snippets & Components

### 1. MetricDisplay Extension (Multi-Format)

```typescript
export interface MetricDisplayProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: TrendType;
  status?: MetricStatus;
  sparkline?: number[]; // NEW: optional sparkline data
  gauge?: boolean;      // NEW: show as gauge instead of value
  className?: string;
}

export const MetricDisplay: React.FC<MetricDisplayProps> = ({
  label,
  value,
  unit,
  trend,
  status = 'default',
  sparkline,
  gauge,
  className,
}) => {
  const renderSparkline = (values: number[]) => {
    const chars = '▁▂▃▄▅▆▇█';
    const max = Math.max(...values);
    const normalized = values.map(v =>
      chars[Math.floor((v / max) * (chars.length - 1))]
    );
    return normalized.join('');
  };

  return (
    <div className={clsx(styles.metric, className)}>
      <div className={styles.label}>{label}</div>
      <div className={styles.valueRow}>
        {gauge ? (
          <span className={styles.gauge}>
            {Array(Math.round((value as number) / 10))
              .fill('█')
              .join('')}
            {Array(10 - Math.round((value as number) / 10))
              .fill('░')
              .join('')}
          </span>
        ) : (
          <>
            <span className={clsx(styles.value, status !== 'default' && styles[status])}>
              {value}
            </span>
            {unit && <span className={styles.unit}>{unit}</span>}
          </>
        )}
        {trend && <span className={clsx(styles.trend, styles[trend])} />}
      </div>
      {sparkline && (
        <div className={styles.sparkline}>
          {renderSparkline(sparkline)}
        </div>
      )}
    </div>
  );
};
```

### 2. Sparkline Component

```typescript
import React, { useMemo } from 'react';
import styles from './Sparkline.module.css';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: 'orange' | 'cyan' | 'green' | 'red';
  trend?: 'up' | 'down' | 'neutral';
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  width = 14,
  color = 'orange',
  trend,
}) => {
  const sparklineStr = useMemo(() => {
    const chars = '▁▂▃▄▅▆▇█';
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    return data
      .slice(-width)
      .map(v => {
        const normalized = (v - min) / range;
        const index = Math.floor(normalized * (chars.length - 1));
        return chars[Math.min(index, chars.length - 1)];
      })
      .join('');
  }, [data, width]);

  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';

  return (
    <span className={`${styles.sparkline} ${styles[color]}`}>
      {sparklineStr}
      {trend && <span className={styles.trend}>{trendIcon}</span>}
    </span>
  );
};
```

### 3. Event Feed Component

```typescript
import React, { useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import styles from './LiveEventFeed.module.css';

interface Event {
  timestamp: string;
  type: 'query' | 'completion' | 'error' | 'system' | 'cache';
  message: string;
  metadata?: Record<string, any>;
}

export const LiveEventFeed: React.FC<{ maxEvents?: number }> = ({
  maxEvents = 8
}) => {
  const [events, setEvents] = useState<Event[]>([]);
  const { data: wsData } = useWebSocket('/ws');

  useEffect(() => {
    if (wsData?.type === 'event') {
      const newEvent: Event = {
        timestamp: new Date().toLocaleTimeString(),
        type: wsData.eventType,
        message: wsData.message,
        metadata: wsData.metadata,
      };

      setEvents(prev => [newEvent, ...prev].slice(0, maxEvents));
    }
  }, [wsData, maxEvents]);

  const getIcon = (type: Event['type']) => {
    switch (type) {
      case 'query': return '▸';
      case 'completion': return '✓';
      case 'error': return '✗';
      case 'cache': return '⚡';
      case 'system': return '◉';
      default: return '●';
    }
  };

  const getColor = (type: Event['type']) => {
    switch (type) {
      case 'completion': return styles.success;
      case 'error': return styles.error;
      case 'cache': return styles.processing;
      case 'system': return styles.system;
      default: return styles.default;
    }
  };

  return (
    <div className={styles.feed} role="region" aria-label="Live event feed">
      {events.map((event, i) => (
        <div key={i} className={`${styles.event} ${getColor(event.type)}`}>
          <span className={styles.timestamp}>[{event.timestamp}]</span>
          <span className={styles.icon}>{getIcon(event.type)}</span>
          <span className={styles.message}>{event.message}</span>
        </div>
      ))}
    </div>
  );
};
```

### 4. QueryPipelineVisualization Component

```typescript
import React from 'react';
import { ProgressBar } from '@/components/terminal';
import styles from './QueryPipelineVisualization.module.css';

interface PipelineStage {
  name: string;
  status: 'pending' | 'in-progress' | 'complete' | 'skipped';
  progress: number; // 0-100
  duration?: number; // milliseconds
}

interface QueryPipelineVisualizationProps {
  stages: PipelineStage[];
  currentStage: number;
  estimatedTimeRemaining?: number;
}

export const QueryPipelineVisualization: React.FC<QueryPipelineVisualizationProps> = ({
  stages,
  currentStage,
  estimatedTimeRemaining,
}) => {
  const getStageIcon = (status: string, index: number) => {
    if (index < currentStage) return '✓';
    if (index === currentStage) return '▸';
    return '○';
  };

  return (
    <div className={styles.container} role="region" aria-label="Query processing pipeline">
      <div className={styles.header}>
        <h3>QUERY PIPELINE</h3>
        {estimatedTimeRemaining && (
          <span className={styles.eta}>
            ETA: {(estimatedTimeRemaining / 1000).toFixed(1)}s
          </span>
        )}
      </div>

      <div className={styles.stages}>
        {stages.map((stage, i) => (
          <div key={i} className={`${styles.stage} ${styles[stage.status]}`}>
            <div className={styles.stageHeader}>
              <span className={styles.icon}>
                {getStageIcon(stage.status, i)}
              </span>
              <span className={styles.name}>{stage.name}</span>
            </div>
            <ProgressBar
              current={stage.progress}
              max={100}
              showPercentage={true}
              variant={
                stage.status === 'in-progress' ? 'accent' : 'default'
              }
            />
            {stage.duration && (
              <span className={styles.duration}>
                {(stage.duration).toFixed(0)}ms
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 5. CSS Module: Panel Enhancement

```css
/* frontend/src/components/terminal/Panel/Panel.module.css */

.panel {
  border: 1px solid #ff9500;
  background: rgba(10, 14, 20, 0.85);
  color: #ff9500;
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 16px;
  box-shadow: 0 0 10px rgba(255, 149, 0, 0.1);
  transition: all 0.3s ease;
  will-change: box-shadow;
}

.panel:hover {
  box-shadow: 0 0 20px rgba(255, 149, 0, 0.2);
  border-color: #00ffff;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #ff9500;
  background: rgba(0, 0, 0, 0.3);
  font-weight: bold;
  font-size: 12px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.title {
  margin: 0;
  color: #ff9500;
  font-size: 12px;
}

.titleRight {
  color: #00ffff;
  font-size: 11px;
}

.content {
  padding: 12px;
}

.noPadding {
  padding: 0;
}

/* Variants */
.default {
  border-color: #ff9500;
}

.accent {
  border-color: #00ffff;
}

.accent .header {
  border-bottom-color: #00ffff;
}

.warning {
  border-color: #ffaa00;
}

.error {
  border-color: #ff0000;
}

.error .header {
  border-bottom-color: #ff0000;
  color: #ff0000;
}
```

---

## File Modification Summary

### New Files to Create

```
➕ frontend/src/components/terminal/Sparkline/Sparkline.tsx
➕ frontend/src/components/terminal/Sparkline/Sparkline.module.css
➕ frontend/src/components/dashboard/LiveEventFeed/LiveEventFeed.tsx
➕ frontend/src/components/dashboard/LiveEventFeed/LiveEventFeed.module.css
➕ frontend/src/components/dashboard/QueryPipelineVisualization/QueryPipelineVisualization.tsx
➕ frontend/src/components/dashboard/QueryPipelineVisualization/QueryPipelineVisualization.module.css
➕ frontend/src/components/dashboard/OrchestratorStatusPanel/OrchestratorStatusPanel.tsx
➕ frontend/src/components/dashboard/OrchestratorStatusPanel/OrchestratorStatusPanel.module.css
➕ frontend/src/components/dashboard/QueryAnalyticsPanel/QueryAnalyticsPanel.tsx
➕ frontend/src/components/dashboard/QueryAnalyticsPanel/QueryAnalyticsPanel.module.css
➕ frontend/src/components/dashboard/ModelSparkline/ModelSparkline.tsx
➕ frontend/src/components/dashboard/ModelSparkline/ModelSparkline.module.css
```

### Files to Modify

```
✏️ frontend/src/pages/HomePage/HomePage.tsx (add new panels, expand layout)
✏️ frontend/src/pages/MetricsPage/MetricsPage.tsx (complete redesign)
✏️ frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx (add sparklines)
✏️ frontend/src/components/terminal/MetricDisplay/MetricDisplay.tsx (add sparkline prop)
✏️ frontend/src/components/terminal/MetricDisplay/MetricDisplay.module.css (add sparkline styles)
✏️ frontend/src/components/terminal/Panel/Panel.module.css (enhance hover effects)
✏️ frontend/package.json (add figlet, asciichart, chalk, cli-table3)
✏️ docker-compose.yml (rebuild frontend with new dependencies)
```

### New Backend Routes

```
✏️ backend/app/routers/metrics.py
  GET /api/metrics/query-analytics (new endpoint)
  GET /api/metrics/tier-breakdown (new endpoint)
  GET /api/metrics/resource-utilization (new endpoint)

✏️ backend/app/routers/orchestrator.py
  GET /api/orchestrator/dashboard (new endpoint)
  GET /api/orchestrator/routing-stats (new endpoint)
  GET /api/orchestrator/context-allocation (new endpoint)
```

---

## Success Criteria

### Phase 1 (HomePage) ✅
- [ ] Figlet banner renders without distortion
- [ ] 8+ metrics visible and updating in real-time
- [ ] Event feed displays and auto-scrolls
- [ ] Pipeline visualization shows progress stages
- [ ] All metrics update via WebSocket every 500ms
- [ ] Mobile responsive (stacks vertically below 1024px)

### Phase 2 (MetricsPage) ✅
- [ ] 4 panels visible without scrolling on 1440p
- [ ] Charts render with asciichart library
- [ ] Sparklines display with proper scaling
- [ ] Real-time updates every 5 seconds
- [ ] Routing accuracy chart shows historical trends
- [ ] CGRAG metrics include vector search latency

### Phase 3 (ModelManagementPage) ✅
- [ ] Card layout instead of table
- [ ] 2 sparklines per model (activity + response time)
- [ ] Model metrics accurate and updating
- [ ] Log feed color-coded by event type
- [ ] Tier distribution gauge shows allocation
- [ ] Performance is smooth (60fps scrolling)

### Phase 4 (NEURAL SUBSTRATE DASHBOARD) ✅
- [ ] 5 active query streams visible
- [ ] Routing decision matrix shows accuracy
- [ ] Context allocation per query with token budgets
- [ ] CGRAG performance panel with vector search metrics
- [ ] System health monitor with real-time gauges
- [ ] WebSocket updates every 500ms
- [ ] New route accessible from main navigation

---

## Performance Considerations

### Memory Usage Targets
- Event feed: 8 events = ~2KB
- Metrics cache: Last 24h data = ~15KB
- Sparkline data: 14 samples × 8 models = ~1KB
- **Total estimated:** <100KB DOM overhead

### Update Frequency
- HomePage: WebSocket 500ms (8 metrics)
- MetricsPage: REST API 5s (cached data)
- ModelManagementPage: WebSocket 3s (sparklines)
- NEURAL SUBSTRATE: WebSocket 500ms (live streams)

### Optimization Strategies
1. **Memoization:** useMemo for chart calculations
2. **Virtual Scrolling:** useCallback for event feed
3. **Debouncing:** 500ms WebSocket throttle
4. **Canvas Rendering:** AsciiChart uses canvas, not DOM
5. **CSS Hardware Acceleration:** will-change on animated elements

---

## Accessibility Checklist

- [ ] All panels have semantic `role="region"` with `aria-label`
- [ ] Charts include `aria-label` describing trends
- [ ] Progress bars use `role="progressbar"` with ARIA attributes
- [ ] Sparklines have text fallback descriptions
- [ ] Event feed is screen-reader friendly
- [ ] Color indicators supplemented with text/symbols
- [ ] Tab navigation through all interactive elements
- [ ] Focus indicators visible (cyan outline)
- [ ] Keyboard support: arrow keys for navigation

---

## Additional Notes

### Why Dense Layouts?

Dense information displays (Bloomberg terminal style) maximize visibility:
- **40+ data points per screen** vs 3-5 in conventional UI
- **Parallel processing:** Your brain can scan patterns across items
- **Professional feel:** Density conveys power and precision
- **Functional:** No unnecessary whitespace, no scroll for core info

### Why ASCII Art?

- **Performance:** Text-based, faster than canvas/SVG
- **Nostalgic:** Fits NGE NERV aesthetic perfectly
- **Accessibility:** Sparklines and charts are text, not images
- **Portability:** Works on any screen size without scaling issues
- **Character-based:** Aligns with terminal philosophy (columns/rows)

### Design Inspirations

- **Bloomberg Terminal:** Extreme information density
- **Evangelion NERV:** Technical interfaces with phosphor orange
- **S.Y.N.A.P.S.E. ENGINE:** Distributed neural network metaphor
- **Unix/Linux:** Terminal-first design philosophy

---

## References

- [AsciiChart.js Documentation](https://github.com/frexp/asciichart)
- [Figlet.js Documentation](https://github.com/patorjk/figlet.js)
- [Chalk Terminal Colors](https://github.com/chalk/chalk)
- [Terminal UI Patterns](https://www.bloombergquint.com/)

---

**Document Status:** Ready for implementation
**Next Step:** Begin Phase 1 (HomePage enhancements)
**Contact:** Terminal UI Specialist