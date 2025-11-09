 # S.Y.N.A.P.S.E. ENGINE - Dot Matrix Effects Implementation Guide

**Date:** 2025-11-09
**Status:** Implementation Plan
**Estimated Time:** 12-16 hours across multiple phases

---

## Executive Summary

Transform the S.Y.N.A.P.S.E. ENGINE interface into a dense, information-rich terminal webui by implementing comprehensive dot matrix effects and advanced terminal animations across all components and pages.

**Vision:** Create a cohesive NERV/technical interface aesthetic that enhances information density, improves visual hierarchy through glow effects, and makes real-time data updates feel more immediate and responsive while maintaining 60fps performance.

### Available Effect Categories

**25+ Terminal Effects Organized by Category:**

| Category | Effects | Use Cases |
|----------|---------|-----------|
| **Grid Patterns** | dot-matrix-bg (3 densities), animated grid | Background texture, data density |
| **Scan Lines** | animated (3 speeds), static horizontal | CRT authenticity, active processing |
| **Phosphor Glow** | text glow (3 colors × 2 modes), border glow (3 colors) | Emphasis, state indication, hierarchy |
| **CRT Effects** | screen curvature, vignette, flicker | Retro aesthetic, depth |
| **Glitch** | horizontal, vertical, severe combination | Errors, warnings, instability |
| **Signal Interference** | static noise, interlacing, screen tear | Loading, connection issues |
| **Chromatic Effects** | RGB split, VHS tracking, phosphor burn-in | Emphasis, corruption, retro |
| **Typography** | teletype (3 speeds), terminal cursor, hex display | Streaming text, code, data |
| **Animations** | matrix rain, boot sequence, EMP wave, data stream | Ambiance, initialization, events |
| **Distortion** | bit shift, data corruption, phosphor trail | Instability, transitions |

**Key Features:**
- ✅ **Composable** - Combine 2-3 effects for maximum impact
- ✅ **Configurable** - 15+ props per component for granular control
- ✅ **Performant** - GPU-accelerated, <5ms overhead, 60fps target
- ✅ **Accessible** - Full `prefers-reduced-motion` support
- ✅ **State-Aware** - Different effects for error/warning/success/active states
- ✅ **Responsive** - Works across screen sizes and resolutions

---

## Current State Analysis

### Existing Visual Effects Foundation

**Location:** `frontend/src/assets/styles/animations.css`

**Already Implemented:**
- ✅ Scan line effect (8s linear infinite)
- ✅ Glow animation (2s ease-in-out infinite)
- ✅ Flicker effect (3s linear infinite for glitch)
- ✅ Border glow animation (2s ease-in-out infinite)
- ✅ Pulse, blink, fade, slide, spin animations
- ✅ Progress bar fill animation

**Color Palette (from `tokens.css`):**
- Primary: `#ff9500` (phosphor orange)
- Accent: `#00ffff` (cyan)
- Error: `#ff0000` (red)
- Dark backgrounds: `#000000`, `#0a0a0a`

**Key Insight:** The foundation exists, but effects are underutilized. No systematic application across the UI. Need unified dot matrix effect system.

---

## Codebase Structure

### Terminal Components
**Location:** `frontend/src/components/terminal/`

Existing components that will benefit from effects:
- `Panel/` - Container with border styling (foundation for effects)
- `Button/` - Interactive element
- `Input/` - Text input field
- `ProgressBar/` - Progress visualization
- `StatusIndicator/` - Status display (already has pulsing)
- `MetricDisplay/` - Value + unit display
- `Divider/` - Visual separator

### Pages Using Terminal Components
1. **HomePage** (`frontend/src/pages/HomePage/HomePage.tsx`)
   - Query interface, model status, quick actions

2. **MetricsPage** (`frontend/src/pages/MetricsPage/MetricsPage.tsx`)
   - Performance metrics, resource utilization
   - Currently uses 4 Panel components

3. **ModelManagementPage** (`frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx`)
   - Model registry, tier allocation, server logs
   - Uses 5+ Panel components with various variants

4. **SettingsPage** (`frontend/src/pages/SettingsPage/SettingsPage.tsx`)
   - Configuration interface

5. **AdminPage** (`frontend/src/pages/AdminPage/AdminPage.tsx`)
   - Administration interface

---

## Implementation Plan

### Phase 1: Core Effect System (4-6 hours)

#### 1.1 Enhance `animations.css`

**File:** `frontend/src/assets/styles/animations.css`

**Add after existing animations (line 213):**

