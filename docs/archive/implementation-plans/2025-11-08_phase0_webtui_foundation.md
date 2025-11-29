# Phase 0: WebTUI Foundation Setup - Execution Plan

**Date:** 2025-11-08
**Status:** Implementation Plan
**Estimated Time:** 8 hours
**Priority:** CRITICAL BLOCKING PHASE

**Related Documentation:**
- [SESSION_NOTES.md](../SESSION_NOTES.md) - Recent development context
- [SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md](../SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md) - Full project plan
- [CLAUDE.md](../CLAUDE.md) - Project documentation and requirements
- [docker-compose.yml](../docker-compose.yml) - Docker configuration

---

## 🎯 Objective

Establish the WebTUI CSS framework foundation with phosphor orange theme for the S.Y.N.A.P.S.E. ENGINE terminal-aesthetic interface. This phase is MANDATORY and blocks all subsequent UI work.

## 📊 Context & Background

**Current State:**
- Basic functional UI exists but lacks the terminal aesthetic
- No unified design system or CSS framework
- Frontend running in Docker container (synapse_frontend)
- Primary color defined as phosphor orange (#ff9500)

**Motivation:**
- WebTUI provides a robust CSS framework for terminal aesthetics
- CSS @layer system ensures predictable specificity
- Foundation needed before implementing ASCII visualizations
- Creates consistent design language across all components

**Constraints:**
- Docker-only development (no local npm commands)
- Frontend env vars are build-time (requires Docker rebuild)
- Must maintain 60fps performance
- Browser support: Chrome 99+, Firefox 97+, Safari 15.5+

## 🤝 Agent Consultations

### @devops-engineer
**File:** [devops-engineer.md](../.claude/agents/devops-engineer.md)
**Query:** "How should we handle the @webtui/css package installation in Docker environment?"
**Insight:**
- Must add to package.json first
- Then rebuild Docker image with --no-cache flag
- Verify installation in running container
- Monitor build logs for any dependency conflicts

### @terminal-ui-specialist
**File:** [terminal-ui-specialist.md](../.claude/agents/terminal-ui-specialist.md)
**Query:** "What's the best approach for implementing phosphor orange theme with WebTUI?"
**Insight:**
- Use CSS custom properties for theme variables
- Override WebTUI defaults at the @layer level
- Implement glow effects with text-shadow and box-shadow
- Ensure color contrast meets WCAG AA standards

### @frontend-engineer
**File:** [frontend-engineer.md](../.claude/agents/frontend-engineer.md)
**Query:** "How should we structure the test page component?"
**Insight:**
- Create standalone route for isolated testing
- Include all WebTUI components for verification
- Use React.memo for performance
- Add performance metrics display

## 🏗️ Architecture Overview

### Component Structure
```
/frontend
├── package.json              (add @webtui/css dependency)
├── src/
│   ├── assets/styles/
│   │   ├── main.css         (import layers)
│   │   ├── theme.css        (phosphor orange variables)
│   │   └── components.css   (component overrides)
│   ├── examples/
│   │   └── WebTUITest.tsx   (test page component)
│   └── App.tsx              (add test route)
└── Dockerfile               (rebuilt with new package)
```

### CSS Layer Architecture
```css
/* Layer ordering for specificity control */
@layer base, utils, components;

@import '@webtui/css' layer(base);
@import './theme.css' layer(utils);
@import './components.css' layer(components);
```

### Data Flow
1. Docker build → Install @webtui/css
2. Vite build → Bundle CSS layers
3. Browser load → Apply layers in order
4. Components render → Use themed styles
5. Test page validates → All elements styled correctly

## 📝 Implementation Plan

### Wave 1: Package Installation (0.5h)
**Agent:** @devops-engineer
**Status:** Pending

#### Task 0.1: Install @webtui/css Package
**Acceptance Criteria:**
- [ ] Package added to package.json dependencies
- [ ] Docker image rebuilt successfully
- [ ] Package accessible in container
- [ ] No dependency conflicts
- [ ] Build logs show successful installation

**Implementation Steps:**
1. Add `"@webtui/css": "^0.1.5"` to frontend/package.json
2. Execute: `docker-compose build --no-cache synapse_frontend`
3. Verify: `docker-compose exec synapse_frontend npm list @webtui/css`
4. Check logs: `docker-compose logs synapse_frontend`

---

### Wave 2: CSS Configuration (4.5h total - parallel execution)

#### Task 0.2: Configure CSS Layer System (1h)
**Agent:** @terminal-ui-specialist
**Status:** Pending
**Dependencies:** Task 0.1 complete

**Acceptance Criteria:**
- [ ] CSS layers imported in correct order
- [ ] WebTUI base styles loading
- [ ] No CSS conflicts or errors
- [ ] Layer specificity working correctly

**Implementation:**
- Modify `/frontend/src/assets/styles/main.css`
- Add @layer declarations
- Import WebTUI and custom layers

#### Task 0.3: Create Phosphor Orange Theme (2h)
**Agent:** @terminal-ui-specialist
**Status:** Pending
**Dependencies:** Task 0.1 complete

**Acceptance Criteria:**
- [ ] All WebTUI colors overridden to phosphor orange
- [ ] CSS variables defined for theme
- [ ] Glow effects implemented
- [ ] Contrast ratios meet WCAG AA

**Implementation:**
- Create `/frontend/src/assets/styles/theme.css`
- Define CSS custom properties
- Override WebTUI color variables
- Add phosphor glow effects

#### Task 0.4: Create Component Styles (1.5h)
**Agent:** @terminal-ui-specialist
**Status:** Pending
**Dependencies:** Task 0.1 complete

**Acceptance Criteria:**
- [ ] Panel styles with borders
- [ ] Status indicator animations
- [ ] Grid layouts responsive
- [ ] All components themed

**Implementation:**
- Create `/frontend/src/assets/styles/components.css`
- Style panels, grids, status elements
- Add animations and transitions

---

### Wave 2.5: Test Page Implementation (2h)

#### Task 0.5: Create WebTUI Test Page (2h)
**Agents:** @terminal-ui-specialist + @frontend-engineer
**Status:** Pending
**Dependencies:** Tasks 0.2, 0.3, 0.4 complete

**Acceptance Criteria:**
- [ ] Test page renders at /webtui-test
- [ ] All WebTUI components displayed
- [ ] Phosphor orange theme applied
- [ ] 60fps animations verified
- [ ] No console errors

**Implementation:**
- Create `/frontend/src/examples/WebTUITest.tsx`
- Add route to `/frontend/src/App.tsx`
- Include all component examples
- Add performance metrics

---

### Wave 3: Documentation (2h total - parallel execution)

#### Task 0.6: Document Integration Patterns (1h)
**Agent:** @terminal-ui-specialist
**Status:** Pending
**Dependencies:** Task 0.5 validated

**Acceptance Criteria:**
- [ ] Component usage examples documented
- [ ] CSS layer patterns explained
- [ ] Theme customization guide
- [ ] Performance tips included

**Implementation:**
- Create `/docs/WEBTUI_INTEGRATION_GUIDE.md`
- Document patterns and best practices
- Include code examples

#### Task 0.7: Create Style Guide (1h)
**Agent:** @terminal-ui-specialist
**Status:** Pending
**Dependencies:** Task 0.5 validated

**Acceptance Criteria:**
- [ ] Color palette documented
- [ ] Typography guidelines
- [ ] Component catalog
- [ ] Animation standards

**Implementation:**
- Create `/docs/WEBTUI_STYLE_GUIDE.md`
- Document visual standards
- Include screenshots

## 🚨 Risks & Mitigation

### Risk 1: Docker Rebuild Time
**Impact:** High - Could slow development
**Probability:** Medium
**Mitigation:**
- Use Docker layer caching effectively
- Only rebuild when package.json changes
- Keep other changes separate from package updates

### Risk 2: CSS Layer Browser Compatibility
**Impact:** Low - 94% browser support
**Probability:** Low
**Mitigation:**
- Test in Chrome, Firefox, Safari
- Have fallback styles if needed
- Document minimum browser versions

### Risk 3: WebTUI Package Breaking Changes
**Impact:** Medium - Could require refactoring
**Probability:** Low - Package at v0.1.5
**Mitigation:**
- Pin exact version in package.json
- Test thoroughly before proceeding
- Keep original styles as backup

### Risk 4: Performance Degradation
**Impact:** High - Could affect 60fps target
**Probability:** Low
**Mitigation:**
- Profile with Chrome DevTools
- Monitor frame rates in test page
- Optimize animations if needed

## 📚 Reference Documentation

### External Resources
- [WebTUI Official Docs](https://webtui.ironclad.sh/)
- [NPM Package](https://www.npmjs.com/package/@webtui/css)
- [CSS @layer MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/@layer)
- [CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)

### Internal Documentation
- [CLAUDE.md](../CLAUDE.md) - Docker-only workflow requirements
- [SESSION_NOTES.md](../SESSION_NOTES.md) - Recent Docker fixes
- [SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md](../SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md) - Full implementation phases

### Agent Files Consulted
- [devops-engineer.md](../.claude/agents/devops-engineer.md) - Docker expertise
- [terminal-ui-specialist.md](../.claude/agents/terminal-ui-specialist.md) - Terminal aesthetics
- [frontend-engineer.md](../.claude/agents/frontend-engineer.md) - React implementation

## ✅ Definition of Done

Phase 0 is complete when ALL of the following are verified:

### Technical Requirements
- [ ] @webtui/css v0.1.5 installed in Docker container
- [ ] CSS layer system configured and working
- [ ] Phosphor orange theme fully applied
- [ ] Test page renders at http://localhost:5173/webtui-test
- [ ] All WebTUI components styled correctly
- [ ] Glow effects animating at 60fps
- [ ] Responsive layouts working (mobile/tablet/desktop/wide)
- [ ] No console errors or warnings
- [ ] Docker image rebuilt and tagged

### Documentation Requirements
- [ ] Integration guide complete with examples
- [ ] Style guide documenting all patterns
- [ ] Code comments explaining layer system
- [ ] README updated with WebTUI information

### Validation Requirements
- [ ] Chrome 99+ tested and working
- [ ] Firefox 97+ tested and working
- [ ] Safari 15.5+ tested and working
- [ ] Performance metrics within targets
- [ ] Accessibility standards met (ARIA labels, keyboard nav)

## 🔄 Next Actions

### Immediate Actions (Wave 1)
1. @devops-engineer: Add @webtui/css to package.json
2. @devops-engineer: Rebuild Docker image
3. @devops-engineer: Verify package installation

### Parallel Actions (Wave 2)
4. @terminal-ui-specialist: Configure CSS layers (0.2)
5. @terminal-ui-specialist: Create phosphor theme (0.3)
6. @terminal-ui-specialist: Create component styles (0.4)

### Sequential Actions (Wave 2.5)
7. @terminal-ui-specialist + @frontend-engineer: Build test page (0.5)
8. Validate test page renders correctly
9. Test responsive layouts and animations

### Final Actions (Wave 3)
10. @terminal-ui-specialist: Document integration patterns (0.6)
11. @terminal-ui-specialist: Create style guide (0.7)
12. Update SESSION_NOTES.md with completion status

## 📊 Estimated Effort

### Phase Breakdown
| Wave | Tasks | Agents | Time | Parallel |
|------|-------|--------|------|----------|
| 1 | 0.1 | @devops-engineer | 0.5h | No |
| 2 | 0.2-0.4 | @terminal-ui-specialist | 4.5h | Yes (3 tasks) |
| 2.5 | 0.5 | @terminal-ui-specialist + @frontend-engineer | 2h | No |
| 3 | 0.6-0.7 | @terminal-ui-specialist | 2h | Yes (2 tasks) |
| **Total** | **7 tasks** | **3 agents** | **8h** | **Mixed** |

### Confidence Levels
- Wave 1: **High** (95%) - Standard package installation
- Wave 2: **High** (90%) - Well-documented CSS framework
- Wave 2.5: **Medium** (80%) - Integration complexity
- Wave 3: **High** (95%) - Documentation only

### Critical Path
1. Task 0.1 (blocks all others)
2. Tasks 0.2-0.4 (parallel CSS work)
3. Task 0.5 (validation checkpoint)
4. Tasks 0.6-0.7 (can be deferred if needed)

## Coordination Strategy

### Communication Protocol
1. **Wave boundaries:** Clear handoff points between waves
2. **Parallel work:** Agents work on separate files to avoid conflicts
3. **Validation gates:** Test page must pass before Wave 3
4. **Status updates:** After each task completion

### Agent Assignments
- **@devops-engineer:** Package management, Docker builds (Wave 1)
- **@terminal-ui-specialist:** CSS framework, theming, documentation (Waves 2-3)
- **@frontend-engineer:** React test component (Wave 2.5)

### File Ownership
| File | Owner | Wave |
|------|-------|------|
| package.json | @devops-engineer | 1 |
| main.css | @terminal-ui-specialist | 2 |
| theme.css | @terminal-ui-specialist | 2 |
| components.css | @terminal-ui-specialist | 2 |
| WebTUITest.tsx | @terminal-ui-specialist + @frontend-engineer | 2.5 |
| App.tsx | @frontend-engineer | 2.5 |
| WEBTUI_INTEGRATION_GUIDE.md | @terminal-ui-specialist | 3 |
| WEBTUI_STYLE_GUIDE.md | @terminal-ui-specialist | 3 |

### Validation Checklist

**After Wave 1:**
- [ ] Package installed in container
- [ ] No build errors
- [ ] Container running

**After Wave 2:**
- [ ] CSS files created
- [ ] No import errors
- [ ] Styles loading

**After Wave 2.5:**
- [ ] Test page accessible
- [ ] All components rendering
- [ ] Theme applied correctly
- [ ] 60fps animations
- [ ] No console errors

**After Wave 3:**
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Ready for Phase 1

## Handoff to Phase 1

Upon successful completion of Phase 0:

1. **Foundation Ready:** WebTUI CSS framework integrated and themed
2. **Patterns Established:** CSS layer system and component styles defined
3. **Documentation Complete:** Integration and style guides available
4. **Test Page Validated:** All components working at 60fps
5. **Team Aligned:** All agents understand the new foundation

Phase 1 (HomePage) can then proceed with:
- ASCII art components built on WebTUI foundation
- Consistent phosphor orange theming
- Established CSS layer patterns
- Validated performance baseline

---

**Phase 0 is the cornerstone of the entire UI implementation. Its successful completion unblocks 52+ hours of subsequent work across Phases 1-4.**