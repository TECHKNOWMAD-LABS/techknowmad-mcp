# TechKnowmad MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776ab.svg)](https://www.python.org/downloads/release/python-3120/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](servers)

A monorepo of production-grade [Model Context Protocol](https://modelcontextprotocol.io) servers for structured thinking, code generation, graph analysis, and agent observability. Each server exposes a focused set of tools consumable by Claude and any MCP-compatible AI assistant.

---

## Features

- **Adversarial idea validation** — stress-test concepts with devil's advocate, skeptic, and market-reality modes before committing resources
- **Hallucination detection** — store ground-truth anchors and validate AI claims against them at call time
- **Edge-case benchmarking** — auto-generate security, robustness, and boundary-condition test suites from a function spec
- **Polyglot code scaffolding** — emit typed code skeletons, JSON schemas, and test stubs across multiple languages from a single spec
- **Knowledge graph construction** — build, query, and compute centrality metrics on in-memory directed graphs
- **Agent execution tracing** — instrument multi-step agent workflows with timestamped step logs for replay and audit

---

## Servers

| Server | Tools | Purpose |
|--------|-------|---------|
| `idea-killer-mcp` | `kill_idea`, `stress_test_idea`, `find_fatal_flaws` | Adversarial critique |
| `ground-truth-mcp` | `store_ground_truth`, `validate_claim`, `compare_outputs` | Fact validation |
| `edgecraft-benchmark-mcp` | `generate_edge_cases`, `run_benchmark`, `compare_benchmarks` | Edge-case generation |
| `forge-generate-mcp` | `generate_code`, `generate_schema`, `generate_tests` | Code/schema scaffolding |
| `graph-forge-mcp` | `create_graph`, `query_graph`, `compute_centrality` | Knowledge graphs |
| `trace-agent-mcp` | `start_trace`, `log_step`, `get_trace` | Agent tracing |
| `phyloid-evolve` | `evolve_population`, `compute_phylogeny`, `mutate_individual` | Evolutionary computation |
| `negativa-score` | `score_negatives`, `rank_by_downside`, `compute_risk_profile` | Risk scoring |

---

## Quick Start

**Requirements:** Python 3.12+, `uv` or `pip`

```bash
git clone https://github.com/techknowmad/techknowmad-mcp.git
cd techknowmad-mcp
pip install -e ".[dev]"
```

Run all tests:

```bash
pytest -v
```

Run a single server:

```bash
python servers/idea-killer-mcp/server.py
```

Add to Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "idea-killer": {
      "command": "python",
      "args": ["/path/to/techknowmad-mcp/servers/idea-killer-mcp/server.py"]
    }
  }
}
```

---

## Architecture

```
techknowmad-mcp/
├── pyproject.toml              # Root: Python 3.12, pytest, hatchling
└── servers/
    └── {server-name}/
        ├── server.py           # MCP server — tool registration + handlers
        ├── pyproject.toml      # Per-server package config
        ├── SKILL.md            # Tool reference and usage examples
        └── tests/
            └── test_server.py  # Async pytest suite
```

Each server follows a consistent pattern:

1. **Tool registration** — `@app.tool()` decorators declare name, description, and input schema
2. **Async handlers** — `handle_list_tools()` and `handle_call_tool()` implement the MCP protocol
3. **JSON responses** — all results wrapped in `types.TextContent` as serialized JSON
4. **No external state** — in-memory only; suitable for stateless agent sessions

Adding a new server: copy an existing server directory, rename it, update `pyproject.toml`, implement tools in `server.py`, add tests, and register in Claude Desktop config.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow (fork → feature branch → tests → `pytest -v` → `ruff check` → PR). All PRs must include tests and pass CI.

---

## License

[MIT](LICENSE)

---

Built by [TechKnowMad Labs](https://techknowmad.ai)
