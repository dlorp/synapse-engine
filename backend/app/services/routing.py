"""Query routing and complexity assessment service.

This module implements the logic for analyzing query complexity
and determining the appropriate model tier for processing.
"""

import logging
from typing import List

from app.core.logging import get_logger
from app.models.config import RoutingConfig
from app.models.query import QueryComplexity


logger = get_logger(__name__)


# Pattern definitions for complexity detection
SIMPLE_PATTERNS: List[str] = [
    "what is",
    "what are",
    "define",
    "definition of",
    "who is",
    "who was",
    "when was",
    "when did",
    "where is",
    "where was",
    "list",
    "name"
]

MODERATE_PATTERNS: List[str] = [
    "explain",
    "describe",
    "compare",
    "summarize",
    "how does",
    "how do",
    "why does",
    "why do",
    "difference between",
    "similarities between",
    "contrast",
    "overview of"
]

COMPLEX_PATTERNS: List[str] = [
    "analyze",
    "evaluate",
    "assess",
    "design",
    "architect",
    "synthesize",
    "critique",
    "propose",
    "develop",
    "formulate",
    "justify",
    "argue",
    "defend",
    "refute"
]


async def assess_complexity(
    query: str,
    config: RoutingConfig
) -> QueryComplexity:
    """Assess query complexity and determine appropriate model tier.

    This function analyzes the query using multiple heuristics:
    1. Token count (length-based complexity)
    2. Pattern matching (keywords indicating complexity level)
    3. Structural analysis (multiple parts, questions, conditionals)
    4. Score calculation and tier mapping

    Args:
        query: User query text to analyze
        config: Routing configuration with tier thresholds

    Returns:
        QueryComplexity with tier selection and reasoning

    Example:
        >>> config = RoutingConfig(complexity_thresholds={'fast': 3.0, 'balanced': 7.0})
        >>> complexity = await assess_complexity("What is Python?", config)
        >>> print(complexity.tier)
        'fast'
        >>> print(complexity.score)
        1.65

    Note:
        This is a heuristic-based approach. Future versions may incorporate
        ML-based complexity prediction for more accurate routing.
    """
    # Normalize query for pattern matching
    query_lower = query.lower()

    # 1. Token counting (simple word-based approximation)
    # More accurate tokenization with tiktoken can be added later
    token_count = len(query.split())

    # 2. Pattern detection
    pattern_type = _detect_pattern_type(query_lower)

    # 3. Structural complexity indicators
    has_multiple_parts = any(
        sep in query_lower
        for sep in [" and ", " then ", " also ", ";", " or ", " but "]
    )
    has_multiple_questions = query.count("?") > 1
    has_conditionals = any(
        word in query_lower
        for word in ["if ", "when ", "assuming", "suppose", "given that"]
    )
    has_reasoning_indicators = any(
        word in query_lower
        for word in ["because", "therefore", "thus", "hence", "consequently"]
    )
    has_enumeration = any(
        word in query_lower
        for word in ["first", "second", "third", "step by step", "stages"]
    )

    # 4. Calculate complexity score
    score = _calculate_score(
        token_count=token_count,
        pattern_type=pattern_type,
        has_multiple_parts=has_multiple_parts,
        has_multiple_questions=has_multiple_questions,
        has_conditionals=has_conditionals,
        has_reasoning_indicators=has_reasoning_indicators,
        has_enumeration=has_enumeration
    )

    # 5. Map score to tier using configured thresholds
    tier = _map_score_to_tier(score, config)

    # 6. Build reasoning explanation
    reasoning = _build_reasoning(
        tier=tier,
        score=score,
        pattern_type=pattern_type,
        token_count=token_count
    )

    # 7. Collect indicators for metadata
    indicators = {
        "token_count": token_count,
        "pattern_type": pattern_type,
        "has_multiple_parts": has_multiple_parts,
        "has_multiple_questions": has_multiple_questions,
        "has_conditionals": has_conditionals,
        "has_reasoning_indicators": has_reasoning_indicators,
        "has_enumeration": has_enumeration
    }

    logger.debug(
        f"Complexity assessment complete: tier={tier}, score={score:.2f}",
        extra={
            "tier": tier,
            "score": score,
            "query_length": len(query),
            "indicators": indicators
        }
    )

    return QueryComplexity(
        tier=tier,
        score=round(score, 2),
        reasoning=reasoning,
        indicators=indicators
    )


