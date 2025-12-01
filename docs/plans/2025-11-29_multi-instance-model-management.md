# Multi-Instance Model Management Implementation Plan

**Date:** 2025-11-29
**Status:** Implementation Plan
**Estimated Time:** 16-24 hours (across 3 phases)
**Feature:** Multi-Instance Model Management with System Prompts and Web Search

---

**Related Documentation:**
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Recent development context
- [CLAUDE.md](../../CLAUDE.md) - Project guidelines and architecture
- [MODEL_REGISTRY.md](../features/MODEL_REGISTRY.md) - Model registry design (if exists)
- [llama_server_manager.py](../../backend/app/services/llama_server_manager.py) - Current server management
- [discovered_model.py](../../backend/app/models/discovered_model.py) - Current model schema
- [models.py router](../../backend/app/routers/models.py) - Current model API endpoints
- [ModelManagementPage.tsx](../../frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx) - Current UI

---

## Executive Summary

### Vision Statement

Transform the S.Y.N.A.P.S.E. ENGINE Model Management page from a simple enable/disable interface to a powerful multi-instance orchestration system where users can:

1. **Spawn N instances** of the same base model (e.g., 2x Q2_FAST for parallel processing)
2. **Configure system prompts** per instance to create specialized agents/personas
3. **Toggle web search** per instance to enable internet-enhanced responses via SearXNG

### Current State vs. New Behavior

| Aspect | Current | New |
|--------|---------|-----|
| **Instance count** | 1 per model | 1-N per model |
| **Identity** | model_id only | instance_id (model_id + instance number) |
| **System prompt** | None (hardcoded) | Per-instance configurable |
| **Web search** | Global setting | Per-instance toggle |
| **Port assignment** | 1 port per model | 1 port per instance |
| **UI representation** | 1 card per model | 1 card per instance (grouped by model) |

### Expected Outcomes

- Users can load balance simple queries across multiple FAST instances
- Users can create specialized agents (e.g., "Code Assistant", "Research Assistant") from the same model
- Users can enable web search only for instances that need it (saves resources)
- Query routing can intelligently select instances based on capabilities

---

## Agent Consultations

### @record-keeper
**File:** [record-keeper.md](../../.claude/agents/record-keeper.md)
**Query:** "What historical context exists for model instances, system prompts, or web search integration?"
**Key Insights:**
- SESSION_NOTES.md shows Code Chat mode was recently completed with 18+ tools
- LlamaServerManager already supports external Metal servers via host API
- SearXNG integration exists in [websearch.py](../../backend/app/services/websearch.py)
- Query routing logic in [routing.py](../../backend/app/services/routing.py) maps to tiers, not specific instances

### @backend-architect
**File:** [backend-architect.md](../../.claude/agents/backend-architect.md)
**Query:** "How should we architect multi-instance spawning while maintaining the current LlamaServerManager patterns?"
**Key Insights:**
- LlamaServerManager.servers dict currently keys by model_id - needs instance_id
- ServerProcess wrapper already tracks port, model, readiness - extend for instance metadata
- Health checks need to work per-instance, not per-model
- Query routing needs instance-aware selection, not just tier-based

**Recommendations:**
1. Create new `ModelInstance` Pydantic model that wraps `DiscoveredModel` + instance config
2. Update servers dict key from `model_id` to `instance_id`
3. Add `InstanceRegistry` service to manage instance configurations
4. Modify query router to accept instance capabilities filter

### @model-lifecycle-manager
**File:** [model-lifecycle-manager.md](../../.claude/agents/model-lifecycle-manager.md)
**Query:** "What lifecycle considerations exist for multiple instances of the same model?"
**Key Insights:**
- VRAM management becomes critical with multiple instances
- Wave-based startup strategy should consider instance priority
- Port conflicts must be prevented with proper allocation algorithm
- Cleanup must handle partial failures (some instances up, some down)

**Recommendations:**
1. Add VRAM estimation per model (rough: size_params * quantization_factor)
2. Implement instance priority for startup order
3. Port allocation should reserve ranges per base model
4. Graceful degradation: if 2/3 instances fail, keep the 1 running

