"""Tests for edgecraft-benchmark-mcp server."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.edgecraft_benchmark_mcp.server import handle_call_tool, handle_list_tools


@pytest.mark.asyncio
async def test_list_tools():
    tools = await handle_list_tools()
    assert len(tools) == 3
    names = [t.name for t in tools]
    assert "generate_edge_cases" in names
    assert "run_benchmark" in names
    assert "compare_benchmarks" in names


@pytest.mark.asyncio
async def test_generate_edge_cases_integer():
    result = await handle_call_tool(
        "generate_edge_cases",
        {"input_type": "integer", "constraints": {"min": 0, "max": 100}},
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "edge_cases" in data
    assert data["case_count"] > 0
    assert data["input_type"] == "integer"
    # Should have boundary values
    values = [c["value"] for c in data["edge_cases"]]
    assert 0 in values or 100 in values


@pytest.mark.asyncio
async def test_run_benchmark():
    result = await handle_call_tool(
        "run_benchmark",
        {
            "function_spec": "add two integers",
            "test_cases": [
                {"input": 5, "expected": 5},
                {"input": 0, "expected": 0},
                {"input": -1, "expected": 1},
            ],
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["total"] == 3
    assert data["passed"] + data["failed"] == data["total"]
    assert 0.0 <= data["pass_rate"] <= 100.0
