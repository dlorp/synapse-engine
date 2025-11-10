# Historical Metrics Panel Integration Guide

**Date:** 2025-11-09
**Component:** HistoricalMetricsPanel
**Location:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/pages/MetricsPage/HistoricalMetricsPanel.tsx`

---

## Overview

The HistoricalMetricsPanel is a collapsible component that displays lifetime/historical metrics on the MetricsPage. It follows the NGE/NERV terminal aesthetic with phosphor orange (#ff9500) styling and smooth animations.

**Key Features:**
- Collapsible design (default: collapsed)
- Click header to toggle expand/collapse
- Smooth 0.3s animation with GPU acceleration
- Dense 2-column grid layout
- Color-coded error rates (green <1%, amber <5%, red >=5%)
- Handles loading, error, and no-data states
- Uses existing `useQueryMetrics()` and `useResourceMetrics()` hooks

---

## Step 1: Integration into MetricsPage

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/pages/MetricsPage/MetricsPage.tsx`

### Add Import Statement (Line 7)

```typescript
import { HistoricalMetricsPanel } from './HistoricalMetricsPanel';
```

### Add Component to Page Layout (After RoutingAnalyticsPanel, Line 49-50)

```typescript
export const MetricsPage: React.FC = () => {
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>S.Y.N.A.P.S.E. ENGINE - System Metrics</h1>

      {/* Panel 0: System Health Overview - Aggregate system performance trends */}
      <SystemHealthOverview />

      <Divider spacing="lg" />

      {/* Panel 1: Query Analytics - Real-time query rate and tier distribution */}
      <QueryAnalyticsPanel />

      <Divider spacing="lg" />

      {/* Panel 2: Tier Performance Comparison - Real-time sparklines for Q2/Q3/Q4 */}
      <TierComparisonPanel />

      <Divider spacing="lg" />

      {/* Panel 3: Resource Utilization - System resource monitoring (9 metrics) */}
      <ResourceUtilizationPanel />

      <Divider spacing="lg" />

      {/* Panel 4: Routing Analytics - Decision matrix and model availability */}
      <RoutingAnalyticsPanel />

      <Divider spacing="lg" />

      {/* Panel 5: Historical Metrics - Lifetime statistics (collapsible) */}
      <HistoricalMetricsPanel />
    </div>
  );
};
```

---

## Step 2: Update Exports (Optional)

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/pages/MetricsPage/index.ts`

Add export for HistoricalMetricsPanel:

```typescript
/**
 * Metrics Page components
 */

export { MetricsPage } from './MetricsPage';
export { SystemHealthOverview } from './SystemHealthOverview';
export { QueryAnalyticsPanel } from './QueryAnalyticsPanel';
export { TierComparisonPanel } from './TierComparisonPanel';
export { ResourceUtilizationPanel } from './ResourceUtilizationPanel';
export { RoutingAnalyticsPanel } from './RoutingAnalyticsPanel';
export { HistoricalMetricsPanel } from './HistoricalMetricsPanel';  // NEW
```

---

## Step 3: Testing the Component

### Manual Testing Checklist

1. **Start Docker environment:**
   ```bash
   docker-compose up -d
   docker-compose logs -f synapse_frontend
   ```

2. **Navigate to Metrics Page:**
   - Open browser: `http://localhost:5173/metrics`
   - Scroll to bottom to see HistoricalMetricsPanel

3. **Test Collapsible Functionality:**
   - [ ] Panel is collapsed by default (only header visible)
   - [ ] Click header to expand (should see metrics grid)
   - [ ] Click header again to collapse
   - [ ] Toggle icon rotates: ▼ (collapsed) → ▲ (expanded)
   - [ ] Animation is smooth (0.3s transition)

4. **Test States:**
   - [ ] **Loading State:** See spinner and "LOADING HISTORICAL DATA..." text
   - [ ] **No Data State:** If no queries processed, shows "NO HISTORICAL DATA AVAILABLE"
   - [ ] **Error State:** If API fails, shows red ✗ icon and error message
   - [ ] **Normal State:** Displays 10 metrics in 2-column grid