### @frontend-engineer
**File:** [frontend-engineer.md](../../.claude/agents/frontend-engineer.md)
**Query:** "How should we design the UI for multi-instance configuration with our terminal aesthetic?"
**Key Insights:**
- ModelCardGrid currently displays one card per model
- Need instance counter + spawn button on each model card
- System prompt config needs modal or collapsible panel
- Web search toggle is simple boolean

**Recommendations:**
1. Add "INSTANCES" count badge on model cards
2. "+" button to spawn new instance, "-" to remove
3. Click on instance row to expand config (system prompt, web search)
4. Group instances by base model with collapsible sections
5. Terminal-style instance naming: `model_id:01`, `model_id:02`

### @security-specialist
**File:** [security-specialist.md](../../.claude/agents/security-specialist.md)
**Query:** "What security considerations exist for user-configured system prompts?"
**Key Insights:**
- System prompts are injected into LLM context - potential prompt injection risk
- Need to sanitize/validate system prompts before storage
- Character limits prevent resource exhaustion
- Log all system prompt changes for audit

**Recommendations:**
1. Max system prompt length: 4096 characters
2. Strip control characters and null bytes
3. No execution of system prompts - treat as plain text
4. Audit log: instance_id, old_prompt, new_prompt, timestamp, user (when auth exists)
5. Consider read-only "default" prompts that can't be modified

---

## Architecture Overview

### Data Flow

```
+------------------+     +-----------------+     +------------------+
|   Frontend UI    |     |   Backend API   |     |  llama-server    |
|                  |     |                 |     |   Instances      |
|  InstanceEditor  |---->|  /instances/*   |---->|  :8080 (model:01)|
|  PresetCreator   |     |  POST/PUT/DEL   |     |  :8081 (model:02)|
|                  |     |                 |     |  :8082 (model:03)|
+------------------+     +-----------------+     +------------------+
                                |
                                v
                         +-------------+
                         |   Instance  |
                         |   Registry  |
                         |   (JSON)    |
                         +-------------+
```

### Component Interactions

1. **User creates instance** -> Frontend calls POST /api/instances
2. **Backend validates** -> Creates InstanceConfig, assigns port
3. **Backend persists** -> Writes to instance_registry.json
4. **User starts instance** -> POST /api/instances/{id}/start
5. **LlamaServerManager** -> Spawns llama-server with port
6. **Query arrives** -> Router selects instance based on tier + capabilities
7. **Request to instance** -> System prompt prepended, web search if enabled

---

## Data Model Design

### New Pydantic Models

**File:** `backend/app/models/instance.py` (NEW)

