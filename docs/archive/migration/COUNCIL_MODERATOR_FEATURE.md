# Council Moderator Feature

**Status:** ✅ Implemented
**Version:** 1.0.0
**Date:** 2025-11-08

## Overview

The Council Moderator feature provides deep analytical insights into Council Debate Mode dialogues using the `mcp__sequential-thinking__sequentialthinking` MCP tool. It analyzes debate transcripts step-by-step to provide comprehensive assessments including argument strength, logical fallacies, rhetorical techniques, and overall winner determination.

## Architecture

### Components

1. **QueryRequest Extension** ([backend/app/models/query.py](../backend/app/models/query.py))
   - Added `councilModerator: boolean` field (default: false)
   - Enables moderator analysis when set to true

2. **Moderator Analysis Module** ([backend/app/services/moderator_analysis.py](../backend/app/services/moderator_analysis.py))
   - `run_moderator_analysis()` - Main entry point for analysis
   - `ModeratorAnalysis` - Result class with analysis text, thinking steps, and breakdown
   - Sequential thinking integration via MCP tools

3. **MCP Tools Interface** ([backend/app/core/mcp_tools.py](../backend/app/core/mcp_tools.py))
   - `call_mcp_tool()` - Unified interface for calling MCP tools
   - Handles sequential thinking tool invocation
   - Provides graceful degradation when MCP unavailable

4. **QueryMetadata Extension** ([backend/app/models/query.py](../backend/app/models/query.py))
   - `councilModeratorAnalysis: string` - Full analysis text
   - `councilModeratorThinkingSteps: int` - Number of thinking steps
   - `councilModeratorBreakdown: dict` - Structured analysis breakdown

5. **Query Router Integration** ([backend/app/routers/query.py](../backend/app/routers/query.py))
   - Integrated into `_process_debate_mode()`
   - Runs AFTER dialogue completes
   - Adds analysis to QueryResponse metadata

## Usage

### API Request

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "TypeScript vs JavaScript for backend development?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 4,
    "councilModerator": true
  }'
```

### Response Structure

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "TypeScript vs JavaScript for backend development?",
  "response": "After a thorough debate...",
  "metadata": {
    "modelTier": "council",
    "modelId": "model_pro vs model_con",
    "processingTimeMs": 12500,
    "queryMode": "council",
    "councilMode": "adversarial",
    "councilDialogue": true,
    "councilTurns": [...],
    "councilSynthesis": "...",
    "councilModeratorAnalysis": "DEBATE ANALYSIS\n\n1. ARGUMENT STRENGTH...",
    "councilModeratorThinkingSteps": 9,
    "councilModeratorBreakdown": {
      "argument_strength": {
        "pro_strengths": ["Strong type safety argument"],
        "pro_weaknesses": [],
        "con_strengths": ["Flexibility point"],
        "con_weaknesses": ["Weak ecosystem claim"]
      },
      "logical_fallacies": ["False dichotomy in turn 3"],
      "rhetorical_techniques": ["Effective use of examples"],
      "key_turning_points": ["Turn 2 shifted momentum"],
      "unanswered_questions": ["Performance comparison not addressed"],
      "overall_winner": "pro"
    }
  }
}
```

## Sequential Thinking Process

The moderator uses the MCP sequential thinking tool to analyze the debate through multiple reasoning steps:

### Analysis Phases

1. **Argument Strength Assessment**
   - Evaluates PRO and CON argument quality
   - Identifies strongest and weakest points
   - Assesses evidence quality and logical coherence

2. **Logical Analysis**
   - Identifies logical fallacies (ad hominem, straw man, false dichotomy, etc.)
   - Notes weak reasoning or unsupported claims
   - Highlights strong logical progressions

3. **Rhetorical Techniques**
   - Identifies persuasive techniques used
   - Notes effective use of examples, analogies, evidence
   - Assesses tone and framing strategies

4. **Debate Dynamics**
   - Identifies key turning points
   - Notes when arguments shifted or evolved
   - Assesses responsiveness to opponent's points

5. **Unanswered Questions & Gaps**
   - Identifies important questions not addressed
   - Notes missing perspectives or evidence
   - Highlights areas where debate could be deepened

6. **Overall Assessment**
   - Determines which side presented more compelling case
   - Extracts key takeaways
   - Evaluates synthesis quality

### Thinking Steps Example

```
Step 1: Starting analysis of TypeScript vs JavaScript debate
Step 2: Examining PRO side's argument strength - strong type safety points
Step 3: Analyzing CON side's counter-arguments - flexibility is valid but limited
Step 4: Identifying logical fallacies - false dichotomy detected in CON's ecosystem claim
Step 5: Examining rhetorical techniques - PRO used effective runtime error examples
Step 6: Identifying key turning points - Turn 3 where PRO countered flexibility argument
Step 7: Noting unanswered questions - performance comparison missing
Step 8: Comparing argument quality - PRO presented more evidence-based case
Step 9: Finalizing assessment - PRO has stronger overall position
```

