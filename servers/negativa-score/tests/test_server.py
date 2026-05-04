"""Tests for negativa-score server."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.negativa_score.server import handle_call_tool, handle_list_tools


@pytest.mark.asyncio
async def test_list_tools():
    tools = await handle_list_tools()
    assert len(tools) == 3
    names = [t.name for t in tools]
    assert "score_negatives" in names
    assert "rank_by_downside" in names
    assert "compute_risk_profile" in names


@pytest.mark.asyncio
async def test_score_negatives():
    result = await handle_call_tool(
        "score_negatives",
        {
            "idea": "Build a complex scalable platform with many integrations",
            "dimensions": ["technical", "market"],
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "dimension_scores" in data
    assert "technical" in data["dimension_scores"]
    assert "market" in data["dimension_scores"]
    assert 0 <= data["dimension_scores"]["technical"]["score"] <= 10


@pytest.mark.asyncio
async def test_compute_risk_profile():
    result = await handle_call_tool(
        "compute_risk_profile",
        {
            "idea": "Launch expensive regulated fintech startup with complex compliance requirements"
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "risk_profile" in data
    assert "overall_risk" in data
    assert data["overall_risk"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(data["risk_profile"]) == 5
