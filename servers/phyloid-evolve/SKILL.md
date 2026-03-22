# phyloid-evolve

**Evolutionary and Phylogenetic Tree Operations MCP Server**

## Overview

phyloid-evolve provides tools for simulating evolutionary processes and building phylogenetic trees from sequence data. It implements core evolutionary algorithms including selection, crossover, and mutation.

## Tools

### `evolve_population`
Evolves a population of individuals over multiple generations using genetic algorithm principles.
- **Selection**: Top 50% of individuals by fitness survive
- **Crossover**: Child genes computed as average of two parents
- **Mutation**: Gaussian noise added to genes scaled by mutation_rate (default 0.1)
- Returns the evolved population with updated fitness scores

### `compute_phylogeny`
Builds a phylogenetic tree from biological sequences using pairwise distance methods.
- Computes pairwise Hamming distances between sequences
- Implements UPGMA-style hierarchical clustering
- Returns a nested dict representing the tree topology

### `mutate_individual`
Applies Gaussian mutation to an individual's gene values.
- Adds noise sampled from N(0, mutation_rate) to each gene
- Returns the mutated individual with updated genes

## Use Cases
- Simulating evolutionary dynamics
- Phylogenetic analysis of biological sequences
- Genetic algorithm experimentation
- Population genetics modeling
