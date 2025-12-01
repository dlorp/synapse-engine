"""Query Expansion for CRAG - Expand queries with synonyms to improve retrieval.

This module implements query expansion for the PARTIAL relevance category in CRAG.
Uses local synonym mappings (no external API calls) for privacy-preserving expansion.
"""

import logging
from typing import List, Set

logger = logging.getLogger(__name__)


class QueryExpander:
    """Expands queries with synonyms to improve retrieval (PARTIAL category).

    Uses local domain-specific synonym mappings (no external API calls for privacy).
    When CRAG evaluates retrieval as PARTIAL, query expansion is applied to
    augment the original query with related terms, then re-retrieval is performed.
    """

    # Domain-specific synonym mappings
    # TODO: Load from configuration file (backend/data/synonyms.json) for extensibility
    SYNONYMS = {
        # Programming concepts
        'function': ['method', 'procedure', 'routine', 'callable'],
        'variable': ['parameter', 'argument', 'value', 'identifier'],
        'error': ['exception', 'failure', 'bug', 'issue'],
        'class': ['type', 'object', 'structure', 'entity'],
        'async': ['asynchronous', 'concurrent', 'non-blocking'],
        'sync': ['synchronous', 'blocking', 'sequential'],
        'loop': ['iteration', 'cycle', 'repeat'],
        'condition': ['conditional', 'if-statement', 'branch'],

        # Actions and operations
        'explain': ['describe', 'clarify', 'illustrate', 'define'],
        'compare': ['contrast', 'differentiate', 'distinguish'],
        'implement': ['create', 'build', 'develop', 'code'],
        'optimize': ['improve', 'enhance', 'refactor', 'speed up'],
        'debug': ['troubleshoot', 'diagnose', 'fix'],
        'test': ['validate', 'verify', 'check'],
        'analyze': ['examine', 'investigate', 'study'],

        # System concepts
        'performance': ['speed', 'efficiency', 'throughput', 'latency'],
        'memory': ['RAM', 'heap', 'storage', 'allocation'],
        'network': ['connection', 'communication', 'protocol'],
        'database': ['db', 'datastore', 'persistence', 'storage'],
        'cache': ['buffer', 'temporary storage', 'memoization'],
        'api': ['interface', 'endpoint', 'service'],

        # Architecture patterns
        'pattern': ['design pattern', 'architecture', 'approach'],
        'service': ['microservice', 'component', 'module'],
        'client': ['consumer', 'caller', 'user'],
        'server': ['backend', 'service', 'provider'],

        # Documentation terms
        'guide': ['tutorial', 'walkthrough', 'documentation'],
        'example': ['sample', 'demo', 'illustration'],
        'reference': ['documentation', 'manual', 'spec'],

        # Common technical terms
        'config': ['configuration', 'settings', 'parameters'],
        'log': ['logging', 'record', 'trace'],
        'monitor': ['observe', 'track', 'watch'],
        'deploy': ['deployment', 'release', 'publish']
    }

    def __init__(self, max_synonyms_per_term: int = 2):
        """Initialize query expander.

        Args:
            max_synonyms_per_term: Maximum synonyms to add per keyword
        """
        self.max_synonyms = max_synonyms_per_term
        logger.info(
            f"Initialized QueryExpander: max_synonyms={max_synonyms_per_term}, "
            f"synonym_dict_size={len(self.SYNONYMS)}"
        )

    def expand(self, query: str) -> str:
        """Expand query with synonyms.

        Extracts keywords from query, looks up synonyms, and constructs
        expanded query by adding related terms.

        Args:
            query: Original query

        Returns:
            Expanded query with synonyms added

        Example:
            >>> expander = QueryExpander()
            >>> expander.expand("explain async function")
            "explain describe clarify async asynchronous concurrent function method routine"
        """
        # Tokenize query (lowercase for matching)
        tokens = query.lower().split()

        # Collect original terms + synonyms
        expanded_terms: Set[str] = set(tokens)

        for token in tokens:
            if token in self.SYNONYMS:
                # Add up to max_synonyms for this term
                synonyms = self.SYNONYMS[token][:self.max_synonyms]
                expanded_terms.update(synonyms)
                logger.debug(f"[EXPAND] '{token}' -> {synonyms}")

        # Construct expanded query (original + synonyms)
        expanded_query = ' '.join(expanded_terms)

        logger.info(
            f"[EXPAND] Original query: '{query}' "
            f"({len(tokens)} tokens) -> "
            f"Expanded query: '{expanded_query}' "
            f"({len(expanded_terms)} terms)"
        )

        return expanded_query

    def add_synonym(self, term: str, synonyms: List[str]):
        """Add a new synonym mapping to the expander.

        Allows runtime extension of synonym dictionary.

        Args:
            term: Base term
            synonyms: List of synonym terms
        """
        self.SYNONYMS[term.lower()] = synonyms
        logger.info(f"[EXPAND] Added synonym mapping: '{term}' -> {synonyms}")

    def load_synonyms_from_file(self, filepath: str):
        """Load synonym mappings from JSON file.

        Expected format:
        {
            "function": ["method", "procedure"],
            "error": ["exception", "bug"]
        }

        Args:
            filepath: Path to JSON file with synonyms

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON format is invalid
        """
        import json
        from pathlib import Path

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Synonym file not found: {filepath}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                synonyms = json.load(f)

            # Validate format
            if not isinstance(synonyms, dict):
                raise ValueError("Synonym file must contain a JSON object")

            # Merge with existing synonyms
            self.SYNONYMS.update(synonyms)

            logger.info(
                f"[EXPAND] Loaded {len(synonyms)} synonym mappings from {filepath}"
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in synonym file: {e}")
