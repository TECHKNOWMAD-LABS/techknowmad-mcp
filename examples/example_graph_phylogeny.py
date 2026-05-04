"""Example: Using graph-forge-mcp + phyloid-evolve for knowledge graphs and evolution.

Demonstrates:
1. Building a knowledge graph and computing centrality
2. Querying graph paths and neighbors
3. Running genetic evolution on a population
4. Building a phylogenetic tree from DNA sequences

Usage:
    uv run python examples/example_graph_phylogeny.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from servers.graph_forge_mcp.server import (
    _compute_centrality_logic,
    _create_graph_logic,
    _query_graph_logic,
)
from servers.phyloid_evolve.server import (
    _compute_phylogeny_logic,
    _evolve_population_logic,
)


def demo_knowledge_graph() -> None:
    """Build and query a technology dependency graph."""
    print("=== Knowledge Graph: Technology Dependencies ===\n")

    nodes = [
        {"id": "Python", "label": "Python"},
        {"id": "FastAPI", "label": "FastAPI"},
        {"id": "Pydantic", "label": "Pydantic"},
        {"id": "SQLAlchemy", "label": "SQLAlchemy"},
        {"id": "PostgreSQL", "label": "PostgreSQL"},
        {"id": "Redis", "label": "Redis"},
        {"id": "Docker", "label": "Docker"},
    ]

    edges = [
        {"source": "FastAPI", "target": "Python", "weight": 1.0},
        {"source": "Pydantic", "target": "Python", "weight": 1.0},
        {"source": "SQLAlchemy", "target": "Python", "weight": 1.0},
        {"source": "SQLAlchemy", "target": "PostgreSQL", "weight": 1.0},
        {"source": "FastAPI", "target": "Pydantic", "weight": 1.0},
        {"source": "FastAPI", "target": "SQLAlchemy", "weight": 1.0},
        {"source": "FastAPI", "target": "Redis", "weight": 0.5},
        {"source": "Docker", "target": "Python", "weight": 0.5},
    ]

    graph = _create_graph_logic(nodes, edges, "tech-stack")
    print(
        f"Graph: {graph['node_count']} nodes, {graph['edge_count']} edges, "
        f"density={graph['density']:.3f}\n"
    )

    # Degree centrality — most connected nodes
    centrality = _compute_centrality_logic({"nodes": nodes, "edges": edges}, "degree")
    print("Degree centrality (most connected first):")
    for node, score in list(centrality["centrality"].items())[:5]:
        print(f"  {node:15s}: {score:.0f} connections")
    print()

    # Path query
    graph_data = {"nodes": nodes, "edges": edges}
    path_result = _query_graph_logic(graph_data, "path:Docker:PostgreSQL")
    if path_result["found"]:
        print(
            f"Path Docker→PostgreSQL: {' → '.join(path_result['result'])} (length {path_result['length']})\n"
        )
    else:
        print("No path found from Docker to PostgreSQL\n")

    # Neighbors of FastAPI
    neighbors = _query_graph_logic(graph_data, "neighbors:FastAPI")
    print(f"FastAPI depends on: {', '.join(sorted(neighbors['result']))}\n")


def demo_evolution() -> None:
    """Run genetic algorithm on a simulated AI agent population."""
    print("=== Genetic Evolution: AI Agent Population ===\n")

    # Population of AI agents with capability genes
    population = [
        {"fitness": 0.3, "genes": [0.2, 0.1, 0.4, 0.3]},
        {"fitness": 0.7, "genes": [0.7, 0.5, 0.6, 0.8]},
        {"fitness": 0.5, "genes": [0.5, 0.4, 0.5, 0.4]},
        {"fitness": 0.9, "genes": [0.9, 0.8, 0.7, 0.9]},
        {"fitness": 0.4, "genes": [0.3, 0.6, 0.2, 0.5]},
        {"fitness": 0.6, "genes": [0.6, 0.7, 0.5, 0.6]},
    ]

    print(f"Initial population: {len(population)} agents")
    avg_initial = sum(a["fitness"] for a in population) / len(population)
    print(f"Initial avg fitness: {avg_initial:.3f}")

    result = _evolve_population_logic(population, generations=20, fitness_fn="mean")

    final_pop = result["population"]
    avg_final = sum(a["fitness"] for a in final_pop) / len(final_pop)
    best = max(final_pop, key=lambda x: x["fitness"])
    print(f"After {result['generations_run']} generations:")
    print(f"  Avg fitness: {avg_final:.3f} (delta: {avg_final - avg_initial:+.3f})")
    print(
        f"  Best agent:  fitness={best['fitness']:.3f}, genes={[round(g, 2) for g in best['genes'][:3]]}...\n"
    )


def demo_phylogeny() -> None:
    """Build a phylogenetic tree from SARS-CoV variants."""
    print("=== Phylogenetic Tree: Simulated Virus Variants ===\n")

    sequences = {
        "Original": "ACGTACGTACGTACGT",
        "Alpha": "ACGTACGTACGTAGGT",
        "Beta": "ACGTACGTACGTAGCT",
        "Delta": "ACGTATGTACGTAGGT",
        "Omicron": "TCGTACGTATGTAGGT",
        "XBB": "TCGTACGTATGCAGGT",
    }

    result = _compute_phylogeny_logic(list(sequences.values()), method="upgma")
    print(f"Sequences: {result['sequence_count']}")
    print(f"Method: {result['method']}")
    print("Pairwise distances (sample):")
    for key, dist in list(result["pairwise_distances"].items())[:5]:
        pair_idx = eval(key)
        names = list(sequences.keys())
        s1 = names[pair_idx[0]]
        s2 = names[pair_idx[1]]
        print(f"  {s1:10s} <-> {s2:10s}: {int(dist)} mutations")
    print()


def main() -> None:
    """Run all graph and evolution examples."""
    demo_knowledge_graph()
    demo_evolution()
    demo_phylogeny()
    print("All examples completed successfully.")


if __name__ == "__main__":
    main()
