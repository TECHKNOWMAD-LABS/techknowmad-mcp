"""idea-killer-mcp — Systematically critique and kill bad ideas."""
from mcp.server import Server
import mcp.types as types
import json
from typing import Any

app = Server("idea-killer-mcp")

_DEVIL_ARGUMENTS = [
    ("There is already evidence this approach failed at {company} scale.", 8),
    ("The core assumption contradicts established research in this domain.", 9),
    ("Historical precedent shows similar ideas collapsed within 18 months.", 7),
    ("The technology required does not yet exist at production quality.", 8),
    ("Early adopters of this model reported abandonment after pilot phase.", 6),
]

_SKEPTIC_ARGUMENTS = [
    ("Assumes the target market is aware of and cares about this problem.", 7),
    ("Assumes regulatory environment will remain favorable.", 6),
    ("Assumes the team has expertise they have not yet demonstrated.", 8),
    ("Assumes competitors will not respond aggressively.", 7),
    ("Assumes cost structure will improve at scale — unproven.", 5),
]

_MARKET_ARGUMENTS = [
    ("The addressable market is too small to justify venture-scale investment.", 8),
    ("Incumbents with distribution advantages can replicate this in 6 months.", 9),
    ("Market timing is off — adoption requires behavior change that takes 5+ years.", 7),
    ("Pricing model conflicts with how buyers in this segment are accustomed to pay.", 6),
    ("Network effects require critical mass that cannot be bootstrapped.", 8),
]

_SCENARIO_RESPONSES = {
    "recession": {
        "signals": ["luxury", "optional", "premium", "expensive", "discretionary"],
        "kill_words": ["essential", "savings", "efficiency", "cost reduction"],
        "fail_reasoning": "Discretionary spending collapses in recessions — this product is non-essential.",
        "pass_reasoning": "This product provides cost savings or essential services, which are recession-resilient.",
    },
    "competitor entry": {
        "signals": ["unique", "patent", "moat", "proprietary"],
        "kill_words": ["open source", "commodity", "undifferentiated"],
        "fail_reasoning": "Without strong defensibility, a well-funded competitor can replicate and outspend.",
        "pass_reasoning": "Proprietary advantages or network effects create meaningful switching costs.",
    },
    "regulation change": {
        "signals": ["data", "privacy", "health", "finance", "ai", "crypto"],
        "kill_words": ["unregulated", "gray area", "offshore"],
        "fail_reasoning": "Core model depends on a regulatory loophole that is increasingly scrutinized.",
        "pass_reasoning": "Business model is regulation-neutral or benefits from stricter compliance requirements.",
    },
}

_DOMAIN_FLAWS = {
    "tech": [
        ("Single point of failure architecture creates catastrophic risk.", 9),
        ("Technology stack lacks mature ecosystem — limited hiring pool.", 7),
        ("Security threat model has not been defined — critical vulnerability.", 10),
        ("No clear path to horizontal scalability beyond MVP.", 8),
    ],
    "business": [
        ("No defensible moat — competitive advantage erodes immediately.", 9),
        ("Unit economics don't work at current pricing — negative gross margin.", 10),
        ("Customer acquisition cost exceeds lifetime value in the model.", 9),
        ("Revenue model requires behavior change that historically has low adoption.", 7),
    ],
    "social": [
        ("Data collection practices raise significant privacy concerns.", 8),
        ("Potential for algorithmic bias affecting vulnerable populations.", 9),
        ("Environmental impact has not been assessed or disclosed.", 6),
        ("Creates dependency that reduces user autonomy over time.", 7),
    ],
    "scientific": [
        ("Methodology lacks control group — results are not attributable.", 9),
        ("Sample size insufficient to achieve statistical significance.", 8),
        ("Confounding variables not controlled for in experimental design.", 8),
        ("Results have not been independently replicated.", 7),
    ],
}


