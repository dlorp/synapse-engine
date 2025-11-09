# ASCII Libraries Quick Reference

**TL;DR:** Use these 5 libraries with WebTUI for S.Y.N.A.P.S.E. ENGINE terminal UI

---

## At-a-Glance Comparison

| Library | Purpose | Size | TypeScript | Browser | Complexity | Priority |
|---------|---------|------|------------|---------|------------|----------|
| **simple-ascii-chart** | Bar/line charts, sparklines | 50KB | ✅ Native | ✅ Yes | ⚡⚡ Low | 🔥🔥🔥🔥🔥 |
| **figlet.js** | Text banners (400+ fonts) | 200KB | ✅ Native | ✅ Yes | ⚡⚡ Low | 🔥🔥🔥🔥 |
| **text-graph.js** | Multi-series charts | 30KB | ✅ Yes | ✅ Yes | ⚡⚡⚡ Med | 🔥🔥🔥🔥 |
| **asciichart** | Simple line charts | 15KB | ⚠️ Add types | ✅ Yes | ⚡ Very Low | 🔥🔥 |
| **Custom Box Utils** | Borders, progress bars | 0KB | ✅ Yes | ✅ Yes | ⚡⚡ Low | 🔥🔥🔥🔥🔥 |
| **aalib.js** | Image-to-ASCII | 25KB | ⚠️ Add types | ✅ Yes | ⚡⚡⚡ Med | 🔥🔥 |

---

## Installation Commands

```bash
# Essential (install immediately)
npm install simple-ascii-chart figlet

# Advanced (install when needed)
npm install text-graph.js asciichart

# TypeScript types (if needed)
npm install --save-dev @types/figlet
```

---

## Code Snippets

### 1. Simple Bar Chart

```typescript
import { plot } from 'simple-ascii-chart';

const data = [[1, 5], [2, 8], [3, 6], [4, 9]];
const chart = plot(data, {
  mode: 'bar',
  width: 40,
  height: 10,
  color: 'ansiCyan',
});

console.log(chart);
```

**Output:**
```
 ▲
 9┤    ┏━┓
 8┤ ┏━┓┃ ┃
 6┤ ┃ ┃┗━┫
 5┤━┫ ┃  ┃
 └┬─┬─┬─┬▶
  1 2 3 4
```

---

### 2. Text Banner

```typescript
import figlet from 'figlet';
import standard from 'figlet/fonts/Standard';

figlet.parseFont('Standard', standard);

const banner = await figlet.text('SYNAPSE', { font: 'Standard' });
console.log(banner);
```

**Output:**
```
  ____   __   __  _   _      _      ____   ____   _____
 / ___| \ \ / / | \ | |    / \    |  _ \ / ___| | ____|
 \___ \  \ V /  |  \| |   / _ \   | |_) |\___ \ |  _|
  ___) |  | |   | |\  |  / ___ \  |  __/  ___) || |___
 |____/   |_|   |_| \_| /_/   \_\ |_|    |____/ |_____|
```

---

### 3. Multi-Series Chart

```typescript
import { Plot, Color } from 'text-graph.js';

const plot = new Plot(60, 15, {
  showAxis: true,
  title: 'VRAM Usage',
});

const series1 = plot.addSeries({ color: Color.cyan });
const series2 = plot.addSeries({ color: Color.magenta });

plot.addSeriesRange(series1, [4.2, 4.5, 4.8, 5.1]);
plot.addSeriesRange(series2, [2.1, 2.3, 2.2, 2.5]);

console.log(plot.paint());
```

---

### 4. Progress Bar

```typescript
const createProgressBar = (value: number, max: number, width: number = 40): string => {
  const percentage = Math.min(100, (value / max) * 100);
  const filled = Math.round((percentage / 100) * width);
  const empty = width - filled;
  return `[${'\u2588'.repeat(filled)}${'\u2591'.repeat(empty)}] ${percentage.toFixed(0)}%`;
};

console.log(createProgressBar(75, 100, 40));
```

**Output:**
```
[████████████████████████████░░░░░░░░░] 75%
```

---

### 5. Sparkline

```typescript
const createSparkline = (data: number[]): string => {
  const chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  return data.map(value => {
    const normalized = (value - min) / range;
    const index = Math.min(7, Math.floor(normalized * 8));
    return chars[index];
  }).join('');
};

const vramHistory = [4.2, 4.5, 4.8, 5.1, 5.3, 5.8, 5.6, 5.4, 5.7, 6.0];
console.log(createSparkline(vramHistory));
```

**Output:**
```
▂▃▄▅▅▇▆▅▆█
```

---

### 6. Box Drawing

