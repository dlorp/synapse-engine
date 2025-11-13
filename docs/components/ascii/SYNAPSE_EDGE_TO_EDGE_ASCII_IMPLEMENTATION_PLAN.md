# S.Y.N.A.P.S.E. ENGINE - Edge-to-Edge ASCII Borders Implementation Plan

**Date:** 2025-11-10
**Status:** Implementation Plan - Ready for Execution
**Estimated Time:** 4-6 hours
**Priority:** HIGH (User Interface Consistency)

---

## Executive Summary

### Vision Statement
Achieve consistent edge-to-edge ASCII borders across ALL S.Y.N.A.P.S.E. ENGINE pages to match the reference AdminPage implementation. ASCII section headers (`─ TITLE ─────────`) should extend fully to viewport edges with no gaps, creating the distinctive NERV-inspired terminal aesthetic that defines the project's visual identity.

### Key Changes
1. **Fix Panel.module.css** - Change content padding from all-sides to horizontal-only (HIGHEST IMPACT)
2. **Fix SettingsPage** - Remove max-width constraint to allow edge-to-edge rendering
3. **Standardize HomePage** - Replace all custom headers with AsciiSectionHeader component
4. **Standardize MetricsPage** - Verify all panels use proper patterns (already correct)
5. **Fix ModelManagementPage** - Replace ModelSettings inline ASCII with AsciiSectionHeader

### Current Problems vs. New Behavior

**BEFORE:**
- SettingsPage: 1600px max-width with centered content, ASCII borders don't reach edges
- Panel component: Padding on all sides pushes ASCII headers inward
- HomePage: Components use Panel titles instead of AsciiSectionHeader
- ModelSettings: Inline ASCII generation with padLine() function (inconsistent width)

**AFTER:**
- ALL pages: ASCII borders extend edge-to-edge at 100% viewport width
- Panel component: Horizontal padding only, vertical edges untouched
- HomePage: SystemStatusPanelEnhanced, OrchestratorStatusPanel, LiveEventFeed use AsciiSectionHeader
- ModelSettings: Standard AsciiSectionHeader component (consistent 150-char dash repeat)
- Consistent visual hierarchy across entire application

### Expected Outcomes
- Professional terminal aesthetic with edge-to-edge ASCII borders on ALL pages
- Visual consistency matching AdminPage reference implementation
- Improved perceived quality and attention to detail
- No regressions in existing functionality
- Responsive design maintained at all viewport widths (320px → 4K)

---

## Phase 1: Fix Core Panel Component (HIGHEST IMPACT)

### Overview
The Panel component is used throughout the application. Fixing its padding pattern will automatically improve ALL pages using it. This is the **single most impactful change** in this plan.

### File: `/frontend/src/components/terminal/Panel/Panel.module.css`

**Lines to modify:** 53-57

**Current code:**
```css
.content {
  padding: var(--space-md);
  flex: 1;
  overflow: visible; /* Allow tooltips to render outside panel bounds */
}
```

**New code:**
```css
.content {
  padding: 0 var(--space-md); /* Horizontal padding only - allows vertical elements (ASCII headers) to extend edge-to-edge */
  flex: 1;
  overflow: visible; /* Allow tooltips to render outside panel bounds */
}
```

**Explanation:**
- **BEFORE:** `padding: var(--space-md)` applies 16px padding on ALL sides (top, right, bottom, left)
- **AFTER:** `padding: 0 var(--space-md)` applies 0px padding on top/bottom, 16px on left/right
- This allows AsciiSectionHeader components inside Panel to extend fully to left/right edges
- Content still has comfortable horizontal margins (16px) for readability
- Vertical spacing is controlled by individual components (gaps, margins)

**Expected result:**
ALL pages using Panel with AsciiSectionHeader will automatically show edge-to-edge borders:
- AdminPage (already working, will stay working)
- HomePage (SystemStatusPanelEnhanced uses DotMatrixPanel which wraps Panel)
- MetricsPage (all 6 panels use Panel)
- Any other components using Panel with ASCII headers

