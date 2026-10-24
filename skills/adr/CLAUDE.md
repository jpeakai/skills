# adr: Maintainer Decision Lens

Read the ADR log below before changing anything.
Each ADR carries a **Lens**: apply it to the next decision instead of re-deriving the trade-off.

## Development contract

Code gates come first.
The skill carries `scripts/` in Python (uv): the okf-yaml generator and the compliance audit.
`ci` regenerates the shipped example bundle via `docs`, so a template change that stops reproducing the golden fails the gate.
Run from repo root, never `cd`:

```sh
make -C skills/adr/scripts fix   # mutates: format + lint --write
make -C skills/adr/scripts ci    # the gate: format-check, lint, typecheck, test-cov (≥90%), docs
```

Doc gates before handoff, also from repo root:

```sh
bunx @jpeakai/mermaidjs-lint skills/adr/README.md
uvx --from md-toc md_toc --in-place --no-list-coherence github --header-levels 4 skills/adr/README.md
```

All prose files ≤ 500 lines (the workspace skills rule).

## File map

| File | Role |
|------|------|
| `SKILL.md` | Agent operating manual: modes, surface discovery, the audit's check table, setup and migrate steps |
| `README.md` | Human explainer: purpose, quickstart, architecture diagram, troubleshooting |
| `resources/adr_template.md` | Preferred shape of one ADR, one block per layout (lazy; setup, migrate, audit) |
| `resources/adr_decision_theory.md` | What a decision record captures; the theory behind the lens (lazy) |
| `resources/adr_okf_yaml.md` | The named `okf-yaml` convention: schema, relation vocabulary, OKF conformance, finding table, migration, gate (lazy) |
| `resources/okf_yaml/record.schema.json` | The okf-yaml record contract, copied into an adopting repo |
| `resources/okf_yaml/example/` | Worked two-record bundle; the golden fixture `test_okf_render.py` diffs against |
| `scripts/okf_render.py` | Reference generator: validate, then build markdown + index + graph + viewer; `build()` writes nothing |
| `scripts/adr_audit.py` | The compliance audit: discovery, the eight checks, the findings table, exit 1 on 🔴 |
| `scripts/templates/*.j2` | Jinja templates, one per generated artifact |
| `scripts/test_okf_render.py`, `scripts/test_adr_audit.py` | pytest suites (PEP-723 entry points), real git repos in `tmp_path` |
| `scripts/conftest.py` | Coverage reload fixture for both modules |
| `scripts/Makefile` | `fix` / `ci` quality gates, plus `docs` (regenerate the example bundle) |
| `CLAUDE.md` | This file: rationale and decision log |

## Architecture principles

- Structure only: a record's reasoning is cargo, never judged.
- Accepted means immutable: a change of mind is a new record that supersedes the old one, both ways.
- Generated files are never hand-edited; the source record or the template is fixed instead.
- Audit is read-only and deterministic; setup, migrate and render mutate, and each ends by running audit.

## ADR log

Ids continue the librarian's sequence, because the records under [Carried from librarian](#carried-from-librarian) keep their numbers.
A new record takes the next number after the highest in either log, so no two records here ever share an id.

### ADR-25: decision records are their own skill

