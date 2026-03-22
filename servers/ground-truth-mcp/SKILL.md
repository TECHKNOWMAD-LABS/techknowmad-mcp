# ground-truth-mcp

**Validate Claims Against Ground Truth MCP Server**

## Overview

ground-truth-mcp maintains an in-memory store of verified facts and provides tools to validate claims against that store, compare outputs, and assess confidence in assertions.

## Tools

### `store_ground_truth`
Stores a verified fact in the module-level truth store.
- `key`: unique identifier for the fact
- `value`: the fact content
- `source`: provenance of the fact
Returns confirmation with timestamp.

### `validate_claim`
Validates a claim against stored facts and provided evidence.
- Computes confidence score 0-100 based on keyword overlap with stored truths
- Returns supporting and contradicting facts
- Useful for hallucination detection and fact checking

### `compare_outputs`
Compares two outputs on specified criteria:
- Keyword overlap with criteria terms
- Length ratio comparison
- Returns per-criterion scores and winner

## Use Cases
- AI output validation
- Fact-checking pipelines
- A/B output comparison
- Hallucination detection
- Ground truth maintenance for RAG systems
