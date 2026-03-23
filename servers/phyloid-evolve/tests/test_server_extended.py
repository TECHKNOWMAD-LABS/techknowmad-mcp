"""Extended tests for phyloid-evolve — targeting 90%+ coverage."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.phyloid_evolve.server import (
    _compute_phylogeny_logic,
    _evolve_population_logic,
    _hamming_distance,
    _mutate_individual_logic,
    handle_call_tool,
)


class TestHammingDistance:
    def test_identical_strings(self):
        assert _hamming_distance("ACGT", "ACGT") == 0

    def test_completely_different(self):
        assert _hamming_distance("AAAA", "TTTT") == 4

    def test_partial_difference(self):
        assert _hamming_distance("ACGT", "ACTT") == 1

    def test_different_lengths(self):
        # Pads shorter string
        dist = _hamming_distance("AC", "ACGT")
        assert dist == 2  # "AC  " vs "ACGT"

    def test_empty_strings(self):
        assert _hamming_distance("", "") == 0

    def test_one_empty_string(self):
        dist = _hamming_distance("", "ACGT")
        assert dist == 4


class TestEvolutionLogic:
    def test_basic_evolution(self):
        population = [
            {"fitness": 0.8, "genes": [0.5, 0.3]},
            {"fitness": 0.6, "genes": [0.2, 0.7]},
            {"fitness": 0.4, "genes": [0.1, 0.1]},
            {"fitness": 0.9, "genes": [0.9, 0.8]},
        ]
        result = _evolve_population_logic(population, 5, "mean")
        assert result["generations_run"] == 5
        assert result["population_size"] == 4
        assert all("fitness" in ind for ind in result["population"])

    def test_max_fitness_fn(self):
        population = [
            {"fitness": 0.5, "genes": [0.5, 0.3, 0.8]},
            {"fitness": 0.7, "genes": [0.7, 0.2, 0.1]},
        ]
        result = _evolve_population_logic(population, 2, "max")
        assert result["generations_run"] == 2

    def test_sum_fitness_fn(self):
        population = [
            {"fitness": 0.5, "genes": [0.5, 0.3]},
            {"fitness": 0.7, "genes": [0.7, 0.2]},
        ]
        result = _evolve_population_logic(population, 3, "sum")
        assert result["generations_run"] == 3

    def test_zero_generations(self):
        population = [{"fitness": 0.5, "genes": [0.5]}]
        result = _evolve_population_logic(population, 0, "mean")
        assert result["generations_run"] == 0

    def test_single_individual(self):
        population = [{"fitness": 0.5, "genes": [0.5, 0.5]}]
        result = _evolve_population_logic(population, 3, "mean")
        assert result["population_size"] == 1

    def test_missing_genes_handled(self):
        population = [
            {"fitness": 0.5},  # no genes key
            {"fitness": 0.7, "genes": [0.7]},
        ]
        result = _evolve_population_logic(population, 2, "mean")
        assert result["generations_run"] == 2

    def test_population_is_not_mutated_in_place(self):
        original_pop = [
            {"fitness": 0.8, "genes": [0.5, 0.3]},
            {"fitness": 0.6, "genes": [0.2, 0.7]},
        ]
        original_genes = [list(ind["genes"]) for ind in original_pop]
        _evolve_population_logic(original_pop, 5, "mean")
        # Original should not be mutated (we use dict copies)
        assert [list(ind["genes"]) for ind in original_pop] == original_genes


class TestComputePhylogenyLogic:
    def test_empty_sequences(self):
        result = _compute_phylogeny_logic([], "upgma")
        assert result["sequence_count"] == 0
        assert result["tree"] == {}

    def test_single_sequence(self):
        result = _compute_phylogeny_logic(["ACGT"], "upgma")
        assert result["sequence_count"] == 1

    def test_two_sequences(self):
        result = _compute_phylogeny_logic(["ACGT", "ACTT"], "upgma")
        assert result["sequence_count"] == 2
        assert "tree" in result
        assert "children" in result["tree"]

    def test_three_sequences(self):
        result = _compute_phylogeny_logic(["AAAA", "TTTT", "CCCC"], "upgma")
        assert result["sequence_count"] == 3
        assert "pairwise_distances" in result

    def test_identical_sequences(self):
        result = _compute_phylogeny_logic(["ACGT", "ACGT", "ACGT"], "upgma")
        assert result["sequence_count"] == 3

    def test_method_stored(self):
        result = _compute_phylogeny_logic(["ACGT", "GCTA"], "nj")
        assert result["method"] == "nj"

    def test_pairwise_distances_non_negative(self):
        result = _compute_phylogeny_logic(["ACGT", "ACTT", "TTTT"], "upgma")
        for k, v in result["pairwise_distances"].items():
            assert v >= 0


class TestMutateIndividualLogic:
    def test_genes_mutated(self):
        ind = {"fitness": 0.5, "genes": [0.5, 0.5, 0.5]}
        result = _mutate_individual_logic(ind, 0.01)
        assert result["genes"] != ind["genes"]  # Very likely to differ with noise

    def test_fitness_recomputed(self):
        ind = {"fitness": 0.5, "genes": [1.0, 1.0]}
        result = _mutate_individual_logic(ind, 0.0)  # zero noise
        # fitness = mean of genes = 1.0 (no noise)
        assert abs(result["fitness"] - 1.0) < 0.01

    def test_empty_genes(self):
        ind = {"fitness": 0.5, "genes": []}
        result = _mutate_individual_logic(ind, 0.1)
        assert result["genes"] == []

    def test_original_not_mutated(self):
        ind = {"fitness": 0.5, "genes": [0.5, 0.5]}
        original_genes = list(ind["genes"])
        _mutate_individual_logic(ind, 1.0)
        assert ind["genes"] == original_genes  # original unchanged via dict copy

    def test_mutation_rate_zero(self):
        ind = {"fitness": 0.5, "genes": [0.5, 0.5]}
        result = _mutate_individual_logic(ind, 0.0)
        # With zero Gaussian noise, genes should be exactly the same
        for orig, mutated in zip(ind["genes"], result["genes"]):
            assert abs(orig - mutated) < 1e-10


@pytest.mark.asyncio
class TestHandleCallToolMCP:
    async def test_mutate_individual_via_mcp(self):
        result = await handle_call_tool(
            "mutate_individual",
            {
                "individual": {"fitness": 0.5, "genes": [0.5, 0.5, 0.5]},
                "mutation_rate": 0.01,
            },
        )
        data = json.loads(result[0].text)
        assert "genes" in data
        assert "fitness" in data
        assert len(data["genes"]) == 3

    async def test_evolve_population_via_mcp(self):
        result = await handle_call_tool(
            "evolve_population",
            {
                "population": [
                    {"fitness": 0.8, "genes": [0.5, 0.3]},
                    {"fitness": 0.6, "genes": [0.2, 0.7]},
                ],
                "generations": 3,
                "fitness_fn": "mean",
            },
        )
        data = json.loads(result[0].text)
        assert data["generations_run"] == 3

    async def test_compute_phylogeny_via_mcp(self):
        result = await handle_call_tool(
            "compute_phylogeny",
            {"sequences": ["ACGT", "ACTT", "GGGG"], "method": "upgma"},
        )
        data = json.loads(result[0].text)
        assert data["sequence_count"] == 3

    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError):
            await handle_call_tool("nonexistent", {})