```typescript
const BOX_CHARS = {
  light: { topLeft: '┌', topRight: '┐', bottomLeft: '└', bottomRight: '┘', horizontal: '─', vertical: '│' },
  heavy: { topLeft: '┏', topRight: '┓', bottomLeft: '┗', bottomRight: '┛', horizontal: '━', vertical: '┃' },
  double: { topLeft: '╔', topRight: '╗', bottomLeft: '╚', bottomRight: '╝', horizontal: '═', vertical: '║' },
};

const createBox = (width: number, height: number, style: 'light' | 'heavy' | 'double' = 'light', title?: string): string => {
  const chars = BOX_CHARS[style];
  const lines: string[] = [];

  // Top
  let top = chars.topLeft;
  if (title) {
    top += ` ${title} ` + chars.horizontal.repeat(Math.max(0, width - 4 - title.length)) + chars.topRight;
  } else {
    top += chars.horizontal.repeat(width - 2) + chars.topRight;
  }
  lines.push(top);

  // Middle
  for (let i = 0; i < height - 2; i++) {
    lines.push(chars.vertical + ' '.repeat(width - 2) + chars.vertical);
  }

  // Bottom
  lines.push(chars.bottomLeft + chars.horizontal.repeat(width - 2) + chars.bottomRight);

  return lines.join('\n');
};

console.log(createBox(40, 5, 'heavy', 'MODEL STATUS'));
```

**Output:**
```
┏ MODEL STATUS ━━━━━━━━━━━━━━━━━━━━━━┓
┃                                      ┃
┃                                      ┃
┃                                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## React Component Pattern

```typescript
// /frontend/src/components/terminal/AsciiChart/AsciiChart.tsx
import React, { useMemo } from 'react';
import { plot } from 'simple-ascii-chart';
import styles from './AsciiChart.module.css';

interface AsciiChartProps {
  data: [number, number][];
  mode?: 'line' | 'bar';
  width?: number;
  height?: number;
  title?: string;
}

export const AsciiChart: React.FC<AsciiChartProps> = ({
  data,
  mode = 'line',
  width = 40,
  height = 10,
  title,
}) => {
  const chartOutput = useMemo(() => {
    return plot(data, { mode, width, height, title, color: 'ansiCyan' });
  }, [data, mode, width, height, title]);

  return (
    <pre className={styles.chart} aria-label={title || 'Chart'}>
      {chartOutput}
    </pre>
  );
};
```

**CSS Module:**

```css
.chart {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #ff9500;
  text-shadow: 0 0 2px #ff9500, 0 0 4px #ff9500;
  white-space: pre;
  margin: 0;
  padding: 8px;
  line-height: 1.2;
}
```

**Usage:**

```typescript
<AsciiChart
  data={[[1, 4.2], [2, 4.5], [3, 4.8], [4, 5.1]]}
  mode="line"
  title="VRAM Trend"
/>
```

---

## WebTUI Integration

### Step 1: Install WebTUI

```bash
npm install @webtui/css
```

### Step 2: Configure CSS Layers

```css
/* /frontend/src/assets/styles/main.css */
@layer base, utils, components;
@import '@webtui/css';
```

### Step 3: Customize Theme

```css
/* /frontend/src/assets/styles/theme.css */
:root {
  --webtui-primary: #ff9500;      /* Phosphor orange */
  --webtui-background: #000000;   /* Pure black */
  --webtui-accent: #00ffff;       /* Cyan */
  --webtui-text: #ff9500;
  --webtui-border: #ff9500;
}
```

### Step 4: Use WebTUI Components

```html
<!-- WebTUI provides base styling -->
<button>SUBMIT QUERY</button>

<!-- Your ASCII content inside WebTUI container -->
<pre box-="square">
  ┏━━━━━━━━━━━━━━┓
  ┃ CHART HERE   ┃
  ┗━━━━━━━━━━━━━━┛
</pre>
```

---

## Performance Tips

### 1. Memoize Chart Generation

```typescript
const chartOutput = useMemo(() => {
  return plot(data, settings);
}, [data, settings]); // Only regenerate when data changes
```

### 2. Throttle WebSocket Updates

```typescript
const THROTTLE_MS = 33; // 30fps max

useEffect(() => {
  let buffer: any[] = [];
  const ws = new WebSocket('ws://localhost:8000/ws');

  ws.onmessage = (e) => buffer.push(JSON.parse(e.data));

  const interval = setInterval(() => {
    if (buffer.length > 0) {
      setMetrics(buffer[buffer.length - 1]); // Use latest only
      buffer = [];
    }
  }, THROTTLE_MS);

  return () => {
    clearInterval(interval);
    ws.close();
  };
}, []);
```

### 3. Limit Historical Data

```typescript
const MAX_HISTORY = 100;

