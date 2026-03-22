"""ground-truth-mcp — Validate claims against ground truth."""
from mcp.server import Server
import mcp.types as types
import json
from datetime import datetime, timezone
from typing import Any

app = Server("ground-truth-mcp")

# Module-level in-memory truth store
_truth_store: dict[str, dict] = {}


def _store_ground_truth_logic(key: str, value: str, source: str) -> dict:
    """Store a fact in the truth store."""
    timestamp = datetime.now(timezone.utc).isoformat()
    _truth_store[key] = {
        "value": value,
        "source": source,
        "stored_at": timestamp,
    }
    return {
        "status": "stored",
        "key": key,
        "timestamp": timestamp,
        "store_size": len(_truth_store),
    }


def _token_overlap(text_a: str, text_b: str) -> float:
    """Compute Jaccard similarity of word tokens."""
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _validate_claim_logic(claim: str, evidence: list) -> dict:
    """Validate a claim against stored facts and provided evidence."""
    supporting = []
    contradicting = []
    claim_lower = claim.lower()
    claim_tokens = set(claim_lower.split())

    # Check stored facts
    for key, fact in _truth_store.items():
        fact_tokens = set(fact["value"].lower().split())
        overlap = len(claim_tokens & fact_tokens) / max(len(claim_tokens), 1)
        if overlap >= 0.3:
            supporting.append({"key": key, "fact": fact["value"], "overlap": round(overlap, 3)})
        elif overlap < 0.1 and len(fact_tokens) > 3:
            contradicting.append({"key": key, "fact": fact["value"], "overlap": round(overlap, 3)})

    # Check provided evidence
    evidence_support = 0
    for ev in evidence:
        overlap = _token_overlap(claim, str(ev))
        if overlap >= 0.2:
            evidence_support += 1
            supporting.append({"source": "evidence", "fact": str(ev)[:100], "overlap": round(overlap, 3)})

    # Compute confidence
    support_score = len(supporting) * 20
    contradict_penalty = len(contradicting) * 15
    evidence_boost = min(30, evidence_support * 10)
    confidence = max(0, min(100, support_score - contradict_penalty + evidence_boost + 10))

    return {
        "claim": claim[:200],
        "confidence": confidence,
        "verdict": "SUPPORTED" if confidence >= 50 else "UNSUPPORTED" if confidence < 25 else "UNCERTAIN",
        "supporting_facts": supporting[:5],
        "contradicting_facts": contradicting[:5],
        "evidence_checked": len(evidence),
    }


def _compare_outputs_logic(output_a: str, output_b: str, criteria: list) -> dict:
    """Compare two outputs on specified criteria."""
    comparison = {}
    wins_a = 0
    wins_b = 0

    for criterion in criteria:
        crit_lower = criterion.lower()
        # Keyword overlap with criterion
        overlap_a = _token_overlap(output_a, crit_lower)
        overlap_b = _token_overlap(output_b, crit_lower)
        crit_tokens = set(crit_lower.split())

        # Score based on criterion keyword presence in output
        score_a_kw = sum(1 for t in crit_tokens if t in output_a.lower()) / max(len(crit_tokens), 1)
        score_b_kw = sum(1 for t in crit_tokens if t in output_b.lower()) / max(len(crit_tokens), 1)

        # Length consideration: prefer more detailed for "detail", "comprehensive" criteria
        len_a = len(output_a)
        len_b = len(output_b)
        length_ratio = len_a / max(len_b, 1)
        if "detail" in crit_lower or "comprehensive" in crit_lower or "complete" in crit_lower:
            score_a_len = min(1.0, length_ratio)
            score_b_len = min(1.0, 1 / max(length_ratio, 0.01))
        else:
            # Prefer concise for brevity criteria
            score_a_len = 0.5
            score_b_len = 0.5

        score_a = round((score_a_kw + score_a_len) / 2, 3)
        score_b = round((score_b_kw + score_b_len) / 2, 3)

        winner = "A" if score_a > score_b else "B" if score_b > score_a else "TIE"
        if winner == "A":
            wins_a += 1
        elif winner == "B":
            wins_b += 1

        comparison[criterion] = {
            "score_a": score_a,
            "score_b": score_b,
            "winner": winner,
        }

    overall_winner = "A" if wins_a > wins_b else "B" if wins_b > wins_a else "TIE"
    return {
        "criteria_comparison": comparison,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "overall_winner": overall_winner,
        "output_a_length": len(output_a),
        "output_b_length": len(output_b),
    }


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="store_ground_truth",
            description="Store a verified fact in the ground truth store",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Unique key for the fact"},
                    "value": {"type": "string", "description": "The fact content"},
                    "source": {"type": "string", "description": "Source/provenance of the fact"},
                },
                "required": ["key", "value", "source"],
            },
        ),
        types.Tool(
            name="validate_claim",
            description="Validate a claim against stored ground truth facts and provided evidence",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "The claim to validate"},
                    "evidence": {
                        "type": "array",
                        "description": "List of evidence strings to check against",
                    },
                },
                "required": ["claim", "evidence"],
            },
        ),
        types.Tool(
            name="compare_outputs",
            description="Compare two outputs on specified criteria and return per-criterion scores",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_a": {"type": "string", "description": "First output to compare"},
                    "output_b": {"type": "string", "description": "Second output to compare"},
                    "criteria": {
                        "type": "array",
                        "description": "List of criteria strings to compare on",
                    },
                },
                "required": ["output_a", "output_b", "criteria"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name == "store_ground_truth":
        result = _store_ground_truth_logic(
            arguments["key"], arguments["value"], arguments["source"]
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "validate_claim":
        result = _validate_claim_logic(arguments["claim"], arguments["evidence"])
        return [types.TextContent(type="text", text=json.dumps(result))]
    elif name == "compare_outputs":
        result = _compare_outputs_logic(
            arguments["output_a"], arguments["output_b"], arguments["criteria"]
        )
        return [types.TextContent(type="text", text=json.dumps(result))]
    raise ValueError(f"Unknown tool: {name}")
