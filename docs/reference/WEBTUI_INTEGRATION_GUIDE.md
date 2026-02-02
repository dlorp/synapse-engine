# WebTUI Integration Guide

**Date:** 2025-11-08
**Version:** 1.0
**Status:** Official Integration Standard

## Overview

Synapse Engine uses **WebTUI** as its CSS foundation to achieve a dense, terminal-inspired aesthetic with modern web performance. WebTUI provides battle-tested terminal UI components, and we customize it with a phosphor orange theme (#ff9500) to match our NERV-inspired visual identity.

**Integration Approach:**
- WebTUI provides the terminal base layer (panels, metrics, status indicators)
- Custom theme overrides WebTUI's default green with phosphor orange (#ff9500)
- Component styles add Synapse-specific patterns (ASCII charts, sparklines)
- CSS layers ensure clean separation and override control

**Benefits:**
- Production-tested terminal UI components (60fps animations, accessibility)
- Consistent design system across all interfaces
- Minimal custom CSS (WebTUI handles most patterns)
- Performance-optimized (GPU acceleration, efficient repaints)
- Maintainable (clear style hierarchy, documented patterns)

---

## Architecture

### CSS Layer System

We use CSS `@layer` to control style precedence and maintain clean separation:

```css
/* /frontend/src/assets/styles/main.css */
@layer base, utils, components;

/* WebTUI base layer */
@layer base {
  @import '@webtui/css';
}

/* Utility classes */
@layer utils {
  @import './theme.css';
}

/* Component-specific styles */
@layer components {
  @import './components.css';
}
```

**Layer Hierarchy:**
1. **base** (lowest) - WebTUI framework defaults
2. **utils** - Theme variables and utility classes
3. **components** (highest) - Custom component styles

**Why Layers?**
- Clear override hierarchy (components > utils > base)
- No specificity battles or `!important` hacks
- Easy to see where styles come from
- Safe to add custom styles without breaking WebTUI

### Style Hierarchy

```
WebTUI Base (@layer base)
  ├── Terminal foundation (.webtui-panel, .webtui-metric, etc.)
  ├── Default theme (green phosphor)
  └── Base utilities
      ↓
Custom Theme (@layer utils)
  ├── Phosphor orange variables (--webtui-primary: #ff9500)
  ├── Synapse branding
  └── Typography overrides
      ↓
Component Styles (@layer components)
  ├── .synapse-* components
  ├── ASCII chart patterns
  └── Application-specific styles
```

---

## Using WebTUI Classes

### Base Components

WebTUI provides ready-to-use terminal components. Use these as building blocks:

**Panel Component:**
```tsx
<div className="webtui-panel">
  <div className="webtui-panel__header">
    NEURAL SUBSTRATE STATUS
  </div>
  <div className="webtui-panel__content">
    <p>Panel content goes here</p>
  </div>
</div>
```

**Metric Display:**
```tsx
<div className="webtui-metric">
  <div className="webtui-metric__label">TOKENS/SEC</div>
  <div className="webtui-metric__value">45.2</div>
  <div className="webtui-metric__unit">tok/s</div>
</div>
```

**Status Indicator:**
```tsx
<span className="webtui-status webtui-status--active">ACTIVE</span>
<span className="webtui-status webtui-status--idle">IDLE</span>
<span className="webtui-status webtui-status--error">ERROR</span>
<span className="webtui-status webtui-status--processing">PROCESSING</span>
```

**Grid Layout:**
```tsx
<div className="webtui-grid webtui-grid--2">
  <div className="webtui-panel">Panel 1</div>
  <div className="webtui-panel">Panel 2</div>
</div>
```

---

## Theme Variables

Our custom theme (`/frontend/src/assets/styles/theme.css`) overrides WebTUI's default green with phosphor orange.

### Primary Colors

```css
/* Phosphor orange theme */
--webtui-primary: #ff9500;           /* Primary text, borders, accents */
--webtui-primary-dim: #cc7700;       /* Dimmed version for secondary text */
--webtui-primary-bright: #ffad33;    /* Bright version for highlights */

/* Background */
--webtui-background: #000000;        /* Pure black background */
--webtui-background-elevated: #0a0e14; /* Slightly elevated panels */

/* Accents */
--webtui-accent: #00ffff;            /* Cyan accents for interactive elements */
--webtui-warning: #ff9500;           /* Amber warnings */
--webtui-error: #ff0000;             /* Red errors */
--webtui-success: #00ff00;           /* Green success (rare, prefer primary) */
```

### Typography

```css
--webtui-font-family: 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', monospace;
--webtui-font-size-sm: 10px;         /* Metadata, labels */
--webtui-font-size-base: 12px;       /* Body text */
--webtui-font-size-lg: 14px;         /* Emphasis */
--webtui-font-size-xl: 16px;         /* Subheadings */
--webtui-font-size-2xl: 20px;        /* Headings */
```

### Effects

```css
/* Phosphor glow effect */
--phosphor-glow: 0 0 8px rgba(255, 149, 0, 0.6),
                 0 0 16px rgba(255, 149, 0, 0.4),
                 0 0 24px rgba(255, 149, 0, 0.2);

/* Subtle glow for text */
--phosphor-glow-subtle: 0 0 4px rgba(255, 149, 0, 0.3),
                        0 0 8px rgba(255, 149, 0, 0.1);

/* Panel border glow */
--panel-glow: 0 0 15px rgba(255, 149, 0, 0.3);

/* Processing pulse animation */
@keyframes phosphor-pulse {
  0%, 100% {
    text-shadow: var(--phosphor-glow-subtle);
    opacity: 1;
  }
  50% {
    text-shadow: var(--phosphor-glow);
    opacity: 0.8;
  }
}
```

---

## Custom Styles Guidelines

### When to Use Custom CSS

**DO use custom CSS when:**
- Creating Synapse-specific components (ASCII charts, sparklines)
- Adding application-specific layouts
- Implementing unique interactions WebTUI doesn't provide
- Overriding WebTUI defaults for branding

**DON'T create custom CSS when:**
- WebTUI already provides the pattern (use `.webtui-*` classes)
- A theme variable can achieve the result
- Simple utility classes would suffice

**Good Example:**
```css
/* ✅ GOOD - Custom ASCII chart component */
@layer components {
  .synapse-ascii-chart {
    font-family: var(--webtui-font-family);
    font-size: 10px;
    line-height: 1.2;
    color: var(--webtui-primary);
    white-space: pre;
  }
}
```

**Bad Example:**
```css
/* ❌ BAD - Reinventing WebTUI panel */
.my-custom-panel {
  background: black;
  border: 1px solid #ff9500;
  padding: 12px;
}

/* ✅ GOOD - Use WebTUI class instead */
<div className="webtui-panel">...</div>
```

### Custom Style Template

When creating custom component styles, follow this pattern:

```css
@layer components {
  /* Component base */
  .synapse-component-name {
    /* Use theme variables */
    color: var(--webtui-primary);
    background: var(--webtui-background);
    font-family: var(--webtui-font-family);

    /* GPU acceleration for performance */
    transform: translateZ(0);
    will-change: transform;

    /* Smooth transitions */
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  /* Component variants */
  .synapse-component-name--variant {
    /* Variant-specific styles */
  }

  /* Component states */
  .synapse-component-name:hover {
    border-color: var(--webtui-accent);
    box-shadow: var(--panel-glow);
  }

  .synapse-component-name:focus-visible {
    outline: 2px solid var(--webtui-accent);
    outline-offset: 2px;
  }
}
```

---

## Common Patterns

### Responsive Grid

```tsx
{/* 2-column grid on desktop, 1-column on mobile */}
<div className="webtui-grid webtui-grid--2">
  <div className="webtui-panel">
    <div className="webtui-panel__header">MODEL STATUS</div>
    <div className="webtui-panel__content">
      {/* Model metrics */}
    </div>
  </div>

  <div className="webtui-panel">
    <div className="webtui-panel__header">QUERY METRICS</div>
    <div className="webtui-panel__content">
      {/* Query metrics */}
    </div>
  </div>
</div>

{/* 3-column grid */}
<div className="webtui-grid webtui-grid--3">
  <div className="webtui-panel">Panel 1</div>
  <div className="webtui-panel">Panel 2</div>
  <div className="webtui-panel">Panel 3</div>
</div>

{/* 4-column grid */}
<div className="webtui-grid webtui-grid--4">
  <div className="webtui-panel">Panel 1</div>
  <div className="webtui-panel">Panel 2</div>
  <div className="webtui-panel">Panel 3</div>
  <div className="webtui-panel">Panel 4</div>
</div>
```

### ASCII Chart Container

```tsx
<div className="webtui-panel">
  <div className="webtui-panel__header">
    MEMORY USAGE
  </div>
  <div className="webtui-panel__content">
    <div className="synapse-ascii-chart">
{`
100% ┤     ╭─╮
 75% ┤   ╭─╯ ╰╮
 50% ┤ ╭─╯    ╰─╮
 25% ┤─╯        ╰──
  0% ┴─────────────
     0  2  4  6  8
        (hours)
`}
    </div>
  </div>
</div>
```

### Metric Display

```tsx
<div className="webtui-panel">
  <div className="webtui-panel__header">
    SUBSTRATE METRICS
  </div>
  <div className="webtui-panel__content">
    <div className="webtui-grid webtui-grid--3">
      <div className="webtui-metric">
        <div className="webtui-metric__label">Q2 FAST</div>
        <div className="webtui-metric__value">45.2</div>
        <div className="webtui-metric__unit">tok/s</div>
      </div>

      <div className="webtui-metric">
        <div className="webtui-metric__label">Q3 BALANCED</div>
        <div className="webtui-metric__value">28.7</div>
        <div className="webtui-metric__unit">tok/s</div>
      </div>

      <div className="webtui-metric">
        <div className="webtui-metric__label">Q4 POWERFUL</div>
        <div className="webtui-metric__value">12.3</div>
        <div className="webtui-metric__unit">tok/s</div>
      </div>
    </div>
  </div>
</div>
```

---

## Additional Examples

### Combining Multiple Components

**Model Status Card with Metric + Sparkline + Status:**
```tsx
<div className="webtui-panel">
  <div className="webtui-panel__header">
    DeepSeek-V3
    <span className="webtui-status webtui-status--active">ACTIVE</span>
  </div>
  <div className="webtui-panel__content">
    <div className="webtui-metric">
      <div className="webtui-metric__label">TOKENS/SEC</div>
      <div className="webtui-metric__value">45.2</div>
      <div className="webtui-metric__unit">tok/s</div>
    </div>

    <div className="synapse-sparkline">
      ▁▂▃▅▇█████
    </div>

    <div className="webtui-metric">
      <div className="webtui-metric__label">MEMORY</div>
      <div className="webtui-metric__value">
        <span className="webtui-metric__value-primary">4.2</span>
        <span className="webtui-metric__value-secondary"> / 8.0</span>
      </div>
      <div className="webtui-metric__unit">GB</div>
    </div>
  </div>
</div>
```

**Multi-Tier Status Grid:**
```tsx
<div className="webtui-grid webtui-grid--3">
  {[
    { tier: 'Q2', status: 'active', throughput: 45.2 },
    { tier: 'Q3', status: 'processing', throughput: 28.7 },
    { tier: 'Q4', status: 'idle', throughput: 0 }
  ].map(model => (
    <div key={model.tier} className="webtui-panel">
      <div className="webtui-panel__header">
        {model.tier} TIER
        <span className={`webtui-status webtui-status--${model.status}`}>
          {model.status.toUpperCase()}
        </span>
      </div>
      <div className="webtui-panel__content">
        <div className="webtui-metric">
          <div className="webtui-metric__label">THROUGHPUT</div>
          <div className="webtui-metric__value">{model.throughput}</div>
          <div className="webtui-metric__unit">tok/s</div>
        </div>
      </div>
    </div>
  ))}
</div>
```

**Processing Pipeline Visualization:**
```tsx
<div className="webtui-panel">
  <div className="webtui-panel__header">PROCESSING PIPELINE</div>
  <div className="webtui-panel__content">
    <div className="synapse-pipeline">
      <div className="synapse-pipeline__stage synapse-pipeline__stage--complete">
        <div className="synapse-pipeline__stage-label">CGRAG</div>
        <div className="synapse-pipeline__stage-status">✓</div>
        <div className="synapse-pipeline__stage-time">52ms</div>
      </div>

      <div className="synapse-pipeline__connector">→</div>

      <div className="synapse-pipeline__stage synapse-pipeline__stage--active">
        <div className="synapse-pipeline__stage-label">Q3 MODEL</div>
        <div className="synapse-pipeline__stage-status">
          <span className="webtui-status webtui-status--processing">PROC</span>
        </div>
        <div className="synapse-pipeline__stage-time">2.1s</div>
      </div>

      <div className="synapse-pipeline__connector">→</div>

      <div className="synapse-pipeline__stage synapse-pipeline__stage--pending">
        <div className="synapse-pipeline__stage-label">WEB SEARCH</div>
        <div className="synapse-pipeline__stage-status">○</div>
        <div className="synapse-pipeline__stage-time">--</div>
      </div>
    </div>
  </div>
</div>
```

### Dynamic Classes with React

**Conditional Status Classes:**
```tsx
interface ModelStatusProps {
  status: 'active' | 'idle' | 'processing' | 'error';
}

const ModelStatus: React.FC<ModelStatusProps> = ({ status }) => (
  <span className={`webtui-status webtui-status--${status}`}>
    {status.toUpperCase()}
  </span>
);

// Usage
<ModelStatus status="active" />
<ModelStatus status="processing" />
```

**Dynamic Metric with Units:**
```tsx
interface MetricProps {
  label: string;
  value: number | string;
  unit?: string;
  status?: 'normal' | 'warning' | 'critical';
}

const Metric: React.FC<MetricProps> = ({ label, value, unit, status }) => (
  <div className={`webtui-metric ${status ? `webtui-metric--${status}` : ''}`}>
    <div className="webtui-metric__label">{label}</div>
    <div className="webtui-metric__value">
      {value}
      {unit && <span className="webtui-metric__unit">{unit}</span>}
    </div>
  </div>
);

// Usage
<Metric label="TOKENS/SEC" value={45.2} unit="tok/s" />
<Metric label="MEMORY" value="4.2 / 8.0" unit="GB" status="warning" />
```

**Animated State Transitions:**
```tsx
const [isProcessing, setIsProcessing] = useState(false);

<div className={`webtui-panel ${isProcessing ? 'webtui-panel--active' : ''}`}>
  <div className="webtui-panel__header">
    MODEL STATUS
    <span className={`webtui-status webtui-status--${isProcessing ? 'processing' : 'idle'}`}>
      {isProcessing ? 'PROCESSING' : 'IDLE'}
    </span>
  </div>
</div>
```

---

## Import Patterns

### Full WebTUI Import (Default)

**Recommended for most applications:**
```css
/* /frontend/src/assets/styles/main.css */
@layer base {
  @import '@webtui/css';
}
```

**Characteristics:**
- Imports complete WebTUI framework (~35KB minified)
- All components available
- Single HTTP request
- Best for applications using multiple WebTUI components

### Selective WebTUI Import (Advanced)

**For bundle size optimization:**
```css
/* Import only needed components */
@layer base {
  @import '@webtui/css/dist/base.css';              /* Required base styles */
  @import '@webtui/css/dist/components/panel.css';   /* Panel component */
  @import '@webtui/css/dist/components/metric.css';  /* Metric component */
  @import '@webtui/css/dist/components/status.css';  /* Status component */
  @import '@webtui/css/dist/utils/spacing.css';      /* Spacing utilities */
  @import '@webtui/css/dist/utils/grid.css';         /* Grid layout */
}
```

**Characteristics:**
- Smaller bundle size (import only what you use)
- Multiple HTTP requests (may be slower on HTTP/1.1)
- More maintenance overhead
- Best for single-page applications with limited component usage

**Bundle Size Comparison:**
- Full import: ~35KB minified (~8KB gzipped)
- Selective import (panel + metric + status): ~18KB minified (~5KB gzipped)

### React Component Import

**Main stylesheet is imported once in App.tsx:**
```tsx
// /frontend/src/App.tsx
import './assets/styles/main.css';

function App() {
  return <Router>{/* app content */}</Router>;
}
```

**DO NOT re-import in component files:**
```tsx
// ❌ BAD - Unnecessary re-import
import '../assets/styles/main.css';

const MyComponent = () => <div>...</div>;
```

**Exception - Component-specific styles:**
```tsx
// ✅ GOOD - Component-specific CSS module
import styles from './MyComponent.module.css';

const MyComponent = () => (
  <div className={styles.container}>...</div>
);
```

---

## Common Mistakes

### Mistake: Hardcoding Colors

**Problem:** Hardcoded colors break theming and make maintenance difficult.

```css
/* ❌ BAD - Hardcoded hex values */
.my-component {
  color: #ff9500;
  background: black;
  border: 1px solid #00ffff;
}

/* ✅ GOOD - Use theme variables */
.my-component {
  color: var(--webtui-primary);
  background: var(--webtui-background);
  border: 1px solid var(--webtui-accent);
}
```

**Why it matters:**
- Theme changes require updating every hardcoded value
- Inconsistent colors across components
- No support for theme switching (light/dark modes)

### Mistake: Fighting CSS Specificity

**Problem:** Using `!important` creates maintenance nightmares.

```css
/* ❌ BAD - Using !important to override */
.my-panel {
  border: 1px solid blue !important;
  background: gray !important;
}

/* ✅ GOOD - Use CSS layers for clean overrides */
@layer components {
  .my-panel {
    border: 1px solid var(--webtui-accent);
    background: var(--webtui-background-elevated);
  }
}
```

**Why it matters:**
- `!important` makes styles impossible to override later
- Creates specificity arms race
- CSS layers provide clean, predictable override mechanism

### Mistake: Breaking ASCII Alignment

**Problem:** Proportional fonts destroy ASCII art alignment.

```css
/* ❌ BAD - Proportional font breaks ASCII art */
.ascii-chart {
  font-family: Arial, sans-serif;
  letter-spacing: 2px;
  line-height: 1.5;
}

/* ✅ GOOD - Monospace font required for alignment */
.synapse-chart {
  font-family: var(--webtui-font-family);
  letter-spacing: 0;
  line-height: 1.2;
  white-space: pre;
}
```

**Why it matters:**
- ASCII art requires exact character width
- Letter spacing breaks box drawing characters
- Line height affects vertical alignment

**Correct ASCII rendering:**
```tsx
<div className="synapse-ascii-chart">
{`
┌─────────────────────┐
│  MEMORY USAGE       │
├─────────────────────┤
│ ████████░░░░  65%   │
│ ██████░░░░░░  48%   │
│ ███████████░  92%   │
└─────────────────────┘
`}
</div>
```

### Mistake: Overusing Glow Effects

**Problem:** Text shadows are GPU-intensive and can cause performance issues.

```css
/* ❌ BAD - Glow on every element */
* {
  text-shadow: var(--phosphor-glow);
}

.my-component, .my-component p, .my-component span {
  text-shadow: 0 0 10px rgba(255, 149, 0, 0.8);
}

/* ✅ GOOD - Glow on headers and important elements only */
h1, h2, .webtui-panel__header {
  text-shadow: var(--phosphor-glow-subtle);
}

.webtui-status--active {
  text-shadow: var(--phosphor-glow);
}
```

**Why it matters:**
- Text shadows trigger GPU compositing for every element
- Reduces frame rate, especially on lower-end devices
- Diminishes visual impact (everything glows = nothing stands out)

### Mistake: Blocking Main Thread

**Problem:** Heavy animations without GPU acceleration cause janky UI.

```css
/* ❌ BAD - Animating properties that trigger layout */
@keyframes slide {
  from {
    left: 0;
    width: 100px;
  }
  to {
    left: 200px;
    width: 200px;
  }
}

/* ✅ GOOD - GPU-accelerated transforms */
@keyframes slide {
  from {
    transform: translateX(0) scaleX(1);
  }
  to {
    transform: translateX(200px) scaleX(2);
  }
}

.animated-element {
  will-change: transform;
  transform: translateZ(0); /* Force GPU layer */
}
```

**Why it matters:**
- Animating `left`, `top`, `width`, `height` triggers layout recalculation
- Layout recalc blocks main thread (janky animations)
- `transform` and `opacity` are GPU-accelerated (smooth 60fps)

---

## Performance Tips

### Minimize Glow Effects

**Principle:** Glow effects are GPU-intensive. Use strategically for maximum impact with minimal performance cost.

```css
/* ✅ GOOD - Glow on headers only */
h1, h2, .webtui-panel__header {
  text-shadow: var(--phosphor-glow-subtle);
}

.webtui-status--active {
  text-shadow: var(--phosphor-glow);
  animation: phosphor-pulse 2s ease-in-out infinite;
}

/* ❌ BAD - Glow on every element */
* {
  text-shadow: var(--phosphor-glow);
}

p, span, div, label, input {
  text-shadow: 0 0 8px rgba(255, 149, 0, 0.6);
}
```

**Performance impact:**
- Glow on 100 elements: ~15fps drop on mid-range GPU
- Glow on 10 key elements: <2fps drop

### Optimize Animations

**Use `will-change` for animated elements:**
```css
/* ✅ GOOD - Declare intent to animate */
.webtui-status--active {
  animation: phosphor-pulse 2s ease-in-out infinite;
  will-change: text-shadow, opacity;
}

.webtui-panel:hover {
  will-change: box-shadow, border-color;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
```

**Remove `will-change` after animation:**
```css
/* ✅ GOOD - Clean up will-change */
.webtui-status--idle {
  will-change: auto;
}

.webtui-panel {
  will-change: auto;
}
```

**Why it matters:**
- `will-change` tells browser to create GPU layer in advance
- Prevents janky animation start
- Too many `will-change` declarations waste memory
- Always clean up after animation completes

**Example - Conditional will-change in React:**
```tsx
const [isProcessing, setIsProcessing] = useState(false);

<div
  className="webtui-status"
  style={{ willChange: isProcessing ? 'text-shadow, opacity' : 'auto' }}
>
  {status}
</div>
```

### Reduce Repaints

**Use transform instead of position changes:**

```css
/* ❌ BAD - Triggers layout recalculation */
@keyframes slide {
  from { left: 0; }
  to { left: 100px; }
}

@keyframes expand {
  from { width: 100px; height: 100px; }
  to { width: 200px; height: 200px; }
}

/* ✅ GOOD - GPU accelerated, no layout */
@keyframes slide {
  from { transform: translateX(0); }
  to { transform: translateX(100px); }
}

@keyframes expand {
  from { transform: scale(1); }
  to { transform: scale(2); }
}
```

**Properties that trigger layout (avoid in animations):**
- `width`, `height`, `padding`, `margin`
- `top`, `left`, `right`, `bottom`
- `border-width`
- `font-size`

**Properties that are GPU-accelerated (safe to animate):**
- `transform` (translate, scale, rotate)
- `opacity`
- `filter` (on some browsers)

**Example - Smooth panel expansion:**
```css
/* ❌ BAD - Janky height animation */
.webtui-panel--expanded {
  height: 500px;
  transition: height 0.3s ease;
}

/* ✅ GOOD - Smooth scale animation */
.webtui-panel--expanded {
  transform: scaleY(1.5);
  transform-origin: top center;
  transition: transform 0.3s ease;
}
```

### Debounce Rapid Updates

**Problem:** WebSocket events firing 60 times per second can overwhelm React rendering.

```tsx
/* ❌ BAD - Re-render on every WebSocket message */
useEffect(() => {
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setMetrics(data); // Triggers re-render 60 times/sec
  };
}, []);

/* ✅ GOOD - Debounce updates to 10fps */
import { useDebouncedCallback } from 'use-debounce';

const updateMetrics = useDebouncedCallback((data) => {
  setMetrics(data);
}, 100); // Update max 10 times per second

useEffect(() => {
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateMetrics(data);
  };
}, []);
```

**Debounce intervals by use case:**
- Live metrics: 100ms (10fps) - smooth enough, reduces render cost
- Status updates: 250ms (4fps) - status changes are infrequent
- Logs/text: 500ms (2fps) - text is readable at low refresh rates

### Virtual Scrolling for Long Lists

**Problem:** Rendering 1000+ log lines kills performance.

```tsx
/* ❌ BAD - Render all 1000 logs */
<div className="webtui-panel__content">
  {logs.map(log => (
    <div key={log.id} className="log-line">{log.message}</div>
  ))}
</div>

/* ✅ GOOD - Virtual scrolling with react-window */
import { FixedSizeList as List } from 'react-window';

<List
  height={600}
  itemCount={logs.length}
  itemSize={20}
  width="100%"
>
  {({ index, style }) => (
    <div style={style} className="log-line">
      {logs[index].message}
    </div>
  )}
</List>
```

**Performance impact:**
- 1000 DOM nodes: ~500ms render time, janky scrolling
- Virtual scrolling (render 30 visible): ~16ms render time, smooth 60fps

---

## Troubleshooting

### Issue: WebTUI styles not applying

**Symptoms:**
- Components appear unstyled
- Terminal aesthetic not visible
- Default browser styles showing

**Solutions:**

1. **Check import order in main.css:**
```css
/* ✅ Correct order */
@layer base, utils, components;

@layer base {
  @import '@webtui/css'; /* Must be first */
}

@layer utils {
  @import './theme.css';
}

@layer components {
  @import './components.css';
}
```

2. **Verify main.css is imported in App.tsx:**
```tsx
// App.tsx
import './assets/styles/main.css'; // Must be at top of imports
```

3. **Check WebTUI package installation:**
```bash
npm list @webtui/css
# Should show installed version
```

4. **Clear Vite cache and rebuild:**
```bash
docker-compose down
docker-compose build --no-cache synapse_frontend
docker-compose up -d
```

### Issue: Theme variables not working

**Symptoms:**
- Components still showing green phosphor (WebTUI default)
- Custom orange theme not applied
- Variables showing as literal strings in dev tools

**Solutions:**

1. **Verify theme.css is in utils layer:**
```css
@layer utils {
  @import './theme.css'; /* Must override base layer */
}
```

2. **Check variable names match exactly:**
```css
/* ✅ Correct variable name */
--webtui-primary: #ff9500;

/* ❌ Wrong - typo in name */
--webtui-primry: #ff9500;
```

3. **Ensure variables are declared in :root:**
```css
/* theme.css */
:root {
  --webtui-primary: #ff9500; /* Must be in :root */
}
```

### Issue: ASCII art misaligned

**Symptoms:**
- Box drawing characters don't connect
- Charts appear garbled
- Vertical/horizontal misalignment

**Solutions:**

1. **Use monospace font:**
```css
.synapse-ascii-chart {
  font-family: var(--webtui-font-family); /* Monospace required */
}
```

2. **Remove letter spacing:**
```css
.synapse-ascii-chart {
  letter-spacing: 0; /* No extra spacing */
}
```

3. **Set line height:**
```css
.synapse-ascii-chart {
  line-height: 1.2; /* Tight line height */
}
```

4. **Use `white-space: pre`:**
```css
.synapse-ascii-chart {
  white-space: pre; /* Preserve whitespace */
}
```

5. **Check character encoding:**
```tsx
{/* ✅ Use template literals for multi-line ASCII */}
<div className="synapse-ascii-chart">
{`
┌─────┐
│ OK  │
└─────┘
`}
</div>

{/* ❌ Don't use string concatenation */}
<div className="synapse-ascii-chart">
  "┌─────┐\n" +
  "│ OK  │\n" +
  "└─────┘"
</div>
```

### Issue: Animations janky or slow

**Symptoms:**
- Stuttering animations
- Frame rate drops
- Lag when hovering or transitioning

**Solutions:**

1. **Use GPU-accelerated properties:**
```css
/* ✅ GPU-accelerated */
@keyframes slide {
  from { transform: translateX(0); }
  to { transform: translateX(100px); }
}

/* ❌ CPU-bound, triggers layout */
@keyframes slide {
  from { left: 0; }
  to { left: 100px; }
}
```

2. **Add `will-change` for animated elements:**
```css
.animated-element {
  will-change: transform, opacity;
}
```

3. **Reduce glow effects:**
```css
/* Limit text-shadow to key elements only */
h1, h2, .webtui-panel__header {
  text-shadow: var(--phosphor-glow-subtle);
}
```

4. **Check browser DevTools Performance tab:**
- Look for long layout/paint times
- Identify expensive CSS selectors
- Monitor frame rate during animations

### Issue: Layout breaks at different screen sizes

**Symptoms:**
- Panels overflow on mobile
- Grid doesn't collapse to single column
- Text wraps incorrectly

**Solutions:**

1. **Use responsive grid classes:**
```tsx
{/* Automatically responsive */}
<div className="webtui-grid webtui-grid--2">
  <div className="webtui-panel">Panel 1</div>
  <div className="webtui-panel">Panel 2</div>
</div>
```

2. **Test at multiple breakpoints:**
- Desktop: 1920x1080
- Tablet: 768x1024
- Mobile: 375x667

3. **Use viewport units for critical dimensions:**
```css
.full-height-panel {
  height: 100vh;
  max-height: 100vh;
}
```

4. **Add overflow handling:**
```css
.webtui-panel__content {
  overflow-y: auto;
  max-height: 80vh;
}
```

---

## Related Documentation

- [WEBTUI_STYLE_GUIDE.md](./WEBTUI_STYLE_GUIDE.md) - Comprehensive style guide for custom components
- [DENSE_TERMINAL_MOCKUPS.md](./DENSE_TERMINAL_MOCKUPS.md) - Visual mockups and design specifications
- [ASCII_LIBRARIES_RESEARCH.md](./ASCII_LIBRARIES_RESEARCH.md) - Research on ASCII visualization libraries
- [CLAUDE.md](../CLAUDE.md) - Project context and development guidelines
- [SESSION_NOTES.md](../SESSION_NOTES.md) - Recent implementation history
- [docker-compose.yml](../docker-compose.yml) - Frontend build configuration

---

## Appendix: Complete Class Reference

### WebTUI Base Classes

**Layout:**
- `.webtui-grid` - Grid container
- `.webtui-grid--2` - 2-column grid
- `.webtui-grid--3` - 3-column grid
- `.webtui-grid--4` - 4-column grid

**Components:**
- `.webtui-panel` - Panel container
- `.webtui-panel__header` - Panel header
- `.webtui-panel__content` - Panel content
- `.webtui-metric` - Metric display
- `.webtui-metric__label` - Metric label
- `.webtui-metric__value` - Metric value
- `.webtui-metric__unit` - Metric unit
- `.webtui-status` - Status indicator
- `.webtui-status--active` - Active state (pulsing orange)
- `.webtui-status--idle` - Idle state (dim orange)
- `.webtui-status--processing` - Processing state (pulsing cyan)
- `.webtui-status--error` - Error state (red)

### Synapse Custom Classes

**Components:**
- `.synapse-ascii-chart` - ASCII art container
- `.synapse-sparkline` - Inline sparkline
- `.synapse-pipeline` - Pipeline visualization container
- `.synapse-pipeline__stage` - Pipeline stage
- `.synapse-pipeline__stage--complete` - Completed stage
- `.synapse-pipeline__stage--active` - Active stage
- `.synapse-pipeline__stage--pending` - Pending stage
- `.synapse-pipeline__connector` - Stage connector (arrow)

**Utilities:**
- `.synapse-glow` - Apply phosphor glow effect
- `.synapse-glow-subtle` - Apply subtle glow effect
- `.synapse-mono` - Force monospace font
- `.synapse-nowrap` - Prevent text wrapping

---

**Last Updated:** 2025-11-08
**Maintainer:** Synapse Engine Development Team
**License:** MIT
