# Preset System Improvements - Testing Guide

**Date:** 2025-11-30
**Application URL:** http://localhost:5173

## Quick Testing Checklist

Use this guide to verify all three improvements are working correctly.

---

## Test 1: Portal Dropdown Behavior

### Expected Behavior
The preset dropdown should "pop out" above all other UI elements and not be clipped by parent containers.

### Steps to Test

1. **Navigate to Home Page**
   - Open http://localhost:5173 in browser
   - Should see QUERY INPUT panel

2. **Locate Preset Selector**
   - Look for `[◆ DEFAULT ▼]` button in the action group
   - Should be to the left of `[▶ ADVANCED]` button

3. **Click Dropdown Button**
   - Click the `[◆ DEFAULT ▼]` button
   - Dropdown menu should appear below the button
   - Menu should NOT be clipped by parent container

4. **Verify Visual Appearance**
   - ✅ Dropdown renders with full width (at least 180px)
   - ✅ All 7 options visible (DEFAULT, ANALYST, CODER, CREATIVE, RESEARCH, JUDGE, CUSTOM)
   - ✅ Dropdown has phosphor orange border (#ff9500)
   - ✅ Dropdown has subtle shadow
   - ✅ Selected option has orange checkmark (●)
   - ✅ Selected option has left border accent

5. **Test Positioning**
   - Scroll the page up/down
   - Click dropdown again - should reposition correctly
   - Dropdown should always appear below button, never clipped

6. **Test Click Outside**
   - Open dropdown
   - Click anywhere outside dropdown
   - ✅ Dropdown should close

### Visual Reference
```
[◆ DEFAULT ▼]  [▶ ADVANCED]  [EXECUTE]
      ↓
┌──────────────────────┐
│ [D] DEFAULT        ● │ ← Selected, has checkmark
│ [A] ANALYST          │
│ [C] CODER            │
│ [V] CREATIVE         │
│ [R] RESEARCH         │
│ [J] JUDGE            │
├──────────────────────┤ ← Separator line
│ [U] CUSTOM           │
└──────────────────────┘
```

---

## Test 2: System Prompt Preview

### Expected Behavior
When Advanced settings are expanded, the system prompt for the selected preset should be visible.

### Steps to Test

1. **Expand Advanced Settings**
   - Click `[▶ ADVANCED]` button
   - Should expand to show advanced settings panel

2. **Verify System Prompt Section**
   - Should see section labeled "SYSTEM PROMPT (SYNAPSE_DEFAULT):"
   - Below label should be a bordered preview box

3. **Check Default State**
   - Since built-in presets don't have system_prompt values yet
   - Should see: **"No system prompt defined for this preset"**
   - Text should be gray, italic, centered

4. **Test Different Presets**
   - Select ANALYST from dropdown
   - Label should change to "SYSTEM PROMPT (SYNAPSE_ANALYST):"
   - Should still show "No system prompt defined" (until backend adds prompts)

5. **Verify Styling**
   - ✅ Preview box has dark background
   - ✅ Preview box has border
   - ✅ Max height ~120px
   - ✅ Scrollbar appears if content exceeds height
   - ✅ Monospace font (JetBrains Mono)
   - ✅ Phosphor orange text color

### Visual Reference
```
▼ ADVANCED SETTINGS
┌─────────────────────────────────────────────────┐
│ SYSTEM PROMPT (SYNAPSE_DEFAULT):                │
│ ┌─────────────────────────────────────────────┐ │
│ │                                             │ │
│ │  No system prompt defined for this preset   │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ MAX TOKENS: 512        TEMPERATURE: 0.70        │
└─────────────────────────────────────────────────┘
```

### Testing with Actual System Prompt

If you want to see the preview with actual content, temporarily add a system_prompt to a preset:

**Backend modification (OPTIONAL):**
```python
# backend/app/models/code_chat.py, line ~860

"SYNAPSE_DEFAULT": ModelPreset(
    name="SYNAPSE_DEFAULT",
    description="Foundational baseline preset...",
    system_prompt="You are SYNAPSE_DEFAULT, a helpful AI assistant.",  # Add this line
    planning_tier="balanced",
    is_custom=False,
    tool_configs={}
),
```

Then:
```bash
docker-compose restart synapse_core
```

Now the preview should show the prompt text instead of "No system prompt defined".

---

## Test 3: Custom System Prompt Option

### Expected Behavior
Selecting CUSTOM from the dropdown should show an editable textarea in the Advanced section.

### Steps to Test

1. **Select CUSTOM Preset**
   - Click preset dropdown
   - Scroll to bottom of list
   - Should see **CUSTOM** option with separator line above it
   - Keyboard shortcut key: `[U]`
   - Click CUSTOM option

2. **Verify Dropdown Display**
   - Button should now show: `[◆ CUSTOM ▼]`
   - ✅ CUSTOM option has separator line (border-top)
   - ✅ CUSTOM option has visual distinction

3. **Expand Advanced Settings**
   - Click `[▶ ADVANCED]` if not already expanded
   - Label should show: "CUSTOM SYSTEM PROMPT:"

4. **Verify Textarea**
   - Should see editable textarea (NOT read-only preview box)
   - Placeholder text: "Enter custom system prompt..."
   - Height: ~120px (6 rows)
   - Resizable vertically

5. **Type Custom Prompt**
   - Click in textarea
   - Type: "You are an expert TypeScript developer..."
   - ✅ Text appears in phosphor orange color
   - ✅ Monospace font
   - ✅ Border glows orange on focus

6. **Test Submission**
   - Keep CUSTOM selected
   - Enter query in main textarea: "Help me debug this code"
   - Click EXECUTE
   - Backend should receive customSystemPrompt field in request

### Visual Reference (CUSTOM Selected)
```
[◆ CUSTOM ▼]  [▶ ADVANCED]  [EXECUTE]

▼ ADVANCED SETTINGS
┌─────────────────────────────────────────────────┐
│ CUSTOM SYSTEM PROMPT:                           │
│ ┌─────────────────────────────────────────────┐ │
│ │ You are an expert TypeScript developer...  │ │ ← Editable
│ │ [user can type here]                        │ │
│ │                                             │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ MAX TOKENS: 512        TEMPERATURE: 0.70        │
└─────────────────────────────────────────────────┘
```

### Keyboard Shortcut Test
- Press `U` key (anywhere on page, not in input field)
- Should immediately switch to CUSTOM preset
- Advanced section should update to show textarea

---

## Keyboard Shortcuts Testing

Test all preset shortcuts work correctly.

### Shortcuts Map
- `D` → SYNAPSE_DEFAULT
- `A` → SYNAPSE_ANALYST
- `C` → SYNAPSE_CODER
- `V` → SYNAPSE_CREATIVE
- `R` → SYNAPSE_RESEARCH
- `J` → SYNAPSE_JUDGE
- `U` → CUSTOM

### Steps to Test

1. **Test Each Shortcut**
   - Press `D` - Button should show DEFAULT
   - Press `A` - Button should show ANALYST
   - Press `C` - Button should show CODER
   - Press `V` - Button should show CREATIVE
   - Press `R` - Button should show RESEARCH
   - Press `J` - Button should show JUDGE
   - Press `U` - Button should show CUSTOM

2. **Test Shortcut Blocking in Inputs**
   - Click in main query textarea
   - Type "D" - should type 'D' in textarea, NOT switch preset
   - Same for CUSTOM textarea when CUSTOM selected

3. **Test Escape to Close**
   - Open dropdown
   - Press ESC key
   - ✅ Dropdown should close

---

## Responsive Testing

Test on different screen sizes.

### Desktop (>768px)
- ✅ Dropdown min-width 180px
- ✅ Advanced section uses 2-column grid for sliders
- ✅ System prompt section full width

### Mobile (<768px)
- ✅ Dropdown min-width 160px
- ✅ Advanced section uses 1-column layout
- ✅ All elements stack vertically

### Test Steps
1. Open browser DevTools (F12)
2. Click device emulation icon
3. Select iPhone 12 Pro
4. Verify layout stacks correctly
5. Test dropdown still works

---

## Edge Cases Testing

### Empty Custom Prompt
1. Select CUSTOM
2. Leave textarea empty
3. Submit query
4. Backend should receive empty string (not null/undefined)

### Very Long System Prompt
1. If testing with actual system_prompt values
2. Add a very long prompt (>500 characters)
3. Preview should show scrollbar
4. Max height should be ~120px

### Rapid Preset Switching
1. Click dropdown
2. Click ANALYST
3. Immediately click dropdown again
4. Click CODER
5. Repeat rapidly
6. Should not cause errors or visual glitches

### Network Error
1. Stop backend: `docker-compose stop synapse_core`
2. Try to load page
3. Preset selector should still render
4. May show loading state or cached data

---

## Browser Compatibility

Test in multiple browsers:

### Chrome/Edge (Chromium)
- ✅ All features work
- ✅ Portal rendering correct
- ✅ Animations smooth

### Firefox
- ✅ All features work
- ✅ Portal rendering correct
- ✅ Scrollbars styled correctly

### Safari
- ✅ All features work
- ✅ Portal rendering correct
- ✅ Webkit-specific styles applied

---

## Accessibility Testing

### Screen Reader
1. Enable VoiceOver (Mac) or NVDA (Windows)
2. Tab to preset dropdown
3. Should announce: "DEFAULT, button, has popup"
4. Open dropdown
5. Should announce: "listbox"
6. Arrow through options
7. Should announce each preset name and selected state

### Keyboard Navigation
1. Tab through all controls
2. Should be able to reach:
   - Query textarea
   - CGRAG checkbox
   - WEB SEARCH checkbox
   - Preset dropdown
   - ADVANCED button
   - EXECUTE button
3. All interactive elements should have visible focus ring

### Color Contrast
1. Use browser extension (e.g., axe DevTools)
2. Check contrast ratios
3. All text should meet WCAG AA standards
4. Phosphor orange (#ff9500) on black should pass

---

## Performance Testing

### Portal Re-rendering
1. Open browser DevTools
2. Go to Performance tab
3. Start recording
4. Open/close dropdown 10 times rapidly
5. Stop recording
6. Check for:
   - ✅ No memory leaks
   - ✅ No layout thrashing
   - ✅ 60fps maintained

### Large Prompt Rendering
1. Add 10KB system prompt to preset
2. Open Advanced section
3. Check rendering time
4. Should be <50ms

---

## Integration Testing

### With Query Submission

**Test 1: Built-in Preset**
1. Select SYNAPSE_ANALYST
2. Enter query: "Analyze this data"
3. Submit
4. Check network tab (DevTools)
5. Request should include: `presetId: "SYNAPSE_ANALYST"`

**Test 2: Custom Preset**
1. Select CUSTOM
2. Enter custom prompt: "You are an expert in X"
3. Enter query: "Help with Y"
4. Submit
5. Request should include:
   - `presetId: undefined` (or not present)
   - `customSystemPrompt: "You are an expert in X"`

**Test 3: Switching Presets Mid-Session**
1. Start with DEFAULT
2. Submit query
3. Switch to CUSTOM
4. Submit another query
5. Verify each request has correct preset/custom prompt

---

## Visual Regression Testing

Compare screenshots before/after:

### Screenshot Locations
1. Query Input (collapsed)
2. Query Input (advanced expanded, DEFAULT selected)
3. Query Input (advanced expanded, CUSTOM selected)
4. Dropdown menu (open)
5. Dropdown menu (CUSTOM option highlighted)

### Expected Changes
- Advanced section layout changed (vertical stack)
- New system prompt preview/textarea area
- CUSTOM option in dropdown with separator

### No Changes Expected
- Main query textarea
- Checkboxes
- Sliders
- Execute button

---

## Known Issues / Limitations

### Not Implemented Yet
1. System prompt validation
2. Custom prompt persistence (localStorage)
3. Character/token counter for prompts
4. Prompt templates/library

### Expected Behavior
1. Built-in presets show "No system prompt defined" until backend adds prompts
2. Custom prompts lost on page refresh (no persistence)
3. Empty custom prompts are allowed (no validation)

---

## Troubleshooting

### Dropdown Not Appearing
- Check browser console for errors
- Verify Portal is rendering to document.body
- Check z-index conflicts (should be 10000)

### System Prompt Not Showing
- Verify preset has `system_prompt` field in backend
- Check network response in DevTools
- Verify transformation in usePresets hook

### Custom Textarea Not Editable
- Check if loading/disabled state is active
- Verify isCustomPreset logic
- Check textarea disabled attribute

### Keyboard Shortcuts Not Working
- Verify you're not focused in an input field
- Check browser console for errors
- Test in different browser

---

## Success Criteria

All features passing when:

- ✅ Dropdown renders via portal above all elements
- ✅ Dropdown not clipped by parent containers
- ✅ System prompt preview shows for presets with prompts
- ✅ "No system prompt defined" shows for presets without prompts
- ✅ CUSTOM option appears in dropdown with separator
- ✅ Custom textarea appears when CUSTOM selected
- ✅ Custom prompt is editable
- ✅ All keyboard shortcuts work (D/A/C/V/R/J/U)
- ✅ Clicking outside closes dropdown
- ✅ Terminal aesthetic maintained
- ✅ No console errors
- ✅ Accessible to screen readers
- ✅ Works in Chrome, Firefox, Safari
- ✅ Responsive on mobile devices

---

## Next Steps After Testing

1. **Add System Prompts to Built-in Presets**
   - Edit `backend/app/models/code_chat.py`
   - Add `system_prompt` values to each preset
   - Restart backend: `docker-compose restart synapse_core`

2. **Add Custom Prompt Persistence**
   - Implement localStorage for custom prompts
   - Add "Save as Preset" button
   - Add preset management UI

3. **Enhance UX**
   - Add prompt character counter
   - Add prompt templates
   - Add syntax highlighting for prompts

---

## Report Issues

If you find any issues during testing, document:

1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Browser/OS**
5. **Screenshots** (if visual issue)
6. **Console errors** (if any)

Create an issue in the project repository or update SESSION_NOTES.md with findings.

---

**Testing Complete ✓**

Frontend is ready for testing at: http://localhost:5173
