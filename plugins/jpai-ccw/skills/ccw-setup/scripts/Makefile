# Quality gates for the ccw-setup skill's scripts (Python and shell).
# Run from repo root: make -C skills/ccw-setup/scripts <target>

PY_SRC = ccw_check.py test_ccw_check.py conftest.py
SH_SRC = cloud-setup.sh cloud-setup-stub.sh

THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# `--no-project` stops uv walking up and discovering a root pyproject.toml.
UV = uv run --no-project
RUFF = $(UV) --with ruff ruff
PYTEST_ARGS = -v --rootdir . -o 'addopts='

.PHONY: format format-check lint lint-fix typecheck shell-check test test-cov ci fix clean help

format:       ; $(RUFF) format --line-length 110 $(PY_SRC)
format-check: ; $(RUFF) format --check --line-length 110 $(PY_SRC)
lint:         ; $(RUFF) check --line-length 110 $(PY_SRC)
lint-fix:     ; $(RUFF) check --fix --line-length 110 $(PY_SRC)
typecheck:    ; $(UV) --with mypy mypy ccw_check.py --strict

# No ShellCheck gate is declared repository-wide; parse every script at least.
shell-check:
	@for f in $(SH_SRC); do bash -n "$$f" || exit 1; done

test:
	$(UV) $(THIS_DIR)test_ccw_check.py $(PYTEST_ARGS)

test-cov:
	$(UV) $(THIS_DIR)test_ccw_check.py $(PYTEST_ARGS) \
		--cov=ccw_check --cov-report=term-missing --cov-fail-under=90

ci: format-check lint typecheck shell-check test-cov
fix: format lint-fix

clean:
	rm -rf $(THIS_DIR)__pycache__ $(THIS_DIR).pytest_cache $(THIS_DIR).mypy_cache \
	       $(THIS_DIR).ruff_cache $(THIS_DIR).coverage

help:
	@echo "fix  - format + lint --fix (mutates)"
	@echo "ci   - format-check, lint, typecheck, shell-check, test-cov (the gate)"
