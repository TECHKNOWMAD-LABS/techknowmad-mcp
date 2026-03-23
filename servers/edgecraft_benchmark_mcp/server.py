"""edgecraft-benchmark-mcp — Benchmark edge cases."""
from mcp.server import Server
import mcp.types as types
import json
import math
from typing import Any

app = Server("edgecraft-benchmark-mcp")

_EDGE_CASES: dict[str, list[dict]] = {
    "integer": [
        {"value": 0, "description": "zero"},
        {"value": -1, "description": "negative one"},
        {"value": 1, "description": "positive one"},
        {"value": -2147483648, "description": "int32 min"},
        {"value": 2147483647, "description": "int32 max"},
        {"value": -9223372036854775808, "description": "int64 min"},
        {"value": 9223372036854775807, "description": "int64 max"},
        {"value": 2**31, "description": "int32 overflow"},
        {"value": -2**31 - 1, "description": "int32 underflow"},
    ],
    "string": [
        {"value": "", "description": "empty string"},
        {"value": " ", "description": "whitespace only"},
        {"value": "\t\n", "description": "tab and newline"},
        {"value": "a" * 1000, "description": "very long string (1000 chars)"},
        {"value": "a" * 65536, "description": "extremely long string (64KB)"},
        {"value": "'; DROP TABLE users; --", "description": "SQL injection attempt"},
        {"value": "<script>alert('xss')</script>", "description": "XSS injection attempt"},
        {"value": "null", "description": "null as string"},
        {"value": "undefined", "description": "undefined as string"},
        {"value": "\\x00\\x01\\x02", "description": "control characters"},
        {"value": "你好世界", "description": "unicode CJK characters"},
        {"value": "🔥💀🎉", "description": "unicode emoji"},
        {"value": "café résumé naïve", "description": "unicode accented characters"},
    ],
    "list": [
        {"value": [], "description": "empty list"},
        {"value": [None], "description": "single null element"},
        {"value": [1], "description": "single integer element"},
        {"value": list(range(10000)), "description": "large list (10000 elements)"},
        {"value": [[1, 2], [3, 4]], "description": "nested list"},
        {"value": [1, "two", 3.0, None, True], "description": "mixed type list"},
        {"value": [{}], "description": "list with empty dict"},
    ],
    "float": [
        {"value": 0.0, "description": "positive zero"},
        {"value": -0.0, "description": "negative zero"},
        {"value": float("nan"), "description": "NaN (not a number)"},
        {"value": float("inf"), "description": "positive infinity"},
        {"value": float("-inf"), "description": "negative infinity"},
        {"value": 1.7976931348623157e+308, "description": "float64 max"},
        {"value": 5e-324, "description": "float64 min positive"},
        {"value": -1.7976931348623157e+308, "description": "float64 min negative"},
        {"value": 1e-15, "description": "very small positive float"},
    ],
}


def _generate_edge_cases_logic(input_type: str, constraints: dict) -> dict:
    """Generate edge cases for the given input type."""
    if not input_type:
        input_type = "string"
    if constraints is None:
        constraints = {}
    type_lower = input_type.lower()
    base_cases = _EDGE_CASES.get(type_lower, _EDGE_CASES["string"])

    # Apply constraints filtering/addition
    filtered_cases = []
    for case in base_cases:
        value = case["value"]
        skip = False

        if type_lower == "integer" and isinstance(value, int):
            if "min" in constraints and value < constraints["min"]:
                skip = True
            if "max" in constraints and value > constraints["max"]:
                skip = True

        if not skip:
            filtered_cases.append(case)

    # Add constraint boundary cases for integers
    if type_lower == "integer":
        if "min" in constraints:
            filtered_cases.append({"value": constraints["min"], "description": f"constraint min ({constraints['min']})"})
            filtered_cases.append({"value": constraints["min"] - 1, "description": f"just below constraint min"})
        if "max" in constraints:
            filtered_cases.append({"value": constraints["max"], "description": f"constraint max ({constraints['max']})"})
            filtered_cases.append({"value": constraints["max"] + 1, "description": f"just above constraint max"})

    return {
        "input_type": input_type,
        "constraints": constraints,
        "edge_cases": filtered_cases,
        "case_count": len(filtered_cases),
    }


