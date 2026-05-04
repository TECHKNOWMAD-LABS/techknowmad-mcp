"""trace-agent-mcp — Trace agent execution paths."""

import json
from datetime import datetime, timezone
from typing import Any

import mcp.types as types
from mcp.server import Server

app = Server("trace-agent-mcp")

# Module-level in-memory trace storage
_traces: dict[str, list] = {}
_trace_meta: dict[str, dict] = {}


def _start_trace_logic(trace_id: str, agent_name: str) -> dict:
    """Initialize a new agent execution trace in the in-memory store.

    Creates an empty step list for the trace_id. If a trace with the same
    trace_id already exists, it is overwritten (reset).

    Args:
        trace_id: Unique string identifier for this trace session.
        agent_name: Human-readable name of the agent being traced.

    Returns:
        Dict with keys: status, trace_id, agent_name, started_at (ISO 8601 UTC).
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    _traces[trace_id] = []
    _trace_meta[trace_id] = {
        "agent_name": agent_name,
        "started_at": timestamp,
        "trace_id": trace_id,
    }
    return {
        "status": "initialized",
        "trace_id": trace_id,
        "agent_name": agent_name,
        "started_at": timestamp,
    }


def _log_step_logic(trace_id: str, step: str, data: dict) -> dict:
    """Append a step to an existing trace."""
    if trace_id not in _traces:
        # Auto-initialize if not present
        _traces[trace_id] = []
        _trace_meta[trace_id] = {
            "agent_name": "unknown",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
        }

    timestamp = datetime.now(timezone.utc).isoformat()
    step_index = len(_traces[trace_id])
    step_record = {
        "index": step_index,
        "step": step,
        "data": data,
        "timestamp": timestamp,
    }
    _traces[trace_id].append(step_record)

    return {
        "status": "logged",
        "trace_id": trace_id,
        "step_index": step_index,
        "timestamp": timestamp,
    }


def _get_trace_logic(trace_id: str) -> dict:
    """Retrieve all steps for a trace."""
    if trace_id not in _traces:
        return {
            "trace_id": trace_id,
            "error": "Trace not found",
            "steps": [],
            "total_steps": 0,
        }

    steps = _traces[trace_id]
    meta = _trace_meta.get(trace_id, {})

    # Compute duration if possible
    duration_ms = None
    if steps and meta.get("started_at"):
        try:
            start = datetime.fromisoformat(meta["started_at"])
            last = datetime.fromisoformat(steps[-1]["timestamp"])
            duration_ms = int((last - start).total_seconds() * 1000)
        except (ValueError, KeyError):
            pass

    return {
        "trace_id": trace_id,
        "agent_name": meta.get("agent_name", "unknown"),
        "started_at": meta.get("started_at"),
        "steps": steps,
        "total_steps": len(steps),
        "duration_ms": duration_ms,
    }


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="start_trace",
            description="Initialize a new agent execution trace",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_id": {
                        "type": "string",
                        "description": "Unique identifier for this trace",
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent being traced",
                    },
                },
                "required": ["trace_id", "agent_name"],
            },
        ),
        types.Tool(
            name="log_step",
            description="Append an execution step to an existing trace",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_id": {"type": "string", "description": "Trace to append to"},
                    "step": {
                        "type": "string",
                        "description": "Description of the step taken",
                    },
                    "data": {
                        "type": "object",
                        "description": "Arbitrary metadata for this step",
                    },
                },
                "required": ["trace_id", "step", "data"],
            },
        ),
        types.Tool(
            name="get_trace",
            description="Retrieve all recorded steps for a trace with timestamps and metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_id": {
                        "type": "string",
                        "description": "Trace ID to retrieve",
                    },
                },
                "required": ["trace_id"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    if name == "start_trace":
        result = _start_trace_logic(arguments["trace_id"], arguments["agent_name"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "log_step":
        result = _log_step_logic(
            arguments["trace_id"], arguments["step"], arguments["data"]
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "get_trace":
        result = _get_trace_logic(arguments["trace_id"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    raise ValueError(f"Unknown tool: {name}")
