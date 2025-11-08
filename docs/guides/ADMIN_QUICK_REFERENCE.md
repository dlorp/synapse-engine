# S.Y.N.A.P.S.E. ENGINE Admin Page - Quick Reference

**Full Documentation:** [Admin Page Complete](../implementation/ADMIN_PAGE_COMPLETE.md)

## Access

**URL**: `http://localhost:5173/admin`
**Sidebar**: Click "Admin" (◎ icon)

## Quick Operations

### 1. Discover Models
**When**: After adding new models to HUB
**Action**: Click "RUN DISCOVERY"
**Result**: Scans `/models`, updates registry

### 2. Check Health
**When**: Verify system is working
**Action**: View "SYSTEM HEALTH" panel (auto-refreshes)
**Result**: Shows registry, servers, profiles status

### 3. Test Endpoints
**When**: After making changes
**Action**: Click "RUN TESTS"
**Result**: Tests all API endpoints, shows pass/fail

### 4. Restart Servers
**When**: Apply config changes or fix errors
**Action**: Click "RESTART ALL SERVERS" + confirm
**Result**: Stops and restarts all model servers

### 5. Stop Servers
**When**: Shut down all models
**Action**: Click "STOP ALL SERVERS" + confirm
**Result**: Stops all llama-server processes

### 6. View System Info
**When**: Check configuration
**Action**: View "SYSTEM INFORMATION" panel
**Result**: Shows environment, Python, services

## Status Colors

- 🟢 **Green (Healthy/Passed)**: Everything OK
- 🟠 **Amber (Degraded/Warning)**: Some issues
- 🔴 **Red (Error/Failed)**: Critical problem

## Typical Workflow

1. **Start Docker**: `docker-compose up -d`
2. **Open Browser**: `http://localhost:5173/admin`
3. **Check Health**: Verify all green
4. **Run Discovery**: If needed (new models)
5. **Test Endpoints**: Verify all pass
6. **Use System**: Start querying models!

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Health degraded | Check which component, run discovery or restart |
| Discovery fails | Check scan path in system info, verify models exist |
| Tests fail | Check health status, review specific test failures |
| Servers won't start | Run discovery first, check backend logs |

## No CLI Commands Needed!

Everything is in the browser:
- ✅ Model discovery
- ✅ Health monitoring
- ✅ API testing
- ✅ Server control
- ✅ System info

**Perfect for Docker-based testing!**

## Additional Resources

- [Admin Page Complete](../implementation/ADMIN_PAGE_COMPLETE.md) - Full documentation
- [Model Management Quick Start](QUICK_START_MODEL_MANAGEMENT.md) - Model UI guide
- [Docker Quick Reference](DOCKER_QUICK_REFERENCE.md) - Docker commands
- [Testing Guide](../TESTING_GUIDE.md) - Testing procedures
- [Project README](../../README.md) - Project overview
