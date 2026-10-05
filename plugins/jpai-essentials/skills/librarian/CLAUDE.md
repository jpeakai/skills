# librarian: Maintainer Decision Lens

Read the ADR log below before changing anything.
Each ADR carries a **Lens**: apply it to the next decision instead of re-deriving the trade-off.

## Development contract

Code gates come first.
The skill carries `scripts/` in two languages: TypeScript (bun) for the indexer, Python (uv) for the okf-yaml generator.
`ci` regenerates the shipped example bundle via `docs`, so a template change that stops reproducing the golden fails the gate.
Run from repo root, never `cd`:

```sh
make -C skills/librarian/scripts fix   # mutates: format + lint --write, both languages
make -C skills/librarian/scripts ci    # the gate: format-check, lint, typecheck, test-cov (≥90%), docs
```

Doc gates before handoff, also from repo root:

```sh
bun run skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts   skills/librarian/README.md skills/librarian/ARCHITECTURE.md
bun run skills/mermaidjs-diagrams/scripts/mermaid_complexity.ts skills/librarian/README.md skills/librarian/ARCHITECTURE.md
uvx --from md-toc md_toc --in-place --no-list-coherence github --header-levels 4 skills/librarian/README.md
```

Eval matrix before a release, from repo root (`--dry-run` is free; a live run bills one agent session per case):

```sh
uv run pytest skills/librarian/evals --dry-run
uv run pytest skills/librarian/evals -v
```

All files ≤ 500 lines (the workspace skills rule, `../../.claude/rules/claude_skills/index.md` from repo root).

## File map

| File | Role |
|------|------|
| `SKILL.md` | Agent operating manual: modes, authority ladder, audit steps, apply invariants |
| `README.md` | Human explainer: purpose, quickstart, architecture diagram |
| `ARCHITECTURE.md` | Dual-density diagrams per lens + the permutation axes and their eval coverage |
| `evals/` | pytest-xharness-eval scenarios, one per permutation row, with seed fixtures |
| `resources/baseline.md` | Universal compliance baseline: required set, locations, naming, ADR/agent-file rules (lazy) |
| `resources/misplacement_smells.md` | Detection catalogue: M1-M10 whole-doc + P1-P8 within-file smells (lazy; audit) |
| `resources/conventions_template.md` | docs/CONVENTIONS.md template + bootstrapping guidance (lazy; init) |
| `resources/flavours.md` | Named presets (minimal/standard/rigorous) + graduation triggers (lazy; init + audit) |
| `resources/adr_template.md` | Preferred shape of one ADR, one block per layout (lazy; init + audit + apply) |
| `resources/adr_decision_theory.md` | What a decision record captures; the theory behind the lens (lazy) |
| `resources/glossary_template.md` | Preferred shape of GLOSSARY.md + structural finding table (lazy; init + audit) |
| `resources/coding_standards_template.md` | Preferred shape of CODING_STANDARDS.md: seven baseline tenets mapped per language, structural findings (lazy; init + audit) |
| `resources/structured_siblings.md` | Machine-readable layouts in general: authored-YAML vs indexed-markdown, triggers, output shape, gotchas (lazy; index mode) |
| `resources/adr_okf_yaml.md` | The named `okf-yaml` ADR-surface convention: record schema, relation vocabulary, OKF conformance, finding table, migration (lazy; named or observed) |
| `resources/okf_yaml/record.schema.json` | The okf-yaml record contract, copied into an adopting repo |
| `resources/okf_yaml/example/` | Worked two-record bundle; doubles as the golden fixture the Python suite diffs against |
| `scripts/okf_render.py` | Reference generator: validate, then render markdown + index + graph + viewer |
| `scripts/templates/*.j2` | Jinja templates, one per generated artifact (including `graph.html.j2`) |
| `scripts/test_okf_render.py` | pytest suite (PEP-723 entry point) |
| `scripts/conftest.py` | Coverage reload fixture |
| `resources/evidence.md` | Research citations + counter-evidence, dated 2026-07-23 |
| `scripts/md2yaml.ts` | The markdown → YAML/JSON indexer; `--check` is the byte-exact round-trip gate |
| `scripts/md2yaml.test.ts` | `bun:test` suite: structure, tables, lists, whitespace fields, CLI via subprocess |
| `scripts/Makefile` | `fix` / `ci` quality gates, plus `docs` (regenerate the example bundle) and `install` (bun deps) |
| `resources/learned/` | User adjudications on placement rulings (created on first rejection; already-decided) |
| `CLAUDE.md` | This file: rationale and decision log |