```css
/* =================================================================
   DOT MATRIX EFFECTS
   ================================================================= */

/* Dot Matrix Grid Background Pattern */
.dot-matrix-bg {
  background-image: radial-gradient(
    circle at center,
    var(--text-primary) 0.5px,
    transparent 0.5px
  );
  background-size: 4px 4px;
  background-position: 0 0;
  opacity: 0.15;
}

.dot-matrix-bg-dense {
  background-image: radial-gradient(
    circle at center,
    var(--text-primary) 0.5px,
    transparent 0.5px
  );
  background-size: 2px 2px;
  background-position: 0 0;
  opacity: 0.2;
}

.dot-matrix-bg-sparse {
  background-image: radial-gradient(
    circle at center,
    var(--text-primary) 0.5px,
    transparent 0.5px
  );
  background-size: 8px 8px;
  background-position: 0 0;
  opacity: 0.1;
}

/* Animated Dot Matrix Grid */
@keyframes dot-matrix-pulse {
  0%, 100% { opacity: 0.15; }
  50% { opacity: 0.25; }
}

.dot-matrix-bg-animated {
  background-image: radial-gradient(
    circle at center,
    var(--text-primary) 0.5px,
    transparent 0.5px
  );
  background-size: 4px 4px;
  background-position: 0 0;
  animation: dot-matrix-pulse 4s ease-in-out infinite;
}

/* Enhanced Scan Line Variants */
.scan-line-fast {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(
    to bottom,
    transparent,
    var(--text-primary) 50%,
    transparent
  );
  opacity: 0.15;
  pointer-events: none;
  animation: scan-line 4s linear infinite;
}

.scan-line-slow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(
    to bottom,
    transparent,
    var(--text-primary) 50%,
    transparent
  );
  opacity: 0.2;
  pointer-events: none;
  animation: scan-line 12s linear infinite;
}

.scan-line-thick {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(
    to bottom,
    transparent,
    var(--text-primary) 30%,
    var(--text-primary) 70%,
    transparent
  );
  opacity: 0.25;
  pointer-events: none;
  animation: scan-line 8s linear infinite;
}

/* Horizontal Scan Lines (static) */
.scan-lines-static {
  position: relative;
}

.scan-lines-static::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(255, 149, 0, 0.03) 2px,
    rgba(255, 149, 0, 0.03) 4px
  );
  pointer-events: none;
  z-index: 1;
}

/* Phosphor Glow Presets */
@keyframes phosphor-glow-orange {
  0%, 100% {
    text-shadow: 0 0 4px var(--text-primary), 0 0 8px var(--text-primary);
  }
  50% {
    text-shadow: 0 0 8px var(--text-primary), 0 0 16px var(--text-primary),
      0 0 24px var(--text-primary);
  }
}

@keyframes phosphor-glow-cyan {
  0%, 100% {
    text-shadow: 0 0 4px var(--text-accent), 0 0 8px var(--text-accent);
  }
  50% {
    text-shadow: 0 0 8px var(--text-accent), 0 0 16px var(--text-accent),
      0 0 24px var(--text-accent);
  }
}

@keyframes phosphor-glow-red {
  0%, 100% {
    text-shadow: 0 0 4px var(--text-error), 0 0 8px var(--text-error);
  }
  50% {
    text-shadow: 0 0 8px var(--text-error), 0 0 16px var(--text-error),
      0 0 24px var(--text-error);
  }
}

.phosphor-glow-orange {
  animation: phosphor-glow-orange 2s ease-in-out infinite;
}

.phosphor-glow-cyan {
  animation: phosphor-glow-cyan 2s ease-in-out infinite;
}

.phosphor-glow-red {
  animation: phosphor-glow-red 2s ease-in-out infinite;
}

/* Static Phosphor Glow (no animation) */
.phosphor-glow-static-orange {
  text-shadow: 0 0 4px var(--text-primary), 0 0 8px var(--text-primary);
}

.phosphor-glow-static-cyan {
  text-shadow: 0 0 4px var(--text-accent), 0 0 8px var(--text-accent);
}

.phosphor-glow-static-red {
  text-shadow: 0 0 4px var(--text-error), 0 0 8px var(--text-error);
}

/* CRT Screen Effects */
.crt-screen {
  position: relative;
  overflow: hidden;
}

/* CRT Vignette Effect */
.crt-screen::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(
    ellipse at center,
    transparent 0%,
    transparent 60%,
    rgba(0, 0, 0, 0.3) 100%
  );
  pointer-events: none;
  z-index: var(--z-overlay);
}

/* CRT Flicker */
@keyframes crt-flicker {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.98; }
}

.crt-flicker {
  animation: crt-flicker 0.15s infinite;
}

/* Border Glow Variants */
@keyframes border-glow-orange {
  0%, 100% {
    border-color: var(--border-primary);
    box-shadow: 0 0 4px var(--text-primary);
  }
  50% {
    border-color: var(--text-primary);
    box-shadow: 0 0 12px var(--text-primary), 0 0 24px var(--text-primary);
  }
}

@keyframes border-glow-cyan {
  0%, 100% {
    border-color: var(--border-primary);
    box-shadow: 0 0 4px var(--text-accent);
  }
  50% {
    border-color: var(--text-accent);
    box-shadow: 0 0 12px var(--text-accent), 0 0 24px var(--text-accent);
  }
}

@keyframes border-glow-red {
  0%, 100% {
    border-color: var(--border-primary);
    box-shadow: 0 0 4px var(--text-error);
  }
  50% {
    border-color: var(--text-error);
    box-shadow: 0 0 12px var(--text-error), 0 0 24px var(--text-error);
  }
}

.border-glow-orange {
  animation: border-glow-orange 2s ease-in-out infinite;
}

.border-glow-cyan {
  animation: border-glow-cyan 2s ease-in-out infinite;
}

.border-glow-red {
  animation: border-glow-red 2s ease-in-out infinite;
}

/* Enhanced Flicker for Critical States */
@keyframes flicker-intense {
  0%, 100% { opacity: 1; }
  10% { opacity: 0.1; }
  20% { opacity: 1; }
  30% { opacity: 0.3; }
  40% { opacity: 1; }
  50% { opacity: 0.2; }
  60% { opacity: 1; }
  70% { opacity: 0.4; }
  80% { opacity: 1; }
}

.flicker-intense {
  animation: flicker-intense 0.5s linear infinite;
}

/* Scan Line Sweep (for transitions) */
@keyframes scan-sweep {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}

.scan-sweep {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 20%;
  background: linear-gradient(
    to bottom,
    transparent,
    var(--text-primary) 50%,
    transparent
  );
  opacity: 0.3;
  pointer-events: none;
  animation: scan-sweep 1s ease-out;
}

/* Grid Expand Animation */
@keyframes grid-expand {
  0% {
    background-size: 2px 2px;
    opacity: 0.1;
  }
  100% {
    background-size: 8px 8px;
    opacity: 0.3;
  }
}

.grid-expand {
  background-image: radial-gradient(
    circle at center,
    var(--text-primary) 0.5px,
    transparent 0.5px
  );
  animation: grid-expand 0.5s ease-out forwards;
}

/* Phosphor Trail Effect */
@keyframes phosphor-trail {
  0% {
    opacity: 1;
    filter: blur(0);
  }
  100% {
    opacity: 0;
    filter: blur(4px);
  }
}

.phosphor-trail {
  animation: phosphor-trail 0.5s ease-out forwards;
}

/* Data Stream Effect */
@keyframes data-stream {
  0% {
    transform: translateY(-20px);
    opacity: 0;
  }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% {
    transform: translateY(20px);
    opacity: 0;
  }
}

.data-stream {
  animation: data-stream 2s linear infinite;
}

/* =================================================================
   ADVANCED TERMINAL EFFECTS
   ================================================================= */

/* Glitch Effects - Digital Corruption */
@keyframes glitch-horizontal {
  0%, 100% {
    transform: translateX(0);
  }
  10% {
    transform: translateX(-5px);
  }
  20% {
    transform: translateX(5px);
  }
  30% {
    transform: translateX(-3px);
  }
  40% {
    transform: translateX(3px);
  }
  50% {
    transform: translateX(0);
  }
}

@keyframes glitch-vertical {
  0%, 100% {
    clip-path: inset(0 0 0 0);
  }
  20% {
    clip-path: inset(10% 0 85% 0);
  }
  40% {
    clip-path: inset(60% 0 25% 0);
  }
  60% {
    clip-path: inset(30% 0 50% 0);
  }
  80% {
    clip-path: inset(80% 0 10% 0);
  }
}

.glitch {
  animation: glitch-horizontal 0.3s linear infinite;
}

.glitch-severe {
  animation: glitch-horizontal 0.15s linear infinite,
    glitch-vertical 0.2s linear infinite;
}

/* Chromatic Aberration - RGB Split */
.chromatic-aberration {
  position: relative;
  color: var(--text-primary);
}

.chromatic-aberration::before,
.chromatic-aberration::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  mix-blend-mode: screen;
}

.chromatic-aberration::before {
  color: #ff0000;
  transform: translateX(-2px);
  opacity: 0.7;
}

.chromatic-aberration::after {
  color: #00ffff;
  transform: translateX(2px);
  opacity: 0.7;
}

/* Screen Tearing Effect */
@keyframes screen-tear {
  0%, 100% {
    transform: translateX(0);
  }
  10% {
    transform: translateX(-10px);
  }
  20% {
    transform: translateX(10px);
  }
  30% {
    transform: translateX(-5px);
  }
  40% {
    transform: translateX(5px);
  }
  50% {
    transform: translateX(0);
  }
}

.screen-tear {
  position: relative;
}

.screen-tear::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--text-primary);
  opacity: 0.3;
  animation: screen-tear 0.2s linear infinite;
}

/* Interlacing Effect */
.interlaced {
  position: relative;
}

.interlaced::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 1px,
    rgba(0, 0, 0, 0.3) 1px,
    rgba(0, 0, 0, 0.3) 2px
  );
  pointer-events: none;
  z-index: 1;
}

/* Signal Interference - Static Noise */
@keyframes static-noise {
  0%, 100% {
    background-position: 0 0;
  }
  10% {
    background-position: -5% -10%;
  }
  20% {
    background-position: -15% 5%;
  }
  30% {
    background-position: 7% -25%;
  }
  40% {
    background-position: 20% 25%;
  }
  50% {
    background-position: -25% 10%;
  }
  60% {
    background-position: 15% -20%;
  }
  70% {
    background-position: -10% 15%;
  }
  80% {
    background-position: 25% -5%;
  }
  90% {
    background-position: -20% -15%;
  }
}

.static-noise {
  position: relative;
}

.static-noise::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJhIj48ZmVUdXJidWxlbmNlIGJhc2VGcmVxdWVuY3k9Ii43NSIgc3RpdGNoVGlsZXM9InN0aXRjaCIgdHlwZT0iZnJhY3RhbE5vaXNlIi8+PGZlQ29sb3JNYXRyaXggdHlwZT0ic2F0dXJhdGUiIHZhbHVlcz0iMCIvPjwvZmlsdGVyPjxwYXRoIGQ9Ik0wIDBoMzAwdjMwMEgweiIgZmlsdGVyPSJ1cmwoI2EpIiBvcGFjaXR5PSIuMDUiLz48L3N2Zz4=');
  background-size: 100px 100px;
  opacity: 0.1;
  animation: static-noise 0.2s steps(10) infinite;
  pointer-events: none;
  z-index: 1;
}

/* Teletype/Typing Effect */
@keyframes typing {
  from {
    width: 0;
  }
  to {
    width: 100%;
  }
}

.teletype {
  overflow: hidden;
  white-space: nowrap;
  animation: typing 2s steps(40) 1s forwards;
  width: 0;
}

.teletype-fast {
  overflow: hidden;
  white-space: nowrap;
  animation: typing 1s steps(40) forwards;
  width: 0;
}

.teletype-slow {
  overflow: hidden;
  white-space: nowrap;
  animation: typing 4s steps(40) forwards;
  width: 0;
}

/* Terminal Cursor Blink */
.terminal-cursor {
  position: relative;
}

.terminal-cursor::after {
  content: '▊';
  margin-left: 2px;
  animation: blink 1s step-end infinite;
  color: var(--text-primary);
}

/* Matrix Rain - Cascading Characters */
@keyframes matrix-rain {
  0% {
    transform: translateY(-100%);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(100vh);
    opacity: 0;
  }
}

.matrix-rain {
  position: fixed;
  top: 0;
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text-accent);
  text-shadow: 0 0 8px var(--text-accent);
  animation: matrix-rain 3s linear infinite;
  pointer-events: none;
  z-index: 0;
}

/* Boot Sequence Animation */
@keyframes boot-sequence {
  0% {
    opacity: 0;
  }
  5% {
    opacity: 1;
  }
  95% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

.boot-line {
  opacity: 0;
  animation: boot-sequence 0.5s ease-in-out forwards;
  font-family: var(--font-mono);
  color: var(--text-primary);
}

/* Stagger boot lines */
.boot-line:nth-child(1) { animation-delay: 0s; }
.boot-line:nth-child(2) { animation-delay: 0.1s; }
.boot-line:nth-child(3) { animation-delay: 0.2s; }
.boot-line:nth-child(4) { animation-delay: 0.3s; }
.boot-line:nth-child(5) { animation-delay: 0.4s; }

/* EMP Wave - Electromagnetic Pulse Effect */
@keyframes emp-wave {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.7;
    filter: blur(2px);
  }
  100% {
    transform: scale(1);
    opacity: 1;
    filter: blur(0);
  }
}

.emp-wave {
  animation: emp-wave 0.3s ease-out;
}

/* VHS Tracking Error */
@keyframes vhs-tracking {
  0%, 100% {
    transform: translateX(0);
    filter: hue-rotate(0deg);
  }
  20% {
    transform: translateX(-10px);
    filter: hue-rotate(90deg);
  }
  40% {
    transform: translateX(10px);
    filter: hue-rotate(-90deg);
  }
  60% {
    transform: translateX(-5px);
    filter: hue-rotate(45deg);
  }
  80% {
    transform: translateX(5px);
    filter: hue-rotate(-45deg);
  }
}

.vhs-tracking {
  animation: vhs-tracking 0.5s ease-in-out;
}

/* Phosphor Burn-In (Ghost Image) */
.phosphor-burn {
  position: relative;
}

.phosphor-burn::before {
  content: attr(data-text);
  position: absolute;
  top: 2px;
  left: 2px;
  color: var(--text-primary);
  opacity: 0.2;
  filter: blur(1px);
  pointer-events: none;
}

/* Data Corruption - Character Scramble */
@keyframes char-scramble {
  0%, 100% {
    opacity: 1;
  }
  10%, 30%, 50%, 70%, 90% {
    opacity: 0.3;
  }
  20%, 40%, 60%, 80% {
    opacity: 1;
  }
}

.data-corrupt {
  animation: char-scramble 0.5s linear infinite;
}

/* Bit Shift Effect */
@keyframes bit-shift {
  0%, 100% {
    transform: translateX(0) skew(0deg);
  }
  25% {
    transform: translateX(-2px) skew(-2deg);
  }
  50% {
    transform: translateX(2px) skew(2deg);
  }
  75% {
    transform: translateX(-1px) skew(-1deg);
  }
}

.bit-shift {
  animation: bit-shift 0.2s linear infinite;
}

/* Hexadecimal Display Effect */
.hex-display {
  font-family: var(--font-mono);
  color: var(--text-accent);
  text-shadow: 0 0 4px var(--text-accent);
  letter-spacing: 0.1em;
}

/* Binary Rain */
.binary-rain {
  font-family: var(--font-mono);
  color: var(--text-accent);
  text-shadow: 0 0 8px var(--text-accent);
  animation: data-stream 2s linear infinite;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  .dot-matrix-bg-animated,
  .scan-line,
  .scan-line-fast,
  .scan-line-slow,
  .scan-line-thick,
  .scan-sweep,
  .phosphor-glow-orange,
  .phosphor-glow-cyan,
  .phosphor-glow-red,
  .border-glow-orange,
  .border-glow-cyan,
  .border-glow-red,
  .crt-flicker,
  .flicker-intense,
  .grid-expand,
  .phosphor-trail,
  .data-stream,
  .glitch,
  .glitch-severe,
  .screen-tear,
  .static-noise,
  .teletype,
  .teletype-fast,
  .teletype-slow,
  .matrix-rain,
  .boot-line,
  .emp-wave,
  .vhs-tracking,
  .data-corrupt,
  .bit-shift,
  .binary-rain {
    animation: none;
  }

  .chromatic-aberration::before,
  .chromatic-aberration::after {
    display: none;
  }
}

/* =================================================================
   END DOT MATRIX EFFECTS
   ================================================================= */
```

