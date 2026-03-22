# edgecraft-benchmark-mcp

**Benchmark Edge Cases MCP Server**

## Overview

edgecraft-benchmark-mcp generates comprehensive edge case test suites and benchmarks software behavior at boundary conditions. It focuses on catching the cases that typical happy-path tests miss.

## Tools

### `generate_edge_cases`
Generates edge cases for common input types:
- **integer**: min, max, zero, negative, overflow boundary values
- **string**: empty, whitespace, very long, unicode, SQL injection, XSS
- **list**: empty list, single element, large list, nested
- **float**: NaN, +Infinity, -Infinity, zero, negative, very small
Returns list of edge case values with descriptions.

### `run_benchmark`
Simulates a benchmark run against test cases.
- Each test case has `input` and `expected` values
- Evaluates pass/fail using type and equality heuristics
- Returns: total, passed, failed, pass_rate, per-case results

### `compare_benchmarks`
Compares two benchmark result dicts.
- Computes improvement percentages per metric
- Returns per-metric winner and overall winner
- Useful for before/after performance comparisons

## Use Cases
- Automated edge case generation for CI pipelines
- Regression testing at boundary conditions
- Security input validation testing
- Performance comparison between implementations
- Robustness scoring for production systems
