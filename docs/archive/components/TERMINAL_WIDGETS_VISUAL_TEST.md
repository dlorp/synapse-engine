# Terminal Widgets Visual Testing Guide

**Date:** 2025-11-08
**Components:** NetworkGraph, HeatMap, FigletBanner, SystemStatusPanel

This guide provides quick visual tests to verify the gorgeous phosphor glow aesthetic is working correctly for all 4 new terminal widgets.

---

## Quick Visual Checklist

For each component, verify:

- [ ] Phosphor orange (#ff9500) primary color visible
- [ ] Pulsating or static glow effect present
- [ ] Border glow on panels (orange pulse)
- [ ] Scan lines animating smoothly
- [ ] Dot matrix grid background visible
- [ ] 60fps smooth animations (no jank)
- [ ] Reduced motion disables animations
- [ ] High contrast mode increases visibility
- [ ] Mobile responsive sizing works

---

## 1. NetworkGraph Visual Test

**Test Page:** Create `/frontend/src/pages/NetworkGraphTestPage.tsx`

```typescript
import React from 'react';
import { NetworkGraph, NetworkNode, NetworkLink } from '@/components/terminal';

const testNodes: NetworkNode[] = [
  { id: 'q2-1', label: 'Q2 FAST 1', type: 'model' },
  { id: 'q2-2', label: 'Q2 FAST 2', type: 'model' },
  { id: 'q3', label: 'Q3 BALANCED', type: 'model' },
  { id: 'q4', label: 'Q4 POWERFUL', type: 'model' },
  { id: 'cgrag', label: 'CGRAG ENGINE', type: 'cgrag' },
  { id: 'query', label: 'USER QUERY', type: 'query' },
  { id: 'cache', label: 'REDIS CACHE', type: 'cache' },
];

const testLinks: NetworkLink[] = [
  { source: 'query', target: 'cgrag', active: true },
  { source: 'cgrag', target: 'q2-1', active: true },
  { source: 'cgrag', target: 'q3', active: false },
  { source: 'q2-1', target: 'cache', active: true },
  { source: 'cache', target: 'q2-2', active: false },
];

export const NetworkGraphTestPage: React.FC = () => {
  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <h1 style={{ color: '#ff9500', fontFamily: 'monospace' }}>
        NetworkGraph Visual Test
      </h1>

      <NetworkGraph
        nodes={testNodes}
        links={testLinks}
        width={800}
        height={600}
        onNodeClick={(node) => console.log('Clicked:', node.label)}
        onNodeHover={(node) => console.log('Hover:', node?.label)}
      />
    </div>
  );
};
```

**Expected Visuals:**
- Orange nodes (#ff9500) with pulsating glow
- Cyan active links (#00ffff) with glow
- Faded orange inactive links
- Nodes move organically (force simulation)
- Hover increases glow intensity
- Scan line moving top to bottom
- Click shows console log

**Verification:**
1. Open in browser
2. Observe nodes moving smoothly
3. Hover over nodes - label appears, glow intensifies
4. Click nodes - console logs click
5. Active links should be bright cyan
6. Inactive links should be dim orange
7. Scan line should animate smoothly

---

## 2. HeatMap Visual Test

**Test Page:** Create `/frontend/src/pages/HeatMapTestPage.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { HeatMap, HeatMapCell } from '@/components/terminal';

export const HeatMapTestPage: React.FC = () => {
  const [data, setData] = useState<HeatMapCell[]>([]);

  // Simulate live data updates
  useEffect(() => {
    const interval = setInterval(() => {
      const newData: HeatMapCell[] = [];
      for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 4; col++) {
          newData.push({
            row,
            col,
            value: Math.random(),
          });
        }
      }
      setData(newData);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <h1 style={{ color: '#ff9500', fontFamily: 'monospace' }}>
        HeatMap Visual Test
      </h1>

      <HeatMap
        data={data}
        rows={8}
        cols={4}
        rowLabels={['Q2-1', 'Q2-2', 'Q3-1', 'Q3-2', 'Q4-1', 'Q4-2', 'CGRAG', 'CACHE']}
        colLabels={['CPU', 'MEMORY', 'LATENCY', 'THROUGHPUT']}
        width={600}
        height={400}
        colorScale="orange-red"
        showLabels
        onCellClick={(row, col, value) =>
          console.log(`Cell [${row}, ${col}] = ${value.toFixed(2)}`)
        }
      />
    </div>
  );
};
```

**Expected Visuals:**
- Cells transition smoothly between colors
- High-intensity cells (>0.5) have visible glow
- Orange (#ff9500) → Red (#ff0000) gradient
- Row/column labels with phosphor glow
- Dense dot matrix grid in background
- Border glow on panel
- Slow scan line animation

**Verification:**
1. Open in browser
2. Observe cells changing color every 2 seconds
3. Smooth transitions (no sudden jumps)
4. High-value cells glow brightly
5. Labels visible with orange glow
6. Click cell - console logs row, col, value
7. Hover over cells - no visual glitch
8. Dense grid pattern visible in background

---

## 3. FigletBanner Visual Test

**Test Page:** Create `/frontend/src/pages/FigletBannerTestPage.tsx`

```typescript
import React, { useState } from 'react';
import { FigletBanner } from '@/components/terminal';

const presets = [
  'S.Y.N.A.P.S.E. ENGINE',
  'SYNAPSE ENGINE',
  'NEURAL SUBSTRATE',
  'SYSTEM ONLINE',
  'READY',
];

export const FigletBannerTestPage: React.FC = () => {
  const [textIndex, setTextIndex] = useState(0);

  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <h1 style={{ color: '#ff9500', fontFamily: 'monospace' }}>
        FigletBanner Visual Test
      </h1>

      <button
        onClick={() => setTextIndex((textIndex + 1) % presets.length)}
        style={{
          padding: '10px 20px',
          background: '#ff9500',
          color: '#000',
          border: 'none',
          fontFamily: 'monospace',
          cursor: 'pointer',
          marginBottom: '20px',
        }}
      >
        NEXT BANNER
      </button>

      <FigletBanner
        text={presets[textIndex]}
        variant="standard"
        enableScanLines
        enablePulse
      />

      <div style={{ marginTop: '40px' }}>
        <h2 style={{ color: '#ff9500', fontFamily: 'monospace' }}>
          Without Pulse/Scan Lines
        </h2>
        <FigletBanner
          text={presets[textIndex]}
          variant="standard"
          enableScanLines={false}
          enablePulse={false}
        />
      </div>

      <div style={{ marginTop: '40px' }}>
        <h2 style={{ color: '#ff9500', fontFamily: 'monospace' }}>
          Custom Text (Fallback)
        </h2>
        <FigletBanner
          text="CUSTOM TEXT"
          variant="standard"
          enableScanLines
          enablePulse
        />
      </div>
    </div>
  );
};
```

**Expected Visuals:**
- Large ASCII art in phosphor orange
- Text glows and pulses (2s cycle)
- Fast scan line moving vertically
- Box-style fallback for custom text
- Responsive sizing on mobile
- Center-aligned

**Verification:**
1. Open in browser
2. ASCII art renders correctly
3. Text has pulsating glow effect
4. Scan line animates across text
5. Click "NEXT BANNER" - banner changes
6. Scroll to second banner - no pulse/scan lines
7. Scroll to third banner - simple box style
8. Resize window - font size adjusts

---

## 4. SystemStatusPanel Visual Test

**Test Page:** Create `/frontend/src/pages/SystemStatusPanelTestPage.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { SystemStatusPanel, SystemMetrics } from '@/components/terminal';

export const SystemStatusPanelTestPage: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpuUsage: 45.2,
    memoryUsedMb: 8192,
    memoryTotalMb: 16384,
    activeModels: { total: 3, q2: 1, q3: 1, q4: 1 },
    queryQueue: 2,
    cgragIndexSize: 15000,
    cacheHitRate: 0.82,
    avgQueryLatencyMs: 1250,
    uptimeSeconds: 86400,
    activeQueries: 1,
    totalQueries: 1523,
    errorRate: 0.02,
  });

  // Simulate live metric updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics((prev) => ({
        ...prev,
        cpuUsage: 20 + Math.random() * 60,
        memoryUsedMb: 6000 + Math.random() * 4000,
        queryQueue: Math.floor(Math.random() * 5),
        cacheHitRate: 0.6 + Math.random() * 0.3,
        avgQueryLatencyMs: 500 + Math.random() * 2000,
        uptimeSeconds: prev.uptimeSeconds + 1,
        activeQueries: Math.floor(Math.random() * 3),
        totalQueries: prev.totalQueries + Math.floor(Math.random() * 2),
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '20px', background: '#000' }}>
      <h1 style={{ color: '#ff9500', fontFamily: 'monospace' }}>
        SystemStatusPanel Visual Test
      </h1>

      <div style={{ maxWidth: '800px' }}>
        <SystemStatusPanel
          metrics={metrics}
          title="SYSTEM STATUS"
        />
      </div>

      <div style={{ maxWidth: '400px', marginTop: '40px' }}>
        <h2 style={{ color: '#ff9500', fontFamily: 'monospace' }}>
          Compact Mode
        </h2>
        <SystemStatusPanel
          metrics={metrics}
          title="COMPACT STATUS"
          compact
        />
      </div>
    </div>
  );
};
```

**Expected Visuals:**
- 2-column dense grid of metrics
- All values with phosphor-glow-static-orange
- CPU/Memory/Cache/Latency color-coded by threshold
- "PENDING" pulse on query queue when > 0
- Uptime formatted as days/hours/minutes
- Hover effect on metric rows (border color change)
- Dense dot matrix grid background
- Border glow on panel
- Slow scan line animation

**Verification:**
1. Open in browser
2. Metrics update every second
3. Values change smoothly (no flicker)
4. Color changes based on thresholds:
   - CPU > 70% → yellow, > 90% → red
   - Memory > 70% → yellow, > 90% → red
   - Cache < 50% → red, < 70% → yellow
   - Latency > 2000ms → yellow, > 5000ms → red
5. Query queue shows "PENDING" when > 0 with pulse
6. Uptime increments and formats correctly
7. Hover over rows - border changes color
8. Compact mode shows single column

---

## Browser Testing

Test in all supported browsers:

- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari

**Check:**
- Canvas rendering quality
- CSS animation smoothness
- requestAnimationFrame performance
- Reduced motion media query
- High contrast mode

---

## Performance Testing

Open DevTools Performance panel:

1. **FPS Monitoring**
   - Open Performance monitor
   - Watch FPS while components animate
   - Should maintain 60fps consistently
   - No drops below 50fps

2. **Memory Usage**
   - Check memory consumption
   - NetworkGraph: ~10-20MB
   - HeatMap: ~5-10MB
   - Should not increase over time (no leaks)

3. **Animation Jank**
   - No stuttering during:
     - NetworkGraph node movement
     - HeatMap value transitions
     - Scan line animations
     - Phosphor glow pulsing

---

## Accessibility Testing

1. **Screen Reader**
   - Enable screen reader (NVDA/JAWS/VoiceOver)
   - Verify ARIA labels announced
   - Canvas elements describe content

2. **Keyboard Navigation**
   - Tab through components
   - Focus indicators visible
   - Interactive elements focusable

3. **Reduced Motion**
   - Enable in OS settings (macOS: System Preferences → Accessibility → Display → Reduce Motion)
   - All animations should stop
   - Static glow remains
   - No pulsing, no scan lines

4. **High Contrast**
   - Enable high contrast mode
   - Text remains readable
   - Borders more visible
   - Colors meet WCAG AA

---

## Responsive Testing

Resize browser to test breakpoints:

**Desktop (1920px)**
- [ ] NetworkGraph: Full size 800x600
- [ ] HeatMap: Full size 600x400
- [ ] FigletBanner: 8px font size
- [ ] SystemStatusPanel: 2-column grid

**Tablet (768px)**
- [ ] NetworkGraph: Scaled appropriately
- [ ] HeatMap: Scaled appropriately
- [ ] FigletBanner: 6px font size
- [ ] SystemStatusPanel: 1-column grid

**Mobile (480px)**
- [ ] NetworkGraph: Touch-friendly (if applicable)
- [ ] HeatMap: Labels readable
- [ ] FigletBanner: 4px font size
- [ ] SystemStatusPanel: 1-column grid, compact

---

## Docker Build Test

Build and test in Docker to verify production behavior:

```bash
# Build frontend
docker-compose build --no-cache synapse_frontend

# Start services
docker-compose up -d

# View logs
docker-compose logs -f synapse_frontend

# Test in browser
open http://localhost:5173
```

**Verify:**
- [ ] All components render in Docker
- [ ] No console errors
- [ ] Animations work correctly
- [ ] No missing CSS classes
- [ ] Performance remains 60fps

---

## Known Issues to Check

1. **Canvas Blur on Retina/HiDPI**
   - Verify canvas looks crisp on high-DPI screens
   - Check `image-rendering: crisp-edges` works

2. **Animation Performance on Low-End Devices**
   - Test on older hardware
   - Verify graceful degradation

3. **Memory Leaks**
   - Leave page open for 5+ minutes
   - Check memory doesn't grow unbounded
   - Verify requestAnimationFrame cleanup

4. **Z-Index Conflicts**
   - Check scan lines don't overlap incorrectly
   - Verify panels layer correctly

---

## Success Criteria

All components pass if:

✅ **Visual:** Phosphor glow visible and pulsating correctly
✅ **Performance:** 60fps maintained during animations
✅ **Accessibility:** ARIA labels, reduced motion, high contrast work
✅ **Responsive:** Mobile/tablet/desktop layouts correct
✅ **Interactive:** Click/hover handlers work
✅ **Production:** Docker build works, no errors

---

## Next Steps After Visual Testing

1. Create Storybook stories for each component
2. Add visual regression tests (Chromatic/Percy)
3. Profile performance in production
4. Document edge cases and limitations
5. Create component gallery page

---

**Visual testing complete when all checkboxes are marked and no issues found.**
