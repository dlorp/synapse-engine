# Dense Terminal Mockups - Quick Reference Guide

**Document:** [DENSE_TERMINAL_MOCKUPS.md](./DENSE_TERMINAL_MOCKUPS.md)
**Status:** Production Design Phase - Ready for Implementation
**Last Updated:** 2025-11-08

---

## For Product Designers

Review these sections to understand the overall vision:

1. **[Design Philosophy](./DENSE_TERMINAL_MOCKUPS.md#design-philosophy)** - Why dense layouts, color palette, ASCII art principles
2. **[HomePage Enhanced](./DENSE_TERMINAL_MOCKUPS.md#homepage---enhanced)** - Main query interface mockup (6 section layout)
3. **[MetricsPage Redesign](./DENSE_TERMINAL_MOCKUPS.md#metricspage---complete-redesign)** - Analytics dashboard (4 dense panels)
4. **[ModelManagementPage Enhanced](./DENSE_TERMINAL_MOCKUPS.md#modelmanagementpage---enhanced)** - Model control interface with sparklines
5. **[NEURAL SUBSTRATE DASHBOARD](./DENSE_TERMINAL_MOCKUPS.md#neural-substrate-dashboard---new)** - Orchestrator command center (5 complex panels)

**Visual Style:** Bloomberg terminal meets Evangelion NERV, phosphor orange (#ff9500) primary color, dense information displays.

---

## For Frontend Engineers

Implement features using this structured approach:

### Phase 1: HomePage (Week 1)
**File:** [DENSE_TERMINAL_MOCKUPS.md#phase-1-homepage-enhancements-week-1](./DENSE_TERMINAL_MOCKUPS.md#phase-1-homepage-enhancements-week-1)

Components to create:
- `OrchestratorStatusPanel` - Multi-tier status + allocation
- `LiveEventFeed` - 8-event carousel with auto-scroll
- `QueryPipelineVisualization` - Multi-stage progress

Code patterns: [DENSE_TERMINAL_MOCKUPS.md#4-querypipelinevisualization-component](./DENSE_TERMINAL_MOCKUPS.md#4-querypipelinevisualization-component)

### Phase 2: MetricsPage (Week 2)
**File:** [DENSE_TERMINAL_MOCKUPS.md#phase-2-metricspage-redesign-week-2](./DENSE_TERMINAL_MOCKUPS.md#phase-2-metricspage-redesign-week-2)

Components to create:
- `QueryAnalyticsPanel` - Line charts with AsciiChart
- `TierComparisonPanel` - Sparkline comparisons
- `ResourceUtilizationPanel` - 9 metrics display
- `RoutingAnalyticsPanel` - Accuracy visualization

Key library: `asciichart` for ASCII charts

### Phase 3: ModelManagementPage (Week 2-3)
**File:** [DENSE_TERMINAL_MOCKUPS.md#phase-3-modelmanagementpage-enhancements-week-2-3](./DENSE_TERMINAL_MOCKUPS.md#phase-3-modelmanagementpage-enhancements-week-2-3)

Components to create:
- `Sparkline` - Reusable sparkline component (14 chars, 8 symbols)
- `ModelDashboard` - Card-based layout for models
- Enhanced `LogViewer` - Color-coded event types

Code pattern: [DENSE_TERMINAL_MOCKUPS.md#2-sparkline-component](./DENSE_TERMINAL_MOCKUPS.md#2-sparkline-component)

### Phase 4: NEURAL SUBSTRATE DASHBOARD (Week 3-4)
**File:** [DENSE_TERMINAL_MOCKUPS.md#phase-4-neural-substrate-dashboard-week-3-4](./DENSE_TERMINAL_MOCKUPS.md#phase-4-neural-substrate-dashboard-week-3-4)

Components to create:
- `ActiveQueryStreams` - 5-query carousel
- `RoutingDecisionMatrix` - Complexity distribution
- `ContextAllocationPanel` - Token budget vis
- `CGRAGPerformancePanel` - Vector search metrics
- `SystemHealthMonitor` - Resource gauges

---

## For Backend Engineers

API endpoints needed:

### Existing (Verify Compatibility)
- `GET /api/models/status` - Used by HomePage, MetricsPage
- `GET /api/models/registry` - Used by ModelManagementPage

### New Endpoints Required

**MetricsPage:**
```
GET /api/metrics/query-analytics
  Response: {
    totalQueries: number,
    avgLatency: number,
    p95Latency: number,
    p99Latency: number,
    queryRate: number[],      // Last 24 hours
    responseTime: number[],   // Last 24 hours
    cacheHitRate: number,
    successRate: number,
    errorBreakdown: { timeout: number, network: number, ... }
  }

GET /api/metrics/tier-breakdown
  Response: {
    q2: { count: number, avgTime: number, successRate: number, ... },
    q3: { count: number, avgTime: number, successRate: number, ... },
    q4: { count: number, avgTime: number, successRate: number, ... }
  }

GET /api/metrics/resource-utilization
  Response: {
    gpu: { used: number, total: number, byTier: {...} },
    cpu: number,
    disk: { read: number, write: number },
    network: { in: number, out: number },
    ...
  }
```

**NEURAL SUBSTRATE DASHBOARD (WebSocket):**
```
GET /api/orchestrator/dashboard
  Pushed every 500ms via WebSocket /ws:
  {
    activeQueries: QueryStream[],
    routingStats: {
      decisions: RoutingDecision[],
      accuracy: number,
      avgConfidence: number
    },
    contextAllocation: { [queryId]: { used: number, budget: number } },
    cgradPerformance: { latency: number, relevance: number, ... },
    health: { queues: {...}, memory: {...}, temps: {...} }
  }
```

See [DENSE_TERMINAL_MOCKUPS.md#code-snippets--components](./DENSE_TERMINAL_MOCKUPS.md#code-snippets--components) for data structures.

---

## Library Installation

Add to `frontend/package.json`:
```bash
npm install asciichart figlet chalk cli-table3 sparkly
```

See [DENSE_TERMINAL_MOCKUPS.md#ascii-art-library--tools](./DENSE_TERMINAL_MOCKUPS.md#ascii-art-library--tools) for detailed usage examples.

---

## File Changes at a Glance

### New Files (10+)
```
✏️ frontend/src/components/terminal/Sparkline/
✏️ frontend/src/components/dashboard/LiveEventFeed/
✏️ frontend/src/components/dashboard/QueryPipelineVisualization/
✏️ frontend/src/components/dashboard/OrchestratorStatusPanel/
✏️ frontend/src/components/dashboard/QueryAnalyticsPanel/
✏️ frontend/src/components/dashboard/ModelSparkline/
```

### Modified Files (7)
```
HomePage.tsx - Add orchestrator panel, event feed, pipeline viz
MetricsPage.tsx - Complete redesign with 4 panels
ModelManagementPage.tsx - Add sparklines, card layout
MetricDisplay.tsx - Add sparkline & gauge support
Panel.module.css - Enhance hover effects
package.json - Add ASCII libraries
docker-compose.yml - Rebuild frontend
```

Full details: [DENSE_TERMINAL_MOCKUPS.md#file-modification-summary](./DENSE_TERMINAL_MOCKUPS.md#file-modification-summary)

---

## Mockup Visual Summary

### HomePage
```
┌─ FIGLET BANNER (ASCII Art Title)
├─ SYSTEM STATUS (8+ metrics)
├─ NEURAL SUBSTRATE ORCHESTRATOR (Tier status, context allocation)
├─ LIVE EVENT FEED (Last 8 events)
├─ QUERY INPUT & PROCESSING (Mode selector, input field)
└─ RESPONSE (Pipeline progress with stages)
```

### MetricsPage
```
├─ QUERY ANALYTICS (Charts: query rate, response time, by tier)
├─ TIER-SPECIFIC METRICS (Q2, Q3, Q4 side-by-side)
├─ RESOURCE UTILIZATION (GPU/CPU/Disk/Network gauges)
└─ ORCHESTRATION & ROUTING (Accuracy, complexity, CGRAG perf)
```

### ModelManagementPage
```
├─ TIER ALLOCATION (Gauge showing distribution)
├─ MODEL DASHBOARD (Cards with per-model metrics + sparklines)
│  └─ Each card: Memory%, Temp, 24h query count, 2 sparklines
└─ REAL-TIME LOGS (Auto-scrolling color-coded event feed)
```

### NEURAL SUBSTRATE DASHBOARD (New)
```
├─ ACTIVE QUERY STREAMS (5 concurrent queries with progress)
├─ ROUTING DECISION MATRIX (Complexity distribution + accuracy)
├─ CONTEXT ALLOCATION (Token budget per query)
├─ CGRAG PERFORMANCE (Vector search + relevance metrics)
└─ SYSTEM HEALTH (Resource gauges + queue depth)
```

---

## Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| WebSocket latency | <50ms | Binary protocol, delta updates |
| Chart render time | <100ms | AsciiChart uses canvas |
| Sparkline render | <5ms | Text-based, no DOM mutations |
| Memory overhead | <100KB | Event feed limited to 8 items |
| Update frequency | 500ms (WebSocket) / 5s (REST) | Configurable per view |

---

## Implementation Checklist

### Before Starting
- [ ] Read entire [DENSE_TERMINAL_MOCKUPS.md](./DENSE_TERMINAL_MOCKUPS.md)
- [ ] Review [Design Philosophy](./DENSE_TERMINAL_MOCKUPS.md#design-philosophy) section
- [ ] Understand color palette: #ff9500 (orange), #00ffff (cyan), #ff0000 (red)
- [ ] Set up ASCII libraries: `npm install asciichart figlet chalk`

### Phase 1 Completion
- [ ] HomePage displays figlet banner
- [ ] 8+ metrics visible and updating
- [ ] Event feed auto-scrolls (8 items max)
- [ ] Pipeline visualization shows 4-5 stages
- [ ] All updates via WebSocket every 500ms

### Phase 2 Completion
- [ ] MetricsPage renders without scroll on 1440p
- [ ] 4 dense panels with 8+ charts
- [ ] Real-time data every 5 seconds
- [ ] Sparklines display with proper scaling

### Phase 3 Completion
- [ ] Models display as cards with sparklines
- [ ] 2 sparklines per model (activity + response time)
- [ ] Log feed color-coded by event type

### Phase 4 Completion
- [ ] NEURAL SUBSTRATE DASHBOARD accessible from nav
- [ ] 5 complex panels visible
- [ ] WebSocket updates every 500ms
- [ ] All metrics real-time and accurate

---

## Common Patterns

### Sparkline Rendering
```typescript
const chars = '▁▂▃▄▅▆▇█';
const sparkline = data.map(v =>
  chars[Math.floor((v / max) * (chars.length - 1))]
).join('');
// Result: ▁▂▃▄▅▆▇█
```

### Gauge Rendering
```typescript
const filled = Math.round((percent / 100) * 20);
const gauge = '█'.repeat(filled) + '░'.repeat(20 - filled);
// Result: ████████████░░░░░░░░
```

### WebSocket Subscription
```typescript
const { data } = useWebSocket('/ws', {
  onMessage: (msg) => {
    if (msg.type === 'metrics') updateMetrics(msg.payload);
  },
});
```

---

## Design Decision Rationale

**Why Dense Layouts?**
- Bloomberg terminal shows 40+ data points per screen
- Enables pattern recognition across multiple metrics
- Professional appearance conveying power
- Maximizes information without excessive scrolling

**Why ASCII Art?**
- Nostalgic NGE NERV aesthetic
- Performant (text-based, not canvas)
- Accessible (no images, works with screen readers)
- Fits terminal UI philosophy

**Why WebSocket for Updates?**
- Real-time at 500ms intervals
- Lower bandwidth than constant polling
- Better UX (immediate visual feedback)
- Enables live event streams

**Why Sparklines Over Charts?**
- Compact (14 characters per 6-hour trend)
- Easy to scan across multiple models
- Information-dense representation
- No separate chart library needed

---

## Troubleshooting

**AsciiChart not rendering?**
- Ensure canvas rendering is enabled
- Check console for width/height errors
- Verify data array is not empty

**Sparklines showing all same height?**
- Check max value calculation
- Verify data has variance (not flat)
- Ensure normalization formula is correct

**WebSocket updates not flowing?**
- Verify `/ws` endpoint exists on backend
- Check browser console for connection errors
- Ensure JSON serialization of complex types

**Color not showing?**
- Use CSS classes, not inline styles
- Verify color hex values (e.g., #ff9500)
- Check Panel variant prop (default/accent/warning/error)

---

## Next Steps

1. **Review:** Read [DENSE_TERMINAL_MOCKUPS.md](./DENSE_TERMINAL_MOCKUPS.md) entirely
2. **Discuss:** Review design with team, get feedback on Phase 1
3. **Start Phase 1:** Create HomePage enhancements (figlet, 8+ metrics, event feed)
4. **Estimate:** Refine timeline based on backend availability
5. **Build:** Implement components following code snippets provided

---

## Document Navigation

- **Design Overview:** [Design Philosophy](./DENSE_TERMINAL_MOCKUPS.md#design-philosophy)
- **HomePage Mockup:** [Enhanced HomePage](./DENSE_TERMINAL_MOCKUPS.md#homepage---enhanced)
- **MetricsPage Mockup:** [Complete Redesign](./DENSE_TERMINAL_MOCKUPS.md#metricspage---complete-redesign)
- **ModelManagement Mockup:** [Enhancements](./DENSE_TERMINAL_MOCKUPS.md#modelmanagementpage---enhanced)
- **NEURAL SUBSTRATE Dashboard:** [New Dashboard](./DENSE_TERMINAL_MOCKUPS.md#neural-substrate-dashboard---new)
- **Libraries & Tools:** [ASCII Art Library](./DENSE_TERMINAL_MOCKUPS.md#ascii-art-library--tools)
- **Implementation Phases:** [Roadmap](./DENSE_TERMINAL_MOCKUPS.md#implementation-roadmap)
- **Code Snippets:** [Production Code](./DENSE_TERMINAL_MOCKUPS.md#code-snippets--components)
- **File Changes:** [Modification Summary](./DENSE_TERMINAL_MOCKUPS.md#file-modification-summary)

---

## Contacts & Questions

**Terminal UI Specialist** - I wrote this mockup document. Use it as your implementation spec.

**Design Questions?** Review the [Design Philosophy](./DENSE_TERMINAL_MOCKUPS.md#design-philosophy) section.

**Implementation Questions?** Check the [Code Snippets](./DENSE_TERMINAL_MOCKUPS.md#code-snippets--components) section for production-ready examples.

**Backend Integration?** See the [Implementation Roadmap](./DENSE_TERMINAL_MOCKUPS.md#implementation-roadmap) for required endpoints.

---

**Status:** Ready for implementation
**Target Start:** Immediately (Phase 1)
**Estimated Duration:** 4-5 weeks (all 4 phases)