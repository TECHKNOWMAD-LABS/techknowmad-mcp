# graph-forge-mcp

**Forge Knowledge Graphs MCP Server**

## Overview

graph-forge-mcp provides tools for creating, querying, and analyzing knowledge graphs. It represents entities as nodes and relationships as weighted edges, enabling graph traversal and centrality analysis.

## Tools

### `create_graph`
Creates a graph from nodes and edges.
- Nodes: list of dicts with `id` and `label`
- Edges: list of dicts with `source`, `target`, and `weight`
- Returns: node count, edge count, density, adjacency list

### `query_graph`
Queries a graph using simple query syntax:
- `neighbors:{node_id}` — returns all neighbors of a node
- `path:{src}:{dst}` — finds a path between two nodes (BFS)
- `degree:{node_id}` — returns the degree (edge count) of a node

### `compute_centrality`
Computes centrality metrics for all nodes:
- **degree**: number of edges per node
- **closeness**: inverse of average shortest path length (BFS-based)
Returns dict of node_id → score, sorted descending.

## Use Cases
- Knowledge graph construction and exploration
- Ontology modeling
- Relationship network analysis
- Dependency graph analysis
