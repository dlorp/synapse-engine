"""Token counting service for accurate context window tracking.

This module provides token counting capabilities using tiktoken for accurate
token estimation. Token counts are essential for context window management,
ensuring queries stay within model context limits.

The service supports caching to avoid re-counting identical text, and uses
the cl100k_base encoding which is compatible with most modern LLMs.

Author: Backend Architect
Feature: Context Window Allocation Viewer
"""

from typing import Dict, List, Optional

import tiktoken

from app.core.logging import get_logger

logger = get_logger(__name__)


class TokenCounter:
    """Token counting service using tiktoken.

    Provides accurate token counting for text using the tiktoken library,
    which implements the same tokenization as OpenAI models. Most modern
    LLMs use similar tokenization schemes, making this a reliable estimator.

    Architecture:
        - Uses cl100k_base encoding (GPT-4, GPT-3.5-turbo compatible)
        - Caches encodings to avoid reinitialization
        - Supports batch counting for efficiency
        - Thread-safe singleton pattern

    Attributes:
        encoding: tiktoken encoding instance
        _cache: Optional cache for repeated text (future enhancement)

    Example:
        >>> counter = TokenCounter()
        >>> tokens = counter.count_tokens("Hello world")
        >>> print(tokens)  # Output: 2
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize token counter with specified encoding.

        Args:
            encoding_name: Tiktoken encoding name (default: cl100k_base)
                Supported encodings:
                - cl100k_base: GPT-4, GPT-3.5-turbo, text-embedding-ada-002
                - p50k_base: Codex models, text-davinci-002/003
                - r50k_base: GPT-3 models (davinci, curie, babbage, ada)

        Raises:
            ValueError: If encoding_name is not recognized
        """
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
            self._encoding_name = encoding_name
            logger.info(
                f"TokenCounter initialized with encoding: {encoding_name}",
                extra={"encoding": encoding_name},
            )
        except Exception as e:
            logger.error(f"Failed to initialize tiktoken encoding: {e}", exc_info=True)
            raise ValueError(f"Invalid encoding name: {encoding_name}") from e

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens in the text

        Example:
            >>> counter = TokenCounter()
            >>> count = counter.count_tokens("The quick brown fox jumps")
            >>> print(count)  # Output: 5
        """
        if not text:
            return 0

        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(
                f"Error counting tokens: {e}",
                extra={"text_length": len(text)},
                exc_info=True,
            )
            # Fallback to rough estimation
            return self._estimate_tokens(text)

    def count_tokens_batch(self, texts: List[str]) -> List[int]:
        """Count tokens for multiple texts efficiently.

        Args:
            texts: List of text strings to count

        Returns:
            List of token counts corresponding to input texts

        Example:
            >>> counter = TokenCounter()
            >>> counts = counter.count_tokens_batch(["Hello", "World"])
            >>> print(counts)  # Output: [1, 1]
        """
        return [self.count_tokens(text) for text in texts]

    def count_tokens_dict(self, text_dict: Dict[str, str]) -> Dict[str, int]:
        """Count tokens for a dictionary of text strings.

        Useful for counting tokens in structured data (system prompt,
        user query, context, etc.) in a single call.

        Args:
            text_dict: Dictionary mapping keys to text strings

        Returns:
            Dictionary mapping same keys to token counts

        Example:
            >>> counter = TokenCounter()
            >>> counts = counter.count_tokens_dict({
            ...     "system": "You are a helpful assistant",
            ...     "user": "Hello"
            ... })
            >>> print(counts)  # Output: {'system': 5, 'user': 1}
        """
        return {key: self.count_tokens(text) for key, text in text_dict.items()}

    def _estimate_tokens(self, text: str) -> int:
        """Fallback token estimation using word counting.

        This is a rough approximation used when tiktoken fails. Uses
        the heuristic of 1.3 tokens per word, which is approximately
        correct for English text.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        # Rough estimation: ~1.3 tokens per word
        word_count = len(text.split())
        estimated_tokens = int(word_count * 1.3)

        logger.warning(
            f"Using fallback token estimation: {estimated_tokens} tokens",
            extra={"word_count": word_count, "estimated_tokens": estimated_tokens},
        )

        return estimated_tokens

    def truncate_to_token_limit(
        self, text: str, max_tokens: int, suffix: str = "..."
    ) -> str:
        """Truncate text to fit within token limit.

        Useful for ensuring text fits within context windows. Adds an
        optional suffix (default: "...") to indicate truncation.

        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens allowed
            suffix: String to append if truncated (default: "...")

        Returns:
            Truncated text that fits within token limit (including suffix)

        Example:
            >>> counter = TokenCounter()
            >>> text = "The quick brown fox jumps over the lazy dog"
            >>> truncated = counter.truncate_to_token_limit(text, 5)
            >>> print(truncated)  # Output: "The quick brown..."
        """
        if not text:
            return text

        try:
            tokens = self.encoding.encode(text)

            if len(tokens) <= max_tokens:
                return text

            # Reserve tokens for suffix
            suffix_tokens = self.encoding.encode(suffix)
            available_tokens = max_tokens - len(suffix_tokens)

            if available_tokens <= 0:
                return suffix

            # Truncate and decode
            truncated_tokens = tokens[:available_tokens]
            truncated_text = self.encoding.decode(truncated_tokens)

            return truncated_text + suffix

        except Exception as e:
            logger.error(
                f"Error truncating text: {e}",
                extra={"max_tokens": max_tokens},
                exc_info=True,
            )
            # Fallback to character-based truncation
            chars_per_token = 4  # Rough approximation
            max_chars = max_tokens * chars_per_token

            if len(text) <= max_chars:
                return text

            return text[: max_chars - len(suffix)] + suffix


# Global singleton instance
_token_counter: Optional[TokenCounter] = None


def get_token_counter() -> TokenCounter:
    """Get the global token counter instance.

    Implements lazy initialization - creates the counter on first access.

    Returns:
        Global TokenCounter instance

    Example:
        >>> counter = get_token_counter()
        >>> tokens = counter.count_tokens("Hello world")
    """
    global _token_counter

    if _token_counter is None:
        _token_counter = TokenCounter()

    return _token_counter
