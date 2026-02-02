# Security Architecture

## Localhost-Only Binding

Model servers bind to `127.0.0.1` (localhost):
- NOT directly accessible from outside Docker
- Ports 8080-8099 NOT exposed to host

## Reverse Proxy Access

All model access goes through FastAPI backend:

```bash
# Access via backend proxy
POST /api/proxy/{model_id}/v1/chat/completions
POST /api/proxy/{model_id}/v1/completions
GET /api/proxy/{model_id}/health
```

**Direct access no longer works:**
```bash
# ❌ This fails - ports not exposed
curl http://localhost:8080/v1/chat/completions
```

## Benefits

1. **Security** - Models not exposed to host network
2. **Control** - All access through authenticated backend
3. **Observability** - Request/response logging
4. **Future-proof** - Foundation for auth, rate limiting

## Verification

```bash
# Check ports NOT exposed
docker ps | grep synapse_core
# Only 8000 should be exposed

# Test proxy access
curl http://localhost:8000/api/proxy/{model_id}/health

# Verify localhost binding (inside container)
docker exec synapse_core netstat -tulpn | grep llama-server
# Should show 127.0.0.1:8080, NOT 0.0.0.0:8080
```

## SSH Security (Metal Mode)

- Ed25519 key-only authentication
- Command restriction via `authorized_keys`
- `ssh-wrapper.sh` only allows:
  - `start-metal-servers`
  - `stop-metal-servers`
- All other commands rejected
