# CRT Effects Visual Testing Guide

**Quick reference for testing the enhanced CRT effects**

---

## Access Points

- **Frontend:** http://localhost:5173
- **Example Component:** `/examples/CRTEffectsExample` (to be added to routes)
- **Docker Status:** `docker-compose ps`

---

## Test Checklist

### 1. Bloom Intensity Testing

Visit a page with CRTMonitor and test different bloom values:

```tsx
// Test each intensity level
bloomIntensity={0}    → No glow at all
bloomIntensity={0.3}  → Subtle glow (default)
bloomIntensity={0.6}  → Moderate glow
bloomIntensity={1.0}  → Maximum phosphor bleeding
```

**What to Look For:**
- [ ] No bloom (0): Clean text, no blur visible
- [ ] Default bloom (0.3): Subtle orange glow around text
- [ ] Strong bloom (0.6): Noticeable glow, text still readable
- [ ] Max bloom (1.0): Heavy glow effect, phosphor persistence visible
- [ ] Smooth transitions when changing intensity

---

### 2. Screen Curvature Testing

```tsx
curvatureEnabled={true}   → Curved screen
curvatureEnabled={false}  → Flat screen
```

**What to Look For:**
- [ ] Curved variant: Edges slightly pulled back, center closer
- [ ] Effect is subtle (doesn't distort text)
- [ ] Vignette darkens corners for depth
- [ ] Readability not impaired
- [ ] Effect visible on large panels (>500px width)

**Visual Cues:**
- Outer border appears slightly rounded
- Content has subtle 3D depth
- Corners slightly darker than center

---

### 3. Scanline Animation Testing

```tsx
scanlinesEnabled={true}
scanlineSpeed="slow" | "medium" | "fast"
```

**What to Look For:**
- [ ] Horizontal lines moving smoothly downward
- [ ] No jank or stuttering (should be 60fps)
- [ ] Speed variants work correctly:
  - Slow: 8 seconds per cycle
  - Medium: 4 seconds per cycle
  - Fast: 2 seconds per cycle
- [ ] Lines subtle but visible (phosphor orange tint)
- [ ] No performance impact (check DevTools FPS)

**Performance Test:**
1. Open Chrome DevTools → Performance tab
2. Click Record
3. Watch scanlines for 10 seconds
4. Stop recording
5. Verify FPS ≥ 60fps consistently

---

### 4. Combined Effects Testing

Test all effects working together:

```tsx
<CRTMonitor
  bloomIntensity={0.3}
  curvatureEnabled={true}
  scanlinesEnabled={true}
  intensity="medium"
>
  <YourContent />
</CRTMonitor>
```

**What to Look For:**
- [ ] All effects visible simultaneously
- [ ] No visual conflicts or artifacts
- [ ] Bloom doesn't obscure scanlines
- [ ] Vignette works with curvature
- [ ] Text remains readable with all effects on
- [ ] Performance still 60fps

---

## Chrome DevTools Testing

### Performance Profiling

1. **Open DevTools:**
   - Press `F12` or `Cmd+Option+I` (Mac)
   - Go to "Performance" tab

2. **Record Performance:**
   - Click "Record" button (circle icon)
   - Interact with CRT-wrapped content for 10 seconds
   - Click "Stop"

3. **Analyze Results:**
   - **FPS Graph:** Should be consistently at 60fps
   - **Main Thread:** No long tasks (yellow blocks)
   - **GPU Activity:** Should show GPU involvement (green bars)
   - **Frame Time:** Should be <16.67ms (60fps = 16.67ms per frame)

**Success Criteria:**
- ✅ FPS: ≥60fps consistently
- ✅ Frame time: <16.67ms average
- ✅ No dropped frames
- ✅ GPU rendering active

---

### GPU Layers Verification

1. **Open Layers Panel:**
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
   - Type "Show Layers"
   - Press Enter

2. **Verify Compositor Layers:**
   - Look for separate layers for:
     - `.crtContainer` (perspective transform)
     - `.bloomLayer` (blur filter, will-change)
     - `.scanlines` (transform animation, will-change)

3. **Check Layer Properties:**
   - Each layer should show "Composited" status
   - Look for "will-change" properties
   - Verify GPU memory usage reasonable

**What to Look For:**
- [ ] CRT components on separate compositor layers
- [ ] Each layer shows "Composited: true"
- [ ] GPU memory usage <50MB for effects
- [ ] No excessive layer count (4-6 layers per CRT instance)

---

### Memory Profiling

1. **Open Memory Panel:**
   - DevTools → Memory tab
   - Select "Heap snapshot"

2. **Take Baseline Snapshot:**
   - Load page with CRT effects
   - Take snapshot (click circle icon)

3. **Interact for 5 Minutes:**
   - Scroll, interact with content
   - Change bloom intensity (if interactive)
   - Toggle effects on/off

4. **Take Second Snapshot:**
   - Compare with baseline
   - Look for memory growth

**Success Criteria:**
- ✅ Memory growth <100MB over 5 minutes
- ✅ No detached DOM nodes
- ✅ No memory leaks on component unmount
- ✅ Garbage collection working properly

---

## Browser Compatibility Testing

### Chrome (Primary)

- [ ] All effects render correctly
- [ ] 60fps performance
- [ ] GPU acceleration active
- [ ] Bloom visible and smooth

### Firefox

- [ ] All effects render correctly
- [ ] Performance acceptable (may be slightly slower)
- [ ] Blur filter works
- [ ] Scanlines animate smoothly

### Safari

- [ ] All effects render correctly
- [ ] Bloom may be less intense (blur performance)
- [ ] Scanlines work
- [ ] Consider reducing bloom to 0.2 if FPS drops

**Safari Note:** If bloom causes performance issues:
```tsx
const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
const bloomIntensity = isSafari ? 0.2 : 0.3;
```

### Edge

- [ ] Should match Chrome (Chromium-based)
- [ ] All effects working
- [ ] Performance identical to Chrome

---

## Visual Comparison Test

### Test Setup

1. Open two browser windows side-by-side
2. Left window: `bloomIntensity={0}` (no bloom)
3. Right window: `bloomIntensity={0.3}` (default)

### What to Compare

**No Bloom (0):**
- Clean, crisp text
- No glow around elements
- Sharp edges
- Minimal visual effects

**Default Bloom (0.3):**
- Subtle orange glow around text
- Phosphor persistence effect visible
- Slightly softer appearance
- Retains readability

**Strong Bloom (0.6):**
- Noticeable glow
- Text appears to bleed into background
- Strong CRT aesthetic
- Still readable

**Maximum Bloom (1.0):**
- Heavy phosphor bleeding
- Strong visual impact
- May reduce readability
- Best for short text/titles

---

## Accessibility Testing

### Screen Reader Test

1. Enable screen reader (VoiceOver on Mac, NVDA on Windows)
2. Navigate through CRT-wrapped content
3. Verify all overlays are ignored (aria-hidden)
4. Content should be announced normally

**Success Criteria:**
- [ ] Screen reader doesn't announce visual overlays
- [ ] Content read in correct order
- [ ] No confusion from decorative elements

### Keyboard Navigation

1. Tab through interactive elements
2. Verify focus indicators visible
3. Check all clickable items accessible

**Success Criteria:**
- [ ] Focus indicators visible with effects on
- [ ] Tab order logical
- [ ] No keyboard traps

### Reduced Motion

1. Enable reduced motion in OS settings:
   - Mac: System Preferences → Accessibility → Display → Reduce motion
   - Windows: Settings → Ease of Access → Display → Show animations

2. Reload page
3. Verify animations disabled or reduced

**Success Criteria:**
- [ ] Scanlines stopped or faded
- [ ] Bloom reduced
- [ ] Static effects remain (curvature, vignette)

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| FPS | 60fps | 50-60fps | <50fps |
| Frame Time | <16.67ms | <20ms | >20ms |
| Memory Growth (5min) | <50MB | <100MB | >100MB |
| GPU Memory | <30MB | <50MB | >50MB |
| CPU Usage | <10% | <20% | >20% |

### Test Devices

**Desktop (Required):**
- [ ] macOS (Chrome)
- [ ] Windows (Chrome)
- [ ] Linux (Chrome)

**Mobile (Optional):**
- [ ] iOS Safari (consider bloom=0 or 0.1)
- [ ] Android Chrome (test with reduced effects)

---

## Known Issues & Workarounds

### Issue: Safari Blur Performance

**Symptom:** FPS drops below 50 with bloom enabled
**Workaround:** Reduce bloom to 0.2 or disable on Safari

```tsx
const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
<CRTMonitor bloomIntensity={isSafari ? 0.2 : 0.3}>
```

### Issue: Mobile Performance

**Symptom:** Jank or dropped frames on low-end mobile
**Workaround:** Use performance mode

```tsx
const isMobile = /Mobile|Android|iPhone/i.test(navigator.userAgent);
<CRTMonitor
  bloomIntensity={isMobile ? 0 : 0.3}
  scanlinesEnabled={!isMobile}
  intensity={isMobile ? 'subtle' : 'medium'}
>
```

### Issue: High DPI Displays

**Symptom:** Bloom appears too subtle on Retina displays
**Workaround:** Increase intensity for high DPI

```tsx
const isRetina = window.devicePixelRatio > 1.5;
<CRTMonitor bloomIntensity={isRetina ? 0.4 : 0.3}>
```

---

## Test Results Template

Copy and fill out after testing:

```markdown
## Test Results - [Date]

**Browser:** Chrome 120 / Firefox 121 / Safari 17
**OS:** macOS 14 / Windows 11 / Linux
**Device:** Desktop / Laptop / Mobile

### Bloom Effect
- [ ] bloomIntensity=0: Clean, no glow
- [ ] bloomIntensity=0.3: Subtle glow visible
- [ ] bloomIntensity=0.6: Moderate glow
- [ ] bloomIntensity=1.0: Maximum glow

### Screen Curvature
- [ ] Curvature visible and subtle
- [ ] Vignette darkens edges
- [ ] Readability maintained

### Scanlines
- [ ] Animation smooth at 60fps
- [ ] Speed variants work (slow/medium/fast)
- [ ] No jank or stuttering

### Performance
- FPS: ___fps (target: ≥60)
- Frame Time: ___ms (target: <16.67ms)
- Memory Growth: ___MB (target: <50MB)
- GPU Memory: ___MB (target: <30MB)

### Browser Compatibility
- [ ] Chrome: All effects working
- [ ] Firefox: All effects working
- [ ] Safari: Effects working (bloom may be reduced)
- [ ] Edge: All effects working

### Accessibility
- [ ] Screen reader ignores overlays
- [ ] Keyboard navigation works
- [ ] Reduced motion support

### Issues Found
(List any issues here)

### Screenshots
(Attach screenshots of different bloom levels)
```

---

## Quick Test Script

Run these tests in browser console:

```javascript
// Check if CRT components exist
const crtMonitor = document.querySelector('[data-testid="crt-monitor"]');
console.log('CRT Monitor found:', !!crtMonitor);

const bloomLayer = document.querySelector('[data-testid="bloom-layer"]');
console.log('Bloom layer found:', !!bloomLayer);

const scanlines = document.querySelector('[data-testid="animated-scanlines"]');
console.log('Scanlines found:', !!scanlines);

// Check performance
const fps = performance.now();
requestAnimationFrame(() => {
  const delta = performance.now() - fps;
  console.log('Frame time:', delta.toFixed(2), 'ms');
  console.log('Target FPS:', (1000 / delta).toFixed(2));
});

// Check GPU layers
console.log('Device Pixel Ratio:', window.devicePixelRatio);
console.log('Is Retina:', window.devicePixelRatio > 1.5);
```

---

**Ready to test! Open http://localhost:5173 and verify all effects.**
