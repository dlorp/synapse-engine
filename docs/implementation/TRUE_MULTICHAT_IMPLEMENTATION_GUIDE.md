# True Multi-Chat Dialogue Implementation Guide

**Date:** 2025-11-07
**Status:** Implementation Plan
**Estimated Time:** 12-17 hours (Phase 1)

---

## Executive Summary

### Vision
Upgrade Council Modes from 2-round parallel refinement to true sequential multi-chat dialogue where models engage in back-and-forth addressable conversation.

### Current State
- **Round 1:** All models respond independently in parallel
- **Round 2:** All models refine after reading others' responses in parallel
- **Limitation:** No sequential turn-taking or addressable dialogue

### Target State
- **Sequential Turns:** Model A → B responds to A → A counters B → etc.
- **Addressable Dialogue:** "Model B, your point about X is incorrect because..."
- **Dynamic Termination:** Continue until consensus/stalemate or user-configured max
- **Personas:** User-defined roles with named profile presets

### Implementation Approach
**Phase 1:** Implement for Debate Mode (adversarial, 2 models)
**Phase 2:** Apply learnings to Consensus Mode (collaborative, 3+ models)

---

## Current vs. Target Architecture

### Current Implementation (Parallel Refinement)

```
Debate Mode - Current Flow:

Round 1 (Parallel):
  Model PRO → Argument A1 (independent)
  Model CON → Argument C1 (independent)

Round 2 (Parallel):
  Model PRO reads C1 → Rebuttal A2
  Model CON reads A1 → Rebuttal C2

Synthesis:
  Neutral model reads (A2, C2) → Summary
```

**Problems:**
- Both rebuttals happen simultaneously (not sequential)
- Only 2 rounds (opening + rebuttal)
- No further dialogue after rebuttals
- Models don't directly address each other

### Target Implementation (Sequential Dialogue)

```
Debate Mode - True Multi-Chat:

Turn 1: Model PRO speaks
  "I argue FOR this position because X, Y, and Z..."

Turn 2: Model CON responds TO PRO
  "Model PRO, while your points X and Y are valid, you overlooked A..."

Turn 3: Model PRO responds TO CON's challenge
  "Model CON, you raise a fair point about A, but consider B..."

Turn 4: Model CON counters PRO's point B
  "Regarding your point B, Model PRO, the evidence suggests C..."

Turn 5: Model PRO addresses point C
  "Model CON, point C is interesting, but D contradicts it..."

[Continue sequentially until stalemate, concession, or max turns]

Synthesis:
  Neutral model reads full dialogue → Balanced summary
```

**Improvements:**
- ✅ Sequential turn-taking (not parallel)
- ✅ Addressable responses ("Model PRO, ...")
- ✅ Extended dialogue (5-20 turns vs. 2 rounds)
- ✅ Dynamic termination (stalemate/concession detection)
- ✅ Persona-driven responses

---

## Phase 1: Debate Mode Implementation

### Step 1: Core Dialogue Engine (3-4 hours)

#### 1.1 Create `backend/app/services/dialogue_engine.py`

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/backend/app/services/dialogue_engine.py`

**Implementation:**

```python
"""Sequential multi-model dialogue engine for true multi-chat."""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.services.model_manager import model_manager
from app.models.query import QueryRequest

logger = logging.getLogger(__name__)


class DialogueTurn:
    """Represents a single turn in dialogue."""

    def __init__(
        self,
        turn_number: int,
        speaker_id: str,
        persona: str,
        content: str,
        timestamp: datetime,
        tokens_used: int
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
            "tokensUsed": self.tokens_used
        }


class DialogueResult:
    """Result of a complete dialogue session."""

    def __init__(
        self,
        turns: List[DialogueTurn],
        synthesis: str,
        termination_reason: str,
        total_tokens: int,
        total_time_ms: int
    ):
        self.turns = turns
        self.synthesis = synthesis
        self.termination_reason = termination_reason
        self.total_tokens = total_tokens
        self.total_time_ms = total_time_ms

    def to_dict(self) -> dict:
        return {
            "turns": [turn.to_dict() for turn in self.turns],
            "synthesis": self.synthesis,
            "terminationReason": self.termination_reason,
            "totalTokens": self.total_tokens,
            "totalTimeMs": self.total_time_ms
        }


