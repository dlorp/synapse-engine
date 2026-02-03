"""Tests for the TokenCounter service.

This module tests the token counting functionality including:
- Basic token counting
- Batch token counting
- Dict token counting
- Token truncation
- Fallback estimation
- Global singleton access
"""

import pytest
from unittest.mock import patch

from app.services.token_counter import TokenCounter, get_token_counter


class TestTokenCounter:
    """Tests for the TokenCounter class."""

    def test_init_default_encoding(self) -> None:
        """Test TokenCounter initializes with default encoding."""
        counter = TokenCounter()
        assert counter._encoding_name == "cl100k_base"
        assert counter.encoding is not None

    def test_init_custom_encoding(self) -> None:
        """Test TokenCounter initializes with custom encoding."""
        counter = TokenCounter(encoding_name="p50k_base")
        assert counter._encoding_name == "p50k_base"

    def test_init_invalid_encoding_raises(self) -> None:
        """Test TokenCounter raises ValueError for invalid encoding."""
        with pytest.raises(ValueError, match="Invalid encoding name"):
            TokenCounter(encoding_name="invalid_encoding")

    def test_count_tokens_basic(self) -> None:
        """Test basic token counting."""
        counter = TokenCounter()
        # "Hello world" is typically 2 tokens
        count = counter.count_tokens("Hello world")
        assert count >= 2
        assert count < 10  # Sanity check

    def test_count_tokens_empty_string(self) -> None:
        """Test token counting with empty string."""
        counter = TokenCounter()
        assert counter.count_tokens("") == 0

    def test_count_tokens_whitespace(self) -> None:
        """Test token counting with whitespace."""
        counter = TokenCounter()
        count = counter.count_tokens("   ")
        assert count >= 0  # Whitespace may or may not be tokenized

    def test_count_tokens_unicode(self) -> None:
        """Test token counting with unicode characters."""
        counter = TokenCounter()
        count = counter.count_tokens("Hello 世界 🌍")
        assert count > 0

    def test_count_tokens_long_text(self) -> None:
        """Test token counting with longer text."""
        counter = TokenCounter()
        text = "The quick brown fox jumps over the lazy dog. " * 100
        count = counter.count_tokens(text)
        assert count > 100  # Should be significantly more than word count

    def test_count_tokens_batch(self) -> None:
        """Test batch token counting."""
        counter = TokenCounter()
        texts = ["Hello", "World", "Hello World"]
        counts = counter.count_tokens_batch(texts)

        assert len(counts) == 3
        assert all(isinstance(c, int) for c in counts)
        assert all(c > 0 for c in counts)
        # "Hello World" should have at least as many tokens as individual words
        assert counts[2] >= min(counts[0], counts[1])

    def test_count_tokens_batch_empty_list(self) -> None:
        """Test batch token counting with empty list."""
        counter = TokenCounter()
        counts = counter.count_tokens_batch([])
        assert counts == []

    def test_count_tokens_dict(self) -> None:
        """Test dict token counting."""
        counter = TokenCounter()
        text_dict = {
            "system": "You are a helpful assistant",
            "user": "Hello",
            "empty": "",
        }
        counts = counter.count_tokens_dict(text_dict)

        assert len(counts) == 3
        assert "system" in counts
        assert "user" in counts
        assert "empty" in counts
        assert counts["system"] > counts["user"]  # System prompt is longer
        assert counts["empty"] == 0

    def test_estimate_tokens_fallback(self) -> None:
        """Test fallback token estimation."""
        counter = TokenCounter()
        text = "one two three four five"  # 5 words
        estimated = counter._estimate_tokens(text)

        # Should be approximately 5 * 1.3 = 6.5 -> 6 tokens
        assert 4 <= estimated <= 10

    def test_truncate_to_token_limit_no_truncation(self) -> None:
        """Test truncation when text is within limit."""
        counter = TokenCounter()
        text = "Hello world"
        result = counter.truncate_to_token_limit(text, max_tokens=100)
        assert result == text  # Should not be truncated

    def test_truncate_to_token_limit_truncates(self) -> None:
        """Test truncation when text exceeds limit."""
        counter = TokenCounter()
        text = "The quick brown fox jumps over the lazy dog. " * 10
        result = counter.truncate_to_token_limit(text, max_tokens=10)

        assert len(result) < len(text)
        assert result.endswith("...")

    def test_truncate_to_token_limit_custom_suffix(self) -> None:
        """Test truncation with custom suffix."""
        counter = TokenCounter()
        text = "The quick brown fox jumps over the lazy dog. " * 10
        result = counter.truncate_to_token_limit(text, max_tokens=10, suffix=" [...]")

        assert result.endswith(" [...]")

    def test_truncate_to_token_limit_empty_string(self) -> None:
        """Test truncation with empty string."""
        counter = TokenCounter()
        result = counter.truncate_to_token_limit("", max_tokens=10)
        assert result == ""

    def test_truncate_to_token_limit_very_small_limit(self) -> None:
        """Test truncation with very small limit."""
        counter = TokenCounter()
        text = "Hello world"
        # If max_tokens is smaller than suffix, should return just suffix
        result = counter.truncate_to_token_limit(text, max_tokens=1)
        assert "..." in result or len(result) < len(text)


class TestGetTokenCounter:
    """Tests for the get_token_counter singleton function."""

    def test_get_token_counter_returns_instance(self) -> None:
        """Test get_token_counter returns a TokenCounter instance."""
        counter = get_token_counter()
        assert isinstance(counter, TokenCounter)

    def test_get_token_counter_returns_same_instance(self) -> None:
        """Test get_token_counter returns same instance (singleton)."""
        counter1 = get_token_counter()
        counter2 = get_token_counter()
        assert counter1 is counter2

    def test_get_token_counter_is_functional(self) -> None:
        """Test singleton instance can count tokens."""
        counter = get_token_counter()
        count = counter.count_tokens("Hello world")
        assert count > 0


class TestTokenCounterErrorHandling:
    """Tests for TokenCounter error handling."""

    def test_count_tokens_with_encoding_error(self) -> None:
        """Test that encoding errors fall back to estimation."""
        counter = TokenCounter()

        # Mock the encoding to raise an error
        with patch.object(
            counter.encoding, "encode", side_effect=Exception("Encoding error")
        ):
            # Should fall back to estimation
            result = counter.count_tokens("Hello world")
            assert result > 0  # Should still return a value

    def test_truncate_with_encoding_error(self) -> None:
        """Test that truncation errors fall back to character-based truncation."""
        counter = TokenCounter()

        # Mock the encoding to raise an error
        with patch.object(
            counter.encoding, "encode", side_effect=Exception("Encoding error")
        ):
            text = "Hello world " * 100
            result = counter.truncate_to_token_limit(text, max_tokens=10)
            # Should still return truncated text
            assert len(result) < len(text)
