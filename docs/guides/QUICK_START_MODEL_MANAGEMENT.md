# MAGI Model Management UI - Quick Start Guide

## Access the UI

**For Docker users:** See [Docker Quick Reference](DOCKER_QUICK_REFERENCE.md) for Docker-specific commands.

1. **Start Backend** (if not running):
   ```bash
   cd ${PROJECT_DIR}/backend
   python -m app.main
   ```

2. **Start Frontend**:
   ```bash
   cd ${PROJECT_DIR}/frontend
   npm run dev
   ```

3. **Open Browser**:
   ```
   http://localhost:5173/model-management
   ```

## UI Overview

### Header
- **Title**: MODEL MANAGEMENT (green glow)
- **RE-SCAN HUB Button**: Triggers model discovery re-scan

### System Status Panel
Shows at-a-glance metrics:
- **Models Discovered**: Total count of discovered models
- **Models Enabled**: How many are enabled for use
- **Servers Running**: Total running model servers
- **Servers Ready**: Ready servers / total running (green=all ready, amber=some not ready)

**Tier Distribution**:
- Fast Tier: Count of fast models
- Balanced Tier: Count of balanced models
- Powerful Tier: Count of powerful models

**Registry Info**:
- Scan Path: HUB directory path
- Last Scan: Timestamp of last discovery scan
- Port Range: Available ports for servers

### Discovered Models Table

**Columns:**
- **ENABLED**: Checkbox to enable/disable model
- **MODEL**: Family name with badges (CODER, INSTRUCT, ⚡ thinking)
- **SIZE**: Parameter count (e.g., 4.0B, 8.0B)
- **QUANT**: Quantization level (Q2_K, Q3_K_M, Q4_K_M)
- **TIER**: Dropdown selector (FAST/BALANCED/POWERFUL)
- **THINKING**: Toggle switch for thinking capability
- **PORT**: Assigned port number (or `-` if not assigned)
- **STATUS**: ACTIVE (green, pulsing) or IDLE (gray)

## Operations

### Enable/Disable a Model
1. Click checkbox in ENABLED column
2. Status updates immediately
3. Server will start/stop on next cycle

### Change Model Tier
1. Click tier dropdown
2. Select FAST, BALANCED, or POWERFUL
3. Orange `*` indicator shows user override
4. Server will use new tier on next startup

### Toggle Thinking Mode
1. Click thinking toggle switch
2. Green switch = thinking enabled
3. Cyan `*` indicator shows user override
4. Affects model inference behavior

### Re-scan HUB Directory
1. Click RE-SCAN HUB button in header
2. Button shows "SCANNING..." with spin animation
3. Table updates with newly discovered models
4. Last Scan timestamp updates

## Visual Indicators

### Status Colors
- **Green** (#00ff41): Active, good, enabled
- **Cyan** (#00ffff): Processing, thinking mode
- **Amber** (#ff9500): Warning, attention needed
- **Red** (#ff0000): Error, critical issue
- **Gray**: Inactive, disabled

### Badges
- **CODER**: Model optimized for code generation
- **INSTRUCT**: Instruction-tuned model
- **⚡**: Thinking model (extended reasoning)

### Override Indicators
- **Orange \***: Tier manually overridden by user
- **Cyan \***: Thinking mode manually overridden by user

### Animations
- **Pulse**: Active status indicator
- **Spin**: Scanning in progress
- **Glow**: Hover effects on interactive elements

## Keyboard Navigation

- **Tab**: Navigate between interactive elements
- **Space**: Toggle checkboxes and switches
- **Enter**: Activate buttons and selects
- **Arrow Keys**: Navigate select dropdowns

## Real-time Updates

- **Server Status**: Updates every 5 seconds
- **Model Registry**: Updates every 30 seconds
- **Manual Updates**: Click RE-SCAN HUB anytime

## Troubleshooting

### "NO MODELS DISCOVERED"
- **Cause**: HUB directory is empty or not scanned
- **Solution**: Click "RUN DISCOVERY SCAN" button

### "FAILED TO LOAD MODEL REGISTRY"
- **Cause**: Backend API not running or unreachable
- **Solution**:
  1. Check backend is running on http://localhost:8000
  2. Click "RETRY" button
  3. Check browser console for errors

### Changes Not Persisting
- **Cause**: Backend registry file not writable
- **Solution**: Check file permissions on `config/model_registry.yaml`

### Models Not Starting
- **Cause**: Model file not found or port conflict
- **Solution**:
  1. Verify model files exist in HUB directory
  2. Check port range configuration
  3. View backend logs for errors

## Tips

1. **Start Small**: Enable 1-2 models per tier initially
2. **Monitor Resources**: Watch server status for memory/CPU usage
3. **Override Thoughtfully**: Auto-detected settings are usually optimal
4. **Re-scan Periodically**: New models won't appear until re-scan

## Advanced

### Custom Tier Assignment
1. Change dropdown to desired tier
2. Orange `*` indicates override
3. To reset: Use backend API or edit YAML directly

### Thinking Override
1. Toggle thinking switch
2. Cyan `*` indicates override
3. Useful for controlling inference speed vs quality

### Profile Management (Future)
- Will allow saving/loading tier configurations
- Bulk enable/disable operations
- Custom model groupings

## Browser Compatibility

- Chrome 120+: ✓ Full support
- Firefox 120+: ✓ Full support
- Safari 17+: ✓ Full support
- Edge 120+: ✓ Full support

## Mobile/Tablet

- Responsive design adapts to screen size
- Touch-friendly interactive elements
- Horizontal scroll for table on small screens

## Accessibility

- Full keyboard navigation
- ARIA labels on all controls
- High contrast colors
- Screen reader compatible

## Performance

- Handles 100+ models smoothly
- <100ms interaction response time
- Smooth 60fps animations
- Automatic caching and invalidation

---

**Need Help?**
- Check backend logs: `backend/logs/`
- Check browser console (F12)
- Review API docs: `/docs` endpoint on backend
- Read full implementation: [Model Management UI Complete](../implementation/MODEL_MANAGEMENT_UI_COMPLETE.md)

## Additional Resources

- [Profile Quick Reference](PROFILE_QUICK_REFERENCE.md) - Managing profiles
- [Admin Quick Reference](ADMIN_QUICK_REFERENCE.md) - Admin panel operations
- [Docker Quick Reference](DOCKER_QUICK_REFERENCE.md) - Docker commands
- [Testing Guide](../TESTING_GUIDE.md) - Testing procedures
- [Project README](../../README.md) - Project overview
