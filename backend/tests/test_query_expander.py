"""Tests for QueryExpander service.

Tests query expansion functionality used in CRAG for improving retrieval
when initial results are evaluated as PARTIAL relevance.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.query_expander import QueryExpander


class TestQueryExpanderInit:
    """Test QueryExpander initialization."""

    def test_default_initialization(self):
        """Test default initialization without custom synonyms."""
        with patch.object(Path, "exists", return_value=False):
            expander = QueryExpander(auto_load=False)

        assert expander.max_synonyms == 2
        assert len(expander.SYNONYMS) > 0  # Has built-in synonyms

    def test_custom_max_synonyms(self):
        """Test initialization with custom max_synonyms."""
        expander = QueryExpander(max_synonyms_per_term=5, auto_load=False)
        assert expander.max_synonyms == 5

    def test_auto_load_disabled(self):
        """Test that auto_load=False prevents loading from default path."""
        expander = QueryExpander(auto_load=False)
        # Should still have default synonyms
        assert "function" in expander.SYNONYMS

    def test_auto_load_with_missing_file(self):
        """Test that missing file doesn't crash with auto_load=True."""
        with patch.object(Path, "exists", return_value=False):
            expander = QueryExpander(auto_load=True)
            assert len(expander.SYNONYMS) > 0

    def test_auto_load_with_existing_file(self):
        """Test loading synonyms from file on init."""
        custom_synonyms = {"llm": ["language model", "neural network"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(custom_synonyms, f)
            temp_path = f.name

        try:
            expander = QueryExpander(synonyms_path=temp_path, auto_load=True)
            assert "llm" in expander.SYNONYMS
            assert expander.SYNONYMS["llm"] == ["language model", "neural network"]
        finally:
            Path(temp_path).unlink()


class TestQueryExpanderExpand:
    """Test query expansion functionality."""

    @pytest.fixture
    def expander(self):
        """Create a QueryExpander instance for testing."""
        return QueryExpander(max_synonyms_per_term=2, auto_load=False)

    def test_expand_single_keyword(self, expander):
        """Test expanding a single keyword."""
        result = expander.expand("function")
        assert "function" in result
        assert "method" in result  # First synonym

    def test_expand_multiple_keywords(self, expander):
        """Test expanding multiple keywords."""
        result = expander.expand("async function")
        terms = set(result.split())

        assert "async" in terms
        assert "function" in terms
        assert "asynchronous" in terms  # Synonym of async
        assert "method" in terms  # Synonym of function

    def test_expand_unknown_words_unchanged(self, expander):
        """Test that unknown words remain unchanged."""
        result = expander.expand("xyzabc123")
        assert "xyzabc123" in result

    def test_expand_mixed_known_unknown(self, expander):
        """Test expansion with mixed known and unknown terms."""
        result = expander.expand("explain xyzabc")
        terms = set(result.split())

        assert "explain" in terms
        assert "xyzabc" in terms
        assert "describe" in terms  # Synonym of explain

    def test_expand_respects_max_synonyms(self):
        """Test that max_synonyms limit is respected."""
        expander = QueryExpander(max_synonyms_per_term=1, auto_load=False)
        result = expander.expand("function")
        terms = result.split()

        # Should have original + at most 1 synonym
        synonym_count = sum(1 for t in terms if t in expander.SYNONYMS.get("function", []))
        assert synonym_count <= 1

    def test_expand_case_insensitive(self, expander):
        """Test that expansion is case-insensitive."""
        result = expander.expand("FUNCTION")
        terms = set(result.split())

        assert "function" in terms  # Lowercased
        assert "method" in terms

    def test_expand_empty_query(self, expander):
        """Test expanding an empty query."""
        result = expander.expand("")
        assert result == ""

    def test_expand_preserves_unique_terms(self, expander):
        """Test that duplicate terms are not added."""
        result = expander.expand("error error")
        terms = result.split()

        # Count occurrences of 'error'
        error_count = terms.count("error")
        assert error_count == 1  # Deduped via set

    def test_expand_returns_string(self, expander):
        """Test that expand always returns a string."""
        result = expander.expand("test query")
        assert isinstance(result, str)


class TestQueryExpanderAddSynonym:
    """Test dynamic synonym addition."""

    def test_add_new_synonym(self):
        """Test adding a new synonym mapping."""
        expander = QueryExpander(auto_load=False)
        expander.add_synonym("rag", ["retrieval augmented generation", "retrieval"])

        assert "rag" in expander.SYNONYMS
        result = expander.expand("rag system")
        assert "retrieval" in result

    def test_add_synonym_lowercase(self):
        """Test that added synonyms are lowercased."""
        expander = QueryExpander(auto_load=False)
        expander.add_synonym("RAG", ["retrieval"])

        assert "rag" in expander.SYNONYMS  # Should be lowercase
        result = expander.expand("rag")
        assert "retrieval" in result

    def test_add_synonym_overwrites_existing(self):
        """Test that adding existing term overwrites."""
        expander = QueryExpander(auto_load=False)
        original_synonyms = expander.SYNONYMS.get("function", []).copy()

        try:
            expander.add_synonym("function", ["foo", "bar"])

            assert expander.SYNONYMS["function"] == ["foo", "bar"]
            assert expander.SYNONYMS["function"] != original_synonyms
        finally:
            # Restore original to not affect other tests (SYNONYMS is class var)
            QueryExpander.SYNONYMS["function"] = original_synonyms


class TestQueryExpanderFileLoading:
    """Test synonym file loading functionality."""

    def test_load_valid_json_file(self):
        """Test loading a valid JSON synonyms file."""
        synonyms = {
            "custom1": ["synonym1", "synonym2"],
            "custom2": ["synonym3"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(synonyms, f)
            temp_path = f.name

        try:
            expander = QueryExpander(auto_load=False)
            expander.load_synonyms_from_file(temp_path)

            assert "custom1" in expander.SYNONYMS
            assert "custom2" in expander.SYNONYMS
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self):
        """Test loading from a nonexistent file raises error."""
        expander = QueryExpander(auto_load=False)

        with pytest.raises(FileNotFoundError):
            expander.load_synonyms_from_file("/nonexistent/path/synonyms.json")

    def test_load_invalid_json_file(self):
        """Test loading invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            temp_path = f.name

        try:
            expander = QueryExpander(auto_load=False)

            with pytest.raises(ValueError, match="Invalid JSON"):
                expander.load_synonyms_from_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_non_dict_json(self):
        """Test loading JSON that's not a dict raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["not", "a", "dict"], f)
            temp_path = f.name

        try:
            expander = QueryExpander(auto_load=False)

            with pytest.raises(ValueError, match="must contain a JSON object"):
                expander.load_synonyms_from_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_merges_with_defaults(self):
        """Test that loaded synonyms merge with defaults."""
        custom = {"newterm": ["newsyn"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(custom, f)
            temp_path = f.name

        try:
            expander = QueryExpander(auto_load=False)
            original_count = len(expander.SYNONYMS)

            expander.load_synonyms_from_file(temp_path)

            assert "newterm" in expander.SYNONYMS
            assert "function" in expander.SYNONYMS  # Original still present
            assert len(expander.SYNONYMS) == original_count + 1
        finally:
            Path(temp_path).unlink()


class TestQueryExpanderBuiltinSynonyms:
    """Test built-in synonym mappings."""

    @pytest.fixture
    def expander(self):
        """Create a QueryExpander with built-in synonyms."""
        return QueryExpander(auto_load=False)

    def test_programming_concepts_present(self, expander):
        """Test that programming concept synonyms are present."""
        programming_terms = ["function", "variable", "error", "class", "async", "loop"]
        for term in programming_terms:
            assert term in expander.SYNONYMS, f"Missing programming term: {term}"

    def test_action_terms_present(self, expander):
        """Test that action term synonyms are present."""
        action_terms = ["explain", "compare", "implement", "optimize", "debug", "test"]
        for term in action_terms:
            assert term in expander.SYNONYMS, f"Missing action term: {term}"

    def test_system_concepts_present(self, expander):
        """Test that system concept synonyms are present."""
        system_terms = ["performance", "memory", "network", "database", "cache", "api"]
        for term in system_terms:
            assert term in expander.SYNONYMS, f"Missing system term: {term}"

    def test_synonyms_are_lists(self, expander):
        """Test that all synonym values are lists."""
        for term, synonyms in expander.SYNONYMS.items():
            assert isinstance(synonyms, list), f"Synonyms for '{term}' should be list"
            assert len(synonyms) > 0, f"Synonyms for '{term}' should not be empty"


class TestQueryExpanderEdgeCases:
    """Test edge cases and special scenarios."""

    def test_expand_with_punctuation(self):
        """Test expansion handles punctuation gracefully."""
        expander = QueryExpander(auto_load=False)
        result = expander.expand("function, error!")

        # Punctuation stays attached to words
        assert "function," in result or "function" in result

    def test_expand_with_extra_whitespace(self):
        """Test expansion handles extra whitespace."""
        expander = QueryExpander(auto_load=False)
        result = expander.expand("  function   error  ")
        terms = result.split()

        # Empty strings should not be in result
        assert "" not in terms

    def test_expand_numeric_only(self):
        """Test expansion with numeric-only input."""
        expander = QueryExpander(auto_load=False)
        result = expander.expand("12345 67890")
        assert "12345" in result
        assert "67890" in result

    def test_expand_special_characters(self):
        """Test expansion with special characters."""
        expander = QueryExpander(auto_load=False)
        result = expander.expand("@#$% function")
        terms = set(result.split())

        assert "@#$%" in terms
        assert "method" in terms  # function expanded

    def test_concurrent_modification_safety(self):
        """Test that modifications don't affect other instances unexpectedly."""
        # Note: SYNONYMS is a class variable, so modifications affect all instances
        # This test documents that behavior
        expander1 = QueryExpander(auto_load=False)
        expander2 = QueryExpander(auto_load=False)

        expander1.add_synonym("unique_term", ["unique_syn"])

        # Both instances share SYNONYMS (class variable behavior)
        assert "unique_term" in expander2.SYNONYMS

        # Clean up to not affect other tests
        del QueryExpander.SYNONYMS["unique_term"]