def _detect_pattern_type(query_lower: str) -> str:
    """Detect the dominant pattern type in the query.

    Args:
        query_lower: Lowercased query text

    Returns:
        Pattern type: "simple", "moderate", "complex", or "none"
    """
    # Check in order of complexity (highest first)
    for pattern in COMPLEX_PATTERNS:
        if pattern in query_lower:
            return "complex"

    for pattern in MODERATE_PATTERNS:
        if pattern in query_lower:
            return "moderate"

    for pattern in SIMPLE_PATTERNS:
        if pattern in query_lower:
            return "simple"

    return "none"


def _calculate_score(
    token_count: int,
    pattern_type: str,
    has_multiple_parts: bool,
    has_multiple_questions: bool,
    has_conditionals: bool,
    has_reasoning_indicators: bool,
    has_enumeration: bool
) -> float:
    """Calculate numerical complexity score.

    Score calculation uses weighted factors:
    - Base: 0.05 per token
    - Pattern bonuses: simple +0.5, moderate +2.0, complex +5.0
    - Structural bonuses: multiple parts +2.0, questions +1.5, etc.

    Args:
        token_count: Number of tokens in query
        pattern_type: Detected pattern type
        has_multiple_parts: Query has multiple parts
        has_multiple_questions: Query has multiple questions
        has_conditionals: Query has conditional statements
        has_reasoning_indicators: Query has reasoning keywords
        has_enumeration: Query has enumeration/steps

    Returns:
        Complexity score (float)
    """
    # Base score from length
    score = token_count * 0.05

    # Pattern-based scoring
    if pattern_type == "simple":
        score += 0.5
    elif pattern_type == "moderate":
        score += 2.0
    elif pattern_type == "complex":
        score += 5.0
    else:
        # No clear pattern detected - moderate bonus
        score += 1.0

    # Structural complexity bonuses
    if has_multiple_parts:
        score += 2.0
    if has_multiple_questions:
        score += 1.5
    if has_conditionals:
        score += 1.0
    if has_reasoning_indicators:
        score += 1.5
    if has_enumeration:
        score += 1.0

    return score


def _map_score_to_tier(score: float, config: RoutingConfig) -> str:
    """Map complexity score to model tier using configured thresholds.

    Args:
        score: Complexity score
        config: Routing configuration with thresholds

    Returns:
        Tier name: "fast", "balanced", or "powerful"
    """
    thresholds = config.complexity_thresholds

    # Default thresholds if not configured
    fast_threshold = thresholds.get('fast', 3.0)
    balanced_threshold = thresholds.get('balanced', 7.0)

    if score < fast_threshold:
        return "fast"
    elif score < balanced_threshold:
        return "balanced"
    else:
        return "powerful"


def _build_reasoning(
    tier: str,
    score: float,
    pattern_type: str,
    token_count: int
) -> str:
    """Build human-readable reasoning for tier selection.

    Args:
        tier: Selected tier
        score: Complexity score
        pattern_type: Detected pattern type
        token_count: Number of tokens

    Returns:
        Reasoning string
    """
    reasoning_parts = [f"Score: {score:.2f}."]

    # Add tier-specific explanation
    if tier == "fast":
        reasoning_parts.append(
            "Simple query routed to FAST tier (2B-7B models)."
        )
        reasoning_parts.append(
            "Expected response time: <2s."
        )
    elif tier == "balanced":
        reasoning_parts.append(
            "Moderate complexity routed to BALANCED tier (8B-14B models)."
        )
        reasoning_parts.append(
            "Expected response time: <5s."
        )
    else:  # powerful
        reasoning_parts.append(
            "Complex query routed to POWERFUL tier (>14B models)."
        )
        reasoning_parts.append(
            "Expected response time: <15s."
        )

    # Add pattern information if detected
    if pattern_type != "none":
        reasoning_parts.append(
            f"Detected {pattern_type} query pattern."
        )

    # Add length information for long queries
    if token_count > 50:
        reasoning_parts.append(
            f"Query length ({token_count} tokens) indicates detailed analysis needed."
        )

    return " ".join(reasoning_parts)