def _evaluate_test_case(test_case: dict) -> dict:
    """Evaluate a single test case against expected."""
    input_val = test_case.get("input")
    expected = test_case.get("expected")

    # Heuristic evaluation
    passes = False
    reasoning = ""

    if expected is None:
        # No expected value — pass if input is not None
        passes = input_val is not None
        reasoning = "No expected value specified — checking input is not None"
    elif isinstance(expected, bool) and isinstance(input_val, bool):
        passes = input_val == expected
        reasoning = f"Boolean comparison: {input_val} == {expected}"
    elif isinstance(expected, (int, float)) and isinstance(input_val, (int, float)):
        # Allow small float tolerance
        try:
            passes = abs(float(input_val) - float(expected)) < 1e-9
        except (TypeError, ValueError):
            passes = input_val == expected
        reasoning = f"Numeric comparison: {input_val} vs {expected}"
    elif isinstance(expected, str) and isinstance(input_val, str):
        passes = input_val == expected
        reasoning = f"String comparison: '{input_val[:20]}' vs '{expected[:20]}'"
    elif isinstance(expected, list) and isinstance(input_val, list):
        passes = len(input_val) == len(expected)
        reasoning = f"List length comparison: {len(input_val)} vs {len(expected)}"
    elif isinstance(expected, dict) and isinstance(input_val, dict):
        passes = set(expected.keys()) <= set(input_val.keys())
        reasoning = f"Dict key subset check"
    else:
        passes = str(input_val) == str(expected)
        reasoning = f"String repr comparison"

    return {
        "input": str(input_val)[:100],
        "expected": str(expected)[:100],
        "result": "PASS" if passes else "FAIL",
        "reasoning": reasoning,
    }


def _run_benchmark_logic(function_spec: str, test_cases: list) -> dict:
    """Simulate benchmark run."""
    if test_cases is None:
        test_cases = []
    if not isinstance(test_cases, list):
        test_cases = list(test_cases) if hasattr(test_cases, "__iter__") else []
    results = []
    for tc in test_cases:
        result = _evaluate_test_case(tc)
        results.append(result)

    total = len(results)
    passed = sum(1 for r in results if r["result"] == "PASS")
    failed = total - passed
    pass_rate = round((passed / total) * 100, 2) if total > 0 else 0.0

    return {
        "function_spec": function_spec[:200],
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "results": results,
    }


def _compare_benchmarks_logic(benchmark_a: dict, benchmark_b: dict) -> dict:
    """Compare two benchmark result dicts."""
    if not isinstance(benchmark_a, dict):
        benchmark_a = {}
    if not isinstance(benchmark_b, dict):
        benchmark_b = {}
    metrics = ["total", "passed", "failed", "pass_rate"]
    comparison = {}
    wins_a = 0
    wins_b = 0

    for metric in metrics:
        val_a = benchmark_a.get(metric, 0)
        val_b = benchmark_b.get(metric, 0)

        if not isinstance(val_a, (int, float)):
            val_a = 0
        if not isinstance(val_b, (int, float)):
            val_b = 0

        # For "failed", lower is better
        if metric == "failed":
            winner = "A" if val_a < val_b else "B" if val_b < val_a else "TIE"
        else:
            winner = "A" if val_a > val_b else "B" if val_b > val_a else "TIE"

        if winner == "A":
            wins_a += 1
        elif winner == "B":
            wins_b += 1

        # Improvement percentage
        if val_a != 0:
            improvement = round(((val_b - val_a) / abs(val_a)) * 100, 2)
        else:
            improvement = 0.0

        comparison[metric] = {
            "a": val_a,
            "b": val_b,
            "winner": winner,
            "b_vs_a_improvement_pct": improvement,
        }

    overall_winner = "A" if wins_a > wins_b else "B" if wins_b > wins_a else "TIE"
    return {
        "metric_comparison": comparison,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "overall_winner": overall_winner,
    }


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_edge_cases",
            description="Generate edge cases for integer, string, list, or float input types",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_type": {
                        "type": "string",
                        "description": "Type to generate edge cases for: integer, string, list, float",
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Optional constraints dict (e.g. {'min': 0, 'max': 100})",
                    },
                },
                "required": ["input_type", "constraints"],
            },
        ),
        types.Tool(
            name="run_benchmark",
            description="Simulate a benchmark run against test cases with pass/fail evaluation",
            inputSchema={
                "type": "object",
                "properties": {
                    "function_spec": {
                        "type": "string",
                        "description": "Description of the function being tested",
                    },
                    "test_cases": {
                        "type": "array",
                        "description": "List of test case dicts with 'input' and 'expected' fields",
                    },
                },
                "required": ["function_spec", "test_cases"],
            },
        ),
        types.Tool(
            name="compare_benchmarks",
            description="Compare two benchmark result dicts and return per-metric winners and improvement percentages",
            inputSchema={
                "type": "object",
                "properties": {
                    "benchmark_a": {
                        "type": "object",
                        "description": "First benchmark result dict",
                    },
                    "benchmark_b": {
                        "type": "object",
                        "description": "Second benchmark result dict",
                    },
                },
                "required": ["benchmark_a", "benchmark_b"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name == "generate_edge_cases":
        result = _generate_edge_cases_logic(arguments["input_type"], arguments["constraints"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "run_benchmark":
        result = _run_benchmark_logic(arguments["function_spec"], arguments["test_cases"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "compare_benchmarks":
        result = _compare_benchmarks_logic(arguments["benchmark_a"], arguments["benchmark_b"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    raise ValueError(f"Unknown tool: {name}")
