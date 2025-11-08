# MAGI Multi-Model Orchestration WebUI - Implementation Plan

**Project Status:** ✅ Session 1 COMPLETE | 📅 Ready for Session 2
**Current Phase:** Session 1 Complete - Infrastructure + UI Skeleton
**Last Updated:** 2025-11-02 (Session 1 Complete at 2:15 PM PST)
**Environment:** macOS with models running on host (localhost:8080-8083)

**Related Documentation:**
- [Project Specification](PROJECT_SPECfINAL.md) - Complete specification
- [Project Status](PROJECT_STATUS.md) - Current implementation status
- [Docker Infrastructure](DOCKER_INFRASTRUCTURE.md) - Docker setup details
- [Testing Guide](../TESTING_GUIDE.md) - Testing procedures

---

## Overview

Building a terminal-aesthetic WebUI for orchestrating multiple local LLM instances with CGRAG.

**Implementation Strategy:** UI-first approach - get the visual foundation running, then connect backend functionality.

---

## Session 1: Infrastructure + UI Skeleton ✅ COMPLETE

**Goal:** Beautiful terminal-style UI rendering + basic backend structure
**Estimated Time:** 4-5 hours
**Actual Time:** ~4.5 hours
**Status:** ✅ **COMPLETE** - All objectives achieved!

**Live Services:**
- Frontend: http://localhost:5173 (Vite dev server with HMR)
- Backend: http://localhost:8000 (Uvicorn with hot reload)
- API Docs: http://localhost:8000/api/docs

**See [SESSION1_COMPLETE.md](./SESSION1_COMPLETE.md) for comprehensive summary.**

### Part 1: Project Scaffolding (30 minutes) 🟡

- [ ] Create complete directory structure
- [ ] Initialize git repository with .gitignore
- [x] Create IMPLEMENTATION_PLAN.md (this file as live tracker)
- [ ] Create .env.example with all required variables
- [ ] Create config/default.yaml with model configurations
- [ ] Create README.md with quick start guide

**Status:** In Progress
**Notes:** Document created, proceeding with directory structure

---

### Part 2: Frontend Foundation - UI Skeleton (2 hours) ⏸️

**Goal:** Get the terminal-aesthetic UI rendering in browser at http://localhost:5173

#### Setup

- [ ] Initialize Vite + React + TypeScript project
- [ ] Configure tsconfig.json (strict mode)
- [ ] Install all dependencies (React 19, Router, Zustand, TanStack Query)
- [ ] Configure Vite proxy for API/WebSocket

#### Design System

- [ ] Create assets/styles/reset.css
- [ ] Create assets/styles/tokens.css (colors, typography, spacing)
- [ ] Create assets/styles/animations.css (pulse, scan, blink)

#### Terminal Component Library

- [ ] Panel component with variants (default, accent, warning, error)
- [ ] StatusIndicator with pulse animation and color coding
- [ ] Button component with terminal styling and states
- [ ] Input component with terminal styling and error handling
- [ ] MetricDisplay component for numerical data
- [ ] ProgressBar component for token usage visualization
- [ ] Divider component (horizontal/vertical)

#### Layout Components

- [ ] RootLayout with grid structure (header + sidebar + main)
- [ ] Header with navigation and connection status
- [ ] Sidebar (collapsible with animation)

#### Routing & Pages

- [ ] Set up React Router v6
- [ ] HomePage (main query interface placeholder)
- [ ] ModelsPage (model status placeholder)
- [ ] MetricsPage (metrics placeholder)
- [ ] SettingsPage (settings placeholder)
- [ ] NotFoundPage (404 handler)

**Status:** Pending
**Deliverable:** Beautiful terminal-style UI skeleton at http://localhost:5173

---

### Part 3: Docker Infrastructure (1 hour) ⏸️

- [ ] Create docker-compose.yml with Redis, backend, frontend services
- [ ] Create backend/Dockerfile (multi-stage build)
- [ ] Create frontend/Dockerfile.dev (Vite dev server)
- [ ] Create frontend/Dockerfile (Nginx production)
- [ ] Create config/redis.conf
- [ ] Test: `docker compose up -d` starts all services with health checks

**Status:** Pending
**Deliverable:** Docker stack running at http://localhost:5173 (frontend) and http://localhost:8000 (backend)

---