**Expected Result:** CSS classes available globally for dot matrix effects.

---

#### 1.1.5 Advanced Terminal Effects - Usage Guide

**Purpose:** The advanced terminal effects provide enhanced visual feedback for specific UI states and interactions in the terminal webui. Use these effects to create a more immersive, retro-futuristic interface.

**Effect Categories & Use Cases:**

**1. Glitch Effects** - Digital corruption and system errors

```html
<!-- Moderate glitch for warnings -->
<div class="glitch">
  <span>WARNING: SYSTEM OVERLOAD</span>
</div>

<!-- Severe glitch for critical errors -->
<div class="glitch-severe">
  <span>CRITICAL ERROR: MEMORY FAULT</span>
</div>
```

**Use when:**
- ❌ Displaying critical errors or system failures
- ⚠️ Warning states that require immediate attention
- 🔴 Model server connection failures
- 💥 Query processing errors

---

**2. Chromatic Aberration** - RGB split for emphasis

```html
<!-- Add data-text attribute for RGB split -->
<span class="chromatic-aberration" data-text="NEURAL SUBSTRATE ACTIVE">
  NEURAL SUBSTRATE ACTIVE
</span>
```

**Use when:**
- ⚡ Highlighting active processing states
- 🎯 Emphasizing critical system messages
- 🚀 Model initialization or startup sequences
- ✨ Special announcements or alerts

