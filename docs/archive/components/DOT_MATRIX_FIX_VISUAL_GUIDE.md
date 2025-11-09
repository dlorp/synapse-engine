# Dot Matrix Animation Restart Bug - Visual Guide

This visual guide uses ASCII diagrams to explain the bug and fix.

---

## Timeline: Before Fix (Buggy Behavior)

```
Time (ms)  Animation State         React State              Problem
─────────────────────────────────────────────────────────────────────
0          S                       HomePage mounts
           ▓░░░░░░░░░░░░░░         reactive = {new obj}

100        SY                      First debounced update
           ▓▓░░░░░░░░░░░░

500        SYNAP                   React Query updates
           ▓▓▓▓▓░░░░░░░░           HomePage re-renders
                                   reactive = {new obj}    ← NEW REFERENCE!

600        S                       Debounced update triggers
           ▓░░░░░░░░░░░░░          Animation RESTARTS       ❌ BUG!

1000       SYNA                    React Query updates again
           ▓▓▓▓░░░░░░░░            HomePage re-renders
                                   reactive = {new obj}    ← NEW REFERENCE!

1100       S                       Debounced update triggers
           ▓░░░░░░░░░░░░░          Animation RESTARTS AGAIN ❌ BUG!
```

**User Experience:** Frustrating, unprofessional, animation never completes

---

## Timeline: After Fix (Correct Behavior)

```
Time (ms)  Animation State         React State              Fix
─────────────────────────────────────────────────────────────────────
0          S                       HomePage mounts
           ▓░░░░░░░░░░░░░░         reactive = useMemo {obj}

100        SY                      First debounced update
           ▓▓░░░░░░░░░░░░

500        SYNAP                   React Query updates
           ▓▓▓▓▓░░░░░░░░           HomePage re-renders
                                   reactive = SAME {obj}   ✅ Same reference!

600        SYNAPPS                 No useEffect trigger
           ▓▓▓▓▓▓▓░░░░░░           Animation continues     ✅ Smooth!

1000       SYNAPSE EN              React Query updates again
           ▓▓▓▓▓▓▓▓▓▓░░           HomePage re-renders
                                   reactive = SAME {obj}   ✅ Same reference!

1400       SYNAPSE ENGINE          Animation completes
           ▓▓▓▓▓▓▓▓▓▓▓▓▓▓          No restarts             ✅ Perfect!
```

**User Experience:** Smooth, professional, animation completes as expected

---

## React Render Flow: Before Fix

```
┌─────────────────────────────────────────────────────────────────┐
│                         HomePage Component                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Render #1 (t=0ms)                                              │
│  ┌────────────────────────────────────┐                         │
│  │ reactive = {                       │  New object created     │
│  │   enabled: true,                   │  Memory: 0x1234         │
│  │   isProcessing: false,             │                         │
│  │   hasError: false                  │                         │
│  │ }                                  │                         │
│  └────────────────────────────────────┘                         │
│                    │                                             │
│                    ▼                                             │
│         Pass to DotMatrixDisplay                                │
│                    │                                             │
│  ┌─────────────────┴──────────────────┐                         │
│  │ useEffect([reactive]) triggers     │                         │
│  │ → Animation starts                 │                         │
│  └────────────────────────────────────┘                         │
│                                                                  │
│  Render #2 (t=500ms - React Query update)                       │
│  ┌────────────────────────────────────┐                         │
│  │ reactive = {                       │  NEW object created     │
│  │   enabled: true,                   │  Memory: 0x5678  ← DIFFERENT!
│  │   isProcessing: false,  (SAME!)   │                         │
│  │   hasError: false       (SAME!)   │                         │
│  │ }                                  │                         │
│  └────────────────────────────────────┘                         │
│                    │                                             │
│                    ▼                                             │
│         Pass to DotMatrixDisplay                                │
│                    │                                             │
│  ┌─────────────────┴──────────────────┐                         │
│  │ useEffect([reactive]) triggers     │  ❌ BUG!                │
│  │ → Animation RESTARTS               │  Reference changed!     │
│  └────────────────────────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Problem:** `0x1234 !== 0x5678` even though values are identical!

---

## React Render Flow: After Fix (useMemo)

```
┌─────────────────────────────────────────────────────────────────┐
│                         HomePage Component                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Render #1 (t=0ms)                                              │
│  ┌────────────────────────────────────┐                         │
│  │ const reactive = useMemo(          │                         │
│  │   () => ({                         │  New object created     │
│  │     enabled: true,                 │  Memory: 0x1234         │
│  │     isProcessing: false,           │  CACHED by useMemo      │
│  │     hasError: false                │                         │
│  │   }),                              │                         │
│  │   [false, false]  ← dependencies   │                         │
│  │ )                                  │                         │
│  └────────────────────────────────────┘                         │
│                    │                                             │
│                    ▼                                             │
│         Pass to DotMatrixDisplay                                │
│                    │                                             │
│  ┌─────────────────┴──────────────────┐                         │
│  │ useEffect([reactive]) triggers     │                         │
│  │ → Animation starts                 │                         │
│  └────────────────────────────────────┘                         │
│                                                                  │
│  Render #2 (t=500ms - React Query update)                       │
│  ┌────────────────────────────────────┐                         │
│  │ const reactive = useMemo(          │                         │
│  │   () => ({ ... }),                 │  useMemo checks deps:   │
│  │   [false, false]  ← SAME!          │  [false, false]         │
│  │ )                                  │  → Return CACHED object │
│  │                                    │  Memory: 0x1234  ← SAME!│
│  │ // Returns cached object           │                         │
│  └────────────────────────────────────┘                         │
│                    │                                             │
│                    ▼                                             │
│         Pass to DotMatrixDisplay                                │
│                    │                                             │
│  ┌─────────────────┴──────────────────┐                         │
│  │ useEffect([reactive]) NO TRIGGER   │  ✅ FIXED!              │
│  │ → Animation continues smoothly     │  Same reference!        │
│  └────────────────────────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Solution:** `0x1234 === 0x1234` - useMemo returns cached object!

