.PHONY: test lint format security clean install help

# Default target
help:
	@echo "Available targets:"
	@echo "  make test      — run pytest with coverage"
	@echo "  make lint      — run ruff linter"
	@echo "  make format    — run ruff formatter"
	@echo "  make security  — check for secrets and large inputs"
	@echo "  make clean     — remove cache and build artifacts"
	@echo "  make install   — install all dependencies via uv"

install:
	uv sync --all-extras --dev

test:
	uv run pytest -v --tb=short --cov=servers --cov-report=term-missing --cov-fail-under=90

test-fast:
	uv run pytest -q --tb=short

test-property:
	uv run pytest -v -k "test_properties" --tb=short

lint:
	uv run ruff check servers/ --select E,F,W,I --ignore E501

format:
	uv run ruff format servers/
	uv run ruff check servers/ --select I --fix

security:
	@echo "Scanning for secrets..."
	@grep -rn "api_key\s*=\s*['\"][^'\"]\|password\s*=\s*['\"][^'\"]\|secret\s*=\s*['\"][^'\"]" \
		servers/ --include="*.py" || echo "No hardcoded secrets found."
	@echo "Checking for eval/exec usage..."
	@grep -rn "eval(\|exec(\|os\.system(" servers/ --include="*.py" | \
		grep -v "test_\|#" || echo "No dangerous eval/exec found."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage dist build *.egg-info
