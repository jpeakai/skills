# Repository agent instructions

## Read before changing files

- Follow [docs/CONVENTIONS.md](docs/CONVENTIONS.md) for documentation placement and naming.
- Check existing decisions before asking a question: [adrs/index.md](adrs/index.md).
  Read the affected skill's scoped decision log too.
  Apply recorded reasoning before asking the maintainer to decide again.
- Follow [CODING_STANDARDS.md](CODING_STANDARDS.md) before writing code.
  Contributor commands and delivery workflow live in [CONTRIBUTING.md](CONTRIBUTING.md).
- Use the canonical terms in [GLOSSARY.md](GLOSSARY.md) for identifiers, documentation and prose.
  Add new domain terms to the glossary in the same change that introduces them.
- Read the nearest skill's `AGENTS.md` when present.
  These files guide maintenance; `SKILL.md` and its resources define a skill's runtime behavior.

## Sources and generated output

- Edit canonical skills in `skills/` and canonical hooks in `hooks/`.
  Declare plugin membership in `plugins/composition.yaml`, then run `make fix`.
- Never hand-edit `plugins/*/skills/` or `plugins/*/hooks/`.
  Keep each plugin's Claude and Codex manifests consistent.
- Preserve `skills/richdocs/vendor/` as an upstream-owned snapshot.
  Refresh it through the documented procedure rather than patching individual files.
- Keep `evals/` only in canonical skills; exclude it from vendor snapshots and plugin output.
- Every authored `AGENTS.md` has a regular sibling `CLAUDE.md` containing only `@AGENTS.md`.
  Preserve existing instructions and accepted decision arguments when moving agent files.
- Every canonical skill has a concise human overview in `README.md`.
  Include an always-visible Mermaid overview and a more detailed diagram inside `<details>`.
  Keep README guidance distinct from the runtime instructions in `SKILL.md`.
- Keep examples generic under the [agnostic skill](skills/agnostic/SKILL.md).
  Do not add client names, private repository paths or extraction history to maintained documentation.

## Decisions and checks

- Author repository decisions as `adrs/NNNN-slug.yml` using [adrs/TEMPLATE.yaml](adrs/TEMPLATE.yaml).
  Accepted arguments are immutable; record a changed decision through supersession and reciprocal relations.
  Run `make adrs` after source or template changes; never edit generated decision views.
- Run `uv run scripts/validate_plugins.py` and `uv run pytest` after composition or publication changes.
- Run `make docs-ci` after authored documentation changes.
  It includes every canonical skill README and checks Mermaid parsing, complexity and contrast.
- Run the affected skill's `scripts/Makefile` gate when changing its executable code.
  Run `make adr-ci` for repository decision changes.
- `make ci` expects committed generated files and a clean tree.
  During uncommitted work, run its applicable component checks and report their actual results.
- Preserve unrelated work and existing authorization boundaries.
  Commits, pushes, releases and external writes follow the user's request; a documentation change alone does not authorize publication.
