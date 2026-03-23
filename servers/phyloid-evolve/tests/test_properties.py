"""Property-based tests for phyloid-evolve using Hypothesis."""
import sys
import os

from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.phyloid_evolve.server import (
    _compute_phylogeny_logic,
    _evolve_population_logic,
    _hamming_distance,
    _mutate_individual_logic,
)

gene_st = st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False)
individual_st = st.fixed_dictionaries({
    "fitness": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    "genes": st.lists(gene_st, min_size=1, max_size=10),
})


class TestHammingDistanceProperties:
    @given(s1=st.text(max_size=100), s2=st.text(max_size=100))
    def test_non_negative(self, s1, s2):
        """Hamming distance is always non-negative."""
        assert _hamming_distance(s1, s2) >= 0

    @given(s=st.text(max_size=100))
    def test_identity_is_zero(self, s):
        """Hamming distance of string with itself is always 0."""
        assert _hamming_distance(s, s) == 0

    @given(s1=st.text(max_size=100), s2=st.text(max_size=100))
    def test_symmetry(self, s1, s2):
        """Hamming distance is symmetric: d(a,b) == d(b,a)."""
        assert _hamming_distance(s1, s2) == _hamming_distance(s2, s1)

    @given(s1=st.text(max_size=50), s2=st.text(max_size=50))
    def test_bounded_by_max_length(self, s1, s2):
        """Hamming distance <= max(len(s1), len(s2))."""
        assert _hamming_distance(s1, s2) <= max(len(s1), len(s2))


class TestEvolutionProperties:
    @given(
        population=st.lists(individual_st, min_size=2, max_size=10),
        generations=st.integers(min_value=0, max_value=10),
        fitness_fn=st.sampled_from(["max", "sum", "mean"]),
    )
    def test_population_size_preserved(self, population, generations, fitness_fn):
        """Population size is always preserved after evolution."""
        result = _evolve_population_logic(population, generations, fitness_fn)
        assert result["population_size"] == len(population)

    @given(
        population=st.lists(individual_st, min_size=2, max_size=10),
        generations=st.integers(min_value=0, max_value=10),
        fitness_fn=st.sampled_from(["max", "sum", "mean"]),
    )
    def test_all_individuals_have_fitness(self, population, generations, fitness_fn):
        """All individuals in evolved population have a fitness key."""
        result = _evolve_population_logic(population, generations, fitness_fn)
        for ind in result["population"]:
            assert "fitness" in ind

    @given(
        individual=individual_st,
        mutation_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    def test_mutation_preserves_gene_count(self, individual, mutation_rate):
        """Mutation always preserves the number of genes."""
        result = _mutate_individual_logic(individual, mutation_rate)
        assert len(result["genes"]) == len(individual["genes"])

    @given(individual=individual_st)
    def test_zero_mutation_rate_preserves_genes(self, individual):
        """With zero mutation rate, genes are numerically unchanged."""
        result = _mutate_individual_logic(individual, 0.0)
        for orig, mutated in zip(individual["genes"], result["genes"]):
            assert abs(orig - mutated) < 1e-10


class TestPhylogenyProperties:
    @given(
        sequences=st.lists(
            st.text(alphabet="ACGT", min_size=1, max_size=20),
            min_size=2,
            max_size=10,
        )
    )
    def test_sequence_count_correct(self, sequences):
        """sequence_count in result matches number of input sequences."""
        result = _compute_phylogeny_logic(sequences, "upgma")
        assert result["sequence_count"] == len(sequences)

    @given(
        sequences=st.lists(
            st.text(alphabet="ACGT", min_size=1, max_size=20),
            min_size=2,
            max_size=8,
        )
    )
    def test_pairwise_distances_non_negative(self, sequences):
        """All pairwise distances are non-negative."""
        result = _compute_phylogeny_logic(sequences, "upgma")
        for dist in result["pairwise_distances"].values():
            assert dist >= 0