## Architecture principles

- Placement, existence, naming, linking only: content is cargo, never judged.
- Loss-free operations: `git mv`, inbound-link rewrites, link stubs; deletion is never an operation.
- Authority ladder: declared dialect > observed dialect > baseline; user adjudications beat all.
- Audit is read-only; apply, init and index mutate, and index writes only generated files.

## ADR log

### ADR-1: the skill judges location, never content

- **Status:** Accepted (2026-07)
- **Context:** The maintainer runs separate skills for content quality (drift/staleness, prose, within-one-file structure).
  The maintainer wants fine-grained independent control: organisation passes and quality passes must be composable without either being aware of the other.
  Mixing them would also make apply-mode diffs unreviewable (moves hiding rewrites).
- **Decision:** The librarian's verdict vocabulary is closed: missing, misnamed, misfiled, unlinked, duplicated.
  Extracted/moved content travels verbatim; a section that looks wrong in transit is flagged for a content-quality pass, never fixed here.
  The skill names no sibling skill and reads no sibling's files (skills are self-contained).
- **Consequences:**
  - Apply diffs are pure moves and reviewable as such.
  - The skill composes with any content-quality tooling.
  - Some obviously-stale text gets relocated untouched, which is correct.
- **Lens:** If a candidate feature needs to read a sentence to judge its *quality* rather than its *charter*, it belongs in a different skill.
  Charter questions ("which document should hold this?") are in; quality questions ("is this good/true?") are out.

### ADR-2: compliance resolves through a three-rung authority ladder

- **Status:** Accepted (2026-07)
- **Context:** Research found no ecosystem-standard docs layout to enforce.
  GitHub's health-file precedence, Diátaxis, and ADR conventions are strong defaults.
  But real repos hold deliberate local choices (single-file ADR logs, federated scoped logs, Ways-of-Working in README instead of CONTRIBUTING).
  A skill that imposes the textbook layout over a working local dialect creates churn, not compliance.
- **Decision:** Declared dialect (`docs/CONVENTIONS.md`) > observed dialect (a pattern consistently followed, ≥3 instances) > researched baseline.
  Internal inconsistency resolves to the majority pattern; the minority files are the findings.
  Baseline-preferred migrations (e.g. log → file-per-decision) are recommendations, never findings.
- **Consequences:** The audit must state which rung answered each contested question; two repos can both be fully compliant with different layouts.
- **Lens:** The librarian enforces *coherence with the repo's own declared or demonstrated system*, and only invents an answer (baseline) where the repo has none.
  Never file a finding whose only evidence is "the baseline prefers otherwise".

### ADR-3: docs/CONVENTIONS.md is the declared-dialect surface, and init describes rather than prescribes

- **Status:** Accepted (2026-07)
- **Context:** No standard docs-conventions filename exists in the wild.
  The role is filled piecemeal by `.adr-dir` (tiny pointer), GitLab's docs-about-docs directory (human meta-doc), and site-generator navs (machine manifests).
  The maintainer wants one file the root CLAUDE.md can reference so agents learn the local dialect before filing anything.
- **Decision:** Adopt `docs/CONVENTIONS.md` as this skill's convention: free-form markdown (AGENTS.md philosophy, no schema) holding Dialect lines, a path→charter→audience Layout map, naming rules, and greppable pointers.
  Init mode generates it by *describing observed practice*, marking baseline-defaulted lines for veto, and wires the root CLAUDE.md reference in the same change.
- **Consequences:** The layout map becomes the misplacement oracle for all future audits.
  The evidence file honestly records that this is a defined convention composing precedents, not an adopted industry standard.
