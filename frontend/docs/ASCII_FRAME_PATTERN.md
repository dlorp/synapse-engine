# ASCII Frame Pattern - S.Y.N.A.P.S.E. ENGINE Terminal UI Framework

**Version:** 1.0
**Last Updated:** 2025-11-09
**Status:** Production Standard

---

## Table of Contents

1. [Overview](#overview)
2. [Design Philosophy](#design-philosophy)
3. [Implementation Guide](#implementation-guide)
4. [Code Examples](#code-examples)
5. [CSS Requirements](#css-requirements)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)
8. [Visual Examples](#visual-examples)

---

## Overview

The ASCII Frame Pattern is the foundational visual framework for S.Y.N.A.P.S.E. ENGINE's terminal-inspired UI. It provides a consistent, high-density information display system with real-time updates, phosphor glow effects, and NERV-inspired aesthetics.

### What is the ASCII Frame Pattern?

An ASCII frame is a text-based visualization component that uses:
- **Box-drawing characters** for borders (─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼)
- **Fixed-width content** (70 characters) for alignment consistency
- **Extended borders** (150 characters) that overflow for responsiveness
- **Phosphor glow effects** for terminal authenticity
- **Real-time data updates** with smooth 60fps animations

### Why Use This Pattern?

1. **Visual Consistency** - All data displays share the same aesthetic language
2. **Information Density** - Pack maximum data without overwhelming users
3. **Performance** - Pure CSS animations run at 60fps on GPU
4. **Accessibility** - Proper contrast ratios, semantic HTML, screen reader support
5. **Responsiveness** - Overflow pattern adapts to narrow and wide screens
6. **Brand Identity** - Distinctive terminal aesthetic aligned with project vision

---

## Design Philosophy

### Terminal-First Approach

The UI embraces **dense information displays** with **terminal aesthetics** inspired by engineering interfaces and Evangelion's NERV panels. This is NOT about nostalgia - it's about **functional density** and **immediate visual feedback**.

### Core Principles

1. **Dense Information Displays** - Every pixel serves a purpose
2. **High Contrast** - Bright text on dark backgrounds (#ff9500 on #000000)
3. **Real-time Feedback** - Live updating data at 60fps
4. **Modular Panels** - Boxed sections with borders and labels
5. **Technical Readout Style** - Numerical data, status codes, system diagrams
6. **Color-coded States** - Immediate visual understanding
7. **Functional Animations** - Purposeful state transitions (glow, breathe, pulse)

### Color Palette

```css
--webtui-primary: #ff9500;       /* Phosphor orange (brand color) */
--webtui-accent: #00ffff;        /* Cyan accents */
--webtui-warning: #ff9500;       /* Amber warnings */
--webtui-error: #ff0000;         /* Red errors */
--webtui-success: #00ff00;       /* Green success states */
--webtui-text: #ff9500;          /* Primary text */
--webtui-text-muted: #997a5c;    /* Secondary text */
--webtui-background: #000000;    /* Pure black */
```

**Note:** The primary brand color is phosphor orange (#ff9500), NOT phosphor green.

---

## Implementation Guide

### Step 1: Set Up Component Structure

Every ASCII visualization follows this structure:

```tsx
// MyComponent.tsx
import React from 'react';
import styles from './MyComponent.module.css';

export const MyComponent: React.FC = () => {
  return (
    <div className={styles.asciiPanel}>
      <pre className={styles.asciiFrame}>
        {/* ASCII content goes here */}
      </pre>

      {/* Optional: Additional UI elements */}
      <div className={styles.panelBody}>
        {/* Buttons, forms, etc. */}
      </div>
    </div>
  );
};
```

### Step 2: Create the padLine Utility

The `padLine` utility ensures consistent content width:

```typescript
// Utility function (define globally or in component)
const padLine = (content: string, width: number): string => {
  if (content.length > width) {
    return content.substring(0, width);
  }
  return content.padEnd(width, ' ');
};
```

**Purpose:** Pads content to exact character width or truncates if too long.

### Step 3: Generate ASCII Frame Content

```tsx
<pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;  // Content width
  const header = '─ PANEL TITLE ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('Content line 1', FRAME_WIDTH)}
${padLine('Content line 2', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
</pre>
```

**Key Points:**
- Header: Text + 150 dashes (extends beyond container for overflow effect)
- Content: 70 characters wide, padded with `padLine()`
- Footer: 150 dashes (matches header)
- No corner characters (┌ ┐ └ ┘) - use overflow pattern for responsiveness

### Step 4: Add CSS Styles

```css
/* Component.module.css */
.asciiPanel {
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--webtui-primary);
  animation: panel-breathe 2s ease-in-out infinite;
  max-width: 1200px;
  margin: 0 auto var(--webtui-spacing-lg);
}

.asciiFrame {
  font-family: var(--webtui-font-family);
  font-size: 12px;
  line-height: 1.2;
  letter-spacing: 0;
  color: var(--webtui-primary);
  white-space: pre;
  overflow: hidden;
  text-shadow: 0 0 8px rgba(255, 149, 0, 0.6);
  animation: frame-glow 2s ease-in-out infinite;
  font-kerning: none;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: geometricPrecision;
  font-feature-settings: "liga" 0, "calt" 0;
}

@keyframes panel-breathe {
  0%, 100% {
    border-color: var(--webtui-primary);
    box-shadow: 0 0 0 rgba(255, 149, 0, 0);
  }
  50% {
    border-color: rgba(255, 149, 0, 0.8);
    box-shadow: 0 0 15px rgba(255, 149, 0, 0.2);
  }
}

@keyframes frame-glow {
  0%, 100% {
    text-shadow: 0 0 8px rgba(255, 149, 0, 0.6),
                 0 0 12px rgba(255, 149, 0, 0.3);
  }
  50% {
    text-shadow: 0 0 12px rgba(255, 149, 0, 0.8),
                 0 0 16px rgba(255, 149, 0, 0.4),
                 0 0 20px rgba(255, 149, 0, 0.2);
  }
}
```

---

## Code Examples

### Example 1: Basic Frame with Header/Footer

```tsx
const BasicFrame: React.FC = () => {
  const padLine = (content: string, width: number): string => {
    if (content.length > width) {
      return content.substring(0, width);
    }
    return content.padEnd(width, ' ');
  };

  return (
    <div className={styles.asciiPanel}>
      <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = '─ SYSTEM STATUS ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('STATUS: OPERATIONAL', FRAME_WIDTH)}
${padLine('UPTIME: 72h 14m 32s', FRAME_WIDTH)}
${padLine('MODELS: 5 active', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
      </pre>
    </div>
  );
};
```

**Output:**
```
─ SYSTEM STATUS ──────────────────────────────────────────────────────────

STATUS: OPERATIONAL
UPTIME: 72h 14m 32s
MODELS: 5 active

──────────────────────────────────────────────────────────────────────────
```

### Example 2: Frame with Dynamic Content

```tsx
interface MetricData {
  label: string;
  value: number;
  unit: string;
}

const MetricsFrame: React.FC<{ metrics: MetricData[] }> = ({ metrics }) => {
  const padLine = (content: string, width: number): string => {
    if (content.length > width) {
      return content.substring(0, width);
    }
    return content.padEnd(width, ' ');
  };

  return (
    <div className={styles.asciiPanel}>
      <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = '─ SYSTEM METRICS ';

  const contentLines = metrics.map(metric => {
    const line = `${metric.label.padEnd(15)} ${metric.value.toFixed(1).padStart(6)} ${metric.unit}`;
    return padLine(line, FRAME_WIDTH);
  });

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${contentLines.join('\n')}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
      </pre>
    </div>
  );
};
```

**Usage:**
```tsx
<MetricsFrame
  metrics={[
    { label: 'CPU Usage', value: 45.2, unit: '%' },
    { label: 'Memory', value: 8.5, unit: 'GB' },
    { label: 'Disk I/O', value: 128.3, unit: 'MB/s' }
  ]}
/>
```

### Example 3: Frame with ASCII Chart

```tsx
const generateBarChart = (value: number, maxValue: number = 100, width: number = 20): string => {
  const filled = Math.floor((value / maxValue) * width);
  const empty = width - filled;
  return '█'.repeat(filled) + '░'.repeat(empty);
};

const ChartFrame: React.FC<{ data: { label: string; value: number }[] }> = ({ data }) => {
  const padLine = (content: string, width: number): string => {
    if (content.length > width) {
      return content.substring(0, width);
    }
    return content.padEnd(width, ' ');
  };

  return (
    <div className={styles.asciiPanel}>
      <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = '─ PERFORMANCE METRICS ';

  const chartLines = data.map(item => {
    const bar = generateBarChart(item.value, 100, 20);
    const line = `${item.label.padEnd(15)} [${bar}] ${item.value.toFixed(0).padStart(3)}%`;
    return padLine(line, FRAME_WIDTH);
  });

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${chartLines.join('\n')}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
      </pre>
    </div>
  );
};
```

**Output:**
```
─ PERFORMANCE METRICS ────────────────────────────────────────────────────

CPU Usage       [████████████░░░░░░░░] 60%
Memory          [██████████████░░░░░░] 70%
Network         [█████████░░░░░░░░░░░] 45%

──────────────────────────────────────────────────────────────────────────
```

### Example 4: Responsive Frame with Real-time Updates

```tsx
const LiveMetricsFrame: React.FC = () => {
  const [metrics, setMetrics] = useState({
    cpu: 0,
    memory: 0,
    requests: 0
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics({
        cpu: Math.random() * 100,
        memory: Math.random() * 100,
        requests: Math.floor(Math.random() * 150)
      });
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  const padLine = (content: string, width: number): string => {
    if (content.length > width) {
      return content.substring(0, width);
    }
    return content.padEnd(width, ' ');
  };

  return (
    <div className={styles.asciiPanel}>
      <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = '─ LIVE METRICS (2s refresh) ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine(`CPU:      ${metrics.cpu.toFixed(1).padStart(5)}%`, FRAME_WIDTH)}
${padLine(`Memory:   ${metrics.memory.toFixed(1).padStart(5)}%`, FRAME_WIDTH)}
${padLine(`Requests: ${metrics.requests.toString().padStart(5)}/s`, FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
      </pre>
    </div>
  );
};
```

---

## CSS Requirements

### Required Variables (components.css)

Ensure these CSS variables are defined in your global stylesheet:

```css
:root {
  --webtui-primary: #ff9500;
  --webtui-accent: #00ffff;
  --webtui-warning: #ff9500;
  --webtui-error: #ff0000;
  --webtui-success: #00ff00;
  --webtui-text: #ff9500;
  --webtui-text-muted: #997a5c;
  --webtui-background: #000000;
  --webtui-font-family: 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', monospace;
  --webtui-font-size-base: 14px;
  --webtui-font-size-small: 12px;
  --webtui-spacing-xs: 4px;
  --webtui-spacing-sm: 8px;
  --webtui-spacing-md: 16px;
  --webtui-spacing-lg: 24px;
  --webtui-spacing-xl: 32px;
}
```

### Required Component Styles

Every component using ASCII frames needs these classes in its module.css:

```css
/* Panel container - centers on wide screens, constrains max width */
.asciiPanel {
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--webtui-primary);
  animation: panel-breathe 2s ease-in-out infinite;
  max-width: 1200px;
  margin: 0 auto var(--webtui-spacing-lg);
}

/* ASCII frame content */
.asciiFrame {
  font-family: var(--webtui-font-family);
  font-size: 12px;
  line-height: 1.2;
  letter-spacing: 0;
  color: var(--webtui-primary);
  white-space: pre;
  overflow: hidden;
  text-overflow: clip;
  width: 100%;
  text-shadow: 0 0 8px rgba(255, 149, 0, 0.6);
  animation: frame-glow 2s ease-in-out infinite;
  margin: var(--webtui-spacing-md) 0;
  font-kerning: none;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: geometricPrecision;
  font-feature-settings: "liga" 0, "calt" 0;
  padding: 0;
  background: transparent;
  box-sizing: border-box;
}

/* Panel breathing animation */
@keyframes panel-breathe {
  0%, 100% {
    border-color: var(--webtui-primary);
    box-shadow: 0 0 0 rgba(255, 149, 0, 0);
  }
  50% {
    border-color: rgba(255, 149, 0, 0.8);
    box-shadow: 0 0 15px rgba(255, 149, 0, 0.2);
  }
}

/* Frame glow animation */
@keyframes frame-glow {
  0%, 100% {
    text-shadow: 0 0 8px rgba(255, 149, 0, 0.6),
                 0 0 12px rgba(255, 149, 0, 0.3);
  }
  50% {
    text-shadow: 0 0 12px rgba(255, 149, 0, 0.8),
                 0 0 16px rgba(255, 149, 0, 0.4),
                 0 0 20px rgba(255, 149, 0, 0.2);
  }
}

/* Optional: Panel body for additional UI elements */
.panelBody {
  padding: var(--webtui-spacing-md);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .asciiFrame {
    font-size: 10px;
  }

  .asciiPanel {
    margin: 0 0 var(--webtui-spacing-md);
  }
}
```

---

## Common Patterns

### System Topology Diagram

```typescript
const TopologyDiagram: React.FC<{ servers: number }> = ({ servers }) => {
  const padLine = (content: string, width: number): string => {
    if (content.length > width) {
      return content.substring(0, width);
    }
    return content.padEnd(width, ' ');
  };

  return (
    <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = '─ SYSTEM TOPOLOGY ';

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine('[FASTAPI]──[ORCHESTRATOR]──[NEURAL SUBSTRATE]', FRAME_WIDTH)}
${padLine('    │             │                 │', FRAME_WIDTH)}
${padLine(`    │             ├──[Q2]─────────┼─── ${servers} ACTIVE`, FRAME_WIDTH)}
${padLine('    │             ├──[Q3]─────────┤', FRAME_WIDTH)}
${padLine('    │             └──[Q4]─────────┘', FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
    </pre>
  );
};
```

### Status Grid

```typescript
const StatusGrid: React.FC<{ statuses: { label: string; value: string; state: string }[] }> = ({ statuses }) => {
  const padLine = (content: string, width: number): string => {
    if (content.length > width) {
      return content.substring(0, width);
    }
    return content.padEnd(width, ' ');
  };

  return (
    <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = '─ COMPONENT STATUS ';

  const statusLines = statuses.map(s => {
    const icon = s.state === 'healthy' ? '✓' : s.state === 'warning' ? '⚠' : '✗';
    const line = `${icon} ${s.label.padEnd(20)} ${s.value.padStart(15)}`;
    return padLine(line, FRAME_WIDTH);
  });

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${statusLines.join('\n')}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
    </pre>
  );
};
```

### Progress Indicator

```typescript
const ProgressBar: React.FC<{ progress: number; label: string }> = ({ progress, label }) => {
  const padLine = (content: string, width: number): string => {
    if (content.length > width) {
      return content.substring(0, width);
    }
    return content.padEnd(width, ' ');
  };

  return (
    <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = `─ ${label.toUpperCase()} `;
  const barWidth = 40;
  const filled = Math.floor((progress / 100) * barWidth);
  const empty = barWidth - filled;
  const bar = '█'.repeat(filled) + '░'.repeat(empty);

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${padLine(`[${bar}] ${progress.toFixed(0)}%`, FRAME_WIDTH)}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
    </pre>
  );
};
```

### Sparkline Metrics

```typescript
const generateSparkline = (values: number[]): string => {
  const chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;

  return values.map(v => {
    const normalized = (v - min) / range;
    const index = Math.min(Math.floor(normalized * chars.length), chars.length - 1);
    return chars[index];
  }).join('');
};

const SparklinePanel: React.FC<{ data: { label: string; values: number[] }[] }> = ({ data }) => {
  const padLine = (content: string, width: number): string => {
    if (content.length > width) {
      return content.substring(0, width);
    }
    return content.padEnd(width, ' ');
  };

  return (
    <pre className={styles.asciiFrame}>
{(() => {
  const FRAME_WIDTH = 70;
  const header = '─ TREND ANALYSIS ';

  const sparklineLines = data.map(item => {
    const sparkline = generateSparkline(item.values);
    const currentVal = item.values[item.values.length - 1].toFixed(0).padStart(3);
    const line = `${item.label.padEnd(10)} [${sparkline}] ${currentVal}`;
    return padLine(line, FRAME_WIDTH);
  });

  return `${header}${'─'.repeat(150)}
${padLine('', FRAME_WIDTH)}
${sparklineLines.join('\n')}
${padLine('', FRAME_WIDTH)}
${'─'.repeat(150)}`;
})()}
    </pre>
  );
};
```

---

## Troubleshooting

### Issue: Misaligned Characters

**Problem:** Box-drawing characters don't align properly, frames look jagged.

**Solution:**
1. Verify monospace font is applied: `font-family: var(--webtui-font-family);`
2. Disable ligatures: `font-feature-settings: "liga" 0, "calt" 0;`
3. Disable kerning: `font-kerning: none;`
4. Set precise rendering: `text-rendering: geometricPrecision;`

### Issue: Excessive Negative Space on Wide Screens

**Problem:** ASCII content is narrow but borders extend to full browser width.

**Solution:**
Add centering constraints to `.asciiPanel`:
```css
.asciiPanel {
  max-width: 1200px;
  margin: 0 auto var(--webtui-spacing-lg);
}
```

### Issue: Content Overflows Frame Width

**Problem:** Dynamic content exceeds 70 character width, breaking alignment.

**Solution:**
Always use `padLine()` utility and check content length:
```typescript
const safeLine = (content: string): string => {
  return padLine(content, FRAME_WIDTH);
};
```

### Issue: Animations Cause Jank

**Problem:** Frame glow or panel breathe animations drop below 60fps.

**Solution:**
1. Use GPU-accelerated properties only (transform, opacity)
2. Add `will-change: auto;` (not `will-change: transform;` - can cause memory issues)
3. Use `contain: layout style paint;` for containment
4. Avoid animating box-shadow on many elements simultaneously

### Issue: Text Shadow Not Visible

**Problem:** Phosphor glow effect not appearing.

**Solution:**
1. Check CSS variable is defined: `--webtui-primary: #ff9500;`
2. Verify animation is running: `animation: frame-glow 2s ease-in-out infinite;`
3. Check contrast against background (should be #000000)

### Issue: Responsive Breakpoints Not Working

**Problem:** Mobile layout doesn't adapt properly.

**Solution:**
Add media queries to component module.css:
```css
@media (max-width: 768px) {
  .asciiFrame {
    font-size: 10px;
  }

  .asciiPanel {
    margin: 0 0 var(--webtui-spacing-md);
  }
}
```

### Issue: Unicode Characters Render Incorrectly

**Problem:** Box-drawing or block characters show as boxes/question marks.

**Solution:**
1. Verify UTF-8 encoding in HTML: `<meta charset="UTF-8">`
2. Check font supports Unicode block: JetBrains Mono, IBM Plex Mono
3. Use consistent Unicode code points (e.g., U+2500-U+257F for box drawing)

---

## Visual Examples

### Before/After: Centering Fix

**Before (Excessive Negative Space):**
```
Browser Width: 2560px
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│  ─ PANEL TITLE ──────────────                                                       │
│  Content (70 chars)                                                                  │
│  ──────────────────────────────                                                      │
│                                                      [MASSIVE EMPTY SPACE]           │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**After (Centered, max-width: 1200px):**
```
Browser Width: 2560px
              ┌──────────────────────────────────────────────┐
              │                                              │
              │  ─ PANEL TITLE ────────────────────────────  │
              │  Content (70 chars)                          │
              │  ────────────────────────────────────────     │
              │                                              │
              └──────────────────────────────────────────────┘
```

### Complete ASCII Frame Example

```
─ SYSTEM HEALTH ──────────────────────────────────────────────────────────

TOPOLOGY:
[FASTAPI]──[ORCHESTRATOR]──[NEURAL SUBSTRATE]
    │             │                 │
    │             ├──[Q2]─────────┼─── 3/3 ACTIVE
    │             ├──[Q3]─────────┤
    │             └──[Q4]─────────┘
    │
    └───[REGISTRY: 5 models]

STATUS: HEALTHY    │ Profiles: 2 │ Ready: 3
──────────────────────────────────────────────────────────────────────────
```

### ASCII Bar Chart Example

```
─ SYSTEM METRICS (LIVE) ──────────────────────────────────────────────────

CPU:    [████████████░░░░░░░░] 45%
Memory: [██████████████░░░░░░] 70%
Disk:   [█████████░░░░░░░░░░░] 32%
Net:    [███████████████░░░░░] 58%

──────────────────────────────────────────────────────────────────────────
```

### ASCII Sparkline Example

```
─ TREND ANALYSIS (20 samples) ────────────────────────────────────────────

CPU:    [▁▂▃▃▄▅▆▇█▇▆▅▄▃▃▂▁▁▂▃] 45%
Memory: [▃▃▃▄▄▄▅▅▅▆▆▆▇▇▇████▇▇] 82%
Disk:   [▂▂▁▁▂▃▄▅▅▄▃▂▂▁▁▁▂▃▄▅] 28%

──────────────────────────────────────────────────────────────────────────
```

### Server Rack Status Example

```
─ SERVER RACK STATUS ─────────────────────────────────────────────────────

┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  Q2 FAST       │  │  Q3 BALANCED   │  │  Q4 POWERFUL   │
│  ┌──────────┐  │  │  ┌──────────┐  │  │  ┌──────────┐  │
│  │ █████████ │  │  │  │ █████████ │  │  │  │ █████████ │  │
│  └──────────┘  │  │  └──────────┘  │  │  └──────────┘  │
│  :8080-8082    │  │  :8090-8091    │  │  :8100         │
│  [3 active]    │  │  [2 active]    │  │  [1 active]    │
└────────────────┘  └────────────────┘  └────────────────┘

CONTROL PANEL: ◉ READY
──────────────────────────────────────────────────────────────────────────
```

---

## Performance Guidelines

### Animation Performance

1. **Use CSS animations only** - Avoid JavaScript-driven animations for visual effects
2. **Limit simultaneous animations** - Max 3-4 animated panels visible at once
3. **Use transform/opacity** - GPU-accelerated properties for 60fps
4. **Avoid animating layout** - No width/height/margin animations

### Real-time Updates

1. **Debounce frequent updates** - Max 10 updates/second for smooth rendering
2. **Use React.memo** - Prevent unnecessary re-renders
3. **Batch state updates** - Update multiple metrics in single setState call
4. **Virtualize long lists** - For >50 items, use react-window

### Memory Management

1. **Clean up intervals** - Always return cleanup function from useEffect
2. **Limit history length** - Keep max 60-100 data points for sparklines
3. **Avoid memory leaks** - Clear timers, close WebSocket connections
4. **Monitor component count** - Too many ASCII frames (>20) can impact performance

---

## Accessibility Requirements

### Screen Reader Support

```tsx
<div className={styles.asciiPanel} role="region" aria-label="System Health Status">
  <pre className={styles.asciiFrame} aria-live="polite">
    {/* ASCII content */}
  </pre>
</div>
```

### Keyboard Navigation

- All interactive elements must be keyboard accessible (tab, enter, space)
- Focus indicators must be visible with terminal aesthetic
- Use `aria-label` for icon-only buttons

### Color Contrast

- Phosphor orange (#ff9500) on black (#000000) = 9.98:1 (AAA compliant)
- Cyan accent (#00ffff) on black = 9.47:1 (AAA compliant)
- Always test with browser DevTools accessibility panel

---

## Related Documentation

- [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md) - Overall project structure
- [CLAUDE.md](../../CLAUDE.md) - Development guidelines
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Recent implementation history
- [components.css](../src/styles/components.css) - Global terminal UI variables

---

## Changelog

### 2025-11-09 - v1.0
- Initial documentation
- Defined standard frame pattern (70 char content, 150 char borders)
- Added centering solution for wide screens (max-width: 1200px)
- Documented CSS requirements and common patterns
- Added troubleshooting guide and visual examples

---

**Maintained by:** S.Y.N.A.P.S.E. ENGINE Engineering Team
**Contact:** See [CLAUDE.md](../../CLAUDE.md) for agent responsibilities