```python
"""Model instance configuration and registry.

Extends DiscoveredModel with instance-specific configuration including
system prompts, web search capability, and unique instance identity.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class InstanceStatus(str, Enum):
    """Runtime status of a model instance."""
    STOPPED = "stopped"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    ERROR = "error"


class InstanceConfig(BaseModel):
    """Configuration for a single model instance.

    Represents a running or configured instance of a base model,
    with instance-specific settings like system prompt and web search.
    """

    # Identity
    instance_id: str = Field(
        description="Unique instance identifier (model_id:NN)",
        alias="instanceId",
        pattern=r"^[a-z0-9_]+:\d{2}$"
    )
    model_id: str = Field(
        description="Reference to base DiscoveredModel",
        alias="modelId"
    )
    instance_number: int = Field(
        ge=1, le=99,
        description="Instance number (01-99)",
        alias="instanceNumber"
    )

    # User-configurable settings
    display_name: str = Field(
        max_length=64,
        description="User-friendly name for this instance",
        alias="displayName"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        max_length=4096,
        description="System prompt injected at query time",
        alias="systemPrompt"
    )
    web_search_enabled: bool = Field(
        default=False,
        description="Enable SearXNG web search for this instance",
        alias="webSearchEnabled"
    )

    # Runtime configuration
    port: int = Field(
        ge=1024, le=65535,
        description="Assigned port for this instance"
    )

    # Status tracking (not persisted, computed at runtime)
    status: InstanceStatus = Field(
        default=InstanceStatus.STOPPED,
        description="Current runtime status"
    )

    # Metadata
    created_at: str = Field(
        description="ISO timestamp of instance creation",
        alias="createdAt"
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last update",
        alias="updatedAt"
    )

    @field_validator('system_prompt')
    @classmethod
    def sanitize_system_prompt(cls, v: Optional[str]) -> Optional[str]:
        """Remove control characters and null bytes from system prompt."""
        if v is None:
            return None
        # Remove null bytes
        v = v.replace('\x00', '')
        # Remove control characters except newlines/tabs
        v = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', v)
        return v.strip()

    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """Ensure display name is safe and non-empty."""
        v = v.strip()
        if not v:
            raise ValueError("Display name cannot be empty")
        # Remove any HTML-like tags for safety
        v = re.sub(r'<[^>]+>', '', v)
        return v

    def get_full_name(self) -> str:
        """Get formatted instance name for display."""
        return f"{self.display_name} [{self.instance_id}]"

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True
    )


class InstanceRegistry(BaseModel):
    """Registry of all configured model instances.

    Persisted to JSON and loaded at startup. Tracks all instances
    across all models with their configurations.
    """

    instances: Dict[str, InstanceConfig] = Field(
        default_factory=dict,
        description="Map of instance_id to InstanceConfig"
    )

    # Port management
    port_range: tuple[int, int] = Field(
        default=(8100, 8199),
        description="Port range reserved for instances",
        alias="portRange"
    )

    # Metadata
    last_updated: str = Field(
        description="ISO timestamp of last registry update",
        alias="lastUpdated"
    )

    def get_instances_for_model(self, model_id: str) -> List[InstanceConfig]:
        """Get all instances of a specific base model."""
        return [
            inst for inst in self.instances.values()
            if inst.model_id == model_id
        ]

    def get_next_instance_number(self, model_id: str) -> int:
        """Get the next available instance number for a model."""
        existing = self.get_instances_for_model(model_id)
        if not existing:
            return 1
        max_num = max(inst.instance_number for inst in existing)
        return min(max_num + 1, 99)

    def get_available_port(self) -> Optional[int]:
        """Get next available port in the instance range."""
        used_ports = {inst.port for inst in self.instances.values()}
        for port in range(self.port_range[0], self.port_range[1] + 1):
            if port not in used_ports:
                return port
        return None

    def add_instance(self, instance: InstanceConfig) -> None:
        """Add or update an instance in the registry."""
        self.instances[instance.instance_id] = instance
        self.last_updated = datetime.utcnow().isoformat() + "Z"

    def remove_instance(self, instance_id: str) -> bool:
        """Remove an instance from the registry."""
        if instance_id in self.instances:
            del self.instances[instance_id]
            self.last_updated = datetime.utcnow().isoformat() + "Z"
            return True
        return False

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True
    )


class CreateInstanceRequest(BaseModel):
    """Request to create a new model instance."""

    model_id: str = Field(alias="modelId")
    display_name: str = Field(max_length=64, alias="displayName")
    system_prompt: Optional[str] = Field(
        default=None, max_length=4096, alias="systemPrompt"
    )
    web_search_enabled: bool = Field(default=False, alias="webSearchEnabled")

    model_config = ConfigDict(populate_by_name=True)


class UpdateInstanceRequest(BaseModel):
    """Request to update an existing instance."""

    display_name: Optional[str] = Field(
        default=None, max_length=64, alias="displayName"
    )
    system_prompt: Optional[str] = Field(
        default=None, max_length=4096, alias="systemPrompt"
    )
    web_search_enabled: Optional[bool] = Field(
        default=None, alias="webSearchEnabled"
    )

    model_config = ConfigDict(populate_by_name=True)
```

### Updated LlamaServerManager

The `LlamaServerManager` needs minimal changes:

1. Change `servers` dict key from `model_id` to `instance_id`
2. Accept `InstanceConfig` instead of `DiscoveredModel` for start operations
3. Prepend system prompt when routing queries

### Registry File Structure

**File:** `backend/data/instance_registry.json` (NEW)

