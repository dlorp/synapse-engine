# Documentation Cleanup and Reorganization Plan

**Date:** 2025-11-29
**Status:** Implementation Plan
**Estimated Time:** 2-3 hours
**Priority:** HIGH - Documentation structure affects agent efficiency

**Related Documentation:**
- [SESSION_NOTES.md](../SESSION_NOTES.md) - Development history (578KB - needs pruning)
- [CLAUDE.md](../CLAUDE.md) - Agent instructions
- [docs/INDEX.md](../docs/INDEX.md) - Current documentation index

---

## 1. Objective

Clean up and reorganize the SYNAPSE_ENGINE documentation to create:
1. A scannable root directory with only essential files
2. A well-organized docs/ structure that agents can easily navigate
3. Proper archival of outdated implementation plans and migration docs
4. A pruned SESSION_NOTES.md focused on recent entries (last 2-3 weeks)

---

## 2. Context and Background

### Current State Analysis

**Root Directory (7 markdown files, 842KB total):**
| File | Size | Status | Action |
|------|------|--------|--------|
| CLAUDE.md | 34KB | ESSENTIAL | Keep |
| README.md | 30KB | ESSENTIAL | Keep |
| SESSION_NOTES.md | 578KB | ESSENTIAL but BLOATED | Prune to last 3 weeks |
| PROJECT_OVERVIEW.md | 24KB | ESSENTIAL | Keep |
| ASCII_MASTER_GUIDE.md | 50KB | Reference material | Move to docs/guides/ |
| SCIFI_GUI_RESEARCH.md | 27KB | Reference material | Move to docs/reference/ |
| SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md | 96KB | Outdated plan | Archive |

**docs/ Directory (14 subdirectories, 100+ files):**
- architecture/ (116KB) - Keep, contains active specs
- archive/ (616KB) - Keep, proper archive location
- assets/ (104KB) - Keep
- components/ (252KB) - Move to archive (phase docs)
- development/ (168KB) - Keep active, archive old SESSION*.md
- features/ (13MB!) - Large due to GIF file
- fixes/ (64KB) - Move to archive
- guides/ (60KB) - Keep, essential quick references
- implementation/ (904KB) - Move old phase docs to archive
- phases/ (28KB) - Move to archive
- planning/ (52KB) - Keep
- research/ (156KB) - Keep
- testing/ (4KB) - Merge into guides/
- troubleshooting/ (12KB) - Keep

**SESSION_NOTES.md Analysis:**
- 14,549 lines, 578KB
- 54 dated sessions (Nov 4-29, 2025)
- Oldest entries: Nov 4, 2025
- Most recent: Nov 29, 2025
- Consolidation section for scrollbar issue already exists at top

### Problems Identified

