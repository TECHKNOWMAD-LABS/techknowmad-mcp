"""Example: Using edgecraft-benchmark-mcp to generate edge cases and run benchmarks.

This script demonstrates how to call the core logic functions directly
without starting the MCP server. Useful for CI, scripting, or integration.

Usage:
    uv run python examples/example_benchmark_edgecases.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from servers.edgecraft_benchmark_mcp.server import (
    _compare_benchmarks_logic,
    _generate_edge_cases_logic,
    _run_benchmark_logic,
)


def main() -> None:
    """Run benchmark edge case examples."""
    print("=== edgecraft-benchmark-mcp example ===\n")

    # 1. Generate integer edge cases with constraints
    print("1. Integer edge cases (0 to 100):")
    result = _generate_edge_cases_logic("integer", {"min": 0, "max": 100})
    print(f"   Found {result['case_count']} edge cases")
    for case in result["edge_cases"][:5]:
        print(f"   - {case['value']:>15} : {case['description']}")
    print()

    # 2. Generate string edge cases
    print("2. String edge cases:")
    result = _generate_edge_cases_logic("string", {})
    for case in result["edge_cases"][:5]:
        print(f"   - {repr(case['value'])[:30]:>32} : {case['description']}")
    print()

    # 3. Run a benchmark
    print("3. Run benchmark — identity function:")
    bench_result = _run_benchmark_logic(
        function_spec="identity(x) — returns x unchanged",
        test_cases=[
            {"input": 42, "expected": 42},
            {"input": "hello", "expected": "hello"},
            {"input": True, "expected": True},
            {"input": 0, "expected": 0},
            {"input": [1, 2], "expected": [1, 2]},
        ],
    )
    print(f"   Total: {bench_result['total']} | Passed: {bench_result['passed']} | "
          f"Failed: {bench_result['failed']} | Pass rate: {bench_result['pass_rate']}%")
    print()

    # 4. Compare two benchmark runs
    print("4. Compare two benchmark runs:")
    bench_a = {"total": 100, "passed": 85, "failed": 15, "pass_rate": 85.0}
    bench_b = {"total": 100, "passed": 92, "failed": 8, "pass_rate": 92.0}
    comparison = _compare_benchmarks_logic(bench_a, bench_b)
    print(f"   Winner: {comparison['overall_winner']} "
          f"(A wins: {comparison['wins_a']}, B wins: {comparison['wins_b']})")
    for metric, data in comparison["metric_comparison"].items():
        print(f"   {metric:12s}: A={data['a']:>6} B={data['b']:>6} => {data['winner']}")
    print()

    print("Example completed successfully.")


if __name__ == "__main__":
    main()
