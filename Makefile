.PHONY: fix ci tools-ci skills-ci docs-ci harness-ci adrs adr-ci ui-ci profile-themes codex-setup kiro-setup

# Regenerate everything that is generated. Safe to run at any time.
fix: profile-themes
	uv run --project tools/plugin-ci plugin-ci sync
	$(MAKE) adrs

# Compile the shared fallback through the design-profiles CLI, then ship local copies.
profile-themes:
	node skills/design-profiles/scripts/profiles.mjs init osakanights --example osakanights --force --store tmp/design-profiles-prebuilt
	node skills/design-profiles/scripts/profiles.mjs all osakanights --store tmp/design-profiles-prebuilt
	mkdir -p skills/mermaidjs-diagrams/resources/themes/osakanights skills/richdocs/resources/themes/osakanights/profile
	cp tmp/design-profiles-prebuilt/osakanights/theme.css skills/mermaidjs-diagrams/resources/themes/osakanights/themes.css
	cp tmp/design-profiles-prebuilt/osakanights/design-tokens.json skills/mermaidjs-diagrams/resources/themes/osakanights/design-tokens.json
	cp tmp/design-profiles-prebuilt/osakanights/theme.css skills/richdocs/resources/themes/osakanights/themes.css
	cp tmp/design-profiles-prebuilt/osakanights/design-tokens.json skills/richdocs/resources/themes/osakanights/profile/design-tokens.json

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
	$(MAKE) ui-ci
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

# The richdocs UI build: a dev-time Vite + shadcn project outside the skill
# (ADR-0011). Only its built output ships in skills/richdocs/assets/, so the
# gate rebuilds it and fails when the committed copy differs from the source.
UI_OUTPUT := skills/richdocs/assets/viewer.html skills/richdocs/assets/viewer.bundle.js \
             skills/richdocs/assets/viewer.bundle.css

ui-ci:
	$(MAKE) -C web/richdocs-ui ci
	@test -z "$$(git status --porcelain -- $(UI_OUTPUT))" || { \
		git status --short -- $(UI_OUTPUT); \
		echo "ERROR: the UI Build output is stale or uncommitted - commit skills/richdocs/assets"; \
		exit 1; }

# Gate root documentation and canonical skill README diagrams once.
# Plugin mirrors and vendored references remain outside the authored corpus.
DOCS := README.md CONTRIBUTING.md CODING_STANDARDS.md GLOSSARY.md AGENTS.md \
        docs/CONVENTIONS.md plugins/README.md hooks/README.md kiro-conf/README.md web/richdocs-ui/README.md $(wildcard rules/*.md) \
        tools/README.md tools/AGENTS.md $(wildcard tools/*/README.md) $(wildcard tools/*/AGENTS.md)
SKILL_READMES := $(wildcard skills/*/README.md)
PLUGIN_READMES := $(wildcard plugins/*/README.md)

# One published CLI checks Markdown structure, prose and Mermaid. Preserve the
# existing prose scope; skill READMEs receive the Markdown and Mermaid checks.
SLOPSTOPPER := @jpeakai/remark-lint-slopstopper@latest

docs-ci:
	bunx $(SLOPSTOPPER) $(DOCS) $(PLUGIN_READMES)
	bunx $(SLOPSTOPPER) --mermaid-only $(SKILL_READMES)

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