**Testing:**
1. Navigate to AdminPage → ASCII headers should still extend edge-to-edge (no regression)
2. Navigate to HomePage → SystemStatusPanelEnhanced should show edge-to-edge borders
3. Navigate to MetricsPage → All panels should show edge-to-edge borders
4. Check spacing: Content should have 16px horizontal margins, no awkward gaps

---

## Phase 2: Fix SettingsPage Edge-to-Edge

### Overview
SettingsPage has a hardcoded 1600px max-width with centered content. This prevents ASCII sections from extending to viewport edges on wider screens (>1600px).

### File: `/frontend/src/pages/SettingsPage/SettingsPage.module.css`

**Lines to modify:** 7-14

**Current code:**
```css
.page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: fade-in var(--transition-base);
  max-width: 1600px;
  margin: 0 auto;
  padding: 24px;
}
```

**New code:**
```css
.page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: fade-in var(--transition-base);
  /* Full width - no max-width to allow ASCII borders to extend edge-to-edge */
  width: 100%;
  margin: 0;
  padding: 0; /* Edge-to-edge pattern: Child components handle their own padding */
}
```

**Explanation:**
- **REMOVED:** `max-width: 1600px` and `margin: 0 auto` (centering with width constraint)
- **REMOVED:** `padding: 24px` (page-level padding pushes ASCII borders inward)
- **ADDED:** `width: 100%` to ensure full viewport width
- **ADDED:** `margin: 0` to remove any centering
- **ADDED:** `padding: 0` with comment explaining child components handle spacing
- This matches HomePage and AdminPage patterns (both use `padding: 0`)

**Expected result:**
- SettingsPage ASCII section headers (`─ SYSTEM CONFIGURATION`, `─ PORT CONFIGURATION`, etc.) extend fully to left/right viewport edges
- Content inside sections still has proper spacing (handled by `.asciiBody` class which has `padding: 24px`)
- No visual regressions in field layouts, grids, or buttons

**Testing:**
1. Navigate to Settings → ASCII section headers extend edge-to-edge
2. Check at 1920px width → No centered box, borders reach edges
3. Check at 2560px width → Still edge-to-edge (no max-width constraint)
4. Check at 768px width → Responsive layout still works, no overflow
5. Verify form fields have proper spacing (asciiBody padding provides this)

---

## Phase 3: Standardize HomePage Headers (PRIORITY 1)

### Overview
HomePage currently has 3 components that don't use AsciiSectionHeader:
1. **SystemStatusPanelEnhanced** - Uses DotMatrixPanel with custom title
2. **OrchestratorStatusPanel** - Uses Panel with custom title
3. **LiveEventFeed** - Uses Panel with custom title

We need to replace Panel titles with AsciiSectionHeader to achieve edge-to-edge borders.

---

### 3A. SystemStatusPanelEnhanced - Add AsciiSectionHeader

**File:** `/frontend/src/components/terminal/SystemStatusPanel/SystemStatusPanelEnhanced.tsx`

**Lines to modify:** 16, 19, 138-148, 205-215

**Current code (lines 138-148):**
```tsx
return (
  <DotMatrixPanel
    title={title}
    enableGrid
    gridDensity="dense"
    enableScanLines
    scanLineSpeed="slow"
    enableBorderGlow
    glowColor="orange"
    className={className}
  >
```

**New code (lines 138-150):**
```tsx
return (
  <>
    <AsciiSectionHeader title={title} />
    <DotMatrixPanel
      enableGrid
      gridDensity="dense"
      enableScanLines
      scanLineSpeed="slow"
      enableBorderGlow
      glowColor="orange"
      className={className}
    >
```

**Current code (lines 205-215):**
```tsx
return (
  <DotMatrixPanel
    title={title}
    enableGrid
    gridDensity="dense"
    enableScanLines
    scanLineSpeed="slow"
    enableBorderGlow
    glowColor="orange"
    className={className}
  >
```

**New code (lines 205-217):**
```tsx
return (
  <>
    <AsciiSectionHeader title={title} />
    <DotMatrixPanel
      enableGrid
      gridDensity="dense"
      enableScanLines
      scanLineSpeed="slow"
      enableBorderGlow
      glowColor="orange"
      className={className}
    >
```

**Add closing tag at end of both return statements:**
```tsx
    </DotMatrixPanel>
  </>
);
```