def _kill_idea_logic(idea: str, mode: str) -> dict:
    """Generate killing arguments for an idea using the specified mode."""
    idea_lower = idea.lower()

    if mode == "devil":
        base_args = _DEVIL_ARGUMENTS
    elif mode == "skeptic":
        base_args = _SKEPTIC_ARGUMENTS
    elif mode == "market":
        base_args = _MARKET_ARGUMENTS
    else:
        base_args = _SKEPTIC_ARGUMENTS

    arguments = []
    for template, severity in base_args[:3]:
        arg_text = template.replace("{company}", "Fortune 500").replace("{idea}", idea[:50])
        # Boost severity if idea keywords overlap with risk signals
        if any(w in idea_lower for w in ["new", "innovative", "disrupt", "revolutionary"]):
            severity = min(10, severity + 1)
        arguments.append({"argument": arg_text, "severity": severity, "mode": mode})

    return {
        "idea": idea[:200],
        "mode": mode,
        "killing_arguments": arguments,
        "max_severity": max(a["severity"] for a in arguments) if arguments else 0,
    }


def _stress_test_logic(idea: str, scenarios: list) -> dict:
    """Test idea against scenarios."""
    idea_lower = idea.lower()
    results = []

    for scenario in scenarios:
        scenario_lower = scenario.lower()
        config = None
        for key, val in _SCENARIO_RESPONSES.items():
            if key in scenario_lower:
                config = val
                break

        if config:
            has_kill = any(w in idea_lower for w in config["kill_words"])
            has_signal = any(w in idea_lower for w in config["signals"])
            passes = has_kill or not has_signal
            reasoning = config["pass_reasoning"] if passes else config["fail_reasoning"]
        else:
            # Generic evaluation
            passes = len(idea.split()) > 10
            reasoning = "Insufficient specificity to fully evaluate this scenario." if not passes else "Idea has enough detail to likely adapt to this scenario."

        results.append({
            "scenario": scenario,
            "result": "PASS" if passes else "FAIL",
            "reasoning": reasoning,
        })

    passed = sum(1 for r in results if r["result"] == "PASS")
    resilience = round((passed / len(results)) * 100) if results else 0
    return {
        "idea": idea[:200],
        "scenario_results": results,
        "passed": passed,
        "failed": len(results) - passed,
        "resilience_score": resilience,
    }


def _find_fatal_flaws_logic(idea: str, domain: str) -> dict:
    """Find domain-specific fatal flaws."""
    domain_lower = domain.lower()
    flaws_config = _DOMAIN_FLAWS.get(domain_lower, _DOMAIN_FLAWS["business"])
    idea_lower = idea.lower()

    flaws = []
    for flaw_text, impact in flaws_config:
        # Increase impact if idea mentions relevant risky terms
        if any(w in idea_lower for w in ["simple", "easy", "fast", "quick"]):
            impact = min(10, impact + 1)
        flaws.append({"flaw": flaw_text, "impact": impact, "domain": domain})

    return {
        "idea": idea[:200],
        "domain": domain,
        "fatal_flaws": flaws,
        "max_impact": max(f["impact"] for f in flaws) if flaws else 0,
        "flaw_count": len(flaws),
    }


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="kill_idea",
            description="Generate adversarial killing arguments for an idea using devil, skeptic, or market mode",
            inputSchema={
                "type": "object",
                "properties": {
                    "idea": {"type": "string", "description": "The idea to critique"},
                    "mode": {"type": "string", "description": "Critique mode: 'devil', 'skeptic', or 'market'"},
                },
                "required": ["idea", "mode"],
            },
        ),
        types.Tool(
            name="stress_test_idea",
            description="Test an idea against adversarial scenarios like recession, competitor entry, regulation change",
            inputSchema={
                "type": "object",
                "properties": {
                    "idea": {"type": "string", "description": "The idea to stress test"},
                    "scenarios": {"type": "array", "description": "List of scenario strings to test against"},
                },
                "required": ["idea", "scenarios"],
            },
        ),
        types.Tool(
            name="find_fatal_flaws",
            description="Find domain-specific fatal flaws in an idea",
            inputSchema={
                "type": "object",
                "properties": {
                    "idea": {"type": "string", "description": "The idea to analyze"},
                    "domain": {"type": "string", "description": "Domain: 'tech', 'business', 'social', or 'scientific'"},
                },
                "required": ["idea", "domain"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name == "kill_idea":
        result = _kill_idea_logic(arguments["idea"], arguments["mode"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "stress_test_idea":
        result = _stress_test_logic(arguments["idea"], arguments["scenarios"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "find_fatal_flaws":
        result = _find_fatal_flaws_logic(arguments["idea"], arguments["domain"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    raise ValueError(f"Unknown tool: {name}")
