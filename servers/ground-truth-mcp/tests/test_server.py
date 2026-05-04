"""Tests for ground-truth-mcp server."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.ground_truth_mcp.server import handle_call_tool, handle_list_tools


@pytest.mark.asyncio
async def test_list_tools():
    tools = await handle_list_tools()
    assert len(tools) == 3
    names = [t.name for t in tools]
    assert "store_ground_truth" in names
    assert "validate_claim" in names
    assert "compare_outputs" in names


@pytest.mark.asyncio
async def test_store_and_validate():
    # Store a fact first
    store_result = await handle_call_tool(
        "store_ground_truth",
        {
            "key": "fact_water",
            "value": "Water boils at 100 degrees Celsius at sea level",
            "source": "physics-textbook",
        },
    )
    store_data = json.loads(store_result[0].text)
    assert store_data["status"] == "stored"
    assert store_data["key"] == "fact_water"

    # Validate a related claim
    validate_result = await handle_call_tool(
        "validate_claim",
        {
            "claim": "Water boils at 100 degrees",
            "evidence": ["Boiling point of water is 100C"],
        },
    )
    val_data = json.loads(validate_result[0].text)
    assert "confidence" in val_data
    assert val_data["confidence"] >= 0
    assert val_data["verdict"] in ["SUPPORTED", "UNCERTAIN", "UNSUPPORTED"]


@pytest.mark.asyncio
async def test_compare_outputs():
    result = await handle_call_tool(
        "compare_outputs",
        {
            "output_a": "This is a comprehensive and detailed explanation with complete coverage.",
            "output_b": "Short.",
            "criteria": ["comprehensive", "detail"],
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "criteria_comparison" in data
    assert "overall_winner" in data
    assert data["overall_winner"] in ["A", "B", "TIE"]
    assert "comprehensive" in data["criteria_comparison"]