class DialogueEngine:
    """Manages sequential multi-model dialogue."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def run_debate_dialogue(
        self,
        participants: List[str],  # [model_pro_id, model_con_id]
        query: str,
        personas: Dict[str, str],  # {model_id: persona_description}
        context: Optional[str] = None,
        max_turns: int = 10,
        dynamic_termination: bool = True,
        temperature: float = 0.7,
        max_tokens_per_turn: int = 400
    ) -> DialogueResult:
        """
        Execute sequential debate dialogue between two models.

        Args:
            participants: List of 2 model IDs [pro, con]
            query: Original query/debate topic
            personas: Persona descriptions for each model
            context: Optional CGRAG context
            max_turns: Maximum number of dialogue turns
            dynamic_termination: End early if stalemate/concession detected
            temperature: Model temperature
            max_tokens_per_turn: Max tokens per response

        Returns:
            DialogueResult with full conversation history and synthesis
        """
        if len(participants) != 2:
            raise ValueError("Debate mode requires exactly 2 participants")

        start_time = datetime.now()
        conversation_history: List[DialogueTurn] = []
        total_tokens = 0

        self.logger.info(f"Starting debate dialogue: {len(participants)} participants, max {max_turns} turns")

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
                turn_number=turn_num + 1
            )

            # Call model
            self.logger.debug(f"Turn {turn_num + 1}: {speaker_id} speaking")
            turn_start = datetime.now()

            response = await model_manager.call_model(
                model_id=speaker_id,
                prompt=prompt,
                max_tokens=max_tokens_per_turn,
                temperature=temperature
            )

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
                tokens_used=tokens_used
            )

            conversation_history.append(turn)

            self.logger.debug(f"Turn {turn_num + 1} completed in {(turn_end - turn_start).total_seconds():.2f}s")

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
            conversation_history=conversation_history,
            query=query,
            temperature=temperature
        )

        end_time = datetime.now()
        total_time_ms = int((end_time - start_time).total_seconds() * 1000)

        self.logger.info(f"Debate completed: {len(conversation_history)} turns, {total_time_ms}ms, {total_tokens} tokens")

        return DialogueResult(
            turns=conversation_history,
            synthesis=synthesis,
            termination_reason=termination_reason,
            total_tokens=total_tokens,
            total_time_ms=total_time_ms
        )

    def _build_debate_prompt(
        self,
        query: str,
        speaker_id: str,
        speaker_persona: str,
        conversation_history: List[DialogueTurn],
        context: Optional[str],
        turn_number: int
    ) -> str:
        """Build prompt for next speaker in debate dialogue."""

        # Determine position (PRO or CON)
        position = "PRO" if turn_number % 2 == 1 else "CON"
        opponent_position = "CON" if position == "PRO" else "PRO"

        # Build conversation transcript
        if conversation_history:
            transcript = "\n\n".join([
                f"[Turn {turn.turn_number}] {self._get_position_for_turn(turn.turn_number)}: {turn.content}"
                for turn in conversation_history
            ])
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
            "you make a valid point"
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
        conversation_history: List[DialogueTurn],
        query: str,
        temperature: float = 0.3
    ) -> str:
        """
        Synthesize final summary of debate dialogue.

        Uses a neutral model to create balanced summary of both positions.
        """
        # Build full transcript
        transcript = "\n\n".join([
            f"[Turn {turn.turn_number}] {self._get_position_for_turn(turn.turn_number)}: {turn.content}"
            for turn in conversation_history
        ])

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

        # Use a balanced-tier model for synthesis (or most powerful available)
        synthesis_model = await model_manager.select_model(tier="balanced")

        response = await model_manager.call_model(
            model_id=synthesis_model.model_id,
            prompt=prompt,
            max_tokens=800,
            temperature=temperature
        )

        return response.get("content", "").strip()


# Global instance
dialogue_engine = DialogueEngine()
```

**Expected Result:** Core dialogue engine with sequential turn-taking, prompt building, and termination detection.

---

### Step 2: Persona System (2-3 hours)

#### 2.1 Create `backend/app/services/persona_manager.py`

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/backend/app/services/persona_manager.py`

**Implementation:**

```python
"""Persona and role management for multi-model dialogue."""

import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


# Named persona profiles for debate mode
DEBATE_PERSONA_PROFILES = {
    "classic": {
        "pro": "an optimistic advocate who emphasizes benefits and opportunities",
        "con": "a skeptical critic who focuses on risks and drawbacks"
    },
    "technical": {
        "pro": "a solution architect arguing for implementation feasibility",
        "con": "a senior engineer raising technical concerns and edge cases"
    },
    "business": {
        "pro": "a product manager focused on market value and user needs",
        "con": "a risk analyst evaluating costs and strategic fit"
    },
    "scientific": {
        "pro": "a research scientist presenting evidence and experimental data",
        "con": "a peer reviewer challenging methodology and conclusions"
    },
    "ethical": {
        "pro": "an ethicist arguing from moral principles and values",
        "con": "a pragmatist focusing on real-world consequences and trade-offs"
    },
    "political": {
        "pro": "a progressive reformer advocating for change",
        "con": "a conservative defender of traditional approaches"
    }
}


# Named persona profiles for consensus mode (future Phase 2)
CONSENSUS_PERSONA_PROFILES = {
    "balanced": {
        "analyst": "a pragmatic analyst focused on data and evidence",
        "creative": "a creative thinker exploring unconventional approaches",
        "critic": "a critical thinker identifying potential issues"
    },
    "technical-review": {
        "engineer": "a senior software engineer focused on implementation details",
        "architect": "a system architect concerned with scalability and design",
        "tester": "a quality assurance specialist identifying edge cases"
    },
    "brainstorm": {
        "dreamer": "an idealistic visionary with bold ideas",
        "realist": "a practical implementer grounding ideas in reality",
        "synthesizer": "a strategic thinker combining perspectives"
    }
}


class PersonaManager:
    """Manages persona assignment for multi-model dialogue."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_debate_personas(
        self,
        participants: List[str],
        user_personas: Optional[Dict[str, str]] = None,
        profile_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get persona descriptions for debate participants.

        Priority:
        1. User-defined personas (if provided)
        2. Named profile (if specified)
        3. Default "classic" profile

        Args:
            participants: List of 2 model IDs [pro, con]
            user_personas: Optional user-defined personas {"pro": "...", "con": "..."}
            profile_name: Optional named profile ("classic", "technical", etc.)

        Returns:
            Dict mapping model_id to persona description
        """
        if len(participants) != 2:
            raise ValueError("Debate mode requires exactly 2 participants")

        # Priority 1: User-defined personas
        if user_personas:
            if "pro" not in user_personas or "con" not in user_personas:
                self.logger.warning("User personas missing 'pro' or 'con', falling back to profile")
            else:
                self.logger.info("Using user-defined personas")
                return {
                    participants[0]: user_personas["pro"],
                    participants[1]: user_personas["con"]
                }

        # Priority 2: Named profile
        if profile_name:
            if profile_name in DEBATE_PERSONA_PROFILES:
                self.logger.info(f"Using named profile: {profile_name}")
                profile = DEBATE_PERSONA_PROFILES[profile_name]
                return {
                    participants[0]: profile["pro"],
                    participants[1]: profile["con"]
                }
            else:
                self.logger.warning(f"Unknown profile '{profile_name}', using default")

        # Priority 3: Default "classic" profile
        self.logger.info("Using default 'classic' profile")
        profile = DEBATE_PERSONA_PROFILES["classic"]
        return {
            participants[0]: profile["pro"],
            participants[1]: profile["con"]
        }

    def get_consensus_personas(
        self,
        participants: List[str],
        user_personas: Optional[Dict[str, str]] = None,
        profile_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get persona descriptions for consensus participants (Phase 2).

        Args:
            participants: List of 3+ model IDs
            user_personas: Optional user-defined personas {model_id: persona}
            profile_name: Optional named profile ("balanced", "technical-review", etc.)

        Returns:
            Dict mapping model_id to persona description
        """
        if len(participants) < 3:
            raise ValueError("Consensus mode requires at least 3 participants")

        # Priority 1: User-defined personas
        if user_personas:
            if len(user_personas) >= len(participants):
                self.logger.info("Using user-defined personas")
                return {
                    participant: user_personas.get(participant, "a collaborative participant")
                    for participant in participants
                }

        # Priority 2: Named profile
        if profile_name and profile_name in CONSENSUS_PERSONA_PROFILES:
            self.logger.info(f"Using named profile: {profile_name}")
            profile = CONSENSUS_PERSONA_PROFILES[profile_name]
            role_names = list(profile.keys())

            # Map participants to roles (round-robin if more participants than roles)
            return {
                participants[i]: profile[role_names[i % len(role_names)]]
                for i in range(len(participants))
            }

        # Priority 3: Default generic personas
        self.logger.info("Using default generic personas")
        generic_roles = [
            "a pragmatic analyst",
            "a creative thinker",
            "a critical evaluator",
            "a detail-oriented specialist",
            "a strategic synthesizer"
        ]

        return {
            participants[i]: generic_roles[i % len(generic_roles)]
            for i in range(len(participants))
        }

    def list_debate_profiles(self) -> List[str]:
        """List available debate persona profile names."""
        return list(DEBATE_PERSONA_PROFILES.keys())

    def list_consensus_profiles(self) -> List[str]:
        """List available consensus persona profile names."""
        return list(CONSENSUS_PERSONA_PROFILES.keys())

    def get_profile_description(self, mode: str, profile_name: str) -> Optional[Dict[str, str]]:
        """Get full persona profile by name."""
        if mode == "debate":
            return DEBATE_PERSONA_PROFILES.get(profile_name)
        elif mode == "consensus":
            return CONSENSUS_PERSONA_PROFILES.get(profile_name)
        return None