```json
{
  "instances": {
    "qwen3_4p0b_q4km_fast:01": {
      "instanceId": "qwen3_4p0b_q4km_fast:01",
      "modelId": "qwen3_4p0b_q4km_fast",
      "instanceNumber": 1,
      "displayName": "Fast Query Handler",
      "systemPrompt": "You are a fast, concise assistant. Keep responses brief.",
      "webSearchEnabled": false,
      "port": 8100,
      "createdAt": "2025-11-29T12:00:00Z",
      "updatedAt": null
    },
    "qwen3_4p0b_q4km_fast:02": {
      "instanceId": "qwen3_4p0b_q4km_fast:02",
      "modelId": "qwen3_4p0b_q4km_fast",
      "instanceNumber": 2,
      "displayName": "Research Assistant",
      "systemPrompt": "You are a research assistant with access to web search. Provide detailed, well-sourced answers.",
      "webSearchEnabled": true,
      "port": 8101,
      "createdAt": "2025-11-29T12:30:00Z",
      "updatedAt": null
    }
  },
  "portRange": [8100, 8199],
  "lastUpdated": "2025-11-29T12:30:00Z"
}
```

---

## Implementation Plan

### Phase 1: Multi-Instance Foundation (6-8 hours)

**Objective:** Enable spawning and managing multiple instances of the same model.

#### Task 1.1: Create Instance Data Models
**File:** `backend/app/models/instance.py` (NEW - ~200 lines)
**Acceptance Criteria:**
- [x] InstanceStatus enum with all states
- [x] InstanceConfig with full validation
- [x] InstanceRegistry with port/instance management
- [x] CreateInstanceRequest and UpdateInstanceRequest
- [x] System prompt sanitization via validator

#### Task 1.2: Create Instance Manager Service
**File:** `backend/app/services/instance_manager.py` (NEW - ~300 lines)
**Code Pattern:**
```python
class InstanceManager:
    """Manages model instance configurations and lifecycle."""

    def __init__(self, registry_path: Path, server_manager: LlamaServerManager):
        self.registry_path = registry_path
        self.server_manager = server_manager
        self.registry: InstanceRegistry = self._load_registry()

    async def create_instance(
        self,
        request: CreateInstanceRequest,
        model: DiscoveredModel
    ) -> InstanceConfig:
        """Create a new instance of a base model."""
        # Generate instance_id
        instance_num = self.registry.get_next_instance_number(request.model_id)
        instance_id = f"{request.model_id}:{instance_num:02d}"

        # Allocate port
        port = self.registry.get_available_port()
        if port is None:
            raise SynapseException("No available ports for new instance")

        # Create config
        config = InstanceConfig(
            instance_id=instance_id,
            model_id=request.model_id,
            instance_number=instance_num,
            display_name=request.display_name,
            system_prompt=request.system_prompt,
            web_search_enabled=request.web_search_enabled,
            port=port,
            created_at=datetime.utcnow().isoformat() + "Z"
        )

        # Persist
        self.registry.add_instance(config)
        self._save_registry()

        return config

    async def start_instance(self, instance_id: str) -> None:
        """Start a specific instance's llama-server."""
        config = self.registry.instances.get(instance_id)
        if not config:
            raise SynapseException(f"Instance not found: {instance_id}")

        # Get base model from model registry
        model = self._get_base_model(config.model_id)

        # Create augmented model with instance port
        augmented = self._create_augmented_model(model, config)

        # Start server
        await self.server_manager.start_server(augmented)

        # Update status
        config.status = InstanceStatus.ACTIVE
```

**Acceptance Criteria:**
- [ ] create_instance() with port allocation
- [ ] update_instance() with validation
- [ ] delete_instance() with cleanup
- [ ] start_instance() delegating to LlamaServerManager
- [ ] stop_instance() with graceful shutdown
- [ ] get_instance_status() with health check
- [ ] Registry persistence to JSON

#### Task 1.3: Create Instance API Router
**File:** `backend/app/routers/instances.py` (NEW - ~200 lines)
**Endpoints:**
```
GET    /api/instances              - List all instances
GET    /api/instances/{id}         - Get instance details
POST   /api/instances              - Create new instance
PUT    /api/instances/{id}         - Update instance config
DELETE /api/instances/{id}         - Delete instance
POST   /api/instances/{id}/start   - Start instance server
POST   /api/instances/{id}/stop    - Stop instance server
GET    /api/instances/{id}/health  - Instance health check
```

**Acceptance Criteria:**
- [ ] All CRUD endpoints functional
- [ ] Start/stop with proper error handling
- [ ] Health endpoint returns live status
- [ ] Pydantic validation on all inputs
- [ ] Proper HTTP status codes