---

## State Transition: Query Submission

### Before Fix (Buggy)
```
┌──────────────┐  Submit Query   ┌──────────────┐
│ IDLE         │  (t=1000ms)     │ PROCESSING   │
│ isPending: ● │ ─────────────▶  │ isPending: ● │
│ hasError:  ○ │                 │ hasError:  ○ │
│              │                 │              │
│ reactive =   │                 │ reactive =   │
│ {new obj}    │                 │ {new obj}    │  ❌ Different reference!
│ 0x1234       │                 │ 0x5678       │
│              │                 │              │
│ Animation:   │                 │ Animation:   │
│ SYNAP▓▓░░    │                 │ S▓░░░░░░░    │  ❌ RESTARTED!
└──────────────┘                 └──────────────┘
```

### After Fix (Correct)
```
┌──────────────┐  Submit Query   ┌──────────────┐
│ IDLE         │  (t=1000ms)     │ PROCESSING   │
│ isPending: ○ │ ─────────────▶  │ isPending: ● │  ← Dependency changed!
│ hasError:  ○ │                 │ hasError:  ○ │
│              │                 │              │
│ reactive =   │                 │ reactive =   │
│ useMemo {obj}│                 │ useMemo {obj}│  ✅ New object (expected!)
│ 0x1234       │                 │ 0x9ABC       │
│              │                 │              │
│ Animation:   │                 │ Animation:   │
│ SYNAP▓▓░░    │                 │ SYNAPSE ▓▓░  │  ✅ CONTINUES!
│              │                 │ + blink      │  ✅ Effect added smoothly
└──────────────┘                 └──────────────┘
```

**Key Difference:** When isPending actually changes, useMemo creates new object (correct behavior)

---

## JavaScript Reference Equality Visualization

### Primitives (Value Equality)
```
┌─────────┐     ┌─────────┐
│ a = 5   │     │ b = 5   │
└─────────┘     └─────────┘
     │               │
     └───────┬───────┘
             │
       a === b → TRUE ✅
       (Same value)
```

### Objects (Reference Equality)
```
┌──────────────┐     ┌──────────────┐
│ obj1 = {x:1} │     │ obj2 = {x:1} │
│ @0x1234      │     │ @0x5678      │  Different memory addresses!
└──────────────┘     └──────────────┘
       │                   │
       └────────┬──────────┘
                │
       obj1 === obj2 → FALSE ❌
       (Different references, even though values same!)


┌──────────────┐
│ obj3 = obj1  │     Same reference!
│ @0x1234      │
└──────────────┘
       │
       │ obj1 ─────────┐
       └────────┬──────┘
                │
       obj1 === obj3 → TRUE ✅
       (Same reference)
```

---

## useMemo Dependency Tracking

### Dependencies Unchanged (Cache Hit)
```
Render #1: useMemo(() => ({x: 1}), [false, false])
           ┌────────────────────────────────────┐
           │ Calculate: {x: 1}                  │
           │ Store: cache[0x1234] = {x: 1}      │
           │ deps: [false, false]               │
           └────────────────────────────────────┘
           Return: 0x1234


Render #2: useMemo(() => ({x: 1}), [false, false])
           ┌────────────────────────────────────┐
           │ Check deps: [false, false]         │
           │ deps === prevDeps? YES ✅          │
           │ Return cached: 0x1234              │  ← Same reference!
           └────────────────────────────────────┘
           Return: 0x1234
```

### Dependencies Changed (Cache Miss)
```
Render #1: useMemo(() => ({x: 1}), [false, false])
           ┌────────────────────────────────────┐
           │ Calculate: {x: 1}                  │
           │ Store: cache[0x1234] = {x: 1}      │
           │ deps: [false, false]               │
           └────────────────────────────────────┘
           Return: 0x1234


Render #2: useMemo(() => ({x: 1}), [true, false])   ← Changed!
           ┌────────────────────────────────────┐
           │ Check deps: [true, false]          │
           │ deps === prevDeps? NO ❌           │
           │ Recalculate: {x: 1}                │
           │ Store: cache[0x5678] = {x: 1}      │  ← New reference!
           │ deps: [true, false]                │
           └────────────────────────────────────┘
           Return: 0x5678
```

