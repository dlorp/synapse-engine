# S.Y.N.A.P.S.E. ENGINE Documentation

This directory contains all project documentation organized by category.

**Last Updated:** 2025-11-29

---

## Directory Structure

```
docs/
├── architecture/     # System design & infrastructure
├── features/         # Feature specifications
├── guides/           # How-to guides & quickstarts
├── reference/        # Style guides & API docs (NEW)
├── implementation/   # Active phase work (phase3, phase4)
├── components/       # Component documentation
├── fixes/            # Recent bug fix documentation
├── development/      # Development setup & notes
├── testing/          # Test documentation
└── archive/          # Historical documentation
    ├── session-history/
    ├── implementation-plans/
    ├── research/
    ├── migration/
    ├── phase-1/
    └── components/
```

---

## Quick Navigation

| Need | Location |
|------|----------|
| **Starting the project?** | [guides/DOCKER_QUICKSTART.md](./guides/DOCKER_QUICKSTART.md) |
| **System architecture?** | [architecture/PROJECT_SPECfINAL.md](./architecture/PROJECT_SPECfINAL.md) |
| **Query modes?** | [features/MODES.md](./features/MODES.md) |
| **UI styling?** | [reference/WEBTUI_STYLE_GUIDE.md](./reference/WEBTUI_STYLE_GUIDE.md) |
| **Docker commands?** | [guides/DOCKER_QUICK_REFERENCE.md](./guides/DOCKER_QUICK_REFERENCE.md) |
| **Recent development?** | [../SESSION_NOTES.md](../SESSION_NOTES.md) |

---

## Agent-Referenced Paths

The following paths are referenced by Claude Code agents and must exist:

- `docs/guides/DOCKER_QUICK_REFERENCE.md` - DevOps, WebSocket agents
- `docs/features/MODES.md` - Query Mode, CGRAG agents
- `docs/architecture/*` - Security agent

---

## Root-Level Documentation

Files that remain in the project root:

| File | Purpose |
|------|---------|
| `/README.md` | Main project README |
| `/CLAUDE.md` | Claude Code project instructions |
| `/SESSION_NOTES.md` | Development log (recent 2 weeks) |
| `/PROJECT_OVERVIEW.md` | High-level architecture |
| `/ASCII_MASTER_GUIDE.md` | Terminal aesthetic design guide |

---

## Adding New Documentation

1. **Root** - Only essential files (max 5)
2. **architecture/** - System design documents
3. **features/** - Feature specifications
4. **guides/** - How-to guides and quickstarts
5. **reference/** - Style guides and API docs
6. **implementation/** - Active phase work
7. **archive/** - Historical and completed work

See [INDEX.md](./INDEX.md) for detailed directory contents.