**Import addition (line 19):**
```tsx
import { DotMatrixPanel } from '../DotMatrixPanel';
import { StatusIndicator } from '../StatusIndicator';
import { AsciiSectionHeader } from '../AsciiSectionHeader'; // ADD THIS LINE
import { ModelStatusResponse } from '@/types/models';
```

**Explanation:**
- Wrap DotMatrixPanel return statements with `<> ... </>` (React Fragment)
- Add `<AsciiSectionHeader title={title} />` BEFORE DotMatrixPanel
- Remove `title={title}` prop from DotMatrixPanel (AsciiSectionHeader handles title now)
- This creates edge-to-edge ASCII header above the panel content
- DotMatrixPanel still provides grid background, scan lines, and border glow

**Expected result:**
- System Status section shows `─ SYSTEM STATUS ──────────` extending edge-to-edge
- DotMatrixPanel content below header has proper spacing
- Quick Actions footer remains at bottom of panel
- No visual regressions in metrics display or button layout

---

### 3B. OrchestratorStatusPanel - Add AsciiSectionHeader

**File:** `/frontend/src/components/dashboard/OrchestratorStatusPanel/OrchestratorStatusPanel.tsx`

**Lines to modify:** 18, 68-73, 77-84, 88-93, 139-147

**Current code (lines 68-73):**
```tsx
if (isLoading) {
  return (
    <Panel title="NEURAL SUBSTRATE ORCHESTRATOR">
      <div className={styles.loading}>Initializing orchestrator telemetry...</div>
    </Panel>
  );
}
```

**New code:**
```tsx
if (isLoading) {
  return (
    <>
      <AsciiSectionHeader title="NEURAL SUBSTRATE ORCHESTRATOR" />
      <Panel>
        <div className={styles.loading}>Initializing orchestrator telemetry...</div>
      </Panel>
    </>
  );
}
```

**Current code (lines 77-84):**
```tsx
if (error) {
  return (
    <Panel title="NEURAL SUBSTRATE ORCHESTRATOR" variant="error">
      <div className={styles.error}>
        ORCHESTRATOR TELEMETRY OFFLINE
        <div className={styles.errorDetail}>{error.message}</div>
      </div>
    </Panel>
  );
}
```

**New code:**
```tsx
if (error) {
  return (
    <>
      <AsciiSectionHeader title="NEURAL SUBSTRATE ORCHESTRATOR" />
      <Panel variant="error">
        <div className={styles.error}>
          ORCHESTRATOR TELEMETRY OFFLINE
          <div className={styles.errorDetail}>{error.message}</div>
        </div>
      </Panel>
    </>
  );
}
```

**Current code (lines 88-93):**
```tsx
if (!status) {
  return (
    <Panel title="NEURAL SUBSTRATE ORCHESTRATOR">
      <div className={styles.noData}>No orchestrator data available</div>
    </Panel>
  );
}
```

**New code:**
```tsx
if (!status) {
  return (
    <>
      <AsciiSectionHeader title="NEURAL SUBSTRATE ORCHESTRATOR" />
      <Panel>
        <div className={styles.noData}>No orchestrator data available</div>
      </Panel>
    </>
  );
}
```

**Current code (lines 104-136):**
```tsx
if (!lastDecision || status.recentDecisions.length === 0) {
  return (
    <Panel
      title="NEURAL SUBSTRATE ORCHESTRATOR"
      titleRight={
        <span className={styles.statusIdle}>
          STATUS: IDLE
        </span>
      }
    >
```

**New code:**
```tsx
if (!lastDecision || status.recentDecisions.length === 0) {
  return (
    <>
      <AsciiSectionHeader title="NEURAL SUBSTRATE ORCHESTRATOR" />
      <Panel
        titleRight={
          <span className={styles.statusIdle}>
            STATUS: IDLE
          </span>
        }
      >
```

**Current code (lines 139-147):**
```tsx
return (
  <Panel
    title="NEURAL SUBSTRATE ORCHESTRATOR"
    titleRight={
      <span className={statusClass}>
        STATUS: {routingStatus}
      </span>
    }
  >
```

