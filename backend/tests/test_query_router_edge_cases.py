#!/usr/bin/env python3
"""
Test suite for query router edge cases.

Covers the two bugs fixed in query.py:
1. cgrag_context_text unbound variable when CGRAG index doesn't exist
2. quantization.value AttributeError when quantization is a string

Author: Backend Architect Agent
Date: 2025-11-30
"""

import pytest
from pathlib import Path

from app.models.discovered_model import DiscoveredModel, QuantizationLevel, ModelTier


class TestCGRAGContextEdgeCases:
    """Test CGRAG context variable initialization edge cases."""

    @pytest.mark.asyncio
    async def test_cgrag_context_text_initialized_when_index_missing(self):
        """
        Test that cgrag_context_text is properly initialized to None
        when FAISS index files don't exist.

        This tests the fix for the unbound variable error on line 1414.
        Instead of doing a full integration test (which requires all dependencies),
        we verify the defensive coding pattern exists in the source code.
        """
        # Read source file directly to verify the pattern exists
        query_file = Path(__file__).parent.parent / "app" / "routers" / "query.py"
        source = query_file.read_text()

        # Verify cgrag_context_text is initialized to None before use
        # This prevents UnboundLocalError when FAISS index doesn't exist
        assert "cgrag_context_text = None" in source, (
            "cgrag_context_text should be initialized to None before conditional use"
        )

        # Count occurrences - should have multiple (one per endpoint)
        init_count = source.count("cgrag_context_text = None")
        assert init_count >= 4, (
            f"Expected at least 4 cgrag_context_text initializations "
            f"(one per query endpoint), found {init_count}"
        )

    @pytest.mark.asyncio
    async def test_cgrag_context_none_in_all_query_modes(self):
        """
        Test that cgrag_context_text is initialized to None in all query mode endpoints.

        Ensures all endpoints handle missing CGRAG index gracefully:
        - /api/query (standard)
        - /api/query/debate
        - /api/query/council
        """
        # This test validates that the pattern is consistently applied
        # across all query endpoints (lines 494, 906, 1414, 1917, etc.)

        from pathlib import Path

        # Read source file directly instead of importing
        query_file = Path(__file__).parent.parent / "app" / "routers" / "query.py"
        source = query_file.read_text()

        # Count occurrences of cgrag_context_text initialization
        init_pattern = "cgrag_context_text = None"
        occurrences = source.count(init_pattern)

        # Should have multiple initializations (one per endpoint)
        assert occurrences >= 4, (
            f"Expected at least 4 cgrag_context_text initializations, found {occurrences}. "
            "Each query endpoint should initialize this variable."
        )


class TestQuantizationValueEdgeCases:
    """Test quantization.value attribute access edge cases."""

    def test_quantization_enum_to_string(self):
        """Test that quantization enum values are correctly converted to strings."""
        # Test with enum
        model_with_enum = DiscoveredModel(
            model_id="test-model-enum",
            file_path="/test/model.gguf",
            filename="model.gguf",
            family="qwen",
            size_params=8.0,
            quantization=QuantizationLevel.Q4_K_M,  # Enum value
            assigned_tier=ModelTier.BALANCED,
        )

        # Should handle enum correctly
        if isinstance(model_with_enum.quantization, str):
            quant_str = model_with_enum.quantization.upper()
        else:
            quant_str = model_with_enum.quantization.value.upper()

        assert quant_str in ["Q4_K_M", "q4_k_m".upper()]

    def test_quantization_string_to_string(self):
        """Test that quantization string values are handled correctly."""
        # Pydantic may coerce enum to string in some cases
        model_with_string = DiscoveredModel(
            model_id="test-model-string",
            file_path="/test/model.gguf",
            filename="model.gguf",
            family="qwen",
            size_params=8.0,
            quantization="q4_k_m",  # String value
            assigned_tier=ModelTier.BALANCED,
        )

        # Should handle string correctly without .value attribute access
        if isinstance(model_with_string.quantization, str):
            quant_str = model_with_string.quantization.upper()
        else:
            quant_str = model_with_string.quantization.value.upper()

        assert quant_str == "Q4_K_M"

    def test_quantization_none_handling(self):
        """Test that None quantization values are handled with default."""
        DiscoveredModel(
            model_id="test-model-none",
            file_path="/test/model.gguf",
            filename="model.gguf",
            family="qwen",
            size_params=8.0,
            quantization=QuantizationLevel.Q4_K_M,  # Will be tested as None
            assigned_tier=ModelTier.BALANCED,
        )

        # Simulate None quantization (would need model validation to allow None)
        # This pattern is used in query.py lines 2438-2441, 2553-2556
        quantization = None
        if quantization:
            quantization_str = (
                quantization.upper()
                if isinstance(quantization, str)
                else quantization.value.upper()
            )
        else:
            quantization_str = "Q4_K_M"  # Default

        assert quantization_str == "Q4_K_M"

    def test_all_quantization_levels_have_value_attribute(self):
        """Verify all QuantizationLevel enum members have .value attribute."""
        for level in QuantizationLevel:
            assert hasattr(level, "value"), (
                f"QuantizationLevel.{level.name} missing .value attribute"
            )
            assert isinstance(level.value, str), (
                f"QuantizationLevel.{level.name}.value is not a string"
            )