### Part 4: Backend Core Structure (1 hour) ⏸️

#### Project Setup

- [ ] Create backend directory structure
- [ ] Create requirements.txt with FastAPI, Pydantic, httpx, Redis, etc.
- [ ] Create pyproject.toml for Python project metadata

#### Configuration System

- [ ] Implement config.py (TOML + env loading with Pydantic)
- [ ] Create app/models/config.py (Pydantic configuration models)
- [ ] Environment variable validation on startup

#### FastAPI Application

- [ ] Create app/main.py (FastAPI app with CORS, middleware)
- [ ] Create app/core/exceptions.py (exception hierarchy)
- [ ] Create app/core/logging.py (structured JSON logging)
- [ ] Create app/core/dependencies.py (FastAPI dependency injection)

#### API Endpoints (Mock Data)

- [ ] Create app/routers/health.py with GET /health endpoint
- [ ] Create app/routers/models.py with GET /api/models/status endpoint
- [ ] Mock model status data (will connect to real models in Session 2)

**Status:** Pending
**Deliverable:** Backend API responding at http://localhost:8000 with mock data

---

### Part 5: Basic Integration (30 minutes) ⏸️

- [ ] Create frontend API client (api/client.ts)
- [ ] Create TanStack Query hook for model status (hooks/useModelStatus.ts)
- [ ] Connect HomePage to display mock model status
- [ ] Verify API proxy working through Vite
- [ ] Test WebSocket connection placeholder (not functional yet)
- [ ] Update IMPLEMENTATION_PLAN.md with final status

**Status:** Pending
**Deliverable:** Frontend displaying backend data, end-to-end connection verified

---

## Success Criteria - Session 1

### Must Have ✅ (Blocking)

- [ ] Frontend renders at localhost:5173 with terminal aesthetic
- [ ] All terminal components render correctly (Panel, Button, Input, etc.)
- [ ] Navigation between pages works smoothly
- [ ] Docker Compose starts all services (Redis, backend, frontend)
- [ ] Backend responds to health checks (GET /health returns 200)
- [ ] Backend returns mock model status (GET /api/models/status)
- [ ] Frontend displays mock model status data
- [ ] No TypeScript compilation errors
- [ ] No console errors in browser DevTools
- [ ] Design tokens (colors, typography) applied consistently

### Nice to Have 🎯 (Non-blocking)

- [ ] Sidebar collapse animation smooth (60fps)
- [ ] All pages have consistent terminal aesthetic
- [ ] Loading states implemented
- [ ] Error boundaries in place
- [ ] Mock data looks realistic

### Known Limitations (Session 1)

⚠️ **Expected for Session 2:**
- Model status shows mock data (real health checks in Session 2)
- Query submission not functional yet
- WebSocket events don't fire yet
- No CGRAG functionality yet
- No actual model communication yet

---

## Session 2: Backend Core + CGRAG (Planned)

**Estimated Time:** 4-5 hours
**Status:** 📅 Scheduled for next session

### Part 1: Model Manager & Health Checks (1.5 hours)

- [ ] Implement llama.cpp HTTP client (app/services/llama_client.py)
- [ ] Implement ModelManager with periodic health checking
- [ ] Connect to your running llama.cpp instances (localhost:8080-8083)
- [ ] Real model status in /api/models/status endpoint
- [ ] Frontend displays real model status with live updates

### Part 2: Query Routing (1.5 hours)

- [ ] Implement complexity assessment (app/services/routing.py)
- [ ] Implement query router with tier selection
- [ ] Create POST /api/query endpoint
- [ ] Test routing to actual models on host
- [ ] Frontend query submission component functional

### Part 3: CGRAG Foundation (1.5 hours)

- [ ] Implement document indexing pipeline
- [ ] Integrate FAISS vector search
- [ ] Implement sentence-transformers embeddings
- [ ] Create indexing CLI script (python -m app.cli.index_docs)
- [ ] Redis caching for embeddings
- [ ] Test retrieval with sample documents

### Part 4: Integration & Testing (30 minutes)

- [ ] End-to-end query flow working (frontend → backend → model → response)
- [ ] CGRAG context included in responses
- [ ] Frontend displays full query response with metadata
- [ ] Update IMPLEMENTATION_PLAN.md with Session 2 results

---

