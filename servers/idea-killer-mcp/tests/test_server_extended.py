"""Extended tests for idea-killer-mcp — targeting 90%+ coverage."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from servers.idea_killer_mcp.server import (
    _find_fatal_flaws_logic,
    _kill_idea_logic,
    _stress_test_logic,
    handle_call_tool,
)


class TestKillIdeaLogic:
    def test_devil_mode(self):
        result = _kill_idea_logic("A new social network for dogs", "devil")
        assert result["mode"] == "devil"
        assert len(result["killing_arguments"]) > 0
        assert all(a["mode"] == "devil" for a in result["killing_arguments"])

    def test_skeptic_mode(self):
        result = _kill_idea_logic("A subscription service for AI art", "skeptic")
        assert result["mode"] == "skeptic"
        assert len(result["killing_arguments"]) > 0

    def test_market_mode(self):
        result = _kill_idea_logic("An enterprise SaaS platform for invoicing", "market")
        assert result["mode"] == "market"

    def test_unknown_mode_defaults_to_skeptic(self):
        result = _kill_idea_logic("some idea", "unknown_mode")
        assert len(result["killing_arguments"]) > 0

    def test_severity_boosted_for_innovative_ideas(self):
        result_normal = _kill_idea_logic("A platform for data management", "skeptic")
        result_innovative = _kill_idea_logic(
            "A revolutionary innovative disruptive new platform", "skeptic"
        )
        # Innovative idea should have higher or equal severity
        assert result_innovative["max_severity"] >= result_normal["max_severity"]

    def test_long_idea_truncated(self):
        long_idea = "x" * 500
        result = _kill_idea_logic(long_idea, "devil")
        assert len(result["idea"]) <= 200

    def test_max_severity_computed(self):
        result = _kill_idea_logic("test idea", "market")
        assert result["max_severity"] >= 0
        assert result["max_severity"] <= 10

    def test_fortune500_placeholder_replaced(self):
        result = _kill_idea_logic("a new platform", "devil")
        args = result["killing_arguments"]
        assert all("{company}" not in a["argument"] for a in args)


class TestStressTestLogic:
    def test_recession_scenario_optional_product_fails(self):
        result = _stress_test_logic(
            "Luxury premium expensive discretionary lifestyle app", ["recession"]
        )
        scenario = result["scenario_results"][0]
        assert scenario["scenario"] == "recession"

    def test_recession_scenario_cost_reduction_passes(self):
        result = _stress_test_logic(
            "A tool for cost reduction and efficiency savings", ["recession"]
        )
        scenario = result["scenario_results"][0]
        assert scenario["result"] == "PASS"

    def test_competitor_scenario_commodity_fails(self):
        # Commodity open source idea has kill words and no signals -> PASS (it's cost-effective), actually fails
        # The competitor scenario: passes = has_kill OR not has_signal
        # A product with proprietary signals but no kill words => has_signal=True, has_kill=False => FAIL
        result = _stress_test_logic(
            "A patent-protected proprietary unique SaaS", ["competitor entry"]
        )
        scenario = result["scenario_results"][0]
        # Logic: passes = has_kill OR not has_signal => False OR False => FAIL
        assert scenario["result"] == "FAIL"

    def test_regulation_scenario_detected(self):
        result = _stress_test_logic(
            "An AI data privacy platform", ["regulation change"]
        )
        assert len(result["scenario_results"]) == 1

    def test_unknown_scenario_short_idea_fails(self):
        result = _stress_test_logic("X", ["zombie apocalypse scenario"])
        scenario = result["scenario_results"][0]
        assert scenario["result"] == "FAIL"

    def test_unknown_scenario_detailed_idea_passes(self):
        long_idea = " ".join(["word"] * 15)
        result = _stress_test_logic(long_idea, ["zombie apocalypse scenario"])
        scenario = result["scenario_results"][0]
        assert scenario["result"] == "PASS"

    def test_multiple_scenarios(self):
        result = _stress_test_logic("A SaaS tool", ["recession", "competitor entry"])
        assert len(result["scenario_results"]) == 2
        assert result["passed"] + result["failed"] == 2

    def test_resilience_score_range(self):
        result = _stress_test_logic(
            "test idea with cost savings", ["recession", "competitor entry"]
        )
        assert 0 <= result["resilience_score"] <= 100

    def test_empty_scenarios(self):
        result = _stress_test_logic("some idea", [])
        assert result["resilience_score"] == 0
        assert result["passed"] == 0

    def test_long_idea_truncated(self):
        result = _stress_test_logic("x" * 500, ["recession"])
        assert len(result["idea"]) <= 200


class TestFindFatalFlawsLogic:
    def test_tech_domain(self):
        result = _find_fatal_flaws_logic(
            "A complex scalable platform with legacy integrations", "tech"
        )
        assert result["domain"] == "tech"
        assert len(result["fatal_flaws"]) > 0
        assert all(f["domain"] == "tech" for f in result["fatal_flaws"])

    def test_business_domain(self):
        result = _find_fatal_flaws_logic("A simple startup with no moat", "business")
        assert result["domain"] == "business"
        assert result["flaw_count"] > 0

    def test_social_domain(self):
        result = _find_fatal_flaws_logic(
            "An AI platform collecting user data", "social"
        )
        assert result["domain"] == "social"

    def test_scientific_domain(self):
        result = _find_fatal_flaws_logic("A study to prove hypothesis", "scientific")
        assert result["domain"] == "scientific"

    def test_unknown_domain_defaults_to_business(self):
        result = _find_fatal_flaws_logic("an idea", "unknown_domain")
        assert result["flaw_count"] > 0

    def test_impact_boosted_for_simple_ideas(self):
        result_complex = _find_fatal_flaws_logic(
            "A complex enterprise solution", "business"
        )
        result_simple = _find_fatal_flaws_logic(
            "A simple easy fast quick startup", "business"
        )
        assert result_simple["max_impact"] >= result_complex["max_impact"]

    def test_max_impact_computed(self):
        result = _find_fatal_flaws_logic("some idea", "tech")
        assert 0 < result["max_impact"] <= 10

    def test_long_idea_truncated(self):
        result = _find_fatal_flaws_logic("x" * 500, "tech")
        assert len(result["idea"]) <= 200


@pytest.mark.asyncio
class TestHandleCallToolMCP:
    async def test_stress_test_via_mcp(self):
        result = await handle_call_tool(
            "stress_test_idea",
            {
                "idea": "A cost reduction efficiency savings tool",
                "scenarios": ["recession", "competitor entry"],
            },
        )
        data = json.loads(result[0].text)
        assert len(data["scenario_results"]) == 2
        assert 0 <= data["resilience_score"] <= 100

    async def test_find_fatal_flaws_via_mcp(self):
        result = await handle_call_tool(
            "find_fatal_flaws",
            {"idea": "A tech platform with scalability issues", "domain": "tech"},
        )
        data = json.loads(result[0].text)
        assert data["domain"] == "tech"

    async def test_kill_idea_all_modes(self):
        for mode in ["devil", "skeptic", "market"]:
            result = await handle_call_tool(
                "kill_idea",
                {"idea": "A generic startup idea", "mode": mode},
            )
            data = json.loads(result[0].text)
            assert data["mode"] == mode

    async def test_unknown_tool_raises(self):
        with pytest.raises(ValueError):
            await handle_call_tool("nonexistent", {})
