# Change documents

Use `/richdocs [md|html+live|html+inline] [pr-review|plan] <sources>`.
Sources may be PR URLs, revision ranges, files, or hunks. Read the vendored
[PR Review](../vendor/mermaidjs-diagrams/resources/document-types/pr-review.md)
or [Plan](../vendor/mermaidjs-diagrams/resources/document-types/plan.md) contract.
Curate evidence before writing. Conversion does not infer groups, produce
diagrams, or detect keywords. `data-model` and `event-flow` select extra lenses.

Each change section starts with its own **Related files** list, sorted by
filepath. Keep those lists beside the behavior they explain, rather than in an
upfront coverage table. Use language-tagged fences (`javascript`, `typescript`, `diff`,
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

Run `bunx @jpeakai/mermaidjs-lint@0.5.0` (parse, complexity and contrast,
sequence diagrams included) before `md2html.py`, as shown in the SKILL.md
Mermaid gate. Render live and
inline into separate directories so the HTML filenames do not collide. Inline
embeds Markdown/tokens but still needs network for pinned CDN libraries. Serve
both locally for verification.

For sequence diagrams, the lint scores page-backed colors against GitHub's page
(`#ffffff` and `#0d1117`), not the chosen theme's `surface` colors. Check the
page-backed variables you set (`signalTextColor`, `signalColor`,
`loopTextColor`, `actorLineColor`, and `actorTextColor` for a human `actor`)
against the theme's light and dark `surface` with the vendored calculator:

```bash
bun install --cwd .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts --frozen-lockfile
bun run .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts/color_contrast.ts COLOR SURFACE
```

A failing pair is a blocker. Do not pin
`theme: base` merely to customize actor boxes: leave the host theme adaptive
and set only the box-specific colors needed. Syntax highlighting loads its
pinned CDN library alongside the existing renderer libraries.
