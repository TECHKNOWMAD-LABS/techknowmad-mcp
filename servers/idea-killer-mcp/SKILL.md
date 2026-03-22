# idea-killer-mcp

**Systematically Critique and Kill Bad Ideas MCP Server**

## Overview

idea-killer-mcp applies structured adversarial thinking to evaluate ideas. It uses multiple modes of critique to surface fatal flaws, hidden assumptions, and real-world failure scenarios before resources are committed.

## Tools

### `kill_idea`
Applies adversarial modes to generate killing arguments:
- **devil**: Seeks contrary evidence and counterexamples
- **skeptic**: Surfaces unstated assumptions and logical gaps
- **market**: Identifies market failures, timing issues, and competitive threats
Each argument includes a severity score (1-10).

### `stress_test_idea`
Tests an idea against user-defined scenarios:
- Scenarios like "recession", "competitor entry", "regulation change"
- Each scenario gets pass/fail with reasoning
- Returns overall resilience score

### `find_fatal_flaws`
Domain-specific deep analysis:
- **tech**: Architecture, scalability, security, maintainability flaws
- **business**: Revenue model, moat, unit economics flaws
- **social**: Ethical, privacy, equity, harm flaws
- **scientific**: Methodology, reproducibility, validity flaws
Each flaw includes an impact score (1-10).

## Use Cases
- Pre-mortem before product launches
- Investment rejection criteria generation
- Research hypothesis stress testing
- Startup idea validation
