"""Property-based tests for negativa-score using Hypothesis."""

import os
import sys

from hypothesis import given
from hypothesis import strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.negativa_score.server import (
    _compute_risk_profile_logic,
    _rank_by_downside_logic,
    _score_dimension,
    _score_negatives_logic,
)

_VALID_DIMS = [
    "technical",
    "market",
    "regulatory",
    "execution",
    "financial",
    "social",
    "strategic",
    "operational",
]


class TestScoreDimensionProperties:
    @given(
        idea=st.text(min_size=0, max_size=500),
        dimension=st.sampled_from(_VALID_DIMS),
    )
    def test_score_always_in_range(self, idea, dimension):
        """Score is always 0-10."""
        # Clear cache to avoid cross-test pollution
        _score_dimension.cache_clear()
        score, _ = _score_dimension(idea, dimension)
        assert 0 <= score <= 10

    @given(
        idea=st.text(min_size=0, max_size=200),
        dimension=st.sampled_from(_VALID_DIMS),
    )
    def test_explanation_always_string(self, idea, dimension):
        """Explanation is always a string."""
        _score_dimension.cache_clear()
        _, explanation = _score_dimension(idea, dimension)
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    @given(
        idea=st.text(min_size=0, max_size=200),
        dimension=st.sampled_from(_VALID_DIMS),
    )
    def test_deterministic(self, idea, dimension):
        """Same inputs always produce same outputs (pure function)."""
        _score_dimension.cache_clear()
        result1 = _score_dimension(idea, dimension)
        _score_dimension.cache_clear()
        result2 = _score_dimension(idea, dimension)
        assert result1 == result2


class TestScoreNegativesProperties:
    @given(
        idea=st.text(min_size=0, max_size=200),
        dimensions=st.lists(
            st.sampled_from(_VALID_DIMS), min_size=1, max_size=8, unique=True
        ),
    )
    def test_average_within_range(self, idea, dimensions):
        """average_downside is always between 0 and 10."""
        _score_dimension.cache_clear()
        result = _score_negatives_logic(idea, dimensions)
        assert 0 <= result["average_downside"] <= 10

    @given(
        idea=st.text(min_size=0, max_size=200),
        dimensions=st.lists(
            st.sampled_from(_VALID_DIMS), min_size=1, max_size=8, unique=True
        ),
    )
    def test_total_downside_equals_sum(self, idea, dimensions):
        """total_downside equals sum of all dimension scores."""
        _score_dimension.cache_clear()
        result = _score_negatives_logic(idea, dimensions)
        expected_total = sum(v["score"] for v in result["dimension_scores"].values())
        assert result["total_downside"] == expected_total

    @given(
        idea=st.text(min_size=0, max_size=200),
        dimensions=st.lists(
            st.sampled_from(_VALID_DIMS), min_size=1, max_size=5, unique=True
        ),
    )
    def test_all_dimensions_present_in_output(self, idea, dimensions):
        """Every requested dimension appears in output."""
        _score_dimension.cache_clear()
        result = _score_negatives_logic(idea, dimensions)
        for dim in dimensions:
            assert dim in result["dimension_scores"]


class TestRankByDownsideProperties:
    @given(
        ideas=st.lists(st.text(min_size=0, max_size=100), min_size=2, max_size=20),
        dimension=st.sampled_from(_VALID_DIMS),
    )
    def test_output_sorted_descending(self, ideas, dimension):
        """Output is always sorted by score descending (worst first)."""
        _score_dimension.cache_clear()
        result = _rank_by_downside_logic(ideas, dimension)
        scores = [r["score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    @given(
        ideas=st.lists(st.text(min_size=0, max_size=100), min_size=0, max_size=20),
        dimension=st.sampled_from(_VALID_DIMS),
    )
    def test_output_length_matches_input(self, ideas, dimension):
        """Output has same number of items as input."""
        _score_dimension.cache_clear()
        result = _rank_by_downside_logic(ideas, dimension)
        assert len(result) == len(ideas)


class TestRiskProfileProperties:
    @given(idea=st.text(min_size=0, max_size=500))
    def test_always_has_five_categories(self, idea):
        """Risk profile always has exactly 5 categories."""
        _score_dimension.cache_clear()
        result = _compute_risk_profile_logic(idea)
        assert len(result["risk_profile"]) == 5

    @given(idea=st.text(min_size=0, max_size=200))
    def test_overall_risk_valid_value(self, idea):
        """overall_risk is always LOW, MEDIUM, or HIGH."""
        _score_dimension.cache_clear()
        result = _compute_risk_profile_logic(idea)
        assert result["overall_risk"] in ("LOW", "MEDIUM", "HIGH")

    @given(idea=st.text(min_size=0, max_size=200))
    def test_average_risk_in_range(self, idea):
        """average_risk_score is always in [0, 10]."""
        _score_dimension.cache_clear()
        result = _compute_risk_profile_logic(idea)
        assert 0.0 <= result["average_risk_score"] <= 10.0