- **Lens:** When the skill needs a repo to declare something, the declaration is markdown a human can edit and veto.
  It is generated from what the repo already does.
  It is never a schema, and never a prescription written before observation.

### ADR-4: partial misplacement is a first-class finding, judged against written charters

- **Status:** Accepted (2026-07)
- **Context:** The highest-value organisation failures are within-file: a README absorbing contributor policy, decisions buried in prose invisible to the ADR surface, agent files warehousing conventions.
  Whole-file checks (presence, naming, location) catch none of these; and "this section feels wrong here" is taste unless anchored to something.
- **Decision:** The audit builds a charter table (one line per document: what belongs in it) *before* judging any section.
  Partial smells P1-P6 are detected by asking which charter a section serves.
  Sections serving two charters are reported with both candidates: uncertain is a question, not a move.
  Every extract leaves a one-line link at the source.
- **Consequences:** Audits require reading, not just globbing (subagent fan-out for large repos); findings carry evidence a user can check (section heading + charter mismatch).
- **Lens:** No placement verdict without a charter to cite.
  If a section's correct home is genuinely ambiguous, the ladder says the user decides: record the ruling in `learned/` and never re-litigate it.

### ADR-5: apply is mechanical, history-preserving, and loss-free

- **Status:** Accepted (2026-07)
- **Context:** Reorganisation is only trustworthy if nothing is lost and nothing breaks.
  Renames that orphan inbound links, deletes disguised as moves, and renumbered ADRs that break citations all destroy more value than misplacement ever did.
- **Decision:** Apply's closed operation set (create-stub / move / rename / extract / merge / link / symlink) with invariants:
  - `git mv` always
  - repo-wide inbound-reference rewrite
  - redirect stubs where external links may exist
  - ADR ids immutable
  - deletion not in the vocabulary (merge leaves a link)
  - verification greps before done
- **Consequences:** Apply is slower than a naive move script, and every step is commit-sized and reversible.
  A plan row that can't be executed loss-free is reported back, not forced.
- **Lens:** An organisation change is done when every old path either resolves or intentionally redirects, and `git status` shows renames, not a delete+add pair.
  If an operation can't meet that bar, it's a finding for the user, not an action.

### ADR-6: GLOSSARY.md is required, and its currency obligation lives in CLAUDE.md wiring

- **Status:** Accepted (2026-07)
- **Context:** The maintainer treats the project's domain vocabulary as a **ubiquitous language** shared between developer and agent.
  Naming in code, docs, and conversation must converge on one canonical term per concept.
  The vocabulary must not silently grow outside the shared reference.
  But "is this glossary up to date?" is a content-freshness question: exactly what ADR-1 forbids the librarian from judging.
- **Decision:** GLOSSARY.md joins the required document set in every flavour.
  The librarian enforces the *structural* contract:
  - the file exists
  - CLAUDE.md carries both standing instructions: use canonical terms for naming, and add new domain terms in the same change that introduces them
  - terms defined ad hoc elsewhere are consolidated (smell P7: home and uniqueness are placement questions)

  Whether a definition is accurate or the glossary is complete stays out of scope: the CLAUDE.md wiring makes *every future agent session* the currency mechanism.
- **Consequences:** The audit can guarantee the shared-language contract is wired without reading a single definition; drift detection on glossary content belongs to content-quality tooling.
- **Lens:** When a document's value depends on staying current, the librarian's job is to install the *obligation*, never the *content*.
  The obligation is the cross-link and the standing instruction in the agent file.
  Enforce wiring, not freshness.

### ADR-7: flavours are named presets; growth is handled by graduation triggers, not bigger defaults

- **Status:** Accepted (2026-07)
- **Context:** The maintainer initialises projects of very different use case, scale, complexity, and rigour.
  The maintainer wants two things:
  - a deliberate starting layout per case rather than one-size-fits-all
  - to know *when* a growing project should adopt scale-up elements

  A single baseline can't serve both a prototype and a regulated platform.
  Sized for the large case, it inflicts premature taxonomy (smell M9).
  Sized for the small case, it under-serves rigour.
