# Timeout Configuration Quick Reference

## Current Settings (After Fix)

| Model | Tier | Timeout | Retries | Delay | Worst-Case | Status |
|-------|------|---------|---------|-------|------------|--------|
| Q2_FAST_1 | Q2 | 30s | 0 | 2s | 30s | ✓ Fits in 30s |
| Q2_FAST_2 | Q2 | 30s | 0 | 2s | 30s | ✓ Fits in 30s |
| Q3_SYNTH | Q3 | 45s | 2 | 3s | 51s | ✓ Expected |
| Q4_DEEP | Q4 | 120s | 1 | 5s | 125s | ✓ Expected |

## Formula

```
Worst-case time = timeout_seconds + (max_retries × retry_delay_seconds)
```

## Key Changes From Original

### Before (Broken)
- Q2: 10s timeout, 3 retries, exponential backoff → **~37s** ✗
- Frontend timeout: 30s
- Result: **Queries timed out**

### After (Fixed)
- Q2: 30s timeout, 0 retries, linear backoff → **30s** ✓
- Frontend timeout: 30s
- Result: **Queries complete within timeout**

## Retry Logic

### Exponential Backoff (OLD - REMOVED)
```python
backoff = 2 ** attempt  # 1s, 2s, 4s, 8s...
# Problem: Quickly compounds to huge delays
```

### Linear Backoff (NEW)
```python
backoff = retry_delay_seconds  # 2s, 2s, 2s...
# Predictable, configurable delays
```

## Performance Expectations

| Model | Typical Response | Timeout | Buffer |
|-------|------------------|---------|--------|
| Q2 | ~2.5s | 30s | 27.5s |
| Q3 | ~5-10s | 45s | 35-40s |
| Q4 | ~15-30s | 120s | 90-105s |

## Configuration Files

**Main config**: `${PROJECT_DIR}/config/default.yaml`

**Schema**: `${PROJECT_DIR}/backend/app/models/config.py`

**Client**: `${PROJECT_DIR}/backend/app/services/llama_client.py`

## Monitoring

Watch for these log messages:
- `"Completion generated successfully"` - First attempt succeeded
- `"Retrying after Xs delay"` - Retry in progress
- `"Completion request failed after N attempts"` - All retries exhausted

## Troubleshooting

### Q2 Queries Still Timing Out?

1. Check model server is running: `curl http://localhost:8080/health`
2. Verify config loaded: Check backend startup logs
3. Monitor actual response times in logs
4. Consider increasing frontend timeout to 35s if needed

### Need More Resilience?

If 0 retries proves insufficient:
```yaml
Q2_FAST_1:
  timeout_seconds: 28      # Reduced slightly
  max_retries: 1           # Add 1 retry
  retry_delay_seconds: 1   # Shorter delay
  # Worst-case: 28 + (1 × 1) = 29s < 30s ✓
```

### Models Too Slow?

1. Check CPU usage on model servers
2. Verify quantization level (Q2 should be fastest)
3. Monitor token counts in requests
4. Consider reducing max_context_tokens if using full 32K
