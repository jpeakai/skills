# Documentation conventions

The declared documentation dialect for this repository.
Consult it before creating, moving or renaming documentation.

## Dialect

- Flavour: **standard** (explicitly requested).
- Sources: root `skills/` and `hooks/` are canonical; plugin copies are generated (observed).
- Docs taxonomy: flat lowercase kebab-case topic files under `docs/` (standard default).
- Ticketing: repository workflow lives in `docs/TICKETING.md` (explicitly requested).
- Skill documentation: `skills/<name>/README.md` is a concise human overview with dual-density Mermaid diagrams (explicitly requested).
- Agent files: `AGENTS.md` is canonical; its sibling `CLAUDE.md` contains only `@AGENTS.md` (explicitly requested).
- Root ADR surface: `okf-yaml` in `adrs/NNNN-slug.yml`, rendered into Markdown, an index and a graph viewer (explicitly requested).
- Scoped decisions: existing skill-local logs remain in their current layout and retain accepted arguments (observed).
- ADR links: use relative links between bundle files and to scoped decision logs.
- Generated ADR paths:
  - `adrs/NNNN-*.md`
  - `adrs/index.md`
  - `adrs/graph.md`
  - `adrs/graph.json`
  - `adrs/graph.html`
- ADR regeneration: `make adrs`; validation and freshness: `make adr-ci`.
- Prose gate scope: root `prose-gates.config.json` anchors discovery to this repository and its glossary (observed tool requirement).
- Glossary: root `GLOSSARY.md`, alphabetical H2 terms and a relationship diagram (standard default).
- Coding standards: root `CODING_STANDARDS.md`, seven baseline tenets mapped to observed tools and explicit enforcement gaps (standard default).
- Proposals: no separate RFC surface (standard default).
- Release history: Git and plugin versions remain the observed record; a changelog is a future standard-flavour recommendation.
- Security reporting: no dedicated policy is declared; adding one requires a maintainer-supplied reporting route.

## Layout map

| Path | Charter | Audience | Changes when |
|---|---|---|---|
| `README.md` | Installation, skill catalog and repository overview | Consumers | Entry points change |
| `CONTRIBUTING.md` | Setup, validation and contribution workflow | Contributors | Workflow changes |
| `CODING_STANDARDS.md` | Coding tenets, tools and enforcement gaps | Contributors and agents | Standards change |
| `AGENTS.md` | Repository invariants and routing | Agents | Maintenance contracts change |
| `CLAUDE.md` | Import of sibling agent instructions | Claude Code | Import convention changes |
| `GLOSSARY.md` | Canonical domain vocabulary | Everyone | New terms appear |
| `docs/TICKETING.md` | Ticketing system and issue workflow | Contributors and agents | Ticket conventions change |
| `adrs/` | Root decision sources, templates and generated views | Everyone | A binding decision is recorded |
| `docs/CONVENTIONS.md` | Documentation dialect and placement | Everyone | Documentation layout changes |
| `skills/*/README.md` | Human skill overviews and workflow diagrams | Skill consumers | Skill behavior changes |
| `skills/*/AGENTS.md` | Scoped maintainer instructions and existing decision logs | Agents | Scoped maintenance rules change |
| `skills/*/SKILL.md` | Runtime skill instructions and discovery metadata | Agents | Runtime behavior changes |
| `skills/*/resources/` | On-demand references and existing scoped logs | Agents and maintainers | Supporting contracts change |
| `skills/*/docs/` | Existing skill-local documentation and decision surfaces | Maintainers | Scoped decisions change |
| `skills/*/scripts/` | Executable helpers and scoped maintenance instructions | Maintainers | Tool behavior changes |
| `skills/*/ARCHITECTURE.md` | Existing detailed architecture references | Maintainers | Skill architecture changes |
| `skills/richdocs/vendor/` | Upstream-owned reference snapshot | Maintainers | Documented refresh runs |
| `hooks/README.md` | Hook behavior and configuration | Consumers | Hook contract changes |
| `plugins/README.md` | Plugin composition and generation | Consumers and maintainers | Composition changes |
| `plugins/*/skills/`, `plugins/*/hooks/` | Generated canonical mirrors | Installed agents | `make fix` runs |
| `codex-conf/` | Codex configuration references | Consumers | Configuration changes |
| `rules/` | Reusable operating rules | Agents | Rule contracts change |
| `.claude/` | Existing local harness rules and configuration | Agents | Harness configuration changes |
| `tmp/` | Unpublished experiments and task evidence | Maintainers | Local work requires scratch space |

## Naming and links

- Root role documents use uppercase names; skill names and new topic filenames use lowercase kebab-case.
- Existing resource filenames keep their observed spelling unless a rename is explicitly requested.
- Each authored agent file has a regular import sibling; vendored files keep their upstream layout.
- README links to CONTRIBUTING; CONTRIBUTING and AGENTS link to CODING_STANDARDS.
- AGENTS links to this dialect, the glossary and the ADR index with a check-before-you-ask instruction.
- The root ADR index links scoped decision logs; accepted record arguments remain unchanged.
- Generated files are never hand-edited.

## Split triggers

- Split flat `docs/` into Diataxis categories when it exceeds ten topics or mixes reader purposes.
- Split a scoped agent file before it exceeds 500 lines; leave a pointer to the extracted material.
- Keep root agent instructions under 200 lines and use pointers for skill-specific rules.