---

**3. Screen Tearing** - Visual disruption effect

```html
<div class="screen-tear">
  <p>Connection interrupted...</p>
</div>
```

**Use when:**
- 🔌 Network connection issues
- 📡 WebSocket disconnections
- ⚡ Data stream interruptions
- 🔄 Reconnection attempts

---

**4. Static Noise** - Signal interference effect

```html
<div class="static-noise">
  <div class="interlaced">
    <!-- Content with noise overlay -->
  </div>
</div>
```

**Use when:**
- 📊 Loading states for data-heavy components
- 🌐 Network request pending
- 💿 Cache miss scenarios
- 🔍 Search in progress

---

**5. Teletype Effects** - Character-by-character reveal

```html
<!-- Standard typing speed -->
<p class="teletype">Initializing neural substrate...</p>

<!-- Fast typing -->
<p class="teletype-fast">READY</p>

<!-- Slow typing for dramatic effect -->
<p class="teletype-slow">WARNING: APPROACHING CONTEXT LIMIT</p>

<!-- With blinking cursor -->
<span class="terminal-cursor">Awaiting input</span>
```

**Use when:**
- 💬 Streaming LLM responses (token-by-token)
- 📝 System status messages
- 🎬 Onboarding or tutorial text
- ⚙️ Configuration confirmations
- 🖥️ Terminal command output

---

**6. Matrix Rain** - Cascading character effect

```typescript
// JavaScript to create matrix rain effect
function createMatrixRain() {
  const chars = '01アイウエオカキクケコサシスセソタチツテト';
  for (let i = 0; i < 20; i++) {
    const rain = document.createElement('div');
    rain.className = 'matrix-rain';
    rain.style.left = `${Math.random() * 100}%`;
    rain.style.animationDelay = `${Math.random() * 3}s`;
    rain.textContent = chars[Math.floor(Math.random() * chars.length)];
    document.body.appendChild(rain);
  }
}
```

**Use when:**
- 🎨 Background ambiance on loading screens
- 🌟 Splash screens or hero sections
- 🎭 Idle state decoration (subtle, sparse)
- 🖼️ Empty state backgrounds

---

**7. Boot Sequence** - System initialization

```html
<div class="boot-container">
  <div class="boot-line">[  OK  ] Starting S.Y.N.A.P.S.E. ENGINE...</div>
  <div class="boot-line">[  OK  ] Mounting NEURAL SUBSTRATE...</div>
  <div class="boot-line">[  OK  ] Initializing CGRAG Index...</div>
  <div class="boot-line">[  OK  ] Loading Model Registry...</div>
  <div class="boot-line">[  OK  ] System Ready</div>
</div>
```

**Use when:**
- 🚀 Application startup/first load
- 🔄 Model server initialization
- 📦 Component lazy loading
- ⚙️ Configuration changes being applied

---

**8. EMP Wave** - Electromagnetic pulse disruption

```typescript
// Trigger EMP effect on critical event
function triggerEMP(element) {
  element.classList.add('emp-wave');
  setTimeout(() => element.classList.remove('emp-wave'), 300);
}
```

**Use when:**
- ⚡ Model server crash or restart
- 🔴 Emergency stop/shutdown commands
- 💥 Query cancellation
- 🚨 Critical error recovery

---

**9. VHS Tracking Error** - Retro distortion

```html
<div class="vhs-tracking">
  <p>ERROR: MEMORY CORRUPTION DETECTED</p>
</div>
```

**Use when:**
- 📼 Data validation failures
- 🔧 Corrupted cache entries
- ⚠️ Checksum mismatches
- 💾 File read/write errors

---

**10. Phosphor Burn-In** - Ghost image effect

```html
<span class="phosphor-burn" data-text="ACTIVE">ACTIVE</span>
```

**Use when:**
- 👻 Recently changed status indicators
- 📊 Value updates in metrics (shows previous value)
- 🔄 State transitions (old → new)
- ⏱️ Timestamp displays

---

**11. Data Corruption** - Character scramble

```html
<span class="data-corrupt hex-display">0xDEADBEEF</span>
```

**Use when:**
- 🔢 Hexadecimal memory addresses
- 🧮 Binary data displays
- 💻 Debug information
- 📊 Low-level system metrics

---

**12. Bit Shift** - Digital instability

```html
<span class="bit-shift">UNSTABLE SIGNAL</span>
```

**Use when:**
- 📡 Weak network connection indicators
- 🔋 Low resource availability warnings
- ⚠️ Near-threshold conditions (memory, CPU)
- 🌊 Fluctuating metrics

---

**Effect Combination Examples:**

```html
<!-- Critical error with multiple effects -->
<div class="static-noise">
  <div class="screen-tear">
    <div class="glitch-severe">
      <span class="chromatic-aberration" data-text="FATAL ERROR">
        FATAL ERROR
      </span>
    </div>
  </div>
</div>

<!-- Loading state with retro feel -->
<div class="interlaced">
  <div class="scan-lines-static">
    <p class="teletype">Loading neural substrate...</p>
  </div>
</div>

<!-- High-tech data display -->
<div class="dot-matrix-bg-dense">
  <div class="hex-display phosphor-burn" data-text="0xF4A3">
    0xF4A3
  </div>
</div>
```

---

**Performance Considerations:**

⚠️ **Heavy Effects (use sparingly):**
- `static-noise` - Animated SVG background
- `matrix-rain` - Multiple DOM elements with animations
- `glitch-severe` - Multiple simultaneous animations
- `vhs-tracking` - Filter effects (can impact performance)

✅ **Lightweight Effects (use liberally):**
- `phosphor-burn` - CSS pseudo-element only
- `hex-display` - Static styling
- `teletype` - Single animation
- `interlaced` - Static gradient

**Best Practices:**

1. **Limit concurrent animations** - No more than 3-5 heavy effects on screen simultaneously
2. **Use `will-change` for frequently animated elements** - Improves GPU utilization
3. **Respect `prefers-reduced-motion`** - All effects automatically disable
4. **Combine effects strategically** - Layer 2-3 effects for maximum impact
5. **Test on target hardware** - Verify 60fps on Mac mini M2

---

#### 1.2 Create DotMatrixPanel Component

**Purpose:** Wrapper around existing Panel component that adds configurable dot matrix effects.

**File:** `frontend/src/components/terminal/DotMatrixPanel/DotMatrixPanel.tsx`

**Complete Implementation:**

