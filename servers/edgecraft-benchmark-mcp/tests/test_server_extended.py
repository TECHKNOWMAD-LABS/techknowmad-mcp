"""Extended tests for edgecraft-benchmark-mcp — targeting 90%+ coverage."""
import json
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.edgecraft_benchmark_mcp.server import (
    _compare_benchmarks_logic,
    _evaluate_test_case,
    _generate_edge_cases_logic,
    _run_benchmark_logic,
    handle_call_tool,
)


class TestGenerateEdgeCasesLogic:
    def test_integer_no_constraints(self):
        result = _generate_edge_cases_logic("integer", {})
        assert result["input_type"] == "integer"
        assert result["case_count"] > 0
        values = [c["value"] for c in result["edge_cases"]]
        assert 0 in values

    def test_integer_with_min_only(self):
        result = _generate_edge_cases_logic("integer", {"min": 10})
        values = [c["value"] for c in result["edge_cases"]]
        assert 10 in values
        assert 9 in values  # just below min

    def test_integer_with_max_only(self):
        result = _generate_edge_cases_logic("integer", {"max": 50})
        values = [c["value"] for c in result["edge_cases"]]
        assert 50 in values
        assert 51 in values  # just above max

    def test_integer_with_both_constraints(self):
        result = _generate_edge_cases_logic("integer", {"min": 0, "max": 100})
        values = [c["value"] for c in result["edge_cases"]]
        assert 0 in values
        assert 100 in values
        # Values below min should be filtered
        assert all(v >= 0 for v in values if isinstance(v, int) and v not in [0 - 1, 100 + 1])

    def test_string_type(self):
        result = _generate_edge_cases_logic("string", {})
        assert result["input_type"] == "string"
        assert result["case_count"] > 0
        descriptions = [c["description"] for c in result["edge_cases"]]
        assert any("empty" in d for d in descriptions)

    def test_list_type(self):
        result = _generate_edge_cases_logic("list", {})
        assert result["input_type"] == "list"
        values = [str(c["value"]) for c in result["edge_cases"]]
        assert any("[]" in v for v in values)

    def test_float_type(self):
        result = _generate_edge_cases_logic("float", {})
        assert result["input_type"] == "float"
        values = [c["value"] for c in result["edge_cases"]]
        assert any(math.isnan(v) for v in values if isinstance(v, float))
        assert any(math.isinf(v) for v in values if isinstance(v, float))

    def test_unknown_type_falls_back_to_string(self):
        result = _generate_edge_cases_logic("unknown_type_xyz", {})
        # Should fall back to string edge cases
        assert result["case_count"] > 0

    def test_uppercase_type_works(self):
        result = _generate_edge_cases_logic("INTEGER", {})
        assert result["case_count"] > 0

    def test_constraints_returned_in_result(self):
        constraints = {"min": 5, "max": 50}
        result = _generate_edge_cases_logic("integer", constraints)
        assert result["constraints"] == constraints


class TestEvaluateTestCase:
    def test_boolean_match(self):
        result = _evaluate_test_case({"input": True, "expected": True})
        assert result["result"] == "PASS"

    def test_boolean_mismatch(self):
        result = _evaluate_test_case({"input": True, "expected": False})
        assert result["result"] == "FAIL"

    def test_int_match(self):
        result = _evaluate_test_case({"input": 42, "expected": 42})
        assert result["result"] == "PASS"

    def test_float_tolerance(self):
        result = _evaluate_test_case({"input": 1.0000000001, "expected": 1.0})
        assert result["result"] == "PASS"

    def test_float_mismatch(self):
        result = _evaluate_test_case({"input": 1.5, "expected": 2.0})
        assert result["result"] == "FAIL"

    def test_string_match(self):
        result = _evaluate_test_case({"input": "hello", "expected": "hello"})
        assert result["result"] == "PASS"

    def test_string_mismatch(self):
        result = _evaluate_test_case({"input": "hello", "expected": "world"})
        assert result["result"] == "FAIL"

    def test_list_same_length(self):
        result = _evaluate_test_case({"input": [1, 2, 3], "expected": [4, 5, 6]})
        assert result["result"] == "PASS"  # list length comparison

    def test_list_different_length(self):
        result = _evaluate_test_case({"input": [1, 2], "expected": [1]})
        assert result["result"] == "FAIL"

    def test_dict_subset_keys(self):
        result = _evaluate_test_case({"input": {"a": 1, "b": 2}, "expected": {"a": 0}})
        assert result["result"] == "PASS"  # expected keys are subset of input

    def test_dict_missing_keys(self):
        result = _evaluate_test_case({"input": {"a": 1}, "expected": {"a": 0, "b": 1}})
        assert result["result"] == "FAIL"

    def test_no_expected_none_input(self):
        result = _evaluate_test_case({"input": None, "expected": None})
        assert result["result"] == "FAIL"  # input is None, passes = False

    def test_no_expected_non_none_input(self):
        result = _evaluate_test_case({"input": "something"})
        assert result["result"] == "PASS"

    def test_type_mismatch_fallback(self):
        result = _evaluate_test_case({"input": [1, 2, 3], "expected": "hello"})
        # Falls through to str repr comparison
        assert "result" in result

    def test_long_input_truncated_in_output(self):
        long_val = "x" * 200
        result = _evaluate_test_case({"input": long_val, "expected": long_val})
        assert len(result["input"]) <= 100


