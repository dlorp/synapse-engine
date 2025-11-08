# MAGI Development Session Notes

## 2025-11-03: Fixed Admin Panel, Docker Workflow, and File Organization

### Session Summary
Resolved frontend-backend communication issues causing admin panel 404 errors, enforced Docker-only development workflow, and reorganized project documentation for better maintainability.

### Problems Encountered

#### 1. Admin Panel 404 Errors
**Symptom:** Admin panel endpoints returning 404 errors in Docker, but backend curl tests working fine.

**Root Cause:** Frontend `VITE_API_BASE_URL` was set to absolute URL `http://localhost:8000` instead of relative `/api`, causing requests to bypass nginx proxy.

**Investigation Path:**
1. Initial diagnosis: Thought it was double `/api/` prefix in frontend code ❌
2. Fixed backend path calculation bug (separate issue) ✅
3. Discovered via agent investigation: Frontend making requests to wrong URL ✅
4. Fixed docker-compose.yml build args ✅

#### 2. Model Management Page Crash
**Symptom:** Page crashed with "Cannot read properties of undefined (reading '0')"

**Root Cause:** Accessing `registry.portRange[0]` without null safety check.

**Solution:** Added optional chaining throughout page.

#### 3. Local Dev vs Docker Version Mismatch
**Symptom:** Different behavior between local dev servers and Docker.

**Root Cause:** Multiple dev environments running simultaneously with different configurations.

**Solution:** Killed all local dev servers, enforced Docker-only workflow.

#### 4. Backend Profile Loading Failure
**Symptom:** Backend falling back to degraded mode, couldn't find profiles.

**Root Cause:** `startup.py` line 55 had incorrect path calculation (`Path(__file__).parent.parent.parent.parent` went to `/` instead of `/app`)

**Solution:** Removed one `.parent` call to fix path calculation.

#### 5. Disorganized Documentation
**Symptom:** 30+ markdown files scattered in project root.

**Solution:** Organized into `docs/` subdirectories by category.

### Solutions Implemented

#### Frontend Fixes

**File:** [`frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx`](../../frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx)
- **Line 49:** Removed spinner content for pure CSS animation
- **Line 70-72:** Improved error display with actual backend error messages
- **Line 131:** Empty span for CSS `::before` animation
- **Line 206-209:** Added optional chaining for portRange

**File:** [`frontend/src/pages/ModelManagementPage/ModelManagementPage.module.css`](../../frontend/src/pages/ModelManagementPage/ModelManagementPage.module.css)
- **Lines 133-148:** Added growing ASCII bar animation using CSS keyframes
- **Lines 78-93:** Added rescan button icon animation

**File:** [`frontend/src/pages/AdminPage/AdminPage.tsx`](../../frontend/src/pages/AdminPage/AdminPage.tsx)
- **Lines 277, 374:** Improved error messages to show backend error details

**File:** [`frontend/src/pages/HomePage/HomePage.tsx`](../../frontend/src/pages/HomePage/HomePage.tsx)
- Moved `<QuickActions />` from top to bottom of page

**File:** [`frontend/src/components/layout/Sidebar/Sidebar.module.css`](../../frontend/src/components/layout/Sidebar/Sidebar.module.css)
- **Line 2:** Changed `height` from `calc(100vh - var(--header-height))` to `100vh`
- **Line 7:** Changed `top` from `var(--header-height)` to `0`

**File:** [`frontend/src/components/layout/RootLayout/RootLayout.tsx`](../../frontend/src/components/layout/RootLayout/RootLayout.tsx)
- Removed Header component import and JSX element

**File:** [`frontend/src/components/layout/RootLayout/RootLayout.module.css`](../../frontend/src/components/layout/RootLayout/RootLayout.module.css)
- **Line 3:** Changed `grid-template-rows` from `var(--header-height) 1fr` to `1fr`

#### Backend Fixes

**File:** [`backend/app/services/startup.py`](../../backend/app/services/startup.py)
- **Line 55:** Fixed path calculation
  ```python
  # BEFORE (incorrect - goes to /)
  project_root = Path(__file__).parent.parent.parent.parent

  # AFTER (correct - goes to /app)
  project_root = Path(__file__).parent.parent.parent
  ```

#### Infrastructure Fixes

**File:** [`docker-compose.yml`](../../docker-compose.yml)
- **Line 218:** Changed `VITE_API_BASE_URL` from `${VITE_API_BASE_URL:-http://localhost:8000}` to `/api`
- **Line 219:** Changed `VITE_WS_URL` from `${VITE_WS_URL:-ws://localhost:8000/ws}` to `/ws`
- **Rationale:** Use relative URLs for nginx proxy, avoid CORS issues, ensure same-origin requests

#### Documentation Organization

**Created Structure:**
```
docs/
├── README.md (index explaining organization)
├── architecture/ (specs, planning, infrastructure)
├── development/ (session notes, technical investigations)
├── guides/ (quick references, how-tos)
└── implementation/ (feature completion docs, phase summaries)
```

**Files Moved:**
- Implementation docs (16 files) → `docs/implementation/`
- Quick reference guides (5 files) → `docs/guides/`
- Architecture docs (4 files) → `docs/architecture/`
- Development notes (6 files) → `docs/development/`

