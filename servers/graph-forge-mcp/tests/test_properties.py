"""Property-based tests for graph-forge-mcp using Hypothesis."""
import sys
import os

from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.graph_forge_mcp.server import (
    _compute_centrality_logic,
    _create_graph_logic,
    _query_graph_logic,
)

node_id_st = st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=5)


def _make_nodes(ids):
    return [{"id": i, "label": f"Node {i}"} for i in ids]


def _make_edges(ids):
    if len(ids) < 2:
        return []
    edges = []
    for i in range(len(ids) - 1):
        edges.append({"source": ids[i], "target": ids[i + 1], "weight": 1.0})
    return edges


class TestGraphProperties:
    @given(
        ids=st.lists(node_id_st, min_size=1, max_size=10, unique=True),
        name=st.text(min_size=1, max_size=20),
    )
    def test_node_count_matches_input(self, ids, name):
        """node_count always matches number of nodes."""
        nodes = _make_nodes(ids)
        result = _create_graph_logic(nodes, [], name)
        assert result["node_count"] == len(ids)

    @given(
        ids=st.lists(node_id_st, min_size=2, max_size=10, unique=True),
    )
    def test_density_between_0_and_1(self, ids):
        """density is always in [0, 1]."""
        nodes = _make_nodes(ids)
        edges = _make_edges(ids)
        result = _create_graph_logic(nodes, edges, "g")
        assert 0.0 <= result["density"] <= 1.0

    @given(
        ids=st.lists(node_id_st, min_size=1, max_size=8, unique=True),
    )
    def test_degree_centrality_non_negative(self, ids):
        """Degree centrality scores are always non-negative."""
        nodes = _make_nodes(ids)
        edges = _make_edges(ids)
        graph_data = {"nodes": nodes, "edges": edges}
        result = _compute_centrality_logic(graph_data, "degree")
        for score in result["centrality"].values():
            assert score >= 0.0

    @given(
        ids=st.lists(node_id_st, min_size=2, max_size=8, unique=True),
    )
    def test_closeness_centrality_non_negative(self, ids):
        """Closeness centrality scores are always in [0, 1]."""
        nodes = _make_nodes(ids)
        edges = _make_edges(ids)
        graph_data = {"nodes": nodes, "edges": edges}
        result = _compute_centrality_logic(graph_data, "closeness")
        for score in result["centrality"].values():
            assert 0.0 <= score <= 1.0

    @given(
        ids=st.lists(node_id_st, min_size=2, max_size=10, unique=True),
    )
    def test_degree_query_returns_integer(self, ids):
        """degree: query always returns an integer >= 0."""
        nodes = _make_nodes(ids)
        edges = _make_edges(ids)
        graph_data = {"nodes": nodes, "edges": edges}
        result = _query_graph_logic(graph_data, f"degree:{ids[0]}")
        assert isinstance(result["result"], int)
        assert result["result"] >= 0

    @given(
        ids=st.lists(node_id_st, min_size=3, max_size=8, unique=True),
    )
    def test_path_in_linear_graph_exists(self, ids):
        """In a linear graph, path from first to last node always exists."""
        nodes = _make_nodes(ids)
        edges = _make_edges(ids)
        graph_data = {"nodes": nodes, "edges": edges}
        result = _query_graph_logic(graph_data, f"path:{ids[0]}:{ids[-1]}")
        assert result["found"] is True
        assert result["length"] == len(ids) - 1
