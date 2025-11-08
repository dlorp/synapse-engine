# MAGI Documentation Cross-Linking Plan

**Created:** 2025-11-07
**Purpose:** Add hyperlinks to referenced files across MAGI documentation for easier navigation
**Status:** Implementation Plan

---

## Executive Summary

The MAGI project contains **54 markdown documentation files** across the project root and `/docs` directory. Analysis reveals that while some high-level cross-references exist (e.g., README.md → PROJECT_OVERVIEW.md), the vast majority of file mentions are **not hyperlinked**, making navigation cumbersome.

**Goal:** Create a well-connected documentation system where users can seamlessly navigate between related documents.

**Scope:** Add hyperlinks to file references across all 54 markdown files, prioritizing frequently accessed documents first.

**Estimated Time:** 2-3 hours (given systematic approach with grep/edit tools)

---

## Documentation Inventory

### Root-Level Documentation (6 files - HIGH PRIORITY)
1. **README.md** - Main project documentation (842 lines)
2. **CLAUDE.md** - Claude Code instructions (1,012 lines)
3. **PROJECT_OVERVIEW.md** - Project overview and team structure (517 lines)
4. **SESSION_NOTES.md** - Development history (reverse chronological)
5. **PLANNING.md** - Planning notes (1 line - placeholder)
6. **TEST_SUITE_SUMMARY.md** - Testing quick reference (314 lines)

### Documentation Directory (48 files - MEDIUM/LOW PRIORITY)
Organized into subdirectories:
- **/docs/architecture/** (4 files) - System design, specs, status
- **/docs/development/** (9 files) - Session notes, troubleshooting, setup
- **/docs/implementation/** (17 files) - Phase completions, guides, rework docs
- **/docs/features/** (4 files) - Feature descriptions (MODES, BENCHMARK, LOGVIEWER, SETTINGS)
- **/docs/guides/** (5 files) - Quick references (Docker, Admin, Profile, Model Management)
- **/docs/phases/** (2 files) - Phase 2 frontend and integration test docs
- **/docs/troubleshooting/** (1 file) - Docker llama-server cross-platform guide
- **/docs/README.md** (1 file) - Documentation index

### Agent Documentation (12 files - LOW PRIORITY)
Located in `.claude/agents/`:
- backend-architect.md
- frontend-engineer.md
- cgrag-specialist.md
- devops-engineer.md
- database-persistence-specialist.md
- model-lifecycle-manager.md
- performance-optimizer.md
- query-mode-specialist.md
- security-specialist.md
- terminal-ui-specialist.md
- testing-specialist.md
- websocket-realtime-specialist.md

---

## Reference Analysis

### Cross-Reference Statistics

