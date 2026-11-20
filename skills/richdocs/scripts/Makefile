# Shared Makefile for all richdocs skill scripts (pure Python).
# Run from repo root: make -C {SKILLS_ROOT}/richdocs/scripts <target>

# ── Python source ──────────────────────────────────────────────────────────

# Public Python scripts (referenced in SKILL.md)
PY_SCRIPTS = serve stencil md2html showcase themecheck structure

# Private scripts: maintenance helpers for the skill itself (none yet)
PRIVATE_PY_SCRIPTS =

PY_TESTS := $(wildcard test_*.py)
PY_TEST_TARGETS := $(patsubst test_%.py,test-py-%,$(PY_TESTS))
PY_COV_TARGETS := $(patsubst test_%.py,test-cov-py-%,$(PY_TESTS))

PY_SRC = $(addsuffix .py,$(PY_SCRIPTS)) $(PY_TESTS) \
         $(addsuffix .py,$(PRIVATE_PY_SCRIPTS)) \
         conftest.py

# ── Paths ──────────────────────────────────────────────────────────────────

THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# --no-project prevents uv from discovering the root pyproject.toml,
# which would otherwise inject unrelated coverage config and deps.
UV = uv run --no-project

# Isolate pytest from any root pyproject.toml config (addopts, plugins).
PYTEST_ARGS = -v -c /dev/null --rootdir .

.PHONY: themecheck all debug help clean \
        format format-py \
        format-check format-check-py \
        lint lint-py lint-cognitive \
        lint-fix lint-fix-py \
        typecheck typecheck-py typecheck-ts \
        test test-py test-js \
        test-cov test-cov-py \
        ci fix $(PY_TEST_TARGETS) $(PY_COV_TARGETS)

# Default target
all: format lint typecheck test-cov

debug:
	echo $(MAKEFILE_LIST)
	echo $(THIS_DIR)
	echo $(PY_SRC)

# ── Format ─────────────────────────────────────────────────────────────────

format: format-py

format-py: $(PY_SRC)
	$(UV) --with ruff ruff format $(PY_SRC)

format-check: format-check-py

format-check-py: $(PY_SRC)
	$(UV) --with ruff ruff format --check $(PY_SRC)

# ── Lint ───────────────────────────────────────────────────────────────────

lint: lint-py lint-cognitive

lint-cognitive: $(PY_SRC) pyproject.toml
	$(UV) --with complexipy==9.0.0 complexipy --config $(THIS_DIR)pyproject.toml --failed $(PY_SRC)

lint-py: $(PY_SRC)
	$(UV) --with ruff ruff check --line-length 120 $(PY_SRC)

lint-fix: lint-fix-py lint-cognitive

lint-fix-py: $(PY_SRC)
	$(UV) --with ruff ruff check --fix --line-length 120 $(PY_SRC)

# ── Typecheck ──────────────────────────────────────────────────────────────

typecheck: typecheck-py typecheck-ts

# mypy resolved hermetically via `uv run --with mypy` — no system install assumed.
typecheck-py: $(addsuffix .py,$(PY_SCRIPTS) $(PRIVATE_PY_SCRIPTS))
	$(UV) --with mypy mypy $(addsuffix .py,$(PY_SCRIPTS) $(PRIVATE_PY_SCRIPTS)) --ignore-missing-imports --strict

# The DOM tests for the viewer's own JavaScript are TypeScript (ADR-021).
typecheck-ts:
	bunx --bun tsc --noEmit -p $(THIS_DIR)tsconfig.json

# ── Test ───────────────────────────────────────────────────────────────────

test: test-py test-js

# Discover PEP-723 test entry points while preserving their isolated dependencies.
test-py: $(PY_TEST_TARGETS)

$(PY_TEST_TARGETS): test-py-%: test_%.py
	$(UV) $< $(PYTEST_ARGS)

# The viewer's JavaScript runs in a browser, not here. Its behaviour is
# asserted in happy-dom (ADR-021); bun is a test-time dependency only, and the
# shipped scripts declare their dependencies in PEP-723 headers.
test-js:
	bun test --cwd $(THIS_DIR)

test-cov: test-cov-py test-js

test-cov-py: $(PY_COV_TARGETS)

$(PY_COV_TARGETS): test-cov-py-%: test_%.py
	$(UV) $< $(PYTEST_ARGS) \
		--cov=$* --cov-report=term-missing --cov-fail-under=90

# ── CI / Fix / Misc ────────────────────────────────────────────────────────

# Run all checks with coverage enforcement (CI standard).
ci: format-check lint typecheck test-cov themecheck

# Run all auto-fixers (local development)
# The brandpack gate: a theme that renders unreadable text must not ship.
themecheck:
	$(UV) themecheck.py

fix: format lint-fix

# Clean up cache and temp files
clean:
	rm -f *.pyc
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

# Show help
help:
	@echo "Composite targets:"
	@echo "  all          - format + lint + typecheck + test-cov (default)"
	@echo "  format       - Auto-format source"
	@echo "  format-check - Check formatting without modifying (CI-safe)"
	@echo "  lint         - Lint source and cognitive complexity (non-mutating)"
	@echo "  lint-fix     - Lint and auto-fix"
	@echo "  typecheck    - Type check public scripts (mypy --strict)"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage (>=90%)"
	@echo "  ci           - format-check + lint + typecheck + test-cov"
	@echo "  fix          - format + lint-fix"
	@echo "  clean        - Remove temp files and caches"