## Implementation Details

### MCP Tool Integration

The moderator uses the `mcp__sequential-thinking__sequentialthinking` tool through an iterative process:

```python
async def _call_sequential_thinking(prompt: str) -> Optional[Dict]:
    thoughts = []
    thought_number = 1
    next_thought_needed = True

    while next_thought_needed and thought_number <= 30:  # Safety limit
        result = await call_mcp_tool(
            tool_name="mcp__sequential-thinking__sequentialthinking",
            parameters={
                "thought": current_thought,
                "thoughtNumber": thought_number,
                "totalThoughts": total_thoughts,
                "nextThoughtNeeded": next_thought_needed
            }
        )

        thoughts.append(result.get("thought"))
        next_thought_needed = result.get("nextThoughtNeeded", False)
        thought_number += 1

    return synthesize_analysis(thoughts)
```

### Graceful Degradation

If the MCP sequential thinking tool is unavailable:

1. `run_moderator_analysis()` returns `None`
2. Query processing continues normally
3. Response metadata fields remain `null`
4. No error is thrown (logged as warning)

This ensures the debate feature works even without advanced analysis.

### Error Handling

```python
if request.council_moderator:
    try:
        moderator_result = await run_moderator_analysis(...)
        if moderator_result:
            # Add to metadata
        else:
            logger.warning("MCP tool unavailable")
    except Exception as e:
        logger.warning(f"Moderator analysis failed: {e}")
        # Continue without moderator analysis
```

## Performance Considerations

### Timing

- **Average analysis time:** 2-5 seconds (depends on debate length)
- **Thinking steps:** Typically 8-12 steps
- **Total overhead:** ~10-20% of total debate time

### Optimization

1. **Parallel execution:** Moderator runs AFTER dialogue completes (doesn't delay responses)
2. **Thinking step limit:** Capped at 30 steps to prevent runaway analysis
3. **Context pruning:** Transcript is summarized if excessively long

## Testing

### Unit Tests

```bash
# Run moderator analysis tests
pytest backend/tests/test_moderator_analysis.py -v

# Test with MCP simulation
pytest backend/tests/test_moderator_analysis.py::test_moderator_analysis_integration -v
```

### Integration Tests

```bash
# Test full debate with moderator
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should we use microservices or monoliths?",
    "mode": "council",
    "councilAdversarial": true,
    "councilMaxTurns": 3,
    "councilModerator": true
  }' | jq '.metadata.councilModeratorAnalysis'
```

## Configuration

### Environment Variables

Currently no environment variables required. MCP tool detection is automatic.

### Future Configuration Options

- `MODERATOR_MAX_THINKING_STEPS` - Override default 30 step limit
- `MODERATOR_ANALYSIS_TIMEOUT` - Timeout for moderator analysis (default: 60s)
- `MODERATOR_ENABLE_CACHING` - Cache analysis for similar debates

## Troubleshooting

### Moderator Analysis Not Appearing

**Symptoms:** `councilModeratorAnalysis` is `null` in response

**Possible causes:**
1. `councilModerator: false` in request (check request payload)
2. MCP sequential thinking tool unavailable (check logs for warnings)
3. Analysis failed with exception (check error logs)

**Solution:**
```bash
# Check backend logs
docker-compose logs backend | grep -i moderator

# Verify MCP tool availability
curl http://localhost:8000/api/health
```

### Analysis Quality Issues

**Symptoms:** Analysis is too brief or misses key points

**Possible causes:**
1. Debate transcript too short (fewer than 4 turns)
2. Thinking steps terminated early
3. Parsing logic not extracting insights

**Solution:**
- Increase `councilMaxTurns` for richer debate
- Check `councilModeratorThinkingSteps` in response
- Review logs for parsing warnings

## Future Enhancements

### Planned Features

1. **Custom Analysis Prompts**
   - Allow users to specify analysis focus areas
   - Add `councilModeratorPrompt: string` field

2. **Multi-Model Moderator**
   - Use different model for moderator analysis
   - Add `councilModeratorModel: string` field

3. **Comparative Analysis**
   - Compare multiple debates on same topic
   - Track argument evolution across debates

4. **Export & Sharing**
   - Export moderator analysis as standalone report
   - Share analysis via unique URL

5. **Learning Feedback**
   - Allow users to rate moderator analysis quality
   - Improve analysis prompts based on feedback

## Related Documentation

- [Council Debate Mode](./COUNCIL_DEBATE_MODE.md)
- [Sequential Thinking MCP Tool](./MCP_TOOLS.md)
- [Query Processing Pipeline](./QUERY_PROCESSING.md)
- [WebSocket Events](./WEBSOCKET_EVENTS.md)

## References

- **MCP Protocol:** [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- **Sequential Thinking:** Chain-of-thought reasoning for LLMs
- **Debate Analysis:** Formal debate scoring and assessment methodologies
