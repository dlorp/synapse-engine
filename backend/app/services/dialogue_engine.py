"""Sequential multi-model dialogue engine for true multi-chat."""

import logging
from typing import List, Dict, Optional, TYPE_CHECKING, Callable, Awaitable
from datetime import datetime

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Type alias for model calling function
ModelCallerFunc = Callable[[str, str, int, float], Awaitable[dict]]


class DialogueTurn:
    """Represents a single turn in dialogue."""

    def __init__(
        self,
        turn_number: int,
        speaker_id: str,
        persona: str,
        content: str,
        timestamp: datetime,
        tokens_used: int,
    ):
        self.turn_number = turn_number
        self.speaker_id = speaker_id
        self.persona = persona
        self.content = content
        self.timestamp = timestamp
        self.tokens_used = tokens_used

    def to_dict(self) -> dict:
        return {
            "turnNumber": self.turn_number,
            "speakerId": self.speaker_id,
            "persona": self.persona,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tokensUsed": self.tokens_used,
        }


class DialogueResult:
    """Result of a complete dialogue session."""

    def __init__(
        self,
        turns: List[DialogueTurn],
        synthesis: str,
        termination_reason: str,
        total_tokens: int,
        total_time_ms: int,
        moderator_interjection_count: int = 0,
    ):
        self.turns = turns
        self.synthesis = synthesis
        self.termination_reason = termination_reason
        self.total_tokens = total_tokens
        self.total_time_ms = total_time_ms
        self.moderator_interjection_count = moderator_interjection_count

    def to_dict(self) -> dict:
        return {
            "turns": [turn.to_dict() for turn in self.turns],
            "synthesis": self.synthesis,
            "terminationReason": self.termination_reason,
            "totalTokens": self.total_tokens,
            "totalTimeMs": self.total_time_ms,
            "moderatorInterjectionCount": self.moderator_interjection_count,
        }