**New code:**
```tsx
return (
  <>
    <AsciiSectionHeader title="NEURAL SUBSTRATE ORCHESTRATOR" />
    <Panel
      titleRight={
        <span className={statusClass}>
          STATUS: {routingStatus}
        </span>
      }
    >
```

**Add closing tag at end of return statements (lines ~135, ~200):**
```tsx
    </Panel>
  </>
);
```

**Import addition (line 18):**
```tsx
import React from 'react';
import { Panel } from '@/components/terminal/Panel';
import { AsciiSectionHeader } from '@/components/terminal/AsciiSectionHeader'; // ADD THIS LINE
import { useOrchestratorStatus } from '@/hooks/useOrchestratorStatus';
```

**Explanation:**
- Add AsciiSectionHeader before EVERY Panel return statement
- Remove `title="NEURAL SUBSTRATE ORCHESTRATOR"` from ALL Panel tags
- Keep `titleRight` prop (shows STATUS: IDLE / ROUTING in panel header bar)
- Wrap each return with React Fragment `<> ... </>`
- This creates edge-to-edge ASCII header while preserving status indicator

**Expected result:**
- `─ NEURAL SUBSTRATE ORCHESTRATOR ──────────` extends edge-to-edge
- Panel below shows status indicator in top-right corner
- Empty state (awaiting query) shows properly formatted
- Active state (routing visualization) shows properly formatted

---

### 3C. LiveEventFeed - Add AsciiSectionHeader

**File:** `/frontend/src/components/dashboard/LiveEventFeed/LiveEventFeed.tsx`

**Lines to modify:** 2, 118-124

**Current code (lines 118-124):**
```tsx
return (
  <Panel
    title="SYSTEM EVENT STREAM"
    titleRight={getConnectionStatus()}
    variant="default"
    className={styles.panel}
  >
```

**New code:**
```tsx
return (
  <>
    <AsciiSectionHeader title="SYSTEM EVENT STREAM" />
    <Panel
      titleRight={getConnectionStatus()}
      variant="default"
      className={styles.panel}
    >
```

**Add closing tag at end (line ~155):**
```tsx
    </Panel>
  </>
);
```

**Import addition (line 2):**
```tsx
import React, { useEffect, useRef } from 'react';
import { Panel } from '../../terminal/Panel/Panel';
import { AsciiSectionHeader } from '../../terminal/AsciiSectionHeader/AsciiSectionHeader'; // ADD THIS LINE
import { useSystemEventsContext } from '../../../contexts/SystemEventsContext';
```

**Explanation:**
- Add AsciiSectionHeader before Panel
- Remove `title="SYSTEM EVENT STREAM"` from Panel
- Keep `titleRight={getConnectionStatus()}` (shows LIVE / DISCONNECTED status)
- Wrap return with React Fragment
- This creates edge-to-edge ASCII header while preserving connection status

**Expected result:**
- `─ SYSTEM EVENT STREAM ──────────` extends edge-to-edge
- Panel below shows connection status (LIVE / DISCONNECTED) in top-right
- Event list scrolling works correctly
- Reconnect button appears when disconnected

---

### Phase 3 Testing Checklist

After completing all Phase 3 changes, verify:

- [ ] HomePage loads without errors
- [ ] SystemStatusPanelEnhanced shows edge-to-edge `─ SYSTEM STATUS` header
- [ ] OrchestratorStatusPanel shows edge-to-edge `─ NEURAL SUBSTRATE ORCHESTRATOR` header
- [ ] LiveEventFeed shows edge-to-edge `─ SYSTEM EVENT STREAM` header
- [ ] All three panels show proper status indicators in Panel titleRight
- [ ] Quick Actions buttons still work (RE-SCAN, ENABLE ALL, etc.)
- [ ] Event feed auto-scrolls correctly
- [ ] Orchestrator routing visualization updates in real-time
- [ ] No layout shifts or awkward spacing
- [ ] Responsive behavior works at 768px, 1024px, 1920px widths

---

## Phase 4: Verify MetricsPage Panels (Secondary)

### Overview
MetricsPage already uses correct patterns. This phase verifies no regressions after Panel.module.css changes.