# Global instance
persona_manager = PersonaManager()
```

**Expected Result:** Persona system with named profiles and user-defined persona support.

---

### Step 3: Update API Models (1-2 hours)

#### 3.1 Update `backend/app/models/query.py`

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/backend/app/models/query.py`

**Lines to modify:** ~84-101 (existing council fields) + add new fields

**Changes:**

```python
# Add after existing council fields (around line 101)

# Multi-chat dialogue configuration
council_max_turns: Optional[int] = Field(
    default=10,
    ge=2,
    le=20,
    alias="councilMaxTurns",
    description="Maximum dialogue turns (2-20). Default 10."
)

council_dynamic_termination: bool = Field(
    default=True,
    alias="councilDynamicTermination",
    description="End dialogue early if consensus/stalemate detected"
)

council_personas: Optional[Dict[str, str]] = Field(
    default=None,
    alias="councilPersonas",
    description="User-defined personas. Debate: {'pro': 'description', 'con': 'description'}. Consensus: {model_id: persona}"
)

council_persona_profile: Optional[str] = Field(
    default=None,
    alias="councilPersonaProfile",
    description="Named persona profile: 'classic', 'technical', 'business', 'scientific', 'ethical', 'political'"
)
```

**Expected Result:** API can accept multi-chat configuration from frontend.

