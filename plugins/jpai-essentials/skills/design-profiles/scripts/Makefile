# Node.js-compatible modules; Bun runs the development gates.
JS_SRC = profiles.mjs profile_resolver.mjs shadcn_profile.mjs shadcn.mjs
TEST_SRC = profiles.test.ts profile_resolver.test.ts shadcn_profile.test.ts shadcn.test.ts
BIOME = bunx --bun @biomejs/biome

.PHONY: all ci fix format format-check lint lint-fix typecheck test test-cov
all: ci
ci: format-check lint typecheck test-cov
fix: format lint-fix
format:
	$(BIOME) format --write $(JS_SRC) $(TEST_SRC)
format-check:
	$(BIOME) format $(JS_SRC) $(TEST_SRC)
lint:
	$(BIOME) lint --error-on-warnings $(JS_SRC) $(TEST_SRC)
lint-fix:
	$(BIOME) lint --write $(JS_SRC) $(TEST_SRC)
typecheck:
	./node_modules/.bin/tsc --project tsconfig.json
test:
	bun test $(TEST_SRC)
test-cov:
	bun test $(TEST_SRC) --coverage --coverage-threshold=0.90