### Files to verify:
1. `/frontend/src/pages/MetricsPage/SystemHealthOverview.tsx`
2. `/frontend/src/pages/MetricsPage/QueryAnalyticsPanel.tsx`
3. `/frontend/src/pages/MetricsPage/TierComparisonPanel.tsx`
4. `/frontend/src/pages/MetricsPage/ResourceUtilizationPanel.tsx`
5. `/frontend/src/pages/MetricsPage/RoutingAnalyticsPanel.tsx`
6. `/frontend/src/pages/MetricsPage/HistoricalMetricsPanel.tsx`

### Expected behavior (no code changes needed):
All MetricsPage panels already use Panel component correctly. After Phase 1 (Panel.module.css fix), they should automatically show edge-to-edge borders.

### Testing Checklist:
- [ ] Navigate to /metrics page
- [ ] System Health Overview panel shows edge-to-edge borders
- [ ] Query Analytics panel shows edge-to-edge borders
- [ ] Tier Comparison panel shows edge-to-edge borders
- [ ] Resource Utilization panel shows edge-to-edge borders
- [ ] Routing Analytics panel shows edge-to-edge borders
- [ ] Historical Metrics panel shows edge-to-edge borders
- [ ] All charts and sparklines render correctly
- [ ] No spacing regressions in metric grids
- [ ] Responsive layout works at all breakpoints

**Note:** If any panel shows issues, check if it uses custom padding that conflicts with Panel.module.css changes. Add `padding-top` and `padding-bottom` to panel-specific CSS if needed.

---

## Phase 5: Fix ModelManagementPage (Secondary)

### Overview
ModelSettings component uses inline ASCII generation with `padLine()` function instead of AsciiSectionHeader. This creates inconsistent width and doesn't match the edge-to-edge pattern.

### File: `/frontend/src/components/models/ModelSettings.tsx`

**Current implementation:**
Lines 20-29 define `padLine()` function that generates ASCII borders inline. This should be replaced with AsciiSectionHeader component.

**Problem:**
- `padLine()` uses fixed 150-char width (hardcoded)
- Doesn't automatically adjust to viewport width
- Inline string generation instead of reusable component
- Inconsistent with rest of application

**Solution:**
Replace inline ASCII generation with AsciiSectionHeader component (same as HomePage components).

**Lines to modify:** 1, 24-29, and all instances using `padLine()`

**Add import (line 1):**
```tsx
import React, { useState, useCallback } from 'react';
import { AsciiSectionHeader } from '../terminal/AsciiSectionHeader'; // ADD THIS LINE
import type {
  DiscoveredModel,
  GlobalRuntimeSettings,
  RuntimeSettingsUpdateRequest
} from '@/types/models';
```

**Remove padLine function (lines 24-29):**
```tsx
// DELETE THIS ENTIRE FUNCTION
/**
 * Pad ASCII line to fixed width for terminal aesthetic
 * Ensures consistent frame width across all screen sizes (150 chars)
 */
const padLine = (content: string, width: number = 150): string => {
  if (content.length >= width) {
    return content.substring(0, width);
  }
  return content.padEnd(width, '─');
};
```

**Find all instances of inline ASCII generation:**
Search for patterns like:
```tsx
<div className={styles.asciiHeader}>
  {padLine(`┌─ ${model.modelId} SETTINGS ─`, 150)}
</div>
```

**Replace with:**
```tsx
<AsciiSectionHeader title={`${model.modelId} SETTINGS`} />
```

**Example replacement:**
```tsx
// BEFORE
<div className={styles.settingsPanel}>
  <div className={styles.asciiHeader}>
    {padLine(`┌─ ${model.modelId} SETTINGS ─`, 150)}
  </div>
  <div className={styles.settingsBody}>
    {/* Settings fields */}
  </div>
  <div className={styles.asciiFooter}>
    {padLine('└─', 150)}
  </div>
</div>

// AFTER
<div className={styles.settingsPanel}>
  <AsciiSectionHeader title={`${model.modelId} SETTINGS`} />
  <div className={styles.settingsBody}>
    {/* Settings fields */}
  </div>
</div>
```

