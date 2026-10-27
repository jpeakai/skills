# Quality gates for the librarian skill's scripts (TypeScript only).
# Run from repo root: make -C skills/librarian/scripts <target>

# ── TypeScript source ───────────────────────────────────────────────────
TS_SCRIPTS = md2yaml
TS_SRC = $(addsuffix .ts,$(TS_SCRIPTS)) $(addsuffix .test.ts,$(TS_SCRIPTS))

# ── Paths ───────────────────────────────────────────────────────────────
THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# biome via bunx so it stays out of package.json; --bun pins the runtime.
BIOME = bunx --bun @biomejs/biome

.PHONY: all help clean install \
        format format-ts format-check format-check-ts \
        lint lint-ts lint-fix lint-fix-ts \
        typecheck typecheck-ts \
        test test-ts test-cov test-cov-ts \
        ci fix

all: format lint typecheck test-cov

# ── Format ──────────────────────────────────────────────────────────────
format: format-ts
format-ts:       ; $(BIOME) format --write $(TS_SRC)
format-check: format-check-ts
format-check-ts: ; $(BIOME) format $(TS_SRC)

# ── Lint ────────────────────────────────────────────────────────────────
lint: lint-ts
lint-ts:         ; $(BIOME) lint $(TS_SRC)
lint-fix: lint-fix-ts
lint-fix-ts:     ; $(BIOME) lint --write $(TS_SRC)

# ── Typecheck ───────────────────────────────────────────────────────────
typecheck: typecheck-ts
# Invoke local tsc directly — `bunx tsc` has dep-resolution quirks when cwd differs.
typecheck-ts:    ; $(THIS_DIR)node_modules/.bin/tsc --project $(THIS_DIR)tsconfig.json --noEmit

# ── Test ────────────────────────────────────────────────────────────────
test: test-ts
test-ts:         ; bun test --cwd $(THIS_DIR)

test-cov: test-cov-ts
test-cov-ts:     ; bun test --cwd $(THIS_DIR) --coverage --coverage-threshold=0.90

# ── Misc ────────────────────────────────────────────────────────────────
install:         ; bun install --cwd $(THIS_DIR)

ci: format-check lint typecheck test-cov
fix: format lint-fix

clean:
	rm -rf $(THIS_DIR)tmp

help:
	@echo "fix  — format + lint --write (mutates)"
	@echo "ci   — format-check, lint, typecheck, test-cov (the gate)"