```typescript
import React from 'react';
import clsx from 'clsx';
import { Panel, PanelProps } from '../Panel/Panel';
import styles from './DotMatrixPanel.module.css';

export interface DotMatrixPanelProps extends PanelProps {
  /* ===== BASIC EFFECTS ===== */

  /**
   * Enable scan line effect
   * @default false
   */
  enableScanLines?: boolean;

  /**
   * Scan line speed variant
   * @default 'normal'
   */
  scanLineSpeed?: 'slow' | 'normal' | 'fast';

  /**
   * Enable dot matrix grid background
   * @default false
   */
  enableGrid?: boolean;

  /**
   * Grid density
   * @default 'normal'
   */
  gridDensity?: 'sparse' | 'normal' | 'dense';

  /**
   * Enable animated grid (pulsing)
   * @default false
   */
  animatedGrid?: boolean;

  /**
   * Enable border glow effect
   * @default false
   */
  enableBorderGlow?: boolean;

  /**
   * Border glow color
   * @default 'orange'
   */
  glowColor?: 'orange' | 'cyan' | 'red';

  /**
   * Enable static horizontal scan lines
   * @default false
   */
  enableStaticScanLines?: boolean;

  /**
   * Enable CRT screen effect (vignette)
   * @default false
   */
  enableCrtEffect?: boolean;

  /**
   * Enable CRT flicker
   * @default false
   */
  enableFlicker?: boolean;

  /**
   * Effect intensity (overall opacity multiplier)
   * @default 1
   */
  effectIntensity?: number;

  /* ===== ADVANCED TERMINAL EFFECTS ===== */

  /**
   * Enable glitch effect (horizontal displacement)
   * Use for errors, warnings, or system instability
   * @default false
   */
  enableGlitch?: boolean;

  /**
   * Glitch severity level
   * - 'moderate': Horizontal displacement only
   * - 'severe': Horizontal + vertical clipping
   * @default 'moderate'
   */
  glitchSeverity?: 'moderate' | 'severe';

  /**
   * Enable static noise overlay
   * Use for loading states or signal interference
   * @default false
   */
  enableStaticNoise?: boolean;

  /**
   * Enable interlacing effect (horizontal lines)
   * Creates retro CRT scan line appearance
   * @default false
   */
  enableInterlacing?: boolean;

  /**
   * Enable screen tearing effect
   * Use for connection issues or data corruption
   * @default false
   */
  enableScreenTear?: boolean;

  /**
   * Enable VHS tracking error effect
   * Retro distortion with color shifting
   * @default false
   */
  enableVHSTracking?: boolean;

  /**
   * Enable chromatic aberration (RGB split)
   * Use for emphasis or active states
   * @default false
   */
  enableChromaticAberration?: boolean;
}

export const DotMatrixPanel: React.FC<DotMatrixPanelProps> = ({
  children,
  // Basic effects
  enableScanLines = false,
  scanLineSpeed = 'normal',
  enableGrid = false,
  gridDensity = 'normal',
  animatedGrid = false,
  enableBorderGlow = false,
  glowColor = 'orange',
  enableStaticScanLines = false,
  enableCrtEffect = false,
  enableFlicker = false,
  effectIntensity = 1,
  // Advanced terminal effects
  enableGlitch = false,
  glitchSeverity = 'moderate',
  enableStaticNoise = false,
  enableInterlacing = false,
  enableScreenTear = false,
  enableVHSTracking = false,
  enableChromaticAberration = false,
  className,
  ...panelProps
}) => {
  const panelRef = React.useRef<HTMLDivElement>(null);

  // Build grid class based on configuration
  const gridClass = React.useMemo(() => {
    if (!enableGrid) return null;
    if (animatedGrid) return 'dot-matrix-bg-animated';
    if (gridDensity === 'sparse') return 'dot-matrix-bg-sparse';
    if (gridDensity === 'dense') return 'dot-matrix-bg-dense';
    return 'dot-matrix-bg';
  }, [enableGrid, animatedGrid, gridDensity]);

  // Build scan line class based on speed
  const scanLineClass = React.useMemo(() => {
    if (!enableScanLines) return null;
    if (scanLineSpeed === 'slow') return 'scan-line-slow';
    if (scanLineSpeed === 'fast') return 'scan-line-fast';
    return null; // Use default scan-line from animations.css
  }, [enableScanLines, scanLineSpeed]);

  // Build border glow class
  const borderGlowClass = React.useMemo(() => {
    if (!enableBorderGlow) return null;
    if (glowColor === 'cyan') return 'border-glow-cyan';
    if (glowColor === 'red') return 'border-glow-red';
    return 'border-glow-orange';
  }, [enableBorderGlow, glowColor]);

  // Build glitch class
  const glitchClass = React.useMemo(() => {
    if (!enableGlitch) return null;
    return glitchSeverity === 'severe' ? 'glitch-severe' : 'glitch';
  }, [enableGlitch, glitchSeverity]);

  return (
    <div
      ref={panelRef}
      className={clsx(
        styles.dotMatrixWrapper,
        // Basic effects
        enableStaticScanLines && 'scan-lines-static',
        enableCrtEffect && 'crt-screen',
        enableFlicker && 'crt-flicker',
        // Advanced effects
        enableStaticNoise && 'static-noise',
        enableInterlacing && 'interlaced',
        enableScreenTear && 'screen-tear',
        enableVHSTracking && 'vhs-tracking',
        enableChromaticAberration && 'chromatic-aberration',
        glitchClass,
        className
      )}
      style={{
        ['--effect-intensity' as string]: effectIntensity,
      }}
      {...(enableChromaticAberration && {
        'data-text': typeof children === 'string' ? children : '',
      })}
    >
      {/* Background Grid Layer */}
      {enableGrid && gridClass && (
        <div className={clsx(styles.gridLayer, gridClass)} />
      )}

      {/* Panel with optional border glow */}
      <Panel
        {...panelProps}
        className={clsx(borderGlowClass && borderGlowClass)}
      >
        {children}
      </Panel>

      {/* Animated Scan Line Layer */}
      {enableScanLines && (
        <div className={clsx(styles.scanLineLayer, scanLineClass || 'scan-line')} />
      )}
    </div>
  );
};
```

**File:** `frontend/src/components/terminal/DotMatrixPanel/DotMatrixPanel.module.css`

```css
/* DotMatrixPanel Wrapper */
.dotMatrixWrapper {
  position: relative;
  isolation: isolate; /* Create stacking context */
}

/* Grid Layer - Behind Panel */
.gridLayer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  opacity: var(--effect-intensity, 1);
}

/* Scan Line Layer - In Front of Panel */
.scanLineLayer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  pointer-events: none;
  z-index: 2;
  opacity: var(--effect-intensity, 1);
}

/* Ensure Panel content is in the correct stacking order */
.dotMatrixWrapper > :not(.gridLayer):not(.scanLineLayer) {
  position: relative;
  z-index: 1;
}

/* Accessibility: Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .scanLineLayer {
    display: none;
  }

  .gridLayer {
    animation: none;
  }
}
```

**File:** `frontend/src/components/terminal/DotMatrixPanel/index.ts`

```typescript
export { DotMatrixPanel } from './DotMatrixPanel';
export type { DotMatrixPanelProps } from './DotMatrixPanel';
```

**Update:** `frontend/src/components/terminal/index.ts`

Add after Panel exports:

```typescript
export { DotMatrixPanel } from './DotMatrixPanel';
export type { DotMatrixPanelProps } from './DotMatrixPanel';
```

**Expected Result:** DotMatrixPanel component available for use throughout the app.

---

#### 1.3 Create TerminalEffect HOC

**Purpose:** Higher-order component for wrapping any component with terminal effects.

**File:** `frontend/src/components/terminal/TerminalEffect/withTerminalEffect.tsx`