**Explanation:**
- Remove `padLine()` function entirely
- Replace all inline ASCII generation with `<AsciiSectionHeader title="..." />`
- Remove ASCII footer lines (AsciiSectionHeader handles full line)
- Simplifies code and ensures consistency with rest of application

**Expected result:**
- ModelSettings panels show edge-to-edge ASCII headers matching HomePage
- Consistent visual appearance across all pages
- Simpler code (no inline string generation)
- Automatic viewport width adjustment

**Testing:**
- [ ] Navigate to Model Management page
- [ ] Expand settings for any model
- [ ] ASCII header extends edge-to-edge
- [ ] Settings fields layout unchanged
- [ ] Apply/Reset buttons still work
- [ ] Port selector renders correctly
- [ ] No spacing regressions

---

## Phase 6: ModeSelector ASCII Header Fix (if needed)

### File: `/frontend/src/components/modes/ModeSelector.tsx`

**Current status:** Need to check if ModeSelector uses custom ASCII headers.

**Investigation needed:**
- Search for inline ASCII generation in ModeSelector.tsx
- Check ModeSelector.module.css for custom header styles
- Verify if it uses AsciiSectionHeader or Panel

**If custom headers found:**
Replace with AsciiSectionHeader following Phase 5 pattern.

**If already using AsciiSectionHeader or Panel:**
No changes needed, Phase 1 fix will automatically apply.

**Testing:**
- [ ] Navigate to HomePage
- [ ] Check ModeSelector component (above query input)
- [ ] Verify ASCII headers (if any) extend edge-to-edge
- [ ] Mode selection buttons work correctly
- [ ] Council/Benchmark config panels expand properly

---

## Implementation Order

### Critical Path (Sequential)
1. **Phase 1: Panel.module.css** - MUST be done first (affects all pages)
2. **Phase 2: SettingsPage** - Can be done in parallel with Phase 3
3. **Phase 3: HomePage** - Depends on Phase 1 completion

### Parallel Work (After Phase 1)
- Phase 2 (SettingsPage) and Phase 3 (HomePage) can be done simultaneously
- Phase 4 (MetricsPage verification) can be done anytime after Phase 1
- Phase 5 (ModelManagementPage) can be done anytime after Phase 1

### Recommended Sequence
```
1. Phase 1: Fix Panel.module.css (15 min)
   └─> TEST: AdminPage still works, no regressions

2. Phase 2: Fix SettingsPage (20 min)
   └─> TEST: Settings page edge-to-edge

3. Phase 3A: SystemStatusPanelEnhanced (30 min)
   └─> TEST: HomePage system status header

4. Phase 3B: OrchestratorStatusPanel (30 min)
   └─> TEST: HomePage orchestrator header

5. Phase 3C: LiveEventFeed (20 min)
   └─> TEST: HomePage event feed header

6. Phase 4: Verify MetricsPage (20 min)
   └─> TEST: All 6 panels edge-to-edge

7. Phase 5: ModelManagementPage (45 min)
   └─> TEST: Model settings headers

8. Phase 6: ModeSelector (if needed) (20 min)
   └─> TEST: Mode selector headers

TOTAL: 4-6 hours
```

---

## Testing Checklist

### Visual Regression Testing

**At each phase completion:**
1. Open browser DevTools
2. Test at breakpoints:
   - [ ] 1920x1080 (Desktop)
   - [ ] 1024x768 (Tablet landscape)
   - [ ] 768x1024 (Tablet portrait)
   - [ ] 375x667 (Mobile)

**Check for:**
- [ ] ASCII borders extend to left edge (no gap)
- [ ] ASCII borders extend to right edge (no gap)
- [ ] Content has comfortable horizontal padding (16px)
- [ ] No horizontal scrollbar appears
- [ ] No layout shifts or awkward spacing
- [ ] Text remains readable at all widths

### Functional Testing

**HomePage:**
- [ ] Query input works
- [ ] Mode selector works
- [ ] System status shows correct metrics
- [ ] Orchestrator panel updates in real-time
- [ ] Event feed shows live events
- [ ] Quick Actions buttons work (RE-SCAN, ENABLE ALL, etc.)

**SettingsPage:**
- [ ] All settings sections expand/collapse
- [ ] Form fields editable
- [ ] Save/Reset buttons work
- [ ] Restart banner appears when needed
- [ ] Port configuration updates correctly

