# Performance Testing Guide - ResourceUtilizationPanel

**Component:** ResourceUtilizationPanel
**Target:** <16ms render time (60fps)
**Update Frequency:** 1Hz (1000ms)

---

## Testing Methodology

### 1. Automated Performance Testing

#### Puppeteer Benchmark Script
**Location:** `/scripts/test-resource-panel-performance.js`

**Measures:**
- Frame rate (target: 60fps)
- Render times (target: <16ms avg)
- P50/P95/P99 percentiles
- Memory usage (heap size)

**Usage:**
```bash
# Prerequisites
docker-compose up -d

# Run test (30-second duration)
node scripts/test-resource-panel-performance.js
```

**Expected Output:**
```
📊 Performance Results:

Frame Rate:
  FPS: 59.87 fps
  Target: 60 fps
  Status: ✅ PASS

Render Times:
  Average: 8.45 ms
  Maximum: 14.23 ms
  Target: <16 ms
  Status: ✅ PASS

Percentiles:
  P50: 7.89 ms
  P95: 12.34 ms
  P99: 14.01 ms

Memory Usage:
  JS Heap: 12.45 MB
  JS Heap Limit: 48.00 MB

═══════════════════════════════════════
Overall: ✅ PASS
═══════════════════════════════════════
```

**Thresholds:**
- FPS ≥ 55 (target 60)
- Avg render time < 16ms
- P99 render time < 20ms
- No memory leaks (stable heap over 30s)

---

### 2. Browser DevTools Performance Testing

#### Chrome DevTools Profiler
1. Open `http://localhost:5173/metrics`
2. Open Chrome DevTools (F12)
3. Switch to Performance tab
4. Click Record
5. Wait 10 seconds (10 metric updates)
6. Stop recording

**Analysis:**
- **Main thread:** Should show minimal blocking
- **Frame rate:** Should be stable at 60fps
- **Scripting time:** <5ms per frame
- **Rendering time:** <10ms per frame
- **Painting time:** <1ms per frame

**Red Flags:**
- Long tasks (>50ms) blocking main thread
- Frame drops (red bars)
- Excessive layout recalculations
- Large paint areas

#### React DevTools Profiler
1. Open `http://localhost:5173/metrics`
2. Open React DevTools
3. Switch to Profiler tab
4. Click Record
5. Wait for several updates
6. Stop recording

**Analysis:**
- ResourceUtilizationPanel should render quickly (<10ms)
- ResourceMetricCard should NOT re-render if props unchanged (React.memo working)
- Flamegraph should show minimal nesting
- No red/orange bars (slow components)

---

### 3. Visual Testing

#### Test Page
**URL:** `http://localhost:5173/resource-panel-test`

**Manual Checks:**

✅ **Layout**
- 3×3 grid on desktop (>1024px)
- 2 columns on tablet (640-1024px)
- 1 column on mobile (<640px)
- Consistent spacing (16px gaps)

✅ **Metrics Display**
- All 9 metrics visible
- Values display correctly (no NaN/undefined)
- Units display (GB, %, MB/s)
- Secondary text visible

✅ **Progress Bars**
- Horizontal bars display correctly
- Width matches percentage (visual check)
- Smooth transitions (no jank)
- Glows visible on bars

✅ **Color Coding**
- Healthy state: Green borders/bars (0-70%)
- Warning state: Amber borders/bars (70-90%)
- Critical state: Red borders/bars with pulse (>90%)

✅ **Animations**
- Phosphor glow on panels
- Progress bar transitions (300ms)
- Critical state pulse (2s cycle)
- No flicker or jank

✅ **State Transitions**
- Toggle between healthy/warning/critical
- Smooth color transitions
- No layout shift
- No console errors

---

### 4. Memory Leak Testing

