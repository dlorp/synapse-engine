# Council Moderator Modes - User Guide

**Status:** ✅ Implemented
**Date:** 2025-11-08
**Version:** 1.1.0 (Added Toggleable Active Moderation)

## Overview

The Council Moderator feature now offers **flexible moderation control** with two independent toggles:

1. **Post-Debate Analysis** (`councilModerator`) - Comprehensive analysis after debate completes
2. **Active Interjections** (`councilModeratorActive`) - Real-time guidance during the debate

You can enable either, both, or neither depending on your needs.

---

## Quick Start

### Four Moderation Modes

| Mode | `councilModerator` | `councilModeratorActive` | Behavior |
|------|-------------------|-------------------------|----------|
| **None** | `false` | `false` | No moderation - models debate freely |
| **Post-Analysis Only** | `true` | `false` | Models debate freely, then moderator analyzes the dialogue |
| **Active Guidance Only** | `false` | `true` | Moderator interjects during debate to keep on track |
| **Full Moderation** | `true` | `true` | Active interjections + comprehensive post-debate analysis |

---

## Mode 1: No Moderation

**Use when:** You want completely organic debate without any intervention

```json
{
  "query": "What is the capital of France?",
  "mode": "council",
  "councilAdversarial": true,
  "councilModerator": false,
  "councilModeratorActive": false
}
```

**Result:**
- Models debate freely without interruption
- No post-debate analysis
- `councilModeratorInterjections`: 0
- `councilModeratorAnalysis`: null

**Best for:**
- Quick debates
- When you want unfiltered model perspectives
- Testing model behavior without external influence

---

## Mode 2: Post-Debate Analysis Only

**Use when:** You want comprehensive analysis but don't want to interrupt the natural debate flow

```json
{
  "query": "Should we use Python or Go for microservices?",
  "mode": "council",
  "councilAdversarial": true,
  "councilModerator": true,
  "councilModeratorActive": false
}
```

**Result:**
- Models debate freely without interruption
- After debate completes, moderator analyzes full dialogue
- Provides comprehensive breakdown of:
  - Argument strength (PRO vs CON)
  - Logical fallacies detected
  - Rhetorical techniques used
  - Key turning points
  - Unanswered questions
  - Overall winner assessment

**Response includes:**
```json
{
  "metadata": {
    "councilModeratorAnalysis": "DEBATE ANALYSIS\n\n1. ARGUMENT STRENGTH...",
    "councilModeratorModel": "deepseek_r10528qwen3_8p0b_q4km_powerful",
    "councilModeratorTokens": 3895,
    "councilModeratorBreakdown": {
      "argument_strength": {...},
      "logical_fallacies": [...],
      "overall_winner": "pro"
    },
    "councilModeratorInterjections": 0
  }
}
```

**Best for:**
- Important decisions where you need deep analysis
- Learning from debate patterns
- Identifying argument weaknesses
- Post-mortem analysis

---

## Mode 3: Active Interjections Only

**Use when:** You want the moderator to keep the debate focused but don't need post-analysis

```json
{
  "query": "What is the capital of France?",
  "mode": "council",
  "councilAdversarial": true,
  "councilModerator": false,
  "councilModeratorActive": true,
  "councilModeratorCheckFrequency": 2
}
```

**Behavior:**
- Every N turns (default: 2), moderator reviews recent dialogue
- If models go off-topic, moderator interjects with guidance
- Moderator turns appear with `speakerId="MODERATOR"`
- Max 3 interjections per debate (prevents domination)

**Example Dialogue:**
```
Turn 1 [PRO]: France has a rich history dating back...
Turn 2 [CON]: The French Revolution was a pivotal moment...
[Moderator check: OFF-TOPIC]
Turn 3 [MODERATOR]: "Let's refocus on the question: What is the capital of France?"
Turn 4 [PRO]: Paris is the capital of France.
Turn 5 [CON]: I agree, the answer is Paris.
[Moderator check: ON TRACK]
```

**Response includes:**
```json
{
  "councilTotalTurns": 5,
  "councilTurns": [
    {"turnNumber": 1, "speakerId": "model_pro", "content": "..."},
    {"turnNumber": 2, "speakerId": "model_con", "content": "..."},
    {"turnNumber": 3, "speakerId": "MODERATOR", "content": "Let's refocus..."},
    {"turnNumber": 4, "speakerId": "model_pro", "content": "..."},
    {"turnNumber": 5, "speakerId": "model_con", "content": "..."}
  ],
  "metadata": {
    "councilModeratorInterjections": 1,
    "councilModeratorAnalysis": null
  }
}
```

**Best for:**
- Simple questions where models tend to over-elaborate
- Keeping debates on track
- Time-constrained situations
- When you don't need comprehensive analysis