**MetricsPage:**
- [ ] All 6 panels load data
- [ ] Charts render correctly
- [ ] Sparklines animate smoothly
- [ ] Historical metrics collapsible section works
- [ ] No performance degradation (60fps target)

**ModelManagementPage:**
- [ ] Model cards display correctly
- [ ] Settings panels expand/collapse
- [ ] Port selector works
- [ ] Apply/Reset buttons work
- [ ] Server status updates in real-time

### Cross-Browser Testing

Test in:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if on macOS)

Check for:
- [ ] Consistent ASCII rendering (monospace font)
- [ ] No font kerning issues
- [ ] Borders align properly in all browsers

---

## Success Criteria

### Visual Quality
- [ ] ASCII borders reach left edge at 0px
- [ ] ASCII borders reach right edge at 100vw
- [ ] Consistent appearance across all pages
- [ ] No gaps, overlaps, or misalignments
- [ ] Professional terminal aesthetic maintained

### Functionality
- [ ] All interactive elements work correctly
- [ ] No regressions in existing features
- [ ] Form submissions work
- [ ] Real-time updates continue to work
- [ ] No console errors

### Performance
- [ ] Page load time unchanged (<2s target)
- [ ] 60fps animations maintained
- [ ] No layout thrashing
- [ ] No memory leaks

### Responsiveness
- [ ] Works at 320px minimum width
- [ ] Works at 4K resolution (3840px)
- [ ] No horizontal scrollbar at any width
- [ ] Content readable at all breakpoints

---

## Files Modified Summary

### Phase 1: Core Component Fix
- ✏️ `/frontend/src/components/terminal/Panel/Panel.module.css` (line 54)
  - Change: `padding: var(--space-md)` → `padding: 0 var(--space-md)`

### Phase 2: SettingsPage Fix
- ✏️ `/frontend/src/pages/SettingsPage/SettingsPage.module.css` (lines 12-14)
  - Remove: `max-width: 1600px`, `margin: 0 auto`
  - Change: `padding: 24px` → `padding: 0`

### Phase 3: HomePage Standardization
- ✏️ `/frontend/src/components/terminal/SystemStatusPanel/SystemStatusPanelEnhanced.tsx`
  - Add import: `AsciiSectionHeader`
  - Lines 138-148: Wrap with Fragment, add AsciiSectionHeader, remove title prop
  - Lines 205-215: Wrap with Fragment, add AsciiSectionHeader, remove title prop

- ✏️ `/frontend/src/components/dashboard/OrchestratorStatusPanel/OrchestratorStatusPanel.tsx`
  - Add import: `AsciiSectionHeader`
  - Lines 68-73: Add AsciiSectionHeader, remove title prop
  - Lines 77-84: Add AsciiSectionHeader, remove title prop
  - Lines 88-93: Add AsciiSectionHeader, remove title prop
  - Lines 104-136: Add AsciiSectionHeader, remove title prop
  - Lines 139-147: Add AsciiSectionHeader, remove title prop

- ✏️ `/frontend/src/components/dashboard/LiveEventFeed/LiveEventFeed.tsx`
  - Add import: `AsciiSectionHeader`
  - Lines 118-124: Add AsciiSectionHeader, remove title prop

### Phase 4: MetricsPage Verification
- 🔍 No code changes (verification only)
- Check all 6 panel files for proper edge-to-edge rendering

### Phase 5: ModelManagementPage Fix
- ✏️ `/frontend/src/components/models/ModelSettings.tsx`
  - Add import: `AsciiSectionHeader`
  - Remove: `padLine()` function (lines 24-29)
  - Replace all inline ASCII generation with `<AsciiSectionHeader />`

### Phase 6: ModeSelector Fix (if needed)
- 🔍 Investigation needed
- ✏️ `/frontend/src/components/modes/ModeSelector.tsx` (if changes required)

---

## Troubleshooting Guide

### Issue: ASCII borders still have gaps

**Cause:** Parent container has padding or max-width

**Solution:**
1. Inspect element in DevTools
2. Check all parent containers for padding/margin/max-width
3. Ensure page-level container has `padding: 0` and `width: 100%`
4. Verify Panel.module.css change was applied correctly