class DialogueEngine:
    """Manages sequential multi-model dialogue."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def run_debate_dialogue(
        self,
        model_caller: ModelCallerFunc,
        participants: List[str],  # [model_pro_id, model_con_id]
        query: str,
        personas: Dict[str, str],  # {model_id: persona_description}
        context: Optional[str] = None,
        max_turns: int = 10,
        dynamic_termination: bool = True,
        temperature: float = 0.7,
        max_tokens_per_turn: int = 400,
        enable_active_moderator: bool = False,
        moderator_check_frequency: int = 2,
        moderator_model: Optional[str] = None,
        max_moderator_interjections: int = 3,
    ) -> DialogueResult:
        """
        Execute sequential debate dialogue between two models.

        Args:
            model_caller: Async function to call models with signature:
                (model_id: str, prompt: str, max_tokens: int, temperature: float) -> dict
                The returned dict must have 'content' key with response text
            participants: List of 2 model IDs [pro, con]
            query: Original query/debate topic
            personas: Persona descriptions for each model
            context: Optional CGRAG context
            max_turns: Maximum number of dialogue turns
            dynamic_termination: End early if stalemate/concession detected
            temperature: Model temperature
            max_tokens_per_turn: Max tokens per response
            enable_active_moderator: Enable moderator interjections during debate
            moderator_check_frequency: Check moderator every N turns (default: 2)
            moderator_model: Model ID for moderator (required if enable_active_moderator=True)
            max_moderator_interjections: Maximum number of moderator interjections (default: 3)

        Returns:
            DialogueResult with full conversation history and synthesis.
            The result includes a count of moderator interjections in the interjection_count attribute.
        """
        if len(participants) != 2:
            raise ValueError("Debate mode requires exactly 2 participants")

        start_time = datetime.now()
        conversation_history: List[DialogueTurn] = []
        total_tokens = 0
        moderator_interjection_count = 0

        self.logger.info(
            f"Starting debate dialogue: {len(participants)} participants, max {max_turns} turns"
        )

        if enable_active_moderator:
            if not moderator_model:
                self.logger.warning(
                    "Active moderator enabled but no moderator_model provided - disabling"
                )
                enable_active_moderator = False
            else:
                self.logger.info(
                    f"Active moderator enabled: check every {moderator_check_frequency} turns, max {max_moderator_interjections} interjections"
                )

        # Main dialogue loop
        for turn_num in range(max_turns):
            # Alternate between PRO (0) and CON (1)
            speaker_idx = turn_num % 2
            speaker_id = participants[speaker_idx]
            speaker_persona = personas[speaker_id]

            # Build dialogue prompt
            prompt = self._build_debate_prompt(
                query=query,
                speaker_id=speaker_id,
                speaker_persona=speaker_persona,
                conversation_history=conversation_history,
                context=context,
                turn_number=turn_num + 1,
            )

            # Call model using provided model_caller function
            self.logger.debug(f"Turn {turn_num + 1}: {speaker_id} speaking")
            turn_start = datetime.now()

            try:
                response = await model_caller(
                    model_id=speaker_id,
                    prompt=prompt,
                    max_tokens=max_tokens_per_turn,
                    temperature=temperature,
                )
            except Exception as e:
                self.logger.error(f"Error calling model {speaker_id}: {e}")
                # Continue with error message as content
                response = {
                    "content": f"[Error: Model {speaker_id} failed to respond]",
                    "usage": {"total_tokens": 0},
                }

            turn_end = datetime.now()

            # Extract response content and tokens
            content = response.get("content", "").strip()
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            total_tokens += tokens_used

            # Create turn record
            turn = DialogueTurn(
                turn_number=turn_num + 1,
                speaker_id=speaker_id,
                persona=speaker_persona,
                content=content,
                timestamp=turn_start,
                tokens_used=tokens_used,
            )

            conversation_history.append(turn)

            self.logger.debug(
                f"Turn {turn_num + 1} completed in {(turn_end - turn_start).total_seconds():.2f}s"
            )

            # Check for active moderator interjection
            if (
                enable_active_moderator
                and moderator_interjection_count < max_moderator_interjections
                and len(conversation_history) >= moderator_check_frequency
                and len(conversation_history) % moderator_check_frequency == 0
            ):
                self.logger.info(f"🎓 Moderator check at turn {turn_num + 1}")

                # Get recent turns for moderator review (last moderator_check_frequency * 2 turns)
                recent_turn_count = min(
                    moderator_check_frequency * 2, len(conversation_history)
                )
                recent_turns = conversation_history[-recent_turn_count:]

                # Check if moderator wants to interject
                moderator_guidance = await self._check_moderator_interjection(
                    model_caller=model_caller,
                    query=query,
                    recent_turns=recent_turns,
                    moderator_model=moderator_model,
                )

                if moderator_guidance:
                    # Moderator is interjecting - add moderator turn
                    moderator_interjection_count += 1
                    moderator_turn_num = len(conversation_history) + 1

                    self.logger.info(
                        f"🎓 Moderator interjecting (#{moderator_interjection_count}): {moderator_guidance[:100]}..."
                    )

                    moderator_turn = DialogueTurn(
                        turn_number=moderator_turn_num,
                        speaker_id="MODERATOR",
                        persona="Neutral debate moderator",
                        content=moderator_guidance,
                        timestamp=datetime.now(),
                        tokens_used=0,  # Moderator interjection doesn't count toward token usage
                    )

                    conversation_history.append(moderator_turn)

            # Check for dynamic termination
            if dynamic_termination and len(conversation_history) >= 4:
                termination_reason = self._check_termination(conversation_history)
                if termination_reason:
                    self.logger.info(f"Debate terminated early: {termination_reason}")
                    break
        else:
            # Loop completed without early termination
            termination_reason = "max_turns_reached"

        # Synthesize final summary
        synthesis = await self._synthesize_debate(
            model_caller=model_caller,
            conversation_history=conversation_history,
            query=query,
            participants=participants,
            temperature=temperature,
        )

        end_time = datetime.now()
        total_time_ms = int((end_time - start_time).total_seconds() * 1000)

        self.logger.info(
            f"Debate completed: {len(conversation_history)} turns, {total_time_ms}ms, {total_tokens} tokens, {moderator_interjection_count} moderator interjections"
        )

        return DialogueResult(
            turns=conversation_history,
            synthesis=synthesis,
            termination_reason=termination_reason,
            total_tokens=total_tokens,
            total_time_ms=total_time_ms,
            moderator_interjection_count=moderator_interjection_count,
        )

    def _build_debate_prompt(
        self,
        query: str,
        speaker_id: str,
        speaker_persona: str,
        conversation_history: List[DialogueTurn],
        context: Optional[str],
        turn_number: int,
    ) -> str:
        """Build prompt for next speaker in debate dialogue."""

        # Determine position (PRO or CON)
        position = "PRO" if turn_number % 2 == 1 else "CON"
        opponent_position = "CON" if position == "PRO" else "PRO"

        # Build conversation transcript
        if conversation_history:
            transcript = "\n\n".join(
                [
                    f"[Turn {turn.turn_number}] {self._get_position_for_turn(turn.turn_number)}: {turn.content}"
                    for turn in conversation_history
                ]
            )
            transcript_section = f"""
Conversation so far:
{transcript}
"""
        else:
            transcript_section = "(No messages yet — you're opening the debate)"

        # Context section
        context_section = f"\n\nRelevant Context:\n{context}" if context else ""

        # Build full prompt
        prompt = f"""You are debating the following topic. Your role is to argue {position} (in favor of) the position.

Debate Topic: {query}

Your Persona: You are {speaker_persona}
Opponent Persona: {opponent_position} perspective{context_section}

{transcript_section}

Instructions for Turn {turn_number}:
- Build on the conversation by directly addressing your opponent's most recent points
- Reference specific arguments made by the {opponent_position} side (e.g., "You claim that...")
- Provide counter-evidence, identify logical flaws, or strengthen your position
- Maintain your {position} stance while engaging substantively with opposition
- Be specific and evidence-based in your rebuttals
- Acknowledge valid points when appropriate, but defend your overall position

