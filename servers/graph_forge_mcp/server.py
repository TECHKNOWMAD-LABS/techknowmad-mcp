"""graph-forge-mcp — Forge knowledge graphs."""
import json
from collections import deque
from typing import Any

import mcp.types as types
from mcp.server import Server

app = Server("graph-forge-mcp")


def _build_adjacency(nodes: list, edges: list) -> dict:
    """Build adjacency list from nodes and edges."""
    if nodes is None:
        nodes = []
    if edges is None:
        edges = []
    adj: dict[str, list] = {n["id"]: [] for n in nodes}
    for edge in edges:
        src = edge["source"]
        dst = edge["target"]
        w = edge.get("weight", 1.0)
        if src not in adj:
            adj[src] = []
        if dst not in adj:
            adj[dst] = []
        adj[src].append({"node": dst, "weight": w})
        adj[dst].append({"node": src, "weight": w})
    return adj


def _create_graph_logic(nodes: list, edges: list, name: str) -> dict:
    """Create a graph and return stats."""
    n = len(nodes)
    e = len(edges)
    max_edges = n * (n - 1) / 2 if n > 1 else 1
    density = round(e / max_edges, 4) if max_edges > 0 else 0.0
    adj = _build_adjacency(nodes, edges)
    return {
        "name": name,
        "node_count": n,
        "edge_count": e,
        "density": density,
        "adjacency_list": {k: [nb["node"] for nb in v] for k, v in adj.items()},
        "nodes": nodes,
        "edges": edges,
    }


def _bfs_path(adj: dict, src: str, dst: str) -> list | None:
    """BFS to find shortest path."""
    if src not in adj or dst not in adj:
        return None
    visited = {src}
    queue = deque([[src]])
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == dst:
            return path
        for nb in adj.get(node, []):
            n_id = nb["node"] if isinstance(nb, dict) else nb
            if n_id not in visited:
                visited.add(n_id)
                queue.append(path + [n_id])
    return None


def _query_graph_logic(graph_data: dict, query: str) -> dict:
    """Query a graph."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    adj = _build_adjacency(nodes, edges)

    query_lower = query.lower()

    if query_lower.startswith("neighbors:"):
        node_id = query[len("neighbors:"):]
        neighbors = [nb["node"] if isinstance(nb, dict) else nb for nb in adj.get(node_id, [])]
        return {"query": query, "result": neighbors, "count": len(neighbors)}

    elif query_lower.startswith("path:"):
        parts = query[len("path:"):].split(":", 1)
        if len(parts) == 2:
            src, dst = parts
            path = _bfs_path(adj, src, dst)
            return {"query": query, "result": path, "length": len(path) - 1 if path else None, "found": path is not None}
        return {"query": query, "error": "Invalid path query format, use path:src:dst"}

    elif query_lower.startswith("degree:"):
        node_id = query[len("degree:"):]
        degree = len(adj.get(node_id, []))
        return {"query": query, "result": degree, "node": node_id}

    return {"query": query, "error": f"Unknown query format: {query}"}


def _compute_centrality_logic(graph_data: dict, metric: str) -> dict:
    """Compute centrality for all nodes."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    adj = _build_adjacency(nodes, edges)

    scores: dict[str, float] = {}

    if metric == "degree":
        for node_id in adj:
            scores[node_id] = float(len(adj[node_id]))

    elif metric == "closeness":
        all_nodes = list(adj.keys())
        for node_id in all_nodes:
            # BFS to find distances to all reachable nodes
            distances = {node_id: 0}
            queue = deque([node_id])
            while queue:
                current = queue.popleft()
                for nb in adj.get(current, []):
                    n_id = nb["node"] if isinstance(nb, dict) else nb
                    if n_id not in distances:
                        distances[n_id] = distances[current] + 1
                        queue.append(n_id)
            reachable = len(distances) - 1
            if reachable > 0:
                total_dist = sum(distances.values())
                scores[node_id] = round(reachable / total_dist, 4)
            else:
                scores[node_id] = 0.0
    else:
        # Fallback to degree
        for node_id in adj:
            scores[node_id] = float(len(adj[node_id]))

    sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
    return {"metric": metric, "centrality": sorted_scores, "node_count": len(sorted_scores)}


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_graph",
            description="Create a knowledge graph from nodes and edges, returning stats and adjacency list",
            inputSchema={
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "description": "List of node dicts with 'id' and 'label'",
                    },
                    "edges": {
                        "type": "array",
                        "description": "List of edge dicts with 'source', 'target', 'weight'",
                    },
                    "name": {"type": "string", "description": "Name for the graph"},
                },
                "required": ["nodes", "edges", "name"],
            },
        ),
        types.Tool(
            name="query_graph",
            description="Query a graph: 'neighbors:id', 'path:src:dst', or 'degree:id'",
            inputSchema={
                "type": "object",
                "properties": {
                    "graph_data": {
                        "type": "object",
                        "description": "Graph dict with 'nodes' and 'edges'",
                    },
                    "query": {
                        "type": "string",
                        "description": "Query string: neighbors:id, path:src:dst, degree:id",
                    },
                },
                "required": ["graph_data", "query"],
            },
        ),
        types.Tool(
            name="compute_centrality",
            description="Compute centrality metrics (degree or closeness) for all nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "graph_data": {
                        "type": "object",
                        "description": "Graph dict with 'nodes' and 'edges'",
                    },
                    "metric": {
                        "type": "string",
                        "description": "Centrality metric: 'degree' or 'closeness'",
                    },
                },
                "required": ["graph_data", "metric"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name == "create_graph":
        result = _create_graph_logic(
            arguments["nodes"], arguments["edges"], arguments["name"]
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "query_graph":
        result = _query_graph_logic(arguments["graph_data"], arguments["query"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "compute_centrality":
        result = _compute_centrality_logic(arguments["graph_data"], arguments["metric"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    raise ValueError(f"Unknown tool: {name}")