#### Task 1.4: Update LlamaServerManager
**File:** `backend/app/services/llama_server_manager.py` (MODIFY - ~50 lines)
**Changes:**
- Update `servers` dict key to use `instance_id` instead of `model_id`
- Add method `start_server_for_instance(config: InstanceConfig, model: DiscoveredModel)`
- Update `get_status_summary()` to return instance-level data

**Acceptance Criteria:**
- [ ] servers dict keyed by instance_id
- [ ] start_server accepts InstanceConfig
- [ ] stop_server works with instance_id
- [ ] Status summary includes instance metadata

#### Task 1.5: Frontend - Instance List Component
**File:** `frontend/src/components/instances/InstanceList.tsx` (NEW - ~150 lines)
**Features:**
- List all instances grouped by base model
- Show status indicator per instance
- Start/Stop buttons per instance
- Instance count badge per model

**Acceptance Criteria:**
- [ ] Grouped display by base model
- [ ] Terminal aesthetic styling
- [ ] Real-time status updates via polling
- [ ] Start/Stop functionality

#### Task 1.6: Frontend - Create Instance Modal
**File:** `frontend/src/components/instances/CreateInstanceModal.tsx` (NEW - ~200 lines)
**Features:**
- Model selector dropdown
- Display name input
- Submit creates instance via API

**Acceptance Criteria:**
- [ ] Form validation
- [ ] Loading state during creation
- [ ] Error display on failure
- [ ] Success closes modal and refreshes list

---

### Phase 2: System Prompt Configuration (4-6 hours)

**Objective:** Allow per-instance system prompts that are injected at query time.

#### Task 2.1: System Prompt Storage (Already in Phase 1)
The `InstanceConfig` model already includes `system_prompt` field with:
- 4096 character limit
- Control character sanitization
- Null handling

#### Task 2.2: System Prompt Injection in Query Pipeline
**File:** `backend/app/routers/query.py` (MODIFY - ~30 lines)
**Changes:**
```python
async def process_query(query: QueryRequest) -> QueryResponse:
    # ... existing complexity assessment and routing ...

    # Get selected instance (new logic)
    instance = await select_instance_for_query(complexity, query.mode)

    # Prepend system prompt if configured
    if instance and instance.system_prompt:
        full_prompt = f"<|system|>{instance.system_prompt}<|end|>\n\n{query.query}"
    else:
        full_prompt = query.query

    # Send to model
    response = await model_client.complete(
        prompt=full_prompt,
        port=instance.port
    )
```

**Acceptance Criteria:**
- [ ] System prompt prepended to query
- [ ] Proper chat template format
- [ ] No prompt injection if null/empty
- [ ] Works with existing query modes

#### Task 2.3: Frontend - System Prompt Editor
**File:** `frontend/src/components/instances/SystemPromptEditor.tsx` (NEW - ~150 lines)
**Features:**
- Multiline textarea with character count
- Preview of formatted prompt
- Save/Cancel buttons
- Character limit enforcement

**Acceptance Criteria:**
- [ ] 4096 character limit with visual feedback
- [ ] Terminal-style monospace textarea
- [ ] Save triggers API update
- [ ] Unsaved changes warning

#### Task 2.4: Preset System Prompts
**File:** `backend/data/system_prompt_presets.json` (NEW)
**File:** `backend/app/routers/instances.py` (MODIFY - add GET /api/instances/presets)
**Presets:**
```json
{
  "presets": [
    {
      "id": "concise",
      "name": "Concise Assistant",
      "prompt": "You are a concise assistant. Keep responses brief and to the point.",
      "description": "For quick, short answers"
    },
    {
      "id": "researcher",
      "name": "Research Assistant",
      "prompt": "You are a thorough research assistant. Provide detailed, well-sourced answers with citations when possible.",
      "description": "For in-depth research queries"
    },
    {
      "id": "coder",
      "name": "Code Assistant",
      "prompt": "You are an expert programmer. Write clean, well-documented code. Explain your reasoning.",
      "description": "For coding tasks"
    }
  ]
}
```

**Acceptance Criteria:**
- [ ] Preset endpoint returns available presets
- [ ] Frontend shows preset selector
- [ ] Selecting preset populates system prompt field
- [ ] Custom prompts still allowed