```typescript
import React from 'react';
import clsx from 'clsx';
import styles from './TerminalEffect.module.css';

export interface TerminalEffectConfig {
  enableScanLines?: boolean;
  scanLineSpeed?: 'slow' | 'normal' | 'fast';
  enableGrid?: boolean;
  gridDensity?: 'sparse' | 'normal' | 'dense';
  animatedGrid?: boolean;
  enablePhosphorGlow?: boolean;
  phosphorColor?: 'orange' | 'cyan' | 'red';
  staticGlow?: boolean;
  enableStaticScanLines?: boolean;
  enableCrtEffect?: boolean;
  enableFlicker?: boolean;
  enableDataStream?: boolean;
  effectIntensity?: number;
  className?: string;
}

export interface WithTerminalEffectProps {
  terminalEffect?: TerminalEffectConfig;
}

/**
 * Higher-order component that wraps any component with terminal effects
 */
export function withTerminalEffect<P extends object>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P & WithTerminalEffectProps> {
  const ComponentWithTerminalEffect: React.FC<P & WithTerminalEffectProps> = ({
    terminalEffect,
    ...props
  }) => {
    // If no effect config provided, just render the component as-is
    if (!terminalEffect) {
      return <WrappedComponent {...(props as P)} />;
    }

    const {
      enableScanLines = false,
      scanLineSpeed = 'normal',
      enableGrid = false,
      gridDensity = 'normal',
      animatedGrid = false,
      enablePhosphorGlow = false,
      phosphorColor = 'orange',
      staticGlow = false,
      enableStaticScanLines = false,
      enableCrtEffect = false,
      enableFlicker = false,
      enableDataStream = false,
      effectIntensity = 1,
      className,
    } = terminalEffect;

    // Build grid class
    const gridClass = React.useMemo(() => {
      if (!enableGrid) return null;
      if (animatedGrid) return 'dot-matrix-bg-animated';
      if (gridDensity === 'sparse') return 'dot-matrix-bg-sparse';
      if (gridDensity === 'dense') return 'dot-matrix-bg-dense';
      return 'dot-matrix-bg';
    }, [enableGrid, animatedGrid, gridDensity]);

    // Build scan line class
    const scanLineClass = React.useMemo(() => {
      if (!enableScanLines) return null;
      if (scanLineSpeed === 'slow') return 'scan-line-slow';
      if (scanLineSpeed === 'fast') return 'scan-line-fast';
      return 'scan-line';
    }, [enableScanLines, scanLineSpeed]);

    // Build phosphor glow class
    const phosphorGlowClass = React.useMemo(() => {
      if (!enablePhosphorGlow) return null;
      if (staticGlow) {
        if (phosphorColor === 'cyan') return 'phosphor-glow-static-cyan';
        if (phosphorColor === 'red') return 'phosphor-glow-static-red';
        return 'phosphor-glow-static-orange';
      } else {
        if (phosphorColor === 'cyan') return 'phosphor-glow-cyan';
        if (phosphorColor === 'red') return 'phosphor-glow-red';
        return 'phosphor-glow-orange';
      }
    }, [enablePhosphorGlow, phosphorColor, staticGlow]);

    return (
      <div
        className={clsx(
          styles.terminalEffectWrapper,
          enableStaticScanLines && 'scan-lines-static',
          enableCrtEffect && 'crt-screen',
          enableFlicker && 'crt-flicker',
          enableDataStream && 'data-stream',
          phosphorGlowClass,
          className
        )}
        style={{
          ['--effect-intensity' as string]: effectIntensity,
        }}
      >
        {/* Background Grid Layer */}
        {enableGrid && gridClass && (
          <div className={clsx(styles.gridLayer, gridClass)} />
        )}

        {/* Wrapped Component */}
        <div className={styles.componentLayer}>
          <WrappedComponent {...(props as P)} />
        </div>

        {/* Animated Scan Line Layer */}
        {enableScanLines && scanLineClass && (
          <div className={clsx(styles.scanLineLayer, scanLineClass)} />
        )}
      </div>
    );
  };

  ComponentWithTerminalEffect.displayName = `withTerminalEffect(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return ComponentWithTerminalEffect;
}

/**
 * Component version of terminal effect wrapper
 */
export const TerminalEffect: React.FC<
  TerminalEffectConfig & { children: React.ReactNode }
> = ({ children, ...config }) => {
  const {
    enableScanLines = false,
    scanLineSpeed = 'normal',
    enableGrid = false,
    gridDensity = 'normal',
    animatedGrid = false,
    enablePhosphorGlow = false,
    phosphorColor = 'orange',
    staticGlow = false,
    enableStaticScanLines = false,
    enableCrtEffect = false,
    enableFlicker = false,
    enableDataStream = false,
    effectIntensity = 1,
    className,
  } = config;

  const gridClass = React.useMemo(() => {
    if (!enableGrid) return null;
    if (animatedGrid) return 'dot-matrix-bg-animated';
    if (gridDensity === 'sparse') return 'dot-matrix-bg-sparse';
    if (gridDensity === 'dense') return 'dot-matrix-bg-dense';
    return 'dot-matrix-bg';
  }, [enableGrid, animatedGrid, gridDensity]);

  const scanLineClass = React.useMemo(() => {
    if (!enableScanLines) return null;
    if (scanLineSpeed === 'slow') return 'scan-line-slow';
    if (scanLineSpeed === 'fast') return 'scan-line-fast';
    return 'scan-line';
  }, [enableScanLines, scanLineSpeed]);

  const phosphorGlowClass = React.useMemo(() => {
    if (!enablePhosphorGlow) return null;
    if (staticGlow) {
      if (phosphorColor === 'cyan') return 'phosphor-glow-static-cyan';
      if (phosphorColor === 'red') return 'phosphor-glow-static-red';
      return 'phosphor-glow-static-orange';
    } else {
      if (phosphorColor === 'cyan') return 'phosphor-glow-cyan';
      if (phosphorColor === 'red') return 'phosphor-glow-red';
      return 'phosphor-glow-orange';
    }
  }, [enablePhosphorGlow, phosphorColor, staticGlow]);

  return (
    <div
      className={clsx(
        styles.terminalEffectWrapper,
        enableStaticScanLines && 'scan-lines-static',
        enableCrtEffect && 'crt-screen',
        enableFlicker && 'crt-flicker',
        enableDataStream && 'data-stream',
        phosphorGlowClass,
        className
      )}
      style={{
        ['--effect-intensity' as string]: effectIntensity,
      }}
    >
      {enableGrid && gridClass && (
        <div className={clsx(styles.gridLayer, gridClass)} />
      )}
      <div className={styles.componentLayer}>{children}</div>
      {enableScanLines && scanLineClass && (
        <div className={clsx(styles.scanLineLayer, scanLineClass)} />
      )}
    </div>
  );
};
```

**File:** `frontend/src/components/terminal/TerminalEffect/TerminalEffect.module.css`

```css
/* TerminalEffect Wrapper */
.terminalEffectWrapper {
  position: relative;
  isolation: isolate;
  display: contents;
}

.gridLayer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  opacity: var(--effect-intensity, 1);
}

.componentLayer {
  position: relative;
  z-index: 1;
}

.scanLineLayer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  pointer-events: none;
  z-index: 2;
  opacity: var(--effect-intensity, 1);
}

@media (prefers-reduced-motion: reduce) {
  .scanLineLayer {
    display: none;
  }
  .gridLayer {
    animation: none;
  }
}
```

**File:** `frontend/src/components/terminal/TerminalEffect/index.ts`

```typescript
export { withTerminalEffect, TerminalEffect } from './withTerminalEffect';
export type {
  TerminalEffectConfig,
  WithTerminalEffectProps,
} from './withTerminalEffect';
```

**Update:** `frontend/src/components/terminal/index.ts`

Add after DotMatrixPanel exports:

```typescript
export { withTerminalEffect, TerminalEffect } from './TerminalEffect';
export type {
  TerminalEffectConfig,
  WithTerminalEffectProps,
} from './TerminalEffect';
```

**Expected Result:** TerminalEffect HOC and component wrapper available globally.

---

### Phase 2: Apply Effects to High-Impact Pages (4-6 hours)

#### 2.1 MetricsPage Enhancement

**File:** `frontend/src/pages/MetricsPage/MetricsPage.tsx`

**Current state:** Uses 4 `Panel` components

**Changes:**

1. Replace import:
```typescript
// OLD:
import { Panel, MetricDisplay, Divider } from '@/components/terminal';

