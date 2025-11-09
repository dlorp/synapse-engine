# Documentation Index

**S.Y.N.A.P.S.E. ENGINE Documentation Structure**

Last Updated: 2025-11-09

---

## Root Documentation (../*)

Essential project documentation kept in the root directory for quick access:

- **[CLAUDE.md](../CLAUDE.md)** - Project instructions and development guidelines for Claude Code
- **[README.md](../README.md)** - Project overview and getting started guide
- **[PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)** - Architecture and system design
- **[SESSION_NOTES.md](../SESSION_NOTES.md)** - Development log (reverse chronological)
- **[SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md](../SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md)** - Master UI implementation plan
- **[WEBSOCKET_CONNECTION_LOOP_FIX.md](../WEBSOCKET_CONNECTION_LOOP_FIX.md)** - Recent critical WebSocket fix (2025-11-09)

---

## Archive - Phase 1 Completion Reports ([archive/phase-1/](./archive/phase-1/))

Historical implementation reports for Phase 1 (ASCII UI Foundation):

- **PHASE_1_COMPLETE.md** - Comprehensive Phase 1 completion report
- **PHASE_1_DAYS_3_4_COMPLETE.md** - Days 3-4 progress report
- **PHASE_1_EVENT_INTEGRATION_COMPLETE.md** - Event bus integration completion
- **PHASE_1_TESTING_CHECKLIST.md** - Phase 1 testing checklist
- **TASK_0.5_COMPLETE.md** - Task 0.5 completion report
- **TASK_1.0_CRT_EFFECTS_COMPLETE.md** - CRT effects implementation
- **TASK_1.2_SYSTEM_STATUS_PANEL_COMPLETE.md** - System status panel completion

---

## Archive - Component Implementation Reports ([archive/components/](./archive/components/))

Detailed implementation reports for individual UI components:

### Dot Matrix Display
- DOT_MATRIX_BUG_FIX_REPORT.md
- DOT_MATRIX_FIX_VISUAL_GUIDE.md
- DOT_MATRIX_IMPLEMENTATION_REPORT.md
- DOT_MATRIX_LED_ENHANCEMENT_COMPLETE.md
- DOT_MATRIX_RESTART_BUG_FIX.md
- DOT_MATRIX_RESTART_FIX_SUMMARY.md
- DOT_MATRIX_VISUAL_TEST.md

### CRT Effects
- CRT_EFFECTS_AND_SPINNER_COMPLETE.md
- CRT_EFFECTS_ENHANCEMENT_REPORT.md
- CRT_EFFECTS_PROP_API.md
- CRT_ENHANCEMENT_SUMMARY.md

### Terminal Widgets
- TERMINAL_SPINNER_IMPLEMENTATION.md
- TERMINAL_WIDGETS_IMPLEMENTATION.md
- TERMINAL_WIDGETS_VISUAL_TEST.md

### Orchestrator Status Panel
- ORCHESTRATOR_PANEL_VISUAL_GUIDE.md
- ORCHESTRATOR_STATUS_IMPLEMENTATION.md
- ORCHESTRATOR_STATUS_PANEL_IMPLEMENTATION.md

### Live Event Feed
- LIVE_EVENT_FEED_ARCHITECTURE.md
- LIVE_EVENT_FEED_IMPLEMENTATION_SUMMARY.md
- LIVE_EVENT_FEED_INTEGRATION.md

### Other Components
- WEBSOCKET_EVENTS_COMPLETE.md
- PHASE_3_PARTICLE_EFFECTS_COMPLETE.md
- CSS_LAYER_IMPLEMENTATION_SUMMARY.md
- CSS_TEST_PAGE_REPORT.md

---

## Guides ([guides/](./guides/))

Current operational guides for development and testing:

- **VISUAL_TESTING_GUIDE.md** - Guide for visual testing of terminal UI components

---

## Research ([research/](./research/))

Research materials and reference documentation:

- **ASCII_LIBRARIES_QUICK_REFERENCE.md** - Quick reference for ASCII art libraries
- **ASCII_LIBRARIES_RESEARCH.md** - Detailed research on ASCII art libraries
- **MOCKUPS_QUICK_REFERENCE.md** - UI mockup reference
- **DENSE_TERMINAL_MOCKUPS.md** - Dense terminal UI design mockups

---

## Planning ([planning/](./planning/))

Project planning and roadmap documents:

- **planning.md** - General project planning notes
- **opencode_integration_plan.md** - OpenCode backend integration plan

---

## Tests ([../tests/](../tests/))

Test scripts and verification tools (located at project root level):

- Various test scripts for component verification
- WebSocket connection tests
- CSS layer verification scripts

---

## Navigation Tips

### Finding Historical Implementation Details
All completed Phase 1 work is archived in `archive/phase-1/` and `archive/components/`. These documents are kept for reference but are no longer actively maintained.

### Current Development
Refer to **[SESSION_NOTES.md](../SESSION_NOTES.md)** for the most recent development activity (newest entries at top).

### Architecture Understanding
Start with **[PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)** for system architecture and **[SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md](../SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md)** for UI implementation details.

### Working with Claude Code
Consult **[CLAUDE.md](../CLAUDE.md)** for project-specific instructions, patterns, and development guidelines.

---

## Maintenance

This documentation structure is maintained to keep the project root clean and organized. When adding new documentation:

1. **Root** - Only essential, actively used documents
2. **archive/** - Completed implementation reports and historical records
3. **guides/** - How-to guides and tutorials
4. **research/** - Reference materials and research findings
5. **planning/** - Future work and planning documents

**Last Reorganization:** 2025-11-09 - Moved 38 implementation reports to archive, cleaned root to 6 essential files.