---

### Phase 3: Web Search Integration (4-6 hours)

**Objective:** Enable per-instance web search via SearXNG toggle.

#### Task 3.1: Web Search Service Integration
**File:** `backend/app/services/websearch.py` (EXISTS - ~280 lines)
The SearXNG client already exists. We need to integrate it with instances.

**File:** `backend/app/services/instance_manager.py` (MODIFY - ~50 lines)
**Add:**
```python
async def execute_query_with_search(
    self,
    instance: InstanceConfig,
    query: str
) -> str:
    """Execute query with optional web search augmentation."""
    context = ""

    if instance.web_search_enabled:
        # Perform web search
        search_client = get_searxng_client()
        results = await search_client.search(query)

        # Format results as context
        if results.results:
            context = "## Web Search Results\n\n"
            for r in results.results[:3]:
                context += f"**{r.title}**\n{r.content}\nSource: {r.url}\n\n"

    # Combine system prompt + search context + query
    full_prompt = self._build_full_prompt(instance, context, query)
    return full_prompt
```

**Acceptance Criteria:**
- [ ] web_search_enabled flag checked before search
- [ ] SearXNG called only when enabled
- [ ] Results formatted as context
- [ ] Graceful handling if SearXNG unavailable

#### Task 3.2: Query Router Instance Selection
**File:** `backend/app/services/routing.py` (MODIFY - ~80 lines)
**Changes:**
```python
async def select_instance(
    tier: str,
    require_web_search: bool = False
) -> Optional[InstanceConfig]:
    """Select an appropriate instance for the query.

    Args:
        tier: Required model tier (fast, balanced, powerful)
        require_web_search: If True, only select instances with web search

    Returns:
        Best available InstanceConfig or None
    """
    instances = instance_manager.get_active_instances()

    # Filter by tier
    candidates = [
        i for i in instances
        if get_model_tier(i.model_id) == tier
    ]

    # Filter by web search if required
    if require_web_search:
        candidates = [i for i in candidates if i.web_search_enabled]

    if not candidates:
        return None

    # Simple round-robin or least-loaded selection
    return select_least_loaded(candidates)
```

**Acceptance Criteria:**
- [ ] Instances filtered by tier
- [ ] Web search filter when required
- [ ] Fallback to non-search instance if none available
- [ ] Load balancing across multiple instances

#### Task 3.3: Frontend - Web Search Toggle
**File:** `frontend/src/components/instances/InstanceConfig.tsx` (NEW or extend - ~100 lines)
**Features:**
- Toggle switch with clear labeling
- Status indicator (enabled/disabled)
- Save triggers API update

**Acceptance Criteria:**
- [ ] Toggle updates instance config
- [ ] Visual feedback on toggle state
- [ ] Persists across page refresh

#### Task 3.4: Query Mode Integration
**File:** `frontend/src/components/query/QueryInput.tsx` (MODIFY - ~30 lines)
**Optional Feature:**
- Add "Require Web Search" checkbox to query input
- This hint is passed to backend for instance selection

**Acceptance Criteria:**
- [ ] Optional checkbox for web search requirement
- [ ] Passed to query API
- [ ] Used in instance selection

---

## Risks and Mitigation

### Risk 1: VRAM Exhaustion with Multiple Instances
**Severity:** High
**Likelihood:** Medium
**Mitigation:**
- Add VRAM estimation before creating instance
- Warn user if estimated total exceeds system VRAM
- Implement max instances per model limit (default: 5)

### Risk 2: Port Conflicts
**Severity:** Medium
**Likelihood:** Low
**Mitigation:**
- Reserve dedicated port range (8100-8199) for instances
- Check port availability before assignment
- Release port on instance deletion

### Risk 3: System Prompt Injection Attacks
**Severity:** Medium
**Likelihood:** Low
**Mitigation:**
- Sanitize all control characters
- Character limit prevents excessive prompts
- Treat prompts as plain text, never execute
- Audit logging of all prompt changes

### Risk 4: SearXNG Unavailability
**Severity:** Low
**Likelihood:** Medium
**Mitigation:**
- Graceful fallback: query proceeds without search results
- Log warning when SearXNG unreachable
- Health check in UI shows SearXNG status

