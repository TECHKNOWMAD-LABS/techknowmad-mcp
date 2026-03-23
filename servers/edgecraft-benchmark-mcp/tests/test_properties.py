"""Property-based tests for edgecraft-benchmark-mcp using Hypothesis."""
import sys
import os

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.edgecraft_benchmark_mcp.server import (
    _compare_benchmarks_logic,
    _evaluate_test_case,
    _generate_edge_cases_logic,
    _run_benchmark_logic,
)


class TestEdgeCaseProperties:
    @given(
        input_type=st.sampled_from(["integer", "string", "list", "float", "unknown"]),
    )
    def test_always_returns_dict_with_required_keys(self, input_type):
        """Output always has required keys regardless of input_type."""
        result = _generate_edge_cases_logic(input_type, {})
        assert "input_type" in result
        assert "edge_cases" in result
        assert "case_count" in result
        assert isinstance(result["edge_cases"], list)

    @given(
        min_val=st.integers(min_value=-1000, max_value=0),
        max_val=st.integers(min_value=1, max_value=1000),
    )
    def test_case_count_non_negative(self, min_val, max_val):
        """case_count is always non-negative."""
        result = _generate_edge_cases_logic("integer", {"min": min_val, "max": max_val})
        assert result["case_count"] >= 0
        assert result["case_count"] == len(result["edge_cases"])

    @given(st.text(min_size=0, max_size=200))
    def test_no_crash_on_any_string_type(self, arbitrary_type):
        """Never crashes on any string input_type."""
        result = _generate_edge_cases_logic(arbitrary_type, {})
        assert "edge_cases" in result


class TestBenchmarkProperties:
    @given(
        test_cases=st.lists(
            st.fixed_dictionaries({
                "input": st.one_of(st.integers(), st.text(max_size=20), st.booleans(), st.none()),
                "expected": st.one_of(st.integers(), st.text(max_size=20), st.booleans(), st.none()),
            }),
            max_size=20,
        )
    )
    def test_passed_plus_failed_equals_total(self, test_cases):
        """passed + failed == total always."""
        result = _run_benchmark_logic("test", test_cases)
        assert result["passed"] + result["failed"] == result["total"]

    @given(
        test_cases=st.lists(
            st.fixed_dictionaries({
                "input": st.integers(min_value=-100, max_value=100),
                "expected": st.integers(min_value=-100, max_value=100),
            }),
            min_size=1,
            max_size=50,
        )
    )
    def test_pass_rate_in_valid_range(self, test_cases):
        """pass_rate is always in [0, 100]."""
        result = _run_benchmark_logic("test", test_cases)
        assert 0.0 <= result["pass_rate"] <= 100.0

    @given(
        n=st.integers(min_value=1, max_value=50),
        val=st.one_of(st.integers(), st.text(max_size=50)),
    )
    def test_identical_inputs_always_pass(self, n, val):
        """If input == expected, test always PASSes."""
        cases = [{"input": val, "expected": val} for _ in range(n)]
        result = _run_benchmark_logic("identity", cases)
        assert result["passed"] == n
        assert result["pass_rate"] == 100.0


class TestCompareProperties:
    @given(
        total=st.integers(min_value=0, max_value=1000),
        passed=st.integers(min_value=0, max_value=1000),
    )
    def test_compare_winner_consistent(self, total, passed):
        """overall_winner is always A, B, or TIE."""
        a = {"total": total, "passed": passed, "failed": max(0, total - passed), "pass_rate": 50.0}
        b = {"total": total, "passed": passed, "failed": max(0, total - passed), "pass_rate": 50.0}
        result = _compare_benchmarks_logic(a, b)
        assert result["overall_winner"] in ("A", "B", "TIE")

    @given(
        pass_rate_a=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        pass_rate_b=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    )
    def test_wins_sum_consistent(self, pass_rate_a, pass_rate_b):
        """wins_a + wins_b <= number of metrics."""
        a = {"total": 10, "passed": 5, "failed": 5, "pass_rate": pass_rate_a}
        b = {"total": 10, "passed": 5, "failed": 5, "pass_rate": pass_rate_b}
        result = _compare_benchmarks_logic(a, b)
        assert result["wins_a"] + result["wins_b"] <= 4  # 4 metrics