// NEW:
import { DotMatrixPanel, MetricDisplay, Divider } from '@/components/terminal';
```

2. Replace first Panel (Performance Overview):
```typescript
<DotMatrixPanel
  title="Performance Overview"
  variant="accent"
  enableGrid
  gridDensity="normal"
  enableBorderGlow
  glowColor="cyan"
  enableScanLines
  scanLineSpeed="slow"
>
  {/* existing content */}
</DotMatrixPanel>
```

3. Replace second Panel (Model Distribution):
```typescript
<DotMatrixPanel
  title="Model Distribution"
  variant="default"
  enableGrid
  gridDensity="sparse"
  enableStaticScanLines
>
  {/* existing content */}
</DotMatrixPanel>
```

4. Replace third Panel (Resource Utilization):
```typescript
<DotMatrixPanel
  title="Resource Utilization"
  variant="default"
  enableGrid
  gridDensity="normal"
  enableBorderGlow
  glowColor="orange"
  enableScanLines
  scanLineSpeed="normal"
>
  {/* existing content */}
</DotMatrixPanel>
```

5. Replace fourth Panel (Charts Placeholder):
```typescript
<DotMatrixPanel
  title="Charts Placeholder"
  noPadding
  enableGrid
  gridDensity="dense"
  animatedGrid
  enableCrtEffect
>
  {/* existing content */}
</DotMatrixPanel>
```

**Expected Result:** MetricsPage with comprehensive dot matrix effects on all panels.

---

#### 2.2 ModelManagementPage Enhancement

**File:** `frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx`

**Current state:** Uses 5+ `Panel` components

**Changes:**

1. Replace import:
```typescript
// OLD:
import { Panel } from '@/components/terminal';

// NEW:
import { DotMatrixPanel } from '@/components/terminal';
```

2. Error state Panel (line ~221):
```typescript
<DotMatrixPanel
  title="SYSTEM ERROR"
  variant="error"
  enableBorderGlow
  glowColor="red"
  enableFlicker
  enableGrid
  gridDensity="sparse"
>
  {/* existing error content */}
</DotMatrixPanel>
```

3. No registry Panel (line ~248):
```typescript
<DotMatrixPanel
  title="NO REGISTRY FOUND"
  variant="warning"
  enableBorderGlow
  glowColor="orange"
  enableGrid
  gridDensity="normal"
>
  {/* existing content */}
</DotMatrixPanel>
```

4. External servers Panel (line ~325):
```typescript
<DotMatrixPanel
  title="EXTERNAL METAL SERVERS"
  variant={externalServerStatus.areReachable ? 'accent' : 'error'}
  enableGrid
  gridDensity="sparse"
  enableBorderGlow
  glowColor={externalServerStatus.areReachable ? 'cyan' : 'red'}
  enableScanLines={!externalServerStatus.areReachable}
  scanLineSpeed="fast"
>
  {/* existing content */}
</DotMatrixPanel>
```

5. Success Panel (line ~362):
```typescript
<DotMatrixPanel
  title="OPERATION SUCCESS"
  variant="accent"
  enableBorderGlow
  glowColor="cyan"
  enableGrid
  gridDensity="normal"
>
  {/* existing content */}
</DotMatrixPanel>
```

6. Error Panel (line ~379):
```typescript
<DotMatrixPanel
  title="OPERATION ERROR"
  variant="error"
  enableBorderGlow
  glowColor="red"
  enableFlicker
  enableGrid
  gridDensity="sparse"
>
  {/* existing content */}
</DotMatrixPanel>
```

7. System Status Panel (line ~395):
```typescript
<DotMatrixPanel
  title="SYSTEM STATUS"
  variant="accent"
  enableGrid
  gridDensity="normal"
  enableBorderGlow
  glowColor="cyan"
  enableScanLines
  scanLineSpeed="slow"
  enableStaticScanLines
>
  {/* existing status grid */}
</DotMatrixPanel>
```

8. Discovered Models Panel (line ~464):
```typescript
<DotMatrixPanel
  title="DISCOVERED MODELS"
  variant="default"
  noPadding
  enableGrid
  gridDensity="dense"
  enableScanLines
  scanLineSpeed="normal"
>
  {/* existing ModelTable */}
</DotMatrixPanel>
```

**Expected Result:** ModelManagementPage with comprehensive dot matrix effects, with error states having intense flicker and warning colors.

---

#### 2.3 HomePage Enhancement

**File:** `frontend/src/pages/HomePage/HomePage.tsx`

**Changes needed:** Replace all `Panel` components with `DotMatrixPanel` with appropriate configurations.

**Suggested configurations:**
- Query input panel: `enableGrid`, `enableBorderGlow` (cyan), `enableScanLines`
- Model status panel: `enableGrid`, `gridDensity="dense"`, `enableStaticScanLines`
- Quick actions: `enableGrid`, `gridDensity="sparse"`

**Expected Result:** Consistent dot matrix aesthetic on home page.

---

### Phase 3: Component-Level Enhancements (3-4 hours)

#### 3.1 StatusIndicator Enhancement

**File:** `frontend/src/components/terminal/StatusIndicator/StatusIndicator.tsx`

**Current:** Simple colored dot with optional pulse

**Enhancement:** Add dot matrix symbols and phosphor glow

**Changes:**

1. Update dot rendering to use dot matrix symbols:
```typescript
const symbols = {
  active: '●',     // Solid circle
  processing: '◉', // Circle with dot
  idle: '◇',       // Diamond
  offline: '◆',    // Solid diamond
  error: '⚠',      // Warning triangle
};
```

2. Add phosphor glow class based on status:
```typescript
const glowClass = {
  active: 'phosphor-glow-static-cyan',
  processing: 'phosphor-glow-cyan',
  idle: 'phosphor-glow-static-orange',
  offline: '',
  error: 'phosphor-glow-red',
};
```

3. Add flicker on error state:
```typescript
{status === 'error' && <span className="flicker-intense">!</span>}
```

**Expected Result:** More visually distinct status indicators with terminal aesthetic.

---

#### 3.2 ProgressBar Enhancement

**File:** `frontend/src/components/terminal/ProgressBar/ProgressBar.tsx`

**Enhancement:** Add phosphor trail and grid background

**Changes:**

1. Add grid background to progress bar container
2. Add phosphor glow to fill bar
3. Add scan line effect during progress

**Expected Result:** Terminal-style progress indicator with enhanced visual feedback.

---

#### 3.3 MetricDisplay Enhancement

**File:** `frontend/src/components/terminal/MetricDisplay/MetricDisplay.tsx`

**Enhancement:** Add background grid and value glow on change

**Changes:**

1. Wrap metric in `TerminalEffect`:
```typescript
<TerminalEffect
  enableGrid
  gridDensity="sparse"
  enablePhosphorGlow={status === 'warning' || status === 'error'}
  phosphorColor={status === 'error' ? 'red' : 'orange'}
  staticGlow
>
  {/* existing metric content */}