---

### Step 4: Update Backend Routing (2-3 hours)

#### 4.1 Update `backend/app/routers/query.py`

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/backend/app/routers/query.py`

**Lines to modify:** 502-873 (`_process_debate_mode` function)

**Strategy:** Replace current parallel 2-round implementation with dialogue engine call.

**Current Code (lines ~502-873):**
```python
async def _process_debate_mode(...):
    # Round 1: Parallel opening arguments
    # Round 2: Parallel rebuttals
    # Synthesis
    return response
```

**New Code:**

```python
async def _process_debate_mode(
    request: QueryRequest,
    participants: List[str],
    context_string: str,
    start_time: datetime
) -> QueryResponse:
    """
    Process query using adversarial debate mode with TRUE MULTI-CHAT.

    Uses DialogueEngine for sequential turn-based dialogue instead of
    parallel 2-round refinement.
    """
    from app.services.dialogue_engine import dialogue_engine
    from app.services.persona_manager import persona_manager

    logger.info(f"Processing debate mode with {len(participants)} participants (true multi-chat)")

    # Validate participant count
    if len(participants) != 2:
        raise ValueError("Debate mode requires exactly 2 participants")

    # Get personas (user-defined, profile, or default)
    personas = persona_manager.get_debate_personas(
        participants=participants,
        user_personas=request.council_personas,
        profile_name=request.council_persona_profile
    )

    logger.info(f"Personas: {personas}")

    # Run dialogue engine
    dialogue_result = await dialogue_engine.run_debate_dialogue(
        participants=participants,
        query=request.query,
        personas=personas,
        context=context_string if context_string else None,
        max_turns=request.council_max_turns or 10,
        dynamic_termination=request.council_dynamic_termination,
        temperature=request.temperature,
        max_tokens_per_turn=400
    )

    # Build response metadata
    end_time = datetime.now()
    total_time_ms = int((end_time - start_time).total_seconds() * 1000)

    # Format response
    response_data = {
        "response": dialogue_result.synthesis,
        "queryMode": "council",
        "councilMode": "adversarial",
        "councilDialogue": True,  # Flag for frontend to render as dialogue
        "councilTurns": dialogue_result.to_dict()["turns"],
        "councilSynthesis": dialogue_result.synthesis,
        "councilTerminationReason": dialogue_result.termination_reason,
        "councilTotalTurns": len(dialogue_result.turns),
        "councilMaxTurns": request.council_max_turns or 10,
        "councilParticipants": participants,
        "councilPersonas": personas,
        "processingTimeMs": total_time_ms,
        "totalTokens": dialogue_result.total_tokens,
        "timestamp": start_time.isoformat()
    }

    logger.info(f"Debate dialogue completed: {len(dialogue_result.turns)} turns, {dialogue_result.termination_reason}")

    return QueryResponse(**response_data)