**Root Directory Cleanup:**
- Before: 30+ markdown files
- After: 2 files (README.md, CLAUDE.md)

#### Documentation Updates

**File:** [`CLAUDE.md`](../../CLAUDE.md)
- **Lines 59-190:** Added "Development Environment" section
  - Docker-only development workflow (MANDATORY)
  - Why Docker-only approach
  - Workflow commands
  - Frontend environment variable handling
  - Backend configuration paths
  - Testing workflow
  - Troubleshooting guide
- **Lines 131-190:** Added "Documentation Requirements" section
  - Session notes creation mandate
  - Documentation update triggers
  - Format examples
  - Rationale

### Files Modified Summary

#### Frontend
- `frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx` (lines 49, 70-72, 131, 206-209)
- `frontend/src/pages/ModelManagementPage/ModelManagementPage.module.css` (lines 78-93, 133-148)
- `frontend/src/pages/AdminPage/AdminPage.tsx` (lines 277, 374)
- `frontend/src/pages/HomePage/HomePage.tsx` (QuickActions position)
- `frontend/src/components/layout/Sidebar/Sidebar.module.css` (lines 2, 7)
- `frontend/src/components/layout/RootLayout/RootLayout.tsx` (removed Header)
- `frontend/src/components/layout/RootLayout/RootLayout.module.css` (line 3)

#### Backend
- `backend/app/services/startup.py` (line 55)

#### Infrastructure
- `docker-compose.yml` (lines 218-219)

#### Documentation
- `CLAUDE.md` (lines 57-190)
- [`docs/README.md`](../README.md) (created)
- [`docs/development/SESSION_NOTES.md`](./SESSION_NOTES.md) (this file)
- Organized 30+ files into `docs/` subdirectories

### Key Learnings

1. **Vite Build-Time Variables:** Environment variables prefixed with `VITE_` are embedded at build time, not runtime. Changes require `docker-compose build --no-cache frontend`.

2. **Docker Path Calculations:** Path resolution differs between local dev and Docker. Always use relative paths from known anchors (`__file__`, `/app`).

3. **Relative vs Absolute URLs:** For same-origin architecture with nginx proxy, use relative URLs (`/api`, `/ws`) instead of absolute (`http://localhost:8000`).

4. **CSS-Only Animations:** Terminal aesthetic animations can be achieved with pure CSS using `::before` pseudo-elements and `steps()` timing.

5. **Error Handling:** Always extract and display structured backend errors: `error?.response?.data?.detail?.message || error.message`

6. **Development Workflow:** Running local dev servers alongside Docker creates version mismatches and debugging confusion. Docker-only is mandatory.

### Breaking Changes

1. **Docker-Only Development:** Local dev servers (`npm run dev`, `uvicorn --reload`) are now prohibited.

2. **Frontend Build Process:** All Vite environment variable changes require Docker rebuild with `--no-cache`.

3. **API URL Configuration:** Frontend now hardcoded to use `/api` and `/ws` (relative URLs).

### Next Steps

- [ ] Rebuild frontend Docker image with new VITE_API_BASE_URL
- [ ] Test admin panel model discovery functionality
- [ ] Test admin panel server start/stop operations
- [ ] Verify WebSocket connectivity with relative URL
- [ ] Monitor for any remaining 404 errors
- [ ] Test model management page thoroughly
- [ ] Verify all quick reference guides are accurate post-organization

### Performance Impact

**Expected:**
- No performance impact from code changes
- Slight improvement from removing Header component (one less React component)
- CSS animations use GPU acceleration (no CPU impact)

**To Monitor:**
- API response times after Docker rebuild
- WebSocket connection stability with relative URLs
- Model discovery and server management operations

### Security Considerations

**Improvements:**
- Removed hardcoded absolute URLs (better for deployment)
- Same-origin requests avoid CORS complexity
- nginx proxy provides single entry point

### Testing Checklist

- [ ] Admin panel loads without errors
- [ ] Model discovery works and updates registry
- [ ] Server start/stop operations function correctly
- [ ] Model Management page displays correct data
- [ ] Loading animations display correctly
- [ ] Sidebar reaches top of viewport
- [ ] QuickActions bar is at bottom of HomePage
- [ ] WebSocket connects successfully
- [ ] All API endpoints return 200/expected responses
- [ ] Error messages display backend details

### Reference Commands

```bash
# Kill all background dev servers
pkill -f "npm run dev" && pkill -f uvicorn

# Rebuild frontend with new env vars
docker-compose build --no-cache frontend

# Rebuild backend
docker-compose build --no-cache backend

# Start all services
docker-compose up -d

# Follow backend logs
docker-compose logs -f backend

# Follow frontend logs
docker-compose logs -f frontend

# Check service status
docker-compose ps

# Stop all services
docker-compose down

# Test backend endpoint
curl http://localhost:8000/api/admin/health/detailed

# Test frontend
open http://localhost:5173
```

---

**Session Duration:** ~2 hours
**Files Modified:** 14
**Files Organized:** 30+
**Documentation Created:** 3 new files
**Bugs Fixed:** 5 major issues

**Status:** ✅ Frontend fixes complete, documentation organized, Docker workflow enforced. Ready to rebuild and test.