5. **Test Visual Styling:**
   - [ ] Phosphor orange (#ff9500) primary color
   - [ ] Black background (#000000)
   - [ ] Double-line border style
   - [ ] Hover effect on header (subtle glow increase)
   - [ ] Monospace font (JetBrains Mono)
   - [ ] Numbers formatted with commas (e.g., "1,234,567")

6. **Test Color-Coded Error Rate:**
   - [ ] Green (<1% error rate)
   - [ ] Amber (1-5% error rate)
   - [ ] Red (>=5% error rate)

7. **Test Responsiveness:**
   - [ ] Desktop (>768px): 2-column grid
   - [ ] Mobile (<768px): 1-column grid
   - [ ] Panel width fills container

---

## Step 4: Backend Integration (Future)

**Current State:** Component uses placeholder/mock data calculated from existing metrics hooks.

**TODO:** Backend integration required for accurate lifetime metrics.

### Expected Backend Endpoint

```
GET /api/metrics/historical
```

**Expected Response Schema:**

```json
{
  "totalRequests": 1234567,
  "totalErrors": 1234,
  "errorRate": 0.1,
  "avgLatencyMs": 125.5,
  "p95LatencyMs": 450.2,
  "p99LatencyMs": 1200.8,
  "uptimeSeconds": 3942000,
  "totalCacheHits": 987654,
  "totalCacheMisses": 123456,
  "cacheHitRate": 88.9
}
```

### Backend Implementation Notes

**File:** `backend/app/routers/metrics.py`

Add new endpoint:

```python
@router.get("/historical", response_model=HistoricalMetrics)
async def get_historical_metrics() -> HistoricalMetrics:
    """
    Get lifetime/historical metrics since system startup

    Returns:
        HistoricalMetrics: Aggregate system statistics
    """
    # TODO: Implement actual historical metrics collection
    # - Track process start time for uptime
    # - Persist total request/error counters
    # - Calculate P95/P99 latency percentiles from stored samples
    # - Track cache hit/miss counts in Redis

    pass
```

### Frontend Hook Update

Once backend endpoint is ready, create dedicated hook:

**File:** `frontend/src/hooks/useHistoricalMetrics.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

interface HistoricalMetricsResponse {
  totalRequests: number;
  totalErrors: number;
  errorRate: number;
  avgLatencyMs: number;
  p95LatencyMs: number;
  p99LatencyMs: number;
  uptimeSeconds: number;
  totalCacheHits: number;
  totalCacheMisses: number;
  cacheHitRate: number;
}

const fetchHistoricalMetrics = async (): Promise<HistoricalMetricsResponse> => {
  const response = await apiClient.get<HistoricalMetricsResponse>('/metrics/historical');
  return response.data;
};

export const useHistoricalMetrics = () => {
  return useQuery<HistoricalMetricsResponse, Error>({
    queryKey: ['metrics', 'historical'],
    queryFn: fetchHistoricalMetrics,
    refetchInterval: 5000,  // 5s updates (slower than real-time panels)
    staleTime: 3000,
  });
};
```

Then update HistoricalMetricsPanel.tsx to use this hook instead of calculating from existing data.

---

## Component API

### Props

```typescript
// No props - component is self-contained
<HistoricalMetricsPanel />
```

### State Management

- **Internal state:** `isExpanded` (boolean) - Controls collapse/expand
- **External data:** Uses `useQueryMetrics()` and `useResourceMetrics()` hooks
- **Calculated metrics:** Derived from hook data via `useMemo`

### CSS Classes

**File:** `HistoricalMetricsPanel.module.css`

- `.panel` - Main container
- `.header` - Clickable header with hover effects
- `.title` - Panel title text
- `.toggleIcon` - ▼/▲ icon with rotation animation
- `.content` - Collapsible content area
- `.content.collapsed` - Collapsed state (max-height: 0)
- `.content.expanded` - Expanded state (max-height: 1000px)
- `.sectionTitle` - "LIFETIME STATISTICS" heading
- `.metricsGrid` - 2-column grid container
- `.metricRow` - Individual metric row
- `.metricLabel` - Left side label
- `.metricValue` - Right side value (phosphor orange glow)

---

## Performance Considerations

1. **GPU Acceleration:**
   - `transform: translateZ(0)` on animated elements
   - `will-change: transform, max-height, opacity`

2. **Memoization:**
   - `useMemo` for historical metrics calculation
   - Prevents unnecessary recalculations on re-renders

3. **Transition Optimization:**
   - CSS `max-height` animation (0.3s ease)
   - Single property transitions for smooth 60fps

4. **Data Fetching:**
   - Reuses existing hooks (no additional API calls)
   - Future dedicated hook will use slower refresh rate (5s vs 1s)

---

## Accessibility

- **Keyboard Navigation:** Header is focusable with Enter/Space to toggle
- **ARIA Labels:** Spinner has `role="status"` and `aria-label="Loading"`
- **Focus Indicator:** Cyan outline on header focus (`:focus-visible`)
- **Screen Readers:** Semantic HTML with proper heading hierarchy
- **Reduced Motion:** Transitions disabled if `prefers-reduced-motion: reduce`

---

## Visual Design

### Collapsed State

```
╔═══════════════════════════════════════════════════════════════╗
║ HISTORICAL METRICS                                        [▼] ║
╚═══════════════════════════════════════════════════════════════╝
```

### Expanded State

```
╔═══════════════════════════════════════════════════════════════╗
║ HISTORICAL METRICS                                        [▲] ║
╠═══════════════════════════════════════════════════════════════╣
║ LIFETIME STATISTICS                                          ║
║ ┌─────────────────────────┬────────────────────────────────┐ ║
║ │ Total Requests:         │ 1,234,567                      │ ║
║ │ Total Errors:           │ 1,234                          │ ║
║ │ Error Rate:             │ 0.1%                           │ ║
║ │ Avg Latency (All-Time): │ 125ms                          │ ║
║ │ P95 Latency:            │ 450ms                          │ ║
║ │ P99 Latency:            │ 1,200ms                        │ ║
║ │ Total Uptime:           │ 45d 12h                        │ ║
║ │ Total Cache Hits:       │ 987,654                        │ ║
║ │ Total Cache Misses:     │ 123,456                        │ ║
║ │ Cache Hit Rate:         │ 88.9%                          │ ║
║ └─────────────────────────┴────────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Example Test Page

See `frontend/test_historical_metrics.html` for standalone testing.

---

## Troubleshooting

### Issue: Panel not visible
- **Check:** Import added to MetricsPage.tsx?
- **Check:** Component added to JSX after RoutingAnalyticsPanel?
- **Check:** Docker container rebuilt? (`docker-compose build --no-cache synapse_frontend`)

### Issue: No data showing
- **Check:** Are there any queries processed? (totalQueries > 0)
- **Check:** Backend API returning data? (check `/api/metrics/queries`)
- **Check:** Console errors? (F12 Developer Tools)

### Issue: Animation not smooth
- **Check:** GPU acceleration enabled? (inspect CSS `transform: translateZ(0)`)
- **Check:** Browser performance throttling? (Chrome DevTools Performance tab)
- **Check:** `prefers-reduced-motion` setting? (OS accessibility settings)

### Issue: Styling looks wrong
- **Check:** CSS module imported correctly?
- **Check:** Monospace font loading? (check Network tab for font files)
- **Check:** CSS conflicts with other components? (inspect computed styles)

---

## Files Created

1. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/pages/MetricsPage/HistoricalMetricsPanel.tsx` - Component implementation
2. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/pages/MetricsPage/HistoricalMetricsPanel.module.css` - Component styles
3. `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/HISTORICAL_METRICS_INTEGRATION.md` - This integration guide

---

## Next Steps

1. **Integrate into MetricsPage** (Step 1 above)
2. **Test collapsible functionality** (Step 3 above)
3. **Backend implementation** (Future work - Step 4 above)
4. **Create dedicated hook** (After backend ready)

---

**Status:** Ready for integration
**Estimated Integration Time:** 5 minutes
**Backend Work Required:** Yes (future)
