# Phase 2 Complete: Configuration Profile System

**Related Documents:**
- [PHASE 4 Complete](./PHASE4_COMPLETE.md) - Llama Server Manager
- [PHASE 6 Integration](./PHASE6_INTEGRATION_COMPLETE.md) - Full System Integration
- [Project README](../../README.md)

## Overview

Phase 2 of the MAGI Model Management System has been successfully implemented. This phase introduces a flexible profile system that allows users to create named configurations for different model setups, controlling tier routing, two-stage processing, and load balancing strategies.

## Implementation Summary

### 1. Core Data Models ([backend/app/models/profile.py](../../backend/app/models/profile.py))

Created comprehensive Pydantic models for profile configuration:

- **`TierConfig`**: Defines routing tiers with complexity thresholds and expected response times
- **`TwoStageConfig`**: Configures two-stage processing with stage selection and token limits
- **`LoadBalancingConfig`**: Manages load balancing strategy and health check intervals
- **`ModelProfile`**: Main profile model with enabled models and all configuration options

**Key Features:**
- Full type safety with Pydantic validation
- Default values for common configurations
- Support for infinite complexity thresholds (`.inf`)
- Nested configuration structure

### 2. Profile Manager Service ([backend/app/services/profile_manager.py](../../backend/app/services/profile_manager.py))

Implemented ProfileManager service with full CRUD operations:

**Core Methods:**
- `list_profiles()`: List all available profiles from YAML files
- `load_profile(name)`: Load and validate profile from YAML
- `save_profile(profile)`: Persist profile to YAML with human-readable format
- `delete_profile(name)`: Remove profile from disk
- `validate_profile(profile, available_model_ids)`: Validate enabled models against registry

**Features:**
- Supports both flat and nested YAML structures
- Comprehensive error handling with `MAGIException`
- Structured logging for all operations
- Automatic directory creation
- Filename normalization from profile names

### 3. Default Profile Configurations

Created three default profiles for common use cases:

#### Development Profile ([config/profiles/development.yaml](../../config/profiles/development.yaml))

```yaml
profile:
  name: "Development"
  description: "Fast iteration with small models and two-stage processing"

enabled_models:
  - qwen3_4p0b_q4km_fast
  - deepseek_r10528qwen3_8p0b_q4km_powerful

tier_config:
  - name: "fast"
    max_score: 5.0
    expected_time_seconds: 2
  - name: "powerful"
    max_score: .inf
    expected_time_seconds: 10

two_stage:
  enabled: true
  stage1_tier: "fast"
  stage2_tier: "powerful"
  stage1_max_tokens: 500

load_balancing:
  enabled: false
```

**Use Case:** Development workflow with quick iteration using a fast model for initial responses and a reasoning model for complex refinement.

#### Production Profile ([config/profiles/production.yaml](../../config/profiles/production.yaml))

```yaml
profile:
  name: "Production"
  description: "High-quality responses with best models and load balancing"

enabled_models:
  - deepseek_r10528qwen3_8p0b_q4km_powerful
  - qwen2_coder_p5_14p0b_q4km_powerful

tier_config:
  - name: "powerful"
    max_score: .inf
    expected_time_seconds: 15

two_stage:
  enabled: false

load_balancing:
  enabled: true
  strategy: "round_robin"
  health_check_interval: 30
```

**Use Case:** Production deployment with high-quality reasoning and coding models, load balanced for reliability.

#### Fast-Only Profile ([config/profiles/fast-only.yaml](../../config/profiles/fast-only.yaml))

```yaml
profile:
  name: "Fast Only"
  description: "Maximum speed with single small model"

enabled_models:
  - qwen3_4p0b_q4km_fast

tier_config:
  - name: "fast"
    max_score: .inf
    expected_time_seconds: 2

two_stage:
  enabled: false

load_balancing:
  enabled: false
```

**Use Case:** Speed-optimized setup for simple queries with minimal latency.

## Architecture Highlights

### Profile-Model Integration

Profiles reference models by their `model_id` from the registry:
- Enables/disables specific models for a profile
- Validates model existence against registry
- Allows tier overrides per profile

### Tier Routing System

Profiles define complexity-to-tier mappings:
- Each tier has a `max_score` threshold
- Queries below threshold route to that tier
- Last tier typically has `max_score: .inf` for catch-all

### Two-Stage Processing

Enables fast initial response + deep refinement:
1. Stage 1: Fast model generates initial response (limited tokens)
2. Stage 2: Powerful model refines/expands (full response)
3. Token budget prevents stage 1 runaway

### Load Balancing Configuration

Profiles control load balancing per deployment:
- **Strategy**: `round_robin`, `least_loaded`, or `random`
- **Health checks**: Configurable interval for model health monitoring
- Can be disabled for single-model profiles

## Testing Results

### Basic Tests (`test_profile_system.py`)

