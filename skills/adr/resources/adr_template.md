# ADR template: the preferred shape of one decision record

The format the librarian prefers for a single ADR, whichever layout the repo uses.
Both layouts carry the same fields and the same Given / We prefer / Because / Unless lens; only the heading depth differs.
Each layout has its own block below, so neither is derived by hand.

Format is a **dialect line like any other** (SKILL.md, authority ladder).
A repo keeps its own ADR shape when it has declared one in `docs/CONVENTIONS.md`, or consistently uses one across three or more records.
This template is the rung-3 default for repos that have not chosen.
It is also the recommendation when a repo asks what good looks like.
Never rewrite an accepted ADR to fit this shape.

What a decision *is* (Facts, Value System, Lens, Decisional Balance, the Regulating Condition) lives in [adr_decision_theory.md](adr_decision_theory.md).
This file only owns the shape of one record.
The shape of a whole machine-readable *bundle* (records authored as YAML, markdown generated) is the named `okf-yaml` convention in [adr_okf_yaml.md](adr_okf_yaml.md).
That convention carries this template's fields as its schema.

----

## File-per-decision: one file, `adrs/NNNN-short-name.md`

```markdown
# ADR-NNNN: <the decision, as a short assertion>

| Field | Value |
|---|---|
| **Status** | Accepted, YYYY-MM-DD |
| **Provenance** | <the session, rehearsal, or research that forced it, named in prose, never an id into another file> |
| **Relates to** | <extends / supersedes / superseded by ADR-NNNN, or a one-clause relation, or `-`> |
| **Enforced in** | <runtime surfaces only, comma-separated: `SKILL.md` step N, `resources/<file>`> |

## Decision

### The lens

#### Given

<the context P that holds today>

#### We prefer

<X>, over <Y>

#### Because

<why the preference follows from P>

#### Unless

<P → Q: the condition that would invert the preference, or "never; this one is unconditional">

## Consequences

### Pros

- <what is gained>

### Cons

- <what is paid>
```

## Single-file log: one section of `ADRs.md`

The log opens with `# Decisions` and one charter sentence; each record is a section, newest last.

```markdown
## ADR-NNNN: <the decision, as a short assertion>

| Field | Value |
|---|---|
| **Status** | Accepted, YYYY-MM-DD |
| **Provenance** | <the session, rehearsal, or research that forced it, named in prose, never an id into another file> |
| **Relates to** | <extends / supersedes / superseded by ADR-NNNN, or a one-clause relation, or `-`> |
| **Enforced in** | <runtime surfaces only, comma-separated: `SKILL.md` step N, `resources/<file>`> |

### Decision

#### The lens

##### Given

<the context P that holds today>

##### We prefer

<X>, over <Y>

##### Because

<why the preference follows from P>

##### Unless

<P → Q: the condition that would invert the preference, or "never; this one is unconditional">

### Consequences

#### Pros

- <what is gained>

#### Cons

- <what is paid>
```

----

## Why this shape

Four properties, and an audit can check each one:

- **Headings index the hierarchy.** The record is readable out of order.
   - A reader who wants only the rule reads `We prefer` and `Unless`;
   - A reader who wants the argument reads `Given` and `Because`.
   - A flat bullet list forces linear reading.
- **The lens is the decision, and it comes first.** An ADR's value is the judgement lens of preferring one thing over alternatives.
    - `## Decision` follows the metadata table directly, so a decision can be applied without reading its consequences.
- **The lens has a `Given` and an `Unless`.**
    - A decision is always made in a specific context (eg `Given`).
    - A decision can expire because the context has changed (eg `Unless`)
    - It is important to document the ephemeral nature of decisions.
      That gives a future reader permission to assess if a decision has expired and no longer serves its value.
- **Lens headings are machine-extractable.** `Given` / `We prefer` / `Because` / `Unless` are H4 headings (H5 in the single-file log), so each is a stable path ending in `decision.the_lens.given`.
    - A parser can lift or replace them, so the log is queryable rather than only readable.

## Filling rules

- **One rule per ADR.** If a record needs two lenses, it is two ADRs.
  A grouped ADR cannot carry a coherent `Enforced in` row and cannot be indexed.
- **`Unless` is never blank.** When a preference is absolute, write "never; this one is unconditional" out loud: that is information the reader would otherwise have to infer.
- **`Enforced in` names surfaces, not conditions.** What a surface must *do* belongs in that surface.
  The row is an index into the thing being governed, not a specification of it.
- **`Provenance` is prose.** Name the session, rehearsal, or research that forced the decision.
  Never an id pointing into a companion ledger: the ADR is the whole record, and a second store of the same rulings fragments the log.
- **The record is immutable in substance.** Reformatting to a new template shape is not a change of mind.
  A change of mind is a new ADR that supersedes the old one, with links both ways.
  Adopting this template across an existing log is a reformat, and it is an APPLY operation, never a silent rewrite.
- **Supersession may be partial.** A later ADR can retire one clause of an earlier record and leave the rest standing.
  Record that in the earlier record's Status row, its `Relates to` row, and a parenthetical marker on the affected clause, never by rewriting the clause.
- **Plain punctuation only.** Use `:` after the title number, a comma in the Status date, and comma-separated `Enforced in` values.
  The em-dash and the interpunct are AI-authorship tells that prose-quality audits flag; the template must not mandate glyphs its sibling doctrine bans.

## What the librarian does with it

Placement and existence only, per the skill's own boundary (SKILL.md, "never judge content"):

- **Audit** reports a **structural** finding against an ADR surface whose records carry no `Status`, no decision statement, or no reasoning.
  It names this template as the recommended shape.
  It never reports that the reasoning is *weak*, which is a content judgement.
- **Init** and **apply** write the matching layout block whenever they create an ADR-surface stub.
  The file-per-decision block becomes `<adr-dir>/TEMPLATE.md`, and the single-file block a closing `## Template` section of `ADRs.md`.
  Init also records the choice as a Dialect line in `docs/CONVENTIONS.md`.
- **Apply** migrates existing records to this shape only on explicit user acceptance, preserving every id, anchor, and inbound `ADR-NNNN` citation.