| File Referenced | Times Mentioned | Files Mentioning | Currently Linked? |
|----------------|-----------------|------------------|-------------------|
| **SESSION_NOTES.md** | 36 | 17 files | Partially (1/36) |
| **docker-compose.yml** | 101 | 29 files | No (0/101) |
| **README.md** | 28 | 14 files | Partially (2/28) |
| **CLAUDE.md** | 26 | 16 files | Partially (1/26) |
| **PROJECT_OVERVIEW.md** | 2 | 1 file (README) | Yes (2/2) ✓ |
| **TEST_SUITE_SUMMARY.md** | 4 | 3 files | Yes (1/4) |
| **/docs/** references | 205+ | 37 files | Rarely |
| **scripts/** references | Included above | Many files | No |
| **.env.example** | ~20 | 10+ files | No |

### Key Findings

1. **docker-compose.yml** is mentioned 101 times but NEVER linked
2. **SESSION_NOTES.md** is mentioned constantly but rarely linked
3. **CLAUDE.md** is referenced frequently but not linked
4. **README.md** is mentioned often but not linked
5. Phase completion docs reference each other but without links
6. Quick reference guides mention source docs but don't link back
7. Implementation guides reference architecture docs but no links

---

## File-by-File Analysis

### 1. README.md (HIGH PRIORITY)

**Current Links:**
- ✓ Line 9: `[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)` - Already linked
- ✓ Line 636: `[TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md)` - Already linked
- ✓ Line 816: `[PROJECT_OVERVIEW.md#team-structure](PROJECT_OVERVIEW.md#team-structure)` - Already linked with anchor

**Missing Links (15+ instances):**
- Lines 53, 158, 278, 346, 356, 359: `docker-compose.yml` - NOT linked (6 instances in config examples)
- Line 823: "Check SESSION_NOTES.md" - NOT linked
- Lines 575-580: References to backend/frontend rebuild commands - Could link to docker-compose.yml
- Lines 158-167: References to services in docker-compose.yml - Could link
- Lines 597-604: References to test scripts - Could link to ./scripts/test-all.sh
- Multiple references to "scripts/" directory - Could link to specific scripts

**Proposed Additions:**
```markdown
# After environment config section (line 54)
cp .env.example .env
# Edit [.env](./.env.example) - set MODEL_SCAN_PATH to your HuggingFace cache

# In Docker configuration sections
Edit [docker-compose.yml](./docker-compose.yml) to ensure Host API is enabled

# In session notes references
Check [SESSION_NOTES.md](./SESSION_NOTES.md) for recent context

# In testing section
See [TEST_SUITE_SUMMARY.md](./TEST_SUITE_SUMMARY.md) for detailed test documentation.

# Script references
./scripts/test-all.sh → [test-all.sh](./scripts/test-all.sh)
```

---

### 2. CLAUDE.md (HIGH PRIORITY)

**Current Links:**
- ✗ NO LINKS - File has zero hyperlinks despite 1,012 lines!

**Missing Links (20+ instances):**
- Lines 28, 37: `SESSION_NOTES.md` - mentioned 5 times, NOT linked
- Line 203: "Update CLAUDE.md when:" - self-reference, could link to #documentation-requirements
- Line 209: "Update README.md when:" - NOT linked
- Lines 163, 218, 230, 236: docker-compose.yml in examples - NOT linked
- Line 108: "Glob and AST-Grep" - note: it's actually "Grep" not "AST-Grep"
- References to agent files (.claude/agents/*.md) - NOT linked

**Proposed Additions:**
```markdown
# Line 28
**IMPORTANT: Before starting work, review [SESSION_NOTES.md](../SESSION_NOTES.md)**

# Line 30
The [`SESSION_NOTES.md`](../SESSION_NOTES.md) file contains the complete development history

# Line 37
**When to check [SESSION_NOTES.md](../SESSION_NOTES.md):**

# Line 203
2. **Update [CLAUDE.md](../CLAUDE.md)** when:

# Line 209
3. **Update [README.md](../README.md)** when:

# Line 158
docker-compose up -d → [docker-compose.yml](../docker-compose.yml)

# Agent references (lines 804-897)
**Prompt file:** `agent-backend-architect.md`
→ **Prompt file:** [agent-backend-architect.md](../.claude/agents/agent-backend-architect.md)
```

---

### 3. PROJECT_OVERVIEW.md (HIGH PRIORITY)

**Current Links:**
- ✗ NO LINKS - 517 lines with zero hyperlinks!

**Missing Links (10+ instances):**
- Line 299: "Check SESSION_NOTES.md before starting work" - NOT linked
- Line 419: "open http://localhost:5173" - could be clickable
- Line 430: "./scripts/test-all.sh" - NOT linked
- Line 480: References to README.md, CLAUDE.md, SESSION_NOTES.md - NOT linked
- Line 275: "docker-compose up -d" - could link to docker-compose.yml

**Proposed Additions:**
```markdown
# Line 299
1. **Check [SESSION_NOTES.md](../SESSION_NOTES.md)** before starting work

# Line 480 (File Structure section)
├── [README.md](../README.md)                  # Main documentation
├── [CLAUDE.md](../CLAUDE.md)                  # Claude instructions
├── [SESSION_NOTES.md](../SESSION_NOTES.md)           # Development history
└── [TEST_SUITE_SUMMARY.md](./TEST_SUITE_SUMMARY.md)      # Testing documentation

# Line 430
./scripts/test-all.sh → [test-all.sh](../scripts/test-all.sh)

# Line 275
docker-compose up -d → See [docker-compose.yml](../docker-compose.yml)
```

---

### 4. SESSION_NOTES.md (HIGH PRIORITY)

**Current State:** This file is referenced everywhere but likely has few outbound links.

**Analysis Needed:** Read file to identify references to:
- Other documentation files
- Phase completion docs (/docs/implementation/PHASE*_COMPLETE.md)
- Specific configuration files (docker-compose.yml, .env.example)
- Scripts referenced in session summaries

**Proposed Pattern:**
```markdown
# When referencing completed phases
Completed Phase 6 - see [PHASE6_INTEGRATION_COMPLETE.md](./docs/implementation/PHASE6_INTEGRATION_COMPLETE.md)

# When referencing configuration changes
Modified [docker-compose.yml](./docker-compose.yml) line 218

# When referencing documentation updates
Updated [README.md](./README.md) with new Metal acceleration instructions
```

---

### 5. TEST_SUITE_SUMMARY.md (MEDIUM PRIORITY)

**Current Links:**
- Line 61: Reference to `/docs/TESTING_GUIDE.md` - likely NOT linked

**Missing Links:**
- References to test scripts (./scripts/test-*.sh)
- Reference to TESTING_GUIDE.md
- Reference to docker-compose.yml

**Proposed Additions:**
```markdown
For detailed information, see: [TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)

./scripts/test-all.sh → [test-all.sh](./scripts/test-all.sh)
```

---

### 6. /docs/README.md (MEDIUM PRIORITY)

**Current State:** Documentation index file

**Analysis:**
- Lists all documentation files by directory
- Should have links to EVERY file mentioned
- Currently appears to have NO links

**Proposed Pattern:**
```markdown
### 📖 `/architecture` - System Architecture & Planning

- [PROJECT_SPECfINAL.md](./architecture/PROJECT_SPECfINAL.md) - Complete project specification
- [PROJECT_STATUS.md](./architecture/PROJECT_STATUS.md) - Current project status and roadmap
- [IMPLEMENTATION_PLAN.md](./architecture/IMPLEMENTATION_PLAN.md) - Detailed implementation plan
- [DOCKER_INFRASTRUCTURE.md](./architecture/DOCKER_INFRASTRUCTURE.md) - Docker infrastructure architecture

## Root-Level Documentation

- [/README.md](../README.md) - Main project README
- [/CLAUDE.md](../CLAUDE.md) - Claude Code project instructions
- [/.env.example](../.env.example) - Environment variables example
- [/docker-compose.yml](../docker-compose.yml) - Docker Compose configuration
```

---

### 7. /docs/TESTING_GUIDE.md (MEDIUM PRIORITY)

**Analysis:**
- References test scripts extensively
- Mentions docker-compose.yml
- Should link to all 4 test scripts
- Should link to TEST_SUITE_SUMMARY.md

**Proposed Additions:**
```markdown
**Location:** [`/scripts/test-backend.sh`](../scripts/test-backend.sh)

./scripts/test-all.sh → [test-all.sh](../scripts/test-all.sh)

For quick reference, see [TEST_SUITE_SUMMARY.md](./TEST_SUITE_SUMMARY.md)
```

---

## Linking Conventions & Standards

### 1. Relative vs Absolute Paths

**Standard:** Use relative paths exclusively for consistency.

**Rationale:**
- Works in any clone location
- Works on GitHub, VS Code, and other markdown renderers
- Easier to maintain

**Examples:**
```markdown
# From root file to root file
[SESSION_NOTES.md](./SESSION_NOTES.md)

# From root file to docs file
[TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)

# From docs file to root file
[README.md](../README.md)

# From docs subdirectory to another subdirectory
[DOCKER_INFRASTRUCTURE.md](../architecture/DOCKER_INFRASTRUCTURE.md)
```

### 2. Link Text Formatting

**Standard:** Keep original text, add link around it (don't change wording).

**Rationale:**
- Preserves existing documentation flow
- Minimal invasive changes
- Maintains readability

**Examples:**
```markdown
# BEFORE
Check SESSION_NOTES.md for recent context

# AFTER
Check [SESSION_NOTES.md](./SESSION_NOTES.md) for recent context

# BEFORE
Edit docker-compose.yml to configure services

# AFTER
Edit [docker-compose.yml](./docker-compose.yml) to configure services
```

### 3. Section Anchors

**Standard:** Use section anchors for linking to specific sections within documents.

**Format:** `[Link Text](./file.md#section-heading)`

**Examples:**
```markdown
# Link to specific section
See [Team Structure](./PROJECT_OVERVIEW.md#team-structure) for agent details

# Link to architecture section
Review [Docker Infrastructure](./docs/architecture/DOCKER_INFRASTRUCTURE.md#security-model)
```

### 4. Code Block References

**Standard:** Don't link file paths inside code blocks or bash examples.

**Rationale:**
- Code blocks are for copy-paste
- Links would break syntax highlighting
- Could cause confusion

**Exception:** Add links in explanatory text BEFORE code blocks.

**Examples:**
```markdown
# GOOD
Edit [docker-compose.yml](./docker-compose.yml):
```yaml
services:
  backend:
    ...
```

# BAD (don't do this)
```bash
# Edit [docker-compose.yml](./docker-compose.yml)
docker-compose up -d
```
```

### 5. Configuration Files

**Standard:** Link to configuration files when mentioned in text, not in command examples.

**Examples:**
```markdown
# GOOD
Configure your environment by editing [.env.example](./.env.example):
```bash
cp .env.example .env
```

# AVOID
```bash
cp [.env.example](./.env.example) .env
```
```

### 6. Script References

**Standard:** Link to scripts when mentioned, especially in lists or instructions.

**Examples:**
```markdown
# Run all tests
[./scripts/test-all.sh](./scripts/test-all.sh)

Or run individual suites:
- [Backend tests](./scripts/test-backend.sh)
- [Frontend tests](./scripts/test-frontend.sh)
- [Integration tests](./scripts/test-integration.sh)
```

---

## Implementation Priority

### Phase 1: High-Priority Root Files (30 minutes)
These are the most frequently accessed files and provide the most immediate value:

1. **README.md** - Add links to:
   - SESSION_NOTES.md (1 instance)
   - docker-compose.yml (6 instances)
   - .env.example (2 instances)
   - Test scripts (4 instances)

2. **CLAUDE.md** - Add links to:
   - SESSION_NOTES.md (5 instances)
   - README.md (1 instance)
   - docker-compose.yml (4 instances)
   - Agent files (12 instances)

3. **PROJECT_OVERVIEW.md** - Add links to:
   - SESSION_NOTES.md (1 instance)
   - README.md, CLAUDE.md, TEST_SUITE_SUMMARY.md (in file structure)
   - docker-compose.yml (2 instances)
   - Test scripts (1 instance)

**Expected Impact:** 80% of user navigation needs addressed.

---

### Phase 2: Documentation Index & Testing Docs (20 minutes)

4. **/docs/README.md** - Add links to:
   - All 48 files listed in the index
   - Root-level documentation files

