# ASCII Frame Responsive Implementation

**Date:** 2025-11-09
**Status:** Completed
**Objective:** Remove corner characters from ASCII frames and make them responsive to window width

## Problem Statement

The fixed-width ASCII frames with corner characters (┌, ┐, └, ┘) broke the visual illusion when the window was resized:

```
┌─ TITLE ──────────┐  ← Fixed 70 chars wide
  content             ← Gaps appear on wider screens
└──────────────────┘
```

## Solution Implemented

Removed corners and used pure horizontal lines that extend to fill the container width:

```
─ TITLE ─────────────────────────────────────────
  content
──────────────────────────────────────────────────
```

## Implementation Details

### 1. TypeScript Changes (AdminPage.tsx)

Updated all 8 ASCII frame generation blocks to:
- Remove corner characters (┌, ┐, └, ┘)
- Generate long horizontal lines (150 characters) that overflow
- Let CSS clip excess characters at container edge

**Pattern Changed From:**
```typescript
const header = '─ TITLE ';
const headerPadding = '─'.repeat(FRAME_WIDTH - header.length - 2);

return `┌${header}${headerPadding}┐
${padLine('content', FRAME_WIDTH)}
└${'─'.repeat(FRAME_WIDTH - 2)}┘`;
```

**Pattern Changed To:**
```typescript
const header = '─ TITLE ';

return `${header}${'─'.repeat(150)}
${padLine('content', FRAME_WIDTH)}
${'─'.repeat(150)}`;
```

### 2. CSS Changes (AdminPage.module.css)

Added responsive properties to `.asciiFrame` class:

```css
.asciiFrame {
  /* ... existing properties ... */
  overflow: hidden;      /* Clip excess characters */
  text-overflow: clip;   /* Don't add ellipsis */
  width: 100%;          /* Fill container */
  box-sizing: border-box;
}
```

Added `.asciiPanelBody` class for proper width management:

```css
.asciiPanelBody {
  width: 100%;
  overflow: hidden;
}
```

## Frames Updated

All 8 frames in AdminPage were updated:

1. **System Health** (lines 262-276)
2. **System Metrics (Live)** (lines 308-317)
3. **API Request Rate** (lines 327-341)
4. **Model Tier Performance** (lines 349-360)
5. **Model Discovery** (lines 498-519)
6. **API Endpoint Test Map** (lines 591-608)
7. **Server Rack Status** (lines 667-681)
8. **System Architecture** (lines 751-774)

## Expected Behavior

- **Top border:** `─ TITLE ──────────────...` (extends to edge)
- **Content:** `  content` (no side borders)
- **Bottom border:** `─────────────────────...` (extends to edge)
- **Responsive:** Lines extend/contract with window width
- **No visual breaks:** Smooth appearance at all screen sizes

## Files Modified

### Updated:
- `${PROJECT_DIR}/frontend/src/pages/AdminPage/AdminPage.tsx`
  - Removed all corner characters (┌, ┐, └, ┘)
  - Changed to overflow pattern with 150-character horizontal lines
  - Simplified frame structure

- `${PROJECT_DIR}/frontend/src/pages/AdminPage/AdminPage.module.css`
  - Added `width: 100%` to `.asciiFrame`
  - Added `text-overflow: clip` to prevent ellipsis
  - Added `box-sizing: border-box` for proper sizing
  - Added `.asciiPanelBody` class with width/overflow properties

## Testing

1. **Rebuild frontend container:**
   ```bash
   docker-compose build --no-cache synapse_frontend
   ```

2. **Restart container:**
   ```bash
   docker-compose up -d synapse_frontend
   ```

3. **Verify in browser:**
   - Navigate to `http://localhost:5173/admin`
   - Resize browser window to various widths
   - Confirm horizontal lines extend to edges without breaking
   - Check that content remains properly formatted

## Technical Notes

### Why 150 Characters?

The choice of 150 characters for the overflow lines ensures:
- Wide enough to fill most desktop screens
- Not so long as to cause performance issues
- CSS `overflow: hidden` clips excess automatically
- No need to dynamically calculate screen width

### Box-Drawing Character Alignment

The implementation maintains:
- Fixed-width content lines (70 characters)
- Variable-width border lines (clipped by container)
- Proper monospace alignment throughout

### Performance Considerations

- `box-sizing: border-box` prevents layout shifts
- `overflow: hidden` is GPU-accelerated
- No JavaScript required for responsiveness
- Minimal DOM manipulation on resize

## Alternative Approaches Considered

### 1. CSS Pseudo-elements
Could use `::before` and `::after` to generate borders:
```css
.asciiFrame::before {
  content: '─ TITLE ' attr(data-title) ' ';
  position: absolute;
  top: 0;
  border-bottom: 1px solid var(--webtui-border);
}
```

**Pros:** Cleaner separation of concerns
**Cons:** Requires attribute passing, more complex CSS

### 2. Dynamic Width Calculation
Could calculate exact width based on container size:
```typescript
const containerWidth = ref.current?.clientWidth;
const charsNeeded = Math.floor(containerWidth / charWidth);
```

**Pros:** Exact fit every time
**Cons:** JavaScript required, resize listeners, performance overhead

**Decision:** Overflow + CSS clip was chosen for simplicity and performance

## Design Philosophy

This implementation aligns with the S.Y.N.A.P.S.E. ENGINE terminal aesthetic principles:

1. **Functional Aesthetics:** Visual effects enhance usability
2. **Performance-Critical:** No JavaScript, pure CSS solution
3. **Consistent Palette:** Maintains phosphor orange (#ff9500) theme
4. **Monospace Everything:** Fixed-width fonts for alignment
5. **Progressive Enhancement:** Works at all screen sizes

## Future Enhancements

Potential improvements for consideration:

1. **Adaptive Font Size:** Scale font size based on container width
2. **Content Width Matching:** Make content lines responsive too (currently fixed at 70)
3. **Dynamic Titles:** Pull titles from props/state instead of hardcoding
4. **Theme Variants:** Support different border styles (double-line, dashed, etc.)

## Conclusion

The ASCII frames are now fully responsive, maintaining the terminal aesthetic while adapting to any screen width. The implementation is performant, maintainable, and consistent with the project's design philosophy.

**Result:** Clean, responsive ASCII borders that extend edge-to-edge without breaking the visual illusion.
