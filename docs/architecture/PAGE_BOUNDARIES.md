# Synapse Engine Page Boundaries

**Last Updated:** 2025-11-09
**Status:** Implemented (UI Consolidation Plan)

---

## Purpose

This document defines the **clear boundaries** between the three primary pages in the Synapse Engine UI. Each page serves a distinct role in the user workflow.

---

## HomePage - "Mission Control"

**URL:** `/`

**Purpose:** Submit queries and monitor **current system state** in real-time.

**User Questions Answered:**
- Can I submit a query right now?
- How many models are online?
- Is the system healthy?
- What's happening RIGHT NOW?

**Components:**
- **DotMatrixDisplay** - Synapse Engine banner with reactive states
- **SystemStatusPanelEnhanced** - 5 essential metrics (static snapshots, no trends):
  1. Active Models (Q2/Q3/Q4 breakdown)
  2. Active Queries (current load)
  3. Cache Hit Rate (static percentage)
  4. Context Utilization (operational readiness)
  5. System Uptime (stability indicator)
- **OrchestratorStatusPanel** - Real-time routing visualization
- **LiveEventFeed** - 8-event rolling window (WebSocket)
- **QueryInput** - Query submission with mode selector
- **ResponseDisplay** - Query results display
- **QuickActions** - Rescan, Enable All, Disable All

**What NOT to Show:**
- ❌ Historical trends (sparklines, charts)
- ❌ Time-series data (anything with "over time")
- ❌ Performance analytics (tier comparisons)
- ❌ System resource deep-dive (detailed VRAM/CPU/memory grids)

**Information Philosophy:** "What's the system state RIGHT NOW?"

---

## MetricsPage - "Observatory"

**URL:** `/metrics`

**Purpose:** Monitor **performance trends** and **historical data** for system optimization.

**User Questions Answered:**
- How is performance trending over time?
- Which tier is most efficient?
- Are we seeing resource bottlenecks?
- What's the routing decision accuracy?
- Which models are available?

**Components (5 Panels):**

1. **SystemHealthOverview** - Aggregate system health trends:
   - Queries/sec sparkline (30-min history)
   - Token gen rate sparkline (30-min history)
   - Avg latency sparkline (30-min history)
   - Cache hit rate sparkline (30-min history)

2. **QueryAnalyticsPanel** - Query metrics over time:
   - Query rate line chart
   - Latency bar chart
   - Tier distribution breakdown

3. **TierComparisonPanel** - Q2/Q3/Q4 performance comparison:
   - Tokens/sec sparklines per tier
   - Latency sparklines per tier
   - Side-by-side comparison

4. **ResourceUtilizationPanel** - System resource monitoring:
   - 9-metric grid: VRAM, CPU, Memory, Disk, Network, FAISS, Redis, Context, Cache
   - Real-time percentages and progress bars

5. **RoutingAnalyticsPanel** - Routing decision analytics:
   - Decision matrix (3×3 complexity × tier grid)
   - Accuracy metrics (total decisions, avg time, fallback rate)
   - **MODEL AVAILABILITY WITH BREATHING BARS** (user favorite!):
     - Q2/Q3/Q4 availability progress bars
     - Color-coded: green (100%), amber (50-99%), red (<50%)
     - Pulse animation on critical state

**What to Show:**
- ✅ All time-series data (line charts, bar charts, sparklines)
- ✅ Historical trends (30 min to 24 hour windows)
- ✅ Performance comparisons (tier analysis)
- ✅ System resource analytics (detailed breakdowns)
- ✅ Routing analytics with breathing bars

**Information Philosophy:** "How has the system been performing?"

---

## ModelManagementPage - "Engineering Bay"

**URL:** `/models`

**Purpose:** Manage **individual model lifecycle** and view **per-model metrics**.

**User Questions Answered:**
- Which models are running?
- How is each model performing?
- Can I start/stop/restart a specific model?
- What are the per-model settings?

**Components:**
- **ModelCardGrid** - Responsive grid (3/2/1 columns)
  - Each ModelCard shows:
    - Model name, tier, port, state
    - 3 sparklines per model:
      1. Tokens/sec (20-point history)
      2. Memory usage (20-point history)
      3. Latency (20-point history)
    - Lifecycle controls: Start, Stop, Restart
    - Settings button → ModelSettings dialog

