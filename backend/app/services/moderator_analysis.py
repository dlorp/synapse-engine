"""Moderator analysis for Council Debate Mode using LLM models.

This module provides deep analytical insights into debate dialogues using actual
LLM models for comprehensive analysis, rather than the MCP sequential thinking tool.
"""

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Type alias for model caller function
# Takes model_id, prompt, and optionally max_tokens/temperature
ModelCallerFunc = Callable[..., Awaitable[Dict]]


class ModeratorAnalysis:
    """Result of moderator analysis."""

    def __init__(self, analysis: str, moderator_model: str, tokens_used: int, breakdown: Dict):
        self.analysis = analysis
        self.moderator_model = moderator_model
        self.tokens_used = tokens_used
        self.breakdown = breakdown

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "analysis": self.analysis,
            "moderator_model": self.moderator_model,
            "tokens_used": self.tokens_used,
            "breakdown": self.breakdown,
        }


async def check_for_interjection(
    dialogue_turns: List,  # List[DialogueTurn]
    query: str,
    model_caller: ModelCallerFunc,
    moderator_model: str,
) -> Optional[str]:
    """
    Check if moderator should interject to redirect debate.

    This function analyzes recent dialogue turns to determine if the debate
    is staying on topic and answering the original question. If intervention
    is needed, it returns a guidance message from the moderator.

    Args:
        dialogue_turns: List of DialogueTurn objects (recent turns)
        query: Original debate topic/question
        model_caller: Async function to call LLM models
        moderator_model: Model ID to use for moderator decision

    Returns:
        String with moderator's guidance message if interjection needed, None otherwise

    Example:
        >>> guidance = await check_for_interjection(recent_turns, query, caller, "model_id")
        >>> if guidance:
        ...     # Add moderator turn with guidance message
        ...     pass
    """
    try:
        # Build transcript from recent turns
        transcript = _build_transcript(dialogue_turns)

        # Build interjection check prompt
        prompt = f"""You are moderating a debate on: {query}

RECENT TURNS:
{transcript}

Analyze the last few turns and determine:
1. Are the debaters answering the original question?
2. Are they staying on topic and focused?
3. Is the debate productive or repetitive?

Response format:
- If debate is on track: "CONTINUE"
- If intervention needed: "INTERJECT: [Your guidance message to redirect the debate]"

Be brief and direct. Only interject if genuinely needed to refocus the debate on the original question.

Your decision:"""

        logger.debug(f"Checking for moderator interjection using model {moderator_model}")

        # Call moderator model
        response = await model_caller(
            moderator_model,
            prompt,
            max_tokens=300,  # Brief interjection message
            temperature=0.3,  # Lower temperature for consistent moderation
        )

        response_text = response.get("content", "").strip()

        # Parse response
        if response_text.startswith("CONTINUE"):
            logger.debug("Moderator check: Debate is on track")
            return None
        elif "INTERJECT:" in response_text:
            # Extract guidance message
            guidance = response_text.split("INTERJECT:", 1)[1].strip()
            logger.info(f"Moderator interjection needed: {guidance[:100]}...")
            return guidance
        else:
            # Ambiguous response, default to not interjecting
            logger.warning(f"Moderator gave ambiguous response: {response_text[:100]}")
            return None

    except Exception as e:
        logger.error(f"Error checking for moderator interjection: {e}", exc_info=True)
        # Graceful degradation - don't interject on error
        return None


