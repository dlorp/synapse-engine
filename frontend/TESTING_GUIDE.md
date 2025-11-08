# Query UI Testing Guide

## Prerequisites

### 1. Start Backend
```bash
cd /Users/dperez/Documents/Programming/SYNAPSE_ENGINE/backend
uvicorn app.main:app --reload
```

### 2. Start Frontend
```bash
cd /Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend
npm run dev
```

### 3. Verify Models Running
```bash
curl http://localhost:8000/api/models/status | jq '.models[] | {name, state}'
```

Expected output:
```json
{
  "name": "Q2_FAST_1",
  "state": "active"
}
{
  "name": "Q2_FAST_2",
  "state": "active"
}
{
  "name": "Q3_SYNTH",
  "state": "active"
}
{
  "name": "Q4_DEEP",
  "state": "active"
}
```

## Test Cases

### Test 1: Simple Query (Q2 Tier)

**Objective**: Verify simple queries route to Q2 model

**Steps**:
1. Open http://localhost:5173 in browser
2. Verify system metrics appear in header (VRAM, Queries, Cache)
3. Type in query input: `What is Python?`
4. Leave mode as "AUTO"
5. Ensure "CGRAG CONTEXT" is checked
6. Click "EXECUTE" or press Cmd/Ctrl+Enter

**Expected Results**:
- Loading indicator appears (spinning icon + "Processing query...")
- After 1-3 seconds, response displays
- Metadata shows:
  - Model: Q2_FAST_1 or Q2_FAST_2 [Q2]
  - Tokens: ~100-300
  - Time: <2s
  - Complexity: Q2, Score: ~2-3
  - Reasoning mentions "simple" or "straightforward"