class TestRunBenchmarkLogic:
    def test_empty_test_cases(self):
        result = _run_benchmark_logic("some function", [])
        assert result["total"] == 0
        assert result["pass_rate"] == 0.0

    def test_all_pass(self):
        cases = [{"input": i, "expected": i} for i in range(5)]
        result = _run_benchmark_logic("identity", cases)
        assert result["passed"] == 5
        assert result["pass_rate"] == 100.0

    def test_mixed_results(self):
        cases = [
            {"input": 1, "expected": 1},
            {"input": "a", "expected": "b"},
        ]
        result = _run_benchmark_logic("mixed", cases)
        assert result["total"] == 2
        assert result["passed"] + result["failed"] == 2

    def test_long_function_spec_truncated(self):
        spec = "x" * 500
        result = _run_benchmark_logic(spec, [])
        assert len(result["function_spec"]) <= 200


class TestCompareBenchmarksLogic:
    def test_a_wins_all(self):
        a = {"total": 100, "passed": 90, "failed": 10, "pass_rate": 90.0}
        b = {"total": 100, "passed": 50, "failed": 50, "pass_rate": 50.0}
        result = _compare_benchmarks_logic(a, b)
        assert result["overall_winner"] == "A"

    def test_b_wins_all(self):
        a = {"total": 100, "passed": 50, "failed": 50, "pass_rate": 50.0}
        b = {"total": 100, "passed": 90, "failed": 10, "pass_rate": 90.0}
        result = _compare_benchmarks_logic(a, b)
        assert result["overall_winner"] == "B"

    def test_tie(self):
        a = {"total": 100, "passed": 70, "failed": 30, "pass_rate": 70.0}
        b = {"total": 100, "passed": 70, "failed": 30, "pass_rate": 70.0}
        result = _compare_benchmarks_logic(a, b)
        assert result["overall_winner"] == "TIE"

    def test_missing_keys_handled(self):
        a = {}
        b = {}
        result = _compare_benchmarks_logic(a, b)
        assert "overall_winner" in result

    def test_non_numeric_values_handled(self):
        a = {"total": "bad", "passed": None, "failed": [], "pass_rate": "100%"}
        b = {"total": 10, "passed": 8, "failed": 2, "pass_rate": 80.0}
        result = _compare_benchmarks_logic(a, b)
        assert "overall_winner" in result

    def test_improvement_pct_calculated(self):
        a = {"total": 100, "passed": 50, "failed": 50, "pass_rate": 50.0}
        b = {"total": 100, "passed": 100, "failed": 0, "pass_rate": 100.0}
        result = _compare_benchmarks_logic(a, b)
        assert result["metric_comparison"]["pass_rate"]["b_vs_a_improvement_pct"] == 100.0

    def test_a_zero_base_no_division_error(self):
        a = {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0}
        b = {"total": 10, "passed": 5, "failed": 5, "pass_rate": 50.0}
        result = _compare_benchmarks_logic(a, b)
        assert "overall_winner" in result


@pytest.mark.asyncio
class TestHandleCallToolMCP:
    async def test_generate_edge_cases_string(self):
        result = await handle_call_tool("generate_edge_cases", {"input_type": "string", "constraints": {}})
        data = json.loads(result[0].text)
        assert data["input_type"] == "string"

    async def test_generate_edge_cases_float(self):
        result = await handle_call_tool("generate_edge_cases", {"input_type": "float", "constraints": {}})
        data = json.loads(result[0].text)
        assert data["input_type"] == "float"

    async def test_generate_edge_cases_list(self):
        result = await handle_call_tool("generate_edge_cases", {"input_type": "list", "constraints": {}})
        data = json.loads(result[0].text)
        assert data["case_count"] > 0

    async def test_compare_benchmarks_via_mcp(self):
        result = await handle_call_tool(
            "compare_benchmarks",
            {
                "benchmark_a": {"total": 10, "passed": 8, "failed": 2, "pass_rate": 80.0},
                "benchmark_b": {"total": 10, "passed": 6, "failed": 4, "pass_rate": 60.0},
            },
        )
        data = json.loads(result[0].text)
        assert data["overall_winner"] == "A"

    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_call_tool("nonexistent_tool", {})