async def run_moderator_analysis(
    dialogue_turns: List,  # List[DialogueTurn]
    query: str,
    synthesis: str,
    model_caller: ModelCallerFunc,
    model_selector=None,  # ModelSelector instance for auto-selection
    model_id: Optional[str] = None,
) -> Optional[ModeratorAnalysis]:
    """
    Use LLM model to analyze debate comprehensively.

    This function uses an actual LLM model to perform deep analysis of the debate
    transcript, providing structured insights into argument quality, logical fallacies,
    rhetorical techniques, and overall assessment.

    Args:
        dialogue_turns: List of DialogueTurn objects from the debate
        query: Original debate topic
        synthesis: Final synthesis from the debate
        model_caller: Async function to call LLM models
        model_selector: ModelSelector instance for auto-selecting moderator model
        model_id: Optional specific model ID for moderator (auto-selects if None)

    Returns:
        ModeratorAnalysis object with comprehensive analysis, or None if failed

    Raises:
        Exception: If model call fails critically (errors are logged and None returned for graceful degradation)
    """
    try:
        # Auto-select moderator model if not specified
        if model_id is None:
            if model_selector is None:
                raise ValueError("model_selector must be provided when model_id is None")

            moderator_model = _auto_select_moderator_model(model_selector)
            logger.info(f"Auto-selected moderator model: {moderator_model}")
        else:
            moderator_model = model_id
            logger.info(f"Using specified moderator model: {moderator_model}")

        # Build transcript from dialogue turns
        transcript = _build_transcript(dialogue_turns)

        # Build analysis prompt
        analysis_prompt = _build_analysis_prompt(query, transcript, synthesis)

        logger.info(f"Starting moderator analysis with model {moderator_model}")

        # Call the model for analysis
        try:
            response = await model_caller(
                moderator_model,
                analysis_prompt,
                max_tokens=2000,  # Moderator needs space for detailed analysis
                temperature=0.3,  # Lower temperature for more analytical response
            )

            analysis_text = response.get("content", "")
            tokens_used = response.get("usage", {}).get("total_tokens", 0)

            logger.info(
                f"Moderator analysis completed using {moderator_model}: {tokens_used} tokens",
                extra={"moderator_model": moderator_model, "tokens_used": tokens_used},
            )

        except Exception as e:
            logger.error(f"Error calling moderator model {moderator_model}: {e}", exc_info=True)
            raise

        # Parse the analysis into structured breakdown
        breakdown = _parse_moderator_analysis(analysis_text)

        return ModeratorAnalysis(
            analysis=analysis_text,
            moderator_model=moderator_model,
            tokens_used=tokens_used,
            breakdown=breakdown,
        )

    except Exception as e:
        logger.error(f"Moderator analysis failed: {e}", exc_info=True)
        # Graceful degradation - return None instead of crashing
        return None


def _auto_select_moderator_model(model_selector) -> str:
    """Auto-select the best model for moderator analysis.

    Prefers models in this order:
    1. POWERFUL tier (best analytical capabilities)
    2. BALANCED tier
    3. FAST tier (fallback)

    Note: Selects from ENABLED models, not necessarily running ones.
    The actual model call will validate the server is running.

    Args:
        model_selector: ModelSelector instance

    Returns:
        Model ID string

    Raises:
        ValueError: If no models available
    """
    # Get all enabled models from registry (don't check if server is running yet)
    all_models = model_selector.registry.models.values()
    enabled = [m for m in all_models if m.enabled]

    if not enabled:
        raise ValueError("No enabled models available for moderator analysis")

    # Group by tier
    powerful = [m for m in enabled if m.get_effective_tier() == "powerful"]
    balanced = [m for m in enabled if m.get_effective_tier() == "balanced"]
    fast = [m for m in enabled if m.get_effective_tier() == "fast"]

    # Select from most powerful tier available
    if powerful:
        selected = powerful[0].model_id
        logger.info(f"Selected POWERFUL tier model for moderator: {selected}")
        return selected
    elif balanced:
        selected = balanced[0].model_id
        logger.info(f"Selected BALANCED tier model for moderator: {selected}")
        return selected
    elif fast:
        selected = fast[0].model_id
        logger.info(
            f"Selected FAST tier model for moderator (no powerful/balanced available): {selected}"
        )
        return selected
    else:
        raise ValueError("No enabled models available for moderator analysis")


def _build_transcript(dialogue_turns: List) -> str:
    """Build formatted transcript from dialogue turns.

    Args:
        dialogue_turns: List of DialogueTurn objects

    Returns:
        Formatted transcript string
    """
    transcript_lines = []

    for turn in dialogue_turns:
        # Determine position based on turn number (odd = PRO, even = CON)
        position = "PRO" if turn.turn_number % 2 == 1 else "CON"
        transcript_lines.append(
            f"[Turn {turn.turn_number}] {position} ({turn.speaker_id}):\n{turn.content}"
        )

    return "\n\n".join(transcript_lines)