### Issue: Content too close to edges

**Cause:** Removed padding not compensated by child components

**Solution:**
1. Add horizontal padding to content containers (not ASCII headers)
2. Use `padding: 0 var(--space-md)` on content sections
3. Do NOT add padding to ASCII header components

### Issue: Horizontal scrollbar appears

**Cause:** ASCII dash repeat exceeds viewport width

**Solution:**
1. AsciiSectionHeader uses 150-char dash repeat (should work for most widths)
2. Check for inline ASCII generation with longer strings
3. Ensure `overflow: hidden` on ASCII header containers

### Issue: Panel titleRight overlaps header

**Cause:** AsciiSectionHeader conflicts with Panel title bar

**Solution:**
1. AsciiSectionHeader goes OUTSIDE Panel (before it)
2. Panel titleRight shows status indicators only (no title text)
3. Ensure proper Fragment wrapping: `<> <AsciiSectionHeader /> <Panel titleRight={...}> ... </Panel> </>`

### Issue: Responsive layout breaks on mobile

**Cause:** Fixed-width ASCII dash repeat too wide for narrow screens

**Solution:**
1. AsciiSectionHeader uses `overflow: hidden` to clip long lines
2. Check mobile breakpoints in CSS (768px, 375px)
3. Ensure `white-space: pre` and `text-overflow: clip` set correctly

---

## Rollback Plan

If critical issues arise:

1. **Revert Phase 1** (Panel.module.css):
   ```css
   .content {
     padding: var(--space-md); /* Restore all-sides padding */
     flex: 1;
     overflow: visible;
   }
   ```

2. **Revert Phase 2** (SettingsPage.module.css):
   ```css
   .page {
     display: flex;
     flex-direction: column;
     gap: 24px;
     animation: fade-in var(--transition-base);
     max-width: 1600px; /* Restore max-width */
     margin: 0 auto; /* Restore centering */
     padding: 24px; /* Restore padding */
   }
   ```

3. **Revert Phase 3** (HomePage components):
   - Remove AsciiSectionHeader imports
   - Restore `title="..."` props on Panel components
   - Remove React Fragment wrappers

4. **Rebuild Docker container:**
   ```bash
   docker-compose build --no-cache synapse_frontend
   docker-compose up -d
   ```

---

## Next Steps After Completion

1. **Create SESSION_NOTES.md entry** documenting implementation
2. **Update CLAUDE.md** with ASCII header patterns section
3. **Take screenshots** for documentation (before/after)
4. **Update README.md** with UI consistency improvements
5. **Create git commit** with descriptive message:
   ```
   feat(ui): Achieve edge-to-edge ASCII borders across all pages

   - Fix Panel.module.css: Horizontal padding only (not vertical)
   - Remove SettingsPage max-width constraint
   - Standardize HomePage headers with AsciiSectionHeader
   - Replace ModelSettings inline ASCII with AsciiSectionHeader
   - Verify MetricsPage panels show edge-to-edge borders

   All pages now show consistent NERV-inspired terminal aesthetic
   with ASCII section headers extending fully to viewport edges.

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

---

## Additional Resources

**Reference Files:**
- Good example: `/frontend/src/pages/AdminPage/AdminPage.tsx`
- Good example: `/frontend/src/pages/AdminPage/AdminPage.module.css`
- Component: `/frontend/src/components/terminal/AsciiSectionHeader/AsciiSectionHeader.tsx`
- Component: `/frontend/src/components/terminal/Panel/Panel.tsx`

**Design Principles:**
- Edge-to-edge: ASCII borders touch viewport edges
- Horizontal padding: Content has 16px left/right margins
- Vertical spacing: Controlled by gaps and margins, not padding
- Consistency: Use AsciiSectionHeader everywhere, not inline generation

**Terminal Aesthetic:**
- Font: JetBrains Mono (monospace)
- Character: `─` (U+2500 Box Drawing Light Horizontal)
- Pattern: `─ TITLE ─────────────────` (150 dashes after title)
- Color: Phosphor orange (#ff9500) with glow effect

---

**END OF IMPLEMENTATION PLAN**
