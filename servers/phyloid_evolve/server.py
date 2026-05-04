"""phyloid-evolve — Evolutionary and phylogenetic tree operations."""

import json
import random
from typing import Any

import mcp.types as types
from mcp.server import Server

app = Server("phyloid-evolve")

random.seed(42)


def _hamming_distance(s1: str, s2: str) -> int:
    """Compute Hamming distance between two strings."""
    length = max(len(s1), len(s2))
    s1 = s1.ljust(length)
    s2 = s2.ljust(length)
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))


def _evolve_population_logic(
    population: list, generations: int, fitness_fn: str
) -> dict:
    """Core evolution logic."""
    if population is None:
        population = []
    if not fitness_fn:
        fitness_fn = "mean"
    pop = [dict(ind) for ind in population]

    for gen in range(generations):
        # Sort by fitness descending
        pop.sort(key=lambda x: x.get("fitness", 0), reverse=True)

        # Select top 50%
        survivors = pop[: max(1, len(pop) // 2)]

        # Create offspring via crossover
        offspring = []
        for i in range(len(pop) - len(survivors)):
            if len(survivors) >= 2:
                p1 = survivors[i % len(survivors)]
                p2 = survivors[(i + 1) % len(survivors)]
                genes1 = p1.get("genes", [])
                genes2 = p2.get("genes", [])
                length = max(len(genes1), len(genes2))
                genes1 = (genes1 + [0] * length)[:length]
                genes2 = (genes2 + [0] * length)[:length]
                child_genes = [(g1 + g2) / 2.0 for g1, g2 in zip(genes1, genes2)]
            else:
                child_genes = list(survivors[0].get("genes", []))

            # Mutate child
            mutation_rate = 0.1
            child_genes = [g + random.gauss(0, mutation_rate) for g in child_genes]

            # Compute fitness
            if fitness_fn == "max":
                fitness = max(child_genes) if child_genes else 0.0
            elif fitness_fn == "sum":
                fitness = sum(child_genes)
            else:
                fitness = sum(child_genes) / len(child_genes) if child_genes else 0.0

            offspring.append({"genes": child_genes, "fitness": fitness})

        pop = survivors + offspring

        # Update fitness for survivors too
        for ind in survivors:
            genes = ind.get("genes", [])
            if fitness_fn == "max":
                ind["fitness"] = max(genes) if genes else 0.0
            elif fitness_fn == "sum":
                ind["fitness"] = sum(genes)
            else:
                ind["fitness"] = sum(genes) / len(genes) if genes else 0.0

    return {
        "population": pop,
        "generations_run": generations,
        "population_size": len(pop),
    }


_MAX_SEQUENCES = 500  # O(n^2) pairwise distance — cap to prevent DoS


def _compute_phylogeny_logic(sequences: list, method: str) -> dict:
    """Build a simple phylogenetic tree using hierarchical clustering."""
    if not sequences:
        return {"tree": {}, "method": method, "sequence_count": 0}

    # Guard against O(n^2) DoS: truncate to _MAX_SEQUENCES
    sequences = sequences[:_MAX_SEQUENCES]
    n = len(sequences)
    # Compute pairwise distances
    dist = {}
    for i in range(n):
        for j in range(i + 1, n):
            d = _hamming_distance(sequences[i], sequences[j])
            dist[(i, j)] = d
            dist[(j, i)] = d

    # UPGMA-style clustering: iteratively merge closest clusters
    clusters = {i: {"label": sequences[i], "index": i} for i in range(n)}
    active = list(range(n))

    while len(active) > 1:
        # Find closest pair
        min_dist = float("inf")
        merge_i, merge_j = active[0], active[1]
        for a in range(len(active)):
            for b in range(a + 1, len(active)):
                ci, cj = active[a], active[b]
                d = dist.get((ci, cj), float("inf"))
                if d < min_dist:
                    min_dist = d
                    merge_i, merge_j = ci, cj

        # Merge into new cluster
        new_id = max(clusters.keys()) + 1
        clusters[new_id] = {
            "distance": min_dist,
            "children": [clusters[merge_i], clusters[merge_j]],
        }

        # Update distances to new cluster (average)
        active.remove(merge_i)
        active.remove(merge_j)
        for other in active:
            d1 = dist.get((merge_i, other), float("inf"))
            d2 = dist.get((merge_j, other), float("inf"))
            avg = (d1 + d2) / 2.0
            dist[(new_id, other)] = avg
            dist[(other, new_id)] = avg

        active.append(new_id)

    root_id = active[0] if active else 0
    return {
        "tree": clusters.get(root_id, {}),
        "method": method,
        "sequence_count": n,
        "pairwise_distances": {str(k): v for k, v in dist.items() if k[0] < k[1]},
    }


def _mutate_individual_logic(individual: dict, mutation_rate: float) -> dict:
    """Mutate individual's genes by adding Gaussian noise."""
    if individual is None:
        individual = {"genes": [], "fitness": 0.0}
    if mutation_rate is None or mutation_rate < 0:
        mutation_rate = 0.0
    mutated = dict(individual)
    genes = list(individual.get("genes", []))
    mutated_genes = [g + random.gauss(0, mutation_rate) for g in genes]
    mutated["genes"] = mutated_genes

    # Recompute fitness as mean
    if mutated_genes:
        mutated["fitness"] = sum(mutated_genes) / len(mutated_genes)
    return mutated


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="evolve_population",
            description="Evolve a population of individuals over multiple generations using genetic algorithms",
            inputSchema={
                "type": "object",
                "properties": {
                    "population": {
                        "type": "array",
                        "description": "List of individuals, each with 'fitness' (number) and 'genes' (list of numbers)",
                    },
                    "generations": {
                        "type": "integer",
                        "description": "Number of generations to evolve",
                    },
                    "fitness_fn": {
                        "type": "string",
                        "description": "Fitness function: 'max', 'sum', or 'mean'",
                    },
                },
                "required": ["population", "generations", "fitness_fn"],
            },
        ),
        types.Tool(
            name="compute_phylogeny",
            description="Build a phylogenetic tree from biological sequences using pairwise Hamming distances",
            inputSchema={
                "type": "object",
                "properties": {
                    "sequences": {
                        "type": "array",
                        "description": "List of sequence strings to analyze",
                    },
                    "method": {
                        "type": "string",
                        "description": "Clustering method: 'upgma' or 'nj'",
                    },
                },
                "required": ["sequences", "method"],
            },
        ),
        types.Tool(
            name="mutate_individual",
            description="Mutate an individual's genes by adding Gaussian noise scaled by mutation_rate",
            inputSchema={
                "type": "object",
                "properties": {
                    "individual": {
                        "type": "object",
                        "description": "Individual with 'fitness' and 'genes' fields",
                    },
                    "mutation_rate": {
                        "type": "number",
                        "description": "Standard deviation of Gaussian noise to add",
                    },
                },
                "required": ["individual", "mutation_rate"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    if name == "evolve_population":
        result = _evolve_population_logic(
            arguments["population"],
            arguments["generations"],
            arguments["fitness_fn"],
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "compute_phylogeny":
        result = _compute_phylogeny_logic(
            arguments["sequences"],
            arguments["method"],
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "mutate_individual":
        result = _mutate_individual_logic(
            arguments["individual"],
            arguments["mutation_rate"],
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    raise ValueError(f"Unknown tool: {name}")