```

**Expected Result:** Debate mode now uses true multi-chat dialogue instead of parallel refinement.

---

### Step 5: Frontend UI Updates (3-4 hours)

#### 5.1 Update ModeSelector Component

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/components/modes/ModeSelector.tsx`

**Lines to modify:** ~99-127 (council configuration panel)

**Add:**
1. "Max Turns" slider (2-20, default 10)
2. "Dynamic Termination" checkbox
3. Persona profile dropdown
4. Custom persona text inputs (PRO/CON)

**New UI Elements:**

```typescript
// Add to council configuration section (~line 110)

{/* Max Turns Slider */}
<div className={styles.configOption}>
  <label className={styles.configLabel}>
    Max Dialogue Turns: {councilMaxTurns}
  </label>
  <input
    type="range"
    min={2}
    max={20}
    value={councilMaxTurns}
    onChange={(e) => setCouncilMaxTurns(Number(e.target.value))}
    className={styles.slider}
  />
  <span className={styles.sliderHint}>
    {councilMaxTurns < 6 ? 'Quick' : councilMaxTurns < 12 ? 'Balanced' : 'Extended'}
  </span>
</div>

{/* Dynamic Termination Checkbox */}
<div className={styles.configOption}>
  <label className={styles.checkboxLabel}>
    <input
      type="checkbox"
      checked={councilDynamicTermination}
      onChange={(e) => setCouncilDynamicTermination(e.target.checked)}
    />
    <span>Dynamic Termination</span>
  </label>
  <span className={styles.hint}>
    End early if stalemate or concession detected
  </span>
</div>

{/* Persona Configuration */}
<div className={styles.configSection}>
  <h4 className={styles.sectionTitle}>Persona Configuration</h4>

  {/* Named Profile Dropdown */}
  <div className={styles.configOption}>
    <label className={styles.configLabel}>Named Profile</label>
    <select
      value={councilPersonaProfile}
      onChange={(e) => setCouncilPersonaProfile(e.target.value)}
      className={styles.select}
    >
      <option value="">-- Custom Personas --</option>
      <option value="classic">Classic (Optimist vs. Skeptic)</option>
      <option value="technical">Technical (Architect vs. Engineer)</option>
      <option value="business">Business (PM vs. Risk Analyst)</option>
      <option value="scientific">Scientific (Researcher vs. Peer Reviewer)</option>
      <option value="ethical">Ethical (Ethicist vs. Pragmatist)</option>
      <option value="political">Political (Progressive vs. Conservative)</option>
    </select>
  </div>

  {/* Custom Personas (only show if no profile selected) */}
  {!councilPersonaProfile && (
    <>
      <div className={styles.configOption}>
        <label className={styles.configLabel}>PRO Persona</label>
        <input
          type="text"
          value={councilPersonaPro}
          onChange={(e) => setCouncilPersonaPro(e.target.value)}
          placeholder="e.g., an environmental advocate..."
          className={styles.input}
        />
      </div>

      <div className={styles.configOption}>
        <label className={styles.configLabel}>CON Persona</label>
        <input
          type="text"
          value={councilPersonaCon}
          onChange={(e) => setCouncilPersonaCon(e.target.value)}
          placeholder="e.g., a fiscal conservative..."
          className={styles.input}
        />
      </div>
    </>
  )}
</div>
```

**Expected Result:** Users can configure max turns, dynamic termination, and personas via UI.