---

## Testing Checklist

### Phase 1: Multi-Instance Foundation
- [ ] Create instance with valid data
- [ ] Create instance fails with invalid model_id
- [ ] Create instance fails when port range exhausted
- [ ] Update instance display name
- [ ] Delete instance cleans up port allocation
- [ ] Start instance spawns llama-server
- [ ] Stop instance terminates process gracefully
- [ ] Multiple instances of same model run simultaneously
- [ ] Instances persist across backend restart

### Phase 2: System Prompts
- [ ] System prompt saved to instance config
- [ ] System prompt injected in query flow
- [ ] Empty system prompt not prepended
- [ ] Long prompts (4096 chars) handled correctly
- [ ] Control characters stripped from prompts
- [ ] Preset prompts load correctly
- [ ] Custom prompts override presets

### Phase 3: Web Search
- [ ] Web search enabled flag toggles correctly
- [ ] Enabled instance triggers SearXNG query
- [ ] Disabled instance skips search
- [ ] Search results formatted in context
- [ ] SearXNG failure doesn't crash query
- [ ] Instance selection respects web search filter

---

## Files Modified Summary

### Create (NEW):
- `backend/app/models/instance.py` (~200 lines)
- `backend/app/services/instance_manager.py` (~300 lines)
- `backend/app/routers/instances.py` (~200 lines)
- `backend/data/instance_registry.json` (initial empty)
- `backend/data/system_prompt_presets.json` (~50 lines)
- `backend/tests/test_instance_manager.py` (~300 lines)
- `frontend/src/components/instances/InstanceList.tsx` (~150 lines)
- `frontend/src/components/instances/CreateInstanceModal.tsx` (~200 lines)
- `frontend/src/components/instances/SystemPromptEditor.tsx` (~150 lines)
- `frontend/src/components/instances/InstanceConfig.tsx` (~100 lines)
- `frontend/src/hooks/useInstances.ts` (~100 lines)
- `frontend/src/types/instance.ts` (~50 lines)

### Update (MODIFY):
- `backend/app/services/llama_server_manager.py` (~50 lines changed)
- `backend/app/routers/query.py` (~30 lines changed)
- `backend/app/services/routing.py` (~80 lines changed)
- `backend/app/main.py` (~10 lines - router registration)
- `frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx` (~100 lines changed)
- `frontend/src/router/routes.tsx` (~5 lines - optional new route)

### Total Estimated Lines:
- **New Code:** ~1,800 lines
- **Modified Code:** ~275 lines

---

## Estimated Effort

| Phase | Tasks | Hours | Confidence |
|-------|-------|-------|------------|
| Phase 1: Multi-Instance Foundation | 6 tasks | 6-8 hrs | High |
| Phase 2: System Prompts | 4 tasks | 4-6 hrs | High |
| Phase 3: Web Search Integration | 4 tasks | 4-6 hrs | Medium |
| Testing & Integration | All phases | 2-4 hrs | Medium |
| **Total** | **14 tasks** | **16-24 hrs** | **Medium-High** |

---

## Next Actions

### Immediate (This Session)
1. Create `backend/app/models/instance.py` with Pydantic models
2. Create `backend/app/services/instance_manager.py` basic structure
3. Create `backend/app/routers/instances.py` with CRUD endpoints

### Follow-up (Next Session)
1. Update `LlamaServerManager` for instance-based keys
2. Create frontend components for instance management
3. Integrate system prompt injection in query flow

### Future Enhancements (Backlog)
1. Instance cloning (copy existing config)
2. Instance templates (predefined configs)
3. Instance groups (start/stop multiple at once)
4. Instance metrics (request count, latency per instance)
5. VRAM usage display per instance
6. Load balancing visualization

---

## Definition of Done

- [ ] All Phase 1 acceptance criteria met
- [ ] All Phase 2 acceptance criteria met
- [ ] All Phase 3 acceptance criteria met
- [ ] All backend tests passing
- [ ] All frontend tests passing
- [ ] Documentation updated in SESSION_NOTES.md
- [ ] No TypeScript errors (strict mode)
- [ ] No Python type errors (mypy)
- [ ] Manual testing in Docker environment
- [ ] Code review completed
