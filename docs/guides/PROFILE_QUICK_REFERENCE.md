# MAGI Profile System - Quick Reference

## Profile Structure

```yaml
profile:
  name: "Profile Name"
  description: "Description of what this profile does"

# List of model IDs to enable
enabled_models:
  - model_id_1
  - model_id_2

# Tier routing (ordered by complexity)
tier_config:
  - name: "fast"              # Tier name
    max_score: 5.0            # Max complexity score
    expected_time_seconds: 2  # Target response time
    description: "Fast tier"  # Optional description

  - name: "powerful"
    max_score: .inf           # Use .inf for unlimited
    expected_time_seconds: 15

# Two-stage processing (optional)
two_stage:
  enabled: true               # Enable/disable
  stage1_tier: "fast"         # First stage tier
  stage2_tier: "powerful"     # Second stage tier
  stage1_max_tokens: 500      # Token limit for stage 1

# Load balancing (optional)
load_balancing:
  enabled: true
  strategy: "round_robin"     # round_robin, least_loaded, random
  health_check_interval: 30   # Seconds between health checks
```

## Available Models (from Phase 1)

```python
# POWERFUL tier (8B-20B params, Q4_K_M quant)
"gpt_oss_20p0b_q4km_powerful"              # GPT OSS 20B
"qwen2_coder_p5_14p0b_q4km_powerful"       # Qwen2.5 Coder 14B (coding)
"deepseek_r10528qwen3_8p0b_q4km_powerful"  # DeepSeek R1 8B (reasoning)

# FAST tier (4B params, Q4_K_M quant)
"qwen3_vl_4p0b_q4km_fast"                  # Qwen3 VL 4B (vision)
"qwen3_4p0b_q4km_fast"                     # Qwen3 4B
```

## Python API

### Load a Profile

```python
from app.services.profile_manager import ProfileManager
from pathlib import Path

manager = ProfileManager(profiles_dir=Path("config/profiles"))
profile = manager.load_profile("development")
```

### Access Profile Settings

```python
# Enabled models
models = profile.enabled_models
# ['qwen3_4p0b_q4km_fast', 'deepseek_r10528qwen3_8p0b_q4km_powerful']

# Two-stage settings
if profile.two_stage.enabled:
    stage1 = profile.two_stage.stage1_tier  # "fast"
    stage2 = profile.two_stage.stage2_tier  # "powerful"
    max_tokens = profile.two_stage.stage1_max_tokens  # 500

# Load balancing
if profile.load_balancing.enabled:
    strategy = profile.load_balancing.strategy  # "round_robin"
    interval = profile.load_balancing.health_check_interval  # 30

# Tier routing
for tier in profile.tier_config:
    print(f"{tier.name}: max_score={tier.max_score}, "
          f"time={tier.expected_time_seconds}s")
```

### Create a Custom Profile

```python
from app.models.profile import ModelProfile, TierConfig, TwoStageConfig, LoadBalancingConfig

profile = ModelProfile(
    name="My Custom Profile",
    description="Optimized for my use case",
    enabled_models=["qwen3_4p0b_q4km_fast"],
    tier_config=[
        TierConfig(
            name="fast",
            max_score=float('inf'),
            expected_time_seconds=3,
            description="Single fast tier"
        )
    ],
    two_stage=TwoStageConfig(enabled=False),
    load_balancing=LoadBalancingConfig(enabled=False)
)

# Save to disk
path = manager.save_profile(profile)
# Saves to: config/profiles/my-custom-profile.yaml
```

### Validate Profile

```python
from app.services.model_discovery import ModelDiscoveryService

# Load model registry
discovery = ModelDiscoveryService(scan_path=Path("/path/to/models"))
registry = discovery.load_registry(Path("data/model_registry.json"))

# Validate profile
missing = manager.validate_profile(profile, list(registry.models.keys()))

if missing:
    print(f"Invalid profile - missing models: {missing}")
else:
    print("Profile is valid!")
```

### List All Profiles

```python
profiles = manager.list_profiles()
# Returns: ['development', 'fast-only', 'production']

for name in profiles:
    profile = manager.load_profile(name)
    print(f"{profile.name}: {len(profile.enabled_models)} models")
```

## Common Use Cases

### Development Profile
- **Purpose**: Fast iteration during development
- **Models**: 1 fast + 1 reasoning model
- **Two-stage**: Enabled (fast first, reason second)
- **Load balancing**: Disabled
- **Best for**: Testing, debugging, rapid prototyping

### Production Profile
- **Purpose**: High-quality production responses
- **Models**: Multiple powerful models
- **Two-stage**: Disabled (single-pass)
- **Load balancing**: Enabled (round-robin)
- **Best for**: Production deployments, complex queries

### Fast-Only Profile
- **Purpose**: Maximum speed, minimum latency
- **Models**: Single fast model
- **Two-stage**: Disabled
- **Load balancing**: Disabled
- **Best for**: Simple queries, high-throughput scenarios

