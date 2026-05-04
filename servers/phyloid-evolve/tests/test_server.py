"""Tests for phyloid-evolve server."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.phyloid_evolve.server import handle_call_tool, handle_list_tools


@pytest.mark.asyncio
async def test_list_tools():
    tools = await handle_list_tools()
    assert len(tools) == 3
    names = [t.name for t in tools]
    assert "evolve_population" in names
    assert "compute_phylogeny" in names
    assert "mutate_individual" in names


@pytest.mark.asyncio
async def test_evolve_population():
    result = await handle_call_tool(
        "evolve_population",
        {
            "population": [
                {"fitness": 5, "genes": [1, 2, 3]},
                {"fitness": 3, "genes": [4, 5, 6]},
            ],
            "generations": 2,
            "fitness_fn": "max",
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "population" in data
    assert data["generations_run"] == 2
    assert len(data["population"]) >= 1


@pytest.mark.asyncio
async def test_compute_phylogeny():
    result = await handle_call_tool(
        "compute_phylogeny",
        {
            "sequences": ["ACGT", "ACGG", "TTTT"],
            "method": "upgma",
        },
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "tree" in data
    assert data["sequence_count"] == 3
    assert data["method"] == "upgma"
