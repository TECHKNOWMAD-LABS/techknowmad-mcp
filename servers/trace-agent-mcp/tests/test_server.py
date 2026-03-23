"""Tests for trace-agent-mcp server."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.trace_agent_mcp.server import handle_call_tool, handle_list_tools


@pytest.mark.asyncio
async def test_list_tools():
    tools = await handle_list_tools()
    assert len(tools) == 3
    names = [t.name for t in tools]
    assert "start_trace" in names
    assert "log_step" in names
    assert "get_trace" in names


@pytest.mark.asyncio
async def test_start_trace():
    result = await handle_call_tool(
        "start_trace",
        {"trace_id": "test-trace-001", "agent_name": "test-agent"},
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["status"] == "initialized"
    assert data["trace_id"] == "test-trace-001"
    assert data["agent_name"] == "test-agent"


@pytest.mark.asyncio
async def test_log_and_get_trace():
    trace_id = "test-trace-002"
    await handle_call_tool("start_trace", {"trace_id": trace_id, "agent_name": "bot"})

    log_result = await handle_call_tool(
        "log_step",
        {
            "trace_id": trace_id,
            "step": "retrieved context",
            "data": {"tokens": 512, "source": "vector-db"},
        },
    )
    log_data = json.loads(log_result[0].text)
    assert log_data["step_index"] == 0

    get_result = await handle_call_tool("get_trace", {"trace_id": trace_id})
    trace_data = json.loads(get_result[0].text)
    assert trace_data["total_steps"] == 1
    assert trace_data["steps"][0]["step"] == "retrieved context"
    assert trace_data["agent_name"] == "bot"