#### 5.2 Update ResponseDisplay Component

**File:** `/Users/dperez/Documents/Programming/SYNAPSE_ENGINE/frontend/src/components/query/ResponseDisplay.tsx`

**Lines to modify:** ~497-627 (council deliberation section)

**Changes:** Add dialogue view for `councilDialogue: true` responses.

**New Dialogue View:**

```typescript
// Add dialogue rendering (~line 520, inside council mode section)

{response.councilDialogue && response.councilTurns && (
  <div className={styles.dialogueView}>
    <div className={styles.dialogueHeader}>
      <span className={styles.dialogueTitle}>
        {response.councilMode === 'adversarial' ? 'DEBATE DIALOGUE' : 'CONSENSUS DIALOGUE'}
      </span>
      <span className={styles.dialogueMeta}>
        {response.councilTotalTurns} turns • {response.councilTerminationReason.replace(/_/g, ' ')}
      </span>
    </div>

    <div className={styles.dialogueTranscript}>
      {response.councilTurns.map((turn, idx) => {
        const position = turn.turnNumber % 2 === 1 ? 'PRO' : 'CON';
        const isLeft = position === 'PRO';

        return (
          <div
            key={idx}
            className={`${styles.dialogueTurn} ${isLeft ? styles.turnLeft : styles.turnRight}`}
          >
            <div className={styles.turnHeader}>
              <span className={styles.turnNumber}>Turn {turn.turnNumber}</span>
              <span className={`${styles.turnPosition} ${styles[position.toLowerCase()]}`}>
                {position}
              </span>
              <span className={styles.turnPersona}>{turn.persona}</span>
            </div>

            <div className={styles.turnContent}>
              {turn.content}
            </div>

            <div className={styles.turnFooter}>
              <span className={styles.turnTokens}>{turn.tokensUsed} tokens</span>
            </div>
          </div>
        );
      })}
    </div>

    <div className={styles.dialogueSynthesis}>
      <div className={styles.synthesisHeader}>SYNTHESIS</div>
      <div className={styles.synthesisContent}>
        {response.councilSynthesis || response.response}
      </div>
    </div>
  </div>
)}
```

**CSS Additions** (add to ResponseDisplay.module.css):

```css
/* Dialogue View Styles */
.dialogueView {
  margin-top: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--background-secondary);
}

.dialogueHeader {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialogueTitle {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 0.9rem;
  letter-spacing: 0.05em;
}

.dialogueMeta {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.dialogueTranscript {
  padding: 1rem;
  max-height: 600px;
  overflow-y: auto;
}

.dialogueTurn {
  margin-bottom: 1.5rem;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.turnLeft {
  margin-right: 20%;
  background: rgba(255, 149, 0, 0.05);
  border-left: 3px solid var(--primary-color);
}

.turnRight {
  margin-left: 20%;
  background: rgba(0, 255, 255, 0.05);
  border-right: 3px solid var(--accent-color);
}

.turnHeader {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
  font-size: 0.85rem;
}

.turnNumber {
  font-weight: 600;
  color: var(--text-secondary);
}

.turnPosition {
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}

.turnPosition.pro {
  background: rgba(255, 149, 0, 0.2);
  color: var(--primary-color);
}

.turnPosition.con {
  background: rgba(0, 255, 255, 0.2);
  color: var(--accent-color);
}

.turnPersona {
  color: var(--text-secondary);
  font-style: italic;
}

.turnContent {
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: 0.5rem;
}

.turnFooter {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: right;
}

.dialogueSynthesis {
  margin-top: 1rem;
  padding: 1rem;
  border-top: 2px solid var(--border-color);
  background: rgba(255, 149, 0, 0.03);
}

.synthesisHeader {
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  letter-spacing: 0.05em;
}

.synthesisContent {
  color: var(--text-primary);
  line-height: 1.6;
}
```

**Expected Result:** Chat-style UI showing sequential dialogue turns with PRO/CON visual distinction.

---

### Step 6: Testing & Validation (2-3 hours)

#### 6.1 Docker Testing Workflow

**IMPORTANT:** All testing MUST be done in Docker.

```bash
# 1. Rebuild backend with new dialogue engine
docker-compose build --no-cache backend

# 2. Rebuild frontend with persona UI
docker-compose build --no-cache frontend

# 3. Restart services
docker-compose down
docker-compose up -d

# 4. Monitor logs
docker-compose logs -f backend
docker-compose logs -f frontend

# 5. Test via WebUI at http://localhost:5173
```

