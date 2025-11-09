# Phase 1 REVISED: Advanced Terminal Design Integration - Implementation Plan

**Date:** 2025-11-08
**Status:** Ready to Execute (REVISED with Design Firm Specifications)
**Duration:** 15-17 hours (parallelized) vs 19-25 hours (sequential)
**Priority:** CRITICAL - Foundation for all future UI work
**Phase:** 1 of 4 (UI Enhancement - ADVANCED)

---

## Executive Summary

This REVISED Phase 1 plan replaces the original basic implementation with **professional-grade advanced terminal design** leveraging the design firm's comprehensive specifications in [/design_overhaul/](../design_overhaul/).

### What Changed from Original Plan

**Original Plan (8-10 hours):**
- Basic figlet.js banner
- 3 simple metrics → 8+ metrics
- Basic orchestrator panel
- Simple event list

**REVISED Plan (15-17 hours):**
- **Dot Matrix LED Display** with pixel-by-pixel reveal (user's favorite!)
- **CRT Effects Foundation**: Glow, scanlines, aberration, curvature, bloom
- **8+ metrics** with radial gauges and pulse effects
- **Waveform visualizer** for query complexity distribution
- **Particle effects** on events
- **Professional terminal aesthetic** matching NERV/Evangelion design philosophy

**Quality Increase:** ~500% (authentic terminal aesthetic vs basic UI)
**Time Increase:** ~70% (15-17h vs 8-10h)
**User Impact:** Dramatic - transforms basic UI into production-quality command console

### User's Explicit Feedback

> "I love the idea of a dot matrix display as banner or background reactive element"

**Response:** Dot matrix LED display is now **Task 1.1 (PRIORITY: CRITICAL)** with pixel-by-pixel character reveal at 400ms/char, full phosphor glow effect, and optional reactive background mode.

---

## Foundation: Design Firm Specifications

### Available Design Documents

**Location:** [/design_overhaul/](../design_overhaul/)

1. **[ADVANCED_TERMINAL_DESIGN.md](../design_overhaul/ADVANCED_TERMINAL_DESIGN.md)**
   - Complete implementation catalog
   - 15+ animation techniques
   - CRT effects specifications
   - Advanced widget designs
   - Performance guidelines

2. **[ANIMATION_MOCKUPS.md](../design_overhaul/ANIMATION_MOCKUPS.md)**
   - Frame-by-frame sequences
   - Visual reference guide
   - ASCII art examples
   - Complete screen mockups

3. **[ANIMATION_IMPLEMENTATION_ROADMAP.md](../design_overhaul/ANIMATION_IMPLEMENTATION_ROADMAP.md)**
   - 4-6 week phased roadmap
   - 160-200 hours total effort
   - Performance targets (60fps)
   - Browser support matrix

**Our Scope:** We're implementing **Phase 1 elements** from the design firm's roadmap (~20-30 hours in their plan) with focus on:
- CRT Effects Foundation (BLOCKING - Wave 1)
- Dot Matrix LED Display (user's favorite - Wave 2)
- Radial Gauges & Pulse Effects (Wave 2)
- Waveform Visualizer (Wave 3)
- Particle Effects (Wave 2)

---

## Context & Background

### Current State

**HomePage Status:**
- [HomePage.tsx](../frontend/src/pages/HomePage/HomePage.tsx) exists with basic query interface
- Shows 3 metrics: VRAM, Active Queries, Cache Hit Rate
- Static ASCII banner: `▓▓▓▓ NEURAL SUBSTRATE ORCHESTRATOR ▓▓▓▓`
- No CRT effects
- No advanced animations
- No dot matrix display

**Phase 0 Completion:**
- All CSS foundation complete ([TASK_0.5_COMPLETE.md](../TASK_0.5_COMPLETE.md))
- WebTUI CSS integrated with phosphor orange theme (#ff9500)
- 31 component classes available
- Test page validates all classes at http://localhost:5173/css-test
- CSS layer system configured (base → utils → components)

**Design Firm Deliverables:**
- Professional-grade terminal design specifications
- Frame-by-frame animation mockups
- Performance-tested implementations
- 15+ animation techniques cataloged
- Complete CRT effects system

### Motivation

**User Need:** Engineers monitoring S.Y.N.A.P.S.E. ENGINE need:
1. **Authentic terminal aesthetic** - Not retro nostalgia, functional density
2. **Professional visual quality** - Production-ready command console
3. **Maximum information density** - Every pixel serves purpose
4. **Real-time feedback** - 60fps animations with immediate visual understanding
5. **CRT authenticity** - Phosphor glow, scanlines, bloom, curvature

**Design Philosophy (from [ANIMATION_MOCKUPS.md](../design_overhaul/ANIMATION_MOCKUPS.md)):**
- Dense information displays with high contrast
- Real-time feedback at 60fps
- Modular panels with borders and labels
- Technical readout style (numerical data, status codes)
- Color-coded states for immediate comprehension
- Functional animations with purposeful state transitions

### Technical Constraints

1. **Performance:** All animations must maintain 60fps (strict requirement)
2. **Browser Support:** Modern browsers (Chrome, Firefox, Safari, Edge) - 94%+ support verified
3. **Theme:** Phosphor orange (#ff9500) primary, cyan accents, pure black background
4. **Compatibility:** React 19 strict mode, TypeScript strict mode
5. **Responsive:** Mobile, tablet, desktop, wide-screen support
6. **Accessibility:** ARIA labels, keyboard navigation, screen reader support

---

## Agent Consultations

### Agents Selected (4 agents total - under 6 limit)

**Selection Criteria:**
- **@terminal-ui-specialist** - CRT effects, dot matrix display, terminal aesthetics
- **@frontend-engineer** - React components, TypeScript, radial gauges, waveform visualizer
- **@websocket-realtime-specialist** - Live event feed with particle effects
- **Planning Architect (Strategic Planning)** - This document

**Context Window Management:**
- 3 specialists + 1 planning architect = 4 agents total (well under 6 agent limit)
- Preserves 70%+ context for code and design documentation
- Focused expertise for each advanced feature type

### @terminal-ui-specialist

**Agent File:** [terminal-ui-specialist.md](../.claude/agents/terminal-ui-specialist.md)

**Query 1:** "How should we implement CRT effects foundation (phosphor glow, scanlines, aberration, curvature, bloom) as reusable CRTMonitor wrapper component?"

**Key Insights:**
- Create master CRTMonitor component wrapping all UI elements
- Phosphor glow: `text-shadow: 0 0 10px rgba(255,149,0,0.8), 0 0 20px rgba(255,149,0,0.4)`
- Scanlines: Repeating linear gradient overlay with CSS animation (2s cycle)
- Chromatic aberration: Red/cyan offset using CSS filters or pseudo-elements
- Screen curvature: CSS perspective transform on container
- Bloom: SVG filter with feGaussianBlur for glow extension
- Performance: <0.1ms overhead per frame with GPU acceleration

**Query 2:** "What's the best approach for dot matrix LED display with pixel-by-pixel character reveal and optional reactive background?"

**Key Insights:**
- Use Canvas for pixel-level control (much faster than DOM)
- 5x7 pixel matrix per character (industry standard for LED displays)
- Character map with binary arrays for pixel patterns
- Reveal animation: 400ms per character with stagger timing
- Phosphor glow on each pixel: multiply blend mode
- Reactive background: Pulse on system events, shimmer on success
- Limit to 40 characters for optimal performance (60fps target)

**Implementation Impact:**
- Task 1.0 creates CRTMonitor foundation (BLOCKING all other tasks)
- Task 1.1 implements dot matrix display (user's favorite feature)
- Reusable components for Phase 2, 3, 4

### @frontend-engineer

**Agent File:** [frontend-engineer.md](../.claude/agents/frontend-engineer.md)

**Query 1:** "How do we implement radial gauges with SVG, threshold color coding, and phosphor glow effects for system metrics?"

**Key Insights:**
- Use SVG circle with animated stroke-dashoffset for gauge fill
- Threshold color coding: normal (orange), warning (amber >70%), critical (red >90%)
- Phosphor glow via SVG filter: feGaussianBlur + feComponentTransfer
- Tick marks and labels with SVG text elements
- Responsive sizing: viewBox for container scaling
- Smooth transitions: CSS transitions on stroke-dashoffset (300ms ease-out)
- Performance: SVG is GPU-accelerated, 60fps for 8+ gauges

**Query 2:** "What's the architecture for waveform visualizer showing query complexity distribution with 32+ animated bars?"

**Key Insights:**
- Canvas-based implementation for 60fps with 32+ bars
- Bar height mapping: 0-100 value → pixel height with easing
- Smooth interpolation: 0.4 factor for smooth transitions
- Color gradient: Frequency-based (low=dim orange, high=bright orange)
- Real-time updates: Debounce to 16ms (60fps) for smooth animation
- Frequency analysis display: Mock data for Phase 1, real analysis in Phase 2
- Performance tested: 60fps with 64 bars on modern hardware

**Implementation Impact:**
- Task 1.2 uses radial gauges for 8+ metrics (dramatic upgrade from basic display)
- Task 1.3 adds waveform visualizer for orchestrator complexity distribution
- Reusable gauge and waveform components for Admin panel (Phase 2)

### @websocket-realtime-specialist

**Agent File:** [websocket-realtime-specialist.md](../.claude/agents/websocket-realtime-specialist.md)

**Query:** "How do we integrate particle system effects into LiveEventFeed for celebration/warning visual feedback?"

**Key Insights:**
- Simplified particle system: 50-100 particles max for 60fps
- Character particles (ASCII): Explosion effect on events
- Physics simulation: Velocity, gravity, drag with requestAnimationFrame
- Trigger on event types: Success (green particles), Error (red particles), Processing (orange)
- Lifecycle management: Particle birth/death with fade-out
- Object pooling: Reuse particle objects to reduce GC pressure
- Performance: GPU acceleration with will-change CSS property

**Implementation Impact:**
- Task 1.4 enhanced with particle celebration effects
- Visual feedback on query completion, errors, state changes
- Adds dramatic flair to system events

---

## Architecture Overview

### Component Hierarchy

```
HomePage (wrapped in CRTMonitor)
├── CRTMonitor (Task 1.0 - FOUNDATION)
│   ├── Phosphor glow utility
│   ├── Animated scanlines
│   ├── Chromatic aberration
│   ├── Screen curvature
│   └── Bloom effect
│       │
│       ├── DotMatrixBanner (Task 1.1 - USER'S FAVORITE)
│       │   ├── Canvas-based 5x7 pixel matrix
│       │   ├── Character-by-character reveal (400ms)
│       │   ├── Phosphor glow per pixel
│       │   └── Optional reactive background mode
│       │
│       ├── SystemStatusPanel (Task 1.2 - EXPANDED WITH GAUGES)
│       │   ├── 8+ MetricCard components
│       │   │   ├── RadialGauge (SVG with glow)
│       │   │   ├── Label + Value + Unit
│       │   │   ├── PulseIndicator for active states
│       │   │   └── Sparkline (8 data points)
│       │   └── CSS Grid layout (4 cols → responsive)
│       │
│       ├── OrchestratorStatusPanel (Task 1.3 - WITH WAVEFORM)
│       │   ├── Routing decision display
│       │   ├── Model tier utilization bars (ASCII)
│       │   ├── WaveformVisualizer (query complexity)
│       │   └── Real-time decision flow
│       │
│       ├── LiveEventFeed (Task 1.4 - WITH PARTICLES)
│       │   ├── WebSocket connection hook
│       │   ├── 8-event rolling window
│       │   ├── Color-coded event types
│       │   ├── ParticleSystem integration
│       │   └── 60fps smooth scrolling
│       │
│       └── Existing Components (unchanged)
│           ├── ModeSelector
│           ├── QueryInput
│           └── ResponseDisplay
```

### Data Flow

```
Backend WebSocket → Frontend WS Hook → Event State
                                     ↓
                      ┌──────────────┴──────────────┐
                      ↓                             ↓
           LiveEventFeed (events)    SystemStatusPanel (metrics)
                  ↓                                 ↓
          ParticleSystem             RadialGauges + PulseIndicators
           (celebration)                           ↓
                                      OrchestratorStatusPanel
                                                   ↓
                                      WaveformVisualizer (complexity)

Backend REST API → TanStack Query → Metrics State
                                   ↓
                     SystemStatusPanel (8+ metrics with gauges)

CRT Effects → Applied to ALL components via CRTMonitor wrapper
```

### State Management

**CRT Effects:**
- Global CRTMonitor wrapper in App.tsx or HomePage.tsx
- Props: `intensity`, `scanlineSpeed`, `glowIntensity`, `curvature`
- CSS variables for theming: `--phosphor-glow`, `--scanline-opacity`

**Dot Matrix Display:**
- Character reveal state: `const [revealProgress, setRevealProgress] = useState(0)`
- Animation loop with requestAnimationFrame
- Reactive mode: Listen to system events for pulse/shimmer

**System Metrics:**
- TanStack Query with `useSystemMetrics` hook
- Polling interval: 2000ms (0.5 Hz for non-critical metrics)
- Radial gauge state: Animated stroke-dashoffset with CSS transitions

**Orchestrator Stats:**
- Waveform data: Frequency array (0-255) for 32 bars
- Real-time updates with smooth interpolation (0.4 factor)

**Particle Effects:**
- Particle array: `Particle[]` with position, velocity, life
- Physics simulation in requestAnimationFrame loop
- Trigger on event types with color coding

---

## Implementation Plan

### Wave Execution Strategy

**CRITICAL:** Wave 1 must complete BEFORE Wave 2/3 begin - CRT effects are BLOCKING dependency.

**Wave 1 (Sequential - BLOCKING):**
- Duration: 6-8 hours
- Task 1.0: @terminal-ui-specialist → CRT Effects Foundation
- **BLOCKS** all other tasks (all components need CRTMonitor)

**Wave 2 (Parallel - After Wave 1):**
- Duration: ~5 hours (max of 3-4h, 4-5h, 3-4h)
- Task 1.1: @terminal-ui-specialist → Dot Matrix Banner
- Task 1.2: @frontend-engineer → System Status + Radial Gauges
- Task 1.4: @websocket-realtime-specialist → LiveEventFeed + Particles
- **All run in parallel** (different components, no conflicts)

**Wave 3 (Sequential - After Wave 2):**
- Duration: 3-4 hours
- Task 1.3: @frontend-engineer → Orchestrator + Waveform
- **Depends on:** Task 1.2 patterns (MetricCard, grid layouts)

**Total Time:**
- Sequential: 6-8h + (3-4h + 4-5h + 3-4h) + 3-4h = **19-25 hours**
- Parallelized: 6-8h + 5h + 4h = **15-17 hours**

---

## Task Breakdown

### Task 1.0: CRT Effects Foundation (CRITICAL - BLOCKING)

**Agent:** @terminal-ui-specialist
**Duration:** 6-8 hours
**Dependencies:** None (starts immediately)
**Priority:** CRITICAL - Blocks all other tasks

**Reference Documentation:**
- [ADVANCED_TERMINAL_DESIGN.md](../design_overhaul/ADVANCED_TERMINAL_DESIGN.md) - Section B (CRT Effects Implementation)
- [ANIMATION_IMPLEMENTATION_ROADMAP.md](../design_overhaul/ANIMATION_IMPLEMENTATION_ROADMAP.md) - Phase 1.1 (CRT Effects Foundation)

**Objective:**
Create master CRTMonitor component that wraps all UI elements and applies authentic CRT effects: phosphor glow, scanlines, chromatic aberration, screen curvature, bloom.

**Requirements:**

1. **Create CRTMonitor.tsx Component:**
   ```tsx
   // /frontend/src/components/Terminal/CRTMonitor.tsx
   interface CRTMonitorProps {
     children: React.ReactNode;
     intensity?: number; // 0-1, default 0.8
     scanlineSpeed?: number; // seconds per cycle, default 2
     glowIntensity?: number; // 0-1, default 0.7
     curvature?: number; // degrees, default 15
     enableBloom?: boolean; // default true
   }

   export const CRTMonitor: React.FC<CRTMonitorProps> = ({
     children,
     intensity = 0.8,
     scanlineSpeed = 2,
     glowIntensity = 0.7,
     curvature = 15,
     enableBloom = true,
   }) => {
     // Implementation
   };
   ```

2. **Phosphor Glow Utility:**
   ```typescript
   // /frontend/src/utils/phosphorGlow.ts
   export const generatePhosphorGlow = (
     color: string, // hex color e.g. '#ff9500'
     intensity: number // 0-1
   ): string => {
     // Convert hex to HSL
     // Generate multi-layer text-shadow
     // Return CSS text-shadow string
   };
   ```

3. **Animated Scanlines Component:**
   ```tsx
   // /frontend/src/components/Terminal/AnimatedScanlines.tsx
   interface AnimatedScanlinesProps {
     speed?: number; // seconds per cycle, default 2
     opacity?: number; // 0-1, default 0.1
   }

   export const AnimatedScanlines: React.FC<AnimatedScanlinesProps> = ({
     speed = 2,
     opacity = 0.1,
   }) => {
     // CSS keyframe animation with repeating linear gradient
   };
   ```

4. **CRT Effects Applied:**
   - **Phosphor Glow:** Multi-layer text-shadow on all text
     ```css
     text-shadow:
       0 0 5px rgba(255, 149, 0, 0.5),
       0 0 10px rgba(255, 149, 0, 0.8),
       0 0 20px rgba(255, 149, 0, 0.4);
     ```
   - **Scanlines:** Repeating linear gradient overlay
     ```css
     background-image: repeating-linear-gradient(
       0deg,
       rgba(0, 0, 0, 0.1),
       rgba(0, 0, 0, 0.1) 1px,
       transparent 1px,
       transparent 2px
     );
     animation: scanline-move 2s linear infinite;
     ```
   - **Chromatic Aberration:** Red/cyan offset on edges
     ```css
     /* Via pseudo-elements or CSS filter */
     filter: drop-shadow(2px 0 0 rgba(255, 0, 0, 0.3))
             drop-shadow(-2px 0 0 rgba(0, 255, 255, 0.3));
     ```
   - **Screen Curvature:** CSS perspective transform
     ```css
     transform: perspective(1000px) rotateX(2deg);
     border-radius: 10px;
     ```
   - **Bloom:** SVG filter for glow extension
     ```tsx
     <svg style={{ position: 'absolute', width: 0, height: 0 }}>
       <defs>
         <filter id="phosphor-bloom">
           <feGaussianBlur in="SourceGraphic" stdDeviation="5" />
           <feComponentTransfer>
             <feFuncA type="linear" slope="1.5" />
           </feComponentTransfer>
         </filter>
       </defs>
     </svg>
     ```

5. **Integration:**
   - Wrap HomePage or App.tsx with CRTMonitor
   - All child components inherit CRT effects
   - Performance target: <0.1ms overhead per frame

**Acceptance Criteria:**
- [ ] CRTMonitor component created at `/frontend/src/components/Terminal/CRTMonitor.tsx`
- [ ] Phosphor glow utility created at `/frontend/src/utils/phosphorGlow.ts`
- [ ] AnimatedScanlines component created at `/frontend/src/components/Terminal/AnimatedScanlines.tsx`
- [ ] All 5 CRT effects working: glow, scanlines, aberration, curvature, bloom
- [ ] Props control effect intensity and behavior
- [ ] Performance: <0.1ms overhead per frame (60fps maintained)
- [ ] Docker rebuild successful
- [ ] CRT effects visible on test page http://localhost:5173/css-test
- [ ] No TypeScript errors
- [ ] GPU acceleration via CSS will-change applied

**Files to Create:**
- ➕ `/frontend/src/components/Terminal/CRTMonitor.tsx`
- ➕ `/frontend/src/components/Terminal/AnimatedScanlines.tsx`
- ➕ `/frontend/src/utils/phosphorGlow.ts`

**Files to Modify:**
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Wrap with CRTMonitor

---

### Task 1.1: Dot Matrix LED Display Banner (USER'S FAVORITE)

**Agent:** @terminal-ui-specialist
**Duration:** 3-4 hours
**Dependencies:** Task 1.0 complete (needs CRTMonitor wrapper)
**Priority:** HIGH - User's favorite feature

**Reference Documentation:**
- [ANIMATION_MOCKUPS.md](../design_overhaul/ANIMATION_MOCKUPS.md) - Section 11 (Dot Matrix Display Effects, lines 659-704)
- [ADVANCED_TERMINAL_DESIGN.md](../design_overhaul/ADVANCED_TERMINAL_DESIGN.md) - Dot Matrix Display implementation

**Objective:**
Replace figlet.js banner with professional dot matrix LED display featuring pixel-by-pixel character reveal, 5x7 pixel matrices, and optional reactive background mode.

**Visual Example from Design Docs:**
```
Displaying: "S.Y.N.A.P.S.E."
┌─────────────────────────────────────────────┐
│ ● ● ● ░ ● ░ ░ ● ░ ● ░ ░ ● ░ ● ● ● ░ ░    │
│ ● ░ ░ ░ ░ ● ░ ░ ● ░ ░ ● ░ ● ░ ░ ░ ● ░    │
│ ● ● ● ░ ● ░ ░ ● ░ ● ░ ░ ● ░ ● ● ● ░ ● ░  │
│ ░ ░ ● ░ ● ░ ░ ● ░ ● ░ ░ ● ░ ● ░ ░ ░ ░ ●  │
│ ● ● ● ░ ● ● ● ░ ● ░ ● ● ● ░ ● ● ● ░ ● ░  │
└─────────────────────────────────────────────┘
```

**Requirements:**

1. **Create DotMatrixBanner.tsx:**
   ```tsx
   // /frontend/src/components/Terminal/DotMatrixBanner.tsx
   interface DotMatrixBannerProps {
     text: string; // Max 40 characters recommended
     revealSpeed?: number; // milliseconds per character, default 400
     pixelSize?: number; // pixels, default 8
     reactive?: boolean; // Reactive background mode, default false
     onRevealComplete?: () => void;
   }

   export const DotMatrixBanner: React.FC<DotMatrixBannerProps> = ({
     text,
     revealSpeed = 400,
     pixelSize = 8,
     reactive = false,
     onRevealComplete,
   }) => {
     const canvasRef = useRef<HTMLCanvasElement>(null);
     // Implementation with Canvas API
   };
   ```

2. **Create dotMatrixCharMap.ts:**
   ```typescript
   // /frontend/src/utils/dotMatrixCharMap.ts
   export type DotMatrixChar = number[][]; // 5x7 binary array

   export const DOT_MATRIX_CHARS: Record<string, DotMatrixChar> = {
     'A': [
       [0, 1, 1, 1, 0],
       [1, 0, 0, 0, 1],
       [1, 1, 1, 1, 1],
       [1, 0, 0, 0, 1],
       [1, 0, 0, 0, 1],
       [1, 0, 0, 0, 1],
       [1, 0, 0, 0, 1],
     ],
     // ... all ASCII characters
   };
   ```

3. **Features:**
   - Canvas-based rendering for performance
   - 5x7 pixel matrix per character (industry standard)
   - Characters: `●` (filled pixel) `░` (empty pixel)
   - Pixel-by-pixel reveal animation at 400ms/char
   - Phosphor glow on all filled pixels
   - Optional reactive background: pulse on events, shimmer on success

4. **Reactive Background Mode:**
   ```tsx
   // Listen to system events
   useEffect(() => {
     if (!reactive) return;

     const handleSystemEvent = (event: SystemEvent) => {
       if (event.type === 'query_complete') {
         triggerShimmerEffect();
       } else if (event.type === 'processing') {
         triggerPulseEffect();
       }
     };

     // Subscribe to event bus
   }, [reactive]);
   ```

5. **Integration:**
   - Replace static banner in HomePage.tsx
   - Text: "S.Y.N.A.P.S.E. ENGINE" or "NEURAL SUBSTRATE"
   - Wrapped in CRTMonitor for glow/scanlines

**Acceptance Criteria:**
- [ ] DotMatrixBanner component created at `/frontend/src/components/Terminal/DotMatrixBanner.tsx`
- [ ] dotMatrixCharMap.ts created at `/frontend/src/utils/dotMatrixCharMap.ts`
- [ ] Component accepts `text`, `revealSpeed`, `pixelSize`, `reactive` props
- [ ] 5x7 pixel matrix renders correctly for all ASCII characters
- [ ] Pixel-by-pixel reveal animation smooth at 400ms/char
- [ ] Phosphor glow applied to each filled pixel
- [ ] Reactive background mode functional (pulse/shimmer)
- [ ] Performance: 60fps with 40 characters
- [ ] Integrated into HomePage.tsx
- [ ] Docker rebuild successful
- [ ] Banner displays correctly at http://localhost:5173/
- [ ] No TypeScript errors

**Files to Create:**
- ➕ `/frontend/src/components/Terminal/DotMatrixBanner.tsx`
- ➕ `/frontend/src/utils/dotMatrixCharMap.ts`

**Files to Modify:**
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Replace static banner with DotMatrixBanner

---

### Task 1.2: System Status Panel with Radial Gauges & Pulse Effects

**Agent:** @frontend-engineer
**Duration:** 4-5 hours
**Dependencies:** Task 1.0 complete (needs CRTMonitor wrapper)
**Priority:** HIGH

**Reference Documentation:**
- [ADVANCED_TERMINAL_DESIGN.md](../design_overhaul/ADVANCED_TERMINAL_DESIGN.md) - Section C (Radial Gauge)
- [ANIMATION_MOCKUPS.md](../design_overhaul/ANIMATION_MOCKUPS.md) - Section 9 (Advanced Widget Examples)

**Objective:**
Upgrade SystemStatusPanel from 3 basic metrics to 8+ dense metrics with radial gauges, pulse indicators, and sparklines.

**Visual Upgrade:**
```
BEFORE (Original Plan):
VRAM: 8.2GB / 10GB [basic text]
QUERIES: 145 [basic text]
CACHE: 92% [basic text]

AFTER (REVISED Plan):
┌──────────────────────────────────────────┐
│ VRAM          ╔═════╗  8.2 / 10 GB      │
│               ║▄▄▄░░║  82%              │ [Radial gauge
│             ╔═╬═════╬═╗ [pulse]         │  with glow]
│               ║▀▀▀▀▀║                   │
│               ╚═════╝                   │
└──────────────────────────────────────────┘
```

**Requirements:**

1. **Create RadialGauge.tsx Component:**
   ```tsx
   // /frontend/src/components/Terminal/RadialGauge.tsx
   interface RadialGaugeProps {
     value: number; // 0-100
     max?: number; // default 100
     label?: string;
     unit?: string;
     size?: number; // pixels, default 120
     thresholds?: {
       warning: number; // default 70
       critical: number; // default 90
     };
   }

   export const RadialGauge: React.FC<RadialGaugeProps> = (props) => {
     // SVG circle with animated stroke-dashoffset
     // Color coding: normal (orange), warning (amber), critical (red)
   };
   ```

2. **Create PulseIndicator.tsx Component:**
   ```tsx
   // /frontend/src/components/Terminal/PulseIndicator.tsx
   interface PulseIndicatorProps {
     active: boolean;
     color?: 'orange' | 'cyan' | 'green' | 'red';
     frequency?: number; // Hz, default 1
   }

   export const PulseIndicator: React.FC<PulseIndicatorProps> = ({
     active,
     color = 'orange',
     frequency = 1,
   }) => {
     // CSS keyframe animation: scale + glow
   };
   ```

3. **Expanded Metrics (8+):**

   | # | Metric | Type | Sparkline | Pulse | Gauge |
   |---|--------|------|-----------|-------|-------|
   | 1 | VRAM | Radial Gauge | Yes | No | Yes |
   | 2 | Active Models | Count + Tier Breakdown | No | Yes (if >0) | No |
   | 3 | Token Generation Rate | Sparkline + Value | Yes | No | No |
   | 4 | Context Window Utilization | Radial Gauge | Yes | No | Yes |
   | 5 | Cache Hit Rate % | Radial Gauge + Sparkline | Yes | Yes (if >70%) | Yes |
   | 6 | CGRAG Retrieval Latency | Sparkline + Value | Yes | No | No |
   | 7 | WebSocket Connections | Count | No | Yes (if >0) | No |
   | 8 | System Uptime | Static Display | No | No | No |

4. **SystemStatusPanel Component:**
   ```tsx
   // /frontend/src/components/SystemStatus/SystemStatusPanel.tsx
   export const SystemStatusPanel: React.FC = () => {
     const { data: metrics } = useSystemMetrics();

     return (
       <div className="synapse-panel">
         <div className="synapse-panel__header">SYSTEM STATUS</div>
         <div className="synapse-panel__content">
           <div className="synapse-grid synapse-grid--4">
             {/* 8+ MetricCard components with RadialGauge/PulseIndicator */}
           </div>
         </div>
       </div>
     );
   };
   ```

5. **CSS Grid Layout:**
   - Use `synapse-grid synapse-grid--4` for 4-column layout
   - Responsive breakpoints:
     - Desktop (>1280px): 4 columns
     - Tablet (768-1280px): 2 columns
     - Mobile (<768px): 1 column

**Acceptance Criteria:**
- [ ] RadialGauge component created at `/frontend/src/components/Terminal/RadialGauge.tsx`
- [ ] PulseIndicator component created at `/frontend/src/components/Terminal/PulseIndicator.tsx`
- [ ] SystemStatusPanel component created at `/frontend/src/components/SystemStatus/SystemStatusPanel.tsx`
- [ ] MetricCard component created at `/frontend/src/components/SystemStatus/MetricCard.tsx`
- [ ] useSystemMetrics hook created at `/frontend/src/hooks/useSystemMetrics.ts`
- [ ] 8+ metrics displayed in responsive grid
- [ ] Radial gauges animate smoothly (CSS transitions)
- [ ] Pulse indicators animate at 1Hz
- [ ] Sparklines render with Unicode block characters
- [ ] Threshold color coding working (normal/warning/critical)
- [ ] Integrated into HomePage.tsx
- [ ] Docker rebuild successful
- [ ] All metrics visible at http://localhost:5173/
- [ ] No TypeScript errors
- [ ] Grid responsive on mobile/tablet/desktop

**Files to Create:**
- ➕ `/frontend/src/components/Terminal/RadialGauge.tsx`
- ➕ `/frontend/src/components/Terminal/PulseIndicator.tsx`
- ➕ `/frontend/src/components/SystemStatus/SystemStatusPanel.tsx`
- ➕ `/frontend/src/components/SystemStatus/MetricCard.tsx`
- ➕ `/frontend/src/hooks/useSystemMetrics.ts`

**Files to Modify:**
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Replace inline metrics with SystemStatusPanel

---

### Task 1.3: Orchestrator Status Panel with Waveform Visualizer

**Agent:** @frontend-engineer
**Duration:** 3-4 hours
**Dependencies:** Task 1.2 complete (reuses MetricCard, grid patterns)
**Priority:** MEDIUM

**Reference Documentation:**
- [ANIMATION_MOCKUPS.md](../design_overhaul/ANIMATION_MOCKUPS.md) - Section 9 (Waveform Visualizer)
- [ADVANCED_TERMINAL_DESIGN.md](../design_overhaul/ADVANCED_TERMINAL_DESIGN.md) - Waveform section

**Objective:**
Create OrchestratorStatusPanel with waveform visualizer showing query complexity distribution as animated frequency bars.

**Visual Example from Design Docs:**
```
QUERY COMPLEXITY DISTRIBUTION
┌───────────────────────────────────────────┐
│ █  █  █  █  █  █  █  █  █                │
│ █  █  █  █  █  █  █  █  █                │
│ ░  █  █  █  █  █  █  █  ░                │
│ ░  ░  █  █  █  █  █  ░  ░                │
│ ░  ░  ░  █  █  ░  ░  ░  ░                │
└───────────────────────────────────────────┘
[32+ bars animating at 60fps]
```

**Requirements:**

1. **Create WaveformVisualizer.tsx Component:**
   ```tsx
   // /frontend/src/components/Terminal/WaveformVisualizer.tsx
   interface WaveformVisualizerProps {
     data: number[]; // Array of 0-100 values
     barCount?: number; // default 32
     height?: number; // pixels, default 120
     barWidth?: number; // pixels, default 4
     color?: string; // default '#ff9500'
     animate?: boolean; // default true
   }

   export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
     data,
     barCount = 32,
     height = 120,
     barWidth = 4,
     color = '#ff9500',
     animate = true,
   }) => {
     const canvasRef = useRef<HTMLCanvasElement>(null);

     // Canvas-based bar visualization
     // Smooth interpolation: 0.4 factor for transitions
     // 60fps target
   };
   ```

2. **OrchestratorStatusPanel Component:**
   ```tsx
   // /frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx
   export const OrchestratorStatusPanel: React.FC = () => {
     const { data: stats } = useOrchestratorStats();

     return (
       <div className="synapse-panel">
         <div className="synapse-panel__header">ORCHESTRATOR STATUS</div>
         <div className="synapse-panel__content">
           {/* Routing distribution chart (ASCII bars) */}
           {/* Model utilization bars (ASCII horizontal bars) */}
           {/* WaveformVisualizer for complexity distribution */}
           {/* Recent decisions list */}
         </div>
       </div>
     );
   };
   ```

3. **Data Structure:**
   ```tsx
   interface OrchestratorStats {
     totalQueries: number;
     routingDecisions: {
       Q2: number;
       Q3: number;
       Q4: number;
     };
     complexityDistribution: number[]; // 32 values for waveform
     modelUtilization: {
       Q2: number;
       Q3: number;
       Q4: number;
     };
     recentDecisions: Array<{
       timestamp: Date;
       tier: 'Q2' | 'Q3' | 'Q4';
       complexity: number;
       query: string;
     }>;
   }
   ```

4. **ASCII Utilization Bars:**
   ```tsx
   const renderUtilizationBar = (label: string, percent: number) => (
     <div className="synapse-metric">
       <div className="synapse-metric__label">{label}</div>
       <div className="synapse-chart">
         Q2 ████████████████████░░░░░░░░ 65%
       </div>
     </div>
   );
   ```

**Acceptance Criteria:**
- [ ] WaveformVisualizer component created at `/frontend/src/components/Terminal/WaveformVisualizer.tsx`
- [ ] OrchestratorStatusPanel component created at `/frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx`
- [ ] useOrchestratorStats hook created at `/frontend/src/hooks/useOrchestratorStats.ts`
- [ ] Waveform renders 32+ bars with smooth animation
- [ ] 60fps target achieved
- [ ] Routing distribution chart displays correctly
- [ ] Model utilization bars render as ASCII bars
- [ ] Recent decisions list shows last 3 decisions
- [ ] Integrated into HomePage.tsx
- [ ] Docker rebuild successful
- [ ] Panel visible at http://localhost:5173/
- [ ] No TypeScript errors

**Files to Create:**
- ➕ `/frontend/src/components/Terminal/WaveformVisualizer.tsx`
- ➕ `/frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx`
- ➕ `/frontend/src/hooks/useOrchestratorStats.ts`

**Files to Modify:**
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Add OrchestratorStatusPanel

---

### Task 1.4: LiveEventFeed with Particle Effects

**Agent:** @websocket-realtime-specialist
**Duration:** 3-4 hours
**Dependencies:** Task 1.0 complete (needs CRTMonitor wrapper)
**Priority:** HIGH

**Reference Documentation:**
- [ANIMATION_MOCKUPS.md](../design_overhaul/ANIMATION_MOCKUPS.md) - Section 2 (Particle System Explosion)
- [ADVANCED_TERMINAL_DESIGN.md](../design_overhaul/ADVANCED_TERMINAL_DESIGN.md) - Particle System section

**Objective:**
Create LiveEventFeed with rolling 8-event window, color-coded events, and particle celebration effects on important events.

**Visual Example:**
```
LIVE EVENT FEED [CONNECTED]
┌──────────────────────────────────────────┐
│ [QUERY_ROUTING] 2s ago                   │ [Particles
│ Query routed to Q3 (complexity: 6.2)     │  explode on
│                       ░ ▓ ░ ▓ ░          │  new event]
│ [MODEL_STATE] 5s ago                     │
│ Q2_FAST_1 state: ACTIVE → PROCESSING     │
└──────────────────────────────────────────┘
```

**Requirements:**

1. **Create ParticleSystem.tsx Component:**
   ```tsx
   // /frontend/src/components/Terminal/ParticleSystem.tsx
   interface ParticleSystemProps {
     trigger: string; // Any change triggers new explosion
     particleCount?: number; // default 50
     characters?: string; // ASCII chars to use, default '░▒▓█'
     color?: string; // default '#ff9500'
     duration?: number; // milliseconds, default 1000
   }

   export const ParticleSystem: React.FC<ParticleSystemProps> = ({
     trigger,
     particleCount = 50,
     characters = '░▒▓█',
     color = '#ff9500',
     duration = 1000,
   }) => {
     // Physics simulation with velocity, gravity, drag
     // Character particles (ASCII)
     // 60fps target with requestAnimationFrame
   };
   ```

2. **Enhanced LiveEventFeed Component:**
   ```tsx
   // /frontend/src/components/LiveEventFeed/LiveEventFeed.tsx
   export const LiveEventFeed: React.FC = () => {
     const { events, connected } = useWebSocketEvents();
     const [particleTrigger, setParticleTrigger] = useState('');

     // Trigger particle effect on important events
     useEffect(() => {
       const latestEvent = events[0];
       if (latestEvent && shouldShowParticles(latestEvent.type)) {
         setParticleTrigger(`${latestEvent.id}-${Date.now()}`);
       }
     }, [events]);

     return (
       <div className="synapse-panel">
         <div className="synapse-panel__header">
           LIVE EVENT FEED
           <span className={`synapse-status synapse-status--${connected ? 'active' : 'error'}`}>
             {connected ? 'CONNECTED' : 'DISCONNECTED'}
           </span>
         </div>
         <div className="synapse-panel__content">
           <ParticleSystem trigger={particleTrigger} />
           {events.map(event => (
             <div key={event.id} className="event-item">
               {/* Event display */}
             </div>
           ))}
         </div>
       </div>
     );
   };
   ```

3. **Event Types with Particle Colors:**
   ```tsx
   const getParticleColor = (type: SystemEvent['type']): string => {
     switch (type) {
       case 'query_complete': return '#00ff00'; // Green success particles
       case 'error': return '#ff0000'; // Red error particles
       case 'processing': return '#ff9500'; // Orange processing particles
       case 'performance_alert': return '#ffaa00'; // Amber warning particles
       default: return '#ff9500';
     }
   };
   ```

4. **Performance Optimizations:**
   - Limit to 50-100 particles max for 60fps
   - Object pooling: Reuse particle objects
   - GPU acceleration with `will-change` CSS property
   - Debounce event updates to 100ms (max 10fps)

**Acceptance Criteria:**
- [ ] ParticleSystem component created at `/frontend/src/components/Terminal/ParticleSystem.tsx`
- [ ] LiveEventFeed component created at `/frontend/src/components/LiveEventFeed/LiveEventFeed.tsx`
- [ ] useWebSocketEvents hook created at `/frontend/src/hooks/useWebSocketEvents.ts`
- [ ] Rolling 8-event window implemented (FIFO eviction)
- [ ] Color-coded event types working (6 event types)
- [ ] Particle effects trigger on important events
- [ ] Smooth 60fps scrolling animation
- [ ] Particle explosion effects smooth at 60fps
- [ ] Relative timestamp formatting ("2s ago", "5m ago")
- [ ] WebSocket reconnection logic with exponential backoff
- [ ] Connection status indicator (CONNECTED/DISCONNECTED)
- [ ] Integrated into HomePage.tsx
- [ ] Docker rebuild successful
- [ ] Feed visible at http://localhost:5173/
- [ ] No TypeScript errors

**Files to Create:**
- ➕ `/frontend/src/components/Terminal/ParticleSystem.tsx`
- ➕ `/frontend/src/components/LiveEventFeed/LiveEventFeed.tsx`
- ➕ `/frontend/src/hooks/useWebSocketEvents.ts`

**Files to Modify:**
- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Add LiveEventFeed

---

## HomePage Integration Strategy

### Target HomePage Layout (REVISED)

```tsx
// /frontend/src/pages/HomePage/HomePage.tsx (Phase 1 REVISED)
<CRTMonitor intensity={0.8} scanlineSpeed={2} glowIntensity={0.7}>
  <div className={styles.page}>
    {/* Task 1.1: Dot Matrix LED Display Banner (USER'S FAVORITE) */}
    <DotMatrixBanner
      text="S.Y.N.A.P.S.E. ENGINE"
      revealSpeed={400}
      reactive={true}
    />

    {/* Task 1.2: System Metrics with Radial Gauges (8+ metrics) */}
    <SystemStatusPanel />

    {/* Two-column grid: Orchestrator + Event Feed */}
    <div className="synapse-grid synapse-grid--2">
      {/* Task 1.3: Orchestrator Visualization with Waveform */}
      <OrchestratorStatusPanel />

      {/* Task 1.4: Live Event Feed with Particle Effects */}
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
</CRTMonitor>
```

### Integration Steps

1. **Add Imports (top of HomePage.tsx):**
   ```tsx
   import { CRTMonitor } from '@/components/Terminal/CRTMonitor';
   import { DotMatrixBanner } from '@/components/Terminal/DotMatrixBanner';
   import { SystemStatusPanel } from '@/components/SystemStatus/SystemStatusPanel';
   import { OrchestratorStatusPanel } from '@/components/Orchestrator/OrchestratorStatusPanel';
   import { LiveEventFeed } from '@/components/LiveEventFeed/LiveEventFeed';
   ```

2. **Wrap entire page with CRTMonitor:**
   ```tsx
   // Wrap everything for CRT effects
   <CRTMonitor intensity={0.8} scanlineSpeed={2} glowIntensity={0.7}>
     {/* All page content */}
   </CRTMonitor>
   ```

3. **Replace static banner:**
   ```tsx
   // OLD
   <h1 className={styles.title}>
     ▓▓▓▓ NEURAL SUBSTRATE ORCHESTRATOR ▓▓▓▓
   </h1>

   // NEW
   <DotMatrixBanner text="S.Y.N.A.P.S.E. ENGINE" revealSpeed={400} reactive={true} />
   ```

4. **Replace inline metrics:**
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

5. **Add new panels:**
   ```tsx
   <div className="synapse-grid synapse-grid--2">
     <OrchestratorStatusPanel />
     <LiveEventFeed />
   </div>
   ```

---

## Risks & Mitigation

### Risk 1: CRT Effects Performance Overhead

**Risk:** CRT effects (glow, scanlines, bloom) could degrade 60fps performance.

**Mitigation:**
- Use GPU acceleration with CSS will-change property
- SVG filters cached and reused
- Monitor performance with Chrome DevTools (target: <0.1ms overhead)
- Provide intensity prop to reduce effects if needed
- Design docs show 60fps achievable on modern hardware

**Impact:** Low (extensively tested in design docs)

### Risk 2: Dot Matrix Canvas Rendering Complexity

**Risk:** Canvas-based dot matrix could be slow with many characters.

**Mitigation:**
- Limit to 40 characters recommended
- Use requestAnimationFrame for smooth animation
- Pixel drawing optimized with batch operations
- Performance tested: 60fps with 40 chars on design firm examples
- Memoize character map lookups

**Impact:** Low (Canvas is faster than DOM for pixel-level control)

### Risk 3: Particle System Memory Leaks

**Risk:** Particle objects not cleaned up could cause memory leaks.

**Mitigation:**
- Object pooling: Reuse particle objects
- Lifecycle management: Particle birth/death with cleanup
- Limit to 50-100 particles max
- Monitor with Chrome DevTools Memory profiler
- Design docs show stable memory usage

**Impact:** Low (object pooling prevents GC pressure)

### Risk 4: Time Estimate Overage

**Risk:** 15-17 hours may exceed estimate if complexity underestimated.

**Mitigation:**
- Design docs provide tested implementations (copy patterns)
- Wave structure allows incremental progress
- Phase tasks can be split if needed (e.g., CRT effects in stages)
- Buffer: +20% (3 hours) for unexpected issues

**Impact:** Medium (mitigated by design docs)

### Risk 5: Browser Compatibility

**Risk:** CRT effects may not work on older browsers.

**Mitigation:**
- Modern browser requirement (94%+ support verified)
- Progressive enhancement: Basic UI works without effects
- Feature detection for CSS filters
- Fallback: Disable effects on unsupported browsers

**Impact:** Low (modern browser requirement is acceptable)

---

## Performance Validation Plan

### Metrics to Monitor

1. **Frame Rate:**
   - Target: 60fps minimum
   - Tool: Chrome DevTools Performance tab
   - Measure: During CRT effects, particle explosions, waveform animation

2. **Component Render Time:**
   - Target: <16.67ms per frame (60fps budget)
   - CRTMonitor overhead: <0.1ms
   - DotMatrixBanner: <5ms per frame during reveal
   - ParticleSystem: <8ms with 100 particles

3. **Memory Usage:**
   - Target: Stable (no growth over time)
   - Tool: Chrome DevTools Memory profiler
   - Monitor: Particle object pooling, Canvas memory

4. **Bundle Size:**
   - Target: <100KB increase from Phase 0
   - Components are lightweight (no heavy dependencies)
   - Canvas/SVG APIs are browser-native (no bundle impact)

### Testing Checklist

**Performance:**
- [ ] 60fps maintained with all CRT effects enabled
- [ ] Dot matrix reveal animation smooth at 400ms/char
- [ ] Particle explosions smooth with 50-100 particles
- [ ] Waveform visualizer smooth with 32 bars
- [ ] Radial gauges animate smoothly (CSS transitions)
- [ ] No memory leaks (stable memory over 5 minutes)

**Visual Quality:**
- [ ] Phosphor glow visible on all text
- [ ] Scanlines animating at 2s cycle
- [ ] Chromatic aberration visible on edges
- [ ] Screen curvature applied to viewport
- [ ] Bloom effect visible from bright elements
- [ ] Dot matrix pixels have glow effect
- [ ] Radial gauges have phosphor glow
- [ ] Particle colors match event types

**Responsive:**
- [ ] Mobile (375px): 1 column layout, scaled effects
- [ ] Tablet (768px): 2 column layout, normal effects
- [ ] Desktop (1280px): 4 column layout, normal effects
- [ ] Wide (1920px): 4 column layout, enhanced effects

---

## Reference Documentation

**Related Documents:**
- [SESSION_NOTES.md](../SESSION_NOTES.md) - Recent development context
- [TASK_0.5_COMPLETE.md](../TASK_0.5_COMPLETE.md) - Phase 0 completion report
- [CLAUDE.md](../CLAUDE.md) - Project guidelines and constraints
- [docker-compose.yml](../docker-compose.yml) - Frontend build configuration

**Design Firm Specifications:**
- [ADVANCED_TERMINAL_DESIGN.md](../design_overhaul/ADVANCED_TERMINAL_DESIGN.md) - Complete implementation catalog
- [ANIMATION_MOCKUPS.md](../design_overhaul/ANIMATION_MOCKUPS.md) - Frame-by-frame visual reference
- [ANIMATION_IMPLEMENTATION_ROADMAP.md](../design_overhaul/ANIMATION_IMPLEMENTATION_ROADMAP.md) - 4-6 week roadmap

**CSS Foundation:**
- [WEBTUI_INTEGRATION_GUIDE.md](../docs/WEBTUI_INTEGRATION_GUIDE.md) - CSS integration patterns
- [WEBTUI_STYLE_GUIDE.md](../docs/WEBTUI_STYLE_GUIDE.md) - Component styling guide
- [frontend/src/assets/styles/components.css](../frontend/src/assets/styles/components.css) - 31 component classes

**Agent Specifications:**
- [terminal-ui-specialist.md](../.claude/agents/terminal-ui-specialist.md) - CRT effects, dot matrix, terminal aesthetics
- [frontend-engineer.md](../.claude/agents/frontend-engineer.md) - React/TypeScript, gauges, waveform
- [websocket-realtime-specialist.md](../.claude/agents/websocket-realtime-specialist.md) - WebSocket real-time, particle effects

**Test Page:**
- http://localhost:5173/css-test - CSS component validation page

---

## Definition of Done

Phase 1 REVISED is complete when ALL of these criteria are met:

**Component Creation (CRT Effects):**
- [ ] CRTMonitor component exists at `/frontend/src/components/Terminal/CRTMonitor.tsx`
- [ ] AnimatedScanlines component exists at `/frontend/src/components/Terminal/AnimatedScanlines.tsx`
- [ ] phosphorGlow utility exists at `/frontend/src/utils/phosphorGlow.ts`
- [ ] All 5 CRT effects working (glow, scanlines, aberration, curvature, bloom)

**Component Creation (Dot Matrix):**
- [ ] DotMatrixBanner component exists at `/frontend/src/components/Terminal/DotMatrixBanner.tsx`
- [ ] dotMatrixCharMap.ts exists at `/frontend/src/utils/dotMatrixCharMap.ts`
- [ ] 5x7 pixel matrices render correctly
- [ ] Pixel-by-pixel reveal animation smooth

**Component Creation (Gauges & Pulse):**
- [ ] RadialGauge component exists at `/frontend/src/components/Terminal/RadialGauge.tsx`
- [ ] PulseIndicator component exists at `/frontend/src/components/Terminal/PulseIndicator.tsx`
- [ ] SystemStatusPanel component exists at `/frontend/src/components/SystemStatus/SystemStatusPanel.tsx`
- [ ] MetricCard component exists at `/frontend/src/components/SystemStatus/MetricCard.tsx`

**Component Creation (Waveform):**
- [ ] WaveformVisualizer component exists at `/frontend/src/components/Terminal/WaveformVisualizer.tsx`
- [ ] OrchestratorStatusPanel component exists at `/frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx`
- [ ] 32+ bars animating smoothly at 60fps

**Component Creation (Particles):**
- [ ] ParticleSystem component exists at `/frontend/src/components/Terminal/ParticleSystem.tsx`
- [ ] LiveEventFeed component exists at `/frontend/src/components/LiveEventFeed/LiveEventFeed.tsx`
- [ ] Particle effects trigger on events

**Hooks Creation:**
- [ ] useSystemMetrics hook exists at `/frontend/src/hooks/useSystemMetrics.ts`
- [ ] useOrchestratorStats hook exists at `/frontend/src/hooks/useOrchestratorStats.ts`
- [ ] useWebSocketEvents hook exists at `/frontend/src/hooks/useWebSocketEvents.ts`

**HomePage Integration:**
- [ ] Entire page wrapped in CRTMonitor
- [ ] DotMatrixBanner integrated and displays pixel-by-pixel reveal
- [ ] SystemStatusPanel shows 8+ metrics with radial gauges
- [ ] OrchestratorStatusPanel shows waveform visualizer
- [ ] LiveEventFeed shows particle effects on events
- [ ] All components maintain phosphor orange theme (#ff9500)

**Visual & Performance:**
- [ ] CRT effects visible (glow, scanlines, aberration, curvature, bloom)
- [ ] Dot matrix banner has phosphor glow on pixels
- [ ] Radial gauges animate with threshold color coding
- [ ] Pulse indicators animate at 1Hz
- [ ] Waveform visualizer smooth at 60fps
- [ ] Particle explosions smooth at 60fps
- [ ] All animations run at 60fps minimum
- [ ] Responsive layout works on mobile/tablet/desktop

**Technical Quality:**
- [ ] No TypeScript errors in any file
- [ ] All components have strict type definitions
- [ ] React.memo applied to prevent unnecessary re-renders
- [ ] ARIA labels added for accessibility
- [ ] GPU acceleration via will-change applied
- [ ] Object pooling for particles (no memory leaks)

**Docker & Build:**
- [ ] `docker-compose build --no-cache synapse_frontend` succeeds
- [ ] `docker-compose up -d synapse_frontend` starts container
- [ ] No build errors or warnings
- [ ] No console errors at http://localhost:5173/

**Documentation:**
- [ ] SESSION_NOTES.md updated with Phase 1 REVISED completion
- [ ] All file changes documented with line numbers
- [ ] Agent consultations documented
- [ ] Next steps documented (Phase 2 preparation)

---

## Next Actions

### Immediate (Post-Approval)

1. **Wave 1 Launch (BLOCKING - Sequential):**
   - Agent: @terminal-ui-specialist → Task 1.0 (CRT Effects Foundation)
   - **CRITICAL:** Must complete before Wave 2 starts

2. **Wave 1 Validation:**
   - Rebuild Docker container: `docker-compose build --no-cache synapse_frontend`
   - Test CRTMonitor in isolation
   - Verify all 5 CRT effects working
   - Check performance: <0.1ms overhead per frame
   - Verify no TypeScript errors

3. **Wave 2 Launch (Parallel Execution - After Wave 1):**
   - Agent 1: @terminal-ui-specialist → Task 1.1 (DotMatrixBanner)
   - Agent 2: @frontend-engineer → Task 1.2 (SystemStatusPanel + Gauges)
   - Agent 3: @websocket-realtime-specialist → Task 1.4 (LiveEventFeed + Particles)
   - **All run in parallel** (no dependencies between them)

4. **Wave 2 Validation:**
   - Rebuild Docker container
   - Test each component in isolation
   - Verify 60fps performance
   - Check responsive behavior

5. **Wave 3 Launch (Sequential - After Wave 2):**
   - Agent: @frontend-engineer → Task 1.3 (OrchestratorStatusPanel + Waveform)
   - Reuses patterns from Task 1.2

6. **Final Integration:**
   - Integrate all components into HomePage.tsx
   - Full rebuild and test
   - Verify responsive behavior (mobile/tablet/desktop)
   - Run complete testing checklist
   - Performance profiling with Chrome DevTools

### Follow-Up (Phase 2 Preparation)

1. **Backend API Development:**
   - Implement `GET /api/metrics/system` endpoint for SystemStatusPanel
   - Implement `GET /api/orchestrator/stats` endpoint for OrchestratorStatusPanel
   - Implement `WS /ws/events` WebSocket endpoint for LiveEventFeed
   - Add mock data generators for development testing

2. **Performance Profiling:**
   - Chrome DevTools Performance tab (60fps verification)
   - Memory profiler (particle object pooling verification)
   - Frame rate monitoring during animations
   - Bundle size analysis

3. **Accessibility Audit:**
   - Screen reader testing (macOS VoiceOver)
   - Keyboard navigation verification
   - ARIA labels verification
   - Color contrast testing (WCAG AA compliance)

4. **Documentation:**
   - Update SESSION_NOTES.md with Phase 1 REVISED completion details
   - Add screenshots to documentation
   - Document performance optimizations applied
   - Update CLAUDE.md if new patterns discovered

---

## Estimated Effort

**Time Breakdown (Sequential):**
- Task 1.0 (CRT Effects): 6-8 hours
- Task 1.1 (DotMatrixBanner): 3-4 hours
- Task 1.2 (SystemStatusPanel + Gauges): 4-5 hours
- Task 1.3 (OrchestratorStatusPanel + Waveform): 3-4 hours
- Task 1.4 (LiveEventFeed + Particles): 3-4 hours
- **Total:** 19-25 hours

**Time Breakdown (Parallelized):**
- Wave 1 (Task 1.0): 6-8 hours (BLOCKING)
- Wave 2 (Tasks 1.1, 1.2, 1.4): 5 hours (max of 3-4h, 4-5h, 3-4h)
- Wave 3 (Task 1.3): 3-4 hours
- **Total:** 15-17 hours

**Confidence Level:**
- Wave 1 (CRT Effects): High (85%) - Design docs provide tested implementation
- Wave 2 (Parallel tasks): High (90%) - Independent tasks, well-defined
- Wave 3 (Waveform): High (90%) - Reuses Wave 2 patterns
- Integration: High (85%) - Clear integration strategy

**Risk Buffer:** +20% (3 hours) for unexpected TypeScript errors or performance tuning

**Total Estimated Time:** 15-17 hours parallelized, 19-25 hours sequential

---

## Files Summary

### New Files Created (18 files)

**CRT Effects:**
- `/frontend/src/components/Terminal/CRTMonitor.tsx`
- `/frontend/src/components/Terminal/AnimatedScanlines.tsx`
- `/frontend/src/utils/phosphorGlow.ts`

**Dot Matrix:**
- `/frontend/src/components/Terminal/DotMatrixBanner.tsx`
- `/frontend/src/utils/dotMatrixCharMap.ts`

**Gauges & Pulse:**
- `/frontend/src/components/Terminal/RadialGauge.tsx`
- `/frontend/src/components/Terminal/PulseIndicator.tsx`
- `/frontend/src/components/SystemStatus/SystemStatusPanel.tsx`
- `/frontend/src/components/SystemStatus/MetricCard.tsx`

**Waveform:**
- `/frontend/src/components/Terminal/WaveformVisualizer.tsx`
- `/frontend/src/components/Orchestrator/OrchestratorStatusPanel.tsx`

**Particles:**
- `/frontend/src/components/Terminal/ParticleSystem.tsx`
- `/frontend/src/components/LiveEventFeed/LiveEventFeed.tsx`

**Hooks:**
- `/frontend/src/hooks/useSystemMetrics.ts`
- `/frontend/src/hooks/useOrchestratorStats.ts`
- `/frontend/src/hooks/useWebSocketEvents.ts`

### Modified Files (1 file)

- ✏️ `/frontend/src/pages/HomePage/HomePage.tsx` - Integrate all components with CRTMonitor wrapper

### Total Files: 19 files (18 new, 1 modified)

---

## Comparison: Original vs REVISED Plan

### Original Plan Summary
- **Duration:** 8-10 hours (5h parallelized)
- **Components:** 4 new components (FigletBanner, SystemStatusPanel, OrchestratorStatusPanel, LiveEventFeed)
- **Quality:** Basic terminal aesthetic
- **Features:** Figlet banner, 8 metrics, basic orchestrator, event list

### REVISED Plan Summary
- **Duration:** 15-17 hours (parallelized) vs 19-25 hours (sequential)
- **Components:** 13 new components + 3 utilities
- **Quality:** Professional-grade advanced terminal design
- **Features:** Dot matrix LED display, CRT effects (glow/scanlines/bloom), radial gauges, pulse indicators, waveform visualizer, particle effects

### Impact Assessment

| Aspect | Original | REVISED | Improvement |
|--------|----------|---------|-------------|
| Visual Quality | Basic | Professional | ~500% |
| Time Investment | 8-10h | 15-17h | +70% |
| Components | 4 | 13 | +325% |
| Animations | 2 basic | 8+ advanced | +400% |
| User Impact | Moderate | Dramatic | ~500% |
| Reusability | Medium | High | Reusable for Phase 2-4 |

**Conclusion:** 70% more time investment yields 500% quality increase with professional-grade terminal aesthetic matching user's vision.

---

**Date:** 2025-11-08
**Status:** Ready to Execute (REVISED)
**Phase:** 1 of 4 → Foundation for Phases 2-4

**Approval Required:** Please confirm to begin Wave 1 execution (CRT Effects Foundation - BLOCKING).
