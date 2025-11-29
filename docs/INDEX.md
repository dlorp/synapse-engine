# Documentation Index

**S.Y.N.A.P.S.E. ENGINE Documentation Structure**

Last Updated: 2025-11-29

---

## Root Documentation (../*)

Essential project documentation kept in the root directory for quick access:

- **[CLAUDE.md](../CLAUDE.md)** - Project instructions and development guidelines for Claude Code
- **[README.md](../README.md)** - Project overview and getting started guide
- **[PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)** - Architecture and system design
- **[SESSION_NOTES.md](../SESSION_NOTES.md)** - Development log (reverse chronological, recent 2 weeks)
- **[ASCII_MASTER_GUIDE.md](../ASCII_MASTER_GUIDE.md)** - Terminal aesthetic design guide

---

## Architecture ([architecture/](./architecture/))

System design and infrastructure documentation:

- **PROJECT_SPECfINAL.md** - Complete project specification
- **DOCKER_INFRASTRUCTURE.md** - Docker infrastructure architecture
- **PAGE_BOUNDARIES.md** - Page boundary specifications

---

## Features ([features/](./features/))

Feature specifications and documentation:

- **MODES.md** - Query mode documentation (referenced by agents)
- **BENCHMARK_MODE.md** - Benchmark mode feature
- **LOGVIEWER.md** - Log viewer feature
- **DYNAMIC_CONTROL.md** - Dynamic control feature

---

## Guides ([guides/](./guides/))

Current operational guides for development and testing:

- **DOCKER_QUICKSTART.md** - Docker quickstart guide
- **DOCKER_QUICK_REFERENCE.md** - Docker quick reference (referenced by agents)
- **PROFILE_QUICK_REFERENCE.md** - Profile system quick reference
- **QUICK_START_MODEL_MANAGEMENT.md** - Model management quickstart
- **VISUAL_TESTING_GUIDE.md** - Guide for visual testing of terminal UI components

---

## Reference ([reference/](./reference/)) - NEW

Style guides and API reference documentation:

- **WEBTUI_STYLE_GUIDE.md** - Complete WebTUI styling guide
- **WEBTUI_INTEGRATION_GUIDE.md** - WebTUI integration patterns

---

## Implementation ([implementation/](./implementation/))

Active implementation documentation:

### Phase 3 - Model Management Rework
- **PHASE3_MODEL_MANAGEMENT_REWORK.md** - Current model management overhaul
- **PHASE3_UNIFIED_HEADERS_COMPLETE.md** - Header unification

### Phase 4 - Dashboard Features
- **PHASE4_COMPONENT3_TIMESERIES_METRICS_API.md** - Metrics API implementation
- **CONTEXT_ALLOCATION_API_IMPLEMENTATION.md** - Context allocation backend
- **CONTEXT_WINDOW_PANEL_IMPLEMENTATION.md** - Context window UI
- **PROCESSING_PIPELINE_VISUALIZATION_IMPLEMENTATION.md** - Pipeline visualization
- **TIER_COMPARISON_IMPLEMENTATION.md** - Tier comparison feature

---

## Components ([components/](./components/))

Component-specific documentation:

### ASCII Components
- **ASCII_CHARTS_IMPLEMENTATION.md** - Chart implementation details
- **ASCII_CHARTS_QUICK_REFERENCE.md** - Chart quick reference
- **ASCIIPANEL_COMPONENT_CREATED.md** - ASCIIPanel component docs

### Page Components
- **ADMIN_PAGE_ASCII_ENHANCEMENTS.md** - Admin page improvements
- **SETTINGS_PAGE_TERMINAL_TRANSFORMATION.md** - Settings page transformation

---

## Fixes ([fixes/](./fixes/))

Recent bug fixes and solutions (Nov 12+):

- **ASCIIPANEL_PADDING_FIX.md** - ASCII panel padding solution
- **WEBSOCKET_CONNECTION_LOOP_FIX.md** - WebSocket connection fix
- **ADMINPAGE_ASCII_FRAMES_FIX.md** - Admin page ASCII fix

---

## Development ([development/](./development/))

Development setup and notes:

- **SESSION_NOTES.md** - Current session notes
- **DOCKER_SETUP.md** - Docker environment setup
- **EXPLORATION_REPORT.md** - Codebase exploration findings

---

## Testing ([testing/](./testing/))

Test documentation:

- **TEST_SUITE_SUMMARY.md** - Test suite summary

---

## Archive ([archive/](./archive/))

Historical documentation and completed work:

### Session History
- **session-history/** - Archived session notes (pre-Nov 15)

### Implementation Plans
- **implementation-plans/** - Completed implementation plans (MAGI_REWORK, etc.)

### Research
- **research/** - Design research and mockups

### Migration
- **migration/** - Migration and moderator documentation

### Phase 1
- **phase-1/** - Phase 1 completion reports

### Components
- **components/** - Historical component implementation reports

---

## Navigation Tips

### Agent Documentation Paths
These paths are referenced by agents and must exist:
- `docs/guides/DOCKER_QUICK_REFERENCE.md`
- `docs/features/MODES.md`
- `docs/architecture/*`

### Current Development
Refer to **[SESSION_NOTES.md](../SESSION_NOTES.md)** for the most recent development activity.

### Architecture Understanding
Start with **[PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)** for system architecture.

### Working with Claude Code
Consult **[CLAUDE.md](../CLAUDE.md)** for project-specific instructions.

---

## Maintenance

When adding new documentation:

1. **Root** - Only 5 essential files (CLAUDE.md, README.md, PROJECT_OVERVIEW.md, SESSION_NOTES.md, ASCII_MASTER_GUIDE.md)
2. **architecture/** - System design documents
3. **features/** - Feature specifications
4. **guides/** - How-to guides and quickstarts
5. **reference/** - Style guides and API docs
6. **implementation/** - Active phase work
7. **archive/** - Historical and completed work

**Last Reorganization:** 2025-11-29 - Major cleanup: pruned SESSION_NOTES.md, consolidated docs structure, moved plans/ to archive.
