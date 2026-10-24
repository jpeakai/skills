---
name: adr
description: "Architecture decision records: set up an ADR surface, migrate it between layouts, render an okf-yaml bundle, and audit a repo's decisions for compliance. Modes: (1) AUDIT (default): check records parse, the bundle is fresh, ids are stable, accepted records are unedited, relations resolve, supersession is marked both ways, the agent file is wired and the index covers every scoped log, exiting non-zero on a violation so it can gate CI; (2) SETUP: create a surface (single-file ADRs.md, file-per-decision, or okf-yaml) with its template and agent-file link; (3) MIGRATE: move records between layouts, keeping every id; (4) RENDER: regenerate an okf-yaml bundle from its .yml records. Use when asked to set up, check or audit ADRs or decision records, adopt okf-yaml/okf-yml, render an ADR bundle, migrate an ADR log, or on 'adr'. Skip when the ask is where documents live in general, or whether a decision's reasoning is good. Needs uv, and pypi.org on first run."
argument-hint: "[audit [surface...] | setup [log|files|okf-yaml] | migrate <log|files|okf-yaml> | render <bundle-dir>] (default: audit)"
user-invocable: true
---

# ADR

Keeps a repo's architecture decision records sound: the surface exists in a declared layout, every record has the right shape, accepted decisions stay accepted, and relations hold both ways.
A record's reasoning is cargo: this skill checks that it is present, never whether it is good.

Resources (read on first use):
- [resources/adr_template.md](resources/adr_template.md): the preferred shape of one record, one block per layout.
  It is a metadata table, then a Decision lens of Given / We prefer / Because / Unless, then Consequences.
  Load for setup, for migrate, and when audit reports a record missing a part.
- [resources/adr_decision_theory.md](resources/adr_decision_theory.md): what a decision record captures (Facts, Value System, Lens, Decisional Balance, the Regulating Condition).
  Load with the template when authoring or migrating records.
- [resources/adr_okf_yaml.md](resources/adr_okf_yaml.md): the named `okf-yaml` convention: record schema, relation vocabulary, bundle layout, finding table, migration and verification gate.
  Load whenever `okf-yaml` or `okf-yml` is named, declared in `docs/CONVENTIONS.md`, or observed.
  Accept either spelling; write `okf-yaml` in everything the skill emits.
- `resources/okf_yaml/`: the record schema and a worked two-record bundle that doubles as the generator's golden fixture.
- `resources/learned/adjudications.md`: prior user rulings on the conventions above.
  Treat each as decided; do not re-raise a finding it rejects, and append a new ruling in the same session it is made.

Scripts run from this skill's base directory, shown here as `<skill>`:

```sh
uv run --no-project --with PyYAML --with Jinja2 --with jsonschema <skill>/scripts/adr_audit.py [repo] [--surface PATH ...] [--json]
uv run --no-project --with PyYAML --with Jinja2 --with jsonschema <skill>/scripts/okf_render.py <bundle-dir>
```

## Mode selection

- `audit` (default): run the checks and report. Read-only.
- `setup [log|files|okf-yaml]`: create a surface where none exists.
- `migrate <log|files|okf-yaml>`: move an existing surface to another layout.
- `render <bundle-dir>`: regenerate an `okf-yaml` bundle from its records.

## Step 0: find the surface (every mode)

1. **Declared**: a Dialect line in `docs/CONVENTIONS.md` naming the layout and path wins.
2. **Observed**: `adr_audit.py` discovers `adrs/`, `adr/` and `decisions/` directories and `ADRs.md` / `DECISIONS.md` logs, shallowest first, skipping nested repos and test fixtures.
   The shallowest is the root surface; deeper ones are scoped logs.
3. **None**: audit reports it; setup creates one.

Say which rung answered.
Never impose a layout over a declared or observed one: migrating is a recommendation, not a finding.

## Audit mode

Run `adr_audit.py` on the repo root.
Name the surfaces with `--surface` (root first) only when discovery picks the wrong ones.
It exits 1 on any 🔴 finding, so the same command gates CI.