setVramHistory(prev => {
  const updated = [...prev, newValue];
  return updated.length > MAX_HISTORY ? updated.slice(-MAX_HISTORY) : updated;
});
```

### 4. GPU Acceleration

```css
.chart {
  transform: translateZ(0);
  will-change: transform;
}
```

---

## Character Reference

### Box Drawing

```
Light:  ┌─┬─┐  ├─┼─┤  └─┴─┘
Heavy:  ┏━┳━┓  ┣━╋━┫  ┗━┻━┛
Double: ╔═╦═╗  ╠═╬═╣  ╚═╩═╝
Rounded: ╭─┬─╮  ├─┼─┤  ╰─┴─╯
```

### Block Elements

```
░ ▒ ▓ █     (25% 50% 75% 100% filled)
▀ ▄ ▌ ▐     (top half, bottom half, left half, right half)
▁▂▃▄▅▆▇█    (vertical bars for sparklines)
```

### Symbols

```
● ○ ◉ ◌     (status indicators)
✓ ✗         (checkmarks)
◆ ◇ ■ □     (diamonds, squares)
▶ ◀ ▲ ▼     (arrows for collapse/expand)
⚡ ⚙ ⚠      (icons: lightning, gear, warning)
```

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Install WebTUI (`npm install @webtui/css`)
- [ ] Configure CSS layers and theme
- [ ] Create box drawing utility (`/utils/boxDrawing.ts`)
- [ ] Install simple-ascii-chart (`npm install simple-ascii-chart`)
- [ ] Create AsciiChart component (`/components/terminal/AsciiChart/`)

### Week 2: Core Components
- [ ] Install figlet.js (`npm install figlet`)
- [ ] Create AsciiBanner component
- [ ] Install text-graph.js (`npm install text-graph.js`)
- [ ] Create TextGraph component
- [ ] Build composite panels (ModelStatusPanel, SystemMetricsPanel)

### Week 3: Integration
- [ ] Connect charts to WebSocket data
- [ ] Implement live updates with throttling
- [ ] Add memoization for performance
- [ ] Test with real data streams

### Week 4: Polish
- [ ] Add accessibility labels (aria-label, aria-live)
- [ ] Implement phosphor glow effects
- [ ] Add CRT scan lines (optional)
- [ ] Profile and optimize performance
- [ ] Write documentation

---

## Effort Estimates

| Task | Hours | Priority |
|------|-------|----------|
| WebTUI setup | 8h | 🔥🔥🔥🔥🔥 |
| Box drawing utils | 6h | 🔥🔥🔥🔥🔥 |
| simple-ascii-chart | 4h | 🔥🔥🔥🔥🔥 |
| figlet.js | 3h | 🔥🔥🔥🔥 |
| text-graph.js | 5h | 🔥🔥🔥🔥 |
| Composite components | 16h | 🔥🔥🔥🔥🔥 |
| Real-time integration | 12h | 🔥🔥🔥🔥🔥 |
| Performance optimization | 12h | 🔥🔥🔥 |
| Accessibility | 8h | 🔥🔥🔥 |
| Visual polish | 10h | 🔥🔥🔥 |
| **TOTAL** | **84h** | **(~2 weeks)** |

---

## Common Pitfalls to Avoid

### ❌ Don't: Generate charts on every render

```typescript
// BAD
const MyComponent = ({ data }) => {
  const chart = plot(data, settings); // Regenerates every render!
  return <pre>{chart}</pre>;
};
```

### ✅ Do: Memoize chart generation

```typescript
// GOOD
const MyComponent = ({ data }) => {
  const chart = useMemo(() => plot(data, settings), [data]);
  return <pre>{chart}</pre>;
};
```

---

### ❌ Don't: Update charts on every WebSocket message

```typescript
// BAD
ws.onmessage = (e) => {
  setMetrics(JSON.parse(e.data)); // 60+ updates/sec!
};
```

### ✅ Do: Throttle updates to 30fps

```typescript
// GOOD
let buffer = [];
ws.onmessage = (e) => buffer.push(JSON.parse(e.data));

setInterval(() => {
  if (buffer.length > 0) {
    setMetrics(buffer[buffer.length - 1]);
    buffer = [];
  }
}, 33); // 30fps
```

---

### ❌ Don't: Forget to limit historical data

```typescript
// BAD
setHistory(prev => [...prev, newValue]); // Grows forever!
```

### ✅ Do: Cap array size

```typescript
// GOOD
setHistory(prev => {
  const updated = [...prev, newValue];
  return updated.length > 100 ? updated.slice(-100) : updated;
});
```

---

## Questions & Answers

**Q: Can I use these with vanilla JavaScript?**
A: Yes! All libraries work with vanilla JS. React wrappers are optional.

**Q: Do I need to install WebTUI?**
A: Not required, but highly recommended for consistent terminal styling.

**Q: Which library should I start with?**
A: Start with **simple-ascii-chart** and **custom box drawing**. They're the most versatile.

**Q: Can I use these in production?**
A: Yes. All recommended libraries are stable and actively maintained.

**Q: What about bundle size?**
A: Total impact: ~300KB (gzipped: ~80KB). Acceptable for desktop dashboards.

**Q: How do I style the ASCII output?**
A: Wrap in `<pre>` tag and use CSS with phosphor glow effects.

---

## Next Steps

1. Review [ASCII_LIBRARIES_RESEARCH.md](./ASCII_LIBRARIES_RESEARCH.md) for detailed analysis
2. Check [TERMINAL_UI_MOCKUPS.md](./TERMINAL_UI_MOCKUPS.md) for visual examples
3. Install Tier 1 libraries (WebTUI, simple-ascii-chart, box utils)
4. Create first component (AsciiChart or BoxPanel)
5. Test with live data from dashboard

---

*Quick Reference Version: 1.0*
*Last Updated: 2025-11-08*
*See full research: [ASCII_LIBRARIES_RESEARCH.md](./ASCII_LIBRARIES_RESEARCH.md)*