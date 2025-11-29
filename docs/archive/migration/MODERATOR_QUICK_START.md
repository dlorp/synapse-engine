# Council Moderator - Quick Start Guide

## What is Council Moderator?

The Council Moderator feature provides AI-powered analysis of debate dialogues in Council Mode. Using sequential thinking (chain-of-thought reasoning), it analyzes:

- **Argument Strength** - Which side made stronger points?
- **Logical Fallacies** - Were there reasoning errors?
- **Rhetorical Techniques** - What persuasion tactics were used?
- **Debate Dynamics** - What were the turning points?
- **Gaps & Questions** - What wasn't addressed?
- **Winner Assessment** - Which side won the debate (if determinable)?

## 5-Minute Setup

### 1. Enable Moderator in Request

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "React vs Vue for enterprise applications?",
    "mode": "council",
    "councilAdversarial": true,
    "councilModerator": true
  }'
```

**Key field:** `"councilModerator": true`

### 2. Review Analysis in Response

```json
{
  "metadata": {
    "councilModeratorAnalysis": "DEBATE ANALYSIS\n\nArgument Strength:\nPRO side...",
    "councilModeratorThinkingSteps": 9,
    "councilModeratorBreakdown": {
      "argument_strength": {...},
      "logical_fallacies": [...],
      "overall_winner": "pro"
    }
  }
}
```

## Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `councilModerator` | boolean | `false` | Enable moderator analysis |
| `councilMaxTurns` | integer | `10` | More turns = richer analysis |
| `councilAdversarial` | boolean | `false` | Must be `true` for debate mode |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `councilModeratorAnalysis` | string | Full analysis text |
| `councilModeratorThinkingSteps` | integer | Number of reasoning steps |
| `councilModeratorBreakdown` | object | Structured insights |

### Breakdown Structure

```typescript
{
  "argument_strength": {
    "pro_strengths": string[],
    "pro_weaknesses": string[],
    "con_strengths": string[],
    "con_weaknesses": string[]
  },
  "logical_fallacies": string[],
  "rhetorical_techniques": string[],
  "key_turning_points": string[],
  "unanswered_questions": string[],
  "overall_winner": "pro" | "con" | "tie" | null
}
```

## Common Use Cases

### 1. Technical Debate Analysis

```bash
{
  "query": "Kubernetes vs Docker Swarm for production?",
  "mode": "council",
  "councilAdversarial": true,
  "councilMaxTurns": 5,
  "councilModerator": true
}
```

**Best for:** Architecture decisions, technology comparisons

### 2. Business Strategy Evaluation

```bash
{
  "query": "Should we pivot to B2B or stay B2C?",
  "mode": "council",
  "councilAdversarial": true,
  "councilMaxTurns": 6,
  "councilModerator": true
}
```

**Best for:** Strategic planning, go-to-market decisions

### 3. Research Question Exploration

```bash
{
  "query": "Is AGI achievable by 2030?",
  "mode": "council",
  "councilAdversarial": true,
  "councilMaxTurns": 8,
  "councilModerator": true
}
```

**Best for:** Exploring controversial topics, research questions

## Tips for Best Results

### Increase Debate Depth

```json
{
  "councilMaxTurns": 8,  // More turns = more material to analyze
  "councilDynamicTermination": false  // Prevent early termination
}
```

### Use Custom Personas

```json
{
  "councilPersonaProfile": "technical",  // Preset personas
  // or
  "councilPersonas": {
    "pro": "Expert software architect with 15 years experience",
    "con": "Pragmatic engineer focused on simplicity"
  }
}
```

### Combine with Context

```json
{
  "useContext": true,  // Add CGRAG context
  "useWebSearch": true,  // Include web results
  "councilModerator": true  // Analyze with full context
}
```

## Performance Expectations

| Metric | Typical Value |
|--------|---------------|
| Analysis Time | 2-5 seconds |
| Thinking Steps | 8-12 steps |
| Debate Length | 4-10 turns recommended |
| Total Processing | +10-20% vs. without moderator |

## Troubleshooting

### "councilModeratorAnalysis is null"

**Cause:** MCP sequential thinking tool unavailable

**Solution:** Check backend logs:
```bash
docker-compose logs backend | grep -i "mcp"
```

### "Analysis seems too brief"

**Cause:** Debate too short (< 4 turns)

**Solution:** Increase `councilMaxTurns`:
```json
{
  "councilMaxTurns": 8,
  "councilDynamicTermination": false
}
```

### "Winner assessment is null"

**Cause:** Debate ended in tie or no clear winner

**Solution:** This is normal for balanced debates. Check `argument_strength` breakdown for details.

## Advanced Usage

### Extract Specific Analysis

```bash
# Get only argument strength
curl http://localhost:8000/api/query -X POST \
  -d '{"query": "...", "councilModerator": true}' \
  | jq '.metadata.councilModeratorBreakdown.argument_strength'