## Session 3: Real-time Features & Polish (Future)

- [ ] WebSocket event system (model status updates, query progress)
- [ ] Live token streaming in frontend
- [ ] Model performance metrics collection
- [ ] Processing pipeline visualization (React Flow)
- [ ] Advanced visualizations (Chart.js for metrics)
- [ ] Context window allocation display
- [ ] Query history with local storage

---

## Technical Configuration

### Your Environment

- **OS:** macOS
- **Models:** DeepSeek R1 Qwen3 8B (Q2/Q3/Q4) already running on host
  - Q2_FAST_1: localhost:8080
  - Q2_FAST_2: localhost:8081
  - Q3_SYNTH: localhost:8082
  - Q4_DEEP: localhost:8083
- **llama.cpp:** Already compiled and configured ✅

### Docker Networking (macOS)

- Backend uses `host.docker.internal:8080-8083` to reach host-based models
- Frontend proxies `/api` and `/ws` to backend
- Redis runs in container, exposed to backend only

### Port Allocation

- **Frontend (dev):** 5173
- **Backend (API):** 8000
- **Redis:** 6379 (internal only)
- **Models (host):** 8080-8083
- **Prometheus (future):** 9090
- **Grafana (future):** 3000

---

## Progress Tracking

### Session 1 Progress

**Started:** 2025-11-02
**Completed:** TBD

#### Time Breakdown

- Scaffolding: ___ minutes
- Frontend UI: ___ minutes
- Docker: ___ minutes
- Backend: ___ minutes
- Integration: ___ minutes

**Total Session 1 Time:** TBD

---

## Issues & Resolutions

### Active Issues

_None yet - will update as encountered_

### Resolved Issues

_Will document resolutions here_

---

## Notes & Decisions

### Architecture Decisions

1. **Models on Host:** Running llama.cpp on host (not Docker) for Metal GPU acceleration
2. **UI-First Approach:** Building visible UI skeleton before backend logic for faster feedback
3. **Mock Data:** Using realistic mock data in Session 1 to unblock UI development
4. **Strict TypeScript:** All frontend code uses strict mode for maximum type safety
5. **CSS Modules:** Component styling with CSS Modules (not CSS-in-JS) for performance

### Terminal Aesthetic Decisions

- **Color Palette:** Phosphor green (#00ff41) as primary, cyan (#00ffff) for processing, amber (#ff9500) for warnings
- **Typography:** JetBrains Mono as primary monospace font
- **Animations:** 60fps target, GPU-accelerated transforms
- **Density:** Information-dense displays inspired by engineering interfaces

---

## Quick Commands

### Development

```bash
# Start Docker services
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart service
docker compose restart backend

# Rebuild after dependency changes
docker compose up -d --build

# Stop all services
docker compose down
```

### Frontend

```bash
cd frontend
npm run dev          # Start dev server
npm run build        # Production build
npm run lint         # Run ESLint
npm test            # Run tests
```

### Backend

```bash
cd backend
source venv/bin/activate  # Activate virtualenv
uvicorn app.main:app --reload  # Start dev server
pytest tests/        # Run tests
```

---

## Resources

### Core Documentation
- **Specification:** [PROJECT_SPECfINAL.md](PROJECT_SPECfINAL.md)
- **Claude Instructions:** [CLAUDE.md](../../CLAUDE.md)
- **Project Status:** [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Architecture Designs:** Generated by specialized agents (see agent outputs in conversation)

### Quick References
- [Docker Quick Start Guide](../guides/DOCKER_QUICKSTART.md) - Docker setup
- [Admin Quick Reference](../guides/ADMIN_QUICK_REFERENCE.md) - Admin panel
- [Profile Quick Reference](../guides/PROFILE_QUICK_REFERENCE.md) - Profile system
- [Testing Guide](../TESTING_GUIDE.md) - Testing procedures

### Implementation Guides
- [CGRAG Implementation](../implementation/CGRAG_IMPLEMENTATION.md) - CGRAG system
- [Model Management UI Complete](../implementation/MODEL_MANAGEMENT_UI_COMPLETE.md) - Model UI
- [Admin Page Complete](../implementation/ADMIN_PAGE_COMPLETE.md) - Admin page

---

**Last Updated:** 2025-11-02
**Next Update:** After completing Session 1 Part 1 (Scaffolding)
