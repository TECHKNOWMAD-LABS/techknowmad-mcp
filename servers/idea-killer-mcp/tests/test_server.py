"""Tests for idea-killer-mcp server."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.idea_killer_mcp.server import handle_call_tool, handle_list_tools


@pytest.mark.asyncio
async def test_list_tools():
    tools = await handle_list_tools()
    assert len(tools) == 3
    names = [t.name for t in tools]
    assert "kill_idea" in names
    assert "stress_test_idea" in names
    assert "find_fatal_flaws" in names


@pytest.mark.asyncio
async def test_kill_idea():
    result = await handle_call_tool(
        "kill_idea",
        {
            "idea": "Build a revolutionary new social network for pets",
            "mode": "market",
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "killing_arguments" in data
    assert len(data["killing_arguments"]) > 0
    assert data["killing_arguments"][0]["severity"] > 0
    assert data["mode"] == "market"


@pytest.mark.asyncio
async def test_find_fatal_flaws():
    result = await handle_call_tool(
        "find_fatal_flaws",
        {
            "idea": "Simple fast startup with no moat and easy replication",
            "domain": "business",
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "fatal_flaws" in data
    assert data["domain"] == "business"
    assert data["flaw_count"] > 0
    assert all(f["impact"] > 0 for f in data["fatal_flaws"])
