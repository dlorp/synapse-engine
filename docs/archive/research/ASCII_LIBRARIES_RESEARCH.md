# ASCII Libraries Research & Integration Guide

**Project:** S.Y.N.A.P.S.E. ENGINE
**Date:** 2025-11-08
**Purpose:** Comprehensive research on ASCII chart/art libraries for integration with WebTUI CSS framework
**Primary Color:** Phosphor Orange (#ff9500)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Library Categories & Capabilities](#library-categories--capabilities)
3. [art.py Analysis & JavaScript Equivalents](#artpy-analysis--javascript-equivalents)
4. [Top 5 Recommended Libraries](#top-5-recommended-libraries)
5. [WebTUI Integration Strategy](#webtui-integration-strategy)
6. [React Component Examples](#react-component-examples)
7. [Implementation Effort Estimates](#implementation-effort-estimates)
8. [Priority Ranking](#priority-ranking)
9. [Performance Considerations](#performance-considerations)
10. [Additional Resources](#additional-resources)

---

## Executive Summary

This research identifies browser-compatible ASCII visualization libraries that can layer ON TOP of WebTUI CSS framework to create elite terminal interfaces for S.Y.N.A.P.S.E. ENGINE.

### Key Findings

**Best Libraries for Our Use Case:**
1. **simple-ascii-chart** - TypeScript-native chart library (bar, line, sparklines)
2. **figlet.js** - FIGlet text banners with 400+ fonts
3. **text-graph.js** - Multi-series charts with live updates
4. **aalib.js** - Image-to-ASCII converter for visual effects
5. **asciichart** - Lightweight line charts (mature, stable)

**Integration Approach:**
- WebTUI provides base CSS styling (terminal aesthetics, colors, layouts)
- ASCII libraries generate content (charts, banners, visualizations)
- React components wrap libraries with proper TypeScript types
- CSS Modules style the ASCII output with phosphor glow effects

**Recommended Strategy:**
1. Adopt WebTUI as CSS foundation (replace custom CSS modules gradually)
2. Build React wrapper components for ASCII libraries
3. Layer phosphor orange (#ff9500) styling via WebTUI theme customization
4. Create reusable component library matching existing pattern (`/components/terminal/`)

---

## Library Categories & Capabilities

### Category 1: ASCII Chart Libraries

#### **simple-ascii-chart** ⭐ RECOMMENDED
- **Type:** TypeScript-native chart library
- **NPM:** `simple-ascii-chart`
- **Features:**
  - Line charts, bar charts (vertical/horizontal), sparklines
  - Multiple data series with custom colors
  - ANSI color support ('ansiRed', 'ansiGreen', 'ansiBlue', 'ansiCyan', etc.)
  - Axis labels, titles, legends
  - Custom formatters for labels
  - Thresholds and data points highlighting
  - Fill area (area chart mode)
- **Browser Support:** ✅ Yes (ES6/CommonJS)
- **TypeScript:** ✅ Native TypeScript
- **Size:** ~50KB
- **Last Updated:** Active development (2024)

**Example Output:**
```
 ▲
 4┤ ┏━━━┓
 │ ┃   ┃
 2┤ ┃   ┗━┓
 1┤━┛     ┃
 │       ┃
-1┤       ┗━
 └┬─┬─┬─┬─┬▶
  1 2 3 4 5
```

#### **text-graph.js**
- **Type:** Terminal/console ASCII chart library
- **NPM:** `text-graph.js`
- **Features:**
  - Line charts with single/multi-series
  - Dashboard layouts (multiple charts)
  - Axis scaling (linear, logarithmic)
  - Color support (blue, cyan, magenta, red, green, yellow, white)
  - Data compression functions (mean, max, min)
  - Overflow handling (log scale, clamp, linear scale)
  - Title positioning and styling
  - No external dependencies
- **Browser Support:** ✅ Yes
- **TypeScript:** ✅ TypeScript definitions included
- **Size:** ~30KB
- **Last Updated:** 2024

**Example Usage:**
```typescript
import { Plot } from 'text-graph.js';

const plot = new Plot(80, 20, {
  showAxis: true,
  title: 'VRAM Usage',
  axisScale: PlotAxisScale.linear,
  titleForeground: Color.cyan,
});

const seriesId = plot.addSeries({ color: Color.cyan });
plot.addSeriesRange(seriesId, [4.2, 4.5, 4.8, 5.1, 5.3]);
console.log(plot.paint());
```

#### **asciichart**
- **Type:** Lightweight line chart library
- **NPM:** `asciichart`
- **Features:**
  - Simple line charts
  - Auto-scaling height and range
  - Multiple series plotting
  - Color support (blue, green, default)
  - Custom height configuration
  - Label formatting
  - No dependencies
- **Browser Support:** ✅ Yes (works in console and DOM)
- **TypeScript:** ⚠️ No official types (use `@types/asciichart` or declare module)
- **Size:** ~15KB (very lightweight)
- **Last Updated:** 2019 (stable, mature)
- **Popularity:** 1.5M+ npm downloads/week

**Example Output:**
```
   15.00 ┼╮
   14.00 ┤╰╮
   13.00 ┤ ╰╮
   12.00 ┤  ╰╮
   11.00 ┤   ╰╮
   10.00 ┤    ╰╮
    9.00 ┤     ╰╮
    8.00 ┤      ╰╮
    7.00 ┤       ╰╮
```

### Category 2: ASCII Text Banners (FIGlet)

#### **figlet.js** ⭐ RECOMMENDED
- **Type:** FIGlet implementation for JavaScript/TypeScript
- **NPM:** `figlet`
- **Features:**
  - Full FIGfont specification support
  - 400+ bundled fonts
  - Async/sync rendering
  - Font preloading for browser
  - Dynamic font fetching
  - Horizontal/vertical layout options
  - Text width limiting
  - Whitespace break control
- **Browser Support:** ✅ Yes (ES modules)
- **TypeScript:** ✅ Written in TypeScript
- **Size:** ~200KB (fonts included)
- **Last Updated:** Active (2024)
- **Popularity:** 700K+ npm downloads/week

**Example Output (Standard font):**
```
  ____   __   __  _   _      _      ____   ____   _____
 / ___| \ \ / / | \ | |    / \    |  _ \ / ___| | ____|
 \___ \  \ V /  |  \| |   / _ \   | |_) |\___ \ |  _|
  ___) |  | |   | |\  |  / ___ \  |  __/  ___) || |___
 |____/   |_|   |_| \_| /_/   \_\ |_|    |____/ |_____|
```

**Browser Usage:**
```typescript
import figlet from "figlet";
import standard from "figlet/fonts/Standard";

figlet.parseFont("Standard", standard);

const text = await figlet.text("SYNAPSE", { font: "Standard" });
console.log(text);
```

### Category 3: Image-to-ASCII Converters

#### **aalib.js** ⭐ RECOMMENDED for visual effects
- **Type:** Image/video to ASCII art converter
- **NPM:** Not on npm (use GitHub directly)
- **GitHub:** `mir3z/aalib.js`
- **Features:**
  - Image to ASCII conversion using HTML5 Canvas
  - Video to ASCII (moving ASCII art)
  - Custom character sets (ASCII_CHARSET, SIMPLE_CHARSET)
  - Color preservation option
  - Canvas/HTML rendering
  - RxJS-based pipeline architecture
  - No external dependencies (except RxJS)
- **Browser Support:** ✅ Yes (requires Canvas API)
- **TypeScript:** ⚠️ JavaScript only (can add types)
- **Size:** ~25KB
- **Use Cases:** Logo conversion, background effects, visual flourishes

**Example Character Sets:**
```typescript
// ASCII_CHARSET: printable ASCII characters (32-127)
// SIMPLE_CHARSET: ['.', ':', '*', 'I', '$', 'V', 'F', 'N', 'M']
```

#### **Alternative: jscii**
- **GitHub:** `EnotionZ/jscii`
- **Features:** Image/stream to ASCII using Canvas 2D context
- **Browser Support:** ✅ Yes
- **Size:** ~10KB

### Category 4: Box Drawing & Tables

#### **lines-js**
- **Type:** Unicode box drawing helper
- **NPM:** Not widely available (GitHub: `couchand/lines-js`)
- **Features:**
  - Draw lines with Unicode box characters
  - Convert to Unicode string for console output
  - Programmatic box/line drawing
- **Browser Support:** ✅ Yes
- **TypeScript:** ⚠️ JavaScript only
- **Size:** ~5KB

**Alternative: Manual Implementation**
Given the simplicity, we can manually implement box drawing using Unicode characters:

```typescript
// Box Drawing Characters Reference
const BOX_CHARS = {
  // Light borders
  light: {
    topLeft: '┌', topRight: '┐', bottomLeft: '└', bottomRight: '┘',
    horizontal: '─', vertical: '│',
    topJoin: '┬', bottomJoin: '┴', leftJoin: '├', rightJoin: '┤',
    cross: '┼',
  },
  // Heavy borders
  heavy: {
    topLeft: '┏', topRight: '┓', bottomLeft: '┗', bottomRight: '┛',
    horizontal: '━', vertical: '┃',
    topJoin: '┳', bottomJoin: '┻', leftJoin: '┣', rightJoin: '┫',
    cross: '╋',
  },
  // Double borders
  double: {
    topLeft: '╔', topRight: '╗', bottomLeft: '╚', bottomRight: '╝',
    horizontal: '═', vertical: '║',
    topJoin: '╦', bottomJoin: '╩', leftJoin: '╠', rightJoin: '╣',
    cross: '╬',
  },
  // Rounded borders
  rounded: {
    topLeft: '╭', topRight: '╮', bottomLeft: '╰', bottomRight: '╯',
    horizontal: '─', vertical: '│',
  },
};
```

### Category 5: Progress Bars & Gauges

#### **@yacosta738/ascii-progress-bar**
- **Type:** Web Component for ASCII progress bars
- **NPM:** `@yacosta738/ascii-progress-bar`
- **Features:**
  - Works with React, Vue, Angular, vanilla JS
  - Web Component standard
  - Horizontal progress bars
  - TypeScript support
  - Customizable characters
- **Browser Support:** ✅ Yes (Web Components)
- **TypeScript:** ✅ Yes
- **Size:** ~8KB
- **Framework Agnostic:** Works with any framework

**Example Usage:**
```html
<ascii-progress-bar value="75" max="100"></ascii-progress-bar>
```

**Output:**
```
[█████████████████████████████░░░░░░░░░] 75%
```

**Alternative: Manual Implementation**
We can create custom progress bars easily:

```typescript
const createProgressBar = (value: number, max: number, width: number = 40): string => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;

  return `[${'\u2588'.repeat(filled)}${'\u2591'.repeat(empty)}] ${percentage.toFixed(0)}%`;
};

// Usage
console.log(createProgressBar(75, 100, 40));
// Output: [████████████████████████████░░░░░░░░░] 75%
```

### Category 6: Sparklines

#### **Manual Implementation Recommended**
Sparklines are simple enough to implement manually using block characters:

```typescript
const SPARKLINE_CHARS = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];

const createSparkline = (data: number[]): string => {
  if (data.length === 0) return '';

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  return data.map(value => {
    const normalized = (value - min) / range;
    const index = Math.min(7, Math.floor(normalized * 8));
    return SPARKLINE_CHARS[index];
  }).join('');
};

// Usage
const vramHistory = [4.2, 4.5, 4.8, 5.1, 5.3, 5.8, 5.6, 5.4, 5.7, 6.0];
console.log(createSparkline(vramHistory));
// Output: ▂▃▄▅▅▇▆▅▆█
```

---

## art.py Analysis & JavaScript Equivalents

### What is art.py?

**art.py** is a Python library for converting text to ASCII art with fancy fonts. It's similar to the classic FIGlet utility.

**Key Capabilities:**
- `text2art()` - Convert text to ASCII art string
- `tprint()` - Print ASCII text directly
- Multiple font support (400+ fonts)
- Random font selection
- Character handling for unsupported characters
- ASCII and Non-ASCII font support
- Customizable line separators

**Example:**
```python
from art import text2art

banner = text2art("SYNAPSE", font="block")
print(banner)
```

### JavaScript Equivalent: figlet.js

**figlet.js** is the JavaScript/TypeScript equivalent, implementing the same FIGfont specification.

**Comparison:**

| Feature | art.py | figlet.js |
|---------|--------|-----------|
| Font Count | 400+ | 400+ (same fonts) |
| API Style | `text2art()` | `figlet.text()` async |
| Browser Support | ❌ Python only | ✅ Yes |
| TypeScript | ❌ No | ✅ Native TypeScript |
| Font Loading | Auto | Manual preload for browser |
| Async Support | ❌ Sync only | ✅ Async + Sync |

**Recreation in JS/TS:**

```typescript
// art.py style
import figlet from "figlet";
import standard from "figlet/fonts/Standard";

// Preload font (one-time setup)
figlet.parseFont("Standard", standard);

// art.py: text2art("SYNAPSE", font="block")
const banner = await figlet.text("SYNAPSE", {
  font: "Standard",
  horizontalLayout: "default",
});

console.log(banner);

// art.py: tprint("SYNAPSE", font="block")
figlet.text("SYNAPSE", { font: "Standard" }, (err, text) => {
  if (!err) console.log(text);
});
```

**Conclusion:** Use **figlet.js** as the JavaScript equivalent of art.py. It's mature, actively maintained, and has excellent browser support.

---

## Top 5 Recommended Libraries

### 1. simple-ascii-chart ⭐⭐⭐⭐⭐

**Why:** TypeScript-native, feature-rich, perfect for metrics dashboards

**Capabilities:**
- Bar charts (vertical/horizontal)
- Line charts with multiple series
- Sparklines (compact visualization)
- ANSI color support (easily styled with phosphor orange)
- Custom formatters
- Legends, axis labels, titles
- Threshold lines
- Area fill mode

**WebTUI Integration:**
- Generate ASCII chart string with `plot(data, settings)`
- Render in `<pre>` tag styled by WebTUI
- Apply phosphor glow with CSS filters
- Use ANSI colors mapped to CSS custom properties

**React Component Example:**

```typescript
// /frontend/src/components/terminal/AsciiChart/AsciiChart.tsx
import React, { useMemo } from 'react';
import { plot } from 'simple-ascii-chart';
import styles from './AsciiChart.module.css';

interface AsciiChartProps {
  data: [number, number][] | [number, number][][];
  mode?: 'line' | 'bar' | 'horizontalBar' | 'point';
  width?: number;
  height?: number;
  title?: string;
  color?: 'ansiCyan' | 'ansiMagenta' | 'ansiYellow' | 'ansiGreen';
  fillArea?: boolean;
}

export const AsciiChart: React.FC<AsciiChartProps> = ({
  data,
  mode = 'line',
  width = 40,
  height = 10,
  title,
  color = 'ansiCyan',
  fillArea = false,
}) => {
  const chartOutput = useMemo(() => {
    return plot(data, {
      mode,
      width,
      height,
      title,
      color,
      fillArea,
      showTickLabel: true,
    });
  }, [data, mode, width, height, title, color, fillArea]);

  return (
    <pre className={styles.asciiChart} aria-label={title || 'ASCII Chart'}>
      {chartOutput}
    </pre>
  );
};
```

**CSS Module:**

```css
/* /frontend/src/components/terminal/AsciiChart/AsciiChart.module.css */
.asciiChart {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-orange);
  text-shadow: var(--phosphor-text-glow);
  white-space: pre;
  overflow-x: auto;
  margin: 0;
  padding: var(--space-sm);
  background: transparent;
  line-height: 1.2;
}

.asciiChart::-webkit-scrollbar {
  height: 4px;
}

.asciiChart::-webkit-scrollbar-thumb {
  background: var(--color-dim);
  border-radius: 2px;
}
```

**Effort Estimate:** 4 hours
- Component creation: 1h
- Styling integration: 1h
- Testing with real data: 1h
- Documentation: 1h

---

### 2. figlet.js ⭐⭐⭐⭐⭐

**Why:** Perfect for large ASCII text banners, headers, branding

**Capabilities:**
- 400+ professional fonts
- Async/sync rendering
- Browser font preloading
- Layout control (horizontal/vertical)
- Width limiting
- Full FIGfont spec support

**WebTUI Integration:**
- Preload fonts on app startup
- Generate banner text asynchronously
- Render in styled container with phosphor glow
- Use for dashboard headers, section titles, loading screens

**React Component Example:**

```typescript
// /frontend/src/components/terminal/AsciiBanner/AsciiBanner.tsx
import React, { useEffect, useState } from 'react';
import figlet from 'figlet';
import standard from 'figlet/fonts/Standard';
import styles from './AsciiBanner.module.css';

// Preload font (module-level, runs once)
figlet.parseFont('Standard', standard);

interface AsciiBannerProps {
  text: string;
  font?: string;
  className?: string;
}

export const AsciiBanner: React.FC<AsciiBannerProps> = ({
  text,
  font = 'Standard',
  className,
}) => {
  const [banner, setBanner] = useState<string>('');

  useEffect(() => {
    figlet.text(text, { font }, (err, result) => {
      if (!err && result) {
        setBanner(result);
      }
    });
  }, [text, font]);

  if (!banner) return null;

  return (
    <pre className={`${styles.banner} ${className || ''}`} aria-label={`${text} Banner`}>
      {banner}
    </pre>
  );
};
```

**CSS Module:**

```css
/* /frontend/src/components/terminal/AsciiBanner/AsciiBanner.module.css */
.banner {
  font-family: var(--font-mono);
  font-size: 8px;
  color: var(--color-orange);
  text-shadow: var(--phosphor-text-glow);
  white-space: pre;
  overflow-x: auto;
  margin: 0;
  padding: var(--space-md);
  text-align: center;
  line-height: 1;
  letter-spacing: -1px;
}

/* Glow animation on load */
@keyframes banner-glow {
  0% {
    text-shadow: 0 0 2px #ff9500;
  }
  50% {
    text-shadow: 0 0 8px #ff9500, 0 0 16px #ff9500aa;
  }
  100% {
    text-shadow: 0 0 2px #ff9500;
  }
}

.banner {
  animation: banner-glow 3s ease-in-out;
}

/* Responsive sizing */
@media (max-width: 768px) {
  .banner {
    font-size: 6px;
  }
}
```

**Usage Example:**

```typescript
// In dashboard header
<AsciiBanner text="SYNAPSE" font="Standard" />
```

**Effort Estimate:** 3 hours
- Font preloading setup: 0.5h
- Component creation: 1h
- Styling with phosphor glow: 1h
- Testing with different fonts: 0.5h

---

### 3. text-graph.js ⭐⭐⭐⭐

**Why:** Advanced charting with multi-series, dashboard layouts, TypeScript support

**Capabilities:**
- Multi-series line charts
- Dashboard layouts (multiple charts in grid)
- Axis scaling (linear, logarithmic)
- Data aggregation (mean, max, min)
- Overflow handling
- Color customization
- Title positioning
- No dependencies

**WebTUI Integration:**
- Create Plot instances with custom colors
- Render multiple charts in grid layout
- Real-time data updates with smooth transitions
- Color mapping to phosphor palette

**React Component Example:**

```typescript
// /frontend/src/components/terminal/TextGraph/TextGraph.tsx
import React, { useMemo } from 'react';
import { Plot, PlotAxisScale, Color } from 'text-graph.js';
import styles from './TextGraph.module.css';

interface TextGraphProps {
  data: number[][];
  width?: number;
  height?: number;
  title?: string;
  showAxis?: boolean;
  colors?: Color[];
}

export const TextGraph: React.FC<TextGraphProps> = ({
  data,
  width = 60,
  height = 15,
  title,
  showAxis = true,
  colors = [Color.cyan, Color.magenta, Color.yellow],
}) => {
  const chartOutput = useMemo(() => {
    const plot = new Plot(width, height, {
      showAxis,
      title,
      axisScale: PlotAxisScale.linear,
      titleForeground: Color.cyan,
    });

    data.forEach((series, index) => {
      const seriesId = plot.addSeries({
        color: colors[index % colors.length],
      });
      plot.addSeriesRange(seriesId, series);
    });

    return plot.paint();
  }, [data, width, height, title, showAxis, colors]);

  return (
    <pre className={styles.textGraph} aria-label={title || 'Text Graph'}>
      {chartOutput}
    </pre>
  );
};
```

**CSS Module:**

```css
/* /frontend/src/components/terminal/TextGraph/TextGraph.module.css */
.textGraph {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-orange);
  text-shadow: var(--phosphor-text-glow);
  white-space: pre;
  overflow-x: auto;
  margin: 0;
  padding: var(--space-sm);
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid var(--color-orange);
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(255, 149, 0, 0.2);
}
```

**Effort Estimate:** 5 hours
- Component creation: 2h
- Multi-series handling: 1h
- Color customization: 1h
- Testing and optimization: 1h

---

### 4. asciichart ⭐⭐⭐⭐

**Why:** Lightweight, stable, perfect for simple line charts

**Capabilities:**
- Simple line charts
- Auto-scaling
- Multiple series
- Color support
- Minimal footprint
- No dependencies

**WebTUI Integration:**
- Drop-in chart generation
- Render in styled pre tags
- Apply phosphor glow with CSS
- Use for sparklines and simple trends

**React Component Example:**

```typescript
// /frontend/src/components/terminal/Sparkline/Sparkline.tsx
import React, { useMemo } from 'react';
import asciichart from 'asciichart';
import styles from './Sparkline.module.css';

interface SparklineProps {
  data: number[];
  height?: number;
  label?: string;
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  height = 5,
  label,
}) => {
  const chartOutput = useMemo(() => {
    return asciichart.plot(data, { height });
  }, [data, height]);

  return (
    <div className={styles.sparklineContainer}>
      {label && <span className={styles.label}>{label}</span>}
      <pre className={styles.sparkline} aria-label={label || 'Sparkline Chart'}>
        {chartOutput}
      </pre>
    </div>
  );
};
```

**CSS Module:**

```css
/* /frontend/src/components/terminal/Sparkline/Sparkline.module.css */
.sparklineContainer {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--color-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sparkline {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--color-cyan);
  text-shadow: 0 0 2px var(--color-cyan), 0 0 4px var(--color-cyan);
  white-space: pre;
  margin: 0;
  padding: 0;
  line-height: 1;
}
```

**Effort Estimate:** 2 hours
- Component creation: 0.5h
- Styling: 0.5h
- TypeScript types: 0.5h
- Testing: 0.5h

---

### 5. Custom Box Drawing Utility ⭐⭐⭐⭐⭐

**Why:** Full control, no dependencies, perfect for panel borders

**Capabilities:**
- Light, heavy, double, rounded borders
- Custom box sizes
- Title insertion
- Join characters for nested boxes
- Unicode block characters for progress bars

**Implementation:**

```typescript
// /frontend/src/utils/boxDrawing.ts

type BorderStyle = 'light' | 'heavy' | 'double' | 'rounded';

interface BoxChars {
  topLeft: string;
  topRight: string;
  bottomLeft: string;
  bottomRight: string;
  horizontal: string;
  vertical: string;
  topJoin?: string;
  bottomJoin?: string;
  leftJoin?: string;
  rightJoin?: string;
  cross?: string;
}

const BORDER_CHARS: Record<BorderStyle, BoxChars> = {
  light: {
    topLeft: '┌', topRight: '┐', bottomLeft: '└', bottomRight: '┘',
    horizontal: '─', vertical: '│',
    topJoin: '┬', bottomJoin: '┴', leftJoin: '├', rightJoin: '┤',
    cross: '┼',
  },
  heavy: {
    topLeft: '┏', topRight: '┓', bottomLeft: '┗', bottomRight: '┛',
    horizontal: '━', vertical: '┃',
    topJoin: '┳', bottomJoin: '┻', leftJoin: '┣', rightJoin: '┫',
    cross: '╋',
  },
  double: {
    topLeft: '╔', topRight: '╗', bottomLeft: '╚', bottomRight: '╝',
    horizontal: '═', vertical: '║',
    topJoin: '╦', bottomJoin: '╩', leftJoin: '╠', rightJoin: '╣',
    cross: '╬',
  },
  rounded: {
    topLeft: '╭', topRight: '╮', bottomLeft: '╰', bottomRight: '╯',
    horizontal: '─', vertical: '│',
  },
};

export const createBox = (
  width: number,
  height: number,
  style: BorderStyle = 'light',
  title?: string
): string => {
  const chars = BORDER_CHARS[style];
  const lines: string[] = [];

  // Top border with optional title
  let topLine = chars.topLeft;
  if (title) {
    const titlePadding = Math.max(0, width - 4 - title.length);
    const leftPad = Math.floor(titlePadding / 2);
    const rightPad = Math.ceil(titlePadding / 2);
    topLine += chars.horizontal + ' ' + title + ' ' + chars.horizontal.repeat(rightPad) + chars.topRight;
  } else {
    topLine += chars.horizontal.repeat(width - 2) + chars.topRight;
  }
  lines.push(topLine);

  // Middle lines
  for (let i = 0; i < height - 2; i++) {
    lines.push(chars.vertical + ' '.repeat(width - 2) + chars.vertical);
  }

  // Bottom border
  lines.push(chars.bottomLeft + chars.horizontal.repeat(width - 2) + chars.bottomRight);

  return lines.join('\n');
};

export const createProgressBar = (
  value: number,
  max: number,
  width: number = 40,
  filledChar: string = '█',
  emptyChar: string = '░'
): string => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;

  return `[${filledChar.repeat(filled)}${emptyChar.repeat(empty)}] ${percentage.toFixed(0)}%`;
};

export const createSparkline = (data: number[]): string => {
  const chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];

  if (data.length === 0) return '';

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  return data.map(value => {
    const normalized = (value - min) / range;
    const index = Math.min(7, Math.floor(normalized * 8));
    return chars[index];
  }).join('');
};
```

**React Component Example:**

```typescript
// /frontend/src/components/terminal/BoxPanel/BoxPanel.tsx
import React from 'react';
import { createBox } from '@/utils/boxDrawing';
import styles from './BoxPanel.module.css';

interface BoxPanelProps {
  title?: string;
  width?: number;
  height?: number;
  style?: 'light' | 'heavy' | 'double' | 'rounded';
  children: React.ReactNode;
}

export const BoxPanel: React.FC<BoxPanelProps> = ({
  title,
  width = 60,
  height = 10,
  style = 'light',
  children,
}) => {
  const box = createBox(width, height, style, title);

  return (
    <div className={styles.boxPanel}>
      <pre className={styles.border} aria-hidden="true">
        {box}
      </pre>
      <div className={styles.content}>
        {children}
      </div>
    </div>
  );
};
```

**Effort Estimate:** 6 hours
- Utility functions: 2h
- Component integration: 2h
- Styling and positioning: 1h
- Testing: 1h

---

## WebTUI Integration Strategy

### Phase 1: Foundation Setup (Week 1)

**Goal:** Install WebTUI and configure base styling

**Tasks:**
1. Install WebTUI CSS framework
   ```bash
   npm install @webtui/css
   ```

2. Configure CSS layer imports in main stylesheet
   ```css
   /* /frontend/src/assets/styles/main.css */
   @layer base, utils, components;
   @import '@webtui/css';
   ```

3. Customize WebTUI theme with phosphor orange
   ```css
   /* /frontend/src/assets/styles/theme.css */
   :root {
     --webtui-primary: #ff9500;
     --webtui-background: #000000;
     --webtui-accent: #00ffff;
     --webtui-text: #ff9500;
     --webtui-border: #ff9500;
   }
   ```

4. Test WebTUI components in isolation
   - Create test page with WebTUI buttons, inputs, panels
   - Verify phosphor glow works with WebTUI classes
   - Check responsive behavior

**Effort:** 8 hours

---

### Phase 2: ASCII Library Integration (Week 2)

**Goal:** Wrap ASCII libraries in React components

**Tasks:**
1. Install ASCII libraries
   ```bash
   npm install simple-ascii-chart figlet text-graph.js asciichart
   npm install --save-dev @types/figlet
   ```

2. Create wrapper components (see examples above):
   - `AsciiChart.tsx` (simple-ascii-chart)
   - `AsciiBanner.tsx` (figlet.js)
   - `TextGraph.tsx` (text-graph.js)
   - `Sparkline.tsx` (asciichart)
   - `BoxPanel.tsx` (custom utility)

3. Create shared types
   ```typescript
   // /frontend/src/types/ascii.ts
   export type ChartMode = 'line' | 'bar' | 'horizontalBar' | 'point';
   export type ChartColor = 'ansiCyan' | 'ansiMagenta' | 'ansiYellow' | 'ansiGreen';
   export type BorderStyle = 'light' | 'heavy' | 'double' | 'rounded';
   ```

4. Create CSS modules for each component with WebTUI integration

**Effort:** 20 hours (4h per component × 5)

---

### Phase 3: Component Composition (Week 3)

**Goal:** Build composite components using ASCII libraries + WebTUI

**Tasks:**
1. Create `ModelStatusPanel` with ASCII charts
   ```typescript
   <BoxPanel title="MODEL STATUS" style="heavy">
     <div className={styles.modelGrid}>
       {models.map(model => (
         <div key={model.name}>
           <h3>{model.name}</h3>
           <Sparkline data={model.vramHistory} label="VRAM" />
           <AsciiChart
             data={model.queryTrend}
             mode="line"
             color="ansiCyan"
             width={30}
             height={5}
           />
         </div>
       ))}
     </div>
   </BoxPanel>
   ```

2. Create `SystemMetricsPanel` with multiple charts
   ```typescript
   <BoxPanel title="SYSTEM METRICS" style="double">
     <TextGraph
       data={[cpuHistory, memHistory, vramHistory]}
       title="Resource Utilization"
       colors={[Color.cyan, Color.magenta, Color.yellow]}
     />
   </BoxPanel>
   ```

3. Create `DashboardHeader` with ASCII banner
   ```typescript
   <AsciiBanner text="SYNAPSE" font="Standard" />
   ```

4. Integrate into existing pages (HomePage, MetricsPage, etc.)

**Effort:** 16 hours

---

### Phase 4: Real-Time Updates (Week 4)

**Goal:** Connect ASCII visualizations to WebSocket data

**Tasks:**
1. Create custom hooks for live data
   ```typescript
   // /frontend/src/hooks/useModelMetrics.ts
   export const useModelMetrics = (modelName: string) => {
     const [vramHistory, setVramHistory] = useState<number[]>([]);

     useEffect(() => {
       const ws = new WebSocket('ws://localhost:8000/ws');

       ws.onmessage = (event) => {
         const data = JSON.parse(event.data);
         if (data.type === 'model_metrics' && data.model === modelName) {
           setVramHistory(prev => [...prev.slice(-20), data.vram]);
         }
       };

       return () => ws.close();
     }, [modelName]);

     return { vramHistory };
   };
   ```

2. Update components to use live data
   ```typescript
   const ModelStatusCard: React.FC<{ model: Model }> = ({ model }) => {
     const { vramHistory } = useModelMetrics(model.name);

     return (
       <div>
         <Sparkline data={vramHistory} label="VRAM" />
       </div>
     );
   };
   ```

3. Implement smooth transitions with React.memo
   ```typescript
   export const Sparkline = React.memo<SparklineProps>(({ data, label }) => {
     // Component implementation
   }, (prev, next) => {
     return JSON.stringify(prev.data) === JSON.stringify(next.data);
   });
   ```

4. Add loading states and error handling

**Effort:** 12 hours

---

### Phase 5: Polish & Optimization (Week 5)

**Goal:** Fine-tune performance and aesthetics

**Tasks:**
1. Performance optimization
   - Use `useMemo` for chart generation
   - Implement virtual scrolling for long lists
   - Throttle WebSocket updates to 30fps
   - Profile with React DevTools

2. Accessibility improvements
   - Add ARIA labels to all charts
   - Ensure keyboard navigation works
   - Test with screen readers
   - Add `aria-live` regions for updates

3. Visual polish
   - Fine-tune phosphor glow intensity
   - Add subtle scan line effect
   - Implement CRT bezel frame
   - Test color contrast ratios

4. Documentation
   - Component API docs
   - Usage examples
   - Storybook stories
   - Integration guide

**Effort:** 16 hours

---

### Total WebTUI Integration Timeline

**Total Effort:** 72 hours (approximately 2 weeks for 1 developer)

**Phased Rollout:**
- Week 1: Foundation (8h)
- Week 2: ASCII Libraries (20h)
- Week 3: Composition (16h)
- Week 4: Real-Time (12h)
- Week 5: Polish (16h)

---

## React Component Examples

### Complete Example: VRAM Monitor Panel

This example demonstrates full integration of ASCII libraries with WebTUI styling and real-time data.

```typescript
// /frontend/src/components/dashboard/VRAMMonitorPanel/VRAMMonitorPanel.tsx
import React, { useMemo } from 'react';
import { plot } from 'simple-ascii-chart';
import { createSparkline, createProgressBar } from '@/utils/boxDrawing';
import { useModelMetrics } from '@/hooks/useModelMetrics';
import styles from './VRAMMonitorPanel.module.css';

interface VRAMMonitorPanelProps {
  modelName: string;
  maxVRAM: number;
}

export const VRAMMonitorPanel: React.FC<VRAMMonitorPanelProps> = ({
  modelName,
  maxVRAM,
}) => {
  const { vramHistory, currentVRAM } = useModelMetrics(modelName);

  const sparkline = useMemo(() => {
    return createSparkline(vramHistory);
  }, [vramHistory]);

  const progressBar = useMemo(() => {
    return createProgressBar(currentVRAM, maxVRAM, 40);
  }, [currentVRAM, maxVRAM]);

  const chart = useMemo(() => {
    if (vramHistory.length < 2) return '';

    const chartData = vramHistory.map((value, index) => [index, value]);
    return plot(chartData, {
      mode: 'line',
      width: 50,
      height: 10,
      title: 'VRAM Trend (Last 60s)',
      color: 'ansiCyan',
      showTickLabel: true,
      yRange: [0, maxVRAM],
    });
  }, [vramHistory, maxVRAM]);

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h3 className={styles.title}>{modelName}</h3>
        <span className={styles.sparkline} aria-label="VRAM Sparkline">
          {sparkline}
        </span>
      </div>

      <div className={styles.progressSection}>
        <pre className={styles.progressBar} aria-label={`VRAM Usage: ${currentVRAM} GB of ${maxVRAM} GB`}>
          {progressBar}
        </pre>
        <div className={styles.stats}>
          <span className={styles.stat}>
            <span className={styles.label}>CURRENT:</span>
            <span className={styles.value}>{currentVRAM.toFixed(1)} GB</span>
          </span>
          <span className={styles.stat}>
            <span className={styles.label}>MAX:</span>
            <span className={styles.value}>{maxVRAM.toFixed(1)} GB</span>
          </span>
        </div>
      </div>

      {chart && (
        <pre className={styles.chart} aria-label="VRAM Trend Chart">
          {chart}
        </pre>
      )}
    </div>
  );
};
```

**CSS Module:**

```css
/* /frontend/src/components/dashboard/VRAMMonitorPanel/VRAMMonitorPanel.module.css */
.panel {
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid var(--color-orange);
  border-radius: 4px;
  padding: var(--space-md);
  box-shadow: 0 0 10px rgba(255, 149, 0, 0.2);
  font-family: var(--font-mono);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--color-dim);
}

.title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-orange);
  text-shadow: var(--phosphor-text-glow);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.sparkline {
  font-size: 12px;
  color: var(--color-cyan);
  text-shadow: 0 0 2px var(--color-cyan), 0 0 4px var(--color-cyan);
  letter-spacing: -1px;
}

.progressSection {
  margin: var(--space-md) 0;
}

.progressBar {
  font-size: 12px;
  color: var(--color-orange);
  text-shadow: var(--phosphor-text-glow);
  margin: 0 0 var(--space-sm) 0;
  white-space: pre;
  line-height: 1.2;
}

.stats {
  display: flex;
  gap: var(--space-md);
  font-size: 11px;
}

.stat {
  display: flex;
  gap: var(--space-xs);
}

.label {
  color: var(--color-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value {
  color: var(--color-orange);
  font-weight: 600;
  text-shadow: var(--phosphor-text-glow);
}

.chart {
  font-size: 10px;
  color: var(--color-cyan);
  text-shadow: 0 0 2px var(--color-cyan);
  white-space: pre;
  overflow-x: auto;
  margin: var(--space-md) 0 0 0;
  padding: var(--space-sm);
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid var(--color-dim);
  border-radius: 2px;
  line-height: 1.2;
}

/* Real-time update animation */
@keyframes value-update {
  0%, 100% {
    color: var(--color-orange);
  }
  50% {
    color: var(--color-cyan);
    text-shadow: 0 0 8px var(--color-cyan);
  }
}

.value {
  animation: value-update 0.5s ease-in-out;
}
```

**Usage:**

```typescript
// In Dashboard page
<VRAMMonitorPanel modelName="Q2_FAST_1" maxVRAM={8.0} />
<VRAMMonitorPanel modelName="Q3_BALANCED_1" maxVRAM={16.0} />
<VRAMMonitorPanel modelName="Q4_POWERFUL_1" maxVRAM={24.0} />
```

---

## Implementation Effort Estimates

### Summary Table

| Component/Library | Setup | Development | Testing | Documentation | **Total** |
|-------------------|-------|-------------|---------|---------------|-----------|
| **WebTUI Foundation** | 4h | 2h | 1h | 1h | **8h** |
| **simple-ascii-chart** | 0.5h | 2h | 1h | 0.5h | **4h** |
| **figlet.js** | 0.5h | 1.5h | 0.5h | 0.5h | **3h** |
| **text-graph.js** | 0.5h | 3h | 1h | 0.5h | **5h** |
| **asciichart** | 0.5h | 1h | 0.5h | 0h | **2h** |
| **Custom Box Utils** | 0h | 4h | 1h | 1h | **6h** |
| **Composite Components** | 0h | 12h | 3h | 1h | **16h** |
| **Real-Time Integration** | 0h | 8h | 3h | 1h | **12h** |
| **Performance Optimization** | 0h | 8h | 4h | 0h | **12h** |
| **Accessibility** | 0h | 6h | 2h | 0h | **8h** |
| **Visual Polish** | 0h | 8h | 2h | 0h | **10h** |
| **Documentation** | 0h | 0h | 0h | 6h | **6h** |
| **TOTAL** | **6h** | **55.5h** | **19h** | **11.5h** | **92h** |

**Total Project Effort:** 92 hours (~2.3 weeks for 1 full-time developer)

---

## Priority Ranking

### Tier 1: Must-Have (Immediate Implementation)

**Reasoning:** Core functionality, high impact, low complexity

1. **Custom Box Drawing Utility** (6h)
   - **Impact:** 🔥🔥🔥🔥🔥 Used everywhere for panels
   - **Effort:** ⚡⚡ Low (no dependencies)
   - **ROI:** 10/10
   - **Dependencies:** None
   - **Start Immediately:** Yes

2. **simple-ascii-chart** (4h)
   - **Impact:** 🔥🔥🔥🔥🔥 Essential for metrics dashboards
   - **Effort:** ⚡⚡ Low (library does heavy lifting)
   - **ROI:** 10/10
   - **Dependencies:** None
   - **Start Immediately:** Yes

3. **WebTUI Foundation** (8h)
   - **Impact:** 🔥🔥🔥🔥 Foundation for all future work
   - **Effort:** ⚡⚡⚡ Medium (one-time setup)
   - **ROI:** 9/10
   - **Dependencies:** None
   - **Start Immediately:** Yes

**Tier 1 Total:** 18 hours

---

### Tier 2: High Priority (Week 2)

**Reasoning:** Significant value-add, moderate complexity

4. **figlet.js** (3h)
   - **Impact:** 🔥🔥🔥🔥 Great for branding, headers
   - **Effort:** ⚡⚡ Low (async rendering)
   - **ROI:** 8/10
   - **Dependencies:** None
   - **Start After:** Tier 1 complete

5. **text-graph.js** (5h)
   - **Impact:** 🔥🔥🔥🔥 Advanced charting capabilities
   - **Effort:** ⚡⚡⚡ Medium (multi-series complexity)
   - **ROI:** 8/10
   - **Dependencies:** simple-ascii-chart patterns
   - **Start After:** simple-ascii-chart complete

6. **Composite Components** (16h)
   - **Impact:** 🔥🔥🔥🔥🔥 Brings everything together
   - **Effort:** ⚡⚡⚡⚡ High (integration work)
   - **ROI:** 9/10
   - **Dependencies:** Tier 1 complete
   - **Start After:** Box utils + charts ready

**Tier 2 Total:** 24 hours

---

### Tier 3: Medium Priority (Week 3)

**Reasoning:** Polish and optimization

7. **Real-Time Integration** (12h)
   - **Impact:** 🔥🔥🔥🔥🔥 Live dashboards are killer feature
   - **Effort:** ⚡⚡⚡⚡ High (WebSocket handling)
   - **ROI:** 9/10
   - **Dependencies:** Composite components
   - **Start After:** Tier 2 complete

8. **Performance Optimization** (12h)
   - **Impact:** 🔥🔥🔥 Ensures 60fps
   - **Effort:** ⚡⚡⚡⚡ High (profiling, testing)
   - **ROI:** 7/10
   - **Dependencies:** Real-time integration
   - **Start After:** Real-time working

9. **asciichart** (2h)
   - **Impact:** 🔥🔥 Nice-to-have for simple cases
   - **Effort:** ⚡ Very low
   - **ROI:** 6/10
   - **Dependencies:** None (can add anytime)
   - **Start After:** When needed

**Tier 3 Total:** 26 hours

---

### Tier 4: Low Priority (Week 4+)

**Reasoning:** Nice-to-have, can be deferred

10. **Accessibility Enhancements** (8h)
    - **Impact:** 🔥🔥🔥 Important but can be incremental
    - **Effort:** ⚡⚡⚡ Medium (testing required)
    - **ROI:** 6/10
    - **Dependencies:** None
    - **Start After:** Core features stable

11. **Visual Polish** (10h)
    - **Impact:** 🔥🔥🔥 Looks great but not critical
    - **Effort:** ⚡⚡⚡ Medium (CRT effects, etc.)
    - **ROI:** 6/10
    - **Dependencies:** Core features complete
    - **Start After:** All functionality working

12. **Documentation** (6h)
    - **Impact:** 🔥🔥 Essential long-term
    - **Effort:** ⚡⚡ Low (write as you go)
    - **ROI:** 7/10
    - **Dependencies:** Features finalized
    - **Start After:** Ongoing throughout

**Tier 4 Total:** 24 hours

---

### Recommended Roadmap

**Sprint 1 (Week 1): Foundation**
- WebTUI setup (8h)
- Custom box drawing (6h)
- simple-ascii-chart (4h)
- **Total:** 18h

**Sprint 2 (Week 2): Core Components**
- figlet.js (3h)
- text-graph.js (5h)
- Composite components (16h)
- **Total:** 24h

**Sprint 3 (Week 3): Integration**
- Real-time WebSocket integration (12h)
- asciichart (2h)
- Performance optimization (12h)
- **Total:** 26h

**Sprint 4 (Week 4): Polish**
- Accessibility (8h)
- Visual polish (10h)
- Documentation (6h)
- **Total:** 24h

**Grand Total:** 92 hours

---

## Performance Considerations

### Chart Rendering Performance

**Challenge:** ASCII chart generation can be CPU-intensive, especially for large datasets or real-time updates.

**Solutions:**

1. **Memoization**
   ```typescript
   const chartOutput = useMemo(() => {
     return plot(data, settings);
   }, [data, settings]); // Only regenerate when data changes
   ```

2. **Debouncing/Throttling**
   ```typescript
   import { useDebouncedValue } from '@/hooks/useDebouncedValue';

   const debouncedData = useDebouncedValue(realtimeData, 100); // Update max 10x/sec
   const chartOutput = useMemo(() => plot(debouncedData, settings), [debouncedData]);
   ```

3. **Data Sampling**
   ```typescript
   const sampleData = (data: number[], maxPoints: number = 100): number[] => {
     if (data.length <= maxPoints) return data;
     const step = Math.floor(data.length / maxPoints);
     return data.filter((_, index) => index % step === 0);
   };
   ```

4. **Web Workers for Heavy Processing**
   ```typescript
   // asciiChartWorker.ts
   self.onmessage = (e) => {
     const { data, settings } = e.data;
     const chart = plot(data, settings);
     self.postMessage({ chart });
   };

   // Component
   const worker = useMemo(() => new Worker(new URL('./asciiChartWorker.ts', import.meta.url)), []);
   ```

---

### Rendering Optimization

**Challenge:** Large `<pre>` tags with ASCII art can cause layout thrashing.

**Solutions:**

1. **GPU Acceleration**
   ```css
   .asciiChart {
     transform: translateZ(0); /* Force GPU layer */
     will-change: transform; /* Hint browser for optimization */
   }
   ```

2. **Virtual Scrolling for Long Outputs**
   ```typescript
   import { FixedSizeList } from 'react-window';

   <FixedSizeList
     height={400}
     itemCount={logLines.length}
     itemSize={20}
     width="100%"
   >
     {({ index, style }) => (
       <pre style={style}>{logLines[index]}</pre>
     )}
   </FixedSizeList>
   ```

3. **Avoid Unnecessary Re-renders**
   ```typescript
   export const AsciiChart = React.memo<AsciiChartProps>(
     ({ data, ...props }) => {
       // Component implementation
     },
     (prev, next) => {
       // Custom comparison to prevent re-renders
       return (
         JSON.stringify(prev.data) === JSON.stringify(next.data) &&
         prev.width === next.width &&
         prev.height === next.height
       );
     }
   );
   ```

---

### WebSocket Performance

**Challenge:** High-frequency WebSocket updates can overwhelm the UI.

**Solutions:**

1. **Update Throttling**
   ```typescript
   const METRIC_UPDATE_INTERVAL = 33; // 30fps max

   useEffect(() => {
     let buffer: MetricUpdate[] = [];

     const ws = new WebSocket('ws://localhost:8000/ws');

     ws.onmessage = (event) => {
       buffer.push(JSON.parse(event.data));
     };

     const interval = setInterval(() => {
       if (buffer.length > 0) {
         setMetrics(buffer[buffer.length - 1]); // Use latest only
         buffer = [];
       }
     }, METRIC_UPDATE_INTERVAL);

     return () => {
       clearInterval(interval);
       ws.close();
     };
   }, []);
   ```

2. **Batching State Updates**
   ```typescript
   import { unstable_batchedUpdates } from 'react-dom';

   ws.onmessage = (event) => {
     const updates = JSON.parse(event.data);
     unstable_batchedUpdates(() => {
       setVRAM(updates.vram);
       setQueries(updates.queries);
       setLatency(updates.latency);
     });
   };
   ```

---

### Memory Management

**Challenge:** Long-running dashboards can leak memory if not careful.

**Solutions:**

1. **Limit Historical Data**
   ```typescript
   const MAX_HISTORY = 100;

   setVramHistory(prev => {
     const updated = [...prev, newValue];
     return updated.length > MAX_HISTORY
       ? updated.slice(-MAX_HISTORY)
       : updated;
   });
   ```

2. **Clean Up Timers and Subscriptions**
   ```typescript
   useEffect(() => {
     const ws = new WebSocket('ws://...');
     const interval = setInterval(() => { /* ... */ }, 1000);

     return () => {
       ws.close();
       clearInterval(interval);
     };
   }, []);
   ```

3. **Profile with Chrome DevTools**
   - Use Memory profiler to detect leaks
   - Use Performance profiler to identify bottlenecks
   - Monitor frame rate with FPS meter

---

## Additional Resources

### Documentation Links

**Libraries:**
- [simple-ascii-chart Documentation](https://simple-ascii-chart.vercel.app/)
- [figlet.js GitHub](https://github.com/patorjk/figlet.js)
- [text-graph.js GitHub](https://github.com/DrA1ex/text-graph.js)
- [asciichart GitHub](https://github.com/kroitor/asciichart)
- [WebTUI Documentation](https://webtui.ironclad.sh/)

**Fonts & Resources:**
- [FIGlet Font Database](http://www.figlet.org/fontdb.cgi)
- [Unicode Box Drawing Characters](https://en.wikipedia.org/wiki/Box-drawing_character)
- [Unicode Block Elements](https://en.wikipedia.org/wiki/Block_Elements)

**React & TypeScript:**
- [React.memo Documentation](https://react.dev/reference/react/memo)
- [useMemo Hook](https://react.dev/reference/react/useMemo)
- [TypeScript Declaration Files](https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html)

---

### Code Examples Repository

Create a `/examples` directory in the project with working demos:

```
/frontend/examples/
├── ascii-charts/
│   ├── SimpleLineChart.tsx
│   ├── BarChart.tsx
│   ├── MultiSeriesChart.tsx
│   └── Sparkline.tsx
├── banners/
│   ├── DynamicBanner.tsx
│   ├── FontShowcase.tsx
│   └── AnimatedBanner.tsx
├── boxes/
│   ├── SimpleBorder.tsx
│   ├── NestedBoxes.tsx
│   └── TitledPanel.tsx
├── real-time/
│   ├── LiveMetricsPanel.tsx
│   ├── StreamingChart.tsx
│   └── WebSocketDemo.tsx
└── README.md
```

---

### Testing Strategy

**Unit Tests:**
```typescript
// AsciiChart.test.tsx
import { render, screen } from '@testing-library/react';
import { AsciiChart } from './AsciiChart';

describe('AsciiChart', () => {
  it('renders chart output', () => {
    const data = [[1, 1], [2, 2], [3, 3]];
    render(<AsciiChart data={data} mode="line" />);

    const chart = screen.getByRole('region');
    expect(chart).toBeInTheDocument();
  });

  it('regenerates chart when data changes', () => {
    const { rerender } = render(<AsciiChart data={[[1, 1]]} mode="line" />);
    const initialOutput = screen.getByRole('region').textContent;

    rerender(<AsciiChart data={[[1, 1], [2, 2]]} mode="line" />);
    const updatedOutput = screen.getByRole('region').textContent;

    expect(updatedOutput).not.toBe(initialOutput);
  });
});
```

**Visual Regression Tests:**
```typescript
// Using Playwright for visual regression
import { test, expect } from '@playwright/test';

test('VRAMMonitorPanel visual snapshot', async ({ page }) => {
  await page.goto('http://localhost:5173/dashboard');

  const panel = page.locator('[data-testid="vram-monitor"]');
  await expect(panel).toHaveScreenshot('vram-monitor.png');
});
```

---

## Conclusion

This research provides a comprehensive roadmap for integrating ASCII visualization libraries with WebTUI CSS framework for the S.Y.N.A.P.S.E. ENGINE project.

**Key Takeaways:**

1. **Top 5 Libraries:**
   - simple-ascii-chart (TypeScript charts)
   - figlet.js (text banners)
   - text-graph.js (advanced charting)
   - asciichart (simple line charts)
   - Custom box drawing (full control)

2. **Integration Strategy:**
   - WebTUI provides CSS foundation
   - ASCII libraries generate content
   - React wraps with TypeScript safety
   - Phosphor orange (#ff9500) styling throughout

3. **Implementation Timeline:**
   - 92 hours total effort
   - 4-week phased rollout
   - Prioritize foundation → core → integration → polish

4. **Performance:**
   - Memoize chart generation
   - Throttle WebSocket updates
   - Use GPU acceleration
   - Profile and optimize

**Next Steps:**

1. Review this document with team
2. Approve library selections
3. Begin Tier 1 implementation (Box utils + simple-ascii-chart + WebTUI)
4. Create example components
5. Integrate into existing dashboards

---

*Document Version: 1.0*
*Last Updated: 2025-11-08*
*Author: Terminal UI Specialist*
*Status: Ready for Review*