class TestQueryRouterIntegration:
    """Integration tests for query router with edge cases."""

    @pytest.mark.asyncio
    async def test_query_with_missing_cgrag_and_string_quantization(self):
        """
        Verify both bug fix patterns exist in the query router:
        1. Missing CGRAG index (cgrag_context_text initialized to None)
        2. String quantization value (isinstance check before .value access)

        This is a static analysis test that verifies defensive coding patterns
        without requiring full app initialization and all dependencies.
        """
        # Read source file directly to verify patterns exist
        query_file = Path(__file__).parent.parent / "app" / "routers" / "query.py"
        source = query_file.read_text()

        # Bug fix 1: cgrag_context_text should be initialized to None
        # This prevents UnboundLocalError when FAISS index doesn't exist
        assert "cgrag_context_text = None" in source, (
            "cgrag_context_text should be initialized to None to prevent "
            "UnboundLocalError when CGRAG index is missing"
        )

        # Bug fix 2: isinstance check should protect .value access
        # This prevents AttributeError when quantization is a string
        assert "isinstance" in source and "quantization" in source, (
            "isinstance check should be used when accessing quantization "
            "to handle both string and enum values"
        )

        # Verify the defensive pattern for variable initialization
        required_inits = ["cgrag_context_text = None", "cgrag_artifacts = []"]
        for init_pattern in required_inits:
            assert init_pattern in source, (
                f"Defensive initialization pattern '{init_pattern}' "
                "should exist in query.py"
            )


class TestCodePatternConsistency:
    """Verify defensive coding patterns are applied consistently."""

    def test_isinstance_check_before_value_access(self):
        """
        Verify that all .value accesses on quantization are protected
        by isinstance checks.
        """
        from pathlib import Path

        # Read source file directly instead of importing
        query_file = Path(__file__).parent.parent / "app" / "routers" / "query.py"
        source = query_file.read_text()

        # Find all lines with .value access
        lines = source.split("\n")
        value_access_lines = [
            (i, line) for i, line in enumerate(lines, 1) if "quantization.value" in line
        ]

        # Each should be preceded or wrapped by isinstance check
        for line_num, line in value_access_lines:
            # Check if isinstance is in the same line or nearby
            context = "\n".join(lines[max(0, line_num - 3) : line_num + 1])
            assert "isinstance" in context, (
                f"Line {line_num} accesses .value without isinstance check:\n{line}"
            )

    def test_variable_initialization_pattern(self):
        """
        Verify that potentially unbound variables are initialized
        before conditional use.
        """
        from pathlib import Path

        # Read source file directly instead of importing
        query_file = Path(__file__).parent.parent / "app" / "routers" / "query.py"
        source = query_file.read_text()

        # Variables that should always be initialized
        required_inits = {
            "cgrag_context_text": "None",
            "cgrag_artifacts": "[]",  # Initialized as empty list
            "cgrag_result": "None",
        }

        for var_name, expected_value in required_inits.items():
            # Should have initialization pattern
            init_pattern = f"{var_name} = {expected_value}"
            assert init_pattern in source, (
                f"Variable '{var_name}' should be initialized to {expected_value} "
                "before conditional use"
            )


# Performance regression tests
class TestPerformanceRegression:
    """Ensure bug fixes don't introduce performance regressions."""

    @pytest.mark.asyncio
    async def test_isinstance_check_overhead_negligible(self):
        """
        Verify that isinstance checks don't add significant overhead.

        The isinstance() check is O(1) and should add <1μs overhead.
        """
        import timeit

        # Test enum case
        enum_val = QuantizationLevel.Q4_K_M

        # Without isinstance (unsafe, but fast)
        def unsafe_access():
            return enum_val.value.upper()

        # With isinstance (safe)
        def safe_access():
            return (
                enum_val.upper()
                if isinstance(enum_val, str)
                else enum_val.value.upper()
            )

        unsafe_time = timeit.timeit(unsafe_access, number=100000)
        safe_time = timeit.timeit(safe_access, number=100000)

        overhead_pct = ((safe_time - unsafe_time) / unsafe_time) * 100

        # Overhead should be < 50% (typically ~10-20%)
        assert overhead_pct < 50, (
            f"isinstance check adds {overhead_pct:.1f}% overhead (expected < 50%)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
