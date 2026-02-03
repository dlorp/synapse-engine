# Synapse Engine Documentation

This directory contains all project documentation organized by category.

**Last Updated:** 2025-02-03

---

## Quick Navigation

| Need | Location |
|------|----------|
| **Getting started?** | [guides/DOCKER_QUICKSTART.md](./guides/DOCKER_QUICKSTART.md) |
| **System architecture?** | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| **Query modes?** | [features/MODES.md](./features/MODES.md) |
| **API reference?** | [API.md](./API.md) |
| **Metal (Apple Silicon)?** | [METAL.md](./METAL.md) |
| **CGRAG setup?** | [CGRAG.md](./CGRAG.md) |
| **Security model?** | [SECURITY.md](./SECURITY.md) |
| **Docker commands?** | [guides/DOCKER_QUICK_REFERENCE.md](./guides/DOCKER_QUICK_REFERENCE.md) |
| **UI styling?** | [reference/WEBTUI_STYLE_GUIDE.md](./reference/WEBTUI_STYLE_GUIDE.md) |

---

## Directory Structure

```
docs/
├── API.md                 # Complete API reference
├── ARCHITECTURE.md        # System design overview
├── CGRAG.md               # Document indexing & retrieval
├── METAL.md               # Apple Silicon GPU setup
├── README.md              # This file
├── SECURITY.md            # Security model
│
├── architecture/          # Detailed architecture docs
│   ├── DOCKER_INFRASTRUCTURE.md
│   ├── PAGE_BOUNDARIES.md
│   └── PROJECT_SPECfINAL.md
│
├── features/              # Feature specifications
│   ├── BENCHMARK_MODE.md
│   ├── DYNAMIC_CONTROL.md
│   ├── LOGVIEWER.md
│   ├── MODES.md
│   └── SETTINGS_PAGE.md
│
├── guides/                # How-to guides
│   ├── ADMIN_QUICK_REFERENCE.md
│   ├── DOCKER_QUICK_REFERENCE.md
│   ├── DOCKER_QUICKSTART.md
│   ├── PROFILE_QUICK_REFERENCE.md
│   ├── QUICK_START_MODEL_MANAGEMENT.md
│   └── VISUAL_TESTING_GUIDE.md
│
├── reference/             # Style guides & integration
│   ├── WEBTUI_INTEGRATION_GUIDE.md
│   └── WEBTUI_STYLE_GUIDE.md
│
├── research/              # Research & patterns
│   └── llm-orchestration-patterns.md
│
├── security/              # Security documentation
│   └── SHELL_TOOL_SECURITY.md
│
└── troubleshooting/       # Troubleshooting guides
    └── DOCKER_LLAMA_SERVER_CROSS_PLATFORM.md
```

---

## Root-Level Documentation

Files in the project root:

| File | Purpose |
|------|---------|
| `/README.md` | Main project README with quick start |
| `/CONTRIBUTING.md` | Contribution guidelines |
| `/LICENSE` | PolyForm NonCommercial 1.0.0 license |

---

## Adding New Documentation

1. **Root docs/** - Overview and getting-started content
2. **architecture/** - System design and infrastructure details
3. **features/** - Feature specifications and usage
4. **guides/** - Step-by-step how-to guides
5. **reference/** - Style guides and API integration docs
6. **security/** - Security-related documentation
7. **troubleshooting/** - Problem-solving guides
8. **research/** - Research notes and design patterns

### Documentation Style

- Use Mermaid diagrams for architecture visualizations
- Include code examples with syntax highlighting
- Keep sections focused and scannable
- Link to related documentation
