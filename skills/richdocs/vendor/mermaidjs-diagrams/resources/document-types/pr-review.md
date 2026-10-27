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
mirrors. Apply the review scope below before grouping changes.
Map each in-scope path or hunk to a section; explain mechanical changes there.

### GitHub review scope

For a GitHub PR, default to files remaining to be reviewed by the authenticated
`gh` viewer. Query `viewerViewedState` for every changed file before curating.
This field belongs to the authenticated viewer, who may differ from the requested
reviewer. Record the viewer login and disclose any mismatch.

Resolve the PR hostname, owner, repository name, and number from its URL or
`gh pr view`. Substitute them below; retain pagination for PRs over 100 files.
The query returns the complete inventory, viewer identity, and revision snapshot:

```bash
gh api --hostname github.com graphql --paginate --slurp \
  -F owner=OWNER -F name=REPOSITORY -F number=123 \
  -f query='
    query($owner: String!, $name: String!, $number: Int!, $endCursor: String) {
      viewer { login }
      repository(owner: $owner, name: $name) {
        pullRequest(number: $number) {
          url baseRefOid headRefOid
          files(first: 100, after: $endCursor) {
            totalCount
            nodes { path viewerViewedState }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }'
```

Use the PR's hostname for GitHub Enterprise.
Check for GraphQL errors and reconcile collected paths with `totalCount` and the
revision-backed diff before treating the inventory as complete.
All pages must report the same viewer and base/head revisions.
Recheck those revisions before delivery; refresh the snapshot if either changed.
Record the query, retrieval time, viewer, revisions, and counts by state in scope.

| File state | Default treatment |
|---|---|
| `UNVIEWED` | Include all changed hunks in the review narrative. |
| `DISMISSED` | Include all changed hunks; the file changed since it was last viewed. |
| `VIEWED` | Omit detailed review unless needed as a prerequisite or explicitly requested. |
| Missing or unknown state | Include the file and disclose the state limitation. |

Viewed state is per file, so it cannot identify which individual hunks were read.
Keep every hunk of an included file in scope.
In each section's sorted **Related files** list, label remaining files with their
state and viewed prerequisites as **Context only (VIEWED)**.
Account for other viewed paths in a compact, collapsed **Already viewed** list
after the change sections, with an explicit exclusion reason.
Do not create detailed change sections for those exclusions.
If all files are viewed, report no remaining files; add context only when requested.

An explicit request for the whole PR overrides this default.
For local diffs or unavailable GitHub state, cover the full supplied diff and
state that remaining-review scope could not be determined.
Never treat a failed or incomplete query as evidence that files were viewed.

Querying state and generating a companion do not mark GitHub files as viewed.
Richdocs section controls remain page-local and do not synchronise with GitHub.
Only change GitHub viewed state when the user explicitly requests it.
Viewed state does not establish approval or correctness.

References: [GitHub file states](https://docs.github.com/en/graphql/reference/pulls#fileviewedstate)
and [GitHub CLI pagination](https://cli.github.com/manual/gh_api).

### Change sections

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
scope, then list related files within each change section, before its BEFORE
and AFTER material. Sort filepaths within the section and attach hunk evidence
there. Keep in-scope coverage complete across the section lists, including
generated mirrors and mechanical changes.
Account for viewed exclusions in the collapsed list after those sections.
Do not collect files into one upfront table.

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
Do not mistake GitHub viewed files for approvals, omit `DISMISSED` files, or
equate the companion's section controls with GitHub file state.

## 7. Done checklist

- Every changed path/hunk has a primary group, mechanical mapping, or explicit
  viewed exclusion; context-only files are labelled.
- GitHub scope records viewer, revisions, retrieval time, and state counts;
  pagination and diff reconciliation are complete, or limitations are disclosed.
- Remaining scope includes `UNVIEWED`, `DISMISSED`, and unknown states;
  full-review requests override it, and an empty remaining set is reported.
- Every group has revision-backed BEFORE/AFTER at both densities, snippets,
  takeaway, validation, and a reviewer decision.
- Data and event cues have the applicable additional diagram pairs.
- Earlier sections establish concepts needed by later sections.
- Complexity and contrast gates pass on Markdown before HTML conversion.
- Language-tagged code fences receive syntax highlighting in both HTML modes.
- Inspect light and dark renders; code and collapsed diagrams still work.
- HTML marks sections Reviewed and collapses them; sidebar shows partial and
  complete subtrees; subtree controls mark and undo the entire subtree.
- Navigation reopens reviewed content without clearing its status.
- Reload starts unreviewed. Review state never enters browser storage, cookies,
  caches, URLs, or server storage.
