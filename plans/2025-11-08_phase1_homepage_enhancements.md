# Phase 1: HomePage Enhancements - Implementation Plan

**Date:** 2025-11-08
**Status:** Ready to Execute
**Duration:** 8-10 hours (5 hours with parallelization)
**Priority:** High
**Phase:** 1 of 4 (UI Enhancement)

---

## Executive Summary

Phase 1 builds on the completed Phase 0 (WebTUI Foundation) to transform the S.Y.N.A.P.S.E. ENGINE HomePage into a dense, NERV-inspired command console. This phase adds:

- Dynamic ASCII banners with phosphor glow (figlet.js integration)
- Expanded system metrics (from 3 to 8+ live metrics with sparklines)
- Orchestrator status visualization showing routing decisions
- Live event feed with 60fps scrolling and color-coded events

**Foundation:** Phase 0 completed all CSS infrastructure with phosphor orange theme (#ff9500), component classes, and validated test page at http://localhost:5173/css-test.

**Outcome:** A production-ready HomePage that displays real-time system state with maximum information density while maintaining terminal aesthetic.

---

## Context & Background

### Current State

**HomePage Status:**
- [HomePage.tsx](../frontend/src/pages/HomePage/HomePage.tsx) exists with basic query interface
- Shows 3 metrics: VRAM, Active Queries, Cache Hit Rate
- Static ASCII banner: `▓▓▓▓ NEURAL SUBSTRATE ORCHESTRATOR ▓▓▓▓`
- No orchestrator visualization
- No event feed
- No sparklines or dense metrics

**Phase 0 Completion:**
- All CSS foundation complete ([TASK_0.5_COMPLETE.md](../TASK_0.5_COMPLETE.md))
- WebTUI CSS integrated with phosphor orange theme
- 31 component classes available (synapse-panel, synapse-metric, synapse-status, etc.)
- Test page validates all classes at http://localhost:5173/css-test
- CSS layer system configured (base → utils → components)

**Docker Environment:**
- All development MUST be in Docker containers
- Frontend rebuild: `docker-compose build --no-cache synapse_frontend`
- Test at http://localhost:5173/
- Environment variables embedded at build time (not runtime)

### Motivation

**User Need:** Engineers monitoring S.Y.N.A.P.S.E. ENGINE need immediate visibility into:
1. System health at a glance (8+ key metrics)
2. Query routing decisions in real-time
3. Model tier utilization patterns
4. Recent system events for debugging

**Design Goal:** NERV-inspired command console with maximum information density:
- Every screen pixel conveys useful data
- Real-time updates at 60fps
- Color-coded for instant comprehension
- Terminal aesthetic maintained throughout

### Technical Constraints

1. **Performance:** All animations must maintain 60fps
2. **Compatibility:** React 19 strict mode, TypeScript strict mode
3. **Theme:** Phosphor orange (#ff9500) primary, cyan accents, pure black background
4. **Responsive:** Mobile, tablet, desktop, wide-screen support
5. **Accessibility:** ARIA labels, keyboard navigation, screen reader support

---

## Agent Consultations

### Agents Selected (Max 3 + Planning Architect)

**Selection Criteria:**
- @terminal-ui-specialist - ASCII art, NERV aesthetics, figlet banners
- @frontend-engineer - React components, TypeScript, TanStack Query integration
- @websocket-realtime-specialist - Live event feed, 60fps updates, WebSocket client

**Why These Three:**
1. **Task 1.1 (Figlet Banner)** - Requires ASCII art expertise (@terminal-ui-specialist)
2. **Tasks 1.2 & 1.3 (Metrics & Orchestrator)** - Standard React components (@frontend-engineer)
3. **Task 1.4 (LiveEventFeed)** - Real-time WebSocket updates (@websocket-realtime-specialist)

**Context Window Management:**
- 3 specialists + 1 planning architect = 4 agents total (well under 6 agent limit)
- Preserves 70%+ context for code and documentation
- Focused expertise for each task type

### @terminal-ui-specialist

**Agent File:** [terminal-ui-specialist.md](../.claude/agents/terminal-ui-specialist.md)

**Query:** "How should we implement the dynamic ASCII banner for S.Y.N.A.P.S.E. ENGINE using figlet.js with phosphor glow animations?"

**Key Insights:**
- Use figlet.js library with 'ANSI Shadow' or 'Doom' fonts for maximum impact
- Implement CSS phosphor glow animations (--phosphor-glow variable)
- Component should accept dynamic text prop for future state-based banners
- Optimize with React.memo to prevent unnecessary re-renders (ASCII generation is expensive)
- Consider WebGL fallback for smoother glow effects on high-end systems
- Add fade-in animation on mount for dramatic entrance

**Implementation Impact:**
- Task 1.1 implementation will follow NERV aesthetic principles
- Reusable FigletBanner component for other pages (Admin, Model Management)
- Performance-optimized to prevent banner re-renders on state changes

### @frontend-engineer

**Agent File:** [frontend-engineer.md](../.claude/agents/frontend-engineer.md)

**Query:** "What's the best approach for expanding SystemStatusPanel from 3 to 8+ metrics with sparklines while maintaining 60fps performance?"

**Key Insights:**
- Use CSS Grid with `synapse-grid--4` for responsive layout (4 cols desktop, 2 tablet, 1 mobile)
- Implement custom useSystemMetrics hook with TanStack Query for data fetching
- Sparklines should use Unicode block characters (▁▂▃▄▅▆▇█) in synapse-sparkline class
- Memoize metric calculations with useMemo to prevent expensive re-computations
- Debounce rapid updates to max 10fps (100ms intervals) to reduce render thrashing
- Use React.memo on MetricCard components to isolate re-renders
- Add aria-label to each metric for screen reader accessibility

**Implementation Impact:**
- Tasks 1.2 and 1.3 will use CSS Grid layout pattern
- MetricCard component will be reusable across HomePage and Admin page
- Performance optimizations prevent UI lag during rapid WebSocket updates

### @websocket-realtime-specialist

**Agent File:** [websocket-realtime-specialist.md](../.claude/agents/websocket-realtime-specialist.md)

**Query:** "How do we implement a LiveEventFeed with 8-event rolling window, color-coded events, and smooth 60fps scrolling?"

**Key Insights:**
- Use resilient WebSocket connection with exponential backoff reconnection
- Implement rolling array with max 8 events (shift oldest when new event arrives)
- Debounce rapid events to 100ms intervals (10fps) for smooth rendering
- Color-code event types with synapse-status classes:
  - Query routing → synapse-status--active (orange)
  - Model state changes → synapse-status--processing (cyan)
  - CGRAG retrievals → synapse-status (default orange)
  - Cache operations → synapse-status--idle (dim orange)
  - Errors → synapse-status--error (red)
- Use CSS transitions for smooth scroll animation (transform: translateY())
- Add timestamp with relative formatting ("2s ago", "1m ago")
- Implement virtual scrolling if event history grows beyond 8 (future enhancement)

**Implementation Impact:**
- Task 1.4 will have robust reconnection logic (no dropped connections)
- Event feed won't overwhelm React with rapid re-renders
- Color coding provides instant visual comprehension of system state

---

## Architecture Overview

### Component Hierarchy

```
HomePage
├── FigletBanner (Task 1.1)
│   ├── figlet.js text rendering
│   └── phosphor-glow animation
├── SystemStatusPanel (Task 1.2 - EXPANDED)
│   ├── 8+ MetricCard components
│   │   ├── Label + Value + Unit
│   │   └── Sparkline (8 data points)
│   └── CSS Grid layout (4 cols → responsive)
├── OrchestratorStatusPanel (Task 1.3 - NEW)
│   ├── Routing decision display
│   ├── Model tier utilization bars (ASCII)
│   ├── Query complexity distribution
│   └── Real-time decision flow
├── LiveEventFeed (Task 1.4 - NEW)
│   ├── WebSocket connection hook
│   ├── 8-event rolling window
│   ├── Color-coded event types
│   └── 60fps smooth scrolling
└── Existing Components (unchanged)
    ├── ModeSelector
    ├── QueryInput
    └── ResponseDisplay
```

### Data Flow

```
Backend WebSocket → Frontend WS Hook → Event State
                                     ↓
                      ┌──────────────┴──────────────┐
                      ↓                             ↓
           LiveEventFeed (events)    SystemStatusPanel (metrics)
                                     ↓
                          OrchestratorStatusPanel (routing stats)

Backend REST API → TanStack Query → Metrics State
                                   ↓
                     SystemStatusPanel (8+ metrics with sparklines)
```

### State Management

**WebSocket Events:**
- Global WebSocket connection in App.tsx or custom context
- useWebSocketEvents hook subscribes to event stream
- Rolling window state: `const [events, setEvents] = useState<SystemEvent[]>([])`
- Max 8 events, FIFO eviction

**System Metrics:**
- TanStack Query with `useSystemMetrics` hook
- Polling interval: 2000ms (0.5 Hz for non-critical metrics)
- Cache time: 5000ms (reduce API load)
- Refetch on window focus (refresh on tab return)

**Orchestrator Stats:**
- Derived from WebSocket events or separate REST endpoint
- Aggregated routing decisions (last 100 queries)
- Model tier utilization percentages

### Integration Points

**Existing APIs:**
- `GET /api/models/status` - Model status (existing, used by SystemStatusPanel)
- `GET /api/metrics/system` - System metrics (NEW endpoint needed)
- `WS /ws/events` - WebSocket event stream (NEW endpoint needed)

**New Components Import:**
```tsx
// HomePage.tsx additions
import { FigletBanner } from '@/components/FigletBanner/FigletBanner';
import { SystemStatusPanel } from '@/components/SystemStatus/SystemStatusPanel';
import { OrchestratorStatusPanel } from '@/components/Orchestrator/OrchestratorStatusPanel';
import { LiveEventFeed } from '@/components/LiveEventFeed/LiveEventFeed';
```

---

## Implementation Plan

### Phase Breakdown

**Wave 1 (Parallel - 3 tasks, ~3 hours):**
- Task 1.1: @terminal-ui-specialist → FigletBanner component
- Task 1.2: @frontend-engineer → Expand SystemStatusPanel
- Task 1.4: @websocket-realtime-specialist → LiveEventFeed component

**Wave 2 (Sequential - 1 task, ~2 hours):**
- Task 1.3: @frontend-engineer → OrchestratorStatusPanel (depends on 1.2 patterns)

**Total Time:**
- Sequential: 10 hours
- Parallelized: ~5 hours (3h Wave 1 + 2h Wave 2)

---

### Task 1.1: Create Figlet Banner Component

**Agent:** @terminal-ui-specialist
**Duration:** 2 hours
**Dependencies:** None (can start immediately)
**Priority:** Medium (visual enhancement)

**Objective:**
Replace static ASCII banner with dynamic figlet.js-generated banner with phosphor glow animation.

**Requirements:**

1. **Install figlet.js:**
   ```bash
   npm install --save figlet
   npm install --save-dev @types/figlet
   ```

2. **Create FigletBanner.tsx:**
   ```tsx
   // /frontend/src/components/FigletBanner/FigletBanner.tsx
   interface FigletBannerProps {
     text: string;
     font?: string; // Default: 'ANSI Shadow'
     animate?: boolean; // Default: true
   }
   ```

3. **Features:**
   - Generate ASCII art from text using figlet.js
   - Apply phosphor-glow CSS animation
   - Support multiple fonts (ANSI Shadow, Doom, Standard)
   - Memoize output to prevent re-generation on parent re-renders
   - Fade-in animation on mount

4. **CSS Classes:**
   - Use `synapse-banner` class (defined in components.css)
   - Add phosphor-glow text-shadow
   - Implement fade-in keyframe animation

5. **Integration:**
   - Replace static banner in HomePage.tsx line 96
   - Text: "S.Y.N.A.P.S.E. ENGINE" or "NEURAL SUBSTRATE"

**Acceptance Criteria:**
- [ ] FigletBanner component created at `/frontend/src/components/FigletBanner/FigletBanner.tsx`
- [ ] figlet.js dependency added to package.json
- [ ] Component accepts `text`, `font`, `animate` props
- [ ] Phosphor glow animation applied (uses --phosphor-glow variable)
- [ ] Integrated into HomePage.tsx
- [ ] Docker rebuild successful
- [ ] Banner displays correctly at http://localhost:5173/
- [ ] No TypeScript errors
- [ ] Component memoized with React.memo

**Files to Create/Modify:**
- ➕ `/frontend/src/components/FigletBanner/FigletBanner.tsx`
- ✏️ `/frontend/package.json` - Add figlet.js dependency
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Replace static banner

---

### Task 1.2: Expand System Status Panel

**Agent:** @frontend-engineer
**Duration:** 3 hours
**Dependencies:** None (can start immediately)
**Priority:** High (critical metrics visibility)

**Objective:**
Upgrade SystemStatusPanel from 3 metrics to 8+ dense metrics with sparklines.

**Current State (HomePage.tsx lines 98-119):**
- 3 metrics: VRAM, Active Queries, Cache Hit Rate
- No sparklines
- No responsive grid
- Inline rendering (no separate component)

**Target State:**
- 8+ metrics in responsive grid (4 cols desktop, 2 tablet, 1 mobile)
- Each metric has sparkline showing 8 recent data points
- Separate SystemStatusPanel component
- Real-time updates via TanStack Query

**Metrics to Add:**

| Metric | Label | Value Format | Unit | Sparkline | Status Color |
|--------|-------|--------------|------|-----------|--------------|
| 1 | QUERIES/SEC | `45.2` | `q/s` | Yes (throughput) | Green if >10 |
| 2 | ACTIVE MODELS | `3/5` | `models` | No | Green if ≥1 |
| 3 | TOKEN GEN RATE | `1248` | `tok/s` | Yes (generation) | Green always |
| 4 | CONTEXT WINDOW | `65%` | `%` | Yes (utilization) | Amber if >80% |
| 5 | CACHE HIT RATE | `72.5%` | `%` | Yes (hit rate) | Green if >70% |
| 6 | CGRAG LATENCY | `52ms` | `ms` | Yes (latency) | Green if <100ms |
| 7 | WS CONNECTIONS | `12` | `conn` | No | Green always |
| 8 | SYSTEM UPTIME | `3d 14h` | `` | No | Green always |

**Requirements:**

1. **Create useSystemMetrics Hook:**
   ```tsx
   // /frontend/src/hooks/useSystemMetrics.ts
   export const useSystemMetrics = () => {
     return useQuery({
       queryKey: ['systemMetrics'],
       queryFn: fetchSystemMetrics,
       refetchInterval: 2000, // 2 second polling
       staleTime: 1000,
     });
   };
   ```

2. **Create MetricCard Component:**
   ```tsx
   // /frontend/src/components/SystemStatus/MetricCard.tsx
   interface MetricCardProps {
     label: string;
     value: string | number;
     unit?: string;
     sparkline?: number[]; // 8 data points
     status?: 'active' | 'idle' | 'warning' | 'error';
   }
   ```

3. **Create SystemStatusPanel Component:**
   ```tsx
   // /frontend/src/components/SystemStatus/SystemStatusPanel.tsx
   export const SystemStatusPanel: React.FC = () => {
     const { data: metrics } = useSystemMetrics();

     return (
       <div className="synapse-panel">
         <div className="synapse-panel__header">SYSTEM STATUS</div>
         <div className="synapse-panel__content">
           <div className="synapse-grid synapse-grid--4">
             {/* 8 MetricCard components */}
           </div>
         </div>
       </div>
     );
   };
   ```

4. **Sparkline Implementation:**
   - Use Unicode block characters: `▁▂▃▄▅▆▇█`
   - Map data points 0-100 → block character index
   - Apply `synapse-sparkline` class
   - Example: `<div className="synapse-sparkline">▁▂▃▅▇█████</div>`

5. **CSS Grid Layout:**
   - Use `synapse-grid synapse-grid--4` for 4-column layout
   - Responsive breakpoints:
     - Desktop (>1280px): 4 columns
     - Tablet (768-1280px): 2 columns
     - Mobile (<768px): 1 column

6. **Performance Optimizations:**
   - Memoize MetricCard with React.memo
   - Debounce rapid metric updates to 100ms (max 10fps)
   - Use useMemo for sparkline character generation

**Acceptance Criteria:**
- [ ] SystemStatusPanel component created at `/frontend/src/components/SystemStatus/SystemStatusPanel.tsx`
- [ ] MetricCard component created at `/frontend/src/components/SystemStatus/MetricCard.tsx`
- [ ] useSystemMetrics hook created at `/frontend/src/hooks/useSystemMetrics.ts`
- [ ] 8+ metrics displayed in responsive grid
- [ ] Sparklines render correctly with Unicode block characters
- [ ] Integrated into HomePage.tsx
- [ ] Docker rebuild successful
- [ ] All metrics visible at http://localhost:5173/
- [ ] No TypeScript errors
- [ ] Grid responsive on mobile/tablet/desktop

**Files to Create/Modify:**
- ➕ `/frontend/src/components/SystemStatus/SystemStatusPanel.tsx`
- ➕ `/frontend/src/components/SystemStatus/MetricCard.tsx`
- ➕ `/frontend/src/hooks/useSystemMetrics.ts`
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Replace inline metrics with SystemStatusPanel

---

### Task 1.3: Create OrchestratorStatusPanel Component

**Agent:** @frontend-engineer
**Duration:** 2 hours
**Dependencies:** Task 1.2 complete (reuses MetricCard pattern)
**Priority:** Medium (monitoring enhancement)

**Objective:**
Create new OrchestratorStatusPanel showing real-time query routing decisions and model tier utilization.

**Target State:**
- Panel showing routing decision stats
- Model tier utilization bars (ASCII horizontal bars)
- Query complexity distribution chart
- Real-time updates as queries are processed

**Requirements:**

1. **Create useOrchestratorStats Hook:**
   ```tsx
   // /frontend/src/hooks/useOrchestratorStats.ts
   export const useOrchestratorStats = () => {
     return useQuery({
       queryKey: ['orchestratorStats'],
       queryFn: fetchOrchestratorStats,
       refetchInterval: 3000, // 3 second polling
       staleTime: 2000,
     });
   };
   ```

2. **Data Structure:**
   ```tsx
   interface OrchestratorStats {
     totalQueries: number;
     routingDecisions: {
       Q2: number; // Count routed to Q2
       Q3: number;
       Q4: number;
     };
     avgComplexityScore: number; // 0-10 scale
     modelUtilization: {
       Q2: number; // Percentage 0-100
       Q3: number;
       Q4: number;
     };
     recentDecisions: Array<{
       timestamp: Date;
       tier: 'Q2' | 'Q3' | 'Q4';
       complexity: number;
       query: string; // First 50 chars
     }>;
   }
   ```

3. **Create OrchestratorStatusPanel Component:**
   ```tsx
   // /frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx
   export const OrchestratorStatusPanel: React.FC = () => {
     const { data: stats } = useOrchestratorStats();

     return (
       <div className="synapse-panel">
         <div className="synapse-panel__header">ORCHESTRATOR STATUS</div>
         <div className="synapse-panel__content">
           {/* Routing distribution chart */}
           {/* Model utilization bars */}
           {/* Recent decisions list */}
         </div>
       </div>
     );
   };
   ```

4. **ASCII Utilization Bars:**
   ```tsx
   // Example for Q2 tier at 65% utilization
   const renderUtilizationBar = (label: string, percent: number) => (
     <div className="synapse-metric">
       <div className="synapse-metric__label">{label}</div>
       <div className="synapse-chart">
         Q2 ████████████████████░░░░░░░░ 65%
       </div>
     </div>
   );
   ```

5. **Complexity Distribution:**
   - Show breakdown of query complexity: Simple / Moderate / Complex
   - Use ASCII bar chart with box-drawing characters
   - Example:
   ```
   COMPLEXITY DISTRIBUTION
   Simple   ████████████████████ 45%
   Moderate ████████████░░░░░░░░ 35%
   Complex  ████░░░░░░░░░░░░░░░░ 20%
   ```

6. **Recent Decisions:**
   - Display last 3 routing decisions
   - Format: `[2s ago] Q3 (complexity: 6.2) "Explain async patterns..."`
   - Use `synapse-status` classes for tier badges

**Acceptance Criteria:**
- [ ] OrchestratorStatusPanel component created at `/frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx`
- [ ] useOrchestratorStats hook created at `/frontend/src/hooks/useOrchestratorStats.ts`
- [ ] Routing distribution chart displays correctly
- [ ] Model utilization bars render as ASCII bars
- [ ] Recent decisions list shows last 3 decisions
- [ ] Integrated into HomePage.tsx
- [ ] Docker rebuild successful
- [ ] Panel visible at http://localhost:5173/
- [ ] No TypeScript errors
- [ ] Real-time updates working (3s polling)

**Files to Create/Modify:**
- ➕ `/frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx`
- ➕ `/frontend/src/hooks/useOrchestratorStats.ts`
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Add OrchestratorStatusPanel

---

### Task 1.4: Implement LiveEventFeed Component

**Agent:** @websocket-realtime-specialist
**Duration:** 3 hours
**Dependencies:** None (can start immediately)
**Priority:** High (real-time system visibility)

**Objective:**
Create LiveEventFeed component showing rolling 8-event window with color-coded events and 60fps smooth scrolling.

**Requirements:**

1. **Create useWebSocketEvents Hook:**
   ```tsx
   // /frontend/src/hooks/useWebSocketEvents.ts
   export const useWebSocketEvents = () => {
     const [events, setEvents] = useState<SystemEvent[]>([]);
     const [connected, setConnected] = useState(false);

     useEffect(() => {
       const ws = new WebSocket('ws://localhost:8000/ws/events');

       ws.onopen = () => setConnected(true);
       ws.onmessage = (event) => {
         const newEvent = JSON.parse(event.data);
         setEvents(prev => {
           const updated = [newEvent, ...prev];
           return updated.slice(0, 8); // Keep only 8 most recent
         });
       };
       ws.onclose = () => {
         setConnected(false);
         // Reconnect logic with exponential backoff
       };

       return () => ws.close();
     }, []);

     return { events, connected };
   };
   ```

2. **Event Types:**
   ```tsx
   interface SystemEvent {
     id: string;
     timestamp: Date;
     type: 'query_routing' | 'model_state' | 'cgrag_retrieval' | 'cache_op' | 'error' | 'performance_alert';
     message: string;
     metadata?: Record<string, any>;
   }
   ```

3. **Color Coding:**
   ```tsx
   const getEventClass = (type: SystemEvent['type']) => {
     switch (type) {
       case 'query_routing': return 'synapse-status--active'; // Orange
       case 'model_state': return 'synapse-status--processing'; // Cyan
       case 'cgrag_retrieval': return 'synapse-status'; // Default orange
       case 'cache_op': return 'synapse-status--idle'; // Dim orange
       case 'error': return 'synapse-status--error'; // Red
       case 'performance_alert': return 'synapse-status--warning'; // Amber
     }
   };
   ```

4. **Create LiveEventFeed Component:**
   ```tsx
   // /frontend/src/components/LiveEventFeed/LiveEventFeed.tsx
   export const LiveEventFeed: React.FC = () => {
     const { events, connected } = useWebSocketEvents();

     return (
       <div className="synapse-panel">
         <div className="synapse-panel__header">
           LIVE EVENT FEED
           <span className={`synapse-status synapse-status--${connected ? 'active' : 'error'}`}>
             {connected ? 'CONNECTED' : 'DISCONNECTED'}
           </span>
         </div>
         <div className="synapse-panel__content">
           {events.map(event => (
             <div key={event.id} className="event-item">
               <span className={getEventClass(event.type)}>{event.type.toUpperCase()}</span>
               <span className="event-time">{formatRelativeTime(event.timestamp)}</span>
               <span className="event-message">{event.message}</span>
             </div>
           ))}
         </div>
       </div>
     );
   };
   ```

5. **Smooth Scrolling:**
   - Use CSS transitions for new event insertion
   - Transform-based animation (translateY) for GPU acceleration
   - Fade-in animation for new events (opacity 0 → 1)

6. **Timestamp Formatting:**
   ```tsx
   const formatRelativeTime = (timestamp: Date) => {
     const seconds = Math.floor((Date.now() - timestamp.getTime()) / 1000);
     if (seconds < 60) return `${seconds}s ago`;
     const minutes = Math.floor(seconds / 60);
     if (minutes < 60) return `${minutes}m ago`;
     const hours = Math.floor(minutes / 60);
     return `${hours}h ago`;
   };
   ```

7. **Reconnection Logic:**
   - Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
   - Visual indicator when disconnected (red DISCONNECTED badge)
   - Auto-reconnect on connection drop

**Acceptance Criteria:**
- [ ] LiveEventFeed component created at `/frontend/src/components/LiveEventFeed/LiveEventFeed.tsx`
- [ ] useWebSocketEvents hook created at `/frontend/src/hooks/useWebSocketEvents.ts`
- [ ] Rolling 8-event window implemented (FIFO eviction)
- [ ] Color-coded event types working (6 event types)
- [ ] Smooth 60fps scrolling animation
- [ ] Relative timestamp formatting ("2s ago", "5m ago")
- [ ] WebSocket reconnection logic with exponential backoff
- [ ] Connection status indicator (CONNECTED/DISCONNECTED)
- [ ] Integrated into HomePage.tsx
- [ ] Docker rebuild successful
- [ ] Feed visible at http://localhost:5173/
- [ ] No TypeScript errors

**Files to Create/Modify:**
- ➕ `/frontend/src/components/LiveEventFeed/LiveEventFeed.tsx`
- ➕ `/frontend/src/hooks/useWebSocketEvents.ts`
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Add LiveEventFeed

---

## HomePage Integration Strategy

### Current HomePage Layout

```tsx
// /frontend/src/pages/HomePage/HomePage.tsx (current)
<div className={styles.page}>
  <div className={styles.header}>
    <h1>▓▓▓▓ NEURAL SUBSTRATE ORCHESTRATOR ▓▓▓▓</h1>
    <div className={styles.systemStatus}>
      {/* 3 inline metrics: VRAM, QUERIES, CACHE */}
    </div>
  </div>

  <div className={styles.content}>
    <ModeSelector />
    <QueryInput />
    <ResponseDisplay />
  </div>

  <QuickActions />
</div>
```

### Target HomePage Layout

```tsx
// /frontend/src/pages/HomePage/HomePage.tsx (Phase 1)
<div className={styles.page}>
  {/* Task 1.1: Dynamic ASCII Banner */}
  <FigletBanner text="S.Y.N.A.P.S.E. ENGINE" font="ANSI Shadow" />

  {/* Task 1.2: Expanded System Metrics (8+ metrics with sparklines) */}
  <SystemStatusPanel />

  {/* Two-column grid: Orchestrator + Event Feed */}
  <div className="synapse-grid synapse-grid--2">
    {/* Task 1.3: Orchestrator Visualization */}
    <OrchestratorStatusPanel />

    {/* Task 1.4: Live Event Feed */}
    <LiveEventFeed />
  </div>

  {/* Existing Components (unchanged) */}
  <div className={styles.content}>
    <ModeSelector />
    <QueryInput />
    <ResponseDisplay />
  </div>

  <QuickActions />
</div>
```

### Integration Steps

1. **Add Imports (top of HomePage.tsx):**
   ```tsx
   import { FigletBanner } from '@/components/FigletBanner/FigletBanner';
   import { SystemStatusPanel } from '@/components/SystemStatus/SystemStatusPanel';
   import { OrchestratorStatusPanel } from '@/components/Orchestrator/OrchestratorStatusPanel';
   import { LiveEventFeed } from '@/components/LiveEventFeed/LiveEventFeed';
   ```

2. **Replace Static Banner (line 95-97):**
   ```tsx
   // OLD
   <h1 className={styles.title}>
     ▓▓▓▓ NEURAL SUBSTRATE ORCHESTRATOR ▓▓▓▓
   </h1>

   // NEW
   <FigletBanner text="S.Y.N.A.P.S.E. ENGINE" />
   ```

3. **Replace Inline Metrics (lines 98-119):**
   ```tsx
   // OLD
   <div className={styles.systemStatus}>
     <MetricDisplay label="VRAM" ... />
     <MetricDisplay label="QUERIES" ... />
     <MetricDisplay label="CACHE" ... />
   </div>

   // NEW
   <SystemStatusPanel />
   ```

4. **Add New Panels (after SystemStatusPanel):**
   ```tsx
   <div className="synapse-grid synapse-grid--2">
     <OrchestratorStatusPanel />
     <LiveEventFeed />
   </div>
   ```

5. **Rebuild and Test:**
   ```bash
   docker-compose build --no-cache synapse_frontend
   docker-compose up -d synapse_frontend
   docker-compose logs -f synapse_frontend
   # Open http://localhost:5173/
   ```

---

## Risks & Mitigation

### Risk 1: figlet.js Bundle Size

**Risk:** figlet.js with all fonts could add 200KB+ to bundle size.

**Mitigation:**
- Import only required fonts (ANSI Shadow, Doom)
- Use dynamic import for lazy loading: `const figlet = await import('figlet')`
- Consider font subsetting or custom ASCII art generation for production

**Impact:** Low (acceptable bundle increase for dramatic visual impact)

### Risk 2: WebSocket Backend Not Implemented

**Risk:** Task 1.4 requires `WS /ws/events` endpoint which may not exist yet.

**Mitigation:**
- Frontend component can be built and tested with mock data
- Use mock WebSocket server for development testing
- Phase 1 focuses on frontend; backend WebSocket can be Phase 2 task
- Gracefully handle missing WebSocket (show "DISCONNECTED" state)

**Impact:** Medium (component can be tested with mocks)

### Risk 3: 60fps Performance with Rapid Updates

**Risk:** WebSocket firing 60 events/sec could overwhelm React rendering.

**Mitigation:**
- Debounce updates to max 10fps (100ms intervals)
- Use React.memo on all components to prevent unnecessary re-renders
- Implement virtual scrolling if event volume exceeds 8 events
- Monitor performance with Chrome DevTools Performance tab

**Impact:** Low (debouncing prevents render thrashing)

### Risk 4: Docker Rebuild Time

**Risk:** Each code change requires Docker rebuild (~2-3 minutes).

**Mitigation:**
- Use `.dockerignore` to exclude unnecessary files from build context
- Multi-stage Docker build with cached layers
- Develop components in isolation first, then integrate
- Consider hot-reload for development (Vite HMR in Docker)

**Impact:** Medium (rebuild time is development friction)

### Risk 5: TypeScript Strict Mode Errors

**Risk:** React 19 strict mode + TypeScript strict mode may cause type errors.

**Mitigation:**
- All components must have explicit type definitions
- Use `interface` for props, avoid `any` types
- Test with strict mode enabled from start
- Reference existing components (HomePage, CSSTestPage) for patterns

**Impact:** Low (strict typing is project standard)

---

## Reference Documentation

**Related Documents:**
- [SESSION_NOTES.md](../SESSION_NOTES.md) - Recent development context
- [TASK_0.5_COMPLETE.md](../TASK_0.5_COMPLETE.md) - Phase 0 completion report
- [CLAUDE.md](../CLAUDE.md) - Project guidelines and constraints
- [docker-compose.yml](../docker-compose.yml) - Frontend build configuration

**CSS Foundation:**
- [WEBTUI_INTEGRATION_GUIDE.md](../docs/WEBTUI_INTEGRATION_GUIDE.md) - CSS integration patterns
- [WEBTUI_STYLE_GUIDE.md](../docs/WEBTUI_STYLE_GUIDE.md) - Component styling guide
- [frontend/src/assets/styles/components.css](../frontend/src/assets/styles/components.css) - 31 component classes

**Agent Specifications:**
- [terminal-ui-specialist.md](../.claude/agents/terminal-ui-specialist.md) - ASCII art and NERV aesthetics
- [frontend-engineer.md](../.claude/agents/frontend-engineer.md) - React/TypeScript components
- [websocket-realtime-specialist.md](../.claude/agents/websocket-realtime-specialist.md) - WebSocket real-time updates

**Test Page:**
- http://localhost:5173/css-test - CSS component validation page

---

## Definition of Done

Phase 1 is complete when ALL of these criteria are met:

**Component Creation:**
- [ ] FigletBanner component exists at `/frontend/src/components/FigletBanner/FigletBanner.tsx`
- [ ] SystemStatusPanel component exists at `/frontend/src/components/SystemStatus/SystemStatusPanel.tsx`
- [ ] MetricCard component exists at `/frontend/src/components/SystemStatus/MetricCard.tsx`
- [ ] OrchestratorStatusPanel component exists at `/frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx`
- [ ] LiveEventFeed component exists at `/frontend/src/components/LiveEventFeed/LiveEventFeed.tsx`

**Hook Creation:**
- [ ] useSystemMetrics hook exists at `/frontend/src/hooks/useSystemMetrics.ts`
- [ ] useOrchestratorStats hook exists at `/frontend/src/hooks/useOrchestratorStats.ts`
- [ ] useWebSocketEvents hook exists at `/frontend/src/hooks/useWebSocketEvents.ts`

**HomePage Integration:**
- [ ] FigletBanner integrated and displays dynamic ASCII art
- [ ] SystemStatusPanel shows 8+ metrics with sparklines
- [ ] OrchestratorStatusPanel shows routing stats and utilization bars
- [ ] LiveEventFeed shows rolling 8-event window with color coding
- [ ] All components maintain phosphor orange theme (#ff9500)

**Visual & Performance:**
- [ ] Figlet banner has phosphor glow animation
- [ ] System metrics display sparklines (Unicode block characters)
- [ ] Orchestrator shows ASCII utilization bars
- [ ] Event feed scrolls smoothly at 60fps
- [ ] All animations run at 60fps (no janky updates)
- [ ] Responsive layout works on mobile/tablet/desktop/wide

**Technical Quality:**
- [ ] No TypeScript errors in any file
- [ ] All components have strict type definitions
- [ ] React.memo applied to prevent unnecessary re-renders
- [ ] ARIA labels added for accessibility
- [ ] WebSocket reconnection logic working (exponential backoff)

**Docker & Build:**
- [ ] `docker-compose build --no-cache synapse_frontend` succeeds
- [ ] `docker-compose up -d synapse_frontend` starts container
- [ ] No build errors or warnings
- [ ] No console errors at http://localhost:5173/

**Documentation:**
- [ ] SESSION_NOTES.md updated with Phase 1 completion
- [ ] All file changes documented with line numbers
- [ ] Agent consultations documented
- [ ] Next steps documented (Phase 2 preparation)

---

## Next Actions

### Immediate (Post-Approval)

1. **Wave 1 Launch (Parallel Execution):**
   - Agent 1: @terminal-ui-specialist → Task 1.1 (FigletBanner)
   - Agent 2: @frontend-engineer → Task 1.2 (SystemStatusPanel)
   - Agent 3: @websocket-realtime-specialist → Task 1.4 (LiveEventFeed)

2. **Wave 1 Validation:**
   - Rebuild Docker container: `docker-compose build --no-cache synapse_frontend`
   - Test each component in isolation
   - Verify no TypeScript errors
   - Check component rendering at http://localhost:5173/

3. **Wave 2 Launch (Sequential Execution):**
   - Agent: @frontend-engineer → Task 1.3 (OrchestratorStatusPanel)
   - Reuses patterns from Task 1.2 (MetricCard, CSS Grid)

4. **Final Integration:**
   - Integrate all 4 components into HomePage.tsx
   - Full rebuild and test
   - Verify responsive behavior (mobile/tablet/desktop)
   - Run complete testing checklist

### Follow-Up (Phase 2 Preparation)

1. **Backend API Development:**
   - Implement `GET /api/metrics/system` endpoint for SystemStatusPanel
   - Implement `GET /api/orchestrator/stats` endpoint for OrchestratorStatusPanel
   - Implement `WS /ws/events` WebSocket endpoint for LiveEventFeed
   - Add mock data generators for development testing

2. **Performance Profiling:**
   - Use Chrome DevTools Performance tab to measure frame rate
   - Identify any render bottlenecks
   - Optimize heavy components with useMemo/useCallback
   - Verify WebSocket debouncing is working (max 10fps)

3. **Accessibility Audit:**
   - Test with screen reader (macOS VoiceOver)
   - Verify keyboard navigation works for all components
   - Check ARIA labels are descriptive
   - Test color contrast for accessibility (WCAG AA compliance)

4. **Documentation:**
   - Update SESSION_NOTES.md with Phase 1 completion details
   - Document any performance optimizations applied
   - Add screenshots to documentation
   - Update CLAUDE.md if new patterns discovered

---

## Estimated Effort

**Time Breakdown (Sequential):**
- Task 1.1 (FigletBanner): 2 hours
- Task 1.2 (SystemStatusPanel): 3 hours
- Task 1.3 (OrchestratorStatusPanel): 2 hours
- Task 1.4 (LiveEventFeed): 3 hours
- **Total:** 10 hours

**Time Breakdown (Parallelized):**
- Wave 1 (Tasks 1.1, 1.2, 1.4): 3 hours (max of 2h, 3h, 3h)
- Wave 2 (Task 1.3): 2 hours
- **Total:** 5 hours

**Confidence Level:**
- Wave 1: High (85%) - Independent tasks, well-defined requirements
- Wave 2: High (90%) - Reuses patterns from Wave 1
- Integration: Medium (75%) - Some unknowns with HomePage layout adjustments

**Risk Buffer:** +20% (1 hour) for unexpected TypeScript errors or Docker issues

**Total Estimated Time:** 5-6 hours with parallelization, 10-12 hours sequential

---

## Files Summary

### New Files Created (8 files)

**Components:**
- `/frontend/src/components/FigletBanner/FigletBanner.tsx`
- `/frontend/src/components/SystemStatus/SystemStatusPanel.tsx`
- `/frontend/src/components/SystemStatus/MetricCard.tsx`
- `/frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx`
- `/frontend/src/components/LiveEventFeed/LiveEventFeed.tsx`

**Hooks:**
- `/frontend/src/hooks/useSystemMetrics.ts`
- `/frontend/src/hooks/useOrchestratorStats.ts`
- `/frontend/src/hooks/useWebSocketEvents.ts`

### Modified Files (2 files)

- ✏️ `/frontend/package.json` - Add figlet.js dependency
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Integrate all 4 new components

### Total Files: 10 files (8 new, 2 modified)

---

**Date:** 2025-11-08
**Status:** Ready to Execute
**Phase:** 1 of 4 → Ready for Phase 2

**Approval Required:** Please confirm to begin Wave 1 parallel execution.
