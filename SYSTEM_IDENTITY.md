# S.Y.N.A.P.S.E. ENGINE — SYSTEM_IDENTITY

**S.Y.N.A.P.S.E. ENGINE**  
**Scalable Yoked Network for Adaptive Praxial System Emergence**

---

> *Interlinked cognition — thought in motion.*

All runtime messages and orchestration control flow through the **NEURAL SUBSTRATE ORCHESTRATOR** — the message bus and governance layer that enforces routing, health checks, authentication, and contextual budgeting.

---

## Overview

S.Y.N.A.P.S.E. ENGINE is the canonical identity for the project previously referenced in the repository as MAGI. It is a distributed orchestration platform for local language models and related subsystems — designed to coordinate multiple quantized models, perform sub-100ms contextual retrieval, and run multi-stage refinement, consensus, and debate workflows.

This document exists to:  
- establish a consistent system identity for repo-wide naming and module responsibilities;  
- provide Docker/service naming conventions and suggested env/healthcheck contracts;  
- offer a compact, production-ready header and startup banner for logs and UI;  
- encode a subtle, layered voice for internal documentation — engineering-first, with an evocative, classificatory motif.

---

## Canonical Expansion

**S.Y.N.A.P.S.E. ENGINE**  
**Scalable Yoked Network for Adaptive Praxial System Emergence**

- *Scalable Yoked Network* — denotes the system's engineered linking of discrete model instances and services.  
- *Adaptive Praxial* — indicates the system acts (praxis) on learned patterns and adapts in production.  
- *System Emergence* — captures the emergent behavior from coordinated subsystems.

---

## High-level Architecture (single-paragraph)

S.Y.N.A.P.S.E. ENGINE composes a WebUI control plane, a FastAPI orchestrator, a lightweight host API for native acceleration (Metal), a FAISS-backed retrieval engine (CGRAG), and a small persistent cache layer — all coordinated by the NEURAL SUBSTRATE ORCHESTRATOR. The design prioritizes dynamic model lifecycle management, token-budgeted retrieval, and multi-stage processing patterns (FAST → BALANCED → POWERFUL) while exposing real-time telemetry for monitoring and debugging.

---

## Repository and Docker Service Naming

We recommend migrating service names and references in `docker-compose.yml`, CI, and documentation to the canonical `synapse_*` namespace. Maintain legacy aliases for compatibility during rollout (see Migration Notes below).

| Current / Legacy | Canonical Service | Codename | Responsibility | Default Port | Health-check endpoint |
|------------------|-------------------|---------:|---------------|-------------:|----------------------:|
| `magi` | `synapse_core` | `CORE:PRAXIS` | Orchestrator — FastAPI router, NEURAL SUBSTRATE ORCHESTRATOR inbound/outbound control. | `8000` | `GET /healthz` |
| `magi_frontend` | `synapse_frontend` | `CORE:INTERFACE` | React terminal UI, WebSocket events, visualization & input. | `5173` | `GET /_ping` |
| `magi_host_api` | `synapse_host_api` | `NODE:NEURAL` | Host-level model process manager — Metal control, start/stop, process supervision. | `8700` | `GET /host/health` |
| `magi_searxng` | `synapse_recall` | `NODE:RECALL` | CGRAG preprocessor, SearXNG proxy + FAISS indexing pipeline (semantic recall). | `8080` | `GET /recall/health` |
| `magi_redis` | `synapse_redis` | `CORE:MEMEX` | Redis caching and session store — token budgets, context cache, short-term memory. | `6379` | Redis `PING` |

**Note:** service names (`synapse_core` etc.) are deliberately short and explicit — they map 1:1 to runtime container names and to internal logging tags (examples below).

---

## Subsystem Responsibilities & Logging Tags

- `CORE:PRAXIS` (synapse_core)
  - Responsibilities: query routing, complexity assessment, council orchestration, policy enforcement.  
  - Log tag: `prx:`  
  - Metrics prefix: `prx_`  
  - Primary environment variables: `PRAXIS_PORT`, `PRAXIS_MODEL_PATH`, `NEURAL_ORCH_URL`

- `CORE:MEMEX` (synapse_redis)
  - Responsibilities: short-term context cache, session persistence, cache heatmap for CGRAG.  
  - Log tag: `mem:`  
  - Primary env: `MEMEX_HOST`, `MEMEX_PORT`, `MEMEX_TTL`

- `NODE:RECALL` (synapse_recall)
  - Responsibilities: web-search proxying, embedding refresh, FAISS indexing and query.  
  - Log tag: `rec:`  
  - Env: `RECALL_INDEX_PATH`, `EMBEDDING_MODEL`, `RECALL_MAX_SHARDS`

- `NODE:NEURAL` (synapse_host_api)
  - Responsibilities: native process control (llama-server or similar), GPU/Metal orchestration, process health and restart policy.  
  - Log tag: `nrl:`  
  - Env: `HOST_API_BIN`, `HOST_API_GPU_ENABLED`, `HOST_API_MAX_PROCS`

- `CORE:INTERFACE` (synapse_frontend)
  - Responsibilities: terminal UI, keyboard navigation, real-time model status, local user preferences.  
  - Log tag: `ifc:`  
  - Env: `IFACE_PORT`, `IFACE_WS_URL`

---

## Healthcheck & Contract Guidelines

