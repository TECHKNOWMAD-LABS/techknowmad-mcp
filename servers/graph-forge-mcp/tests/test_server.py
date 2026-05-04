"""Tests for graph-forge-mcp server."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.graph_forge_mcp.server import handle_call_tool, handle_list_tools

_GRAPH = {
    "nodes": [
        {"id": "A", "label": "Alpha"},
        {"id": "B", "label": "Beta"},
        {"id": "C", "label": "Gamma"},
    ],
    "edges": [
        {"source": "A", "target": "B", "weight": 1.0},
        {"source": "B", "target": "C", "weight": 2.0},
    ],
}


@pytest.mark.asyncio
async def test_list_tools():
    tools = await handle_list_tools()
    assert len(tools) == 3
    names = [t.name for t in tools]
    assert "create_graph" in names
    assert "query_graph" in names
    assert "compute_centrality" in names


@pytest.mark.asyncio
async def test_create_graph():
    result = await handle_call_tool(
        "create_graph",
        {
            "nodes": _GRAPH["nodes"],
            "edges": _GRAPH["edges"],
            "name": "test-graph",
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["node_count"] == 3
    assert data["edge_count"] == 2
    assert "adjacency_list" in data
    assert "B" in data["adjacency_list"]["A"]


@pytest.mark.asyncio
async def test_query_graph_neighbors():
    result = await handle_call_tool(
        "query_graph",
        {"graph_data": _GRAPH, "query": "neighbors:B"},
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "result" in data
    assert set(data["result"]) == {"A", "C"}