</TerminalEffect>
```

2. Add glow to changing values using state:
```typescript
const [isChanging, setIsChanging] = useState(false);
useEffect(() => {
  setIsChanging(true);
  const timer = setTimeout(() => setIsChanging(false), 500);
  return () => clearTimeout(timer);
}, [value]);
```

**Expected Result:** Metrics "pop" when they change, easier to scan.

---

#### 3.4 Button Enhancement

**File:** `frontend/src/components/terminal/Button/Button.tsx`

**Enhancement:** Enhanced border glow on hover and active state

**Changes:**

1. Add hover border glow:
```css
.button:hover {
  animation: border-glow-orange 1s ease-in-out infinite;
}
```

2. Add ripple effect on click with phosphor trail

**Expected Result:** Better interaction feedback with terminal aesthetic.

---

#### 3.5 Panel Component Enhancement

**Note:** Panel itself doesn't need changes since DotMatrixPanel wraps it. However, consider:

**File:** `frontend/src/components/terminal/Panel/Panel.module.css`

**Optional enhancement:** Add subtle phosphor glow to title:

```css
.title {
  /* existing styles */
  text-shadow: 0 0 4px var(--text-primary);
}
```

**Expected Result:** Consistent glow across all panel titles.

---

### Phase 4: Data Visualization (Future - 2-3 hours)

Components to create when implementing charts:

#### 4.1 LiveEventFeed Component
- Scrolling log with scan lines
- Event-specific glow colors
- Grid background

#### 4.2 QueryPipelineVisualization
- Stage boxes with glow states
- Connecting lines with phosphor trail
- Progress scan effect

#### 4.3 ContextWindowVisualization
- Token allocation blocks with glow
- Grid showing token boundaries
- Color-coded sections

---

## Testing Checklist

After each phase, verify:

### Visual Tests
- [ ] All animations run at 60fps (check DevTools Performance tab)
- [ ] No visual glitches or z-index issues
- [ ] Effects are visible but not overwhelming
- [ ] Reduced motion preference is respected
- [ ] Effects work on different screen sizes

### Functional Tests
- [ ] All existing functionality still works
- [ ] No performance degradation in model management
- [ ] WebSocket updates still display correctly
- [ ] Form inputs remain usable
- [ ] Buttons remain clickable

### Accessibility Tests
- [ ] Screen readers can still read content
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG AA standards
- [ ] Reduced motion users get static effects

### Browser Tests
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

---

## Performance Targets

- **Animation FPS:** 60fps constant
- **Page load impact:** <10KB additional CSS
- **Runtime overhead:** <5ms per animation frame
- **Memory impact:** <2MB additional

**Optimization strategies:**
- Use CSS transforms (GPU accelerated)
- Avoid layout thrashing
- Use `will-change` sparingly
- Implement `requestAnimationFrame` for JS animations
- Use CSS variables for dynamic values

---

## Configuration Options

Consider adding to SettingsPage:

```typescript
interface VisualEffectsSettings {
  enableDotMatrixEffects: boolean;
  effectIntensity: number; // 0-100
  enableAnimations: boolean;
  enableScanLines: boolean;
  enableGlow: boolean;
  enableCrtEffect: boolean;
}
```

Store in localStorage and apply globally.

---

## Implementation Order

**Recommended sequence:**

1. ✅ **Day 1 (4-6 hours):** Phase 1 - Core Effect System
   - animations.css enhancements
   - DotMatrixPanel component
   - TerminalEffect HOC
   - Test in isolation

2. ✅ **Day 2 (4-6 hours):** Phase 2.1 & 2.2 - High-Impact Pages
   - MetricsPage enhancement
   - ModelManagementPage enhancement
   - Test in Docker

3. ✅ **Day 3 (2-3 hours):** Phase 2.3 & Phase 3 Start
   - HomePage enhancement
   - Begin component enhancements
   - Test performance

4. ✅ **Day 4 (3-4 hours):** Phase 3 Complete
   - Finish component enhancements
   - Polish and bug fixes
   - Final performance testing

---

## Troubleshooting Guide

### Common Issues

**1. Z-index conflicts:**
- Solution: Ensure `isolation: isolate` on wrapper
- Check that scan line layer has `pointer-events: none`

**2. Performance degradation:**
- Check: Are too many animations running simultaneously?
- Solution: Limit concurrent animations to <10
- Use Chrome DevTools → Performance → Record

**3. Grid not visible:**
- Check: Is opacity too low?
- Check: Is `--text-primary` CSS variable defined?
- Solution: Increase grid opacity or check color contrast

**4. Scan lines causing flicker:**
- Check: Browser GPU acceleration enabled?
- Solution: Reduce scan line opacity or speed
- Try `transform: translateZ(0)` for hardware acceleration

**5. Effects not respecting reduced motion:**
- Check: Media query implementation
- Solution: Wrap all animations in `@media (prefers-reduced-motion: reduce)`

---

## Files Modified Summary

### Phase 1 (Core System)
**Modified:**
- `frontend/src/assets/styles/animations.css` (lines 213+)
- `frontend/src/components/terminal/index.ts` (add 2 export blocks)

**Created:**
- `frontend/src/components/terminal/DotMatrixPanel/DotMatrixPanel.tsx`
- `frontend/src/components/terminal/DotMatrixPanel/DotMatrixPanel.module.css`
- `frontend/src/components/terminal/DotMatrixPanel/index.ts`
- `frontend/src/components/terminal/TerminalEffect/withTerminalEffect.tsx`
- `frontend/src/components/terminal/TerminalEffect/TerminalEffect.module.css`
- `frontend/src/components/terminal/TerminalEffect/index.ts`

### Phase 2 (Pages)
**Modified:**
- `frontend/src/pages/MetricsPage/MetricsPage.tsx` (import + 4 Panel replacements)
- `frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx` (import + 8 Panel replacements)
- `frontend/src/pages/HomePage/HomePage.tsx` (import + Panel replacements)

### Phase 3 (Components)
**Modified:**
- `frontend/src/components/terminal/StatusIndicator/StatusIndicator.tsx`
- `frontend/src/components/terminal/ProgressBar/ProgressBar.tsx`
- `frontend/src/components/terminal/MetricDisplay/MetricDisplay.tsx`
- `frontend/src/components/terminal/Button/Button.tsx`
- `frontend/src/components/terminal/Panel/Panel.module.css` (optional)

---

## Success Criteria

Implementation is complete when:

- ✅ Consistent dot matrix aesthetic across all pages
- ✅ 60fps performance maintained for all animations
- ✅ Configurable effect intensity (accessibility)
- ✅ Reduced motion support implemented
- ✅ Visual density matches NERV/technical interface aesthetic
- ✅ Enhanced information hierarchy through glow effects
- ✅ Real-time data updates feel more immediate and responsive
- ✅ No regressions in existing functionality
- ✅ All tests passing

---

## Next Steps After Implementation

1. **Gather user feedback** on effect intensity
2. **Add configuration panel** in SettingsPage
3. **Create theme variants** (classic terminal green, amber, etc.)
4. **Implement Phase 4** (data visualization components)
5. **Document patterns** for future component development
6. **Performance audit** and optimization
7. **Update CLAUDE.md** with new component patterns

---

## Related Documents

- [CLAUDE.md](./CLAUDE.md) - Project context and architecture
- [SESSION_NOTES.md](./SESSION_NOTES.md) - Development history
- [PROJECT_OVERVIEW.md](./docs/PROJECT_OVERVIEW.md) - System overview
- [frontend/src/assets/styles/animations.css](./frontend/src/assets/styles/animations.css) - Current animations

---

**Document Version:** 1.0
**Last Updated:** 2025-11-09