All services should implement a minimal health contract to enable the NEURAL SUBSTRATE ORCHESTRATOR to make routing decisions and graceful degradation:

- **HTTP health endpoint** returning `200` and a JSON body `{ "status": "ok", "uptime": <s>, "components": { ... } }` when applicable.  
- **Liveness**: a fast, lightweight endpoint (e.g. `/healthz`) that must respond under 50ms.  
- **Readiness**: `/ready` which reports dependencies (Redis connected, FAISS index loaded, models started).  
- **Tracing**: propagate `X-TRACE-ID` headers across internal calls.

Example health response (FastAPI):

```json
{
  "status": "ok",
  "uptime": 11234,
  "components": {
    "redis": "connected",
    "faiss": "loaded",
    "host_api": "idle"
  }
}
```

---

## Telemetry, Log Levels and Tagging

- Log levels: `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL`.  
- Correlation: every request must carry `trace_id` and `session_id`.  
- Tagging convention: `<codename_short>:` prefix (see table above) — adopt this in structured logs and metric names.  
- Prometheus metric prefixes: `prx_`, `mem_`, `rec_`, `nrl_`, `ifc_`.

---

## Startup Banner (for terminal / primary UI)

```
─────────────────────────────────────────────
   S.Y.N.A.P.S.E. ENGINE [v5.0]
   Scalable Yoked Network for Adaptive Praxial System Emergence
─────────────────────────────────────────────
   [CORE:PRAXIS]   prx: Orchestrator online
   [CORE:MEMEX]    mem: Cache synchronized
   [NODE:RECALL]   rec: Recall engine initialized
   [NODE:NEURAL]   nrl: Host API active
   [CORE:INTERFACE] ifc: WebUI connected
─────────────────────────────────────────────
   STATUS: NEURAL SUBSTRATE ORCHESTRATOR | SYNCHRONIZATION: 100%
─────────────────────────────────────────────
```

— subtle system messages may appear below the banner — keep them concise and timestamped.

---

## Migration Notes — quick checklist

1. update `docker-compose.yml` service names to `synapse_*` (retain legacy aliases).  
2. update logging prefixes and telemetry tags.  
3. add `/healthz` and `/ready` endpoints to any service missing them.  
4. wire `NEURAL_ORCH_URL` into each service's env for message-bus connectivity.  
5. migrate README top-of-repo to reference `S.Y.N.A.P.S.E. ENGINE` and add this file under `/docs`.

Suggested git commit message for the migration:

```
chore(system): rebrand MAGI -> S.Y.N.A.P.S.E. ENGINE; add canonical service names and health contracts
```

---

## Naming & Thematic Guidance (for docs and UI copy)

Keep outward-facing language concise and technical — reserve evocative lines for the terminal header, status banners, and short taglines. Use em-dashes sparingly for tonal effect:

- Example README header: *S.Y.N.A.P.S.E. ENGINE — Scalable Yoked Network for Adaptive Praxial System Emergence.*  
- Subheader (one-liner): *Interlinked cognition — thought in motion.*  
- In technical docs (API, architecture) lean on pragmatic names and descriptors — use the codename mappings above.  

---

## Lore Layer (internal, optional)

The system’s internal language can retain a restrained, classificatory voice — little flourishes that hint at origin and intent without breaking technical readability. Use these sparingly in status messages and startup banners:

- *"Mindlink stabilized — latency within acceptable bounds."*  
- *"Recall shard 3 — alignment drift: 0.7% — initiating reprobe."*  
- *"Praxis queue overflow — invoking contingency sequence."*

These lines are intended to be atmospheric—short, surgical, and easily scannable in logs.

---

## Example `docker-compose` snippet (recommended)

```yaml
version: '3.8'
services:
  synapse_core:
    image: synapse/core:latest
    container_name: synapse_core
    ports: ['8000:8000']
    environment:
      - PRAXIS_PORT=8000
      - NEURAL_ORCH_URL=http://synapse_core:8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 10s
      timeout: 5s
      retries: 3
    depends_on:
      - synapse_redis
      - synapse_recall

  synapse_redis:
    image: redis:7
    container_name: synapse_redis
    ports: ['6379:6379']

  synapse_recall:
    image: synapse/recall:latest
    container_name: synapse_recall
    ports: ['8080:8080']

  synapse_host_api:
    image: synapse/host-api:latest
    container_name: synapse_host_api
    ports: ['8700:8700']

  synapse_frontend:
    image: synapse/frontend:latest
    container_name: synapse_frontend
    ports: ['5173:5173']
```

---

## Quick README snippet (top of repo)

> **S.Y.N.A.P.S.E. ENGINE** — Scalable Yoked Network for Adaptive Praxial System Emergence.  
> Interlinked cognition — thought in motion.  
> All runtime messages traverse the NEURAL SUBSTRATE ORCHESTRATOR.

---

## Where to put this file

Place this file at `/docs/SYSTEM_IDENTITY.md` and add a reference to it in the repo README. Keep the document small and canonical — use it as the single source for naming, log-tagging, and health contracts.

---

If you want, I can also:
- generate a ready-to-drop `/docs/SYSTEM_NOMENCLATURE.md` with the full mapping (aliases, history), or
- produce per-service `Dockerfile` header comments and `README` stubs that contain the new log tag and env var conventions.

— ready for the next step.

