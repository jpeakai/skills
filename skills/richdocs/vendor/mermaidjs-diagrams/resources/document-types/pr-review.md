# Document Type: PR Review

## 1. Trigger

Select `pr-review` for "pr-review", "PR review document", "visual diff", or
"walk through this pull request". This authors a review companion. It does not
claim the code passed review. For proposed changes, select [plan](plan.md).

## 2. Contract

Curate files and/or git hunks into sections by changed behavior. A file may span
sections, but each hunk has one primary section and cross-links elsewhere.
Record repository, base and head revisions, diff command, and evidence limits.
For a PR, compare its merge base with the head, not a moving branch name.
Inventory every changed path, including deletions, renames, tests, and generated
mirrors. Map each path or hunk to a section; explain mechanical changes there.

Every change section includes:

- A claim heading, motivation, prerequisites, and owned files/hunks.
- **BEFORE** at the base revision and **AFTER (implemented)** at the head.
- A dual-density pair for each side: visible overview (low preset, at most
  12 nodes) and collapsed detail (high preset, at most 35 nodes). That is four
  flowchart fences per section even for small changes. Detail adds real symbols,
  branches, and boundaries; do not invent complexity.
- Short, language-tagged BEFORE/AFTER code fences with paths and revision-specific
  line ranges or hunk headers. Quote actual code; mark omissions. Add `diff`
  fences when they make the change easier to inspect.
- A takeaway, validation evidence, risks, and the reviewer decision.

If a component did not exist, diagram the previous behavior or its absence.
Never manufacture a previous API. Preserve stable labels across both sides.

For Richdocs HTML controls, put this raw HTML marker below the title:

```html
<div data-rd-document-type="pr-review"></div>
```

Use h2 headings for change groups and h3/h4 for nested sections. Review controls
follow that hierarchy. The marker remains harmless in Markdown viewers.

## 3. Sequence

Build a dependency narrative: establish contracts and vocabulary first, then
core behavior, callers/UI, packaging, and validation. Move dependent groups
after prerequisites; explain cycles before splitting by responsibility. Each
group reuses earlier concepts plus the new concept it introduces. Start with
scope and a hunk-to-section coverage table. Keep evidence inside its group.

## 4. Diagram selection

A BEFORE/AFTER flowchart pair at both densities is the default in every group.
Additional triggers are case-insensitive authoring cues, not renderer magic:

| Cue or observed change | Add on both sides at both densities |
|---|---|
| `data-model`, schema, entity, relationship, cardinality, migration | `erDiagram`: entities/cardinality in overview; keys, fields and constraints in detail |
| `event-flow`, event, message, queue, publish, subscribe, webhook, async lifecycle | `sequenceDiagram`: participants/messages in overview; ordering, retries, errors and acknowledgements in detail |

Keywords select a lens when the diff changes that behavior. Explicit `data-model`
and `event-flow` requests select it even when discovery is needed; state missing
evidence instead of inventing actors or schemas. Both cues may apply. An
in-memory set alone does not require a persistent schema diagram.

## 5. Palette

Use semantic roles (`input`, `process`, `output`, `storage`, `external`) from
[the color reference](../color_theming.md). Repeat identical role colors across
both sides and every section. Encode BEFORE/AFTER with labels, not color alone.
Use type-supported theme variables for ER and sequence diagrams. Include an
edge-label background where needed.

## 6. Anti-patterns

Avoid one section per file, unexplained hunk omissions, AFTER based on intent
rather than head code, copied detail without useful detail, uncaptioned code
dumps, and callers introduced before contracts. Reviewed does not mean approved.

## 7. Done checklist

- Every changed path/hunk has a primary group or explained mechanical mapping.
- Every group has revision-backed BEFORE/AFTER at both densities, snippets,
  takeaway, validation, and a reviewer decision.
- Data and event cues have the applicable additional diagram pairs.
- Earlier sections establish concepts needed by later sections.
- Complexity and contrast gates pass on Markdown before HTML conversion.
- Inspect light and dark renders; code and collapsed diagrams still work.
- HTML marks sections Reviewed and collapses them; sidebar shows partial and
  complete subtrees; subtree controls mark and undo the entire subtree.
- Navigation reopens reviewed content without clearing its status.
- Reload starts unreviewed. Review state never enters browser storage, cookies,
  caches, URLs, or server storage.
