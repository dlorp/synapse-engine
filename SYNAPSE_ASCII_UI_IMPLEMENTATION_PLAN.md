# S.Y.N.A.P.S.E. ENGINE - ASCII UI Implementation Plan

**Date:** 2025-11-08 (Revised)
**Status:** Strategic Implementation Plan - REVISED WITH WEBTUI FOUNDATION
**Estimated Total Time:** 52-62 hours across 5 phases
  - Phase 0 (WebTUI Foundation): 8 hours
  - Phase 1 (HomePage): 8-10 hours
  - Phase 2 (MetricsPage): 12-14 hours
  - Phase 3 (ModelManagement): 8-10 hours
  - Phase 4 (Dashboard): 16-20 hours
**Primary Color:** Phosphor Orange (#ff9500)
**Critical Change:** Added Phase 0 for WebTUI CSS framework foundation

---

## Executive Summary

This comprehensive plan outlines the integration of ASCII visualization libraries and implementation of dense terminal UI mockups for the S.Y.N.A.P.S.E. ENGINE. The implementation will transform the current functional UI into a high-density, Bloomberg Terminal NGE style interface with real-time ASCII charts, sparklines, and NERV-inspired aesthetics.

**Vision:** Create an information-dense control interface where every pixel serves a purpose, combining ASCII art visualization with real-time data streams to provide instant system awareness.

**Timeline:** 4-5 weeks of focused development across 5 phases (including foundational WebTUI setup)

**CRITICAL REVISION:** This plan has been revised to include Phase 0 - WebTUI Foundation Setup as a mandatory prerequisite. WebTUI provides the base CSS framework for terminal aesthetics, and all subsequent phases build on top of this foundation.

---

## 🎨 Design Overhaul Integration

**Cross-Reference:** [DESIGN_OVERHAUL_PHASE_1.md](./plans/DESIGN_OVERHAUL_PHASE_1.md)

This ASCII UI Implementation Plan is **coordinated with** the Design Overhaul plan, which focuses on advanced animation techniques and visual effects. The two plans complement each other:

**ASCII UI Plan (This Document):**
- WebTUI CSS framework foundation
- Figlet ASCII banners
- ASCII charts (bar, line, sparkline)
- Dense panel layouts
- System metrics visualization

**Design Overhaul Plan ([DESIGN_OVERHAUL_PHASE_1.md](./plans/DESIGN_OVERHAUL_PHASE_1.md)):**
- ✨ **Dot Matrix LED Display** - Character-by-character reveal animation
- 🖥️ **Enhanced CRT Effects** - Bloom, curvature, scanlines
- ⏳ **Terminal Spinners** - 4 loading animation styles (arc, dots, bar, block)
- 🎨 **Phosphor Glow Effects** - Orange (#ff9500) glow animations

**Unified Phase 1 Approach:**
Both plans work together in Phase 1 to deliver maximum visual impact:
1. **Foundation:** WebTUI CSS + Enhanced CRT effects (from Design Overhaul)
2. **Content:** Figlet banners + Dot Matrix Display (both generate ASCII content)
3. **Loading States:** Terminal Spinners (from Design Overhaul)
4. **Layout:** Dense panels with ASCII charts (from ASCII UI)
5. **Effects:** Phosphor glow on all elements (coordinated between both)

**Implementation Strategy:**
- Agents will implement components from **both plans in parallel**
- All components share the same phosphor orange (#ff9500) theme
- CRT effects and WebTUI foundation support both ASCII and dot matrix content
- Terminal spinners used in both ASCII UI loading states and design overhaul demos

See [DESIGN_OVERHAUL_PHASE_1.md](./plans/DESIGN_OVERHAUL_PHASE_1.md) for detailed implementation guide on dot matrix displays and CRT effects.

**Key Agents:**
- **frontend-engineer** - React components, TypeScript, UI implementation
- **terminal-ui-specialist** - ASCII art, terminal aesthetics, dense layouts
- **backend-architect** - API endpoints for metrics data
- **performance-optimizer** - Ensure 60fps animations, <100ms updates
- **testing-specialist** - Component tests, E2E tests, visual regression

---

## Agent Discovery Results

### Project-Specific Agents (/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/.claude/agents/)

1. **backend-architect.md** - FastAPI, async Python, WebSockets, API design
2. **cgrag-specialist.md** - Vector search, FAISS, embeddings, retrieval optimization
3. **database-persistence-specialist.md** - Data persistence, caching strategies
4. **devops-engineer.md** - Docker, CI/CD, monitoring
5. **frontend-engineer.md** - React, TypeScript, terminal UI, real-time visualizations
6. **model-lifecycle-manager.md** - Model loading, resource management
7. **performance-optimizer.md** - Profiling, optimization, resource usage
8. **query-mode-specialist.md** - Query routing logic, complexity assessment
9. **security-specialist.md** - Security patterns, input validation
10. **terminal-ui-specialist.md** - ASCII art, NERV aesthetics, dense layouts
11. **testing-specialist.md** - Test strategies, performance validation
12. **websocket-realtime-specialist.md** - WebSocket implementation, real-time data

### User-Level Agents (~/.claude/agents/)

1. **record-keeper.md** - Session documentation, progress tracking
2. **strategic-planning-architect.md** - Comprehensive planning, multi-agent coordination

---

## Historical Context

Based on [SESSION_NOTES.md](./SESSION_NOTES.md):
- **Recent Migration:** Project renamed from MAGI to S.Y.N.A.P.S.E. ENGINE
- **Docker Infrastructure:** All development must be in Docker (no local dev servers)
- **Current State:** Production ready v5.0 with Host API operational
- **UI Status:** Functional terminal UI with phosphor orange (#ff9500) branding
- **Performance:** Meeting targets - CGRAG <100ms, 60fps animations

---

## Library Integration Strategy

### Core ASCII Libraries to Integrate

1. **simple-ascii-chart** (TypeScript-native)
   - Primary chart library for bar/line/sparklines
   - Native TypeScript support
   - ANSI color support for phosphor orange theme

2. **figlet.js** (ASCII Banners)
   - System headers and section dividers
   - 400+ font options for variety

3. **text-graph.js** (Multi-series Charts)
   - Complex dashboard layouts
   - Real-time updating support

4. **Custom Box Drawing Utilities**
   - Build reusable box/panel components
   - Use Unicode box-drawing characters

5. **asciichart** (Sparklines)
   - Lightweight performance sparklines
   - Per-model performance tracking

---

## Phase 0: WebTUI Foundation Setup (MANDATORY PREREQUISITE)

**Duration:** 8 hours
**Priority:** Critical (BLOCKS ALL OTHER PHASES)
**Complexity:** Medium
**Lead Agent:** @terminal-ui-specialist
**Support Agents:** @frontend-engineer, @devops-engineer

### Overview

WebTUI CSS framework provides the foundational terminal aesthetics for S.Y.N.A.P.S.E. ENGINE. This phase must be completed before any Phase 1-4 work begins. The framework delivers production-ready terminal styling, eliminating the need to build custom terminal aesthetics from scratch.

**Integration Approach:**
1. WebTUI provides base CSS styling (terminal aesthetics, colors, layouts)
2. ASCII libraries generate content (charts, banners, visualizations)
3. React components wrap libraries with TypeScript types
4. CSS Modules add phosphor glow effects on top of WebTUI base

**Why WebTUI:**
- Professional terminal aesthetic out-of-the-box
- Responsive design pre-implemented
- ANSI color support built-in
- Eliminates custom CSS for terminal features
- Ensures consistent styling across all components

### Tasks

#### Task 0.1: Install WebTUI Package
**Agent:** @devops-engineer
**Time:** 0.5 hours
**Description:** Add @webtui/css to frontend dependencies

**Implementation:**
```bash
# In frontend/ directory
npm install @webtui/css

# Verify installation
npm list @webtui/css

# Update docker-compose.yml if needed to rebuild frontend
docker-compose build --no-cache synapse_frontend
docker-compose up -d
```

**Files Modified:**
- ✏️ `/frontend/package.json` - Add @webtui/css dependency
- ✏️ `/docker-compose.yml` - Ensure frontend rebuild includes new dependency

**Success Criteria:**
- [ ] @webtui/css installed in package.json
- [ ] Frontend Docker container rebuilds successfully
- [ ] No dependency conflicts reported

#### Task 0.2: Configure CSS Layer System
**Agent:** @terminal-ui-specialist
**Time:** 1 hour
**Description:** Set up CSS layer imports in main stylesheet

**Implementation:**
```css
/* /frontend/src/assets/styles/main.css */

/*
 * CSS Layer System for S.Y.N.A.P.S.E. ENGINE
 * Order matters: base → utils → components
 * WebTUI provides base terminal styles
 * Custom styles add phosphor glow effects
 */

@layer base, utils, components;

/* Import WebTUI base terminal styles */
@import '@webtui/css';

/* Custom phosphor theme overrides */
@import './theme.css';

/* Component-specific styles */
@import './components.css';
```

**Why Layers:**
- Ensures predictable CSS specificity
- WebTUI base styles don't override custom effects
- Easy to debug style conflicts
- Professional CSS architecture

**Files Modified:**
- ✏️ `/frontend/src/assets/styles/main.css` - Add layer imports

**Success Criteria:**
- [ ] CSS layers configured correctly
- [ ] WebTUI imports without errors
- [ ] No console warnings about CSS conflicts
- [ ] Layer order verified in DevTools

#### Task 0.3: Create Phosphor Orange Theme
**Agent:** @terminal-ui-specialist
**Time:** 2 hours
**Description:** Customize WebTUI variables for S.Y.N.A.P.S.E. ENGINE aesthetic

**Implementation:**
```css
/* /frontend/src/assets/styles/theme.css */

/**
 * S.Y.N.A.P.S.E. ENGINE - Phosphor Orange Theme
 * Customizes WebTUI CSS variables to match brand identity
 * Primary color: #ff9500 (phosphor orange, NOT green)
 */

:root {
  /* Primary Brand Colors */
  --webtui-primary: #ff9500;        /* Phosphor orange */
  --webtui-background: #000000;     /* Pure black */
  --webtui-accent: #00ffff;         /* Cyan for highlights */
  --webtui-text: #ff9500;           /* Primary text color */
  --webtui-border: #ff9500;         /* Panel borders */

  /* State Colors */
  --webtui-success: #00ff00;        /* Success green */
  --webtui-warning: #ff9500;        /* Warning amber (same as primary) */
  --webtui-error: #ff0000;          /* Error red */
  --webtui-processing: #00ffff;     /* Processing cyan */

  /* Typography */
  --webtui-font-family: 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', monospace;
  --webtui-font-size-base: 14px;
  --webtui-font-size-small: 12px;
  --webtui-font-size-large: 16px;
  --webtui-line-height: 1.5;

  /* Spacing */
  --webtui-spacing-xs: 4px;
  --webtui-spacing-sm: 8px;
  --webtui-spacing-md: 16px;
  --webtui-spacing-lg: 24px;
  --webtui-spacing-xl: 32px;

  /* Border Styles */
  --webtui-border-width: 1px;
  --webtui-border-radius: 0;        /* Sharp corners for terminal aesthetic */

  /* Phosphor Glow Effect */
  --phosphor-glow: 0 0 10px rgba(255, 149, 0, 0.8),
                   0 0 20px rgba(255, 149, 0, 0.4),
                   0 0 30px rgba(255, 149, 0, 0.2);
}

/* Phosphor Glow Animation */
@keyframes phosphor-pulse {
  0%, 100% {
    text-shadow: var(--phosphor-glow);
    opacity: 1;
  }
  50% {
    text-shadow: 0 0 5px rgba(255, 149, 0, 0.6);
    opacity: 0.9;
  }
}

/* Apply glow to headings */
h1, h2, h3, h4, h5, h6 {
  text-shadow: var(--phosphor-glow);
  animation: phosphor-pulse 2s ease-in-out infinite;
}

/* Apply glow to borders */
.webtui-panel,
.webtui-box,
.webtui-card {
  box-shadow: var(--phosphor-glow);
}
```

**Files Created:**
- ➕ `/frontend/src/assets/styles/theme.css` - Phosphor orange customizations

**Success Criteria:**
- [ ] Theme variables override WebTUI defaults
- [ ] Phosphor orange (#ff9500) applied consistently
- [ ] Glow effects render correctly
- [ ] No color bleeding or rendering artifacts
- [ ] Theme works in light and dark modes (if applicable)

#### Task 0.4: Create Component Styles
**Agent:** @terminal-ui-specialist
**Time:** 1.5 hours
**Description:** Define component-specific styles building on WebTUI base

**Implementation:**
```css
/* /frontend/src/assets/styles/components.css */

/**
 * S.Y.N.A.P.S.E. ENGINE - Component Styles
 * Builds on WebTUI base with custom enhancements
 */

/* Panel Enhancements */
.synapse-panel {
  background: var(--webtui-background);
  border: var(--webtui-border-width) solid var(--webtui-border);
  padding: var(--webtui-spacing-md);
  box-shadow: var(--phosphor-glow);
  font-family: var(--webtui-font-family);
}

.synapse-panel__header {
  color: var(--webtui-primary);
  text-shadow: var(--phosphor-glow);
  border-bottom: var(--webtui-border-width) solid var(--webtui-border);
  margin-bottom: var(--webtui-spacing-md);
  padding-bottom: var(--webtui-spacing-sm);
}

/* Status Indicators */
.synapse-status {
  display: inline-block;
  padding: var(--webtui-spacing-xs) var(--webtui-spacing-sm);
  border: 1px solid currentColor;
  text-transform: uppercase;
  font-size: var(--webtui-font-size-small);
  letter-spacing: 0.05em;
}

.synapse-status--active {
  color: var(--webtui-success);
  animation: phosphor-pulse 2s ease-in-out infinite;
}

.synapse-status--processing {
  color: var(--webtui-processing);
  animation: phosphor-pulse 1s ease-in-out infinite;
}

.synapse-status--error {
  color: var(--webtui-error);
}

/* ASCII Chart Containers */
.synapse-chart {
  font-family: var(--webtui-font-family);
  color: var(--webtui-primary);
  white-space: pre;
  overflow-x: auto;
  padding: var(--webtui-spacing-sm);
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid var(--webtui-border);
}

/* Sparkline Containers */
.synapse-sparkline {
  display: inline-block;
  font-family: var(--webtui-font-family);
  color: var(--webtui-primary);
  white-space: nowrap;
  letter-spacing: -0.05em; /* Tighten spacing for block characters */
}

/* Metric Displays */
.synapse-metric {
  display: flex;
  flex-direction: column;
  gap: var(--webtui-spacing-xs);
}

.synapse-metric__label {
  font-size: var(--webtui-font-size-small);
  color: var(--webtui-accent);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.synapse-metric__value {
  font-size: var(--webtui-font-size-large);
  color: var(--webtui-primary);
  font-weight: bold;
  text-shadow: var(--phosphor-glow);
}

/* Responsive Grid Layouts */
.synapse-grid {
  display: grid;
  gap: var(--webtui-spacing-md);
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

@media (min-width: 1920px) {
  .synapse-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .synapse-grid {
    grid-template-columns: 1fr;
  }
}
```

**Files Created:**
- ➕ `/frontend/src/assets/styles/components.css` - Component-specific styles

**Success Criteria:**
- [ ] Components build on WebTUI base
- [ ] Custom styles only for S.Y.N.A.P.S.E.-specific features
- [ ] Responsive grid works on all screen sizes
- [ ] No style duplication with WebTUI

#### Task 0.5: Create WebTUI Test Page
**Agent:** @terminal-ui-specialist
**Time:** 2 hours
**Description:** Create test page to verify WebTUI integration

**Implementation:**
```typescript
// /frontend/src/examples/WebTUITest.tsx

import React from 'react';
import '../assets/styles/main.css';

/**
 * WebTUI Integration Test Page
 * Verifies WebTUI CSS framework integration with phosphor orange theme
 */
const WebTUITest: React.FC = () => {
  return (
    <div className="webtui-container">
      <h1>S.Y.N.A.P.S.E. ENGINE - WebTUI Test</h1>

      {/* Test Panel Component */}
      <section className="synapse-panel">
        <h2 className="synapse-panel__header">System Status Panel</h2>

        {/* Test Metrics Grid */}
        <div className="synapse-grid">
          <div className="synapse-metric">
            <span className="synapse-metric__label">Queries/Sec</span>
            <span className="synapse-metric__value">12.5</span>
          </div>

          <div className="synapse-metric">
            <span className="synapse-metric__label">Active Models</span>
            <span className="synapse-metric__value">3</span>
          </div>

          <div className="synapse-metric">
            <span className="synapse-metric__label">Cache Hit Rate</span>
            <span className="synapse-metric__value">87%</span>
          </div>

          <div className="synapse-metric">
            <span className="synapse-metric__label">Uptime</span>
            <span className="synapse-metric__value">99.9%</span>
          </div>
        </div>
      </section>

      {/* Test Status Indicators */}
      <section className="synapse-panel">
        <h2 className="synapse-panel__header">Status Indicators</h2>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span className="synapse-status synapse-status--active">ACTIVE</span>
          <span className="synapse-status synapse-status--processing">PROCESSING</span>
          <span className="synapse-status synapse-status--error">ERROR</span>
        </div>
      </section>

      {/* Test ASCII Chart Container */}
      <section className="synapse-panel">
        <h2 className="synapse-panel__header">ASCII Chart Test</h2>
        <div className="synapse-chart">
{`  100│     ╭─╮
   80│  ╭──╯ ╰╮
   60│ ╭╯     │
   40│╭╯      ╰──╮
   20││         ╰╮
    0└┴──────────┴─
     0    5    10`}
        </div>
      </section>

      {/* Test Sparkline */}
      <section className="synapse-panel">
        <h2 className="synapse-panel__header">Sparkline Test</h2>
        <div className="synapse-sparkline">▁▂▃▄▅▆▇█▇▆▅▄▃▂▁</div>
      </section>

      {/* Test WebTUI Base Components */}
      <section className="synapse-panel">
        <h2 className="synapse-panel__header">WebTUI Base Components</h2>

        <div className="webtui-box">
          <p>This is a WebTUI box with phosphor orange theming.</p>
        </div>

        <button className="webtui-button">WebTUI Button</button>

        <input
          type="text"
          className="webtui-input"
          placeholder="WebTUI Input Field"
        />
      </section>
    </div>
  );
};

export default WebTUITest;
```

**Files Created:**
- ➕ `/frontend/src/examples/WebTUITest.tsx` - Component test page

**Testing Checklist:**
- [ ] Phosphor orange (#ff9500) renders correctly
- [ ] Glow effects animate smoothly
- [ ] Panels have proper borders and shadows
- [ ] Metrics grid is responsive
- [ ] Status indicators pulse correctly
- [ ] ASCII charts render with monospace alignment
- [ ] Sparklines display without wrapping
- [ ] WebTUI base components styled correctly
- [ ] No console errors or warnings
- [ ] Works in Chrome, Firefox, Safari

#### Task 0.6: Document Integration Patterns
**Agent:** @terminal-ui-specialist
**Time:** 1 hour
**Description:** Create WebTUI integration guide for team

**Implementation:**
```markdown
<!-- /docs/WEBTUI_INTEGRATION_GUIDE.md -->

# WebTUI Integration Guide

**Date:** 2025-11-08
**Version:** 1.0
**Status:** Official Integration Standard

## Overview

This guide documents the integration of WebTUI CSS framework into S.Y.N.A.P.S.E. ENGINE. WebTUI provides the foundational terminal aesthetics, and our custom styles add phosphor orange theming and ASCII-specific enhancements.

## Architecture

### CSS Layer System

```css
@layer base, utils, components;
@import '@webtui/css';         /* Base terminal styles */
@import './theme.css';          /* Phosphor orange theme */
@import './components.css';     /* Custom components */
```

**Why Layers:**
- Predictable CSS specificity
- Easy to override WebTUI defaults
- Clear separation of concerns

### Style Hierarchy

1. **WebTUI Base** - Terminal aesthetics, typography, layout
2. **Phosphor Theme** - Brand colors, glow effects
3. **Component Styles** - S.Y.N.A.P.S.E.-specific components
4. **ASCII Content** - Generated by libraries (simple-ascii-chart, figlet.js)

## Using WebTUI Classes

### Base Components

**Panels:**
```tsx
<div className="synapse-panel">
  <h2 className="synapse-panel__header">Panel Title</h2>
  <div className="synapse-panel__content">
    {/* Panel content */}
  </div>
</div>
```

**Metrics:**
```tsx
<div className="synapse-metric">
  <span className="synapse-metric__label">Queries/Sec</span>
  <span className="synapse-metric__value">12.5</span>
</div>
```

**Status Indicators:**
```tsx
<span className="synapse-status synapse-status--active">ACTIVE</span>
<span className="synapse-status synapse-status--processing">PROCESSING</span>
<span className="synapse-status synapse-status--error">ERROR</span>
```

## Theme Variables

### Primary Colors
```css
--webtui-primary: #ff9500;      /* Phosphor orange */
--webtui-background: #000000;   /* Pure black */
--webtui-accent: #00ffff;       /* Cyan */
```

### Typography
```css
--webtui-font-family: 'JetBrains Mono', monospace;
--webtui-font-size-base: 14px;
```

### Effects
```css
--phosphor-glow: 0 0 10px rgba(255, 149, 0, 0.8), ...;
```

## Custom Styles Guidelines

### When to Use Custom CSS

**✅ DO use custom styles for:**
- ASCII chart containers (specific formatting)
- Phosphor glow effects (brand-specific)
- S.Y.N.A.P.S.E.-specific components
- Fine-tuning spacing for ASCII content

**❌ DON'T use custom styles for:**
- Terminal aesthetics (use WebTUI)
- Base typography (use WebTUI variables)
- Responsive layouts (use WebTUI grid)
- Standard UI components (use WebTUI classes)

### Custom Style Template

```css
/* Good: Builds on WebTUI base */
.synapse-custom-component {
  background: var(--webtui-background);
  border: var(--webtui-border-width) solid var(--webtui-border);
  padding: var(--webtui-spacing-md);
  font-family: var(--webtui-font-family);
  /* Custom enhancements only */
  box-shadow: var(--phosphor-glow);
}

/* Bad: Duplicates WebTUI functionality */
.synapse-custom-component {
  background: #000000;  /* Use var(--webtui-background) */
  border: 1px solid #ff9500;  /* Use var(--webtui-border) */
  /* ... */
}
```

## Common Patterns

### Responsive Grid
```tsx
<div className="synapse-grid">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
  <div>Item 4</div>
</div>
```

### ASCII Chart Container
```tsx
<div className="synapse-chart">
  {asciiChartContent}
</div>
```

### Metric Display
```tsx
<div className="synapse-metric">
  <span className="synapse-metric__label">Label</span>
  <span className="synapse-metric__value">{value}</span>
</div>
```

## Troubleshooting

### Issue: Styles not applying
**Solution:** Check CSS layer import order in main.css

### Issue: Glow effects not rendering
**Solution:** Verify theme.css is imported after WebTUI

### Issue: ASCII charts misaligned
**Solution:** Ensure monospace font is set via WebTUI variables

### Issue: Colors incorrect
**Solution:** Check theme variable overrides in theme.css

## Related Documentation

- [WebTUI Official Docs](https://webtui.dev)
- [WEBTUI_STYLE_GUIDE.md](./WEBTUI_STYLE_GUIDE.md)
- [DENSE_TERMINAL_MOCKUPS.md](./DENSE_TERMINAL_MOCKUPS.md)
- [ASCII_LIBRARIES_RESEARCH.md](./ASCII_LIBRARIES_RESEARCH.md)
```

**Files Created:**
- ➕ `/docs/WEBTUI_INTEGRATION_GUIDE.md` - Integration documentation

**Success Criteria:**
- [ ] Guide covers all integration patterns
- [ ] Examples are clear and copy-pasteable
- [ ] Troubleshooting section addresses common issues
- [ ] Related documentation linked

#### Task 0.7: Create Style Guide for Team
**Agent:** @terminal-ui-specialist
**Time:** 1 hour
**Description:** Document styling approach and best practices

**Implementation:**
```markdown
<!-- /docs/WEBTUI_STYLE_GUIDE.md -->

# S.Y.N.A.P.S.E. ENGINE - WebTUI Style Guide

**Date:** 2025-11-08
**Version:** 1.0
**Audience:** All developers

## Styling Philosophy

**Three-Layer Approach:**
1. **WebTUI Base** - Terminal aesthetics (DON'T reinvent)
2. **ASCII Content** - Generated by libraries (simple-ascii-chart, figlet.js)
3. **Custom Effects** - Phosphor glow, brand-specific enhancements

**Golden Rule:** Use WebTUI for terminal styling, custom CSS only for ASCII-specific effects.

## Component Development Workflow

### Step 1: Start with WebTUI Base
```tsx
// Use WebTUI classes first
<div className="webtui-panel">
  <h2 className="webtui-heading">Panel Title</h2>
  {/* Content */}
</div>
```

### Step 2: Add S.Y.N.A.P.S.E. Theme
```tsx
// Apply custom classes for branding
<div className="webtui-panel synapse-panel">
  <h2 className="webtui-heading synapse-panel__header">Panel Title</h2>
  {/* Content */}
</div>
```

### Step 3: Integrate ASCII Content
```tsx
// Wrap ASCII-generated content
<div className="synapse-chart">
  <AsciiLineChart data={data} />
</div>
```

## Class Naming Convention

### WebTUI Classes (Use As-Is)
- `webtui-panel`, `webtui-box`, `webtui-card`
- `webtui-button`, `webtui-input`, `webtui-select`
- `webtui-grid`, `webtui-flex`, `webtui-container`

### S.Y.N.A.P.S.E. Classes (Custom)
- `synapse-panel`, `synapse-metric`, `synapse-status`
- `synapse-chart`, `synapse-sparkline`
- `synapse-grid` (builds on WebTUI grid)

### BEM Naming for Custom Components
```css
.synapse-component { }
.synapse-component__element { }
.synapse-component--modifier { }
```

## Color Usage

### Primary Palette
```css
/* ALWAYS use CSS variables, NEVER hardcode */
color: var(--webtui-primary);      /* Phosphor orange #ff9500 */
background: var(--webtui-background); /* Pure black #000000 */
border-color: var(--webtui-border);   /* Phosphor orange #ff9500 */
```

### State Colors
```css
--webtui-success: #00ff00;     /* Success green */
--webtui-warning: #ff9500;     /* Warning amber */
--webtui-error: #ff0000;       /* Error red */
--webtui-processing: #00ffff;  /* Processing cyan */
```

### Glow Effects
```css
/* Use predefined phosphor glow */
text-shadow: var(--phosphor-glow);
box-shadow: var(--phosphor-glow);

/* DON'T create custom glow values */
/* ❌ text-shadow: 0 0 5px #ff9500; */
```

## Typography

### Font Stack
```css
/* ALWAYS use WebTUI variable */
font-family: var(--webtui-font-family);
/* JetBrains Mono, IBM Plex Mono, Fira Code, monospace */
```

### Font Sizes
```css
--webtui-font-size-small: 12px;   /* Metadata, labels */
--webtui-font-size-base: 14px;    /* Body text */
--webtui-font-size-large: 16px;   /* Emphasis */
```

## Spacing

### Use WebTUI Spacing Variables
```css
--webtui-spacing-xs: 4px;
--webtui-spacing-sm: 8px;
--webtui-spacing-md: 16px;
--webtui-spacing-lg: 24px;
--webtui-spacing-xl: 32px;
```

### Example
```css
.synapse-panel {
  padding: var(--webtui-spacing-md);
  gap: var(--webtui-spacing-sm);
}
```

## Animations

### Phosphor Pulse (Pre-defined)
```css
/* Applied to headings by default */
animation: phosphor-pulse 2s ease-in-out infinite;
```

### Custom Animations
```css
/* Only for ASCII-specific effects */
@keyframes ascii-scroll {
  /* ... */
}
```

## Responsive Design

### Breakpoints (WebTUI Standard)
```css
/* Mobile: < 768px */
/* Tablet: 768px - 1280px */
/* Desktop: > 1280px */
/* Wide: > 1920px */
```

### Grid System
```css
.synapse-grid {
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

@media (min-width: 1920px) {
  .synapse-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

## Common Pitfalls

### ❌ DON'T: Hardcode Colors
```css
/* Bad */
.my-component {
  color: #ff9500;
  background: #000000;
}
```

### ✅ DO: Use Variables
```css
/* Good */
.my-component {
  color: var(--webtui-primary);
  background: var(--webtui-background);
}
```

### ❌ DON'T: Reinvent Terminal Styles
```css
/* Bad: WebTUI already provides this */
.my-panel {
  border: 1px solid #ff9500;
  background: #000;
  font-family: monospace;
}
```

### ✅ DO: Build on WebTUI
```css
/* Good: Use WebTUI base, add custom enhancements */
.synapse-panel {
  /* WebTUI provides border, background, font */
  box-shadow: var(--phosphor-glow); /* Custom enhancement */
}
```

### ❌ DON'T: Use Non-Monospace Fonts
```css
/* Bad: Breaks ASCII alignment */
.ascii-chart {
  font-family: Arial, sans-serif;
}
```

### ✅ DO: Always Use Monospace
```css
/* Good */
.synapse-chart {
  font-family: var(--webtui-font-family);
}
```

## Code Review Checklist

- [ ] Uses WebTUI base classes where possible
- [ ] Custom styles only for S.Y.N.A.P.S.E.-specific features
- [ ] All colors use CSS variables (no hardcoded hex)
- [ ] Monospace font for ASCII content
- [ ] Spacing uses WebTUI variables
- [ ] Responsive design implemented
- [ ] No duplicate styles (check WebTUI first)
- [ ] Phosphor glow applied consistently
- [ ] BEM naming for custom components

## Related Documentation

- [WEBTUI_INTEGRATION_GUIDE.md](./WEBTUI_INTEGRATION_GUIDE.md)
- [DENSE_TERMINAL_MOCKUPS.md](./DENSE_TERMINAL_MOCKUPS.md)
- [ASCII_LIBRARIES_RESEARCH.md](./ASCII_LIBRARIES_RESEARCH.md)
```

**Files Created:**
- ➕ `/docs/WEBTUI_STYLE_GUIDE.md` - Team style guide

**Success Criteria:**
- [ ] All team members understand WebTUI foundation
- [ ] Clear guidelines for when to use custom CSS
- [ ] Examples cover common scenarios
- [ ] Code review checklist provided

### Success Criteria

**Phase 0 is complete when:**

- [ ] @webtui/css installed and imported in Docker environment
- [ ] CSS layer system configured (@layer base, utils, components)
- [ ] theme.css created with phosphor orange (#ff9500) variables
- [ ] components.css created with S.Y.N.A.P.S.E.-specific styles
- [ ] WebTUITest.tsx test page renders correctly
- [ ] Phosphor glow effects animate smoothly
- [ ] Responsive behavior verified (mobile, tablet, desktop, wide)
- [ ] No console errors or CSS warnings
- [ ] WEBTUI_INTEGRATION_GUIDE.md completed
- [ ] WEBTUI_STYLE_GUIDE.md completed
- [ ] All team members trained on WebTUI approach
- [ ] docker-compose.yml updated to rebuild frontend with WebTUI
- [ ] Test page accessible at /webtui-test route

### Files Created

**New Files:**
- ➕ `/frontend/src/assets/styles/theme.css` - Phosphor orange theme
- ➕ `/frontend/src/assets/styles/components.css` - Component styles
- ➕ `/frontend/src/examples/WebTUITest.tsx` - Integration test page
- ➕ `/docs/WEBTUI_INTEGRATION_GUIDE.md` - Integration documentation
- ➕ `/docs/WEBTUI_STYLE_GUIDE.md` - Team style guide

**Modified Files:**
- ✏️ `/frontend/src/assets/styles/main.css` - Add layer imports
- ✏️ `/frontend/package.json` - Add @webtui/css dependency
- ✏️ `/docker-compose.yml` - Rebuild frontend with new dependencies
- ✏️ `/frontend/src/App.tsx` - Add /webtui-test route (for testing)

### Dependencies

- **Requires:** None (foundational phase)
- **Blocks:** Phase 1, Phase 2, Phase 3, Phase 4 (ALL phases depend on this)

### Notes

**CRITICAL PREREQUISITES:**
- This phase is **MANDATORY** before any other work begins
- All subsequent components will build on WebTUI base classes
- Custom CSS should ONLY be for ASCII-specific effects, not terminal styling
- Terminal aesthetics come from WebTUI, not custom implementations

**Integration Strategy:**
- WebTUI handles: Terminal colors, borders, typography, responsive layouts
- Custom styles handle: Phosphor glow, brand-specific components, ASCII containers
- ASCII libraries handle: Chart generation, banner creation, sparklines

**Testing Verification:**
1. Visit http://localhost:5173/webtui-test in Docker environment
2. Verify phosphor orange (#ff9500) colors throughout
3. Check glow effects animate smoothly
4. Test responsive behavior at different screen sizes
5. Inspect DevTools → Styles to verify CSS layer order
6. Check console for any warnings or errors

**Team Communication:**
- Share WEBTUI_INTEGRATION_GUIDE.md with all developers
- Conduct code review using WEBTUI_STYLE_GUIDE.md checklist
- Emphasize: "WebTUI first, custom CSS only when necessary"

---

## Phase 1: HomePage Enhancements

**Duration:** 8-10 hours
**Priority:** High
**Complexity:** Medium
**Lead Agent:** @frontend-engineer
**Support Agents:** @terminal-ui-specialist, @websocket-realtime-specialist

**Prerequisites:** Phase 0 (WebTUI Foundation) MUST be complete before starting this phase. All components in this phase will build on WebTUI base classes and use the phosphor orange theme.

### Tasks

#### Task 1.1: Create Figlet Banner Component
**Agent:** @terminal-ui-specialist
**Time:** 2 hours
**Description:** Implement ASCII art banner with phosphor glow effect

```typescript
// Components to create:
- FigletBanner.tsx - Dynamic ASCII banners with font selection
- Integration with figlet.js library
- CSS animations for phosphor glow
```

#### Task 1.2: Expand System Status Panel
**Agent:** @frontend-engineer
**Time:** 3 hours
**Description:** Upgrade from 3 metrics to 8+ dense metrics

```typescript
// Metrics to add:
- Queries/sec (with sparkline)
- Active Models (count with tier breakdown)
- Token Generation Rate
- Context Window Utilization
- Cache Hit Rate %
- CGRAG Retrieval Latency
- WebSocket Connections
- System Uptime
```

#### Task 1.3: Create OrchestratorStatusPanel Component
**Agent:** @frontend-engineer
**Time:** 2 hours
**Description:** Real-time orchestrator internals visualization

```typescript
// Features:
- Routing decision visualization
- Model tier utilization bars
- Query complexity distribution
- Real-time decision flow
```

#### Task 1.4: Implement LiveEventFeed Component
**Agent:** @websocket-realtime-specialist
**Time:** 3 hours
**Description:** 8-event rolling window with color-coded entries

```typescript
// Event types:
- Query routing decisions
- Model state changes
- CGRAG retrievals
- Cache operations
- Error events
- Performance alerts
```

### Success Criteria

- [ ] Figlet banner displays with phosphor glow animation
- [ ] System status shows 8+ live metrics
- [ ] Orchestrator panel updates in real-time
- [ ] Event feed scrolls smoothly at 60fps
- [ ] All components maintain terminal aesthetic

---

## Phase 2: MetricsPage Redesign

**Duration:** 12-14 hours
**Priority:** High
**Complexity:** High
**Lead Agent:** @frontend-engineer
**Support Agents:** @terminal-ui-specialist, @backend-architect, @performance-optimizer

**Prerequisites:** Phase 0 (WebTUI Foundation) and Phase 1 complete. All chart components will use WebTUI base styling with ASCII content layered on top.

### Tasks

#### Task 2.1: Create QueryAnalyticsPanel
**Agent:** @frontend-engineer
**Time:** 4 hours
**Description:** ASCII charts for query metrics over time

```typescript
// Components:
- AsciiLineChart for query rate
- AsciiBarChart for tier distribution
- Integration with simple-ascii-chart
- 30-minute rolling window
```

#### Task 2.2: Create TierComparisonPanel
**Agent:** @terminal-ui-specialist
**Time:** 3 hours
**Description:** Side-by-side tier performance sparklines

```typescript
// Features:
- 3 parallel sparklines (Q2/Q3/Q4)
- Color-coded by tier
- Token/sec metrics
- Latency comparison
```

#### Task 2.3: Create ResourceUtilizationPanel
**Agent:** @performance-optimizer
**Time:** 3 hours
**Description:** Dense 9-metric resource grid

```typescript
// Metrics grid:
- VRAM usage (per model)
- CPU utilization %
- System memory
- FAISS index size
- Redis cache size
- Active connections
- Thread pool status
- Disk I/O
- Network throughput
```

#### Task 2.4: Create RoutingAnalyticsPanel
**Agent:** @backend-architect
**Time:** 2 hours
**Description:** Routing accuracy and decision metrics

```typescript
// Features:
- Routing decision matrix
- Complexity assessment accuracy
- Fallback statistics
- Model availability heatmap
```

#### Task 2.5: Implement Backend Metrics API
**Agent:** @backend-architect
**Time:** 2 hours
**Description:** FastAPI endpoints for metrics aggregation

```python
# Endpoints:
- GET /api/metrics/queries (time-series data)
- GET /api/metrics/tiers (tier comparisons)
- GET /api/metrics/resources (system resources)
- GET /api/metrics/routing (routing analytics)
- WebSocket /ws/metrics (real-time stream)
```

### Success Criteria

- [ ] ASCII charts render with smooth updates
- [ ] All panels fit on single screen (no scrolling)
- [ ] Data updates every second without lag
- [ ] Backend provides aggregated metrics efficiently
- [ ] Memory usage remains stable during long sessions

---

## Phase 3: ModelManagementPage Enhancements

**Duration:** 8-10 hours
**Priority:** Medium
**Complexity:** Medium
**Lead Agent:** @frontend-engineer
**Support Agents:** @terminal-ui-specialist, @model-lifecycle-manager

**Prerequisites:** Phase 0 (WebTUI Foundation) complete. Model cards will use synapse-panel classes with WebTUI responsive grid.

### Tasks

#### Task 3.1: Create ModelSparkline Component
**Agent:** @terminal-ui-specialist
**Time:** 3 hours
**Description:** Per-model performance sparklines

```typescript
// Features:
- Token generation rate over 5 minutes
- Memory usage trend
- Request latency trend
- Inline display in model cards
```

#### Task 3.2: Create ModelDashboard Card Layout
**Agent:** @frontend-engineer
**Time:** 3 hours
**Description:** Dense card layout with live metrics

```typescript
// Card sections:
- Model name and tier badge
- Status indicator with pulse
- 3 sparklines (tokens/mem/latency)
- Quick stats (requests, uptime, errors)
- Action buttons (start/stop/restart)
```

#### Task 3.3: Refactor ModelTable to Card Grid
**Agent:** @frontend-engineer
**Time:** 2 hours
**Description:** Convert table to responsive card grid

```typescript
// Layout:
- CSS Grid with auto-fit
- 3 columns on wide screens
- 2 columns on medium
- 1 column on narrow
```

#### Task 3.4: Add Per-Model Metrics Aggregation
**Agent:** @model-lifecycle-manager
**Time:** 2 hours
**Description:** Backend support for model-specific metrics

```python
# Features:
- Track per-model statistics
- Rolling window aggregation
- Expose via REST/WebSocket
- Cache in Redis
```

### Success Criteria

- [ ] Each model shows 3 live sparklines
- [ ] Card layout maximizes screen usage
- [ ] Sparklines update smoothly without flicker
- [ ] Backend tracks metrics per model efficiently
- [ ] Visual hierarchy clear (status > metrics > actions)

---

## Phase 4: NEURAL SUBSTRATE DASHBOARD

**Duration:** 16-20 hours
**Priority:** High
**Complexity:** Very High
**Lead Agent:** @frontend-engineer
**Support Agents:** @terminal-ui-specialist, @cgrag-specialist, @backend-architect, @websocket-realtime-specialist

**Prerequisites:** Phase 0 (WebTUI Foundation) complete. Dashboard uses advanced WebTUI layouts with dense panel arrangements and real-time ASCII visualizations.

### Tasks

#### Task 4.1: Create ActiveQueryStreams Carousel
**Agent:** @terminal-ui-specialist
**Time:** 5 hours
**Description:** Multi-query real-time visualization

```typescript
// Features:
- 4 concurrent query streams
- Stage progression indicators
- Token generation animation
- Model assignment display
- Auto-rotate on completion
```

#### Task 4.2: Create RoutingDecisionMatrix
**Agent:** @frontend-engineer
**Time:** 4 hours
**Description:** Live routing decision visualization

```typescript
// Matrix display:
- Query complexity scores
- Model availability grid
- Decision path animation
- Fallback indicators
- Historical accuracy
```

#### Task 4.3: Create ContextAllocationPanel
**Agent:** @cgrag-specialist
**Time:** 4 hours
**Description:** CGRAG context window visualization

```typescript
// Features:
- Token budget bars
- Document relevance scores
- Retrieval latency gauge
- Cache hit indicators
- Context packing efficiency
```

#### Task 4.4: Create CGRAGPerformancePanel
**Agent:** @cgrag-specialist
**Time:** 3 hours
**Description:** FAISS index and retrieval metrics

```typescript
// Metrics:
- Index size and dimensions
- Query latency histogram
- Embedding generation time
- Cache effectiveness
- Top retrieved documents
```

#### Task 4.5: Implement Dashboard WebSocket Stream
**Agent:** @websocket-realtime-specialist
**Time:** 2 hours
**Description:** High-frequency dashboard data stream

```python
# Stream features:
- Aggregated dashboard state
- 10Hz update frequency
- Delta compression
- Client-side buffering
```

#### Task 4.6: Create Dashboard Route and Layout
**Agent:** @frontend-engineer
**Time:** 2 hours
**Description:** New route with dense panel layout

```typescript
// Layout:
- Header with system status
- 4-panel main grid
- Responsive breakpoints
- Keyboard navigation
```

### Success Criteria

- [ ] Dashboard displays 4+ simultaneous data streams
- [ ] All visualizations update at 60fps
- [ ] Query streams show real-time progress
- [ ] CGRAG metrics update within 100ms
- [ ] No performance degradation with all panels active
- [ ] Layout remains readable on 1920x1080 displays

---

## MCP Tool Integration Strategy

### Browser Automation (Playwright)

**Purpose:** Visual regression testing of ASCII charts
**When to Use:**
- After implementing each phase
- Before major releases
- When changing chart libraries

**Test Scenarios:**
```javascript
// Visual regression tests
- Capture ASCII chart renders
- Compare against baselines
- Detect alignment issues
- Verify color accuracy
- Test responsive layouts
```

### IDE Integration

**Purpose:** TypeScript compilation and diagnostics
**When to Use:**
- During component development
- When adding new libraries
- For type validation

**Integration Points:**
```typescript
// IDE diagnostics for:
- Type safety in chart data
- Component prop validation
- WebSocket message types
- API response types
```

### Sequential Thinking

**Purpose:** Complex layout optimization
**When to Use:**
- Dashboard panel arrangement
- Performance bottleneck analysis
- Multi-component coordination

**Problem Types:**
```
- Optimal panel sizing algorithms
- Data flow optimization
- Render cycle analysis
- Cache strategy design
```

### Image Fetch

**Purpose:** Reference screenshot capture
**When to Use:**
- Documenting completed phases
- Creating comparison matrices
- Bug report documentation

---

## Risk Assessment & Mitigation

### Risk 1: Performance Degradation with Multiple Charts

**Probability:** High
**Impact:** Critical
**Mitigation:**
- Use virtual scrolling for long lists
- Implement chart update batching
- Add performance monitoring from Phase 1
- Set update frequency limits (max 10Hz)
- Use React.memo and useMemo aggressively

### Risk 2: ASCII Rendering Inconsistencies

**Probability:** Medium
**Impact:** High
**Mitigation:**
- Standardize on single font (JetBrains Mono)
- Test across browsers (Chrome, Firefox, Safari)
- Implement fallback characters
- Create visual regression test suite
- Document known rendering quirks

### Risk 3: WebSocket Message Overflow

**Probability:** Medium
**Impact:** High
**Mitigation:**
- Implement message queuing
- Add rate limiting (server-side)
- Use delta compression
- Implement backpressure handling
- Monitor WebSocket buffer size

### Risk 4: Memory Leaks from Real-time Updates

**Probability:** Medium
**Impact:** Critical
**Mitigation:**
- Proper cleanup in useEffect
- Limit historical data retention
- Implement circular buffers
- Regular memory profiling
- Add memory usage monitoring

### Risk 5: Library Compatibility Issues

**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Test library combinations early
- Create abstraction layers
- Document version requirements
- Maintain fallback implementations
- Pin dependency versions

---

## Implementation Timeline

### Week 0 (Nov 8-10) - FOUNDATION WEEK
- **Friday (Nov 8):** Phase 0 - WebTUI Foundation Setup (8 hours)
  - Install @webtui/css package
  - Configure CSS layer system
  - Create phosphor orange theme
  - Test WebTUI integration
  - Document integration patterns
  - **BLOCKER:** No Phase 1-4 work can begin until Phase 0 is complete

### Week 1 (Nov 11-15)
- **Monday-Tuesday:** Phase 1 - HomePage Enhancements (8-10 hours)
- **Wednesday-Friday:** Phase 2 start - MetricsPage panels (6-7 hours)

### Week 2 (Nov 18-22)
- **Monday-Tuesday:** Phase 2 complete - Backend integration (6-7 hours)
- **Wednesday-Thursday:** Phase 3 - ModelManagement (8-10 hours)
- **Friday:** Testing and bug fixes

### Week 3 (Nov 25-29)
- **Monday-Wednesday:** Phase 4 - NEURAL SUBSTRATE DASHBOARD (12-14 hours)
- **Thursday:** Phase 4 complete - Polish and optimization (4-6 hours)
- **Friday:** Integration testing and documentation

### Week 4 (Dec 2-6)
- **Monday-Tuesday:** Performance optimization
- **Wednesday-Thursday:** Visual regression testing
- **Friday:** Final review and deployment

---

## Files Modified Summary

### Phase 0 - New Files (Foundation)
- ➕ `frontend/src/assets/styles/theme.css`
- ➕ `frontend/src/assets/styles/components.css`
- ➕ `frontend/src/examples/WebTUITest.tsx`
- ➕ `docs/WEBTUI_INTEGRATION_GUIDE.md`
- ➕ `docs/WEBTUI_STYLE_GUIDE.md`

### Phase 0 - Modified Files
- ✏️ `frontend/src/assets/styles/main.css` (add CSS layer imports)
- ✏️ `frontend/package.json` (add @webtui/css dependency)
- ✏️ `docker-compose.yml` (rebuild frontend with WebTUI)
- ✏️ `frontend/src/App.tsx` (add /webtui-test route)

### Phase 1 - New Files
- ➕ `frontend/src/components/terminal/FigletBanner.tsx`
- ➕ `frontend/src/components/dashboard/OrchestratorStatusPanel.tsx`
- ➕ `frontend/src/components/dashboard/LiveEventFeed.tsx`
- ➕ `frontend/src/components/charts/AsciiSparkline.tsx`

### Phase 1 - Modified Files
- ✏️ `frontend/src/pages/HomePage/HomePage.tsx` (add new panels)
- ✏️ `frontend/src/components/Panel/Panel.tsx` (enhance density)
- ✏️ `backend/app/routers/websocket.py` (add event stream)

### Phase 2 - New Files
- ➕ `frontend/src/components/charts/AsciiLineChart.tsx`
- ➕ `frontend/src/components/charts/AsciiBarChart.tsx`
- ➕ `frontend/src/pages/MetricsPage/QueryAnalyticsPanel.tsx`
- ➕ `frontend/src/pages/MetricsPage/TierComparisonPanel.tsx`
- ➕ `frontend/src/pages/MetricsPage/ResourceUtilizationPanel.tsx`
- ➕ `frontend/src/pages/MetricsPage/RoutingAnalyticsPanel.tsx`
- ➕ `backend/app/routers/metrics.py`

### Phase 2 - Modified Files
- ✏️ `frontend/src/pages/MetricsPage/MetricsPage.tsx` (complete redesign)
- ✏️ `backend/app/main.py` (add metrics router)

### Phase 3 - New Files
- ➕ `frontend/src/components/models/ModelSparkline.tsx`
- ➕ `frontend/src/components/models/ModelDashboardCard.tsx`

### Phase 3 - Modified Files
- ✏️ `frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx`
- ✏️ `backend/app/services/model_manager.py` (add metrics tracking)

### Phase 4 - New Files
- ➕ `frontend/src/pages/Dashboard/Dashboard.tsx`
- ➕ `frontend/src/pages/Dashboard/ActiveQueryStreams.tsx`
- ➕ `frontend/src/pages/Dashboard/RoutingDecisionMatrix.tsx`
- ➕ `frontend/src/pages/Dashboard/ContextAllocationPanel.tsx`
- ➕ `frontend/src/pages/Dashboard/CGRAGPerformancePanel.tsx`
- ➕ `backend/app/routers/dashboard.py`

### Phase 4 - Modified Files
- ✏️ `frontend/src/App.tsx` (add dashboard route)
- ✏️ `backend/app/services/cgrag.py` (expose metrics)

---

## Definition of Done

### Phase 0 Complete When:
- [ ] @webtui/css package installed in Docker environment
- [ ] CSS layer system configured correctly
- [ ] Phosphor orange theme applied throughout
- [ ] WebTUI test page renders without errors
- [ ] Glow effects animate smoothly at 60fps
- [ ] Responsive layouts work on all screen sizes
- [ ] Integration guide and style guide complete
- [ ] All team members understand WebTUI approach
- [ ] No console warnings or errors

### Phase 1 Complete When:
- [ ] Figlet banner renders with correct font
- [ ] System status shows 8+ metrics
- [ ] Event feed updates smoothly
- [ ] All tests pass
- [ ] No memory leaks detected

### Phase 2 Complete When:
- [ ] All 4 metric panels render
- [ ] ASCII charts update at 1Hz minimum
- [ ] Backend metrics API returns data
- [ ] Performance targets met (<100ms response)
- [ ] Visual regression tests pass

### Phase 3 Complete When:
- [ ] Model cards show sparklines
- [ ] Grid layout responsive
- [ ] Per-model metrics tracked
- [ ] UI remains at 60fps
- [ ] Integration tests pass

### Phase 4 Complete When:
- [ ] Dashboard shows all 4 panels
- [ ] Query streams animate smoothly
- [ ] CGRAG metrics accurate
- [ ] WebSocket stream stable
- [ ] Full E2E tests pass
- [ ] Documentation complete

---

## Next Actions

### Immediate (This Session)
1. Review plan with team
2. Create feature branch: `feature/ascii-ui-implementation`
3. **CRITICAL:** Begin Phase 0 - WebTUI Foundation Setup
4. Install @webtui/css package
5. Configure CSS layer system

### Tomorrow
1. Complete Phase 0 implementation
2. Test WebTUI integration thoroughly
3. Share WEBTUI_INTEGRATION_GUIDE.md with team
4. Get team approval before proceeding to Phase 1

### Next Week (Week 1)
1. Begin Phase 1 - HomePage Enhancements
2. Create visual regression test baseline
3. Document any library issues discovered
4. Weekly progress review

---

## Related Documentation

- [DENSE_TERMINAL_MOCKUPS.md](./DENSE_TERMINAL_MOCKUPS.md) - Complete UI mockups
- [ASCII_LIBRARIES_RESEARCH.md](./ASCII_LIBRARIES_RESEARCH.md) - Library research
- [ASCII_LIBRARIES_QUICK_REFERENCE.md](./ASCII_LIBRARIES_QUICK_REFERENCE.md) - Quick reference
- [MOCKUPS_QUICK_REFERENCE.md](./MOCKUPS_QUICK_REFERENCE.md) - Implementation guide
- [SESSION_NOTES.md](./SESSION_NOTES.md) - Development history
- [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) - System architecture

---

## Agent Consultation Log

### @record-keeper
**File:** [record-keeper.md](~/.claude/agents/record-keeper.md)
**Query:** "What past work relates to UI implementation or terminal aesthetics?"
**Insight:** Review SESSION_NOTES.md shows recent migration from MAGI to S.Y.N.A.P.S.E., established phosphor orange (#ff9500) branding, and strict Docker-only development requirement.

### @frontend-engineer
**File:** [frontend-engineer.md](./.claude/agents/frontend-engineer.md)
**Capability:** React 19, TypeScript, TanStack Query, Chart.js, WebSocket integration
**Recommendation:** Use React.memo extensively for chart components, implement virtual scrolling for event feeds, batch state updates for performance.

### @terminal-ui-specialist
**File:** [terminal-ui-specialist.md](./.claude/agents/terminal-ui-specialist.md)
**Capability:** ASCII art, NERV aesthetics, CRT effects, dense layouts
**Recommendation:** Prioritize monospace font consistency, use CSS Grid for panel layouts, implement phosphor glow with CSS animations not JS.

### @performance-optimizer
**File:** [performance-optimizer.md](./.claude/agents/performance-optimizer.md)
**Capability:** Profiling, optimization, resource monitoring
**Recommendation:** Set 10Hz max update frequency, use requestAnimationFrame for animations, implement message batching for WebSocket.

### @testing-specialist
**File:** [testing-specialist.md](./.claude/agents/testing-specialist.md)
**Capability:** Multi-layer testing, performance benchmarks, visual regression
**Recommendation:** Create visual regression suite from Phase 1, benchmark each chart library, test with 1000+ events per second.

---

## Appendix: ASCII Chart Examples

### Simple Bar Chart
```
 ▲
10┤ ┏━━━┓
 8┤ ┃   ┃
 6┤ ┃   ┗━┓
 4┤━┛     ┃
 2┤       ┗━
 └┬─┬─┬─┬─┬▶
  1 2 3 4 5
```

### Sparkline
```
▁▂▃▄▅▆▇█▇▆▅▄▃▂▁
```

### Multi-Series Line Chart
```
  100│     ╭─╮
   80│  ╭──╯ ╰╮
   60│ ╭╯     │
   40│╭╯      ╰──╮
   20││         ╰╮
    0└┴──────────┴─
     0    5    10
```

---

**END OF PLAN**

*This plan represents 44-54 hours of focused development work across 4 phases, with clear deliverables, risk mitigation strategies, and comprehensive testing requirements.*