✅ **TEST 1: Profile Manager Operations**
- Successfully lists 3 profiles
- Loads all profiles without errors
- Parses YAML correctly
- Extracts tier configs, two-stage settings, load balancing config

✅ **TEST 2: Profile Validation**
- Validates profiles against model registry
- Identifies missing models
- Confirms model existence

✅ **TEST 3: Profile Structure Details**
- Development profile: Two-stage enabled correctly
- Production profile: Load balancing configured
- Fast-only profile: Single tier, single model

### Integration Tests (`test_profile_integration.py`)

✅ **Profile Integration with Registry**
- All profile models validate against mock registry
- Displays enabled models with full metadata
- Shows tier routing configuration
- Displays special configs (two-stage, load balancing)

✅ **Tier Matching Test**
- All enabled models have matching tiers in profile config
- No tier mismatches detected
- Routing logic validated

## Code Quality

### Type Safety
- Full type hints on all functions and methods
- Pydantic models provide runtime validation
- Enum types for tier and quantization levels

### Error Handling
- Uses custom `MAGIException` with status codes
- Provides detailed error context
- Includes available options in 404 errors

### Logging
- Structured logging with Python's `logging` module
- Info-level logs for all operations
- Warning-level logs for validation issues

### Documentation
- Google-style docstrings on all public methods
- Inline comments for complex logic
- Comprehensive module docstrings

## File Structure

```
MAGI/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── profile.py              # Profile data models
│   │   └── services/
│   │       └── profile_manager.py      # Profile management service
│   ├── test_profile_system.py          # Basic tests
│   └── test_profile_integration.py     # Integration tests
└── config/
    └── profiles/
        ├── development.yaml             # Dev profile
        ├── production.yaml              # Prod profile
        └── fast-only.yaml               # Speed profile
```

## API Usage Examples

### Loading a Profile

```python
from app.services.profile_manager import ProfileManager
from pathlib import Path

manager = ProfileManager(profiles_dir=Path("config/profiles"))

# List available profiles
profiles = manager.list_profiles()  # ['development', 'production', 'fast-only']

# Load specific profile
profile = manager.load_profile("development")

# Access configuration
print(profile.enabled_models)
print(profile.two_stage.enabled)
for tier in profile.tier_config:
    print(f"{tier.name}: max_score={tier.max_score}")
```

### Creating a Custom Profile

```python
from app.models.profile import ModelProfile, TierConfig

profile = ModelProfile(
    name="Custom Setup",
    description="My custom configuration",
    enabled_models=["qwen3_4p0b_q4km_fast"],
    tier_config=[
        TierConfig(
            name="fast",
            max_score=float('inf'),
            expected_time_seconds=3
        )
    ]
)

# Save to disk
manager.save_profile(profile)
```

### Validating Profiles

```python
from app.services.model_discovery import ModelDiscoveryService

# Load registry
discovery = ModelDiscoveryService(scan_path=Path("/path/to/models"))
registry = discovery.load_registry(Path("data/model_registry.json"))

# Validate profile
profile = manager.load_profile("development")
missing_models = manager.validate_profile(
    profile,
    list(registry.models.keys())
)

if missing_models:
    print(f"Invalid: missing {missing_models}")
else:
    print("Profile is valid")
```

## Integration Points

### With Phase 1 (Model Discovery)
- Profiles reference models by `model_id` from registry
- Validation ensures profile models exist in registry
- Tier assignments from discovery match profile tier configs

### With Phase 3 (Health Monitoring)
- Load balancing config controls health check frequency
- Enabled models from profile determine which models to monitor
- Health status feeds into load balancing decisions

### With Phase 4 (Query Routing)
- Tier config provides complexity thresholds for routing
- Two-stage config enables multi-pass processing
- Expected time helps with timeout configuration

## Next Steps: Phase 3

See [PHASE 4 Complete](./PHASE4_COMPLETE.md) for the next implementation phase.

**Health Monitoring System**
- Implement health check service for model servers
- Create health status models and endpoints
- Add periodic health monitoring with configurable intervals
- Implement circuit breaker pattern for failing models
- Build health metrics dashboard

**Prerequisites from Phase 2:**
- ✅ Load balancing configuration structure
- ✅ Health check interval settings
- ✅ Enabled models list for monitoring scope

## Summary

Phase 2 successfully implements a flexible, user-friendly profile system for MAGI:

**Achievements:**
- ✅ Complete profile data models with Pydantic validation
- ✅ Full CRUD operations for profile management
- ✅ Three default profiles covering common use cases
- ✅ Comprehensive test suite with 100% pass rate
- ✅ Clean integration with Phase 1 model registry
- ✅ Ready for Phase 3 health monitoring integration

**Code Quality:**
- Production-ready code with full type hints
- Comprehensive error handling and logging
- Well-documented with clear examples
- Follows MAGI code style guidelines

The profile system provides a solid foundation for flexible model orchestration and query routing. Users can easily create custom profiles for different scenarios while maintaining type safety and validation.
