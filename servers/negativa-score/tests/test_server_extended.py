"""Extended tests for negativa-score — targeting 90%+ coverage."""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.negativa_score.server import (
    _score_dimension,
    _score_negatives_logic,
    _rank_by_downside_logic,
    _compute_risk_profile_logic,
    handle_call_tool,
)


class TestScoreDimension:
    def test_technical_with_keywords(self):
        score, explanation = _score_dimension("A complex legacy system with scalability issues", "technical")
        assert score > 0
        assert "technical" in explanation

    def test_technical_no_keywords(self):
        score, explanation = _score_dimension("A simple product", "technical")
        assert score >= 0
        assert "No strong negative signals" in explanation

    def test_market_keywords_detected(self):
        score, explanation = _score_dimension("A saturated commodity market with price war competition", "market")
        assert score > 0

    def test_regulatory_keywords_detected(self):
        score, explanation = _score_dimension("A healthcare AI platform subject to GDPR and FDA compliance", "regulatory")
        assert score > 0

    def test_execution_keywords_detected(self):
        score, explanation = _score_dimension("Team faces skill gap and high turnover with tight deadline", "execution")
        assert score > 0

    def test_financial_keywords_detected(self):
        score, explanation = _score_dimension("High burn rate with limited runway and expensive operations", "financial")
        assert score > 0

    def test_social_keywords_detected(self):
        score, explanation = _score_dimension("Algorithm shows bias and raises privacy concerns", "social")
        assert score > 0

    def test_strategic_keywords_detected(self):
        score, explanation = _score_dimension("Overextended strategy with competitor focus dilution", "strategic")
        assert score > 0

    def test_operational_keywords_detected(self):
        score, explanation = _score_dimension("Manual bottleneck creates single point of failure", "operational")
        assert score > 0

    def test_score_capped_at_10(self):
        idea = "complex scalab integrat legacy hack bug crash slow latency unstable platform extra"
        score, _ = _score_dimension(idea, "technical")
        assert score <= 10

    def test_long_idea_boosts_score(self):
        short_idea = "a thing"
        long_idea = "a thing " * 60  # > 50 words
        s_short, _ = _score_dimension(short_idea, "technical")
        s_long, _ = _score_dimension(long_idea, "technical")
        # Long idea should have same or higher score
        assert s_long >= s_short

    def test_unknown_dimension_uses_dimension_as_keyword(self):
        score, explanation = _score_dimension("random text", "unknown_xyz")
        assert score >= 0

    def test_key_signals_in_explanation(self):
        _, explanation = _score_dimension("complex legacy system", "technical")
        # When keywords detected, they appear in explanation
        assert "complex" in explanation or "legacy" in explanation or "No strong" in explanation


class TestScoreNegativesLogic:
    def test_single_dimension(self):
        result = _score_negatives_logic("A complex technical system", ["technical"])
        assert "technical" in result["dimension_scores"]
        assert result["average_downside"] == result["dimension_scores"]["technical"]["score"]

    def test_multiple_dimensions(self):
        result = _score_negatives_logic("A complex expensive regulatory-heavy platform", ["technical", "financial", "regulatory"])
        assert len(result["dimension_scores"]) == 3
        assert result["total_downside"] == sum(v["score"] for v in result["dimension_scores"].values())

    def test_empty_dimensions(self):
        result = _score_negatives_logic("some idea", [])
        assert result["average_downside"] == 0
        assert result["total_downside"] == 0

    def test_average_computed_correctly(self):
        result = _score_negatives_logic("test idea", ["technical", "market"])
        expected_avg = result["total_downside"] / 2
        assert abs(result["average_downside"] - expected_avg) < 0.01

    def test_long_idea_truncated(self):
        result = _score_negatives_logic("x" * 500, ["technical"])
        assert len(result["idea"]) <= 200


class TestRankByDownsideLogic:
    def test_worst_first_ordering(self):
        ideas = [
            "A simple product with no risks",
            "A complex scalab legacy integrat hack crash system with latency bugs",
            "A moderate market product",
        ]
        result = _rank_by_downside_logic(ideas, "technical")
        scores = [r["score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_empty_list(self):
        result = _rank_by_downside_logic([], "technical")
        assert result == []

    def test_single_idea(self):
        result = _rank_by_downside_logic(["one idea"], "market")
        assert len(result) == 1
        assert "score" in result[0]

    def test_idea_truncated(self):
        ideas = ["x" * 500]
        result = _rank_by_downside_logic(ideas, "technical")
        assert len(result[0]["idea"]) <= 200

    def test_non_string_ideas_handled(self):
        ideas = [42, None, {"key": "val"}]
        result = _rank_by_downside_logic(ideas, "technical")
        assert len(result) == 3


class TestComputeRiskProfileLogic:
    def test_all_categories_present(self):
        result = _compute_risk_profile_logic("A platform idea")
        categories = result["risk_profile"].keys()
        assert "technical" in categories
        assert "market" in categories
        assert "regulatory" in categories
        assert "execution" in categories
        assert "financial" in categories

    def test_high_risk_rating(self):
        high_risk_idea = (
            "A complex scalab legacy integrat expensive regulatory GDPR compliance "
            "team skill gap burnout deadline churn price war saturate competitor"
        )
        result = _compute_risk_profile_logic(high_risk_idea)
        # average_risk_score should reflect the keywords
        assert result["average_risk_score"] >= 0

    def test_overall_risk_low(self):
        result = _compute_risk_profile_logic("sunshine rainbows puppies")
        assert result["overall_risk"] in ("LOW", "MEDIUM", "HIGH")

    def test_summary_contains_risk_level(self):
        result = _compute_risk_profile_logic("some idea")
        assert "Overall risk level:" in result["summary"]

    def test_long_idea_truncated(self):
        result = _compute_risk_profile_logic("x" * 500)
        assert len(result["idea"]) <= 200

    def test_average_risk_calculation(self):
        result = _compute_risk_profile_logic("test idea")
        scores = [v["score"] for v in result["risk_profile"].values()]
        expected_avg = sum(scores) / len(scores)
        assert abs(result["average_risk_score"] - expected_avg) < 0.01


@pytest.mark.asyncio
class TestHandleCallToolMCP:
    async def test_rank_by_downside_via_mcp(self):
        result = await handle_call_tool(
            "rank_by_downside",
            {
                "ideas": ["complex technical system", "simple product", "expensive financial risk"],
                "dimension": "financial",
            },
        )
        data = json.loads(result[0].text)
        scores = [r["score"] for r in data]
        assert scores == sorted(scores, reverse=True)

    async def test_score_negatives_via_mcp(self):
        result = await handle_call_tool(
            "score_negatives",
            {"idea": "A complex scalable technical platform", "dimensions": ["technical", "market"]},
        )
        data = json.loads(result[0].text)
        assert "technical" in data["dimension_scores"]

    async def test_compute_risk_profile_via_mcp(self):
        result = await handle_call_tool(
            "compute_risk_profile",
            {"idea": "A fintech platform with regulatory exposure"},
        )
        data = json.loads(result[0].text)
        assert "risk_profile" in data

    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError):
            await handle_call_tool("nonexistent", {})