#### 6.2 Test Cases

**Test 1: Basic Debate Dialogue (Default Classic Profile)**
- Query: "Should we adopt serverless architecture for our web application?"
- Mode: Council (Adversarial)
- Max Turns: 6
- Dynamic Termination: ON
- Profile: "classic"
- Expected: 4-6 turns, PRO argues benefits, CON argues risks, synthesis balances both

**Test 2: Extended Technical Debate**
- Query: "Is Rust a better choice than Python for backend development?"
- Mode: Council (Adversarial)
- Max Turns: 12
- Dynamic Termination: ON
- Profile: "technical"
- Expected: 8-12 turns, deep technical arguments, possibly early termination on concession

**Test 3: Custom Personas**
- Query: "Should cities ban cars from downtown areas?"
- Mode: Council (Adversarial)
- Max Turns: 8
- Dynamic Termination: ON
- Custom Personas:
  - PRO: "an urban planner advocating for pedestrian-friendly cities"
  - CON: "a small business owner concerned about customer access"
- Expected: Role-specific arguments, addresses from persona perspectives

**Test 4: Stalemate Detection**
- Query: "Is Python or JavaScript better?" (classic flamebait)
- Mode: Council (Adversarial)
- Max Turns: 15
- Dynamic Termination: ON
- Profile: "classic"
- Expected: Early termination due to repetitive arguments (stalemate)

**Test 5: Performance Validation**
- Various queries with max_turns = 10
- Ensure total time < 30 seconds
- Monitor token usage
- Check frontend responsiveness

#### 6.3 Validation Checklist

- [ ] Dialogue engine creates sequential turns (not parallel)
- [ ] Models address each other directly in responses
- [ ] Personas influence response style appropriately
- [ ] Dynamic termination detects concession correctly
- [ ] Dynamic termination detects stalemate correctly
- [ ] Max turns acts as hard limit
- [ ] Frontend displays chat-style dialogue correctly
- [ ] PRO/CON visual distinction is clear
- [ ] Synthesis provides balanced summary
- [ ] Performance meets <30s target for typical debates
- [ ] Custom personas work as expected
- [ ] Named profiles work as expected
- [ ] Switching between profiles updates UI correctly
- [ ] All metadata fields present in response

---

### Step 7: Documentation Updates (1 hour)

#### 7.1 Update MODES.md

**File:** `docs/features/MODES.md`

**Lines 127-151:** Replace "Debate Mode (Coming Soon)" with council adversarial sub-mode description

**Add section at line ~152:**

```markdown
### ✅ True Multi-Chat Dialogue (Implemented for Debate)

**What Changed:**
Council Mode now uses **sequential turn-taking dialogue** instead of 2-round parallel refinement.

**Before (v3.0):**
- Round 1: Both models respond in parallel
- Round 2: Both models rebuttal in parallel
- Fixed 2 rounds only

**Now (v3.1+):**
- Turn-by-turn sequential dialogue
- Models directly address each other's points
- Dynamic termination (stalemate/concession detection)
- User-configurable turn count (2-20)
- Persona-driven responses with named profiles

**Example Debate Flow:**
```
Turn 1 (PRO): "I argue FOR this position because..."
Turn 2 (CON): "Model PRO, while your point about X is valid, you overlooked Y..."
Turn 3 (PRO): "Model CON, regarding Y, consider Z which contradicts your argument..."
Turn 4 (CON): "That's a fair point about Z, but evidence suggests..."
[Continue until stalemate, concession, or max turns]
```

**Configuration Options:**
- `councilMaxTurns`: 2-20 (default 10)
- `councilDynamicTermination`: true/false (default true)
- `councilPersonaProfile`: "classic", "technical", "business", "scientific", "ethical", "political"
- `councilPersonas`: Custom personas {"pro": "description", "con": "description"}

**Persona Profiles:**
- **classic**: Optimist vs. Skeptic
- **technical**: Solution Architect vs. Senior Engineer
- **business**: Product Manager vs. Risk Analyst
- **scientific**: Research Scientist vs. Peer Reviewer
- **ethical**: Ethicist vs. Pragmatist
- **political**: Progressive vs. Conservative

**Status:** ✅ Available for Debate Mode (Phase 1 complete)
**Coming Soon:** Multi-chat for Consensus Mode (Phase 2)
```