# Get thinking process
curl http://localhost:8000/api/query -X POST \
  -d '{"query": "...", "councilModerator": true}' \
  | jq '.metadata.councilModeratorThinkingSteps'

# Get winner only
curl http://localhost:8000/api/query -X POST \
  -d '{"query": "...", "councilModerator": true}' \
  | jq '.metadata.councilModeratorBreakdown.overall_winner'
```

### Combine with Benchmark Mode

```bash
# Run multiple models, then debate best 2, then analyze
# Step 1: Benchmark
curl -X POST http://localhost:8000/api/query \
  -d '{"query": "...", "mode": "benchmark"}'

# Step 2: Select top 2 models
# Step 3: Run debate with moderator
curl -X POST http://localhost:8000/api/query \
  -d '{
    "query": "...",
    "mode": "council",
    "councilAdversarial": true,
    "councilParticipants": ["model_1", "model_2"],
    "councilModerator": true
  }'
```

## Next Steps

- Read [full documentation](./COUNCIL_MODERATOR_FEATURE.md)
- Explore [Council Debate Mode](./COUNCIL_DEBATE_MODE.md)
- Learn about [MCP Tools](./MCP_TOOLS.md)
- Review [API Reference](./API_REFERENCE.md)

## Example Output

```
DEBATE ANALYSIS

TOPIC: React vs Vue for enterprise applications?

1. ARGUMENT STRENGTH ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRO (React):
✓ Strong ecosystem argument (Turn 1)
✓ Effective corporate backing point (Turn 3)
✗ Weak learning curve claim (Turn 5)

CON (Vue):
✓ Compelling simplicity argument (Turn 2)
✓ Good documentation quality point (Turn 4)
✗ Weak enterprise adoption claim (Turn 6)

2. LOGICAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fallacies detected:
- False dichotomy in Turn 3 (React side)
- Appeal to popularity in Turn 4 (Vue side)

Strong reasoning:
- React's ecosystem evidence was well-supported
- Vue's developer experience claims were specific

3. RHETORICAL TECHNIQUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
React:
- Effective use of industry examples (Google, Facebook)
- Strong framing around "battle-tested"

Vue:
- Good emotional appeal around developer happiness
- Effective simplicity metaphors

4. DEBATE DYNAMICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Key turning points:
- Turn 3: React shifted to ecosystem strength
- Turn 5: Vue recovered with documentation argument

5. UNANSWERED QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Performance benchmarks not discussed
- Migration cost comparison missing
- Long-term support commitments unclear

6. OVERALL ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Winner: PRO (React)

React presented a more evidence-based case with
stronger industry backing and ecosystem maturity
arguments. Vue made compelling points about
developer experience but lacked enterprise adoption
evidence.

Key takeaways:
- Both frameworks viable for enterprise
- React has broader ecosystem support
- Vue offers superior developer experience
- Decision depends on team expertise

Synthesis quality: EXCELLENT
The synthesis captured both perspectives well
and highlighted the key trade-offs accurately.
```
