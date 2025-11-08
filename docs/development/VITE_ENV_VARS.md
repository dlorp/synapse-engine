# Vite Environment Variables - Docker Configuration Guide

## Problem Summary

Vite environment variables must be available at **BUILD TIME**, not runtime. This is because Vite embeds these values directly into the JavaScript bundle during the `npm run build` step.

**Common Mistake:**
```yaml
# ❌ WRONG - Runtime environment variables (too late!)
environment:
  - VITE_API_URL=http://localhost:8000
```

**Correct Approach:**
```yaml
# ✅ CORRECT - Build arguments
build:
  args:
    - VITE_API_BASE_URL=http://localhost:8000
```

---

## Changes Made

### 1. Frontend Dockerfile (`/frontend/Dockerfile`)

Added build argument declarations and environment variable conversion in the builder stage:

```dockerfile
# Build arguments for Vite environment variables
# These must be declared as ARGs and converted to ENV for Vite to access them
# during the build process. Vite embeds these values into the JavaScript bundle.
ARG VITE_API_BASE_URL=/api
ARG VITE_WS_URL=ws://localhost:8000/ws

# Convert build args to environment variables for Vite build process
# Vite accesses these via import.meta.env.VITE_* during bundling
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_WS_URL=${VITE_WS_URL}

# Build the application
RUN npm run build
```

**Why this works:**
1. `ARG` declares build-time variables that can be passed from docker-compose
2. `ENV` converts these to environment variables that Vite can access
3. Vite reads `import.meta.env.VITE_*` during the build
4. Values are embedded into the JavaScript bundle
5. No runtime configuration needed (bundle is static)

### 2. Docker Compose Configuration (`/docker-compose.yml`)

Changed from runtime environment variables to build arguments:

**Before:**
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    target: production
    args:
      - NODE_VERSION=20
  
  environment:
    - NODE_ENV=production
    - VITE_API_URL=http://localhost:8000  # ❌ Wrong variable name
    - VITE_WS_URL=ws://localhost:8000/ws
```

**After:**
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    target: production
    args:
      - NODE_VERSION=20
      # Vite build-time environment variables
      - VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8000}
      - VITE_WS_URL=${VITE_WS_URL:-ws://localhost:8000/ws}
  
  environment:
    - NODE_ENV=production  # Only runtime var needed
```

**Key changes:**
- Moved `VITE_*` variables from `environment` to `build.args`
- Fixed variable name: `VITE_API_URL` → `VITE_API_BASE_URL`
- Added default values with `${VAR:-default}` syntax
- Removed runtime environment variables (not needed for Vite)

### 3. Environment Variable Template (`.env.example`)

Updated to use correct variable name and added documentation:

```bash
# -----------------------------------------------------------------------------
# Frontend Configuration (Vite)
# -----------------------------------------------------------------------------
# IMPORTANT: These must be available at BUILD TIME for Vite to embed them
# into the JavaScript bundle. Pass them as build args in docker-compose.yml
# or set them before running 'npm run build'.
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

---

## How Vite Environment Variables Work

### Build-Time Embedding

Vite uses a process called **static replacement** during the build:

1. **During Development (`npm run dev`):**
   - Vite reads `.env` files and environment variables
   - Replaces `import.meta.env.VITE_*` with actual values on-the-fly
   - Values can change between refreshes

2. **During Production Build (`npm run build`):**
   - Vite reads environment variables from the shell environment
   - Replaces ALL occurrences of `import.meta.env.VITE_*` with literal values
   - Bundles the code with embedded values
   - **Result: Static JavaScript file with hardcoded values**

### Example

**Source code (`client.ts`):**
```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
});
```

**After build (with `VITE_API_BASE_URL=http://localhost:8000`):**
```javascript
const apiClient = axios.create({
  baseURL: "http://localhost:8000" || '/api',
});
```

The value is **baked into the bundle**. You cannot change it without rebuilding.

---

## Usage Scenarios

### Scenario 1: Development (Local npm run dev)

```bash
# Set environment variables
export VITE_API_BASE_URL=http://localhost:8000
export VITE_WS_URL=ws://localhost:8000/ws

# Run dev server
cd frontend
npm run dev
```

Or use a `.env` file:
```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### Scenario 2: Docker Compose (Default)

```bash
# Uses defaults from docker-compose.yml
docker-compose up --build frontend
```

Defaults:
- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_WS_URL=ws://localhost:8000/ws`

### Scenario 3: Docker Compose (Custom Backend)