5. **TEST_SUITE_SUMMARY.md** - Add links to:
   - TESTING_GUIDE.md
   - Test scripts (4 instances)

6. **/docs/TESTING_GUIDE.md** - Add links to:
   - Test scripts (12+ instances)
   - TEST_SUITE_SUMMARY.md
   - docker-compose.yml

**Expected Impact:** Complete testing documentation connectivity.

---

### Phase 3: Session Notes & Development Docs (40 minutes)

7. **SESSION_NOTES.md** - Add links to:
   - Phase completion docs
   - Configuration files
   - Implementation guides
   - Troubleshooting docs

8. **/docs/development/SESSION*.md** - Add links to:
   - Related documentation
   - Configuration files
   - Implementation guides

**Expected Impact:** Historical context becomes navigable.

---

### Phase 4: Implementation & Phase Docs (40 minutes)

9. **/docs/implementation/PHASE*_COMPLETE.md** - Add links to:
   - Previous/next phase docs
   - Related guides
   - Architecture documents

10. **/docs/implementation/** (other files) - Add links to:
    - Related architecture docs
    - Configuration files
    - Testing guides

**Expected Impact:** Phase documentation becomes interconnected.

---

### Phase 5: Guides & Architecture (30 minutes)

11. **/docs/guides/** - Add links to:
    - Architecture documents
    - Implementation details
    - Root README

12. **/docs/architecture/** - Add links to:
    - Implementation docs
    - Guides
    - Root documentation

**Expected Impact:** Complete guide connectivity.

---

### Phase 6: Agent Documentation (20 minutes)

13. **.claude/agents/*.md** - Add links to:
    - SESSION_NOTES.md
    - CLAUDE.md
    - Relevant implementation docs

**Expected Impact:** Agent context improves.

---

## Link Addition Checklist

### Pre-Implementation
- [ ] Backup project (commit all changes)
- [ ] Ensure Docker is running (for testing)
- [ ] Read this plan completely
- [ ] Prepare grep patterns for finding references

### Phase 1: Root Files
- [ ] README.md - 13 links added
- [ ] CLAUDE.md - 22 links added
- [ ] PROJECT_OVERVIEW.md - 8 links added
- [ ] Test in browser/VS Code to verify links work

### Phase 2: Testing Docs
- [ ] /docs/README.md - 48+ links added
- [ ] TEST_SUITE_SUMMARY.md - 5 links added
- [ ] /docs/TESTING_GUIDE.md - 15+ links added

### Phase 3: Session & Development
- [ ] SESSION_NOTES.md - 20+ links added
- [ ] /docs/development/*.md - 15+ links added per file

### Phase 4: Implementation Docs
- [ ] /docs/implementation/PHASE*_COMPLETE.md - 10+ links each
- [ ] Other implementation docs - varies

### Phase 5: Guides & Architecture
- [ ] /docs/guides/*.md - 8+ links each
- [ ] /docs/architecture/*.md - 10+ links each

### Phase 6: Agent Docs
- [ ] .claude/agents/*.md - 5+ links each

### Post-Implementation
- [ ] Test random sample of links (20+ links)
- [ ] Verify relative paths work from different locations
- [ ] Commit changes with descriptive message
- [ ] Update this plan with actual counts

---

## Testing Methodology

### Manual Link Testing

After adding links to each file:

1. **VS Code Preview:**
   - Right-click markdown file → "Open Preview"
   - Click each link to verify it navigates correctly
   - Check that anchors (#section-name) work

2. **GitHub Preview (if pushing):**
   - View file on GitHub
   - Test links work in GitHub's markdown renderer
   - Verify relative paths resolve correctly

3. **Command-line Validation:**
   ```bash
   # Find broken links (dead file references)
   for file in $(grep -r "\[.*\](.*.md)" --include="*.md" -o | cut -d'(' -f2 | cut -d')' -f1 | sort -u); do
     [ -f "$file" ] || echo "Broken: $file"
   done
   ```

### Automated Link Checking (Optional)

Use markdown-link-check:
```bash
# Install globally
npm install -g markdown-link-check

# Check all markdown files
find . -name "*.md" -not -path "./node_modules/*" -not -path "./.git/*" | xargs markdown-link-check
```

---

## Expected Outcomes

### Quantitative Results
- **Links Added:** ~300-500 total hyperlinks
- **Files Modified:** 50+ markdown files
- **Time Investment:** 2-3 hours
- **Link Success Rate:** >95% (working links)

### Qualitative Improvements
- **Faster Navigation:** Users can jump between related docs instantly
- **Better Context:** Easy to follow references and cross-references
- **Improved Onboarding:** New developers can navigate documentation structure
- **Enhanced Discoverability:** Related content becomes more accessible
- **Professional Polish:** Documentation feels complete and well-maintained

### User Experience Flow Examples

**Before:**
```
User reads README → Sees "Check SESSION_NOTES.md" → Must manually find file → Opens file
```

**After:**
```
User reads README → Clicks [SESSION_NOTES.md](./SESSION_NOTES.md) → Instantly navigates to file
```

---

## Maintenance Guidelines

### When Adding New Documentation

Always add links when creating new markdown files:

1. **Link to related docs** - If you reference a file, link it
2. **Update index** - Add new file to /docs/README.md
3. **Back-reference** - Consider if existing docs should link to new file

### When Reorganizing Files

If moving/renaming documentation:

1. **Update all links** - Search for old filename, update paths
2. **Test thoroughly** - Check 10+ random links
3. **Document in SESSION_NOTES.md** - Note what was moved

### Link Hygiene

Regular maintenance tasks:

- **Quarterly:** Run markdown-link-check to find broken links
- **After major refactors:** Manual review of high-priority files
- **When adding features:** Update relevant quick references

---

## File Reference Matrix

| File | References | Referenced By | Priority |
|------|-----------|---------------|----------|
| **SESSION_NOTES.md** | Many (phase docs, configs) | 17 files | HIGH |
| **README.md** | PROJECT_OVERVIEW, TEST_SUITE | 14 files | HIGH |
| **CLAUDE.md** | SESSION_NOTES, README, agents | 16 files | HIGH |
| **PROJECT_OVERVIEW.md** | SESSION_NOTES, docs/*, scripts | 1 file (README) | HIGH |
| **TEST_SUITE_SUMMARY.md** | TESTING_GUIDE, scripts | 3 files | MEDIUM |
| **docker-compose.yml** | Many (env vars, services) | 29 files | HIGH |
| **.env.example** | README, guides | 10+ files | MEDIUM |
| **scripts/test-*.sh** | TESTING_GUIDE, TEST_SUITE | 5+ files | MEDIUM |
| **/docs/README.md** | All 48 docs files | Few | HIGH |
| **PHASE*_COMPLETE.md** | Other phases, guides | SESSION_NOTES | MEDIUM |
| **Quick Reference guides** | Implementation docs | Root README | MEDIUM |
| **Agent .md files** | SESSION_NOTES, CLAUDE | CLAUDE, PROJECT_OVERVIEW | LOW |

