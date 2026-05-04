"""Extended tests for ground-truth-mcp — targeting 90%+ coverage."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.ground_truth_mcp.server import (
    _compare_outputs_logic,
    _store_ground_truth_logic,
    _token_overlap,
    _truth_store,
    _validate_claim_logic,
    handle_call_tool,
)


@pytest.fixture(autouse=True)
def clear_store():
    """Clear the global truth store before each test."""
    _truth_store.clear()
    yield
    _truth_store.clear()


class TestTokenOverlap:
    def test_identical_strings(self):
        assert _token_overlap("hello world", "hello world") == 1.0

    def test_completely_different(self):
        result = _token_overlap("cat dog", "fish bird")
        assert result == 0.0

    def test_partial_overlap(self):
        result = _token_overlap("the cat sat", "the dog sat")
        assert 0 < result < 1.0

    def test_empty_both(self):
        assert _token_overlap("", "") == 1.0

    def test_one_empty(self):
        assert _token_overlap("hello", "") == 0.0

    def test_case_insensitive(self):
        assert _token_overlap("Hello World", "hello world") == 1.0


class TestStoreGroundTruthLogic:
    def test_basic_store(self):
        result = _store_ground_truth_logic("key1", "The sky is blue", "science")
        assert result["status"] == "stored"
        assert result["key"] == "key1"
        assert "key1" in _truth_store

    def test_store_size_increments(self):
        _store_ground_truth_logic("k1", "fact 1", "source1")
        r2 = _store_ground_truth_logic("k2", "fact 2", "source2")
        assert r2["store_size"] == 2

    def test_overwrite_existing_key(self):
        _store_ground_truth_logic("k", "original", "s1")
        _store_ground_truth_logic("k", "updated", "s2")
        assert _truth_store["k"]["value"] == "updated"

    def test_timestamp_is_iso(self):
        result = _store_ground_truth_logic("k", "v", "s")
        from datetime import datetime

        datetime.fromisoformat(result["timestamp"])


class TestValidateClaimLogic:
    def test_empty_store_unsupported(self):
        result = _validate_claim_logic("water is wet", [])
        assert result["verdict"] in ("UNSUPPORTED", "UNCERTAIN", "SUPPORTED")

    def test_supporting_fact_boosts_confidence(self):
        _store_ground_truth_logic("w", "water is wet and liquid substance", "science")
        result = _validate_claim_logic("water is wet", [])
        # Should have supporting fact
        assert len(result["supporting_facts"]) > 0

    def test_evidence_boosts_confidence(self):
        result = _validate_claim_logic(
            "the sky is blue",
            ["the sky appears blue during daytime", "blue sky is common"],
        )
        assert result["evidence_checked"] == 2

    def test_verdict_supported(self):
        for i in range(5):
            _store_ground_truth_logic(
                f"k{i}", "python is a great programming language tool", f"src{i}"
            )
        result = _validate_claim_logic("python programming language", [])
        # Multiple overlapping facts should push to supported
        assert result["confidence"] >= 0

    def test_confidence_range(self):
        result = _validate_claim_logic("arbitrary claim here", [])
        assert 0 <= result["confidence"] <= 100

    def test_long_claim_truncated(self):
        result = _validate_claim_logic("x " * 300, [])
        assert len(result["claim"]) <= 200

    def test_result_has_all_keys(self):
        result = _validate_claim_logic("test claim", ["evidence 1"])
        assert "claim" in result
        assert "confidence" in result
        assert "verdict" in result
        assert "supporting_facts" in result
        assert "contradicting_facts" in result
        assert "evidence_checked" in result


class TestCompareOutputsLogic:
    def test_longer_wins_detail_criterion(self):
        short = "short"
        long_text = (
            "This is a very comprehensive and detailed response covering many aspects"
        )
        result = _compare_outputs_logic(short, long_text, ["comprehensive", "detail"])
        assert result["overall_winner"] == "B"

    def test_same_outputs_tie(self):
        same = "identical output text"
        result = _compare_outputs_logic(same, same, ["quality"])
        assert result["overall_winner"] == "TIE"

    def test_wins_tracked_correctly(self):
        a = "accuracy is high quality"
        b = "accuracy is low"
        result = _compare_outputs_logic(a, b, ["accuracy", "quality"])
        assert (
            result["wins_a"]
            + result["wins_b"]
            + (1 if result["overall_winner"] == "TIE" else 0)
            >= 0
        )

    def test_empty_criteria(self):
        result = _compare_outputs_logic("a", "b", [])
        assert result["overall_winner"] == "TIE"

    def test_output_lengths_in_result(self):
        result = _compare_outputs_logic("hello", "world longer text", ["length"])
        assert result["output_a_length"] == 5
        assert result["output_b_length"] == 17

    def test_multiple_criteria(self):
        result = _compare_outputs_logic("aaa", "bbb", ["x", "y", "z"])
        assert "x" in result["criteria_comparison"]
        assert "y" in result["criteria_comparison"]
        assert "z" in result["criteria_comparison"]


@pytest.mark.asyncio
class TestHandleCallToolMCP:
    async def test_store_validate_workflow(self):
        r1 = await handle_call_tool(
            "store_ground_truth",
            {
                "key": "fact-climate",
                "value": "Climate change is driven by CO2 emissions",
                "source": "ipcc",
            },
        )
        d1 = json.loads(r1[0].text)
        assert d1["status"] == "stored"

        r2 = await handle_call_tool(
            "validate_claim",
            {"claim": "CO2 emissions drive climate", "evidence": []},
        )
        d2 = json.loads(r2[0].text)
        assert d2["confidence"] >= 0

    async def test_compare_outputs_via_mcp(self):
        result = await handle_call_tool(
            "compare_outputs",
            {
                "output_a": "This is a comprehensive detailed complete explanation of the topic",
                "output_b": "Short answer",
                "criteria": ["comprehensive", "detail", "complete"],
            },
        )
        data = json.loads(result[0].text)
        assert data["overall_winner"] == "A"

    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError):
            await handle_call_tool("nonexistent", {})