#### Long-Running Test (1 hour)
```javascript
// Run in browser console on /metrics page
const initialMemory = performance.memory.usedJSHeapSize;
const samples = [];

setInterval(() => {
  samples.push(performance.memory.usedJSHeapSize);
  console.log(`Heap: ${(performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);

  if (samples.length === 360) { // 1 hour at 10s intervals
    const finalMemory = performance.memory.usedJSHeapSize;
    const growth = finalMemory - initialMemory;
    console.log(`Memory growth: ${(growth / 1024 / 1024).toFixed(2)} MB`);

    if (growth < 5 * 1024 * 1024) { // <5MB growth acceptable
      console.log('✅ PASS: No memory leak detected');
    } else {
      console.log('❌ FAIL: Possible memory leak');
    }
  }
}, 10000); // Sample every 10s
```

**Expected Result:**
- Initial heap: ~10-15 MB
- Final heap: <20 MB (after 1 hour)
- Growth: <5 MB (acceptable for cache buildup)

**Red Flags:**
- Continuous upward trend (linear growth)
- Heap size > 50 MB
- Growth > 10 MB/hour

---

### 5. Unit Testing

#### Component Tests
**Location:** `/frontend/src/components/metrics/ResourceMetricCard.test.tsx`

**Run:**
```bash
npm test ResourceMetricCard.test.tsx
```

**Tests:**
1. ✅ Basic rendering (label, value, unit)
2. ✅ Progress bar rendering (when percent provided)
3. ✅ Secondary text display
4. ✅ Status class application (ok/warning/critical)
5. ✅ Progress bar clamping (0-100%)
6. ✅ Memoization verification (React.memo working)

**Coverage Target:** >90%

---

### 6. Network Performance Testing

#### TanStack Query Behavior
1. Open browser DevTools Network tab
2. Navigate to `/metrics`
3. Observe API calls

**Expected:**
- Initial request: `GET /api/metrics/resources` (on mount)
- Subsequent requests: Every 1000ms (1Hz polling)
- Request method: GET
- Status code: 200 OK (when backend ready)
- Response size: <5KB
- Response time: <100ms

**Red Flags:**
- Missing CORS headers
- Request failures (4xx/5xx)
- Response time >200ms
- Duplicate requests (polling issues)

#### Query Caching Behavior
```javascript
// Check TanStack Query cache in React DevTools
// Query key: ['metrics', 'resources']
// Stale time: 500ms
// Refetch interval: 1000ms
```

---

### 7. Responsive Design Testing

#### Breakpoint Testing
Test at multiple viewport widths:

**Desktop (1920×1080)**
- ✅ 3 columns (3×3 grid)
- ✅ Cards: ~550px wide
- ✅ Padding: 12px per card
- ✅ Gaps: 16px

**Laptop (1366×768)**
- ✅ 3 columns maintained
- ✅ Cards resize proportionally
- ✅ No horizontal scroll

**Tablet (768×1024)**
- ✅ 2 columns (5 rows)
- ✅ Cards: ~350px wide
- ✅ Gaps: 12px

**Mobile (375×667)**
- ✅ 1 column (9 rows)
- ✅ Cards: 100% width
- ✅ Min-height: 100px
- ✅ Padding: 10px per card

**Tools:**
- Chrome DevTools Device Toolbar
- Responsive Design Mode (Firefox)
- Real devices (iOS/Android)

---

### 8. Accessibility Testing

#### ARIA Attributes
```bash
# Check progress bars have proper ARIA
- role="progressbar"
- aria-valuenow="{percent}"
- aria-valuemin="0"
- aria-valuemax="100"
```

#### Keyboard Navigation
- ✅ Tab through cards (logical order)
- ✅ Focus visible (outline)
- ✅ Screen reader announces values

#### Color Contrast
- ✅ Text: #ff9500 on #000000 (high contrast)
- ✅ Status colors: Green/Amber/Red (distinguishable)
- ✅ WCAG AA compliance

---

## Performance Optimization Checklist

### React Optimizations
- [x] React.memo on ResourceMetricCard
- [x] useMemo for formatted metrics
- [x] useMemo for progress width calculation
- [x] useMemo for class names
- [x] TanStack Query automatic batching

### CSS Optimizations
- [x] GPU-accelerated properties (transform, opacity)
- [x] CSS Grid with gap (not margins)
- [x] will-change on animated elements
- [x] Avoid layout-triggering properties

### Polling Optimizations
- [x] 1Hz refresh rate (not too fast)
- [x] staleTime: 500ms (prevent unnecessary refetches)
- [x] Exponential backoff on retry
- [x] Abort previous requests (TanStack Query default)

### Bundle Optimizations
- [x] Tree-shaking (Vite default)
- [x] Code splitting (dynamic imports)
- [x] Minification (production build)
- [x] Gzip compression (nginx)

---

## Common Performance Issues

### Issue: Low FPS (<55fps)
**Possible Causes:**
- Too many re-renders (check React DevTools Profiler)
- Expensive calculations not memoized
- CSS animations triggering layout

**Solutions:**
1. Verify React.memo is working
2. Add useMemo to expensive calculations
3. Use GPU-accelerated CSS properties
4. Reduce polling frequency to 2Hz (2000ms)

### Issue: High render times (>16ms)
**Possible Causes:**
- Large component tree
- Synchronous formatting operations
- Heavy CSS recalculations

**Solutions:**
1. Memoize formatted metrics at panel level
2. Use CSS Grid (not flexbox) for layout
3. Avoid inline styles (use CSS modules)

### Issue: Memory leaks
**Possible Causes:**
- Event listeners not cleaned up
- TanStack Query not unmounting properly
- Closures holding references

**Solutions:**
1. Verify useEffect cleanup functions
2. Check TanStack Query devtools for stale queries
3. Use Chrome Memory Profiler to find leaks

### Issue: Slow API responses
**Possible Causes:**
- Backend metrics collection is slow
- Network latency
- Large response payload

**Solutions:**
1. Optimize backend metrics collection (cache psutil calls)
2. Reduce response payload size (remove unnecessary fields)
3. Enable gzip compression on backend

---

## Performance Targets Summary

| Metric | Target | Threshold | Status |
|--------|--------|-----------|--------|
| Frame Rate | 60fps | ≥55fps | ✅ |
| Avg Render Time | <16ms | <20ms | ✅ |
| P99 Render Time | <16ms | <25ms | ✅ |
| Memory Growth | <5MB/hr | <10MB/hr | ✅ |
| Bundle Size | <50KB | <75KB | ✅ |
| API Latency | <100ms | <200ms | ⏳ Backend |

---

## Continuous Monitoring

### Production Metrics
Add performance monitoring to production:

```javascript
// Track render times
useEffect(() => {
  const start = performance.now();
  return () => {
    const duration = performance.now() - start;
    if (duration > 16) {
      console.warn(`Slow render: ${duration.toFixed(2)}ms`);
    }
  };
}, [formattedMetrics]);
```

### Real User Monitoring (RUM)
Consider adding RUM tools:
- Sentry (error tracking + performance)
- LogRocket (session replay)
- Datadog (real-time monitoring)

---

## References

- [Web Performance API](https://developer.mozilla.org/en-US/docs/Web/API/Performance)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [React Profiler API](https://react.dev/reference/react/Profiler)
- [TanStack Query DevTools](https://tanstack.com/query/latest/docs/react/devtools)
- [RESOURCE_UTILIZATION_PANEL.md](./components/RESOURCE_UTILIZATION_PANEL.md)

---

**Last Updated:** 2025-11-09
**Component Version:** v1.0
**Test Coverage:** 90%+
