# negativa-score

**Score Ideas by Negatives and Downsides MCP Server**

## Overview

negativa-score applies inversion thinking — instead of asking "why will this succeed?", it asks "why will this fail?". It systematically scores ideas across negative dimensions, helping teams surface hidden risks before committing resources.

## Tools

### `score_negatives`
Scores an idea across specified negative dimensions using keyword-based analysis.
- Each dimension is analyzed for risk signals in the idea text
- Returns a score 0-10 per dimension (higher = more downside) with explanation
- Useful for structured pre-mortem analysis

### `rank_by_downside`
Scores and ranks a list of ideas on a single negative dimension.
- Returns ideas sorted worst-first (highest downside score first)
- Useful for prioritizing which ideas need the most scrutiny

### `compute_risk_profile`
Comprehensive risk analysis across 5 standard categories:
- **Technical**: complexity, scalability, integration risks
- **Market**: competition, adoption, timing risks
- **Regulatory**: compliance, legal, policy risks
- **Execution**: team, timeline, resource risks
- **Financial**: cost, revenue, runway risks

## Use Cases
- Pre-mortem analysis before product launches
- Investment due diligence
- Strategic planning risk assessment
- Idea ranking and filtering