**What to Show:**
- ✅ Per-model metrics and controls
- ✅ Individual performance sparklines
- ✅ Lifecycle management (start/stop/restart)
- ✅ Model-specific configuration

**What NOT to Show:**
- ❌ System-wide aggregates (belong on HomePage/MetricsPage)
- ❌ Cross-tier comparisons (belong on MetricsPage)

**Information Philosophy:** "How do I manage individual models?"

---

## Decision Matrix: Where Does X Belong?

| Feature | HomePage | MetricsPage | ModelManagementPage |
|---------|----------|-------------|---------------------|
| **Current model count** | ✅ Yes | ❌ No | ❌ No |
| **Current query load** | ✅ Yes | ❌ No | ❌ No |
| **Cache hit rate (current)** | ✅ Yes (static) | ✅ Yes (trend) | ❌ No |
| **Queries/sec sparkline** | ❌ No | ✅ Yes | ❌ No |
| **Token gen rate sparkline** | ❌ No | ✅ Yes | ❌ No |
| **Latency trends** | ❌ No | ✅ Yes | ❌ No |
| **Tier performance comparison** | ❌ No | ✅ Yes | ❌ No |
| **System resource grid** | ❌ No | ✅ Yes | ❌ No |
| **Routing decision matrix** | ❌ No | ✅ Yes | ❌ No |
| **Model availability bars** | ❌ No | ✅ Yes | ❌ No |
| **Per-model sparklines** | ❌ No | ❌ No | ✅ Yes |
| **Model lifecycle controls** | ❌ No | ❌ No | ✅ Yes |
| **Query submission** | ✅ Yes | ❌ No | ❌ No |
| **Real-time event feed** | ✅ Yes | ❌ No | ❌ No |
| **Routing visualization** | ✅ Yes | ❌ No | ❌ No |

---

## When to Add a New Feature

**Ask these questions:**

1. **Is it current state or historical trend?**
   - Current state → HomePage
   - Historical trend → MetricsPage

2. **Is it system-wide or per-model?**
   - System-wide → HomePage or MetricsPage
   - Per-model → ModelManagementPage

3. **Does it have a sparkline/chart?**
   - Yes → MetricsPage (or ModelManagementPage if per-model)
   - No → Could be HomePage

4. **Is it essential for query submission?**
   - Yes → HomePage
   - No → Probably MetricsPage or ModelManagementPage

5. **Does it involve time-series data?**
   - Yes → MetricsPage (or ModelManagementPage if per-model)
   - No → Could be HomePage

**Example Decision Tree:**

```
New Feature: "Show FAISS index size over time"
├─ Is it current state or trend? → TREND
├─ Does it have a chart? → YES (time-series)
├─ Is it per-model? → NO (system-wide)
└─ DECISION: Add to MetricsPage → ResourceUtilizationPanel
```

---

## Implementation History

**2025-11-09: UI Consolidation (Phases 1-2)**
- **Phase 1:** Simplified HomePage from 10 metrics → 5 metrics, removed all sparklines
- **Phase 2:** Added SystemHealthOverview to MetricsPage with 4 sparklines
- **Result:** Clear page boundaries, 50% reduction in HomePage clutter, preserved breathing bars

**Files Modified:**
- [SystemStatusPanelEnhanced.tsx](../../frontend/src/components/terminal/SystemStatusPanel/SystemStatusPanelEnhanced.tsx) - Simplified to 5 essential metrics
- [HomePage.tsx](../../frontend/src/pages/HomePage/HomePage.tsx) - Removed metricsHistory dependency
- [SystemHealthOverview.tsx](../../frontend/src/pages/MetricsPage/SystemHealthOverview.tsx) - NEW: Aggregate trends panel
- [MetricsPage.tsx](../../frontend/src/pages/MetricsPage/MetricsPage.tsx) - Added Panel 0 (SystemHealthOverview)

---

## Related Documentation

- [UI_CONSOLIDATION_PLAN.md](../../UI_CONSOLIDATION_PLAN.md) - Implementation plan for page boundaries
- [SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md](../../SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md) - Overall UI roadmap
- [SESSION_NOTES.md](../../SESSION_NOTES.md#2025-11-09) - Recent UI implementation sessions
- [CLAUDE.md](../../CLAUDE.md) - Terminal aesthetic design principles
