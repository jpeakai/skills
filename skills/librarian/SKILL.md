---
name: librarian
description: "Repo documentation organisation: the canonical document set (README, CONTRIBUTING, CODING_STANDARDS, agent file, ADR surface, GLOSSARY) exists and cross-links, and every doc (and every section in a doc) lives where its content says it belongs. Modes: (1) AUDIT (default): report missing, misfiled and misnamed docs and sections as a shelving plan; (2) APPLY: execute it with history-preserving moves and link rewrites; (3) INIT: bootstrap docs/CONVENTIONS.md from the repo's own dialect or a named flavour (minimal/standard/rigorous); (4) INDEX: curate YAML siblings so docs are queryable with jq/yq and schema-gated. Use when asked to organise repo docs, check doc layout or placement, add missing canonical docs, relocate or rename docs, make docs machine-readable or generate YAML indexes for markdown, adopt an okf-yaml/okf-yml/OKF ADR surface, or on 'librarian'. Skip when the ask is prose quality, staleness/drift, or within-one-file readability; content-quality skills own those."
argument-hint: "[audit | apply | init [minimal|standard|rigorous] | index [okf-yaml|okf-yml]] [paths] (default: audit whole repo)"
user-invocable: true
---

# Librarian

Shelves the repository's documentation: the right documents **exist**, carry the right **names**, live in the right **locations**, and **cross-link** as required.
Content is cargo: the librarian moves it, extracts it, and renames its containers, but never rewrites, fact-checks, or restyles it.
Whether a doc is true, current, or well written is out of scope by design.
Other skills own content quality, and they run independently of this one.

Resources (read on first use):
- [resources/baseline.md](resources/baseline.md): the universal compliance baseline (required document set, sibling/link obligations, canonical locations, docs/ taxonomy defaults, agent-file and naming rules).
- [resources/misplacement_smells.md](resources/misplacement_smells.md): the detection catalog of whole-document smells (M1-M10) and partial within-file smells (P1-P8), with severities and fixes.
  Load during audit.
- [resources/conventions_template.md](resources/conventions_template.md): the docs/CONVENTIONS.md template + bootstrapping guidance.
  Load for init, and during audit when the repo lacks a conventions file.
- [resources/flavours.md](resources/flavours.md): the named convention presets (minimal / standard / rigorous) and the graduation triggers for scale-up elements.
  Load for init, and during audit to check whether the repo has outgrown its declared flavour.
- [resources/adr_template.md](resources/adr_template.md): the preferred shape of one ADR, for either layout.
  The shape is a metadata table, then a Decision lens of Given / We prefer / Because / Unless, then Consequences.
  Load when an ADR surface is created, migrated, or found structurally incomplete.
- [resources/glossary_template.md](resources/glossary_template.md): the preferred shape of GLOSSARY.md (four-line intro, relationship diagram, one alphabetical H2 per Title Case term) and its structural findings.
  Load when GLOSSARY.md is created or audited.
- [resources/coding_standards_template.md](resources/coding_standards_template.md): the preferred shape of CODING_STANDARDS.md, its seven baseline tenets and its structural findings.
  Load when CODING_STANDARDS.md is created or audited.
- [resources/adr_decision_theory.md](resources/adr_decision_theory.md): the maintainer's definition of what a decision record captures (Facts, Value System, Lens, Decisional Balance, the Regulating Condition).
  Load with the template when authoring or migrating records, so the shape is filled with the right kind of content.
- [resources/structured_siblings.md](resources/structured_siblings.md): the machine-readable layout in general.
  It covers authored-YAML records with generated markdown, or generated YAML indexes beside authored markdown, plus the adoption triggers and verification gate.
  Load for index mode, and during audit only when the repo already has generated siblings.
- [resources/adr_okf_yaml.md](resources/adr_okf_yaml.md): the named `okf-yaml` ADR-surface convention.
  It holds the record schema, the typed relation vocabulary, OKF conformance of the generated markdown, the shelving-plan finding table, and the migration operation.
  Load when `okf-yaml` is named as an argument, when `docs/CONVENTIONS.md` declares it, or when an ADR surface is observed to follow it. `okf-yml` names the same convention: accept either spelling wherever the name is read, and write `okf-yaml` in everything the skill emits.
