# Document Type: Plan

## 1. Trigger

Select `plan` for "plan", "implementation plan", "proposed changes", or
"before and proposed after" when the deliverable is a change document.

## 2. Contract

Apply the [PR Review contract](pr-review.md), including file/hunk curation,
coverage, code fences, narrative order, and four flowchart fences per group.
The difference is evidence: **BEFORE** is observed at a recorded baseline;
**AFTER (proposed, not implemented)** is a design. Label every AFTER heading,
caption, and snippet as proposed. Include acceptance criteria and unresolved
decisions per group. Proposal validation cannot prove implementation.

List anticipated paths and symbols. Hunk headers exist only for actual draft
patches; never fabricate future line numbers. Mark suggested code as proposed
pseudocode where it is not executable. State assumptions and evidence gaps.
A retrospective plan for an implemented PR explicitly says it reconstructs the
proposal from the base and final diff. Final implementation tests are not
pre-implementation evidence.

Enable the same HTML review controls below the title:

```html
<div data-rd-document-type="plan"></div>
```

Reviewed means examined, not approved.

## 3. Sequence

Order prerequisites, contracts, core changes, consumers, delivery, and acceptance
checks as in PR Review. State earlier decisions each group depends on.

## 4. Diagram selection

Use the same default flowcharts and `data-model` / `event-flow` triggers as
[PR Review](pr-review.md#4-diagram-selection). Every additional type has BEFORE
and proposed AFTER at overview and detail densities.

## 5. Palette

Resolve the active design profile, otherwise use prebuilt OsakaNights.
Delegate palette curation to design-profiles where available; read [the shared theming guide](../color_theming.md) for token selection and renderer constraints.
Assign categorical hue families to meaningful topics, responsibilities, owners or phases in a fixed order.
Use the five same-family shades for related subcategories and repeat the mapping across every view.
Use labels for BEFORE, AFTER, proposed and status meanings rather than relying on hue alone.
Resolve CSS variables to supported concrete values before writing Mermaid styles.
Style each category boundary with its matching tint and a readable same-family border, checking immediate parent surfaces for nested groups.
Use native entity-row and sequence-group mechanisms rather than copying flowchart styles to unsupported families.
Inspect both rendered modes and publish native Mermaid source.
Example colors illustrate syntax; they are not another palette authority.

## 6. Anti-patterns

Do not present intent as implementation, fabricate baseline evidence, claim
tests ran on nonexistent code, or replace diagrams and code with task lists.
Keep unknowns explicit without blocking independent design work.

## 7. Done checklist

Apply the PR Review checklist, replacing head-backed AFTER evidence with labelled
proposals, assumptions, acceptance criteria, and planned validation. Exercise the
same section/sidebar/subtree controls and memory-only reset.