---

## Mode 4: Full Moderation (Both)

**Use when:** You want both real-time guidance AND comprehensive post-debate analysis

```json
{
  "query": "TypeScript vs JavaScript for backend development?",
  "mode": "council",
  "councilAdversarial": true,
  "councilModerator": true,
  "councilModeratorActive": true,
  "councilModeratorCheckFrequency": 2
}
```

**Behavior:**
- Active interjections during debate (keeps on track)
- Comprehensive post-debate analysis (deep insights)
- Best of both worlds

**Response includes:**
```json
{
  "councilTotalTurns": 7,
  "metadata": {
    "councilModeratorInterjections": 1,
    "councilModeratorAnalysis": "DEBATE ANALYSIS\n\n...",
    "councilModeratorBreakdown": {...}
  }
}
```

**Best for:**
- Critical decisions requiring maximum oversight
- Complex topics where models might drift
- When you want both guidance and analysis
- Production use cases with high stakes

---

## Configuration Parameters

### Core Toggles

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `councilModerator` | boolean | `false` | Enable post-debate analysis |
| `councilModeratorActive` | boolean | `false` | Enable active interjections during debate |

### Advanced Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `councilModeratorModel` | string | Auto | Specific model ID for moderator (auto-selects POWERFUL tier if not specified) |
| `councilModeratorCheckFrequency` | integer | `2` | How often moderator checks debate (1-10 turns). Only applies if `councilModeratorActive=true` |

### Model Selection

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `councilProModel` | string | Auto | Specific model for PRO position |
| `councilConModel` | string | Auto | Specific model for CON position |

---

## Performance Impact

| Mode | Processing Time | Cost | When to Use |
|------|----------------|------|-------------|
| **None** | Baseline | Lowest | Quick debates, testing |
| **Post-Analysis** | +2-5s | +1 LLM call | Deep insights needed |
| **Active** | +2-4s | +1-3 LLM calls | Keep on track |
| **Full** | +4-9s | +2-4 LLM calls | Maximum oversight |

**Note:** Active interjections only add cost when moderator actually interjects (not every check).

---

## Testing

### Manual Test Script

Run all 4 modes with one command:

```bash
./test_moderator_modes.sh
```

This script tests:
1. No moderation (baseline)
2. Post-analysis only
3. Active interjections only
4. Both

### Individual Tests

#### Test Post-Analysis Only
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python vs Go for microservices?",
    "mode": "council",
    "councilAdversarial": true,
    "councilModerator": true,
    "councilModeratorActive": false
  }' | jq '.metadata.councilModeratorAnalysis'
```

#### Test Active Interjections Only
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "mode": "council",
    "councilAdversarial": true,
    "councilModerator": false,
    "councilModeratorActive": true
  }' | jq '{interjections: .metadata.councilModeratorInterjections, speakers: [.councilTurns[]?.speakerId]}'
```

---

## Frontend Integration

### TypeScript Types

Updated types in `frontend/src/types/query.ts`:

```typescript
export interface QueryRequest {
  // ... other fields
  councilModerator?: boolean;          // Post-debate analysis
  councilModeratorActive?: boolean;    // Active interjections
  councilModeratorModel?: string;
  councilModeratorCheckFrequency?: number;
}

export interface QueryMetadata {
  // ... other fields
  councilModeratorAnalysis?: string;
  councilModeratorModel?: string;
  councilModeratorTokens?: number;
  councilModeratorBreakdown?: {
    argument_strength?: any;
    logical_fallacies?: string[];
    rhetorical_techniques?: string[];
    key_turning_points?: string[];
    unanswered_questions?: string[];
    overall_winner?: 'pro' | 'con' | 'tie' | null;
  };
  councilModeratorInterjections?: number;
}
```

### UI Implementation (TODO)

Future frontend work:
1. Add toggle switches for `councilModerator` and `councilModeratorActive`
2. Display moderator analysis in ResponseDisplay panel
3. Show moderator interjection turns with distinct styling (orange border for MODERATOR speaker)
4. Add dropdown for moderator model selection

---

## API Reference

### Request Schema

```json
{
  "query": "string (required)",
  "mode": "council",
  "councilAdversarial": true,

  // Moderation toggles
  "councilModerator": false,        // Post-debate analysis
  "councilModeratorActive": false,  // Active interjections

  // Advanced
  "councilModeratorModel": "model_id",
  "councilModeratorCheckFrequency": 2,

  // Model selection
  "councilProModel": "model_id",
  "councilConModel": "model_id",

  // Dialogue config
  "councilMaxTurns": 10,
  "councilDynamicTermination": true
}
```

### Response Schema

