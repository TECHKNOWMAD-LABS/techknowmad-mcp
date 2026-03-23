"""Extended tests for trace-agent-mcp — targeting 90%+ coverage."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.trace_agent_mcp.server import (
    _get_trace_logic,
    _log_step_logic,
    _start_trace_logic,
    _trace_meta,
    _traces,
    handle_call_tool,
)


@pytest.fixture(autouse=True)
def clear_traces():
    """Clear global trace store before each test."""
    _traces.clear()
    _trace_meta.clear()
    yield
    _traces.clear()
    _trace_meta.clear()


class TestStartTraceLogic:
    def test_basic_start(self):
        result = _start_trace_logic("trace-001", "my-agent")
        assert result["status"] == "initialized"
        assert result["trace_id"] == "trace-001"
        assert result["agent_name"] == "my-agent"
        assert "started_at" in result

    def test_trace_stored_in_memory(self):
        _start_trace_logic("trace-002", "test-agent")
        assert "trace-002" in _traces
        assert _traces["trace-002"] == []

    def test_overwrite_existing_trace(self):
        _start_trace_logic("trace-003", "agent-v1")
        _log_step_logic("trace-003", "step1", {})
        _start_trace_logic("trace-003", "agent-v2")
        # Should be reset
        assert _traces["trace-003"] == []
        assert _trace_meta["trace-003"]["agent_name"] == "agent-v2"

    def test_timestamp_is_iso_format(self):
        result = _start_trace_logic("trace-ts", "agent")
        from datetime import datetime
        # Should parse without error
        datetime.fromisoformat(result["started_at"])


class TestLogStepLogic:
    def test_basic_log(self):
        _start_trace_logic("t1", "agent")
        result = _log_step_logic("t1", "do something", {"key": "val"})
        assert result["status"] == "logged"
        assert result["step_index"] == 0

    def test_multiple_steps_indexed(self):
        _start_trace_logic("t2", "agent")
        _log_step_logic("t2", "step 1", {})
        result = _log_step_logic("t2", "step 2", {})
        assert result["step_index"] == 1
        assert len(_traces["t2"]) == 2

    def test_auto_initialize_missing_trace(self):
        result = _log_step_logic("t-new", "orphan step", {"x": 1})
        assert result["status"] == "logged"
        assert "t-new" in _traces
        assert _trace_meta["t-new"]["agent_name"] == "unknown"

    def test_step_data_stored(self):
        _start_trace_logic("t3", "agent")
        _log_step_logic("t3", "my step", {"input": "hello", "output": "world"})
        step = _traces["t3"][0]
        assert step["step"] == "my step"
        assert step["data"] == {"input": "hello", "output": "world"}


class TestGetTraceLogic:
    def test_missing_trace(self):
        result = _get_trace_logic("nonexistent-trace")
        assert "error" in result
        assert result["total_steps"] == 0

    def test_empty_trace(self):
        _start_trace_logic("empty-trace", "agent")
        result = _get_trace_logic("empty-trace")
        assert result["total_steps"] == 0
        assert result["steps"] == []

    def test_trace_with_steps(self):
        _start_trace_logic("full-trace", "my-agent")
        _log_step_logic("full-trace", "step1", {"a": 1})
        _log_step_logic("full-trace", "step2", {"b": 2})
        result = _get_trace_logic("full-trace")
        assert result["total_steps"] == 2
        assert result["agent_name"] == "my-agent"

    def test_duration_computed(self):
        _start_trace_logic("dur-trace", "agent")
        _log_step_logic("dur-trace", "first", {})
        _log_step_logic("dur-trace", "second", {})
        result = _get_trace_logic("dur-trace")
        # Duration may be 0 ms since steps are nearly instant, but key must exist
        assert "duration_ms" in result
        assert result["duration_ms"] is not None
        assert result["duration_ms"] >= 0

    def test_steps_include_timestamp(self):
        _start_trace_logic("ts-trace", "agent")
        _log_step_logic("ts-trace", "step", {})
        result = _get_trace_logic("ts-trace")
        assert "timestamp" in result["steps"][0]

    def test_corrupted_timestamp_handled(self):
        _traces["bad-trace"] = [{"index": 0, "step": "x", "data": {}, "timestamp": "not-a-date"}]
        _trace_meta["bad-trace"] = {"agent_name": "a", "started_at": "also-bad", "trace_id": "bad-trace"}
        result = _get_trace_logic("bad-trace")
        # Should not raise, duration_ms can be None
        assert result["total_steps"] == 1
        assert result["duration_ms"] is None


@pytest.mark.asyncio
class TestHandleCallToolMCP:
    async def test_full_workflow_via_mcp(self):
        # Start trace
        r1 = await handle_call_tool("start_trace", {"trace_id": "mcp-1", "agent_name": "test-bot"})
        d1 = json.loads(r1[0].text)
        assert d1["status"] == "initialized"

        # Log steps
        r2 = await handle_call_tool("log_step", {"trace_id": "mcp-1", "step": "action-A", "data": {"result": 42}})
        d2 = json.loads(r2[0].text)
        assert d2["step_index"] == 0

        # Retrieve
        r3 = await handle_call_tool("get_trace", {"trace_id": "mcp-1"})
        d3 = json.loads(r3[0].text)
        assert d3["total_steps"] == 1
        assert d3["agent_name"] == "test-bot"

    async def test_get_missing_trace_via_mcp(self):
        result = await handle_call_tool("get_trace", {"trace_id": "does-not-exist"})
        data = json.loads(result[0].text)
        assert "error" in data

    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError):
            await handle_call_tool("nonexistent", {})
