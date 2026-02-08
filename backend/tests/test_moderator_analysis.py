"""Tests for moderator analysis functionality.

This module tests the moderator analysis feature for Council Debate Mode,
which uses sequential thinking to provide deep analytical insights.
"""

from datetime import datetime

import pytest

from app.services.dialogue_engine import DialogueTurn
from app.services.moderator_analysis import (
    ModeratorAnalysis,
    _build_transcript,
    _parse_moderator_analysis,
)


@pytest.fixture
def sample_dialogue_turns():
    """Create sample dialogue turns for testing."""
    turns = [
        DialogueTurn(
            turn_number=1,
            speaker_id="model_pro",
            persona="Pro advocate",
            content="TypeScript provides static typing which catches errors at compile time.",
            timestamp=datetime.now(),
            tokens_used=15,
        ),
        DialogueTurn(
            turn_number=2,
            speaker_id="model_con",
            persona="Con advocate",
            content="JavaScript is more flexible and doesn't require type annotations.",
            timestamp=datetime.now(),
            tokens_used=12,
        ),
        DialogueTurn(
            turn_number=3,
            speaker_id="model_pro",
            persona="Pro advocate",
            content="That flexibility leads to runtime errors that TypeScript prevents.",
            timestamp=datetime.now(),
            tokens_used=13,
        ),
        DialogueTurn(
            turn_number=4,
            speaker_id="model_con",
            persona="Con advocate",
            content="The JavaScript ecosystem is larger and more mature than TypeScript.",
            timestamp=datetime.now(),
            tokens_used=14,
        ),
    ]
    return turns


def test_build_transcript(sample_dialogue_turns):
    """Test transcript building from dialogue turns."""
    transcript = _build_transcript(sample_dialogue_turns)

    # Check that all turns are present
    assert "Turn 1" in transcript
    assert "Turn 2" in transcript
    assert "Turn 3" in transcript
    assert "Turn 4" in transcript

    # Check PRO/CON labels
    assert "PRO" in transcript
    assert "CON" in transcript

    # Check content is preserved
    assert "static typing" in transcript
    assert "more flexible" in transcript


def test_parse_analysis():
    """Test parsing of analysis thoughts into structured breakdown."""
    # Create analysis text string (function expects string, not list)
    analysis_text = """
The PRO side presented strong arguments about type safety.
The CON side had a weak argument about ecosystem size.
I detected a fallacy in the CON argument about flexibility.
The PRO side used effective rhetoric about runtime errors.
Overall, the PRO side presented the stronger case.
    """

    breakdown = _parse_moderator_analysis(analysis_text)

    # Check structure
    assert "argument_strength" in breakdown
    assert "logical_fallacies" in breakdown
    assert "rhetorical_techniques" in breakdown
    assert "overall_winner" in breakdown

    # Check extracted insights
    assert len(breakdown["argument_strength"]["pro_strengths"]) > 0
    assert len(breakdown["argument_strength"]["con_weaknesses"]) > 0
    assert len(breakdown["logical_fallacies"]) > 0
    assert len(breakdown["rhetorical_techniques"]) > 0
    assert breakdown["overall_winner"] == "pro"


@pytest.mark.asyncio
async def test_moderator_analysis_integration(sample_dialogue_turns):
    """Test full moderator analysis with sample debate."""
    pytest.skip("Requires model_caller dependency - test skipped for unit testing")

    # This test would require a real model_caller function which is a complex dependency
    # Integration testing should be done in a separate test suite with mocked model responses


def test_moderator_analysis_to_dict():
    """Test serialization of ModeratorAnalysis to dict."""
    analysis = ModeratorAnalysis(
        analysis="Comprehensive analysis text here",
        moderator_model="test-model",
        tokens_used=150,
        breakdown={
            "argument_strength": {"pro_strengths": ["Point 1"], "con_strengths": []},
            "logical_fallacies": ["Fallacy 1"],
            "overall_winner": "pro",
        },
    )

    result = analysis.to_dict()

    assert result["analysis"] == "Comprehensive analysis text here"
    assert result["moderator_model"] == "test-model"
    assert result["tokens_used"] == 150
    assert "argument_strength" in result["breakdown"]
    assert result["breakdown"]["overall_winner"] == "pro"
