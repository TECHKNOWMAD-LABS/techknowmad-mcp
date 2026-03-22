# trace-agent-mcp

**Trace Agent Execution Paths MCP Server**

## Overview

trace-agent-mcp provides lightweight tracing infrastructure for AI agent workflows. It records execution steps with timestamps, enabling replay, debugging, and auditing of agent decision sequences.

## Tools

### `start_trace`
Initializes a new trace session.
- `trace_id`: unique identifier for this trace
- `agent_name`: name of the agent being traced
Returns confirmation and initialization timestamp.

### `log_step`
Appends a step to an existing trace.
- `trace_id`: which trace to append to
- `step`: description of the step taken
- `data`: arbitrary dict with step metadata
Returns the step index in the trace.

### `get_trace`
Retrieves all recorded steps for a trace.
- Returns steps array with timestamps
- Returns total step count and duration metrics
- Useful for replay and post-mortem analysis

## Use Cases
- Debugging multi-step agent workflows
- Auditing AI decision sequences
- Performance profiling of agent pipelines
- Reproducing agent behavior for testing
- Compliance logging for AI systems