- Response text appears with copy button
- No CGRAG artifacts (simple query doesn't need context)

### Test 2: Complex Query with CGRAG (Q4 Tier)

**Objective**: Verify complex queries route to Q4 and retrieve CGRAG artifacts

**Steps**:
1. Clear previous query (refresh page)
2. Type in query input: `What components were delivered in Session 1 of the S.Y.N.A.P.S.E. ENGINE project? Analyze the architecture and explain how they work together.`
3. Leave mode as "AUTO"
4. Ensure "CGRAG CONTEXT" is checked
5. Click "EXECUTE"

**Expected Results**:
- Loading indicator appears
- Processing takes 5-15 seconds (Q4 model is slower)
- Metadata shows:
  - Model: Q4_DEEP [Q4]
  - Tokens: ~500-1500
  - Time: 5-15s
  - Complexity: Q4, Score: >7
  - Reasoning mentions "complex", "multi-part", "analysis"
  - CGRAG Artifacts: 2-5 artifacts
- CGRAG artifacts section shows:
  - File paths (e.g., "SESSION_1_COMPLETE.md")
  - Relevance scores (80-95%)
  - Chunk indices
  - Token counts
- Response contains detailed analysis using context from docs

### Test 3: Mode Forcing (Simple Q2)

**Objective**: Verify manual mode selection works

**Steps**:
1. Type: `Explain quantum computing and its applications in cryptography`
2. Select mode: "SIMPLE (Q2)"
3. Uncheck "CGRAG CONTEXT"
4. Click "EXECUTE"

**Expected Results**:
- Routes to Q2 model despite complex query
- Metadata shows Model: Q2_FAST_1 or Q2_FAST_2 [Q2]
- No CGRAG artifacts (context disabled)
- Response is simpler/shorter than Q4 would provide
- Processing time <2s

### Test 4: Mode Forcing (Complex Q4)

**Objective**: Verify Q4 mode forcing

**Steps**:
1. Type: `What is 2 + 2?`
2. Select mode: "COMPLEX (Q4)"
3. Check "CGRAG CONTEXT"
4. Click "EXECUTE"

**Expected Results**:
- Routes to Q4 model despite simple query
- Metadata shows Model: Q4_DEEP [Q4]
- Processing time 5-15s
- Response is more verbose than needed
- May include CGRAG artifacts if relevant docs exist

### Test 5: Advanced Settings

**Objective**: Verify advanced settings work

**Steps**:
1. Click "▶ ADVANCED" to expand
2. Adjust "MAX TOKENS" slider to 1024
3. Adjust "TEMPERATURE" slider to 1.5
4. Type: `Write a creative story about AI`
5. Select mode: "AUTO"
6. Click "EXECUTE"

**Expected Results**:
- Advanced settings section expands/collapses
- Sliders update displayed values
- Query submits with custom parameters
- Response respects token limit (stops at ~1024 tokens)
- Higher temperature produces more creative/varied output

### Test 6: CGRAG Toggle

**Objective**: Verify CGRAG context can be disabled

**Steps**:
1. Type: `What was delivered in Session 1?`
2. Uncheck "CGRAG CONTEXT"
3. Click "EXECUTE"

**Expected Results**:
- Query processes normally
- Metadata shows cgragArtifacts: 0
- No CGRAG artifacts section appears
- Response is based only on model's knowledge, not docs

### Test 7: Keyboard Shortcuts

**Objective**: Verify Cmd/Ctrl+Enter works

**Steps**:
1. Type a query in the textarea
2. Press Cmd+Enter (Mac) or Ctrl+Enter (Windows/Linux)

**Expected Results**:
- Query submits without clicking button
- Same behavior as clicking "EXECUTE"

### Test 8: Loading State

**Objective**: Verify UI during processing

**Steps**:
1. Submit a complex query to Q4
2. Observe UI during processing

**Expected Results**:
- "EXECUTE" button changes to "PROCESSING..."
- Submit button is disabled
- Textarea is disabled
- Mode selector is disabled
- CGRAG toggle is disabled
- Advanced settings controls are disabled
- Loading indicator appears above response area
- Spinner icon rotates continuously

### Test 9: Error Handling

**Objective**: Verify error states display correctly

**Steps**:
1. Stop backend server: `Ctrl+C` in backend terminal
2. Submit a query in frontend
3. Wait for timeout

**Expected Results**:
- Loading state appears initially
- After timeout, error panel appears
- Error message: "Query failed. Please try again." or network error
- Previous response (if any) remains visible
- Can try submitting again

### Test 10: Copy Response

**Objective**: Verify copy button works

**Steps**:
1. Submit any query and wait for response
2. Click "COPY" button on response panel

**Expected Results**:
- Response text is copied to clipboard
- Can paste into text editor and verify exact match
- TODO: Toast notification appears (not implemented yet)

### Test 11: Character Counter

**Objective**: Verify character count updates

**Steps**:
1. Type various queries
2. Observe character counter in header

**Expected Results**:
- Counter shows "0 chars" when empty
- Updates in real-time as you type
- Shows correct count (e.g., "25 chars" for 25 character query)

### Test 12: No Models Active

**Objective**: Verify warning when models offline

**Steps**:
1. Stop all model servers (if possible)
2. Wait 5 seconds for status refresh
3. Observe UI

**Expected Results**:
- System metrics show 0 active models
- Warning message appears: "NO MODELS ACTIVE - Waiting for models to come online..."
- Query input is disabled
- Submit button is disabled
- Error indicator shows

### Test 13: Mobile Responsive

**Objective**: Verify responsive layout

**Steps**:
1. Open browser DevTools
2. Toggle device toolbar (Cmd+Shift+M)
3. Test various screen sizes:
   - iPhone 12 (390x844)
   - iPad (768x1024)
   - Desktop (1920x1080)

**Expected Results**:
- Layout adjusts at breakpoints (768px, 1024px)
- System metrics stack vertically on mobile
- Advanced settings grid becomes single column on mobile
- Text remains readable at all sizes
- No horizontal scrolling
- Touch targets are adequate (>44px)

### Test 14: Accessibility

**Objective**: Verify keyboard navigation and screen readers

**Steps**:
1. Use Tab key to navigate through interface
2. Verify focus indicators appear
3. Use Space/Enter to activate controls
4. Use screen reader (VoiceOver on Mac: Cmd+F5)

**Expected Results**:
- Tab order is logical (query → mode → CGRAG → advanced → submit)
- Focus indicators are visible (border highlights)
- All controls are reachable via keyboard
- ARIA labels are read by screen reader
- Button states are announced (disabled, loading)
- Form fields are properly labeled

### Test 15: Cache Hit

**Objective**: Verify cache indicator appears

**Steps**:
1. Submit a query: `What is Python?`
2. Wait for response
3. Submit exact same query again

**Expected Results**:
- Second query returns much faster (<100ms)
- Metadata shows "CACHE HIT" indicator with pulse animation
- Processing time is very low (~50-100ms)
- Response is identical to first query
- Model tier may differ (cache is cross-tier)

## Visual Verification

### Terminal Aesthetic Checklist

- [ ] Pure black background (#000000, #0a0a0a)
- [ ] Phosphor green text (#00ff41)
- [ ] Monospace fonts (JetBrains Mono)
- [ ] Sharp borders (2px solid)
- [ ] High contrast readability
- [ ] Consistent spacing and alignment
- [ ] Status color coding:
  - Active: Green
  - Processing: Cyan
  - Error: Red
  - Amber: Warnings/complexity
- [ ] Smooth animations (no jank)
- [ ] No visual glitches on resize

### Layout Verification

- [ ] Header with centered title
- [ ] System metrics aligned horizontally
- [ ] Query input section with clear borders
- [ ] Response section below input
- [ ] Metadata organized in panels
- [ ] CGRAG artifacts in bordered list
- [ ] Proper spacing between sections
- [ ] Content doesn't overflow containers

## Performance Verification

### Timing Checks

Run these queries and verify timing:

1. **Q2 Simple**: `What is Python?`
   - Expected: <2s

2. **Q3 Moderate**: `Compare Python and JavaScript for web development`
   - Expected: <5s

3. **Q4 Complex**: `Analyze the Session 1 deliverables and their integration points`
   - Expected: <15s

4. **CGRAG Retrieval**: Any query with context
   - Expected: <100ms overhead

### Browser Performance

1. Open Chrome DevTools Performance tab
2. Start recording
3. Submit a query
4. Stop recording
5. Verify:
   - No long tasks (>50ms)
   - Smooth 60fps animations
   - No memory leaks
   - Efficient re-renders

## Common Issues & Solutions

### Issue: Query doesn't submit
- **Check**: Are models active? (system metrics)
- **Check**: Is backend running? (curl http://localhost:8000/health)
- **Check**: Browser console for errors

### Issue: No CGRAG artifacts
- **Check**: Is CGRAG context enabled?
- **Check**: Are docs indexed? (backend logs)
- **Check**: Is query complex enough to trigger context retrieval?

### Issue: Styles look broken
- **Check**: CSS modules are loading (DevTools Network tab)
- **Check**: CSS custom properties defined in root
- **Check**: Hard refresh browser (Cmd+Shift+R)

### Issue: TypeScript errors
- **Solution**: `npm run build` to check for compilation errors
- **Solution**: Restart TypeScript server in IDE

## Automated Testing (Future)

### Unit Tests (React Testing Library)
```bash
npm run test
```

### E2E Tests (Playwright)
```bash
npm run test:e2e
```

### Component Tests (Storybook)
```bash
npm run storybook
```

## Success Criteria

All test cases should pass with:
- ✅ No console errors
- ✅ No TypeScript errors
- ✅ Correct routing to model tiers
- ✅ CGRAG artifacts display properly
- ✅ All interactive elements work
- ✅ Responsive layout functions
- ✅ Accessibility standards met
- ✅ Performance targets achieved
- ✅ Terminal aesthetic consistent

---

**Testing Status**: Ready for Manual Testing
**Last Updated**: 2025-01-15
