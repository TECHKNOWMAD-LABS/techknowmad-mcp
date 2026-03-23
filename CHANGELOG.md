# Changelog

All notable changes to `techknowmad-mcp` are documented in this file.

## [0.1.0] — 2026-03-23

First release. Built autonomously via the **Edgecraft Protocol** — 8 development cycles.

### Cycle 1 — Test Coverage
- Added `conftest.py` with shared fixtures for all test modules
- Added 244 new tests (from 24 to 268 total)
- Coverage improved from **71% to 99%** across 8 server modules
- Extended test files for every module: edgecraft-benchmark, forge-generate,
  graph-forge, ground-truth, idea-killer, negativa-score, phyloid-evolve, trace-agent

### Cycle 2 — Error Hardening
- Fixed `None` constraints crashing `_generate_edge_cases_logic`
- Fixed `None` test_cases crashing `_run_benchmark_logic`
- Fixed non-dict args crashing `_compare_benchmarks_logic`
- Fixed `None` nodes/edges crashing `_build_adjacency`
- Fixed `None` idea/mode/domain/scenarios/dimensions crashing idea-killer, negativa-score
- Fixed `None` population crashing `_evolve_population_logic`
- Fixed `None` individual crashing `_mutate_individual_logic`
- All 9 None-input paths now return graceful results

### Cycle 3 — Performance
- Added `@lru_cache(maxsize=512)` to `_score_dimension` in negativa-score
  - **15x measured speedup** on repeated calls (96x with warm cache)
- Added `@lru_cache(maxsize=1024)` to `_token_overlap` in ground-truth-mcp
- Both functions are pure (deterministic) — cache correctness guaranteed

### Cycle 4 — Security
- Security scan: **0 hardcoded secrets found**
- 2 false positives documented: SQL injection test fixture (intentional), JSON Schema URL (static)
- Added `_MAX_IDEA_LENGTH = 10,000` input truncation guard in negativa-score (DoS protection)
- Added `_MAX_SEQUENCES = 500` cap in phyloid-evolve `_compute_phylogeny_logic` (O(n²) DoS guard)

### Cycle 5 — CI/CD
- Added `.github/workflows/ci.yml`:
  - Checkout, setup-python 3.12, uv install, ruff check, pytest with coverage ≥90%
- Added `.pre-commit-config.yaml` with ruff + ruff-format + mypy hooks
- Fixed 87 ruff lint issues (unsorted imports, unused variables, bare f-strings)
- Added `.gitignore` for pycache, build artifacts, venv

### Cycle 6 — Property-Based Testing
- Added 35 Hypothesis property tests across 4 modules
- edgecraft-benchmark: passed+failed==total, pass_rate∈[0,100], identity invariant
- negativa-score: score∈[0,10], total==sum of dimensions, sorted descending
- graph-forge: density∈[0,1], centrality≥0, path invariant in linear graphs
- phyloid-evolve: Hamming symmetry/non-negative/bounded, population size preserved

### Cycle 7 — Examples + Docs
- Added `examples/example_benchmark_edgecases.py` — edge case generation + benchmarking
- Added `examples/example_idea_analysis.py` — adversarial critique + risk profiling pipeline
- Added `examples/example_graph_phylogeny.py` — knowledge graphs + genetic evolution + phylogeny
- Enhanced docstrings for `_run_benchmark_logic`, `_bfs_path`, `_query_graph_logic`, `_start_trace_logic`

### Cycle 8 — Release Engineering
- Updated `pyproject.toml` with author, keywords, classifiers, readme field
- Added `CHANGELOG.md` (this file)
- Added `Makefile` with `test`, `lint`, `format`, `security`, `clean` targets
- Added `AGENTS.md` documenting the Edgecraft autonomous development protocol
- Added `EVOLUTION.md` documenting all 8 cycles with timestamps and findings
- Tagged `v0.1.0`

### Summary
| Metric | Before | After |
|--------|--------|-------|
| Tests | 24 | 303 |
| Coverage | 71% | 99% |
| Lint issues | 87 | 0 |
| Security findings | — | 0 real (2 FP) |
| Property tests | 0 | 35 |
| Working examples | 0 | 3 |
| CI pipeline | None | GitHub Actions |