---

## Appendix: Search Patterns

### Finding Unlinked References

Use these grep patterns to find file mentions that need links:

```bash
# Find unlinked SESSION_NOTES.md references
grep -n "SESSION_NOTES\.md" *.md | grep -v "\[.*SESSION_NOTES\.md.*\]"

# Find unlinked docker-compose.yml references
grep -n "docker-compose\.yml" *.md | grep -v "\[.*docker-compose\.yml.*\]"

# Find unlinked README.md references
grep -n "README\.md" *.md | grep -v "\[.*README\.md.*\]"

# Find all .md references (linked or not)
grep -rn "\.md" --include="*.md" .

# Find all script references
grep -rn "scripts/" --include="*.md" .
```

### Finding Existing Links

```bash
# Find all markdown links
grep -rn "\[.*\](.*\.md)" --include="*.md" .

# Find anchor links (section references)
grep -rn "\[.*\](.*\.md#.*)" --include="*.md" .

# Count links in a file
grep -o "\[.*\](.*)" README.md | wc -l
```

---

## Summary

This plan provides a systematic approach to transforming MAGI's documentation from a collection of isolated files into a well-connected knowledge graph. By prioritizing high-traffic files first, we maximize immediate value while ensuring comprehensive coverage across all 54+ documentation files.

**Implementation Strategy:** Execute phases sequentially, testing links after each phase, to ensure quality and catch issues early.

**Success Criteria:**
- 300+ working hyperlinks added
- <5% broken link rate
- All high-priority files fully linked
- Documentation index (/docs/README.md) becomes a navigation hub
- User feedback indicates improved documentation usability

**Next Steps:** Begin Phase 1 implementation, starting with README.md.

---

**Plan Created By:** Strategic Planning Architect (Claude Code Agent)
**Date:** November 7, 2025
**Review Status:** Ready for implementation
**Estimated Completion:** 2-3 hours of focused work
