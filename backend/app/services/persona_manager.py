"""Persona and role management for multi-model dialogue."""

import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


# Named persona profiles for debate mode
DEBATE_PERSONA_PROFILES = {
    "classic": {
        "pro": "an optimistic advocate who emphasizes benefits and opportunities",
        "con": "a skeptical critic who focuses on risks and drawbacks",
    },
    "technical": {
        "pro": "a solution architect arguing for implementation feasibility",
        "con": "a senior engineer raising technical concerns and edge cases",
    },
    "business": {
        "pro": "a product manager focused on market value and user needs",
        "con": "a risk analyst evaluating costs and strategic fit",
    },
    "scientific": {
        "pro": "a research scientist presenting evidence and experimental data",
        "con": "a peer reviewer challenging methodology and conclusions",
    },
    "ethical": {
        "pro": "an ethicist arguing from moral principles and values",
        "con": "a pragmatist focusing on real-world consequences and trade-offs",
    },
    "political": {
        "pro": "a progressive reformer advocating for change",
        "con": "a conservative defender of traditional approaches",
    },
}


# Named persona profiles for consensus mode (future Phase 2)
CONSENSUS_PERSONA_PROFILES = {
    "balanced": {
        "analyst": "a pragmatic analyst focused on data and evidence",
        "creative": "a creative thinker exploring unconventional approaches",
        "critic": "a critical thinker identifying potential issues",
    },
    "technical-review": {
        "engineer": "a senior software engineer focused on implementation details",
        "architect": "a system architect concerned with scalability and design",
        "tester": "a quality assurance specialist identifying edge cases",
    },
    "brainstorm": {
        "dreamer": "an idealistic visionary with bold ideas",
        "realist": "a practical implementer grounding ideas in reality",
        "synthesizer": "a strategic thinker combining perspectives",
    },
}


class PersonaManager:
    """Manages persona assignment for multi-model dialogue."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_debate_personas(
        self,
        participants: List[str],
        user_personas: Optional[Dict[str, str]] = None,
        profile_name: Optional[str] = None,
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
                self.logger.warning(
                    "User personas missing 'pro' or 'con', falling back to profile"
                )
            else:
                self.logger.info("Using user-defined personas")
                return {
                    participants[0]: user_personas["pro"],
                    participants[1]: user_personas["con"],
                }

        # Priority 2: Named profile
        if profile_name:
            if profile_name in DEBATE_PERSONA_PROFILES:
                self.logger.info(f"Using named profile: {profile_name}")
                profile = DEBATE_PERSONA_PROFILES[profile_name]
                return {
                    participants[0]: profile["pro"],
                    participants[1]: profile["con"],
                }
            else:
                self.logger.warning(f"Unknown profile '{profile_name}', using default")

        # Priority 3: Default "classic" profile
        self.logger.info("Using default 'classic' profile")
        profile = DEBATE_PERSONA_PROFILES["classic"]
        return {participants[0]: profile["pro"], participants[1]: profile["con"]}

    def get_consensus_personas(
        self,
        participants: List[str],
        user_personas: Optional[Dict[str, str]] = None,
        profile_name: Optional[str] = None,
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
                    participant: user_personas.get(
                        participant, "a collaborative participant"
                    )
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
            "a strategic synthesizer",
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

    def get_profile_description(
        self, mode: str, profile_name: str
    ) -> Optional[Dict[str, str]]:
        """Get full persona profile by name."""
        if mode == "debate":
            return DEBATE_PERSONA_PROFILES.get(profile_name)
        elif mode == "consensus":
            return CONSENSUS_PERSONA_PROFILES.get(profile_name)
        return None


# Global instance
persona_manager = PersonaManager()
