"""Tests for forge-generate-mcp server."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.forge_generate_mcp.server import handle_call_tool, handle_list_tools


@pytest.mark.asyncio
async def test_list_tools():
    tools = await handle_list_tools()
    assert len(tools) == 3
    names = [t.name for t in tools]
    assert "generate_code" in names
    assert "generate_schema" in names
    assert "generate_tests" in names


@pytest.mark.asyncio
async def test_generate_code():
    result = await handle_call_tool(
        "generate_code",
        {
            "spec": "Create a service to process and validate user data",
            "language": "python",
            "style": "class-based",
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "code" in data
    assert len(data["code"]) > 10
    assert data["language"] == "python"


@pytest.mark.asyncio
async def test_generate_tests():
    code = """
def calculate_sum(a, b):
    return a + b

def validate_input(data):
    return bool(data)
"""
    result = await handle_call_tool(
        "generate_tests",
        {"code": code, "framework": "pytest", "count": 3},
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "test_file" in data
    assert data["test_count"] >= 1
    assert "pytest" in data["test_file"] or "def test_" in data["test_file"]
