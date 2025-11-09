# Phase 1 Testing Checklist

**Date:** 2025-11-08
**Status:** Ready for Validation
**URL:** http://localhost:5173

---

## Visual Verification

### ✅ Dot Matrix Display Banner

**Location:** Top of HomePage, centered

**What to Check:**
- [ ] Banner displays "SYNAPSE ENGINE" text
- [ ] Characters reveal one at a time (left to right)
- [ ] Each character is composed of 5x7 LED pixels
- [ ] Phosphor orange color (#ff9500) is visible
- [ ] Glow effect around each LED pixel
- [ ] Animation completes in ~5.6 seconds (14 chars × 400ms)
- [ ] Banner is centered and responsive

**Expected Appearance:**
```
   █████   █   █  ███    █████  ███████  ████   █████
  █     █  █   █  █  █   █   █  █     █  █      █
  █        █   █  █   █  █████  █████ █  ████   █████
   █████   █████  █   █  █   █  █     █     █   █
       █       █  █   █  █   █  █     █     █   █
  █     █      █  █  █   █   █  █     █  █      █
   █████       █  ███    █   █  ███████  ████   █████

  (but in dot matrix LED style with phosphor glow)
```

**Common Issues:**
- Banner not visible → Check console for Canvas errors
- Characters don't reveal → Check DotMatrixAnimation.ts requestAnimationFrame
- No glow effect → Check shadowBlur in CharacterMap.ts LED_CONFIG

---

### ✅ CRT Monitor Effects

**Location:** Wraps entire HomePage

**What to Check:**
- [ ] **Bloom Effect** - Bright text has a soft glow spreading beyond edges
- [ ] **Screen Curvature** - Subtle perspective/depth effect (3D transform)
- [ ] **Scanlines** - Horizontal lines moving down the screen
- [ ] **Vignette** - Dark edges around the screen (radial gradient)
- [ ] All effects work together harmoniously

**Expected Appearance:**
- Bloom: Phosphor orange text (#ff9500) should have a soft halo
- Curvature: Entire screen should have a subtle "curved glass" appearance
- Scanlines: Thin horizontal lines (2px cycle) moving at 2s per full cycle
- Vignette: Edges should be slightly darker than center

**Performance Targets:**
- Scanline animation: 60fps (no stuttering)
- Bloom filter: No visible lag on text rendering
- GPU acceleration: Check in DevTools (should use compositing)

**Common Issues:**
- No bloom → Check CRTMonitor bloomIntensity prop (should be 0.3)
- Scanlines not moving → Check AnimatedScanlines animation
- No curvature → Check CRTMonitor.module.css perspective transform
- Poor performance → Check will-change and transform3d in CSS

---

### ✅ Terminal Spinner

**Location:** Loading indicator below query input (only visible during query processing)

**What to Check:**
- [ ] Spinner displays during query processing
- [ ] Arc style animation (◜ ◝ ◞ ◟)
- [ ] Phosphor orange color (#ff9500)
- [ ] Smooth rotation animation
- [ ] Glow effect around spinner character
- [ ] Pulse animation (opacity 1 → 0.7 → 1)

**How to Trigger:**
1. Submit a query on HomePage
2. Watch for spinner to appear below input
3. Spinner should be visible next to Timer component

**Expected Appearance:**
```
  ◜  PROCESSING...  [TIMER: 00:02.45]
  (spinning arc character with phosphor glow)
```

**Performance Targets:**
- Animation: 60fps (smooth rotation)
- Frame updates: ~100ms per frame (800ms / 8 frames)

**Common Issues:**
- Spinner not visible → Submit a query to trigger loading state
- No rotation → Check setInterval in TerminalSpinner.tsx
- No glow → Check text-shadow in TerminalSpinner.module.css

---

## Performance Validation

### 60fps Target Verification

**Tools:** Safari Web Inspector or Brave DevTools

**Steps:**

1. **Open DevTools**
   - Safari: Develop → Show Web Inspector → Timelines
   - Brave: View → Developer → Developer Tools → Performance

2. **Start Recording**
   - Click "Record" button
   - Interact with the page for 10 seconds
   - Click "Stop"

3. **Analyze Results**
   - Check FPS graph (should be steady at 60fps)
   - Look for frame drops (should be minimal)
   - Check scripting time (should be <10ms per frame)
   - Check rendering time (should be <5ms per frame)

**Success Criteria:**
- [ ] Average FPS: ≥60fps
- [ ] Frame time: <16.67ms (60fps budget)
- [ ] Canvas render time: <5ms per frame
- [ ] No memory leaks over 5 minutes
- [ ] No layout thrashing

**Common Issues:**
- FPS drops to 30fps → Check for blocking JavaScript
- High scripting time → Check DotMatrixAnimation render loop
- High rendering time → Check CSS filter performance (bloom)
- Memory growth → Check for missing cleanup in useEffect

---

### Canvas Performance (Dot Matrix)

**DevTools Layers Panel:**
1. Open Layers panel (Safari/Brave DevTools)
2. Verify Canvas element has its own compositor layer
3. Check for hardware acceleration (should say "Compositing reasons")

**Expected:**
- Canvas should be GPU-accelerated
- No forced reflows during animation
- requestAnimationFrame should show in timeline

**Common Issues:**
- Canvas not composited → Add `will-change: transform` to canvas CSS
- Forced reflows → Check for layout reads in animation loop

---

### CSS Animation Performance (Scanlines, Bloom)

**DevTools Performance:**
1. Record timeline during idle state
2. Check for continuous animation activity
3. Verify GPU acceleration for filters and transforms

**Expected:**
- Scanlines: transform animation only (no layout/paint)
- Bloom: CSS filter composited on GPU
- No main thread blocking

**Common Issues:**
- Scanlines causing paint → Check if using transform vs top/bottom
- Bloom filter slow → Check if using too high blur values (20px max)

---

## Browser Compatibility

### Safari (Primary Test)

**Version:** Latest stable
**Status:** ⏳ Pending

**Checks:**
- [ ] Dot matrix displays correctly
- [ ] Canvas animation smooth
- [ ] CRT effects visible (bloom, curvature, scanlines)
- [ ] Terminal spinner rotates smoothly
- [ ] 60fps performance maintained

**Known Safari Issues:**
- Canvas shadowBlur can be slower than Chrome
- CSS backdrop-filter may affect bloom performance

---

### Brave (Chromium)

**Version:** Latest stable
**Status:** ⏳ Pending

**Checks:**
- [ ] All visual effects render correctly
- [ ] Performance matches or exceeds Safari
- [ ] No Chromium-specific rendering bugs

**Expected:**
- Better Canvas performance than Safari
- Potentially better CSS filter performance

---

## Responsive Design

### Desktop (1920×1080)
- [ ] Dot matrix banner: 600px wide, centered
- [ ] All effects visible and smooth
- [ ] No horizontal scroll

### Tablet (1024×768)
- [ ] Dot matrix banner: Scales to fit (max-width: 100%)
- [ ] CRT effects still visible
- [ ] No layout breaks

### Mobile (375×667)
- [ ] Dot matrix banner: Scaled down appropriately
- [ ] Spinner and banner stack vertically in loading state
- [ ] Performance acceptable (may be 30fps on mobile)

---

## Integration Testing

### Component Interaction

**Test 1: HomePage Load**
1. Navigate to http://localhost:5173
2. Verify dot matrix banner animates on page load
3. Verify CRT effects wrap entire page
4. Check browser console for errors

**Expected Result:**
- ✅ All components render
- ✅ No console errors
- ✅ Animations start automatically

---

**Test 2: Query Submission**
1. Enter query in input field
2. Click submit
3. Verify spinner appears in loading state
4. Watch for response display

**Expected Result:**
- ✅ Spinner appears immediately on submit
- ✅ Timer starts counting
- ✅ Spinner disappears when response arrives
- ✅ CRT effects remain active throughout

---

**Test 3: Page Navigation**
1. Navigate to different pages (Settings, Metrics, etc.)
2. Return to HomePage
3. Verify dot matrix banner re-animates

**Expected Result:**
- ✅ Banner resets and animates on each page load
- ✅ No memory leaks from previous animations
- ✅ CRT effects remain consistent

---

## Error Handling

### Console Errors to Check

**Open Browser Console (Cmd+Option+C in Safari/Brave)**

**No Errors Should Appear:**
- [ ] No Canvas context errors
- [ ] No module import errors
- [ ] No React hook errors (useEffect cleanup)
- [ ] No animation frame errors

**Expected Warnings (OK to Ignore):**
- WebSocket connection warnings (if models not running)

**Critical Errors (Must Fix):**
- "Canvas is null" → DotMatrixDisplay ref not attached
- "Cannot read property of undefined" → Missing component props
- "Maximum update depth exceeded" → Infinite re-render loop

---

## Success Criteria Summary

### Phase 1 Complete When:

✅ **Visual:**
- Dot matrix banner displays and animates correctly
- CRT effects (bloom, curvature, scanlines) all visible
- Terminal spinner rotates smoothly
- Phosphor orange theme consistent throughout

✅ **Performance:**
- 60fps maintained during all animations
- No memory leaks over 5+ minutes
- Canvas render time <5ms
- Total frame time <16.67ms

✅ **Integration:**
- All components work together harmoniously
- No console errors
- Responsive on desktop/tablet
- Works in Safari and Brave browsers

✅ **Code Quality:**
- TypeScript strict mode (no errors)
- Proper cleanup in useEffect hooks
- No memory leaks
- Accessible (ARIA labels, reduced motion support)

---

## Next Steps After Validation

### If All Tests Pass:
1. Mark Phase 1 as complete
2. Update [SESSION_NOTES.md](./SESSION_NOTES.md) with results
3. Begin Phase 2 planning (Advanced Charts, System Monitoring)

### If Issues Found:
1. Document specific failures in this checklist
2. Create bug report with:
   - Browser and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots or screen recordings
3. Prioritize fixes based on severity
4. Re-test after fixes

---

## Performance Profiling Commands

**If performance issues are detected:**

```bash
# Check Docker resource usage
docker stats synapse_frontend

# Check frontend bundle size
docker exec synapse_frontend npm run build
# Look for bundle size warnings

# Check for memory leaks in Chrome DevTools:
# 1. Open Memory profiler
# 2. Take heap snapshot
# 3. Interact with page for 5 minutes
# 4. Take another snapshot
# 5. Compare snapshots (should have minimal growth)
```

---

## Visual Reference

**Expected HomePage Layout:**

```
┌────────────────────────────────────────────────────────┐
│  [CRT Monitor Effect - Bloom + Curvature + Scanlines]  │
│                                                          │
│            ╔════════════════════════════════╗            │
│            ║   SYNAPSE ENGINE               ║            │
│            ║   (Dot Matrix LED Banner)      ║            │
│            ╚════════════════════════════════╝            │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Query Input                                      │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │ Enter your query...                        │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │  [Submit]                                         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  ◜ Processing...  Timer: 00:02.45               │  │
│  │  (Terminal Spinner during loading)               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Response Display                                 │  │
│  │  ...                                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└────────────────────────────────────────────────────────┘
```

**Colors:**
- Background: #000000 (black)
- Primary text: #ff9500 (phosphor orange)
- Glow: #ff9500 with shadowBlur

---

**Testing Contact:** Check browser console and Docker logs for detailed error messages if any issues arise.

**Documentation:** See [plans/DESIGN_OVERHAUL_PHASE_1.md](./plans/DESIGN_OVERHAUL_PHASE_1.md) for implementation details.