```json
{
  "id": "uuid",
  "query": "string",
  "response": "string (synthesis)",

  // Dialogue turns
  "councilDialogue": true,
  "councilTurns": [
    {
      "turnNumber": 1,
      "speakerId": "model_pro | model_con | MODERATOR",
      "persona": "string",
      "content": "string",
      "timestamp": "ISO8601",
      "tokensUsed": 123
    }
  ],
  "councilTotalTurns": 5,
  "councilSynthesis": "string",
  "councilTerminationReason": "string",

  // Metadata
  "metadata": {
    // Interjection count
    "councilModeratorInterjections": 1,

    // Post-debate analysis
    "councilModeratorAnalysis": "string (full analysis text)",
    "councilModeratorModel": "model_id",
    "councilModeratorTokens": 3895,
    "councilModeratorBreakdown": {
      "argument_strength": {
        "pro_strengths": ["..."],
        "pro_weaknesses": ["..."],
        "con_strengths": ["..."],
        "con_weaknesses": ["..."]
      },
      "logical_fallacies": ["..."],
      "rhetorical_techniques": ["..."],
      "key_turning_points": ["..."],
      "unanswered_questions": ["..."],
      "overall_winner": "pro | con | tie | null"
    }
  }
}
```

---

## Migration from v1.0

**Backwards Compatibility:** ✅ Fully backwards compatible

Old behavior (v1.0):
```json
{
  "councilModerator": true
}
```
This enabled BOTH post-analysis AND active interjections (always on).

New behavior (v1.1):
```json
{
  "councilModerator": true,       // Post-analysis
  "councilModeratorActive": false  // No interjections (default)
}
```

**To get v1.0 behavior in v1.1:**
```json
{
  "councilModerator": true,
  "councilModeratorActive": true
}
```

**Migration:** No action required. Existing API calls work unchanged. New toggle defaults to `false` for backwards compatibility.

---

## Troubleshooting

### Moderator Not Interjecting

**Symptoms:** `councilModeratorInterjections: 0` even with `councilModeratorActive: true`

**Possible causes:**
1. Debate is already on track (moderator only interjects when needed)
2. Moderator model unavailable (check logs)
3. Check frequency too high (try lowering to 1 or 2)

**Solution:**
```bash
# Check backend logs
docker-compose logs backend | grep -i moderator

# Try more aggressive check frequency
{
  "councilModeratorCheckFrequency": 1
}
```

### No Post-Debate Analysis

**Symptoms:** `councilModeratorAnalysis: null`

**Possible causes:**
1. `councilModerator: false` (check request)
2. Moderator model unavailable
3. Analysis failed silently (check logs)

**Solution:**
```bash
# Verify moderator enabled
{
  "councilModerator": true
}

# Check logs
docker-compose logs backend | grep -i "moderator analysis"
```

---

## Best Practices

### When to Use Each Mode

**Post-Analysis Only:**
- Strategic decisions
- Learning from debates
- When debate quality isn't critical but insights are

**Active Interjections Only:**
- Simple factual questions
- Time-sensitive situations
- When models tend to over-elaborate

**Full Moderation:**
- High-stakes decisions
- Complex topics with high drift risk
- Production use cases
- When you need both guidance and analysis

**No Moderation:**
- Quick tests
- Benchmarking raw model behavior
- When you want unfiltered responses

### Recommended Settings

**For Production:**
```json
{
  "councilModerator": true,
  "councilModeratorActive": true,
  "councilModeratorCheckFrequency": 2,
  "councilMaxTurns": 8
}
```

**For Development/Testing:**
```json
{
  "councilModerator": false,
  "councilModeratorActive": false,
  "councilMaxTurns": 4
}
```

**For Research:**
```json
{
  "councilModerator": true,
  "councilModeratorActive": false,
  "councilMaxTurns": 10
}
```

---

## Related Documentation

- [Council Debate Mode](./COUNCIL_DEBATE_MODE.md)
- [Moderator Quick Start](./MODERATOR_QUICK_START.md)
- [Active Moderator Implementation](./ACTIVE_MODERATOR_IMPLEMENTATION.md)
- [API Reference](./API_REFERENCE.md)

---

## Changelog

### v1.1.0 (2025-11-08)
- **NEW:** Separate `councilModeratorActive` toggle for active interjections
- **CHANGED:** `councilModerator` now only controls post-debate analysis
- **ADDED:** `councilModeratorInterjections` count in metadata
- **IMPROVED:** Clearer separation of moderator responsibilities
- **FIXED:** Backwards compatibility maintained

### v1.0.0 (2025-11-07)
- Initial moderator implementation
- Post-debate analysis
- Active interjections (always enabled with moderator)
