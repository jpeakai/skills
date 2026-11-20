.PHONY: fix ci tools-ci skills-ci docs-ci harness-ci adrs adr-ci codex-setup kiro-setup

# Regenerate everything that is generated. Safe to run at any time.
fix:
	uv run --project tools/plugin-ci plugin-ci sync
	$(MAKE) adrs

adrs:
	uv run --no-project adrs/okf_render.py adrs

adr-ci:
	uv run --no-project skills/adr/scripts/adr_audit.py .

# Validate regenerated plugins while requiring authored files to be committed.
# The main-branch publication workflow owns generated plugin commits.
ci: fix
	uv run --project tools/plugin-ci plugin-ci check-worktree
	uv run --project tools/plugin-ci plugin-ci validate
	uv run pytest
	$(MAKE) tools-ci
	$(MAKE) adr-ci
	$(MAKE) docs-ci
	$(MAKE) skills-ci
	uv run --project tools/plugin-ci plugin-ci check-worktree

TOOL_GATES := $(patsubst %/Makefile,%,$(wildcard tools/*/Makefile))

tools-ci:
	@test -n "$(TOOL_GATES)"
	@for directory in $(TOOL_GATES); do $(MAKE) -C "$$directory" ci || exit 1; done

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

# Gate root documentation and canonical skill README diagrams once.
# Plugin mirrors and vendored references remain outside the authored corpus.
DOCS := README.md CONTRIBUTING.md CODING_STANDARDS.md GLOSSARY.md AGENTS.md \
        docs/CONVENTIONS.md plugins/README.md hooks/README.md kiro-conf/README.md $(wildcard rules/*.md) \
        tools/README.md tools/AGENTS.md $(wildcard tools/*/README.md) $(wildcard tools/*/AGENTS.md)
SKILL_READMES := $(wildcard skills/*/README.md)
PLUGIN_READMES := $(wildcard plugins/*/README.md)

# The prose gate and the diagram gate are both published packages,
# @jpeakai/prose-gates and @jpeakai/mermaidjs-lint, deliberately unpinned: the
# maintainer of this repo also authors both, so taking their latest release on
# every run is a managed risk rather than an unknown one. The diagram gate
# parses every mermaid fence, scores its complexity and audits its contrast;
# it replaced the mermaidjs-diagrams skill's own gate scripts, so docs-ci no
# longer installs that skill's dependencies.
PROSE_GATES := @jpeakai/prose-gates@latest
MERMAID_GATES := @jpeakai/mermaidjs-lint@latest

docs-ci:
	bunx $(PROSE_GATES) $(DOCS) $(PLUGIN_READMES)
	bunx $(MERMAID_GATES) $(DOCS) $(SKILL_READMES) $(PLUGIN_READMES)

# The real install test: clones HEAD and installs both packs into throwaway
# Claude and Codex sandboxes. Kept out of `ci` because it drives two external
# CLIs and retains isolated sandboxes, so it is slower and depends on
# more of the host than the other targets.
harness-ci:
	uv run --locked --project tools/harness-ci harness-ci run

# Use when this repo is cloned into a project as .claude/ to setup the sibling .codex/
codex-setup:
	cp -R codex-conf/ ../.codex/

# Use when this repo is cloned into a project as .claude/ to setup the sibling .kiro/.
# kiro-conf/ holds the hook wiring and agent profile; Kiro reads workspace skills
# from .kiro/skills/, so the canonical skills are copied there too, minus the
# same build artefacts and evals that sync_plugins.py keeps out of the packs.
KIRO_EXCLUDES := --exclude README.md
SKILL_EXCLUDES := $(foreach d,node_modules __pycache__ .venv .mmdc_cache .pytest_cache .ruff_cache .mypy_cache .coverage evals,--exclude $(d))

kiro-setup:
	rsync -a $(KIRO_EXCLUDES) kiro-conf/ ../.kiro/
	rsync -a $(SKILL_EXCLUDES) skills/ ../.kiro/skills/