## Tier Routing Examples

### Single Tier (All Queries)
```yaml
tier_config:
  - name: "fast"
    max_score: .inf
    expected_time_seconds: 2
```
All queries go to "fast" tier regardless of complexity.

### Two Tiers (Fast + Powerful)
```yaml
tier_config:
  - name: "fast"
    max_score: 5.0
    expected_time_seconds: 2
  - name: "powerful"
    max_score: .inf
    expected_time_seconds: 15
```
- Complexity ≤ 5.0 → fast tier (2s target)
- Complexity > 5.0 → powerful tier (15s target)

### Three Tiers (Fast + Balanced + Powerful)
```yaml
tier_config:
  - name: "fast"
    max_score: 3.0
    expected_time_seconds: 2
  - name: "balanced"
    max_score: 7.0
    expected_time_seconds: 5
  - name: "powerful"
    max_score: .inf
    expected_time_seconds: 15
```
- Complexity ≤ 3.0 → fast (2s)
- 3.0 < complexity ≤ 7.0 → balanced (5s)
- Complexity > 7.0 → powerful (15s)

## Two-Stage Processing

### When to Enable
- You want fast initial responses
- Complex queries benefit from refinement
- You have both fast and powerful models

### Configuration
```yaml
two_stage:
  enabled: true
  stage1_tier: "fast"           # Generate initial response
  stage2_tier: "powerful"       # Refine and expand
  stage1_max_tokens: 500        # Prevent runaway generation
```

### Workflow
1. Query complexity is assessed
2. Stage 1: Fast model generates brief response (max 500 tokens)
3. Stage 2: Powerful model refines/expands with full context
4. Final response returned to user

## Load Balancing Strategies

### Round Robin
```yaml
load_balancing:
  strategy: "round_robin"
```
Distributes requests evenly across models in rotation.

### Least Loaded
```yaml
load_balancing:
  strategy: "least_loaded"
```
Routes to model with fewest active requests.

### Random
```yaml
load_balancing:
  strategy: "random"
```
Randomly selects from available models.

## File Locations

```
MAGI/
├── config/
│   └── profiles/
│       ├── development.yaml      # Dev profile
│       ├── production.yaml       # Prod profile
│       ├── fast-only.yaml        # Speed profile
│       └── my-custom.yaml        # Your custom profiles
└── backend/
    ├── app/
    │   ├── models/
    │   │   └── profile.py        # Profile data models
    │   └── services/
    │       └── profile_manager.py # Profile manager
    └── test_profile_*.py          # Test files
```

See also: [Docker Quick Reference](DOCKER_QUICK_REFERENCE.md) for Docker-specific profile management.

## Troubleshooting

### Profile Not Found
```python
# Error: MAGIException: Profile 'my-profile' not found
# Solution: Check profile name (case-sensitive, no .yaml extension)
profiles = manager.list_profiles()  # See available profiles
```

### Invalid YAML
```python
# Error: MAGIException: Failed to load profile: ...
# Solution: Validate YAML syntax
# - Check indentation (use spaces, not tabs)
# - Ensure proper nesting
# - Use .inf for infinity (not inf or Infinity)
```

### Missing Models
```python
# Error: Profile references models not in registry
# Solution: Validate profile
missing = manager.validate_profile(profile, available_model_ids)
# Update profile to use valid model IDs
```

### Tier Mismatch
```python
# Warning: Model tier not in profile tier config
# Solution: Ensure profile has tiers matching enabled models
# If model is "fast", profile should have a "fast" tier config
```

## Best Practices

1. **Name profiles descriptively**: Use names that indicate purpose
2. **Document in description**: Explain when to use this profile
3. **Validate before deployment**: Always validate against registry
4. **Match tiers to models**: Ensure tier configs match model tiers
5. **Set realistic timeouts**: Expected times should match model capabilities
6. **Use two-stage wisely**: Only when you have complementary models
7. **Balance load for production**: Enable load balancing in production
8. **Version control profiles**: Keep profiles in git for team collaboration

## Next Steps

With profiles configured, you can now:
1. **Phase 3**: Implement health monitoring using load balancing configs
2. **Phase 4**: Build query router using tier configurations
3. **Phase 5**: Add two-stage orchestration logic
4. **Phase 6**: Implement load balancer with configured strategies

## Additional Resources

- [Quick Start Model Management Guide](QUICK_START_MODEL_MANAGEMENT.md) - UI for managing profiles
- [Admin Quick Reference](ADMIN_QUICK_REFERENCE.md) - Admin panel operations
- [Docker Quick Reference](DOCKER_QUICK_REFERENCE.md) - Docker commands for profiles
- [Implementation Plan](../architecture/IMPLEMENTATION_PLAN.md) - Overall project roadmap
- [Project Status](../architecture/PROJECT_STATUS.md) - Current implementation status