1. **Root directory too cluttered** - 7 markdown files, 842KB
2. **SESSION_NOTES.md too large** - 578KB is unwieldy for agents
3. **docs/ structure fragmented** - 14 subdirectories, many obsolete
4. **Duplicate content** - docs/development/SESSION_NOTES.md vs root
5. **Archive incomplete** - phase3/, phase4/, fixes/ should be archived
6. **13MB GIF in features/** - synapseEngine.gif bloating directory

---

## 3. Agent Consultations

### @record-keeper
**File:** [~/.claude/agents/record-keeper.md](../../.claude/agents/record-keeper.md)
**Query:** "What is the recommended structure for SESSION_NOTES.md pruning?"
**Insight:** Record-keeper maintains reverse chronological order. When pruning:
- Keep newest sessions at top
- Archive older sessions separately (can create SESSION_NOTES_ARCHIVE.md)
- Preserve the Table of Contents with links to archived sections
- Never lose history - archive, don't delete

### @devops-engineer (Available)
**File:** [.claude/agents/devops-engineer.md](../.claude/agents/devops-engineer.md)
**Query:** N/A - Documentation is not DevOps domain
**Impact:** Minor - only affects Docker docs organization

### @frontend-engineer (Available)
**File:** [.claude/agents/frontend-engineer.md](../.claude/agents/frontend-engineer.md)
**Query:** N/A - Frontend engineers benefit from guides/ organization
**Impact:** Easier access to ASCII_MASTER_GUIDE.md in docs/guides/

---

## 4. Architecture Overview

### New Documentation Structure

```
ROOT (clean - 4 essential files):
├── CLAUDE.md              # Agent instructions (keep)
├── README.md              # Project readme (keep)
├── SESSION_NOTES.md       # Dev history (PRUNE to last 3 weeks)
└── PROJECT_OVERVIEW.md    # Overview (keep)

docs/ (consolidated - 8 directories):
├── INDEX.md               # Documentation index (UPDATE)
├── guides/
│   ├── ASCII_MASTER_GUIDE.md    # Move from root
│   ├── TESTING_GUIDE.md         # Keep
│   ├── PERFORMANCE_TESTING_GUIDE.md
│   ├── DOCKER_QUICKSTART.md
│   ├── DOCKER_QUICK_REFERENCE.md
│   ├── PROFILE_QUICK_REFERENCE.md
│   ├── ADMIN_QUICK_REFERENCE.md
│   ├── QUICK_START_MODEL_MANAGEMENT.md
│   └── VISUAL_TESTING_GUIDE.md
├── architecture/          # Keep as-is
│   ├── DOCKER_INFRASTRUCTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PROJECT_SPECfINAL.md
│   ├── PROJECT_STATUS.md
│   └── PAGE_BOUNDARIES.md
├── reference/             # NEW - research/style materials
│   ├── SCIFI_GUI_RESEARCH.md    # Move from root
│   ├── WEBTUI_STYLE_GUIDE.md    # Move from docs/
│   ├── WEBTUI_INTEGRATION_GUIDE.md  # Move from docs/
│   ├── ASCII_LIBRARIES_RESEARCH.md
│   ├── ASCII_LIBRARIES_QUICK_REFERENCE.md
│   ├── DENSE_TERMINAL_MOCKUPS.md
│   ├── MOCKUPS_QUICK_REFERENCE.md
│   └── SYSTEM_IDENTITY.md
├── features/              # Keep active feature docs
│   ├── MODES.md
│   ├── DYNAMIC_CONTROL.md
│   ├── BENCHMARK_MODE.md
│   ├── LOGVIEWER.md
│   ├── SETTINGS_PAGE.md
│   └── synapseEngine.gif  # Large but useful
├── development/           # Keep active dev guides
│   ├── DOCKER_SETUP.md
│   ├── TROUBLESHOOTING.md
│   └── EXPLORATION_REPORT.md
├── planning/              # Keep
│   ├── planning.md
│   └── opencode_integration_plan.md
├── troubleshooting/       # Keep
│   └── DOCKER_LLAMA_SERVER_CROSS_PLATFORM.md
└── archive/               # All historical/completed docs
    ├── SESSION_NOTES_ARCHIVE.md  # Nov 4 - Nov 11 entries
    ├── root/                     # Archived root files
    │   └── SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md
    ├── migration/                # All migration docs
    │   ├── MIGRATION_*.md files
    │   ├── BACKEND_NAMING_MIGRATION_SUMMARY.md
    │   └── SYNAPSE_MIGRATION_REFERENCE.md
    ├── implementation/           # Completed phases
    │   ├── PHASE_*.md files
    │   ├── ADMIN_PAGE_COMPLETE.md
    │   ├── QUERY_UI_COMPLETE.md
    │   ├── MODEL_MANAGEMENT_UI_COMPLETE.md
    │   ├── CGRAG_IMPLEMENTATION.md
    │   └── phase3/, phase4/ subdirs
    ├── development/              # Old session docs
    │   ├── SESSION1_COMPLETE.md
    │   ├── SESSION2_COMPLETE.md
    │   ├── TIMEOUT_*.md files
    │   └── VITE_ENV_VARS.md
    ├── moderator/                # Moderator feature docs
    │   ├── COUNCIL_MODERATOR_FEATURE.md
    │   ├── MODERATOR_*.md files
    │   └── ACTIVE_MODERATOR_IMPLEMENTATION.md
    ├── components/               # Component history
    │   └── (existing archive/components/)
    ├── phase-1/                  # Phase 1 history
    │   └── (existing archive/phase-1/)
    ├── fixes/                    # All fix documentation
    │   ├── (move from docs/fixes/)
    │   └── WEBSOCKET_CONNECTION_LOOP_FIX.md
    └── phases/                   # Old phase docs
        └── (move from docs/phases/)
```

---

## 5. Implementation Plan

### Phase 1: SESSION_NOTES.md Pruning (30 min)

**Task 1.1: Create archive file for old sessions**
- Create `docs/archive/SESSION_NOTES_ARCHIVE.md`
- Move entries older than Nov 12 (2+ weeks ago) to archive
- Preserve complete history, just relocated

**Task 1.2: Update main SESSION_NOTES.md**
- Keep header and Table of Contents
- Keep consolidated scrollbar section (valuable troubleshooting)
- Keep Nov 12-29 entries (recent 2.5 weeks)
- Add link to archive at bottom
- Target size: ~150KB (from 578KB)

**Acceptance Criteria:**
- [ ] SESSION_NOTES.md reduced to <200KB
- [ ] All historical entries preserved in archive
- [ ] Table of Contents updated with archive link
- [ ] No data loss

### Phase 2: Root Directory Cleanup (15 min)

**Task 2.1: Move reference materials to docs/**
```bash
mv ASCII_MASTER_GUIDE.md docs/guides/
mv SCIFI_GUI_RESEARCH.md docs/reference/
```

**Task 2.2: Archive old implementation plan**
```bash
mkdir -p docs/archive/root/
mv SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md docs/archive/root/
```

**Acceptance Criteria:**
- [ ] Root directory has exactly 4 markdown files
- [ ] Moved files are accessible in new locations
- [ ] No broken links in CLAUDE.md

### Phase 3: docs/ Consolidation (45 min)

**Task 3.1: Create reference/ directory and populate**
```bash
mkdir -p docs/reference/
mv docs/WEBTUI_STYLE_GUIDE.md docs/reference/
mv docs/WEBTUI_INTEGRATION_GUIDE.md docs/reference/
mv docs/SYSTEM_IDENTITY.md docs/reference/
mv docs/research/*.md docs/reference/
rmdir docs/research/
```

**Task 3.2: Archive migration documents**
```bash
mkdir -p docs/archive/migration/
mv docs/MIGRATION_*.md docs/archive/migration/
mv docs/BACKEND_NAMING_MIGRATION_SUMMARY.md docs/archive/migration/
mv docs/SYNAPSE_MIGRATION_REFERENCE.md docs/archive/migration/
```

**Task 3.3: Archive completed implementation docs**
```bash
mkdir -p docs/archive/implementation/
mv docs/implementation/PHASE_*.md docs/archive/implementation/
mv docs/implementation/ADMIN_PAGE_COMPLETE.md docs/archive/implementation/
mv docs/implementation/INTEGRATION_COMPLETE.md docs/archive/implementation/
mv docs/implementation/MODEL_MANAGEMENT_UI_COMPLETE.md docs/archive/implementation/
mv docs/implementation/QUERY_UI_COMPLETE.md docs/archive/implementation/
mv docs/implementation/RESPONSE_DISPLAY_IMPROVEMENTS.md docs/archive/implementation/
mv docs/implementation/CGRAG_IMPLEMENTATION.md docs/archive/implementation/
mv docs/implementation/COUNCIL_MODE_IMPLEMENTATION_GUIDE.md docs/archive/implementation/
mv docs/implementation/TRUE_MULTICHAT_IMPLEMENTATION_GUIDE.md docs/archive/implementation/
mv docs/implementation/phase3/ docs/archive/implementation/
mv docs/implementation/phase4/ docs/archive/implementation/
# Large MAGI files to archive
mv docs/implementation/MAGI_*.md docs/archive/implementation/
mv docs/implementation/UPDATE_MAGI.md docs/archive/implementation/
```

**Task 3.4: Archive old development docs**
```bash
mkdir -p docs/archive/development/
mv docs/development/SESSION*.md docs/archive/development/
mv docs/development/TIMEOUT_*.md docs/archive/development/
mv docs/development/VITE_ENV_VARS.md docs/archive/development/
mv docs/development/frontend-timeout-implementation.md docs/archive/development/
```

**Task 3.5: Archive moderator docs (feature stable)**
```bash
mkdir -p docs/archive/moderator/
mv docs/COUNCIL_MODERATOR_FEATURE.md docs/archive/moderator/
mv docs/MODERATOR_*.md docs/archive/moderator/
mv docs/ACTIVE_MODERATOR_IMPLEMENTATION.md docs/archive/moderator/
```

**Task 3.6: Archive fixes directory**
```bash
mv docs/fixes/* docs/archive/fixes/
rmdir docs/fixes/
```

**Task 3.7: Archive phases directory**
```bash
mv docs/phases/* docs/archive/phases/ 2>/dev/null || mkdir -p docs/archive/phases/
mv docs/phases/*.md docs/archive/phases/ 2>/dev/null
rmdir docs/phases/ 2>/dev/null || true
```

**Task 3.8: Merge testing into guides**
```bash
mv docs/testing/*.txt docs/archive/testing/ 2>/dev/null || mkdir -p docs/archive/testing/
mv docs/testing/* docs/archive/testing/ 2>/dev/null
rmdir docs/testing/ 2>/dev/null || true
```

**Task 3.9: Archive components docs**
```bash
mv docs/components/* docs/archive/components/ 2>/dev/null || true
rmdir docs/components/ 2>/dev/null || true
```

**Task 3.10: Clean up miscellaneous docs/ root files**
```bash
mv docs/DOCUMENTATION_LINKING_PLAN.md docs/archive/
mv docs/TEST_SUITE_SUMMARY.md docs/archive/
mv docs/PHASE_3_7_SUMMARY.md docs/archive/
mv docs/PROJECT_STATUS.md docs/archive/ # Duplicate of architecture/PROJECT_STATUS.md
```

**Acceptance Criteria:**
- [ ] docs/ has 8 clear subdirectories
- [ ] All historical docs preserved in archive/
- [ ] No duplicate files
- [ ] research/ removed (merged into reference/)
- [ ] fixes/ removed (merged into archive/)
- [ ] testing/ removed (content archived)
- [ ] components/ removed (merged into archive/)
- [ ] phases/ removed (merged into archive/)

### Phase 4: Update Documentation Index (20 min)

**Task 4.1: Rewrite docs/INDEX.md**
- Update to reflect new structure
- Add clear navigation for agents
- Link all active directories
- Note archive location for historical docs

**Task 4.2: Update docs/README.md**
- Sync with INDEX.md structure
- Add quick navigation section

**Task 4.3: Update CLAUDE.md references (if needed)**
- Check for any broken file references
- Update paths to moved files

**Acceptance Criteria:**
- [ ] INDEX.md accurately reflects new structure
- [ ] All links in documentation verified working
- [ ] Agents can navigate efficiently

### Phase 5: Cleanup and Verification (15 min)

**Task 5.1: Remove empty directories**
```bash
find docs/ -type d -empty -delete
```

**Task 5.2: Delete duplicate/obsolete files**
- docs/development/SESSION_NOTES.md (10KB - duplicate of root)
- Any .DS_Store files

**Task 5.3: Verify no broken links**
- Check CLAUDE.md references
- Check README.md links
- Spot-check archive links

**Acceptance Criteria:**
- [ ] No empty directories
- [ ] No duplicate files
- [ ] All documentation accessible

---

## 6. Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Broken links in CLAUDE.md | HIGH | Search/replace file paths before moving |
| Lost session history | HIGH | Always archive, never delete |
| Agent confusion during transition | MEDIUM | Update INDEX.md first |
| Large GIF file (13MB) | LOW | Keep in features/ - useful for demos |

---

## 7. Reference Documentation

- [CLAUDE.md](../CLAUDE.md) - Contains file references to update
- [docs/INDEX.md](../docs/INDEX.md) - Current navigation structure
- [SESSION_NOTES.md](../SESSION_NOTES.md) - 54 sessions to triage
- [@record-keeper agent](../../.claude/agents/record-keeper.md) - Session documentation guidelines

---

## 8. Definition of Done

- [ ] Root directory contains exactly 4 markdown files (CLAUDE.md, README.md, SESSION_NOTES.md, PROJECT_OVERVIEW.md)
- [ ] SESSION_NOTES.md is under 200KB with archive link
- [ ] docs/ has 8 well-organized subdirectories
- [ ] All historical content preserved in docs/archive/
- [ ] INDEX.md updated with accurate structure
- [ ] No broken links in essential documentation
- [ ] Agents can easily navigate to find information

---

## 9. Next Actions

**Immediate (Phase 1-2):**
1. Create SESSION_NOTES_ARCHIVE.md with Nov 4-11 entries
2. Prune SESSION_NOTES.md to Nov 12-29 entries
3. Move ASCII_MASTER_GUIDE.md and SCIFI_GUI_RESEARCH.md
4. Archive SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md

**Follow-up (Phase 3-5):**
5. Execute docs/ consolidation commands
6. Update INDEX.md
7. Verify all links
8. Remove empty directories

---

## 10. Estimated Effort

| Phase | Time | Confidence |
|-------|------|------------|
| Phase 1: SESSION_NOTES pruning | 30 min | HIGH |
| Phase 2: Root cleanup | 15 min | HIGH |
| Phase 3: docs/ consolidation | 45 min | MEDIUM |
| Phase 4: Index updates | 20 min | HIGH |
| Phase 5: Verification | 15 min | HIGH |
| **Total** | **~2 hours** | **HIGH** |

---

## Appendix: Complete File Move Commands

```bash
#!/bin/bash
# Documentation Cleanup Script
# Run from SYNAPSE_ENGINE root

# Phase 2: Root cleanup
mkdir -p docs/archive/root/
mv ASCII_MASTER_GUIDE.md docs/guides/
mv SCIFI_GUI_RESEARCH.md docs/reference/ 2>/dev/null || mkdir -p docs/reference/ && mv SCIFI_GUI_RESEARCH.md docs/reference/
mv SYNAPSE_ASCII_UI_IMPLEMENTATION_PLAN.md docs/archive/root/

# Phase 3: docs/ consolidation
mkdir -p docs/reference/
mv docs/WEBTUI_STYLE_GUIDE.md docs/reference/
mv docs/WEBTUI_INTEGRATION_GUIDE.md docs/reference/
mv docs/SYSTEM_IDENTITY.md docs/reference/
mv docs/research/*.md docs/reference/ 2>/dev/null
rmdir docs/research/ 2>/dev/null

mkdir -p docs/archive/migration/
mv docs/MIGRATION_*.md docs/archive/migration/ 2>/dev/null
mv docs/BACKEND_NAMING_MIGRATION_SUMMARY.md docs/archive/migration/ 2>/dev/null
mv docs/SYNAPSE_MIGRATION_REFERENCE.md docs/archive/migration/ 2>/dev/null

mkdir -p docs/archive/implementation/
mv docs/implementation/PHASE_*.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/ADMIN_PAGE_COMPLETE.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/INTEGRATION_COMPLETE.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/MODEL_MANAGEMENT_UI_COMPLETE.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/QUERY_UI_COMPLETE.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/RESPONSE_DISPLAY_IMPROVEMENTS.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/CGRAG_IMPLEMENTATION.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/COUNCIL_MODE_IMPLEMENTATION_GUIDE.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/TRUE_MULTICHAT_IMPLEMENTATION_GUIDE.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/phase3/ docs/archive/implementation/ 2>/dev/null
mv docs/implementation/phase4/ docs/archive/implementation/ 2>/dev/null
mv docs/implementation/MAGI_*.md docs/archive/implementation/ 2>/dev/null
mv docs/implementation/UPDATE_MAGI.md docs/archive/implementation/ 2>/dev/null

mkdir -p docs/archive/development/
mv docs/development/SESSION*.md docs/archive/development/ 2>/dev/null
mv docs/development/TIMEOUT_*.md docs/archive/development/ 2>/dev/null
mv docs/development/VITE_ENV_VARS.md docs/archive/development/ 2>/dev/null
mv docs/development/frontend-timeout-implementation.md docs/archive/development/ 2>/dev/null

mkdir -p docs/archive/moderator/
mv docs/COUNCIL_MODERATOR_FEATURE.md docs/archive/moderator/ 2>/dev/null
mv docs/MODERATOR_*.md docs/archive/moderator/ 2>/dev/null
mv docs/ACTIVE_MODERATOR_IMPLEMENTATION.md docs/archive/moderator/ 2>/dev/null

mkdir -p docs/archive/fixes/
mv docs/fixes/* docs/archive/fixes/ 2>/dev/null
rmdir docs/fixes/ 2>/dev/null

mkdir -p docs/archive/phases/
mv docs/phases/* docs/archive/phases/ 2>/dev/null
rmdir docs/phases/ 2>/dev/null

mkdir -p docs/archive/testing/
mv docs/testing/* docs/archive/testing/ 2>/dev/null
rmdir docs/testing/ 2>/dev/null

mkdir -p docs/archive/components-docs/
mv docs/components/* docs/archive/components-docs/ 2>/dev/null
rmdir docs/components/ 2>/dev/null

mv docs/DOCUMENTATION_LINKING_PLAN.md docs/archive/ 2>/dev/null
mv docs/TEST_SUITE_SUMMARY.md docs/archive/ 2>/dev/null
mv docs/PHASE_3_7_SUMMARY.md docs/archive/ 2>/dev/null

# Delete duplicate
rm docs/development/SESSION_NOTES.md 2>/dev/null

# Cleanup
find docs/ -type d -empty -delete 2>/dev/null
find docs/ -name ".DS_Store" -delete 2>/dev/null

echo "Documentation cleanup complete!"
```