---

## Component Communication Flow

### Before Fix (Multiple Triggers)
```
┌────────────────┐                    ┌──────────────────────┐
│   HomePage     │                    │  DotMatrixDisplay    │
├────────────────┤                    ├──────────────────────┤
│                │                    │                      │
│ Re-render      │  reactive={...}    │ useEffect([reactive])│
│ (t=500ms)      │ ─────────────────▶ │ Detects change       │
│ New object!    │  New reference!    │ Triggers update      │
│                │                    │ → Restart animation  │
│                │                    │                      │
│ Re-render      │  reactive={...}    │ useEffect([reactive])│
│ (t=1000ms)     │ ─────────────────▶ │ Detects change       │
│ New object!    │  New reference!    │ Triggers update      │
│                │                    │ → Restart animation  │
│                │                    │                      │
└────────────────┘                    └──────────────────────┘
     ❌ Too many triggers!                  ❌ Too many restarts!
```

### After Fix (Selective Triggers)
```
┌────────────────┐                    ┌──────────────────────┐
│   HomePage     │                    │  DotMatrixDisplay    │
├────────────────┤                    ├──────────────────────┤
│                │                    │                      │
│ Re-render      │  reactive={memo}   │ useEffect([reactive])│
│ (t=500ms)      │ ─────────────────▶ │ Same reference       │
│ Same object!   │  Same reference!   │ NO TRIGGER ✅        │
│                │                    │ → Animation continues│
│                │                    │                      │
│ Re-render      │  reactive={memo}   │ useEffect([reactive])│
│ (t=1000ms)     │ ─────────────────▶ │ isPending changed!   │
│ New object!    │  New reference!    │ Triggers update      │
│ (deps changed) │                    │ → Add blink effect   │
│                │                    │                      │
└────────────────┘                    └──────────────────────┘
     ✅ Only when needed!                   ✅ Smooth transitions!
```

---

## Code Comparison: Side by Side

### Before Fix (Buggy)
```typescript
export const HomePage: React.FC = () => {
  const queryMutation = useQuerySubmit();

  return (
    <DotMatrixDisplay
      text="SYNAPSE ENGINE"
      pattern="wave"
      effects={['blink', 'pulsate']}
      reactive={{
        // ❌ NEW OBJECT EVERY RENDER!
        enabled: true,
        isProcessing: queryMutation.isPending,
        hasError: queryMutation.isError,
      }}
    />
  );
};
```
**Problem:** `reactive={{...}}` creates new object on every render

---

### After Fix (Correct)
```typescript
import { useMemo } from 'react';

export const HomePage: React.FC = () => {
  const queryMutation = useQuerySubmit();

  // ✅ MEMOIZED - Same reference when deps unchanged
  const dotMatrixReactive = useMemo(
    () => ({
      enabled: true,
      isProcessing: queryMutation.isPending,
      hasError: queryMutation.isError,
    }),
    [queryMutation.isPending, queryMutation.isError]
    // ↑ Only create new object when these change
  );

  return (
    <DotMatrixDisplay
      text="SYNAPSE ENGINE"
      pattern="wave"
      reactive={dotMatrixReactive}
      // ✅ Stable reference!
    />
  );
};
```
**Solution:** useMemo provides reference stability

---

## Summary: The Fix in One Diagram

```
╔══════════════════════════════════════════════════════════════════╗
║                   DOT MATRIX ANIMATION RESTART BUG               ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  BEFORE:  reactive={{...}}  →  New object every render          ║
║           ───────────────────────────────────────────────        ║
║           HomePage re-renders                                    ║
║                    ↓                                             ║
║           New reactive object (different reference)              ║
║                    ↓                                             ║
║           useEffect([reactive]) triggers                         ║
║                    ↓                                             ║
║           Animation restarts  ❌                                 ║
║                                                                  ║
║  ─────────────────────────────────────────────────────────────   ║
║                                                                  ║
║  AFTER:   reactive = useMemo(...)  →  Cached object             ║
║           ───────────────────────────────────────────────        ║
║           HomePage re-renders                                    ║
║                    ↓                                             ║
║           useMemo checks dependencies                            ║
║                    ↓                                             ║
║           Dependencies unchanged? Return cached object           ║
║                    ↓                                             ║
║           Same reference → useEffect DOESN'T trigger             ║
║                    ↓                                             ║
║           Animation continues smoothly  ✅                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Key Takeaway

**Always memoize objects and arrays passed as props or in useEffect dependencies!**

```typescript
// ❌ BAD - Restarts animation
<Component config={{x: 1}} />

// ✅ GOOD - Stable reference
const config = useMemo(() => ({x: 1}), []);
<Component config={config} />
```

---

**This visual guide demonstrates how a simple 3-line change (useMemo) fixes a critical UX bug by understanding React's reference equality and re-render behavior.**