- **Decision:** Three named flavours (minimal / standard / rigorous) live in `resources/flavours.md`, each a coherent bundle across every layout dimension.
  All share the non-negotiable core set (README, CONTRIBUTING, CLAUDE.md-role, ADR surface, GLOSSARY.md + cross-links).
  Init records the flavour in CONVENTIONS.md, where it becomes declared dialect.
  Each scale-up element carries an observable graduation trigger.
  Audit compares observed scale against the declared flavour and emits a Graduation section.
  Its 🟣 recommendations are applied only on acceptance, never findings (ADR-2).
  Downscaling recommendations are equally legitimate.
- **Consequences:** Two repos on different flavours are both fully compliant; growth pressure surfaces as explicit, dated recommendations instead of silent drift or premature structure.
- **Lens:** Size structure to the project, not the textbook.
  A flavour sets the starting shape, and an observable trigger justifies each escalation.
  No element is ever introduced "because bigger projects have it", only because its trigger fired.

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

### ADR-9: machine-readable siblings are generated artifacts, and the index is byte-reversible

- **Status:** Accepted (2026-08-30, user instruction)
- **Context:** Repos increasingly want their documentation *queried* (by scripts, CI gates, derived diagrams, and agents), not only read.
  Two arrangements answer that: author records as YAML and generate the markdown, or keep markdown authoritative and generate a YAML index beside it.
  Both create a second file per document.
  Every existing smell would flag that file as duplication (M-class), and ADR-1 forbids the librarian from judging it on content.
  The motivator is concrete: a corpus whose cross-references live in prose cannot be validated at all, so one-way references and drifted derived views survive indefinitely.
- **Decision:** Treat the arrangement as a **dialect line** (rung 3, ADR-2), so either is compliant and neither is a finding against the other.
  Generated files are build artifacts: exempt from naming and placement smells, never findings, never hand-edited, and always carrying a banner naming their generator.
  Adoption requires an **observable consumer**: a script, gate, or derived view that reads the records.
  This mirrors the graduation-trigger rule (ADR-7).
  Absent one, plain markdown is the correct answer and more structure is not an improvement.
  The indexer ships as a skill-owned script whose `--check` mode reconstructs the markdown and exits non-zero on any drift.