| Check | 🔴 when | 🟡 when |
|---|---|---|
| `schema` | an `okf-yaml` record fails its schema (the bundle's own `record.schema.json` wins); a markdown record has no Status, decision statement or reasoning | |
| `fresh` | an `okf-yaml` generated file is missing or differs from a fresh build | a `.md` in the bundle has no `.yml` source |
| `ids` | a number is used twice, the sequence has a gap, or a record sits in a misnumbered file | |
| `immutable` | an accepted record's argument changed, or the record was removed, since the first commit that showed it accepted | the surface has no git history to check |
| `relations` | a relation or id mention names a record that does not exist | an `okf-yaml` relation has no inverse on the far record |
| `superseded` | a superseding record's target is not marked superseded, or a superseded record names no successor | |
| `wiring` | no root agent file, it never links the root surface, or it has no check-before-you-ask line | |
| `index` | the root index misses a scoped log, or a file-per-decision index misses a record | |
| `presence` | no surface exists | |

The argument of a record is everything except its Status and Relates to lines and partial-supersession markers, so marking a record superseded is never an edit.
For `okf-yaml` it is the title, the four lens fields and the consequences.

Present the script's table as the report, then offer the fix for each row.
Fixes are setup, migrate or render operations, or edits the maintainer makes to a source record.
Never rewrite an accepted record to clear an `immutable` finding: the remedy is a revert, or a new record that supersedes it.

## Setup mode

1. Pick the layout: the argument, else the declared one, else ask once with a recommendation.
   Recommend file-per-decision for most repos and a single-file log for small ones.
   Recommend `okf-yaml` only when an observable consumer reads the records (a script, gate or derived view), per [resources/adr_okf_yaml.md](resources/adr_okf_yaml.md).
2. Write the surface with its template from [resources/adr_template.md](resources/adr_template.md):
   - file-per-decision: `adrs/` with `adrs/TEMPLATE.md` and an index `adrs/README.md`
   - single-file log: `ADRs.md` opening `# Decisions`, with a closing `## Template` section
   - `okf-yaml`: follow the convention's layout, copying `record.schema.json` and the templates in, then render
3. Wire the agent file: link the surface from `AGENTS.md` beside a line telling the agent to check existing decisions before raising a question.
   With no agent file, create `AGENTS.md` and a `CLAUDE.md` holding exactly `@AGENTS.md`.
4. Add the layout as a Dialect line to `docs/CONVENTIONS.md` when that file exists.
5. Run audit. Setup is done only at exit 0.

## Migrate mode

An opt-in operation, one commit-sized step at a time:

1. **Ids never change.** No renumbering; every `ADR-NNNN` citation and anchor still resolves after the move.
2. **Text travels verbatim.** A record's argument after migration is byte-identical to before; only headings deepen or flatten to fit the layout.
3. Log to files: one file per section, named `NNNN-slug.md`, then the index. Files to log: one section per file, in id order. Use `git mv` wherever one file maps to one file.
4. To `okf-yaml`: follow the migration operation and verification gate in [resources/adr_okf_yaml.md](resources/adr_okf_yaml.md), and list every prose relation that becomes a typed edge before running it.
5. Keep the old surface until the new one passes audit, then swap in one commit and update every inbound link.
6. Update the Dialect line, then run audit. Migration is done only at exit 0.

## Render mode

Run `okf_render.py <bundle-dir>`.
Validation runs first and hard: an invalid record stops the build rather than producing markdown nothing checked.
A one-way relation is reported and the build still succeeds.
Fix a failure in the `.yml` record, never in the generated `.md`.
`--schema` points at the repo's own schema once it diverges; `--group-by tag|plan_id` and `--author` shape the graph and frontmatter.

## Cross-cutting rules

- **Never judge reasoning.** The only verdicts are missing, malformed, edited after acceptance, unresolved, unmarked, unwired and unindexed.
- **Accepted means immutable.** A change of mind is a new record that supersedes the old one, with links both ways.
- **Generated files are never hand-edited.** Fix the source record or the template, then render.
- **Audit is read-only**; setup, migrate and render mutate, and each finishes by running audit.
