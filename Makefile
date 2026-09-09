.PHONY: fix ci skills-ci docs-ci harness-ci

# Regenerate everything that is generated. Safe to run at any time.
fix:
	uv run scripts/sync_plugins.py

# Assert the tree is clean after a regenerate: a generated file that differs
# means someone hand-edited a pack, or edited a canonical skill without
# re-syncing. Then the layout invariants, the publication contract, and the
# hook suite.
#
# The two gates split by who owns the rule. validate_plugins.py asserts the
# layout this repo invented (the mirror, the composition, the hook wiring);
# tests/ asserts what a marketplace enforces on sync, which nothing else
# available locally checks - not `claude plugin validate --strict`, not
# harness-ci, not the published marketplace schema.
ci: fix
	@test -z "$$(git status --porcelain)" || { \
		git status --short; \
		echo "ERROR: regenerate left the tree dirty - commit the generated files"; \
		exit 1; }
	uv run scripts/validate_plugins.py
	uv run pytest
	$(MAKE) skills-ci
	@test -z "$$(git status --porcelain)" || { \
		git status --short; \
		echo "ERROR: a skill gate regenerated something - commit it"; \
		exit 1; }

# A skill opts into its own script gate by shipping scripts/Makefile with a `ci`
# target. Discovered, never listed here: adding the file is the opt-in, and the
# four skills with no scripts/ at all need no entry anywhere to be exempt.
#
# The glob is one level deep on purpose, which puts
# skills/*/vendor/*/scripts/Makefile out of scope. A vendored copy is read-only
# and upstream-owned, its gate re-asserts what the upstream skill's own gate
# already covers, and ADR-007's refresh procedure is where it belongs.
#
# An empty discovery is a failure, not a pass: every one of these Makefiles
# disappearing should be loud rather than quietly green.
SKILL_GATES := $(patsubst %/Makefile,%,$(shell grep -lE '^ci:' skills/*/scripts/Makefile 2>/dev/null))

skills-ci:
	@test -n "$(SKILL_GATES)" || { \
		echo "ERROR: no skills/*/scripts/Makefile declares a ci target - discovery found nothing"; \
		exit 1; }
	@echo "Skill script gates ($(words $(SKILL_GATES)) opted in): $(notdir $(patsubst %/scripts,%,$(SKILL_GATES)))"
	@for d in $(SKILL_GATES); do \
		printf '\n── %s\n' "$$d"; \
		if [ -f "$$d/package.json" ]; then bun install --cwd "$$d" --silent || exit 1; fi; \
		$(MAKE) -C "$$d" ci || exit 1; \
	done

# The authored markdown. Everything under skills/ is a skill's own
# documentation, vendored or upstream-owned, and plugins/*/hooks/README.md is a
# generated mirror of hooks/README.md - gating either would report the same
# finding twice, or report one this repo cannot fix.
DOCS := README.md plugins/README.md hooks/README.md

# Prose and diagram gates, run with this repo's own skills rather than an
# external package: gooddocs and mermaidjs-diagrams both ship these scripts, so
# the checks travel with the repo and stay runnable by anyone who clones it.
#
# Each script directory carries its own package.json and lockfile (the
# complexity gate parses with mermaid's canonical parser, which needs a DOM),
# so its dependencies are installed in place rather than hoisted to a root
# package.json this repo deliberately does not have. A gate ships inside a
# pack and must resolve on a machine that has never seen this repo, which is
# also why pyproject.toml covers only the repo's own tooling and no skill.
GATES := skills/gooddocs/scripts skills/mermaidjs-diagrams/scripts

docs-ci:
	@for d in $(GATES); do bun install --cwd $$d --silent || exit 1; done
	bun run skills/gooddocs/scripts/prose_gates.ts $(DOCS)
	bun run skills/mermaidjs-diagrams/scripts/mermaid_complexity.ts $(DOCS)
	bun run skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts $(DOCS)

# The real install test: clones HEAD and installs both packs into throwaway
# Claude and Codex sandboxes. Kept out of `ci` because it drives two external
# CLIs and writes sandboxes outside the repo, so it is slower and depends on
# more of the host than the other targets.
harness-ci:
	./scripts/test_harness_install.sh