```bash
# Override via environment variables
export VITE_API_BASE_URL=http://192.168.1.100:8000
export VITE_WS_URL=ws://192.168.1.100:8000/ws

docker-compose up --build frontend
```

Or use a `.env` file in the project root:
```bash
# .env (project root)
VITE_API_BASE_URL=http://192.168.1.100:8000
VITE_WS_URL=ws://192.168.1.100:8000/ws
```

### Scenario 4: Docker Compose (nginx Proxy)

If using nginx proxy on the same host:

```bash
# Use relative path - nginx will proxy /api to backend
export VITE_API_BASE_URL=/api
export VITE_WS_URL=/ws

docker-compose up --build frontend
```

This is the **recommended approach** for production with a reverse proxy.

---

## Verification

### Check Build Arguments Were Passed

```bash
# Build with verbose output
docker-compose build --progress=plain frontend 2>&1 | grep VITE_
```

You should see:
```
#8 [builder 6/8] ARG VITE_API_BASE_URL=/api
#9 [builder 7/8] ARG VITE_WS_URL=ws://localhost:8000/ws
```

### Check Environment During Build

Add a debug line to the Dockerfile (temporary):

```dockerfile
# After ENV declarations
RUN echo "VITE_API_BASE_URL=${VITE_API_BASE_URL}"
RUN echo "VITE_WS_URL=${VITE_WS_URL}"
```

### Check Bundled JavaScript

```bash
# Extract built files from container
docker create --name temp_frontend magi_frontend
docker cp temp_frontend:/usr/share/nginx/html ./dist_check
docker rm temp_frontend

# Search for the API URL in bundled JavaScript
grep -r "localhost:8000" ./dist_check/assets/
```

You should see your configured URL embedded in the JavaScript files.

---

## Troubleshooting

### Problem: Frontend shows "Network Error" or wrong API URL

**Cause:** Environment variables not set during build

**Solution:**
1. Check `.env` file exists with correct variable names
2. Rebuild with `--no-cache` to force fresh build:
   ```bash
   docker-compose build --no-cache frontend
   ```
3. Verify build args were passed (see Verification section)

### Problem: Changes to .env not reflected

**Cause:** Docker cache reusing old build layer

**Solution:**
```bash
# Force rebuild without cache
docker-compose build --no-cache frontend
docker-compose up frontend
```

### Problem: Wrong variable name in error messages

**Before fix:**
- Code expects: `VITE_API_BASE_URL`
- docker-compose provides: `VITE_API_URL`
- Result: Undefined, falls back to `/api`

**After fix:**
- Code expects: `VITE_API_BASE_URL`
- docker-compose provides: `VITE_API_BASE_URL`
- Result: Correct URL is used

---

## Best Practices

### 1. Use Relative URLs with Reverse Proxy

**Production setup:**
```yaml
# docker-compose.yml
args:
  - VITE_API_BASE_URL=/api
  - VITE_WS_URL=/ws
```

**nginx configuration:**
```nginx
location /api {
  proxy_pass http://backend:8000;
}

location /ws {
  proxy_pass http://backend:8000/ws;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
}
```

**Benefits:**
- No CORS issues (same origin)
- Works with any hostname
- No hardcoded URLs in bundle
- Easy to deploy anywhere

### 2. Use Absolute URLs for Development

**Development setup:**
```yaml
# docker-compose.dev.yml (override)
args:
  - VITE_API_BASE_URL=http://localhost:8000
  - VITE_WS_URL=ws://localhost:8000/ws
```

**Benefits:**
- Direct backend access (no proxy needed)
- Faster debugging (see actual endpoints)
- CORS configured in backend

### 3. Document in .env.example

Always include comments explaining:
- When variables are used (build-time vs runtime)
- Default values
- How to override
- Common configurations

---

## Summary

**The Golden Rule:** Vite environment variables must be available when you run `npm run build`, not when you run the container.

**Implementation:**
1. ✅ Declare `ARG` in Dockerfile
2. ✅ Convert to `ENV` for Vite access
3. ✅ Pass as `build.args` in docker-compose
4. ✅ Use correct variable names (`VITE_API_BASE_URL`)
5. ✅ Rebuild when changing values

**Files Updated:**
- `/frontend/Dockerfile` - Added ARG and ENV declarations
- `/docker-compose.yml` - Moved variables to build.args
- `/.env.example` - Updated variable names and documentation

**Result:**
- Frontend correctly connects to backend API
- Admin page loads without network errors
- Configuration is maintainable and documented
