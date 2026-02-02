# Synapse Engine - WebTUI Style Guide

**Date:** 2025-11-08
**Version:** 1.0
**Audience:** All developers
**Status:** Authoritative styling reference

---

## Table of Contents

1. [Styling Philosophy](#styling-philosophy)
2. [Component Development Workflow](#component-development-workflow)
3. [Class Naming Convention](#class-naming-convention)
4. [Color Usage](#color-usage)
5. [Typography](#typography)
6. [Spacing](#spacing)
7. [Animations](#animations)
8. [Responsive Design](#responsive-design)
9. [CSS Architecture Diagram](#css-architecture-diagram)
10. [Real-World Examples](#real-world-examples)
11. [Migration Guide](#migration-guide)
12. [Common Pitfalls](#common-pitfalls)
13. [Code Review Checklist](#code-review-checklist)
14. [Related Documentation](#related-documentation)

---

## Styling Philosophy

Synapse Engine uses a **three-layer styling approach** for maintainability, consistency, and performance:

### Layer 1: WebTUI Foundation
**What:** Base terminal-aesthetic styles from [@webtui/css](https://github.com/Ztkent/webtui-css)
**Purpose:** Provides foundational terminal UI elements (panels, buttons, inputs, grids)
**Customization:** None - use as-is for consistency

### Layer 2: Synapse Theme
**What:** Project-specific color palette, spacing, and animation overrides
**File:** [`frontend/src/styles/theme.css`](../frontend/src/styles/theme.css)
**Purpose:** Phosphor orange (#ff9500) branding, glow effects, custom animations

### Layer 3: Component-Specific Styles
**What:** Custom classes for domain-specific components
**File:** [`frontend/src/styles/components.css`](../frontend/src/styles/components.css)
**Purpose:** Layout, metrics displays, status indicators, ASCII visualizations

**Key Principle:** Use WebTUI classes first, extend with Synapse classes only when needed.

---

## Component Development Workflow

Follow this process when creating or updating UI components:

### Step 1: Check WebTUI Coverage
Before writing custom CSS, check if WebTUI provides the component:

```tsx
// ✅ GOOD - Uses WebTUI panel directly
<div className="synapse-panel">
  <div className="synapse-panel__header">Model Status</div>
  <div className="synapse-panel__content">
    {/* content */}
  </div>
</div>

// ❌ BAD - Reinventing WebTUI panel
<div className="custom-panel" style={{ border: '1px solid #ff9500', padding: '1rem' }}>
  <h3>Model Status</h3>
  <div>{/* content */}</div>
</div>
```

**WebTUI Components Available:**
- `.synapse-panel` (boxed sections with headers)
- `.synapse-button` (terminal-styled buttons)
- `.synapse-input` (text inputs)
- `.synapse-grid` (responsive grid layouts)
- `.synapse-table` (data tables)

### Step 2: Apply Synapse Theme
Use CSS variables from [`theme.css`](../frontend/src/styles/theme.css) for colors and spacing:

```tsx
// ✅ GOOD - Uses CSS variables
<div style={{
  color: 'var(--webtui-primary)',
  padding: 'var(--webtui-spacing-md)'
}}>
  Status: ACTIVE
</div>

// ❌ BAD - Hardcoded values
<div style={{ color: '#ff9500', padding: '16px' }}>
  Status: ACTIVE
</div>
```

### Step 3: Add Custom Classes (If Needed)
Only create custom classes for domain-specific components not covered by WebTUI:

```css
/* ✅ GOOD - Custom metric component in components.css */
.synapse-metric {
  display: flex;
  flex-direction: column;
  gap: var(--webtui-spacing-sm);
}

.synapse-metric__label {
  font-size: var(--webtui-font-size-sm);
  color: var(--webtui-text-muted);
}

.synapse-metric__value {
  font-size: var(--webtui-font-size-xl);
  color: var(--webtui-primary);
}

/* ❌ BAD - Duplicating WebTUI functionality */
.custom-panel {
  border: 1px solid var(--webtui-border);
  /* This is already provided by .synapse-panel */
}
```

### Step 4: Test Responsive Behavior
Verify layout works at all breakpoints:

```bash
# Test at these viewport widths:
# Mobile: 375px, 414px
# Tablet: 768px, 1024px
# Desktop: 1280px, 1440px
# Wide: 1920px, 2560px
```

---

## Class Naming Convention

### WebTUI Classes (Use As-Is)
- **Prefix:** `synapse-`
- **Pattern:** BEM (Block Element Modifier)
- **Examples:**
  - `.synapse-panel` (block)
  - `.synapse-panel__header` (element)
  - `.synapse-button--primary` (modifier)

### Synapse Custom Classes (Create When Needed)
- **Prefix:** `synapse-`
- **Pattern:** BEM with descriptive names
- **Examples:**
  - `.synapse-metric` (metric display block)
  - `.synapse-metric__label` (metric label element)
  - `.synapse-status--active` (status modifier)

### Naming Rules
1. **Always prefix with `synapse-`** for namespacing
2. **Use BEM notation:**
   - Block: `.synapse-block`
   - Element: `.synapse-block__element`
   - Modifier: `.synapse-block--modifier`
3. **Use kebab-case** for multi-word names: `.synapse-model-status`
4. **Be descriptive:** `.synapse-query-input` not `.synapse-qi`
5. **Avoid abbreviations** unless universally understood (e.g., `qps`, `cpu`)

**Examples:**

```tsx
// ✅ GOOD - Clear, consistent naming
<div className="synapse-panel">
  <div className="synapse-panel__header">Neural Substrate</div>
  <div className="synapse-panel__content">
    <div className="synapse-metric">
      <span className="synapse-metric__label">QPS</span>
      <span className="synapse-metric__value">42.5</span>
    </div>
  </div>
</div>

// ❌ BAD - Inconsistent, unclear naming
<div className="panel">
  <div className="hdr">Neural Substrate</div>
  <div className="cont">
    <div className="met">
      <span className="lbl">QPS</span>
      <span className="val">42.5</span>
    </div>
  </div>
</div>
```

---

## Color Usage

### Primary Palette

| Variable | Value | Usage |
|----------|-------|-------|
| `--webtui-primary` | `#ff9500` | Primary text, borders, headers (phosphor orange) |
| `--webtui-background` | `#000000` | Panel backgrounds (pure black) |
| `--webtui-text-muted` | `#999999` | Secondary text, labels |
| `--webtui-border` | `#ff9500` | Panel borders, dividers |

### State Colors

| Variable | Value | Usage |
|----------|-------|-------|
| `--synapse-success` | `#00ff00` | Success states, healthy status |
| `--synapse-warning` | `#ff9500` | Warnings, degraded performance |
| `--synapse-error` | `#ff0000` | Errors, critical alerts |
| `--synapse-processing` | `#00ffff` | Active processing, pending states |

### Glow Effects

```css
/* Phosphor glow for headers and key elements */
--phosphor-glow: 0 0 10px rgba(255, 149, 0, 0.5);
--phosphor-glow-strong: 0 0 20px rgba(255, 149, 0, 0.8);

/* Cyan glow for processing indicators */
--cyan-glow: 0 0 10px rgba(0, 255, 255, 0.5);
```

**Usage Guidelines:**

```css
/* ✅ GOOD - Glow on headers and key elements */
.synapse-panel__header {
  text-shadow: var(--phosphor-glow);
}

.synapse-status--processing {
  box-shadow: var(--cyan-glow);
}

/* ❌ BAD - Excessive glow on all elements */
.synapse-panel {
  box-shadow: var(--phosphor-glow); /* Too much */
}

.synapse-metric__value {
  text-shadow: var(--phosphor-glow); /* Overused */
}
```

**Color Usage Rules:**
1. **Always use CSS variables** - never hardcode hex values
2. **Phosphor orange is primary** - use for all main UI elements
3. **State colors are semantic** - green = good, red = bad, cyan = active
4. **Glow effects sparingly** - headers and key indicators only
5. **High contrast required** - ensure text readable on black background

---

## Typography

### Font Stack

```css
/* Primary font (all UI text) */
--webtui-font-family: 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', 'Courier New', monospace;

/* Display font (large headers) */
--synapse-font-display: 'Share Tech Mono', 'JetBrains Mono', monospace;
```

### Font Sizes

| Variable | Value | Usage |
|----------|-------|-------|
| `--webtui-font-size-xs` | `10px` | Metadata, timestamps |
| `--webtui-font-size-sm` | `12px` | Labels, secondary text |
| `--webtui-font-size-md` | `14px` | Body text, inputs |
| `--webtui-font-size-lg` | `16px` | Primary content |
| `--webtui-font-size-xl` | `18px` | Section headers |
| `--webtui-font-size-2xl` | `20px` | Page headers |

### Typography Rules

```tsx
// ✅ GOOD - Monospace for ASCII content
<pre className="synapse-chart" style={{ fontFamily: 'var(--webtui-font-family)' }}>
  ██████░░░░ 60%
  ████████░░ 80%
</pre>

// ❌ BAD - Sans-serif destroys alignment
<div style={{ fontFamily: 'Arial, sans-serif' }}>
  ██████░░░░ 60%
  ████████░░ 80%
</div>

// ✅ GOOD - Proper size hierarchy
<div className="synapse-panel">
  <div className="synapse-panel__header" style={{ fontSize: 'var(--webtui-font-size-xl)' }}>
    Model Status
  </div>
  <div className="synapse-metric__label" style={{ fontSize: 'var(--webtui-font-size-sm)' }}>
    Latency
  </div>
</div>
```

---

## Spacing

### Spacing Scale

```css
--webtui-spacing-xs: 4px;   /* Tight spacing (icons, badges) */
--webtui-spacing-sm: 8px;   /* Small gaps (list items) */
--webtui-spacing-md: 16px;  /* Standard spacing (panel padding) */
--webtui-spacing-lg: 24px;  /* Large gaps (section separation) */
--webtui-spacing-xl: 32px;  /* Extra large (page margins) */
```

### Spacing Rules

```css
/* ✅ GOOD - Use spacing variables */
.synapse-metric {
  padding: var(--webtui-spacing-md);
  gap: var(--webtui-spacing-sm);
}

/* ❌ BAD - Hardcoded pixel values */
.synapse-metric {
  padding: 16px;
  gap: 8px;
}

/* ✅ GOOD - Consistent spacing across components */
.synapse-panel {
  margin-bottom: var(--webtui-spacing-lg);
}

.synapse-grid {
  gap: var(--webtui-spacing-md);
}
```

---

## Animations

### Predefined Animations

```css
/* Pulse animation for processing states */
@keyframes synapse-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.synapse-status--processing {
  animation: synapse-pulse 2s ease-in-out infinite;
}

/* Glow pulse for alerts */
@keyframes synapse-glow-pulse {
  0%, 100% { box-shadow: 0 0 5px rgba(255, 149, 0, 0.3); }
  50% { box-shadow: 0 0 20px rgba(255, 149, 0, 0.8); }
}

.synapse-alert {
  animation: synapse-glow-pulse 1.5s ease-in-out infinite;
}

/* Fade in for new elements */
@keyframes synapse-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.synapse-panel {
  animation: synapse-fade-in 0.3s ease-in;
}
```

### Animation Guidelines

```css
/* ✅ GOOD - Smooth, performant animation */
.synapse-status {
  transition: all 0.2s ease-in-out;
  will-change: background-color, color;
}

.synapse-status:hover {
  background-color: var(--webtui-primary);
}

/* ❌ BAD - Janky, expensive animation */
.synapse-status {
  transition: all 0.5s linear; /* Too slow */
}

.synapse-status:hover {
  box-shadow: 0 0 50px rgba(255, 149, 0, 1); /* Too heavy */
  transform: scale(1.5); /* Jarring */
}
```

**Animation Rules:**
1. **Use transitions for state changes** (hover, active, focus)
2. **Use keyframe animations for continuous effects** (pulse, glow)
3. **Keep durations short** (0.2s-0.3s for transitions, 1-2s for keyframes)
4. **Use `ease-in-out` easing** for smooth motion
5. **Add `will-change`** for frequently animated properties
6. **Respect `prefers-reduced-motion`** for accessibility

```css
/* Accessibility: disable animations if user prefers */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile first approach */
--webtui-breakpoint-sm: 768px;   /* Tablet */
--webtui-breakpoint-md: 1280px;  /* Desktop */
--webtui-breakpoint-lg: 1920px;  /* Wide */
```

### Grid System

```css
/* Responsive grid with auto-sizing */
.synapse-grid {
  display: grid;
  gap: var(--webtui-spacing-md);
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

/* Fixed column grids */
.synapse-grid--2col { grid-template-columns: repeat(2, 1fr); }
.synapse-grid--3col { grid-template-columns: repeat(3, 1fr); }
.synapse-grid--4col { grid-template-columns: repeat(4, 1fr); }

/* Responsive overrides */
@media (max-width: 768px) {
  .synapse-grid--2col,
  .synapse-grid--3col,
  .synapse-grid--4col {
    grid-template-columns: 1fr; /* Stack on mobile */
  }
}
```

### Responsive Patterns

```tsx
// ✅ GOOD - Responsive grid with auto-fit
<div className="synapse-grid">
  {metrics.map(metric => (
    <div key={metric.id} className="synapse-metric">
      {/* Content */}
    </div>
  ))}
</div>

// ✅ GOOD - Explicit column count with mobile override
<div className="synapse-grid synapse-grid--3col">
  {/* 3 columns on desktop, 1 on mobile */}
</div>

// ❌ BAD - Fixed width, no responsiveness
<div style={{ display: 'flex', width: '1200px' }}>
  {/* Breaks on small screens */}
</div>
```

---

## CSS Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│  (Renders combined CSS with cascade resolution)            │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
              ┌────────────┴────────────┐
              │     main.css (Entry)     │
              │   @layer base, utils,    │
              │       components         │
              │  Import order matters!   │
              └────────────┬─────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    ┌─────────┐      ┌──────────┐     ┌──────────────┐
    │ WebTUI  │      │  theme   │     │ components   │
    │base.css │      │  .css    │     │    .css      │
    │ (Layer 1)│      │(Layer 2) │     │  (Layer 3)   │
    └─────────┘      └──────────┘     └──────────────┘
         │                 │                  │
         ▼                 ▼                  ▼
   Terminal          Phosphor             Synapse
   Aesthetics         Orange              Components
   (Panels,           Theme               (Metrics,
   Buttons,          (Colors,             Status,
   Inputs,           Glow,                Charts,
   Grids)            Spacing)             Layouts)
         │                 │                  │
         └─────────────────┴──────────────────┘
                           │
                           ▼
                  Combined Stylesheet
                  (Loaded by browser)

Flow:
1. Browser requests main.css
2. main.css imports in order:
   - @webtui/css (WebTUI base)
   - theme.css (overrides WebTUI vars)
   - components.css (custom classes)
3. CSS layers ensure proper cascade
4. CSS variables allow runtime theming
```

**File Locations:**
- Entry: [`frontend/src/styles/main.css`](../frontend/src/styles/main.css)
- WebTUI: `node_modules/@webtui/css/dist/index.css` (external)
- Theme: [`frontend/src/styles/theme.css`](../frontend/src/styles/theme.css)
- Components: [`frontend/src/styles/components.css`](../frontend/src/styles/components.css)

---

## Real-World Examples

### Example 1: Model Status Panel

**File:** `/frontend/src/components/models/ModelStatusPanel.tsx`

```tsx
import React from 'react';

interface Model {
  id: string;
  name: string;
  tier: 'Q2' | 'Q3' | 'Q4';
  status: 'active' | 'idle' | 'processing' | 'error';
  memoryUsed: number;
  memoryTotal: number;
  qps: number;
}

const ModelStatusPanel: React.FC<{ models: Model[] }> = ({ models }) => (
  <div className="synapse-panel">
    <div className="synapse-panel__header">
      Neural Substrate Status
    </div>
    <div className="synapse-panel__content">
      <div className="synapse-grid synapse-grid--3col">
        {models.map(model => (
          <div key={model.id} className="synapse-metric">
            {/* Model name and tier */}
            <div className="synapse-metric__label">
              {model.name} ({model.tier})
            </div>

            {/* Status with color coding */}
            <div className="synapse-metric__value">
              <span className={`synapse-status synapse-status--${model.status}`}>
                {model.status.toUpperCase()}
              </span>
            </div>

            {/* Memory usage bar */}
            <div className="synapse-progress-bar">
              <div
                className="synapse-progress-bar__fill"
                style={{
                  width: `${(model.memoryUsed / model.memoryTotal) * 100}%`
                }}
              />
              <span className="synapse-progress-bar__label">
                {model.memoryUsed}MB / {model.memoryTotal}MB
              </span>
            </div>

            {/* QPS metric */}
            <div className="synapse-metric__sublabel">
              QPS: {model.qps.toFixed(1)}
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default ModelStatusPanel;
```

**CSS (components.css):**

```css
/* Status indicator with state-based colors */
.synapse-status {
  display: inline-block;
  padding: var(--webtui-spacing-xs) var(--webtui-spacing-sm);
  border: 1px solid var(--webtui-border);
  font-size: var(--webtui-font-size-sm);
  font-family: var(--webtui-font-family);
  text-transform: uppercase;
}

.synapse-status--active {
  color: var(--synapse-success);
  border-color: var(--synapse-success);
  box-shadow: 0 0 5px rgba(0, 255, 0, 0.3);
}

.synapse-status--processing {
  color: var(--synapse-processing);
  border-color: var(--synapse-processing);
  animation: synapse-pulse 2s ease-in-out infinite;
}

.synapse-status--error {
  color: var(--synapse-error);
  border-color: var(--synapse-error);
  box-shadow: 0 0 5px rgba(255, 0, 0, 0.3);
}

/* Progress bar for memory usage */
.synapse-progress-bar {
  position: relative;
  width: 100%;
  height: 20px;
  border: 1px solid var(--webtui-border);
  background: transparent;
  overflow: hidden;
}

.synapse-progress-bar__fill {
  height: 100%;
  background: var(--webtui-primary);
  transition: width 0.3s ease-in-out;
}

.synapse-progress-bar__label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: var(--webtui-font-size-xs);
  color: var(--webtui-text);
  text-shadow: 0 0 3px rgba(0, 0, 0, 0.8);
  z-index: 1;
}
```

**Why This Works:**
- ✅ Uses WebTUI `.synapse-panel` structure
- ✅ Custom `.synapse-status` for state indicators
- ✅ State-based modifiers (--active, --processing, --error)
- ✅ CSS variables for all colors and spacing
- ✅ Smooth animations for visual feedback
- ✅ Responsive grid with `.synapse-grid--3col`

---

### Example 2: Real-Time Metrics Dashboard

**File:** `/frontend/src/components/dashboard/MetricsPanel.tsx`

```tsx
import React from 'react';

interface Metrics {
  qps: number;
  qpsHistory: number[];
  latency: number;
  latencyHistory: number[];
  cacheHitRate: number;
  activeConnections: number;
}

const MetricsPanel: React.FC<{ metrics: Metrics }> = ({ metrics }) => {
  const generateSparkline = (data: number[]): string => {
    const max = Math.max(...data);
    const bars = '▁▂▃▄▅▆▇█';
    return data
      .map(val => bars[Math.floor((val / max) * (bars.length - 1))])
      .join('');
  };

  return (
    <div className="synapse-panel">
      <div className="synapse-panel__header">System Performance</div>
      <div className="synapse-panel__content">
        <div className="synapse-grid synapse-grid--4col">
          {/* QPS Metric */}
          <div className="synapse-metric">
            <div className="synapse-metric__label">Queries/Sec</div>
            <div className="synapse-metric__value">
              {metrics.qps.toFixed(1)}
              <span className="synapse-metric__unit">q/s</span>
            </div>
            <div className="synapse-sparkline">
              {generateSparkline(metrics.qpsHistory)}
            </div>
          </div>

          {/* Latency Metric */}
          <div className="synapse-metric">
            <div className="synapse-metric__label">Avg Latency</div>
            <div className="synapse-metric__value">
              {metrics.latency.toFixed(0)}
              <span className="synapse-metric__unit">ms</span>
            </div>
            <div className="synapse-sparkline">
              {generateSparkline(metrics.latencyHistory)}
            </div>
          </div>

          {/* Cache Hit Rate */}
          <div className="synapse-metric">
            <div className="synapse-metric__label">Cache Hit Rate</div>
            <div className="synapse-metric__value">
              {(metrics.cacheHitRate * 100).toFixed(1)}
              <span className="synapse-metric__unit">%</span>
            </div>
            <div className="synapse-progress-bar">
              <div
                className="synapse-progress-bar__fill"
                style={{ width: `${metrics.cacheHitRate * 100}%` }}
              />
            </div>
          </div>

          {/* Active Connections */}
          <div className="synapse-metric">
            <div className="synapse-metric__label">Active Connections</div>
            <div className="synapse-metric__value">
              {metrics.activeConnections}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsPanel;
```

**CSS (components.css):**

```css
/* Metric display component */
.synapse-metric {
  display: flex;
  flex-direction: column;
  gap: var(--webtui-spacing-sm);
  padding: var(--webtui-spacing-md);
  border: 1px solid var(--webtui-border);
  background: rgba(0, 0, 0, 0.5);
}

.synapse-metric__label {
  font-size: var(--webtui-font-size-sm);
  color: var(--webtui-text-muted);
  text-transform: uppercase;
}

.synapse-metric__value {
  font-size: var(--webtui-font-size-2xl);
  color: var(--webtui-primary);
  font-family: var(--webtui-font-family);
  line-height: 1;
}

.synapse-metric__unit {
  font-size: var(--webtui-font-size-sm);
  color: var(--webtui-text-muted);
  margin-left: var(--webtui-spacing-xs);
}

.synapse-metric__sublabel {
  font-size: var(--webtui-font-size-xs);
  color: var(--webtui-text-muted);
}

/* ASCII sparkline */
.synapse-sparkline {
  font-family: var(--webtui-font-family);
  font-size: var(--webtui-font-size-lg);
  color: var(--webtui-primary);
  letter-spacing: 2px;
  white-space: pre;
  overflow-x: auto;
}
```

**Why This Works:**
- ✅ Combines WebTUI structure with custom metric displays
- ✅ ASCII sparklines use monospace font
- ✅ Responsive 4-column grid
- ✅ Units displayed consistently
- ✅ Real-time updates via props
- ✅ Clean separation of label/value/visualization

---

### Example 3: ASCII Chart Visualization

**File:** `/frontend/src/components/visualizations/ASCIIChart.tsx`

```tsx
import React from 'react';

interface ChartProps {
  title: string;
  data: { label: string; value: number }[];
  maxValue?: number;
}

const ASCIIChart: React.FC<ChartProps> = ({ title, data, maxValue }) => {
  const max = maxValue || Math.max(...data.map(d => d.value));
  const barLength = 40; // characters

  const generateBar = (value: number): string => {
    const filled = Math.floor((value / max) * barLength);
    const empty = barLength - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  };

  return (
    <div className="synapse-panel">
      <div className="synapse-panel__header">{title}</div>
      <div className="synapse-panel__content">
        <div className="synapse-chart">
          {data.map(({ label, value }) => (
            <div key={label} className="synapse-chart__row">
              <span className="synapse-chart__label">
                {label.padEnd(15)}
              </span>
              <span className="synapse-chart__bar">
                {generateBar(value)}
              </span>
              <span className="synapse-chart__value">
                {value.toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ASCIIChart;
```

**CSS (components.css):**

```css
/* ASCII chart container */
.synapse-chart {
  font-family: var(--webtui-font-family);
  font-size: var(--webtui-font-size-sm);
  line-height: 1.8;
  white-space: pre;
  overflow-x: auto;
}

.synapse-chart__row {
  display: flex;
  gap: var(--webtui-spacing-sm);
  align-items: center;
}

.synapse-chart__label {
  color: var(--webtui-text-muted);
  min-width: 120px;
}

.synapse-chart__bar {
  color: var(--webtui-primary);
  flex: 1;
}

.synapse-chart__value {
  color: var(--webtui-primary);
  min-width: 60px;
  text-align: right;
}
```

**Why This Works:**
- ✅ Monospace font ensures bar alignment
- ✅ `white-space: pre` preserves spacing
- ✅ Flexbox for label/bar/value layout
- ✅ Horizontal scroll for overflow
- ✅ Consistent color scheme
- ✅ Dynamic bar generation based on data

---

## Migration Guide

### Migrating Existing Components to WebTUI

This guide helps transition legacy components to the WebTUI + Synapse styling system.

---

#### Step 1: Identify Custom Styles

Find components with inline styles or custom CSS modules:

```bash
# Find inline styles
grep -r "style={{" frontend/src/components/

# Find CSS modules
grep -r "\.module\.css" frontend/src/components/

# Find hardcoded colors
grep -r "#[0-9a-fA-F]\{6\}" frontend/src/components/ --include="*.tsx" --include="*.ts"
```

---

#### Step 2: Map to WebTUI Classes

Use this table to identify equivalent WebTUI classes:

| Old Pattern | New WebTUI Pattern | Notes |
|-------------|-------------------|-------|
| `<div className="panel">` | `<div className="synapse-panel">` | WebTUI panel structure |
| `<div className="panel-header">` | `<div className="synapse-panel__header">` | BEM element syntax |
| `<div className="panel-content">` | `<div className="synapse-panel__content">` | BEM element syntax |
| `<div className="status-active">` | `<span className="synapse-status synapse-status--active">` | Custom component |
| `<div className="metric-container">` | `<div className="synapse-metric">` | Custom component |
| `<div className="grid-3">` | `<div className="synapse-grid synapse-grid--3col">` | Responsive grid |
| `<button className="btn-primary">` | `<button className="synapse-button synapse-button--primary">` | WebTUI button |
| `<input className="text-input">` | `<input className="synapse-input" />` | WebTUI input |
| `<table className="data-table">` | `<table className="synapse-table">` | WebTUI table |

---

#### Step 3: Update Component

**Before Migration:**

```tsx
// ❌ OLD - Custom CSS module approach
import React from 'react';
import styles from './Panel.module.css';

interface PanelProps {
  title: string;
  status: 'active' | 'idle';
  children: React.ReactNode;
}

const Panel: React.FC<PanelProps> = ({ title, status, children }) => (
  <div className={styles.panel}>
    <h2 className={styles.header}>{title}</h2>
    <div className={`${styles.status} ${styles[`status-${status}`]}`}>
      {status}
    </div>
    <div className={styles.content}>
      {children}
    </div>
  </div>
);

export default Panel;
```

```css
/* Panel.module.css */
.panel {
  border: 1px solid #ff9500;
  padding: 16px;
  margin-bottom: 24px;
  background: #000;
}

.header {
  font-size: 18px;
  color: #ff9500;
  margin-bottom: 12px;
  text-shadow: 0 0 10px rgba(255, 149, 0, 0.5);
}

.status {
  display: inline-block;
  padding: 4px 8px;
  border: 1px solid #ff9500;
  font-size: 12px;
  text-transform: uppercase;
}

.status-active {
  color: #00ff00;
  border-color: #00ff00;
}

.status-idle {
  color: #999;
  border-color: #999;
}

.content {
  margin-top: 16px;
}
```

**After Migration:**

```tsx
// ✅ NEW - WebTUI + Synapse approach
import React from 'react';

interface PanelProps {
  title: string;
  status: 'active' | 'idle';
  children: React.ReactNode;
}

const Panel: React.FC<PanelProps> = ({ title, status, children }) => (
  <div className="synapse-panel">
    <div className="synapse-panel__header">{title}</div>
    <div className="synapse-panel__content">
      <span className={`synapse-status synapse-status--${status}`}>
        {status}
      </span>
      {children}
    </div>
  </div>
);

export default Panel;
```

**Changes Made:**
1. ✅ Removed CSS module import
2. ✅ Replaced `.panel` with `.synapse-panel`
3. ✅ Replaced `.header` with `.synapse-panel__header`
4. ✅ Replaced `.content` with `.synapse-panel__content`
5. ✅ Replaced custom status classes with `.synapse-status` + modifiers
6. ✅ Removed all inline styles and hardcoded values
7. ✅ Deleted `Panel.module.css` file

---

#### Step 4: Remove Old CSS

After successful migration, delete old CSS files:

```bash
# Delete CSS module
rm frontend/src/components/Panel/Panel.module.css

# Verify no imports remain
grep -r "Panel.module.css" frontend/src/
```

---

#### Step 5: Test Responsive Behavior

Test at all standard breakpoints:

```bash
# Mobile
# - 375px (iPhone SE)
# - 414px (iPhone Pro Max)

# Tablet
# - 768px (iPad Portrait)
# - 1024px (iPad Landscape)

# Desktop
# - 1280px (Standard laptop)
# - 1440px (Large laptop)

# Wide
# - 1920px (Full HD)
# - 2560px (2K display)
```

**Testing Checklist:**
- [ ] Layout doesn't break at any breakpoint
- [ ] Text remains readable (no overflow)
- [ ] Panels stack correctly on mobile
- [ ] Grids collapse to single column appropriately
- [ ] Spacing remains consistent
- [ ] Glow effects render correctly
- [ ] Animations don't cause jank

---

#### Step 6: Verify Accessibility

```bash
# Run accessibility audit
npm run test:a11y

# Check for ARIA attributes
grep -r "aria-" frontend/src/components/Panel/
```

**Accessibility Checklist:**
- [ ] Sufficient color contrast (use browser DevTools)
- [ ] Keyboard navigation works
- [ ] Screen reader labels present
- [ ] Focus indicators visible
- [ ] Status changes announced
- [ ] Animations respect `prefers-reduced-motion`

---

### Common Migration Scenarios

#### Scenario 1: Hardcoded Colors

**Before:**
```tsx
<div style={{ color: '#ff9500', borderColor: '#ff9500' }}>
  Status
</div>
```

**After:**
```tsx
<div style={{
  color: 'var(--webtui-primary)',
  borderColor: 'var(--webtui-border)'
}}>
  Status
</div>
```

#### Scenario 2: Fixed Pixel Spacing

**Before:**
```css
.container {
  padding: 16px;
  margin-bottom: 24px;
  gap: 8px;
}
```

**After:**
```css
.container {
  padding: var(--webtui-spacing-md);
  margin-bottom: var(--webtui-spacing-lg);
  gap: var(--webtui-spacing-sm);
}
```

#### Scenario 3: Custom Grid Layout

**Before:**
```css
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
```

**After:**
```tsx
<div className="synapse-grid synapse-grid--3col">
  {/* WebTUI handles responsive breakpoints */}
</div>
```

#### Scenario 4: Sans-Serif Fonts

**Before:**
```css
.text {
  font-family: Arial, sans-serif;
  font-size: 14px;
}
```

**After:**
```css
.text {
  font-family: var(--webtui-font-family);
  font-size: var(--webtui-font-size-md);
}
```

---

### Migration Timeline

**Small Components (1-2 files):**
- Estimated time: 15-30 minutes per component
- Steps: Identify → Map → Update → Test → Delete old CSS

**Medium Components (3-5 files):**
- Estimated time: 1-2 hours per component
- Steps: Audit → Plan → Migrate → Test responsive → Verify a11y

**Large Features (6+ files):**
- Estimated time: Half day per feature
- Steps: Document current behavior → Incremental migration → E2E testing → Team review

---

## Common Pitfalls

### DO: Use CSS Variables

```tsx
// ✅ GOOD - Uses CSS variables
<div style={{
  color: 'var(--webtui-primary)',
  padding: 'var(--webtui-spacing-md)'
}}>
  Content
</div>

// ❌ BAD - Hardcoded values
<div style={{ color: '#ff9500', padding: '16px' }}>
  Content
</div>
```

### DO: Use WebTUI Classes First

```tsx
// ✅ GOOD - Leverages WebTUI panel
<div className="synapse-panel">
  <div className="synapse-panel__header">Title</div>
  <div className="synapse-panel__content">Content</div>
</div>

// ❌ BAD - Reinventing WebTUI
<div className="custom-box" style={{ border: '1px solid #ff9500' }}>
  <h3>Title</h3>
  <div>Content</div>
</div>
```

### DO: Use Monospace Fonts for ASCII

```tsx
// ✅ GOOD - Monospace preserves alignment
<pre style={{ fontFamily: 'var(--webtui-font-family)' }}>
  ██████░░░░ 60%
  ████████░░ 80%
</pre>

// ❌ BAD - Sans-serif breaks alignment
<div style={{ fontFamily: 'Arial, sans-serif' }}>
  ██████░░░░ 60%
  ████████░░ 80%
</div>
```

### DO: Use BEM Naming

```tsx
// ✅ GOOD - BEM naming
<div className="synapse-metric">
  <span className="synapse-metric__label">Label</span>
  <span className="synapse-metric__value">Value</span>
</div>

// ❌ BAD - Unclear naming
<div className="metric">
  <span className="lbl">Label</span>
  <span className="val">Value</span>
</div>
```

### DON'T: Overuse Glow Effects

```css
/* ✅ GOOD - Glow on headers only */
.synapse-panel__header {
  text-shadow: var(--phosphor-glow);
}

/* ❌ BAD - Glow on everything */
.synapse-panel {
  box-shadow: var(--phosphor-glow);
}

.synapse-panel__content {
  text-shadow: var(--phosphor-glow);
}

.synapse-metric {
  box-shadow: var(--phosphor-glow);
}
```

### DON'T: Use Inline Styles for Static Values

```tsx
// ✅ GOOD - CSS class for reusable styles
<div className="synapse-metric">
  <span className="synapse-metric__label">CPU</span>
</div>

// ❌ BAD - Inline styles duplicated across components
<div>
  <span style={{ fontSize: '12px', color: '#999' }}>CPU</span>
</div>
```

### DON'T: Hardcode Breakpoints

```css
/* ✅ GOOD - Use CSS variables */
@media (max-width: var(--webtui-breakpoint-sm)) {
  .synapse-grid--3col {
    grid-template-columns: 1fr;
  }
}

/* ❌ BAD - Magic numbers */
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
```

### DON'T: Skip Accessibility

```tsx
// ✅ GOOD - Accessible status indicator
<span
  className="synapse-status synapse-status--active"
  role="status"
  aria-label="Model status: active"
>
  ACTIVE
</span>

// ❌ BAD - No accessibility attributes
<span className="synapse-status synapse-status--active">
  ACTIVE
</span>
```

---

## Code Review Checklist

Use this checklist during code reviews to ensure styling standards compliance.

---

### Pre-Commit Checks

Run these automated checks before committing:

```bash
# Check for hardcoded colors
grep -rn "#[0-9a-fA-F]\{6\}" frontend/src/ --include="*.tsx" --include="*.ts" --include="*.css"

# Check for hardcoded pixel spacing
grep -rn "padding:.*[0-9]\+px" frontend/src/ --include="*.css"
grep -rn "margin:.*[0-9]\+px" frontend/src/ --include="*.css"

# Check for sans-serif fonts
grep -rn "font-family:.*sans" frontend/src/ --include="*.css"

# Check for missing ARIA labels on status elements
grep -rn "synapse-status" frontend/src/ --include="*.tsx" | grep -v "aria-label"
```

**Expected Results:**
- ❌ Zero hardcoded color values
- ❌ Zero hardcoded pixel spacing (except for dynamic values)
- ❌ Zero sans-serif font declarations
- ⚠️ Minimal missing ARIA labels (review each case)

---

### File-Specific Checks

#### main.css

**Location:** [`frontend/src/styles/main.css`](../frontend/src/styles/main.css)

- [ ] CSS layers declared: `@layer base, utils, components`
- [ ] WebTUI imported first: `@import '@webtui/css'`
- [ ] Theme imported second: `@import './theme.css'`
- [ ] Components imported third: `@import './components.css'`
- [ ] No custom styles in main.css (only imports and layer declarations)

**Verification:**
```bash
head -n 20 frontend/src/styles/main.css
```

---

#### theme.css

**Location:** [`frontend/src/styles/theme.css`](../frontend/src/styles/theme.css)

- [ ] `--webtui-primary: #ff9500` (phosphor orange)
- [ ] `--webtui-background: #000000` (pure black)
- [ ] `--phosphor-glow` effects defined
- [ ] `--synapse-success`, `--synapse-warning`, `--synapse-error` defined
- [ ] All colors use CSS variables (no hardcoded hex)
- [ ] All spacing uses WebTUI variables
- [ ] Animations defined with `@keyframes`

**Verification:**
```bash
grep "^--webtui-primary:" frontend/src/styles/theme.css
grep "^--phosphor-glow:" frontend/src/styles/theme.css
```

---

#### components.css

**Location:** [`frontend/src/styles/components.css`](../frontend/src/styles/components.css)

- [ ] All classes prefixed with `synapse-`
- [ ] BEM naming used correctly (block__element--modifier)
- [ ] No duplicate WebTUI functionality
- [ ] All colors use CSS variables from theme.css
- [ ] All spacing uses WebTUI spacing variables
- [ ] Monospace fonts for ASCII content

**Verification:**
```bash
# Check for non-synapse prefixed classes
grep "^\." frontend/src/styles/components.css | grep -v "^\.synapse-"

# Check for hardcoded colors
grep "#[0-9a-fA-F]\{6\}" frontend/src/styles/components.css
```

---

#### Component Files (.tsx)

**General Requirements:**
- [ ] Uses `synapse-*` classes for custom components
- [ ] No inline styles (except for dynamic values like `width: ${percent}%`)
- [ ] Responsive classes used (`synapse-grid--*`)
- [ ] Status indicators use correct modifiers (`synapse-status--active`)
- [ ] ASCII containers use `.synapse-chart` or `.synapse-sparkline`
- [ ] TypeScript interfaces defined for all props
- [ ] ARIA attributes on interactive/status elements

**Verification:**
```bash
# Find inline styles (review each for validity)
grep "style={{" frontend/src/components/SomeComponent.tsx

# Check for missing TypeScript types
grep -n "React.FC<{" frontend/src/components/ -r

# Check ARIA attributes on status elements
grep "synapse-status" frontend/src/components/ -r | grep -v "aria-"
```

---

### Performance Checks

- [ ] Glow effects used sparingly (headers, key elements only)
- [ ] Animations use `will-change` property for GPU acceleration
- [ ] No unnecessary re-renders from style changes
- [ ] ASCII content uses `white-space: pre` and monospace fonts
- [ ] Large lists use virtualization (react-window)
- [ ] Images optimized (lazy loading, proper sizing)

**Performance Testing:**
```bash
# Run Lighthouse audit
npm run lighthouse

# Check bundle size
npm run build
ls -lh dist/assets/*.js
```

**Expected Results:**
- Performance score: >90
- Bundle size: <500KB (gzipped)

---

### Accessibility Checks

- [ ] Sufficient contrast ratios (phosphor orange on black: 5.38:1 ✅)
- [ ] Status indicators have text labels or ARIA attributes
- [ ] Animations respect `prefers-reduced-motion`
- [ ] Keyboard navigation supported (tab order correct)
- [ ] Focus indicators visible (outline, box-shadow)
- [ ] Screen reader announcements for live updates (`aria-live`)

**Accessibility Testing:**
```bash
# Run accessibility audit
npm run test:a11y

# Check for ARIA attributes
grep -r "aria-" frontend/src/components/ | wc -l
```

**Manual Testing:**
- [ ] Tab through UI with keyboard only
- [ ] Test with screen reader (NVDA, JAWS, VoiceOver)
- [ ] Enable `prefers-reduced-motion` and verify animations stop
- [ ] Check color contrast with DevTools

---

### Responsive Design Checks

- [ ] Layout tested at mobile (375px, 414px)
- [ ] Layout tested at tablet (768px, 1024px)
- [ ] Layout tested at desktop (1280px, 1440px)
- [ ] Layout tested at wide (1920px, 2560px)
- [ ] Grids collapse correctly on mobile
- [ ] Text remains readable (no overflow)
- [ ] Touch targets >44px on mobile

**Responsive Testing:**
```bash
# Open in browser with DevTools
npm run dev
# Test at each breakpoint using DevTools responsive mode
```

---

### Browser Compatibility Checks

- [ ] Works in Chrome (latest)
- [ ] Works in Firefox (latest)
- [ ] Works in Safari (latest)
- [ ] Works in Edge (latest)
- [ ] CSS variables supported (all modern browsers)
- [ ] Grid layout supported (all modern browsers)

**Note:** Synapse Engine targets modern browsers only (no IE11 support).

---

### Code Quality Checks

- [ ] TypeScript strict mode enabled
- [ ] No TypeScript errors (`npm run type-check`)
- [ ] Linting passes (`npm run lint`)
- [ ] Tests pass (`npm run test`)
- [ ] Build succeeds (`npm run build`)

**Automated Checks:**
```bash
npm run type-check && npm run lint && npm run test && npm run build
```

---

### Documentation Checks

- [ ] New components documented in code comments
- [ ] Complex CSS explained with inline comments
- [ ] Props interfaces documented with JSDoc
- [ ] Usage examples provided for reusable components
- [ ] Breaking changes noted in commit message

**Example:**
```tsx
/**
 * ModelStatusPanel displays real-time status of all model instances.
 *
 * @param models - Array of model status objects
 * @returns Rendered panel with grid of model status cards
 *
 * @example
 * <ModelStatusPanel models={[
 *   { id: '1', name: 'Q2_FAST', status: 'active', ... }
 * ]} />
 */
const ModelStatusPanel: React.FC<{ models: Model[] }> = ({ models }) => {
  // ...
};
```

---

### Review Summary Template

Use this template when approving/requesting changes:

```markdown
## Style Guide Compliance Review

**Component:** [Component name]
**Reviewer:** [Your name]
**Date:** [Date]

### Checklist Results
- [x] WebTUI classes used appropriately
- [x] CSS variables for all colors/spacing
- [x] BEM naming convention followed
- [x] Responsive design verified
- [ ] Accessibility attributes complete (NEEDS WORK)
- [x] Performance optimizations applied
- [x] TypeScript types defined

### Issues Found
1. Missing `aria-label` on status indicators (lines 42, 58)
2. Hardcoded padding value on line 103 (use `var(--webtui-spacing-md)`)

### Recommendations
- Consider using `synapse-grid--3col` instead of custom flexbox (line 67)
- Add `will-change` to animated elements for better performance (line 89)

### Approval
- [ ] Approved (no changes needed)
- [x] Approved with minor changes
- [ ] Changes requested
```

---

## Related Documentation

### Core Documentation
- [WebTUI Integration Guide](./WEBTUI_INTEGRATION_GUIDE.md) - Implementation details and setup
- [Dense Terminal Mockups](./DENSE_TERMINAL_MOCKUPS.md) - Visual design reference
- [ASCII Libraries Research](./ASCII_LIBRARIES_RESEARCH.md) - Chart/visualization options
- [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) - System architecture and team structure
- [CLAUDE.md](../CLAUDE.md) - Development workflow and standards

### Component Documentation
- [Frontend Components](../frontend/src/components/README.md) - Component library reference
- [Styling Architecture](../frontend/src/styles/README.md) - CSS organization

### Testing Documentation
- [Testing Guide](./TESTING_GUIDE.md) - Testing standards and practices
- [Accessibility Testing](./ACCESSIBILITY_TESTING.md) - A11y test procedures

### External Resources
- [WebTUI CSS Documentation](https://github.com/Ztkent/webtui-css) - Official WebTUI docs
- [BEM Methodology](https://getbem.com/) - CSS naming convention
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/) - Accessibility standards

---

## Changelog

### Version 1.0 (2025-11-08)
- Initial style guide creation
- CSS architecture diagram added
- Real-world examples from actual project files
- Migration guide for existing components
- Enhanced code review checklist with file-specific checks
- Pre-commit automation patterns
- Performance and accessibility standards
- Browser compatibility requirements

---

## Contributing

When updating this guide:

1. **Add examples from real code** - Link to actual project files with line numbers
2. **Include searchable patterns** - Provide regex for code review automation
3. **Update version number** - Increment version and add changelog entry
4. **Link related docs** - Add hyperlinks using relative paths
5. **Test code examples** - Ensure all examples are copy-paste ready
6. **Get team review** - Share updates with frontend team before merging

---

**This guide is authoritative. All Synapse Engine developers must follow these standards.**
