"""Extended tests for graph-forge-mcp — targeting 90%+ coverage."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.graph_forge_mcp.server import (
    _bfs_path,
    _build_adjacency,
    _compute_centrality_logic,
    _create_graph_logic,
    _query_graph_logic,
    handle_call_tool,
)


class TestBuildAdjacency:
    def test_simple_undirected(self):
        nodes = [{"id": "A"}, {"id": "B"}]
        edges = [{"source": "A", "target": "B", "weight": 1.0}]
        adj = _build_adjacency(nodes, edges)
        assert "A" in adj
        assert "B" in adj
        assert any(nb["node"] == "B" for nb in adj["A"])
        assert any(nb["node"] == "A" for nb in adj["B"])

    def test_empty_graph(self):
        adj = _build_adjacency([], [])
        assert adj == {}

    def test_default_weight(self):
        nodes = [{"id": "X"}, {"id": "Y"}]
        edges = [{"source": "X", "target": "Y"}]
        adj = _build_adjacency(nodes, edges)
        assert adj["X"][0]["weight"] == 1.0

    def test_auto_creates_missing_node(self):
        nodes = [{"id": "A"}]
        edges = [{"source": "A", "target": "Z", "weight": 1.0}]
        adj = _build_adjacency(nodes, edges)
        assert "Z" in adj


class TestCreateGraphLogic:
    def test_basic_graph(self):
        nodes = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
        edges = [
            {"source": "A", "target": "B", "weight": 1.0},
            {"source": "B", "target": "C", "weight": 1.0},
        ]
        result = _create_graph_logic(nodes, edges, "test-graph")
        assert result["node_count"] == 3
        assert result["edge_count"] == 2
        assert result["name"] == "test-graph"
        assert 0.0 <= result["density"] <= 1.0

    def test_empty_graph(self):
        result = _create_graph_logic([], [], "empty")
        assert result["node_count"] == 0
        assert result["edge_count"] == 0

    def test_single_node(self):
        result = _create_graph_logic([{"id": "A"}], [], "single")
        assert result["node_count"] == 1
        assert result["density"] == 0.0

    def test_complete_graph_density(self):
        nodes = [{"id": str(i)} for i in range(4)]
        edges = [
            {"source": str(i), "target": str(j), "weight": 1.0}
            for i in range(4)
            for j in range(i + 1, 4)
        ]
        result = _create_graph_logic(nodes, edges, "complete")
        assert result["density"] == 1.0

    def test_adjacency_list_in_result(self):
        nodes = [{"id": "A"}, {"id": "B"}]
        edges = [{"source": "A", "target": "B", "weight": 1.0}]
        result = _create_graph_logic(nodes, edges, "test")
        assert "adjacency_list" in result
        assert "B" in result["adjacency_list"]["A"]


class TestBfsPath:
    def setup_method(self):
        """Create a simple linear graph."""
        self.nodes = [{"id": c} for c in ["A", "B", "C", "D"]]
        self.edges = [
            {"source": "A", "target": "B", "weight": 1.0},
            {"source": "B", "target": "C", "weight": 1.0},
            {"source": "C", "target": "D", "weight": 1.0},
        ]
        self.adj = _build_adjacency(self.nodes, self.edges)

    def test_direct_neighbor(self):
        path = _bfs_path(self.adj, "A", "B")
        assert path == ["A", "B"]

    def test_longer_path(self):
        path = _bfs_path(self.adj, "A", "D")
        assert path == ["A", "B", "C", "D"]

    def test_same_source_and_dest(self):
        path = _bfs_path(self.adj, "A", "A")
        assert path == ["A"]

    def test_no_path_disconnected(self):
        nodes = [{"id": "X"}, {"id": "Y"}]
        edges = []
        adj = _build_adjacency(nodes, edges)
        path = _bfs_path(adj, "X", "Y")
        assert path is None

    def test_nonexistent_node(self):
        path = _bfs_path(self.adj, "A", "Z")
        assert path is None


class TestQueryGraphLogic:
    def setup_method(self):
        self.graph_data = {
            "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
            "edges": [
                {"source": "A", "target": "B", "weight": 1.0},
                {"source": "B", "target": "C", "weight": 1.0},
            ],
        }

    def test_neighbors_query(self):
        result = _query_graph_logic(self.graph_data, "neighbors:A")
        assert "B" in result["result"]
        assert result["count"] == 1

    def test_path_query_found(self):
        result = _query_graph_logic(self.graph_data, "path:A:C")
        assert result["found"] is True
        assert result["length"] == 2

    def test_path_query_not_found(self):
        disconnected = {
            "nodes": [{"id": "X"}, {"id": "Y"}],
            "edges": [],
        }
        result = _query_graph_logic(disconnected, "path:X:Y")
        assert result["found"] is False

    def test_path_query_missing_parts(self):
        result = _query_graph_logic(self.graph_data, "path:A")
        assert "error" in result

    def test_degree_query(self):
        result = _query_graph_logic(self.graph_data, "degree:B")
        assert result["result"] == 2

    def test_unknown_query_format(self):
        result = _query_graph_logic(self.graph_data, "foobar:X")
        assert "error" in result

    def test_neighbors_query_case_insensitive(self):
        result = _query_graph_logic(self.graph_data, "NEIGHBORS:A")
        assert "result" in result


class TestComputeCentralityLogic:
    def setup_method(self):
        self.graph_data = {
            "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}, {"id": "D"}],
            "edges": [
                {"source": "A", "target": "B", "weight": 1.0},
                {"source": "A", "target": "C", "weight": 1.0},
                {"source": "A", "target": "D", "weight": 1.0},
                {"source": "B", "target": "C", "weight": 1.0},
            ],
        }

    def test_degree_centrality(self):
        result = _compute_centrality_logic(self.graph_data, "degree")
        assert result["metric"] == "degree"
        # A has 3 connections — highest degree
        assert result["centrality"]["A"] == 3.0

    def test_closeness_centrality(self):
        result = _compute_centrality_logic(self.graph_data, "closeness")
        assert result["metric"] == "closeness"
        # All nodes should have a score
        assert len(result["centrality"]) == 4

    def test_unknown_metric_fallback_to_degree(self):
        result = _compute_centrality_logic(self.graph_data, "betweenness")
        assert "centrality" in result

    def test_sorted_descending(self):
        result = _compute_centrality_logic(self.graph_data, "degree")
        scores = list(result["centrality"].values())
        assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
class TestHandleCallToolMCP:
    async def test_create_graph(self):
        result = await handle_call_tool(
            "create_graph",
            {
                "nodes": [{"id": "A", "label": "Alpha"}, {"id": "B", "label": "Beta"}],
                "edges": [{"source": "A", "target": "B", "weight": 1.0}],
                "name": "test",
            },
        )
        data = json.loads(result[0].text)
        assert data["node_count"] == 2

    async def test_query_graph(self):
        result = await handle_call_tool(
            "query_graph",
            {
                "graph_data": {
                    "nodes": [{"id": "X"}, {"id": "Y"}],
                    "edges": [{"source": "X", "target": "Y", "weight": 1.0}],
                },
                "query": "neighbors:X",
            },
        )
        data = json.loads(result[0].text)
        assert "Y" in data["result"]

    async def test_compute_centrality(self):
        result = await handle_call_tool(
            "compute_centrality",
            {
                "graph_data": {
                    "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
                    "edges": [
                        {"source": "A", "target": "B", "weight": 1.0},
                        {"source": "A", "target": "C", "weight": 1.0},
                    ],
                },
                "metric": "degree",
            },
        )
        data = json.loads(result[0].text)
        assert data["centrality"]["A"] == 2.0

    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError):
            await handle_call_tool("nonexistent", {})