- **Consequences:** The skill stops being prose-only and takes on the scripts contract (`make fix` / `make ci`, ≥90% coverage) and a bun toolchain.
  Index mode mutates, but only generated paths: the first mutating mode that touches no source document.
  Prose-to-typed-relation conversion is inherently one-way and must be reported record-by-record before it runs (ADR-5's loss-free bar applies to *meaning*, not just to files).
- **Lens:** When the skill generates a file from another file, the generator must be able to reproduce the source **byte-for-byte**.
  That proof comes before the generated artifact is trusted.
  A round trip that is merely "equivalent" is a reformatter wearing an indexer's clothes.
  It will silently rewrite documents the skill promised never to touch.
  Prove reversibility across the whole corpus, never a sample.

### ADR-10: a convention is invocable by name, or it is only advice

- **Status:** Accepted (2026-08-30, user instruction)
- **Context:** ADR-9 landed the *general* machine-readable pattern in `structured_siblings.md`: two arrangements, adoption triggers, output shape.
  But the concrete convention that motivated it survived only as a shape sketch inside that general prose.
  That convention authors records as YAML and generates an OKF-conformant bundle with a record schema, typed relations and a derived graph.
  The failure mode was immediate and observable.
  An agent could read the general resource and still not know which fields a record carries.
  Nor would it know which relations are legal, or what a finding against the convention looks like.
  Generalising a convention had erased the convention.
- **Decision:** Every convention the skill can be *asked for* ships as its own resource.
  That resource carries four things a shelving plan needs:
  - the layout
  - the finding table (finding → smell → operation → severity)
  - the migration operation with its loss-free invariants
  - a verification gate

  It is selectable by name as an argument (`index okf-yaml <path>`), declarable as a dialect line, and detectable as an observed dialect.
  That makes it rung 1 or 2 evidence, displacing the generic template rather than competing with it.
  The general resource keeps the *choice* between arrangements and links down to each named instance; it never holds the instance's detail.
- **Consequences:** Adding a convention is now a known-shape task rather than an essay.
  Audits of a repo that follows one judge it against its own rules instead of the generic ADR template.
  The cost is one resource per convention.
  The mirror of ADR-7's discipline applies: a named convention still needs an observable trigger, or naming it is just fashion.
- **Lens:** A convention the skill cannot be *invoked with by name* is documentation, not doctrine.
  When distilling a worked example into the skill, ask two questions.
  What would an agent need to file a finding against it, and to migrate a repo to it?
  If the answer is not in one loadable file, the distillation is incomplete, no matter how well the general principle reads.

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

### ADR-13: AGENTS.md is the canonical agent file, and CLAUDE.md is only `@AGENTS.md`

- **Status:** Accepted (2026-10-05, user instruction); supersedes the agent-file wording of ADR-3, ADR-6 and ADR-7, which said "CLAUDE.md" for the role.
- **Context:** The skill treated `CLAUDE.md` and `AGENTS.md` as interchangeable surfaces for one role, accepting a symlink or an import line followed by harness-specific extras.
  That left three compliant shapes, so every repo could drift differently, and harness-specific extras grew a second home for instructions.
- **Decision:** `AGENTS.md` holds every agent instruction.
  Each `AGENTS.md` has a sibling `CLAUDE.md` whose entire content is the single line `@AGENTS.md`, because Claude Code does not read `AGENTS.md` natively.
  A symlink, extras after the import, or a `CLAUDE.md` with no `AGENTS.md` is smell M3.
  Apply moves the content into `AGENTS.md` with `git mv` and writes the stub.
- **Consequences:** Cross-links, the required set and the flavour table now name `AGENTS.md`.
  This skill's own maintainer file keeps its `CLAUDE.md` name, which is a skill-repo convention, not the audited role.
- **Lens:** One agent file, one shape: the harness-specific file is an import, never a second place to write instructions.

### ADR-14: GLOSSARY.md has a preferred shape, carried as a template

- **Status:** Accepted (2026-10-05, user instruction); extends ADR-6.
- **Context:** ADR-6 made GLOSSARY.md required but said nothing about what one looks like.
  So init had no shape to write, and audit could only check existence.
  The maintainer settled a shape in another repo.
  It has a four-line intro, a relationship diagram with every term as a node, and one alphabetical H2 per Title Case term.
- **Decision:** Carry that shape as `resources/glossary_template.md`, de-branded, with six seed terms every repo has (Agent, Decision Record, Dialect, Generated File, Maintainer, Requirement).
  It is a rung-3 dialect line (ADR-2); audit judges structure only (ADR-1): intro rules, diagram presence, H2-to-node parity, order.
- **Consequences:** Init writes a GLOSSARY.md that is already wired to its currency rule; audits gain structural glossary findings without reading a definition.
- **Lens:** Same as ADR-8: when the skill prefers a shape, ship the shape as a file.

### ADR-15: CODING_STANDARDS.md is a required document, distinct from CONTRIBUTING.md

- **Status:** Accepted (2026-10-05, user instruction).
- **Context:** The required set had no home for how code is written.
  So naming, idioms, error handling and test style landed in CONTRIBUTING.md or the agent file.
  That blurs two charters: CONTRIBUTING is the process for getting a change accepted, and coding standards are the shape of the code in that change.
  Agents need the standards on every edit and the process only at hand-off, so mixing them costs either context or compliance.
- **Decision:** CODING_STANDARDS.md joins the core set in every flavour, at root beside CONTRIBUTING.
  CONTRIBUTING and AGENTS.md each link to it; neither restates a standard.
  Coding rules found elsewhere are smell P8, and process steps found inside it are the reverse case of the same smell.
- **Consequences:** Init stubs it per language with links to linter and formatter config; audits gain a charter boundary between process and code shape.
- **Lens:** Split a document when two audiences read it at different moments: process is read once per change, standards on every line.
  A rule a tool enforces is a pointer to that tool's config, never prose.

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

### ADR-18: init writes the missing core set, never anything else

- **Status:** Accepted (2026-10-05); supersedes the "init creates exactly one file plus one reference line" rule, which ADR-13, ADR-14, ADR-15 and ADR-17 made false.
- **Context:** Each new core document came with "init writes it when missing", so the old one-file rule silently contradicted four later decisions.
- **Decision:** Init writes only missing core documents and the reference lines that wire them.
  The core documents are CONVENTIONS.md, the AGENTS.md + CLAUDE.md pair, GLOSSARY.md, CODING_STANDARDS.md, and the ADR surface with its template.
  An existing document is never rewritten by init; misplaced content inside one is an apply-mode extract.
- **Consequences:** Init's write set is enumerable from the required set, so adding a required document adds an init write in the same change.
- **Lens:** When a decision widens a mode's write set, restate the mode's whole contract in the same change.
  A scope rule left behind becomes a contradiction.

### ADR-19: every permutation axis value has an eval case, and the axis map lives with the evals

- **Status:** Accepted (2026-10-05, user instruction).
- **Context:** The skill expands along five axes (mode, argument, dialect rung, repo state, index trigger), and nothing showed which combinations had ever been run.
  The first live sweep found two grader defects and one fixture too thin to migrate, none visible from reading SKILL.md.
- **Decision:** `ARCHITECTURE.md` diagrams each mode at two densities; `evals/README.md` holds the axis table and maps every axis value to at least one case.
  Cases are pinned to a cheap model, grade read-only modes on the final message and mutating modes on the workspace, and judge structure only (ADR-1).
- **Consequences:** A new mode, argument or repo-state class lands with its axis row, its case and its fixture.
  A live sweep is a release check, not a CI gate, because every case is a billed session.
- **Lens:** A permutation nobody has run is a permutation nobody has seen; cover each axis value once before trusting the cross-product.

### ADR-20: CODING_STANDARDS.md always carries six baseline tenets, mapped to each stack's enforcing tool

- **Status:** Accepted (2026-10-05, user instruction); extends ADR-15.
- **Context:** ADR-15 gave coding standards a home but no floor, so init wrote an empty stub and every repo started from nothing.
  The maintainer holds six tenets for every codebase regardless of language.
- **Decision:** `resources/coding_standards_template.md` carries the six tenets:
  - autoformatting is a must
  - linting on the strictest rule set, with every warning an error
  - type checking on the strictest rule set
  - unit test coverage above 90%
  - never use mocks, always test real code
  - never write tests that are tautologies of the implementation

  Each language the repo ships gets a section mapping every tenet to the tool, config key or gate that enforces it.
  A portable mapping table seeds Python, TypeScript, Go and Rust; tools the repo already uses win (rung 2). (Superseded by ADR-21.)
- **Consequences:** Init writes a CODING_STANDARDS.md that is never empty; audit flags a missing tenet (🔴) or an unmapped one (🟡), structurally only (ADR-1).
- **Lens:** A standard with no enforcing tool is a wish.
  Map every tenet to the config or gate that fails the build.
  Name review as the gate only where no tool can enforce it.

### ADR-21: the skill ships no tool mapping for the coding tenets

- **Status:** Accepted (2026-10-05, user instruction); supersedes ADR-20's portable mapping clause, and leaves the six tenets standing.
- **Context:** ADR-20 shipped a table mapping each tenet to tools and flags for four stacks.
  Tool names, flags and config keys change faster than the skill does, so that table would go stale.
- **Decision:** The template carries the six tenets and the per-language section shape only.
  Init maps each tenet to the tools the repo already uses.
  A tenet with no enforcing tool is written as a gap for the maintainer, never a guessed tool.
- **Consequences:** The skill makes no claim about any tool's flags, so nothing in it drifts when a tool changes.
- **Lens:** Ship the rule, not the tool invocation: what a repo must enforce is stable, and how a tool enforces it belongs to the repo.

### ADR-22: complexity is capped wherever the stack has a tool for it

- **Status:** Accepted (2026-10-05, user instruction); extends ADR-20 with a seventh tenet.
- **Context:** The six tenets cap formatting, lint, types and coverage, but not how tangled the code gets.
  Cyclomatic complexity and Halstead metrics (as radon reports them for Python) measure that, though not every stack has such a tool.
- **Decision:** A seventh tenet: complexity is measured and capped wherever the stack has a tool for it.
  Thresholds live in the tool's config, and a breach fails the build.
  It is the one tenet allowed to say "no complexity tool for this stack"; per ADR-21 the template names no tool.
- **Consequences:** The init eval checks for the complexity tenet alongside the other six.
- **Lens:** Where a metric exists, gate on it; where it does not, say so rather than inventing a proxy.

## Extension checklist

- [ ] New smells enter `misplacement_smells.md` with symptom, detection, fix, and severity: and never a content-quality judgement (ADR-1).
- [ ] New baseline claims cite a source in `evidence.md` with the research date; deployment/adoption stats re-verified if load-bearing (ADR-2).
- [ ] Any new apply operation defines its loss-free invariant before use (ADR-5).
- [ ] Rejected findings appended to `resources/learned/adjudications.md` in the same session (the `resources/learned/` state pathway of the workspace skills rule).
- [ ] New required documents enter via the flavour table (all flavours or a graduation trigger) with their cross-link obligations stated (ADR-6/7).
- [ ] New scale-up elements define an observable graduation trigger before entering `flavours.md` (ADR-7).
- [ ] Deterministic checks (presence, naming, link resolution) are candidates for further `scripts/` helpers per the skills scripts contract.
- [ ] Any change under `scripts/` leaves `make -C skills/librarian/scripts ci` at exit 0, coverage ≥ 90% (ADR-9).
- [ ] A new generated-artifact kind states its regenerate banner and its reversibility proof before it ships (ADR-9).
- [ ] A new **named** convention ships as its own resource with a layout, a shelving-plan finding table, a migration operation and a verification gate.
  It never ships as prose inside the general resource (ADR-10).
- [ ] A change to the ADR record shape lands in `adr_template.md` (both layout blocks), `record.schema.json`, `record.md.j2` and the example records together, then `make -C skills/librarian/scripts docs` (ADR-16/17).
- [ ] A new required document adds an init write and an init eval assertion in the same change (ADR-18).
- [ ] A new mode, argument or repo-state class adds its axis row, case and fixture under `evals/` (ADR-19).
- [ ] Both mermaid gates re-run if README or ARCHITECTURE is touched, and mdtoc if README is touched.
- [ ] All files stay ≤ 500 lines.
- [ ] Prose stays brand-agnostic.

## Known gotchas

- A single existing file is not a convention: the observed-dialect rung needs ≥3 consistent instances, or the librarian will canonise an accident (ADR-2).
- Grep-only audits miss every P-smell: partial misplacement requires reading sections; budget subagents for it on large repos (ADR-4).
- `git mv` alone doesn't rewrite links; the inbound-reference grep must cover agent files, configs, and code comments, not just markdown (ADR-5).
- Health files moved *out* of the three GitHub-recognised locations silently lose platform surfacing.
  The file still exists, so nothing errors, and only the audit's location check catches it.
- Renaming a heading during an extract changes its anchor; inbound `#anchor` links break invisibly.
  Grep old anchors, not just old paths.
- Whitespace is content.
  Blank lines before a heading, two fences butted together, and a missing final newline are invisible in a diff viewer.
  All three break a round trip.
  `md2yaml.ts` models them as `gap` / `leading` / `trailing`; a new block type that ignores them reformats documents silently (ADR-9).
- YAML resolves an unquoted `2026-08-30` to a date, not a string, so a JSON Schema `"type": "string"` rejects it.
  Validate the JSON projection, not the raw load.
- Flattening a heading to text (right for a slug) and *storing* that flattened text (wrong for anything reconstruction reads) are different operations.
  Store the slice, or an inline-code heading loses its backticks.
- Content before the first heading is normal wherever the title lives in frontmatter.
  A parser that assumes a heading comes first drops the document's opening with no error.
- The `@AGENTS.md` stub exists only because Claude Code does not read AGENTS.md natively (evidence.md).
  If that changes, re-verify before keeping the stub as a requirement (ADR-13).
