# AGENTS.md — Edgecraft Protocol: Autonomous Development System

## Overview

This repository was autonomously developed using the **Edgecraft Protocol** —
a structured 8-cycle autonomous iteration framework executed by an AI agent
without human intervention on each cycle.

## Protocol Definition

The Edgecraft Protocol is a systematic approach to autonomous software quality improvement
with 8 mandatory cycles executed in sequence. Each cycle targets a specific quality dimension
and produces verifiable, committed improvements.

## 8 Cycles

### L1 — Test Coverage
**Goal**: Bring all modules to ≥90% test coverage.
**Method**: Read all source files, identify coverage gaps, write comprehensive pytest suites
with `unittest.mock` where needed.
**Verification**: `pytest --cov --cov-fail-under=90`

### L2/L3 — Error Hardening
**Goal**: Make all public functions resilient to None, malformed, and adversarial inputs.
**Method**: Probe all inputs with None, empty strings, huge strings, wrong types. Fix each failure.
**Verification**: All existing tests still pass after fixes.

### L4/L5/L6/L7 — Performance
**Goal**: Identify and optimize sequential hot paths.
**Method**: Measure before/after timing. Apply `lru_cache` to pure deterministic functions.
Use `asyncio.gather` with semaphore for IO-bound parallel calls.
**Verification**: Document speedup measurements in commit messages.

### L2 — Security
**Goal**: Zero hardcoded secrets, zero injection vectors.
**Method**: Pattern scan for API keys, tokens, passwords. Check for eval/exec/os.system.
Assess large-input DoS vectors.
**Verification**: Document findings and false positives explicitly.

### L5 — CI/CD
**Goal**: Automated quality gates on every commit.
**Method**: Create `.github/workflows/ci.yml` with checkout, setup-python, install, lint, test.
Create `.pre-commit-config.yaml` with ruff + mypy hooks.
**Verification**: All CI steps pass locally before commit.

### L6 — Property-Based Testing
**Goal**: Verify invariants hold across all valid inputs using Hypothesis.
**Method**: Identify mathematical/logical invariants for each module. Write `@given` tests.
Fix any failures discovered.
**Verification**: All property tests pass with 100+ examples each.

### L5 — Examples + Docs
**Goal**: Every public function documented; every example runnable.
**Method**: Write 2-3 `examples/` scripts that actually execute. Enhance docstrings with
Args/Returns sections for all short/missing docstrings.
**Verification**: Run `uv run python examples/*.py` — all must succeed.

### Release Engineering
**Goal**: Production-ready package release.
**Method**: Validate pyproject.toml fields, create CHANGELOG.md, Makefile, AGENTS.md, EVOLUTION.md.
Tag version.
**Verification**: `make test lint` passes clean.

## Commit Conventions

Every commit must start with an Edgecraft layer prefix:
- `L0/attention:` — observation, pattern recognition
- `L1/detection:` — anomaly detection, gap identification
- `L2/noise:` — separating signal from noise (false positives, security scan)
- `L3/sub-noise:` — edge case discovery, failure mode identification
- `L4/conjecture:` — hypothesis about improvement
- `L5/action:` — implementation of improvement
- `L6/grounding:` — verification with measurements
- `L7/flywheel:` — cross-module pattern generalization

## Execution Rules

1. **Never ask** — execute every cycle fully without human confirmation
2. **Fix before commit** — if tests fail, fix the code first
3. **Measure** — performance claims require before/after timing
4. **Document** — every finding (including false positives) must be logged
5. **Push after each cycle** — not just at the end

## Results (v0.1.0)

| Metric | Before | After |
|--------|--------|-------|
| Tests | 24 | 303 |
| Coverage | 71% | 99% |
| Lint issues | 87 | 0 |
| Property tests | 0 | 35 |
| Working examples | 0 | 3 |
| Security issues | — | 0 |
| CI pipeline | None | GitHub Actions |
