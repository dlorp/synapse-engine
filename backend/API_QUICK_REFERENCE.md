# S.Y.N.A.P.S.E. ENGINE Model Management API - Quick Reference

**Base URL:** `http://localhost:8000`

---

## Model Registry

### Get Full Registry
```bash
GET /api/models/registry
```
**Response:** ModelRegistry with all models, scan info, and tier thresholds

---

### Rescan Models
```bash
POST /api/models/rescan
```
**Description:** Re-scan HUB folder, preserving user overrides
**Response:** Scan results with counts of models found/added/removed

---

### Get Models by Tier
```bash
GET /api/models/tiers/{tier}
```
**Parameters:** `tier` = `fast` | `balanced` | `powerful`
**Response:** Array of DiscoveredModel objects

---

## Model Configuration

### Update Model Tier
```bash
PUT /api/models/{model_id}/tier
Content-Type: application/json

{
  "tier": "powerful"
}
```
**Response:** Confirmation with updated tier

---

### Update Thinking Capability
```bash
PUT /api/models/{model_id}/thinking
Content-Type: application/json

{
  "thinking": true
}
```
**Note:** Auto-assigns POWERFUL tier if thinking=true and no tier override
**Response:** Confirmation with tierChanged flag

---

### Toggle Enabled Status
```bash
PUT /api/models/{model_id}/enabled
Content-Type: application/json

{
  "enabled": true
}
```
**Note:** Server restart required for changes to take effect
**Response:** Confirmation with restartRequired flag

---

## Server Management

### Get Server Status
```bash
GET /api/models/servers
```
**Response:** Status of all running llama.cpp servers with metrics

---

## Profile Management

### List Profiles
```bash
GET /api/models/profiles
```
**Response:** Array of profile names

---

### Get Profile Details
```bash
GET /api/models/profiles/{profile_name}
```
**Response:** Full ModelProfile configuration

---

### Create Profile
```bash
POST /api/models/profiles
Content-Type: application/json

{
  "name": "Production",
  "description": "Production deployment",
  "enabledModels": ["model_id_1", "model_id_2"]
}
```
**Response:** Confirmation with profile path

---

### Delete Profile
```bash
DELETE /api/models/profiles/{profile_name}
```
**Response:** Confirmation message

---

## Common HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Unexpected error |
| 503 | Service Unavailable | Service not initialized |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_SCAN_PATH` | `/models` | Directory to scan for GGUF files |
| `REGISTRY_PATH` | `data/model_registry.json` | Registry persistence path |
| `LLAMA_SERVER_PATH` | `/usr/local/bin/llama-server` | llama-server binary path |
| `LLAMA_SERVER_HOST` | `0.0.0.0` | Host for llama.cpp servers |
| `MAX_STARTUP_TIME` | `120` | Max seconds to wait for server startup |
| `READINESS_CHECK_INTERVAL` | `2` | Seconds between readiness checks |

---

## Testing

```bash
# Run all endpoint tests
cd backend
python3 test_api_endpoints.py

# Test against custom URL
python3 test_api_endpoints.py --base-url http://localhost:8000
```

---

## Example Workflows

### Initial Setup
```bash
# 1. Scan for models
curl -X POST http://localhost:8000/api/models/rescan

# 2. Get registry
curl http://localhost:8000/api/models/registry

# 3. Enable models
curl -X PUT http://localhost:8000/api/models/MODEL_ID/enabled \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### Model Configuration
```bash
# Update tier override
curl -X PUT http://localhost:8000/api/models/MODEL_ID/tier \
  -H "Content-Type: application/json" \
  -d '{"tier": "powerful"}'

# Mark as thinking model
curl -X PUT http://localhost:8000/api/models/MODEL_ID/thinking \
  -H "Content-Type: application/json" \
  -d '{"thinking": true}'
```

### Profile Management
```bash
# List profiles
curl http://localhost:8000/api/models/profiles

# Load profile
curl http://localhost:8000/api/models/profiles/development

# Create profile
curl -X POST http://localhost:8000/api/models/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Profile",
    "description": "Custom profile",
    "enabledModels": ["model_id_1"]
  }'
```

---

## Frontend Integration

### React/TypeScript Example
```typescript
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000',
});

// Get registry
const registry = await client.get('/api/models/registry');

// Update tier
await client.put(`/api/models/${modelId}/tier`, { tier: 'powerful' });

// List profiles
const profiles = await client.get('/api/models/profiles');
```

### TanStack Query Hook
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

export const useModelRegistry = () => {
  return useQuery({
    queryKey: ['models', 'registry'],
    queryFn: () => client.get('/api/models/registry').then(r => r.data),
  });
};

export const useUpdateTier = () => {
  return useMutation({
    mutationFn: ({ modelId, tier }: { modelId: string; tier: string }) =>
      client.put(`/api/models/${modelId}/tier`, { tier }),
  });
};
```

---

## Error Handling

All endpoints return structured errors:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "field": "value"
  }
}
```

**Common Error Types:**
- `ServiceUnavailable` - Service not initialized
- `ModelNotFound` - Model ID not in registry
- `ProfileNotFound` - Profile doesn't exist
- `InvalidTier` - Tier value not valid
- `RescanFailed` - Model rescan error
- `RegistrySaveFailed` - Failed to persist changes

---

## Response Format

All responses use camelCase keys:
- `modelId` (not `model_id`)
- `totalServers` (not `total_servers`)
- `enabledModels` (not `enabled_models`)

This is configured via Pydantic `alias` parameters.
