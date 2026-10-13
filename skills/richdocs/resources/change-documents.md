# Change documents

Use `/richdocs [md|html+live|html+inline] [pr-review|plan] <sources>`.
Sources may be PR URLs, revision ranges, files, or hunks. Read the vendored
[PR Review](../vendor/mermaidjs-diagrams/resources/document-types/pr-review.md)
or [Plan](../vendor/mermaidjs-diagrams/resources/document-types/plan.md) contract.
Curate evidence before writing. Conversion does not infer groups, produce
diagrams, or detect keywords. `data-model` and `event-flow` select extra lenses.

Coverage tables use **Section | Filepath**, ordered by section number, then
filepath. Use language-tagged fences (`javascript`, `typescript`, `diff`,
`json`, `yaml`, `markdown`) so both HTML modes apply syntax highlighting.
Unknown languages stay as plain source; rich diagram blocks keep their own
renderer.

Put `<div data-rd-document-type="pr-review"></div>` or the corresponding `plan`
marker below the title. Headings h1 through h4 define the review hierarchy.
Article **Mark reviewed** toggles one section and collapses its content.
Sidebar **Review** toggles that heading and every descendant. **Partial** means
some of the subtree is reviewed; **Reviewed** means all of it is. Clicking
Reviewed undoes that control's scope and expands affected sections. A heading
link reopens reviewed content without changing its status. Native buttons use
`aria-pressed`, including mixed sidebar states.

Review state lives only in page memory. Refresh, new tabs, and regenerated pages
start unreviewed. Theme changes and navigation retain state in the current page.
Print includes folded content and hides controls. Sidebar-layout preferences
are separate from review state.

Run vendored complexity and contrast gates before `md2html.py`. Render live and
inline into separate directories so the HTML filenames do not collide. Inline
embeds Markdown/tokens but still needs network for pinned CDN libraries. Serve
both locally for verification.

For sequence diagrams, pass the chosen theme's light/dark `surface` colors via
`--background-light` and `--background-dark`. The audit checks theme-variable
colors, including page-backed message/loop text, on both surfaces. Do not pin
`theme: base` merely to customize actor boxes: leave the host theme adaptive
and set only the box-specific colors needed. Syntax highlighting loads its
pinned CDN library alongside the existing renderer libraries.
