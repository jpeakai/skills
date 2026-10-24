# Quality gates for the adr skill's scripts (Python only).
# Run from repo root: make -C skills/adr/scripts <target>

# ── Python source ───────────────────────────────────────────────────────
PY_SCRIPTS = okf_render adr_audit
PY_SRC = $(addsuffix .py,$(PY_SCRIPTS)) $(addprefix test_,$(addsuffix .py,$(PY_SCRIPTS))) conftest.py

# ── Paths ───────────────────────────────────────────────────────────────
THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
EXAMPLE  := $(THIS_DIR)../resources/okf_yaml/example

# `--no-project` stops uv walking up and discovering a root pyproject.toml.
UV = uv run --no-project
PYTEST_ARGS = -v --rootdir . -o 'addopts='

.PHONY: all help clean \
        format format-py format-check format-check-py \
        lint lint-py lint-fix lint-fix-py \
        typecheck typecheck-py \
        test test-py test-cov test-cov-py \
        docs ci fix

all: format lint typecheck test-cov docs

# ── Format ──────────────────────────────────────────────────────────────
format: format-py
format-py:       ; $(UV) --with ruff ruff format --line-length 110 $(PY_SRC)
format-check: format-check-py
format-check-py: ; $(UV) --with ruff ruff format --check --line-length 110 $(PY_SRC)

# ── Lint ────────────────────────────────────────────────────────────────
lint: lint-py
lint-py:         ; $(UV) --with ruff ruff check --line-length 110 $(PY_SRC)
lint-fix: lint-fix-py
lint-fix-py:     ; $(UV) --with ruff ruff check --fix --line-length 110 $(PY_SRC)

# ── Typecheck ───────────────────────────────────────────────────────────
typecheck: typecheck-py
typecheck-py:
	$(UV) --with mypy --with types-PyYAML --with Jinja2 --with jsonschema \
		mypy $(addsuffix .py,$(PY_SCRIPTS)) --ignore-missing-imports --strict

# ── Test ────────────────────────────────────────────────────────────────
test: test-py
test-py:
	$(UV) $(THIS_DIR)test_okf_render.py $(PYTEST_ARGS)
	$(UV) $(THIS_DIR)test_adr_audit.py $(PYTEST_ARGS)

test-cov: test-cov-py
test-cov-py:
	$(UV) $(THIS_DIR)test_okf_render.py $(PYTEST_ARGS) \
		--cov=okf_render --cov-report=term-missing --cov-fail-under=90
	$(UV) $(THIS_DIR)test_adr_audit.py $(PYTEST_ARGS) \
		--cov=adr_audit --cov-report=term-missing --cov-fail-under=90

# ── Docs / Misc ─────────────────────────────────────────────────────────
# Regenerate the shipped example bundle: it is the golden fixture the Python
# suite diffs against, so a template change must be reflected here.
docs:
	$(UV) --with PyYAML --with Jinja2 --with jsonschema \
		$(THIS_DIR)okf_render.py $(EXAMPLE)

ci: format-check lint typecheck test-cov docs
fix: format lint-fix

clean:
	rm -rf $(THIS_DIR)__pycache__ $(THIS_DIR).pytest_cache $(THIS_DIR).mypy_cache \
	       $(THIS_DIR).ruff_cache $(THIS_DIR).coverage $(THIS_DIR)tmp

help:
	@echo "fix  — format + lint --write (mutates)"
	@echo "ci   — format-check, lint, typecheck, test-cov, docs (the gate)"
