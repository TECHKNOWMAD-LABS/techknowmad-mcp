"""Example: Using idea-killer-mcp + negativa-score for comprehensive idea analysis.

This script shows how to combine adversarial idea critique with quantitative
risk scoring to get a full picture before committing to a startup idea.

Usage:
    uv run python examples/example_idea_analysis.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from servers.idea_killer_mcp.server import (
    _find_fatal_flaws_logic,
    _kill_idea_logic,
    _stress_test_logic,
)
from servers.negativa_score.server import (
    _compute_risk_profile_logic,
    _score_negatives_logic,
)


IDEA = (
    "An AI-powered compliance monitoring platform for financial institutions "
    "using machine learning to detect regulatory violations in real time, "
    "with automated reporting to regulators and a subscription pricing model."
)

SCENARIOS = ["recession", "competitor entry", "regulation change"]
MODES = ["devil", "skeptic", "market"]


def main() -> None:
    """Run comprehensive idea analysis pipeline."""
    print("=== Idea Analysis Pipeline ===\n")
    print(f"Idea: {IDEA[:80]}...\n")

    # 1. Kill the idea from three angles
    print("1. Adversarial critique:")
    for mode in MODES:
        result = _kill_idea_logic(IDEA, mode)
        top_arg = (
            result["killing_arguments"][0]["argument"]
            if result["killing_arguments"]
            else "N/A"
        )
        print(
            f"   [{mode.upper():8s}] severity={result['max_severity']:>2}/10 | {top_arg[:70]}"
        )
    print()

    # 2. Stress test against scenarios
    print("2. Stress test:")
    stress = _stress_test_logic(IDEA, SCENARIOS)
    for sr in stress["scenario_results"]:
        icon = "PASS" if sr["result"] == "PASS" else "FAIL"
        print(f"   [{icon}] {sr['scenario']:25s} | {sr['reasoning'][:60]}")
    print(f"   Resilience score: {stress['resilience_score']}/100\n")

    # 3. Domain fatal flaws
    print("3. Fatal flaws by domain:")
    for domain in ["tech", "business", "social"]:
        flaws = _find_fatal_flaws_logic(IDEA, domain)
        top_flaw = flaws["fatal_flaws"][0]["flaw"] if flaws["fatal_flaws"] else "N/A"
        print(
            f"   [{domain.upper():10s}] max_impact={flaws['max_impact']:>2}/10 | {top_flaw[:60]}"
        )
    print()

    # 4. Risk profile
    print("4. Quantitative risk profile:")
    profile = _compute_risk_profile_logic(IDEA)
    for cat, data in sorted(
        profile["risk_profile"].items(), key=lambda x: x[1]["score"], reverse=True
    ):
        bar = "#" * data["score"]
        print(f"   {cat:12s} [{bar:<10}] {data['score']:>2}/10")
    print(
        f"   Overall: {profile['overall_risk']} (avg {profile['average_risk_score']:.1f}/10)\n"
    )

    # 5. Targeted negative scoring
    print("5. Negativa scores:")
    neg_dims = ["regulatory", "execution", "financial"]
    neg = _score_negatives_logic(IDEA, neg_dims)
    for dim, data in neg["dimension_scores"].items():
        print(f"   {dim:12s}: {data['score']:>2}/10 — {data['explanation'][:55]}")
    print(f"   Average downside: {neg['average_downside']:.1f}\n")

    print("Analysis complete.")


if __name__ == "__main__":
    main()