- [resources/evidence.md](resources/evidence.md): research citations and counter-evidence behind the baseline (dated; check freshness before extending doctrine).
- `resources/learned/` (if present): prior user adjudications on placement rulings.
  Treat as already-decided; do not re-litigate.

## Mode selection

- `audit` (default, bare `/librarian`): discover the dialect, inventory, report a shelving plan.
  Read-only: no file is created, moved, or renamed.
- `apply`: execute a shelving plan (from this session's audit, or a plan the user supplies/edits).
  Mutating; every operation is loss-free.
- `init`: generate `docs/CONVENTIONS.md` describing the repo's existing dialect and wire the root AGENTS.md reference to it.
- `index`: curate machine-readable YAML siblings for a document set: generate them, verify the round trip, and record the arrangement as a dialect line.
  Mutating; generated files only.
  Takes an optional named convention: `index okf-yaml adrs/` adopts or migrates to the [`okf-yaml` ADR surface](resources/adr_okf_yaml.md).
  `index okf-yml adrs/` names the same convention.
  Bare `index` indexes markdown in place without changing how anyone authors.
- A path argument scopes audit/apply to that subtree (monorepo package case); the dialect is still resolved from the repo root downward.

## Step 0: Discover the dialect (every mode)

Compliance is judged against an authority ladder; higher rungs win:

1. **Declared dialect**: `docs/CONVENTIONS.md` (or a file the root AGENTS.md names in that role).
   If present, its Dialect lines and Layout map are the oracle; the baseline fills only what it leaves unstated.
2. **Observed dialect**: strong existing conventions the repo already follows consistently (an established `adrs/` tree, an existing docs taxonomy, scoped ADR logs, a dated-filename habit).
   Consistency is the test: a pattern followed in ≥3 places is a convention, one file is not.
3. **Universal baseline**: [resources/baseline.md](resources/baseline.md).

State which rung answered each question.
**Never impose the baseline over a declared or consistently-observed choice**.
For example, a repo on single-file `ADRs.md` is compliant even though the baseline prefers file-per-decision at scale.
Migrating layouts is a recommendation for the user, not a finding.
Where the repo is *internally inconsistent* (two ADR layouts, three naming styles), the majority pattern is the dialect and the minority files are findings.

The agent-file role: `AGENTS.md` is the canonical agent file and holds every instruction.
Beside each one sits a `CLAUDE.md` whose entire content is the single line `@AGENTS.md`, so Claude Code imports the canonical file.
Detect `CLAUDE.md`, `AGENTS.md` or `AGENT.md` as evidence of the role.
Each of these is smell M3:

- a `CLAUDE.md` carrying anything beyond the import line,
- a symlink,
- an agent file with no `AGENTS.md`.

## Audit mode

### 1. Inventory

Glob `**/*.md` plus the extensionless canonicals (`LICENSE`, `CODEOWNERS`), skipping vendored/generated/`node_modules`/build output.
Record per doc: path, name-style, which charter it apparently serves, inbound links (grep its path and anchors), and whether any hub references it.
Build the charter table first: one line per existing doc, from the dialect's layout map or inferred from baseline roles.
Misplacement is judged against charters, never taste.

### 2. Check existence and links

Against the resolved dialect + baseline §1-§2:

- Required set present?
  (README, CONTRIBUTING, CODING_STANDARDS.md, AGENTS.md + CLAUDE.md stub, ADR surface, GLOSSARY.md; dialect-required extras.)
- ADR records structurally complete?
  Status, a decision statement, and the reasoning must be present.
  Missing parts are a finding against [resources/adr_template.md](resources/adr_template.md).
  The *quality* of the reasoning never is.
  Where the surface declares or demonstrably follows a **named convention**, judge against that convention's own finding table instead.
  For `okf-yaml`, that is [resources/adr_okf_yaml.md](resources/adr_okf_yaml.md).
- GLOSSARY.md structurally complete?
  Judge against the finding table in [resources/glossary_template.md](resources/glossary_template.md), never a definition's accuracy.
- CODING_STANDARDS.md carries every baseline tenet, mapped for every language the repo ships?
  Judge against the finding table in [resources/coding_standards_template.md](resources/coding_standards_template.md), never whether the code complies.
  A named convention is rung 1 or 2 evidence, so its rules displace the generic template, never the reverse.
- Required cross-links present?
  - AGENTS.md → ADR surface, with a check-before-you-ask line.
  - AGENTS.md → GLOSSARY.md, with both standing instructions: canonical terms for all naming, and new domain terms added in the same change.
  - Root AGENTS.md → CONVENTIONS.md when it exists.
  - README → CONTRIBUTING.
  - CONTRIBUTING and AGENTS.md → CODING_STANDARDS.md.
  - ADR index covers all scoped logs.
- Locations recognised?
  (health-file precedence, baseline §3.)
- Flavour still fits?
  Compare observed scale against the declared flavour's graduation triggers ([resources/flavours.md](resources/flavours.md)).
  Exceeded triggers become a **Graduation** section of the plan.
  They are 🟣 recommendations, applied only on user acceptance, never findings.

### 3. Detect misplacement

Apply [resources/misplacement_smells.md](resources/misplacement_smells.md): whole-document smells M1-M10 via the inventory; partial smells P1-P8 by reading each substantial doc's sections and asking which charter each serves.
For large repos, fan out read-only subagents, one per directory or doc cluster.
Each returns: finding → smell id → evidence (path / section heading + first line) → proposed move → confidence.
A section that plausibly serves two charters is reported with both candidates and a recommendation: uncertain is a question, not a move.

### 4. The shelving plan

```
## Librarian audit: <N> docs · <E> existence gaps · <W> misfiled docs · <S> misfiled sections
Dialect authority: <declared | observed | baseline> (per question where mixed)

| # | Finding | Smell | Evidence | Operation | Severity |
|---|---------|-------|----------|-----------|----------|
| 1 | CONTRIBUTING.md missing | M1 | required set | create stub + README link | 🔴 |
| 2 | Release process inside README §Deploy | P1 | README.md#deploy | extract → docs/how-to/release.md, leave link | 🟡 |
```

Order 🔴 → 🟡 → 🟣.
Each row's Operation is one of: **create-stub / move / rename / extract / merge / link / symlink**.
Offer:
- apply all,
- apply 🔴 only,
- report only.
  Findings the user rejects are recorded in `resources/learned/adjudications.md` (create on first use) so later audits honour the ruling.

## Apply mode

Execute the plan mechanically, one numbered finding per commit-sized step:

1. **Moves/renames preserve history**: `git mv` (never delete+create).
2. **Rewrite every inbound reference**: grep the old path and old anchors repo-wide (markdown links, agent-file pointers, code comments, configs); update all.
   For externally-linked docs (published READMEs), leave a one-line redirect stub at the old path; internal-only docs need no stub.
3. **Extracts are verbatim**: the section moves unchanged, though its heading level may be adjusted to fit the target.
   The source keeps a one-line link where the section was.
   Never reword cargo in transit: if a moved section looks wrong or stale, flag it for a content-quality pass; do not fix it here.
4. **Created stubs are minimal**: title, one-sentence charter, the required cross-links, and an explicit `<!-- librarian stub: content pending -->` marker.
   Authoring real content is out of scope.
   An ADR-surface stub also carries the record template for its layout from [resources/adr_template.md](resources/adr_template.md).
   File-per-decision gets it as `adrs/TEMPLATE.md`.
   A single-file log gets it as a closing `## Template` section in `ADRs.md`.
   That way the first real record is written in the Given / We prefer / Because / Unless shape.
5. **ADR operations keep citations resolvable**: renumbering is forbidden; layout migration (log ↔ file-per-decision) preserves ids and regenerates the index.
   Reformatting records to [resources/adr_template.md](resources/adr_template.md) is a separate, opt-in operation: it moves existing text under the template's headings and never rewrites a decision's substance.
6. **Verify before done**:
   - Every moved/renamed path resolves from every inbound link (grep the old path returns only stubs/history).
   - Required cross-links exist.
   - No file was lost (`git status` shows renames, not deletions).
   - Any table of contents in a touched file is regenerated.

## Init mode

Read [resources/conventions_template.md](resources/conventions_template.md) and [resources/flavours.md](resources/flavours.md).
With a flavour argument (`init standard`), the preset supplies the starting dialect.
Without one, apply the flavour-selection questions to the repo's evident use case, and say which flavour was chosen and why.
Then infer each Dialect line from what the repo already does.
This is rung 2 evidence: observed conventions outrank the preset.
Fill remaining gaps from the flavour, marking those lines as defaulted so the maintainer can veto.
Build the Layout map covering every doc-bearing path plus rows for missing required docs.
Wire the root AGENTS.md references (CONVENTIONS.md, ADR surface, GLOSSARY.md obligations, CODING_STANDARDS.md) in the same change, and write its sibling `CLAUDE.md` as exactly `@AGENTS.md`.
An existing full `CLAUDE.md` moves into `AGENTS.md` first (`git mv`), then the stub takes its place.
A missing GLOSSARY.md is written from [resources/glossary_template.md](resources/glossary_template.md) with its seed terms.
A missing CODING_STANDARDS.md is written from [resources/coding_standards_template.md](resources/coding_standards_template.md).
It carries all seven baseline tenets, then one section per language mapping each tenet to its enforcing tool or config.
Map each tenet to the tools the repo already uses.
A tenet with no enforcing tool yet is written as a gap for the maintainer to fill, never guessed.
Coding rules already sitting in CONTRIBUTING or AGENTS.md move into it (smell P8).
A missing ADR surface is created in the declared layout as a stub.
The stub carries that layout's record template from [resources/adr_template.md](resources/adr_template.md) (`adrs/TEMPLATE.md`, or a closing `## Template` section in `ADRs.md`).
Show the draft before writing when running interactively.

## Index mode

Curates machine-readable siblings for a document set.
Read [resources/structured_siblings.md](resources/structured_siblings.md) first: it holds the two arrangements, the adoption triggers, the output shape, and the gotchas.

1. **Check a trigger fired.** Adoption needs an observable consumer: a script, gate, or derived view that reads the records.
   Absent one, report that plain markdown is correct and stop; more structure is not a finding.
2. **Pick the arrangement and say which.** Authored-YAML (records become data, markdown is generated) or indexed-markdown (markdown stays authoritative, YAML is generated beside it).
   Default to indexed-markdown: it changes nothing about how anyone authors, and it is reversible by deleting the artifacts.
   A **named convention** short-circuits this choice.
   `okf-yaml`, spelled either way, selects authored-YAML with a fixed schema, relation vocabulary and bundle layout.
   Follow [resources/adr_okf_yaml.md](resources/adr_okf_yaml.md) from there, including its migration operation and verification gate.
3. **Generate.** For indexed-markdown, one index per document:

   ```sh
   bun run .claude/skills/librarian/scripts/md2yaml.ts <doc.md> --out <doc.yml>
   ```

   `--json` emits the same index for `jq` instead of `yq`; `--check` reconstructs the markdown and exits non-zero on any drift.

   For `okf-yaml`, copy `resources/okf_yaml/record.schema.json` and `scripts/templates/` into the repo, then render:

   ```sh
   uv run --no-project --with PyYAML --with Jinja2 --with jsonschema \
     .claude/skills/librarian/scripts/okf_render.py <bundle-dir>
   ```

   Validation runs first and hard: an invalid record stops the build rather than producing markdown nothing checked.
4. **Verify across the whole corpus, not a sample.** Every document must pass `--check`.
   A document that fails is reported with the construct that broke it; never "fix" the document to suit the tool.
5. **Wire the regeneration.** A make target, and a banner in each generated file naming its generator.
   An index regenerated by a remembered command is a stale index.
6. **Record the dialect.** Add the arrangement, the generated-path glob, and the regeneration command to `docs/CONVENTIONS.md` so later audits treat the artifacts as generated rather than as misfiled documents.

Generated siblings are build artifacts: exempt from naming and placement smells, never findings, and never hand-edited.

## Cross-cutting rules

- **Never judge content.** No finding may be "this is stale/wrong/verbose"; the only verdicts are missing, misnamed, misfiled, unlinked, duplicated.
- **Loss-free or not at all.** Every operation is reversible via git and leaves no dangling inbound link; deletion is never an operation (merge leaves a link behind).
- **Dialect beats baseline. Declared beats observed. User beats all.** Prior adjudications in `resources/learned/` are already-decided.
- **Audit is read-only**; only apply, init and index mutate.
  Init writes only missing core documents and the reference lines that wire them.
  The core documents are CONVENTIONS.md, the AGENTS.md + CLAUDE.md pair, GLOSSARY.md, CODING_STANDARDS.md, and the ADR surface with its template.
  Index writes only generated artifacts and never edits a source document to suit the generator.
- Respect the repo's file-size conventions when extracting (a target file near its size ceiling gets a new sibling, not a forced append).
- Report which authority rung answered each contested question so the user can audit the librarian's own reasoning.