Your Turn {turn_number} ({position} response):"""

        return prompt

    def _get_position_for_turn(self, turn_number: int) -> str:
        """Get position (PRO/CON) for a given turn number."""
        return "PRO" if turn_number % 2 == 1 else "CON"

    async def _check_moderator_interjection(
        self,
        model_caller: ModelCallerFunc,
        query: str,
        recent_turns: List[DialogueTurn],
        moderator_model: str,
    ) -> Optional[str]:
        """
        Check if moderator should interject to redirect debate.

        Args:
            model_caller: Function to call LLM models
            query: Original debate topic
            recent_turns: Recent dialogue turns to review
            moderator_model: Model ID for moderator

        Returns:
            Moderator's guidance message if interjection needed, None otherwise
        """
        try:
            from app.services.moderator_analysis import check_for_interjection

            guidance = await check_for_interjection(
                dialogue_turns=recent_turns,
                query=query,
                model_caller=model_caller,
                moderator_model=moderator_model,
            )

            return guidance

        except Exception as e:
            self.logger.error(
                f"Error checking moderator interjection: {e}", exc_info=True
            )
            return None

    def _check_termination(self, history: List[DialogueTurn]) -> Optional[str]:
        """
        Check if debate should terminate early.

        Returns:
            Termination reason string if should terminate, None otherwise
        """
        if len(history) < 4:
            return None

        # Get recent turns (last 4)
        recent_turns = history[-4:]

        # Check for concession keywords
        concession_keywords = [
            "you're right",
            "i agree",
            "fair point",
            "i concede",
            "you've convinced me",
            "i accept your argument",
            "you make a valid point",
        ]

        last_response = recent_turns[-1].content.lower()
        if any(keyword in last_response for keyword in concession_keywords):
            return "concession_detected"

        # Check for stalemate (repetitive arguments)
        if self._detect_repetition(recent_turns):
            return "stalemate_repetition"

        # Check for very short responses (potential disengagement)
        if len(last_response.split()) < 20:
            # Check if last 2 responses are both very short
            if len(recent_turns) >= 2:
                second_last = recent_turns[-2].content
                if len(second_last.split()) < 20:
                    return "stalemate_disengagement"

        return None

    def _detect_repetition(self, recent_turns: List[DialogueTurn]) -> bool:
        """
        Detect if arguments are becoming repetitive.

        Simple heuristic: Check if recent responses share >60% of keywords.
        """
        if len(recent_turns) < 4:
            return False

        # Extract keywords from each turn (simple: words > 4 chars)
        def extract_keywords(text: str) -> set:
            words = text.lower().split()
            return {word for word in words if len(word) > 4}

        turn_keywords = [extract_keywords(turn.content) for turn in recent_turns]

        # Check overlap between turns
        overlaps = []
        for i in range(len(turn_keywords) - 1):
            for j in range(i + 1, len(turn_keywords)):
                if len(turn_keywords[i]) == 0 or len(turn_keywords[j]) == 0:
                    continue

                intersection = turn_keywords[i] & turn_keywords[j]
                union = turn_keywords[i] | turn_keywords[j]
                overlap = len(intersection) / len(union) if union else 0
                overlaps.append(overlap)

        # If average overlap > 60%, consider it repetitive
        if overlaps:
            avg_overlap = sum(overlaps) / len(overlaps)
            return avg_overlap > 0.6

        return False

    async def _synthesize_debate(
        self,
        model_caller: ModelCallerFunc,
        conversation_history: List[DialogueTurn],
        query: str,
        participants: List[str],
        temperature: float = 0.3,
    ) -> str:
        """
        Synthesize final summary of debate dialogue.

        Uses one of the debate participants to create balanced summary.
        """
        # Build full transcript
        transcript = "\n\n".join(
            [
                f"[Turn {turn.turn_number}] {self._get_position_for_turn(turn.turn_number)}: {turn.content}"
                for turn in conversation_history
            ]
        )

        # Synthesis prompt
        prompt = f"""You are a neutral moderator summarizing a debate between two models.

Debate Topic: {query}

Full Debate Transcript:
{transcript}

Instructions:
- Provide a balanced, objective summary of the debate
- Highlight the strongest arguments from BOTH the PRO and CON sides
- Identify areas of agreement and key points of disagreement
- Note any concessions or shifts in position
- Conclude with an assessment of which side presented the more compelling case (if applicable)

Your neutral summary:"""

        # Use first participant for synthesis (already loaded and available)
        try:
            synthesis_model_id = participants[0]

            response = await model_caller(
                model_id=synthesis_model_id,
                prompt=prompt,
                max_tokens=800,
                temperature=temperature,
            )

            return response.get("content", "").strip()
        except Exception as e:
            self.logger.error(f"Error synthesizing debate: {e}")
            return f"Debate concluded with {len(conversation_history)} turns. See transcript above for details."


# Global instance
dialogue_engine = DialogueEngine()