def _build_analysis_prompt(query: str, transcript: str, synthesis: str) -> str:
    """Build comprehensive analysis prompt for LLM moderator.

    Args:
        query: Original debate topic
        transcript: Full debate transcript
        synthesis: Final synthesis

    Returns:
        Formatted prompt for LLM model
    """
    return f"""You are an expert debate moderator analyzing this debate.

DEBATE TOPIC: {query}

FULL TRANSCRIPT:
{transcript}

SYNTHESIS:
{synthesis}

Please provide a comprehensive moderator analysis with the following sections:

1. ARGUMENT STRENGTH
   - PRO position strengths
   - PRO position weaknesses
   - CON position strengths
   - CON position weaknesses

2. LOGICAL FALLACIES & REASONING QUALITY
   - Identify any logical fallacies used by either side
   - Evaluate quality of evidence and reasoning

3. RHETORICAL TECHNIQUES
   - Effective rhetorical devices used
   - Persuasive techniques employed

4. DEBATE DYNAMICS
   - Key turning points in the debate
   - How arguments evolved over turns
   - Momentum shifts

5. GAPS & UNANSWERED QUESTIONS
   - Important points not addressed
   - Missing perspectives or evidence

6. OVERALL ASSESSMENT
   - Which side presented the stronger case?
   - Why did they win (or was it a tie)?
   - Final verdict

Provide detailed, objective analysis using specific examples from the transcript."""


def _parse_moderator_analysis(analysis_text: str) -> Dict:
    """Parse moderator analysis into structured breakdown.

    Extracts key insights from the analysis text and organizes them into categories.

    Args:
        analysis_text: Raw analysis text from LLM

    Returns:
        Structured breakdown dictionary
    """
    breakdown: Dict[str, Any] = {
        "argument_strength": {
            "pro_strengths": [],
            "pro_weaknesses": [],
            "con_strengths": [],
            "con_weaknesses": [],
        },
        "logical_fallacies": [],
        "rhetorical_techniques": [],
        "key_turning_points": [],
        "unanswered_questions": [],
        "overall_winner": None,  # "pro", "con", or "tie"
    }

    # Simple keyword-based extraction
    # In production, this could use more sophisticated NLP
    lines = analysis_text.lower().split("\n")

    # Type-safe access to nested structures
    arg_strength: Dict[str, List[str]] = breakdown["argument_strength"]  # type: ignore[assignment]
    logical_fallacies: List[str] = breakdown["logical_fallacies"]  # type: ignore[assignment]
    rhetorical_techniques: List[str] = breakdown["rhetorical_techniques"]  # type: ignore[assignment]
    key_turning_points: List[str] = breakdown["key_turning_points"]  # type: ignore[assignment]
    unanswered_questions: List[str] = breakdown["unanswered_questions"]  # type: ignore[assignment]

    for line in lines:
        # Extract argument strengths/weaknesses
        if "pro" in line and ("strong" in line or "effective" in line or "strength" in line):
            arg_strength["pro_strengths"].append(line.strip()[:200])
        if "pro" in line and ("weak" in line or "fallacy" in line or "flaw" in line):
            arg_strength["pro_weaknesses"].append(line.strip()[:200])
        if "con" in line and ("strong" in line or "effective" in line or "strength" in line):
            arg_strength["con_strengths"].append(line.strip()[:200])
        if "con" in line and ("weak" in line or "fallacy" in line or "flaw" in line):
            arg_strength["con_weaknesses"].append(line.strip()[:200])

        # Extract fallacies
        if "fallacy" in line or "logical error" in line or "invalid reasoning" in line:
            logical_fallacies.append(line.strip()[:200])

        # Extract rhetorical techniques
        if "rhetoric" in line or "persuasion" in line or "technique" in line:
            rhetorical_techniques.append(line.strip()[:200])

        # Extract turning points
        if "turning point" in line or "shift" in line or "momentum" in line:
            key_turning_points.append(line.strip()[:200])

        # Extract unanswered questions
        if "unanswered" in line or "gap" in line or "missing" in line or "not addressed" in line:
            unanswered_questions.append(line.strip()[:200])

    # Determine overall winner based on final assessment
    analysis_lower = analysis_text.lower()
    if "pro" in analysis_lower and (
        "stronger" in analysis_lower or "winner" in analysis_lower or "wins" in analysis_lower
    ):
        # Check context to avoid false positives
        if "con" not in analysis_lower.split("pro")[0]:  # PRO mentioned first as winner
            breakdown["overall_winner"] = "pro"
    elif "con" in analysis_lower and (
        "stronger" in analysis_lower or "winner" in analysis_lower or "wins" in analysis_lower
    ):
        breakdown["overall_winner"] = "con"
    elif "tie" in analysis_lower or "balanced" in analysis_lower or "even" in analysis_lower:
        breakdown["overall_winner"] = "tie"

    return breakdown