- **Status:** Accepted (2026-10-24, user instruction, issue #27); the counterpart of librarian ADR-24.
- **Context:** The librarian owns placement, but ADRs had grown a template, a schema, a relation vocabulary, a generator with a viewer, layout migration and decision theory.
  Every docs-organisation task loaded that weight, and nobody could ask whether an ADR surface was compliant on its own.
- **Decision:** This skill owns the inside of the ADR surface: setup, migrate, render and audit.
  The files moved with `git mv`, and the librarian's decision records about them moved here verbatim, below.
  The librarian keeps only presence and the AGENTS.md link, and points here by name.
- **Consequences:** The librarian is TypeScript only; this skill is Python only.
  Two skills now name the ADR surface, so their boundary is a rule: placement there, contents here.
- **Lens:** If a question is about where the surface lives or whether it is linked, it is the librarian's.
  If it is about anything inside it, it is this skill's.

### ADR-26: the audit is a script with an exit code, not a reading the agent performs

- **Status:** Accepted (2026-10-24, issue #27); partially superseded by ADR-28 (the eval fixtures it pins are gone).
- **Context:** The issue asked for an audit that can gate CI, and every check it named is computable: schemas, byte equality, sequences, git history, link targets.
  An agent reading records would be slow, billed, and different on every run.
- **Decision:** `adr_audit.py` runs all eight checks and exits 1 on any 🔴 finding, so one command serves the agent and CI.
  Severity is fixed per check: 🔴 for violations, 🟡 only for a one-way okf-yaml relation, a `.md` with no `.yml` source, and missing git history.
  Freshness compares an in-memory `build()` with the files on disk, so the audit never writes, and a bundle's own `templates/` and `record.schema.json` win over the skill's.
- **Consequences:** `okf_render.render` split into `build` (pure) and a writer, with the golden bundle proving the split changed no bytes.
  Both eval fixtures are pinned in `test_adr_audit.py`, so a failing live eval means the agent, not the script.
- **Lens:** When a check can be computed, compute it in a script and let the agent present the result.
  Keep the agent's reading for judgements a script cannot make, and this skill makes none of those about reasoning.

### ADR-27: an accepted record's argument is everything supersession may not touch

- **Status:** Accepted (2026-10-24, issue #27).
- **Context:** Immutability has to allow exactly the edits the template permits: a Status row moving to superseded, a Relates to row gaining the successor, and a partial-supersession marker on a clause.
  Anything else changed after acceptance is a rewrite.
  Run against a real corpus, the first version flagged the removal of `in_practice`, a key the schema itself dropped (ADR-16), as an edit.
- **Decision:** For markdown, the argument is every line except those naming status, relates to or superseded, with partial-supersession markers stripped first, whitespace collapsed.
  For okf-yaml, it is the title, the four lens fields and the consequences.
  The baseline is the record as of the first commit that showed it accepted; uncommitted edits count.
- **Consequences:** Rewording a lens field after acceptance is caught, and was caught on a real repo the first time the audit ran.
  A reformat to the template during migration shows up too, and the maintainer accepts it as part of that migration.
- **Lens:** Define "unchanged" as the complement of the edits the doctrine allows, and test both sides: each allowed edit passes, and a one-word rewording fails.

### ADR-28: the skill carries no evals

- **Status:** Accepted (2026-10-24, user instruction, issue #27); partially supersedes ADR-26 (its eval fixture pinning).
- **Context:** The skill shipped `evals/` with one live agent scenario per mode and seed fixtures, and `test_adr_audit.py` pinned those fixtures.
  ADR-26 already moved every check into a deterministic script, so a live eval re-tested the agent presenting a result the unit tests prove.
  The maintainer ruled the evals unwanted.
- **Decision:** `evals/` is removed, along with the two tests that audited its fixtures.
  Each check keeps its compliant and per-violation tests built in `tmp_path`, so the fixtures carried no coverage of their own.
- **Consequences:** `make -C skills/adr/scripts ci` is the skill's only gate, and nothing bills an agent session before a release.
  A change to how the agent drives the modes is checked by reading SKILL.md, not by a scenario.
- **Lens:** When a script's tests already prove a behaviour, do not add a billed agent run to prove it again.

## Extension checklist

- [ ] A new check enters `adr_audit.py` with its severity fixed, a compliant test and one test per violation, and a row in SKILL.md's check table (ADR-26).
- [ ] A change to the record shape lands in `adr_template.md` (both layout blocks), `record.schema.json`, `record.md.j2` and the example records together, then `make -C skills/adr/scripts docs` (ADR-16/17).
- [ ] A change to what supersession may edit updates `MUTABLE_LINE` / `LENS` and adds a passing and a failing test (ADR-27).
- [ ] Any change under `scripts/` leaves `make -C skills/adr/scripts ci` at exit 0, coverage ≥ 90%.
- [ ] Prose stays brand-agnostic, and every prose file ≤ 500 lines.

## Known gotchas

- YAML resolves an unquoted `2026-08-30` to a date, not a string, so a JSON Schema `"type": "string"` rejects it.
  Validate the JSON projection, not the raw load.
- `graph.html` embeds its bundle directory's name, so a bundle copied under a new name is stale until rendered again.
  The audit reports it as a `fresh` finding.
- Discovery skips any directory holding its own `.git`, and every `fixtures/` directory.
  An audit run from a parent repo would otherwise sweep in child repos, worktrees and test data.
- A record mentioned only as `ADR-NNNN` inside a template section is not a record: log sections are recognised by a heading with digits.
- A repo without git history cannot prove immutability; that is a 🟡 finding, never a silent pass.

## Carried from librarian

Moved verbatim by librarian ADR-24, so their ids, wording and the paths they name are the librarian's at the time they were accepted.

### ADR-8: the preferred ADR format is a template the skill carries, not just a layout

- **Status:** Accepted (2026-08-25, user instruction)
- **Context:** The baseline covered where decision records *live* (single-file log vs file-per-decision) and said nothing about what one record *looks like*.
  So an audit could pass a repo whose ADRs were undated one-line bullets, and init produced an ADR surface with no shape to fill.
  Meanwhile the maintainer converged on a specific record format elsewhere in this repo.
  It has a metadata table, a `Lens` blockquote holding the reusable rule, then Problem / Decision / Consequences under their own headings.
  The decision itself is written as `Given` / `We prefer … over …` / `Because` / `Unless`.
- **Decision:** Adopt that format as the librarian's preferred one, and carry a **copy** at `resources/adr_template.md`.
  The copy is adapted to work in either layout (a file, or a section with headings demoted).
  Format is a dialect line like any other, so it sits at rung 3 of the authority ladder (ADR-2).
  A declared or consistently observed local format wins, and an accepted record is never rewritten to match.
  The skill uses it structurally only (ADR-1): a record missing Status, a decision statement, or reasoning is a finding; weak reasoning is not.
- **Provenance:** the format originates in the `concise-decisions` skill in this repo, which developed it over four layout iterations.
  This maintainer document may name that origin; no runtime surface here points at it.
  The copy is the skill's own, and it drifts from the origin on purpose (skills are self-contained).
- **Consequences:** Init now writes a `TEMPLATE.md` alongside the ADR surface and records the format as a Dialect line.
  Reformatting an existing log becomes an opt-in APPLY operation that preserves every id and anchor.
  This skill's own log (above) predates the format and has not been migrated.
  That is exactly the "never rewrite an accepted record" rule applied to itself.
- **Lens:** When the skill recommends a shape, ship the shape as a file it owns, not as prose describing one.
  A template can be copied into a repo, diffed, and vetoed; a paragraph saying "ADRs should have a status" cannot.
  Copy it in rather than pointing at wherever it came from.

### ADR-11: the convention ships its artifacts, and the skill goes mixed-language to run them

- **Status:** Accepted (2026-08-30, user decision)
- **Context:** ADR-10 made the convention invocable, but `adr_okf_yaml.md` still only *described* the schema and the bundle in fenced blocks.
  ADR-8's lens already names that failure: "ship the shape as a file it owns, not as prose describing one".
  That lens had been applied to the record and not to the bundle.
  Three options were weighed:
  - schema plus golden fixtures only
  - a TypeScript port keeping the skill single-language
  - vendoring the working Python/Jinja generator as-is

  The maintainer chose the last: the generator is proven over a real corpus, and a port would trade that evidence for toolchain tidiness.
- **Decision:** Vendor the generator and its Jinja templates unchanged in substance.
  Accept the **mixed-language scripts contract**:
  - one Makefile fanning out to `-py` and `-ts` sub-targets
  - `conftest.py`
  - pytest via PEP-723
  - ruff and mypy alongside biome and tsc
  - ≥90% coverage on both

  The schema and a two-record worked bundle ship under `resources/okf_yaml/`, and that bundle is the **golden fixture**.
  `ci`'s `docs` target regenerates it, and the Python suite fails if the output drifts.
  So a generator ported to any other language has bytes to conform to.
  Genericisation is the price of vendoring: hardcoded group names became data (`group`, or `--group-by tag|plan_id`), and the author became `--author`.
- **Consequences:** A contributor now needs both `uv` and `bun` to run `ci`.
  The README says so under requirements rather than letting it surface as a failure.
  Adopting repos are expected to port the generator to their own language, which is exactly what the golden fixture is for.
  Porting found a real defect the prose could not have.
  A null field rendered as `plan_id: None`, which parses as the string `'None'`.
  The defect was present in the origin bundle too, and fixed in both.
- **Lens:** Vendor the working implementation over a cleaner rewrite when the implementation carries evidence a rewrite would discard.
  Pay the toolchain cost openly in the requirements.
  But never vendor an artifact without a **fixture that pins its output**.
  The generator is the part that will be replaced, and the bytes it produces are the part that must not change.

### ADR-12: the okf-yaml bundle always ships a viewer, and it is self-contained

- **Status:** Accepted (2026-09-01, user instruction)
- **Context:** The bundle emitted `graph.json` (a Cytoscape payload) and `graph.md`.
  The fenced `cytoscape` block in `graph.md` only renders inside a companion HTML pipeline the skill does not own.
  So the typed relation graph, the whole point of ADR-10's convention, had no reader in a plain checkout.
  A graph nobody can see is a graph nobody checks.
  One-way edges, orphaned records and mis-grouped decisions all survive review, because reviewing them means reading JSON.
  The maintainer supplied a working viewer from a real corpus rather than a specification.
- **Decision:** Generate `graph.html` **unconditionally**, as one self-contained file.
  It holds three inlined data blocks (elements, every record's rendered markdown, design tokens) and two CDN scripts.
  It shows a graceful message when the network is absent.
  The layout is a deterministic shelf-pack computed from sorted record ids, not a force layout, so the committed file does not redraw on every rebuild.
  Tokens come from an optional repo-supplied `tokens.json`, falling back to defaults carried in the generator, so a missing brandpack cannot break the page.
- **Consequences:** Every bundle grows one large generated file whose diff is dominated by inlined JSON; compact separators keep that as small as it can be.
  The viewer's absence is now a 🔴 finding, and the verification gate checks the data blocks are inlined.
  A record whose prose contains `</script>` would have closed the tag and spilled into the document.
  So the generator escapes `</` before embedding.
  The defect was found while writing the test, not in review.
- **Lens:** When a convention derives a machine-readable artifact, ship the thing that makes it *legible to a human* in the same breath.
  Generate it unconditionally.
  An opt-in viewer is one nobody enables, which returns the derived data to the unchecked state it was created to escape.
  Prefer a deterministic rendering over a prettier non-deterministic one: a generated file that changes on every rebuild stops being reviewable, and review is the point.

### ADR-16: the ADR template is metadata, the decision lens, and consequences

- **Status:** Accepted (2026-10-05, user instruction); supersedes the record shape described in ADR-8 and the fields fixed in ADR-10/11.
- **Context:** The template carried a summary `Lens` blockquote, a Problem section (Symptom / Pain point) and an `In practice` list.
  The maintainer ruled all three invented.
  Given / We prefer / Because / Unless *is* the decision lens.
  Problem restates Given, and In practice is noise.
  The template also mandated an em-dash and an interpunct while its own filling rule banned both.
- **Decision:** `adr_template.md` is a metadata table, `## Decision` with H4 Given / We prefer / Because / Unless, then `## Consequences`, in plain punctuation.
  Three changes follow:
  - the okf-yaml schema drops `lens`, `problem` and `decision.in_practice`
  - `record.md.j2` renders the lens as H4 headings
  - the example bundle and eval fixture are regenerated
- **Consequences:** Existing okf-yaml records carrying the removed keys now fail validation (`additionalProperties: false`); migrating them is deleting three keys, never rewording.
- **Lens:** A template field must earn its place by carrying information no other field carries.
  A field that restates another, or that agents added because a template had a slot for it, is removed.

### ADR-17: every ADR layout carries the lens, and every ADR surface the skill creates carries its template

- **Status:** Accepted (2026-10-05, user instruction); extends ADR-16 and makes ADR-8's "init writes a TEMPLATE.md" operative.
- **Context:** ADR-16 fixed one record's shape, but the single-file layout was only described as "the same with headings demoted".
  That left each agent to derive it by hand.
  The evals also showed init never created an ADR surface.
  So ADR-8's TEMPLATE.md was never written, and the first real record had no shape to copy.
- **Decision:** `adr_template.md` carries one complete block per layout, both with Given / We prefer / Because / Unless:
  - file-per-decision (H1 title, H4 lens headings)
  - single-file log section (H2 title, H5 lens headings)

  Init creates a missing ADR surface in the declared layout.
  Any ADR-surface stub (init or apply) carries its layout's block: `adrs/TEMPLATE.md`, or a closing `## Template` section in `ADRs.md`.
- **Consequences:** Init now writes five core documents, not four; the init eval asserts the template's lens headings.
- **Lens:** A shape that has to be derived is a shape that drifts: ship every variant the skill can produce as its own copyable block.

### ADR-23: generated record prose puts one sentence on each line

- **Status:** Accepted (2026-10-17, user instruction); extends ADR-16.
- **Context:** Prose gates that require one sentence per line now also report a line that holds several sentences, not only a sentence wrapped across lines.
  A record field of two sentences rendered onto one line, so every bundle with such a field failed its own repo's docs gate.
  The output is generated, so the fix belongs in the template, never in the markdown, and never by rewording accepted records.
- **Decision:** `okf_render.py` gains a `one_sentence_per_line` filter, and `record.md.j2` applies it to the four lens fields and to every pros and cons item.
  A list item's later sentences continue on lines indented two spaces, so they stay inside the item.
  A sentence break is the prose gate's own rule: a terminal, then space, then a capital or an opening delimiter, with code spans masked.
- **Consequences:** A single-sentence field renders byte-identical, so the golden example is unchanged.
  An abbreviation followed by a capital, such as "Dr. Smith", splits as the prose gate would split it.
- **Lens:** When generated output fails a gate, fix the generator at its source and prove the fix on the golden fixture.
  Match the gate's rule exactly, so the generator and the gate never disagree about a sentence.