#### 7.2 Update SESSION_NOTES.md

Add new session entry at the top documenting the implementation.

---

## Phase 2: Consensus Mode (Future - 8-12 hours)

### Overview
Apply true multi-chat to Consensus Mode (3+ models, collaborative).

### Key Differences from Debate
- **Participants:** 3+ models instead of 2
- **Turn Order:** Round-robin instead of alternating PRO/CON
- **Termination:** Consensus detection instead of stalemate
- **Personas:** Collaborative roles instead of adversarial

### Reusable Components
- ✅ DialogueEngine core (extend for multi-participant)
- ✅ PersonaManager (use CONSENSUS_PERSONA_PROFILES)
- ✅ API models (already support councilPersonas as dict)
- ✅ Frontend UI patterns (adapt for 3+ speakers)

### New Requirements
1. **Consensus Detection Algorithm**
   - Check if models are converging on similar conclusions
   - Keyword analysis for agreement
   - Similarity scoring between recent responses

2. **Round-Robin Turn Selection**
   - Simple: rotate through participants
   - Smart: select next speaker based on who has spoken least
   - Dynamic: allow models to "yield floor" to others

3. **Multi-Speaker UI**
   - Color-code 3+ participants
   - Show speaking order visually
   - Highlight consensus emergence

---

## Success Metrics

### Functional Requirements
- ✅ Sequential turn-taking (not parallel)
- ✅ Addressable dialogue between models
- ✅ Dynamic termination (stalemate/concession)
- ✅ User-configurable turns (2-20)
- ✅ Named persona profiles (6+ options)
- ✅ Custom user-defined personas
- ✅ Chat-style UI with visual distinction

### Performance Requirements
- ✅ Typical debate (6-8 turns): <25 seconds
- ✅ Max turns (20): <45 seconds
- ✅ No degradation to other query modes

### Quality Requirements
- ✅ Models reference each other's specific points
- ✅ Personas influence response style
- ✅ Synthesis provides balanced summary
- ✅ Better insights than 2-round parallel system

---

## Rollout Strategy

### Phase 1A: Backend Implementation
1. Create dialogue_engine.py
2. Create persona_manager.py
3. Update API models
4. Update _process_debate_mode()
5. Test backend independently

### Phase 1B: Frontend Implementation
6. Update ModeSelector UI
7. Update ResponseDisplay UI
8. Test UI in Docker

### Phase 1C: Integration & Testing
9. End-to-end testing in Docker
10. Performance validation
11. Documentation updates

### Phase 2: Consensus Mode
12. Extend DialogueEngine for 3+ participants
13. Add consensus detection
14. Update UI for multi-speaker
15. Test and refine

---

## File Summary

### New Files
- ✅ `backend/app/services/dialogue_engine.py` (300+ lines)
- ✅ `backend/app/services/persona_manager.py` (200+ lines)
- ✅ `docs/implementation/TRUE_MULTICHAT_IMPLEMENTATION_GUIDE.md` (this file)

### Modified Files
- ✏️ `backend/app/models/query.py` (add 30 lines for multi-chat config)
- ✏️ `backend/app/routers/query.py` (replace _process_debate_mode, ~100 lines)
- ✏️ `frontend/src/components/modes/ModeSelector.tsx` (add 80 lines for UI controls)
- ✏️ `frontend/src/components/query/ResponseDisplay.tsx` (add 100 lines for dialogue view)
- ✏️ `frontend/src/components/query/ResponseDisplay.module.css` (add 150 lines for dialogue styles)
- ✏️ `docs/features/MODES.md` (update lines 127-178)
- ✏️ `SESSION_NOTES.md` (add new session entry)

### Total Estimate
- **New Code:** ~500 lines (backend) + ~180 lines (frontend) + ~150 lines (CSS)
- **Modified Code:** ~330 lines
- **Documentation:** ~200 lines
- **Testing Time:** 2-3 hours
- **Total Time:** 12-17 hours

---

## Next Steps

1. ✅ Create this implementation guide
2. ⏳ Create dialogue_engine.py
3. ⏳ Create persona_manager.py
4. ⏳ Update API models
5. ⏳ Update backend routing
6. ⏳ Update frontend UI
7. ⏳ Docker testing
8. ⏳ Documentation updates

Let's begin! 🚀
