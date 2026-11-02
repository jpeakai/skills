---
name: mermaidjs-diagrams
description: "Render and analyze Mermaid diagrams in Markdown and author diagram-led documents. Resolve design-profiles colors first, otherwise use prebuilt OsakaNights themes/osakanights/themes.css. Reuse categorical hue families and their five shades for meaningful groups, and inspect both rendered modes. Run bunx @jpeakai/remark-lint-slopstopper for Markdown structure, prose, Mermaid parsing, modeled text contrast and complexity. Use for architecture diagrams, codebase discovery, PR companions, implementation plans, educational guides and visual explanations. Requires Bun, Node.js 24 or newer and registry access on first lint use."
argument-hint: "[markdown-file]"
user-invocable: true
---

# Context

Render and maintain Mermaid.JS diagrams with **visual clarity enforcement**.
Works for ANY project. Yoghourdjian et al., 2020 (arXiv:2008.07944) found difficulty
**finding the shortest path** in dense diagrams above ~50 nodes — a path-tracing
result, not a comprehension budget; tighter limits here rest on segmenting instead.

Diagrams live as ` ```mermaid ` code fences inside `.md` files.

# Document types (route first)

For a **whole document** rather than a single diagram, read the matching type
**before drafting**: it governs the *sequence* of diagrams and the invariants
across them. Skip when the task is one diagram, a render, or an audit.

| The request says | Read |
|---|---|
| "pr-review", "PR review document", "visual diff" | `resources/document-types/pr-review.md` |
| "plan", "implementation plan", "proposed changes" | `resources/document-types/plan.md` |
| "educational", "illustrative guide", "explainer", "one-pager on X", "distil X", "explain X visually", "teach me X" | `resources/document-types/educational.md` |
| Unsure which, or adding a new type | `resources/document-types/README.md` |

Verify the selected host supports the chosen Mermaid family and syntax.
If it does not, choose a supported representation that preserves the model or report the remaining limitation.
Publish native Mermaid fences and keep verification images local; see `resources/gfm_beta_diagrams.md`.

---

# Required for every diagram

Two requirements apply to **every** diagram this skill authors or reviews.
Not "consider," not "when time permits" — **mandatory, enforced, verifiable**.

## 1. Resolve the design profile and semantic categories

Delegate palette curation to design-profiles where available.
Use an explicit profile or the project's default; otherwise use the prebuilt `resources/themes/osakanights/themes.css` and matching tokens.
Do not invent another HSL palette or regenerate the Golden Walk in this skill.
Read `resources/color_theming.md` for category assignments, five-shade families, compound boundaries, entity rows and sequence groups.
Use `design_profile.ts palette --mode light` and again with `--mode dark` to read baked colors.
Resolve CSS variables to supported concrete values before writing Mermaid; GitHub fences cannot evaluate `var(...)`.
Keep semantic category assignments consistent across views and verify the actual rendered surfaces in both modes.

## 2. Run Slopstopper before declaring the document done

Use the published standalone CLI for Markdown structure, prose and Mermaid policies:

```bash
bunx @jpeakai/remark-lint-slopstopper SOURCE.md
bunx @jpeakai/remark-lint-slopstopper docs/ --json
```

It needs Bun and Node.js 24 or newer, plus registry access on first use.
Exit 0 is clean, 1 means remaining findings, and 2 means an invocation or processing error.
Treat every nonzero result as a blocker.
Use `--mermaid-only` or `--prose-only` while isolating a concern; both retain recommended Markdown structure checks.
The final document audit enables both policy groups.

`--fix` applies verified prose edits, not diagram repairs.
Review edits and resolve remaining findings manually.
Standalone `.mmd` inputs must be wrapped in Mermaid fences in Markdown for this CLI.

For custom canvases, install the skill's locked dependencies and generate native remark configuration:

```bash
bun install --cwd .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts --frozen-lockfile
mkdir -p tmp/diagrams
bun run .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts/design_profile.ts lint-config > tmp/diagrams/lint-config.json
bunx @jpeakai/remark-lint-slopstopper SOURCE.md --config tmp/diagrams/lint-config.json
```

Slopstopper 0.1.2 does not expose host-profile or canvas CLI flags.
Its canvas options do not model a host stylesheet that forces another foreground, and its Mermaid text policy does not certify border contrast.
Keep source styling explicit and inspect MkDocs or other host overrides in both rendered modes.
See `resources/contrast_tooling.md` for the native config contract and supplemental pair measurements.

## Why this is mandatory

A diagram that's illegible to a low-vision reader, or that melts into the
background under a dark GitHub theme, **fails its job** — it communicates
nothing. The cost of the audit is seconds; the cost of shipping
unreadable documentation is repeated across every reader for the life of
the project. The failure mode of skipping this check is silent (the
author can read it fine on their screen; readers quietly give up). That's
the same Type-2-silent-failure pattern the complexity linter was built to
prevent — the contrast check is its twin, gating the **color** axis of
visual clarity the way complexity checks gate the **structural** axis.

Wire `bunx @jpeakai/remark-lint-slopstopper` into any `make ci` / pre-commit pipeline
that touches docs. One command gates both axes.

> Deep-dive references:
> - `resources/color_theming.md`: profile selection, categorical families, five shades and renderer-aware styles
> - `resources/color_palette_recipes.md`: category assignment patterns using the chosen profile
> - `resources/color_host_themed_renderers.md` — translucent dual-theme fills for host-themed renderers (MkDocs Material)
> - `resources/contrast_tooling.md`: the lint's contrast profiles and rules, and the ad-hoc pair calculator
> - [`@jpeakai/remark-lint-slopstopper` rules](https://github.com/jpeakai/remark-lint-slopstopper/blob/main/RULES.md): every rule with failing and fixed examples
> - `scripts/color_contrast.ts` — generic WCAG + APCA calculator for ad-hoc pairs

---

# Rendering

## Quick render (recommended)

Use the bundled script to render both standard variants (dark+transparent and default+white PNGs) in one command. Two variants are the floor because the skill must work on dark and light hosts alike; one image cannot serve both:

```bash
bash .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts/render_mermaid.sh path/to/document.md
```

Output lands in `.mmdc_cache/{variant}/path/to/document-*.png`.

A **design profile** is read first: `--design-profile NAME` names one, else
`.design-profiles/.default-profile` does. Its Mermaid `themeVariables` reach
`mmdc` on the `base` theme, light for the white variant and dark for the
transparent one, and the script prints which profile it used. A profile that was
asked for and resolves nowhere stops the run before any browser starts. Use the same selected profile for rendering and native lint configuration:

```bash
bash .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts/render_mermaid.sh --design-profile NAME path/to/document.md
bun run .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts/design_profile.ts lint-config --design-profile NAME > tmp/diagrams/lint-config.json
bunx @jpeakai/remark-lint-slopstopper path/to/document.md --config tmp/diagrams/lint-config.json
```

With no selected profile, the renderer and palette reader use prebuilt OsakaNights.

`mmdc` reads the markdown file, extracts every mermaid fence, and renders each as a
numbered image artefact. The script exits 0 only when every expected PNG was written
**and verified** (magic bytes + non-zero dimensions) — a renderer that exits 0 without
producing an image is treated as a failure, not a success.

## Custom variants

For formats beyond the two defaults, drive `mmdc` directly. Three parameters form a
**variant tuple** — theme (`-t`: `default`/`dark`), background (`-b`:
`white`/`black`/`transparent`), format (`-e`: `png`/`svg`) — which also names the
output folder, `{theme}_{backgroundColor}_{format}`.

> Full variant documentation, with copy-paste `mmdc` invocations for every
> combination: `resources/pattern_render_markdown.md`

## When a render fails: triage, don't bail

Rendering drives a real Chromium, so it fails for reasons that have nothing to
do with your diagram. **Classify before you touch the source** — four
independent inputs can break, and only one of them is the diagram:

| stderr signature | Class | What to do |
|------------------|-------|-----------|
| `EPERM` / `EACCES` / `_cacache` | `NPM_CACHE_PERMISSION` | Task-local `NPM_CONFIG_CACHE` (script retries this itself) |
| `Could not find Chrome`, `chrome-headless-shell` | `BROWSER_MISSING` | Point at an installed Chromium, or let Puppeteer download one — never both wrong at once |
| `MachPortRendezvous`, `Permission denied (1100)` | `SANDBOX_DENIED` | Stop retrying; re-run **only** the render in a browser-capable execution class |
| `ENOTFOUND` / `ETIMEDOUT` | `NETWORK_UNREACHABLE` | Ship the fences unrendered — GitHub/GitLab render them natively |
| `Parse error`, `UnknownDiagramError` | `DIAGRAM_SYNTAX` | **The only class that means edit the diagram** |

`render_mermaid.sh` does the classification and the mechanical remedies itself: it resolves a
browser, isolates the npm cache, classifies stderr, retries once per remediable
class, and prints `class` + `evidence` + `remedy` when it genuinely cannot
proceed. Supporting modes:

```bash
bash .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts/render_mermaid.sh --doctor              # probe the host, render nothing
bash .claude/skills/richdocs/vendor/mermaidjs-diagrams/scripts/render_mermaid.sh --verify out/*.png    # is this actually a decodable PNG?
```

Never respond to an environmental failure by simplifying, restyling, or
deleting a diagram that passed the gates — and never report a render as done
without a verified artifact.

> Full triage procedure, escalation recipes, and field evidence:
> `resources/render_troubleshooting.md`

## Icon packs

```bash
# Iconify icons (architecture-beta diagrams)
--iconPacks @iconify-json/logos @iconify-json/mdi

# Custom URL-based packs
--iconPacksNamesAndUrls "vendor#https://example.com/icons.json"
```

Flowchart diagrams with Font Awesome (`fa:fa-icon`) need no `--iconPacks` flag.

---

# Complexity Analysis

The same CLI checks Mermaid fences through Mermaid's own parsers and reports visual complexity.
Use a named density preset when the document requires a tighter budget.

```bash
bunx @jpeakai/remark-lint-slopstopper docs/ --mermaid-only --preset low-density
bunx @jpeakai/remark-lint-slopstopper SOURCE.md --json
bunx @jpeakai/remark-lint-slopstopper --list-rules
```

## Output format

JSON output has a `files` array; each file contains `path`, `fixes` and `messages`.
Each message carries its rule ID, reason, severity and available source positions.
The Mermaid policies are `contrast-text-below-aa` and `complexity-visual-score-acceptable-exceeded`.
Unparseable diagrams produce blocking diagnostics before scoring.
The complexity policy reports VCS and split-plan advice; it does not rewrite the diagram.

## Density presets

| Preset | Nodes | VCS | Typical Use |
|--------|-------|-----|-------------|
| Low (`--preset low-density`) | <=12 | <=25 | Overview diagrams |
| Medium (`--preset medium-density`) | <=20 | <=40 | README diagrams |
| High (`--preset high-density`) | <=35 | <=60 | Detail diagrams (default) |

## Complexity formula

```
VCS = (nodes + edges*0.5 + rows*0.25 + subgraphs*3) * (1 + depth*0.1)
```

Ratings: **ideal** / **acceptable** / **complex** / **critical**

When a diagram is rated **complex** or **critical**, split it into simplified and
detailed versions. See `resources/diagram_organization.md` for the dual-density
approach and naming conventions.

---

# Contrast Analysis

Contrast checking is **mandatory**, not optional. See "Required for every
diagram" above, which carries the mandate and the commands you need.

The `contrast-text-below-aa` policy audits modeled text surfaces in Mermaid fences.
Unparseable diagrams and unsupported styling produce blocking diagnostics.
The CLI does not repair diagrams or provide a separate border-contrast policy.
Verify border pairs and host-forced label styles explicitly, then inspect both rendered modes.

`scripts/color_contrast.ts` scores any two CSS colours ad hoc (hex, rgb, oklch,
named), and exits `0` when every pair passes AA, `1` on any failure, `2` on
usage error. Neither tool needs a browser, so both keep working when rendering
is blocked.

> Full profile behaviour, the calculator's flags and its output fields
> (`ratio` / `rating` / `apca_lc`): `resources/contrast_tooling.md`

---

# Layout Algorithms

Mermaid supports several layout engines (`dagre` default, `elk`, `tidy-tree`,
`cose-bilkent`) selected via YAML frontmatter inside the diagram source:

```yaml
---
config:
  layout: elk
  look: classic
  elk:
    mergeEdges: true
    nodePlacementStrategy: BRANDES_KOEPF
---
flowchart LR
    ...
```

Use `elk` for dense architecture diagrams (cleaner orthogonal routing), stick
with `dagre` for simple flows. The `layout` key is only honored by **flowchart**,
**state**, and **mindmap** diagrams — others use their own built-in algorithms.

> Full documentation: `resources/layout_algorithms.md`
> Rendered comparison gallery (dagre vs. elk vs. tidy-tree): `resources/examples/README.md`

---

# Diagram Organization

For projects with multiple architectural diagrams, organize around **lenses**
(perspectives) and **dual-density** fences inlined in the project README.

> Full documentation: `resources/diagram_organization.md`

## Primary pattern: inline dual-density

Each lens gets a README section with **two** mermaid fences: a simplified
overview (always visible, <=12 nodes) and a detailed reference (wrapped in
`<details>` collapsible, <=35 nodes). Both fences live in the markdown prose —
no separate `.mmd` files, no pre-rendered PNG pipeline (GitHub and GitLab
render mermaid fences natively).

````markdown
### System Overview

```mermaid
{simplified — <=12 nodes}
```

*Caption* | VCS: X.X ✅

<details>
<summary>📋 Complete diagram (N nodes)</summary>

```mermaid
{detailed — <=35 nodes}
```

</details>
````

## Workflow for codebase exploration

When invoked as "generate architecture diagrams for this codebase," do **not**
try to hold the whole codebase in the main agent's context. Delegate the
enumeration step to subagents so the diagram-authoring agent keeps a clean
context to reason in. Loop per lens:

1. **Enumerate components — via subagents and LSP, not raw grep.**

   Dispatch **one `Agent(subagent_type="Explore")` per lens** in parallel.
   Each subagent reports back only the structured component list for its
   lens, keeping the main agent's context clean for diagram authoring.

   Inside each subagent, prefer the **`lsp` skill** when available — it
   provides language-server-backed symbol enumeration, cross-references
   (which map directly to diagram edges), and impact analysis (which
   surfaces coupling strength). Fall back to `Grep` / `Glob` only where the
   LSP can't reach (shell scripts, config files, IaC):

   | Lens | Primary LSP queries | Fallback |
   |------|---------------------|---------|
   | `architecture` | Top-level symbols, module boundaries, public exports | `Glob` for directory tree |
   | `data-flow` | References for each I/O helper (DB client, HTTP client, event bus) | `Grep` for `fetch`/`requests`/SQL strings |
   | `deployment` | — | `Glob` + read for Dockerfiles, Terraform, `*.yaml` manifests |
   | `security` | References to auth/crypto helpers, middleware symbols | `Grep` for decorators, middleware wiring |
   | `sequence` | Call graph for an entry-point symbol | `Grep` for route/handler decorators |
   | `state` | Enum / state-machine symbols and their transition call sites | `Grep` for state-constant usage |

   The subagent returns **a ≤500-word structured report** — a component list,
   edge list, and any notable external integrations. No raw code.

2. **Draft the detailed fence first** (<=35 nodes, subgraphs by
   responsibility, edge labels for what travels between nodes). Work from the
   subagent reports — do not re-explore the code yourself.

3. **Collapse to the simplified fence** — replace each subgraph with a single
   node, drop internal wiring, keep the top-level narrative.

4. **Validate: the lint is mandatory** and may not be skipped. One run covers
   parsing, complexity (structural clarity) and contrast (colour clarity):
   ```bash
   bunx @jpeakai/remark-lint-slopstopper README.md
   ```
   A non-zero exit is a **blocker**. Fix by shrinking,
   splitting, or recoloring — do not relax the budget, do not skip the
   audit. If you added custom colors, their palette must come from
   `resources/color_theming.md`, not from ad-hoc hex picks.

5. **Render PNGs only if needed** for PDFs / slides / non-mermaid viewers via
   `scripts/render_mermaid.sh`. Do not re-link them from the README that
   already holds the fences. If the render fails, run the triage above —
   a browser or cache failure is never a reason to change a diagram that
   just passed both gates.

### Why subagents + LSP over direct exploration

- **Context hygiene.** Exploration pulls huge amounts of code into context;
  diagram authoring needs a clean slate to reason about naming, layout, and
  layering. Subagents return structured summaries, not raw files.
- **Parallelism.** Dispatching one subagent per lens in a single message runs
  them concurrently — the six-lens survey takes ~one wall-clock lens-time.
- **Cross-reference accuracy.** LSP's `find references` produces a *real*
  call graph; grep produces a text-match approximation that misses method
  dispatch, dynamic imports, and renames. For edges labeled "calls" or
  "invokes," LSP is authoritative.
- **Failure modes to watch.** If the LSP skill reports no server is
  available for the codebase's primary language, don't pretend — tell the
  user, and fall back to `Explore` + `Grep` with the caveat that edges may
  be undercounted.

## Key concepts

- **Lenses**: architecture, data-flow, deployment, security, sequence, state.
- **Density tiers**: simplified (overview, always-visible) vs detailed
  (reference, collapsed).
- **Split, don't relax** — if the detail fence exceeds 35 nodes, break the
  lens into per-subsystem sections rather than loosening the budget.
- **Legacy file-per-diagram** pattern (`docs/diagrams/{lens}--{scope}.md` +
  PNG links) remains supported for wikis/static sites that can't inline
  mermaid — see `resources/diagram_organization.md`.

---

# Common Pitfalls

## Multiline Text in Node Labels

**`\n` does NOT work** in flowchart node labels — renders as garbled characters.
Use `<br/>` instead:

```mermaid
flowchart LR
    A["Line one<br/>Line two"]
```

Alternative for Mermaid v10.1+: markdown strings with real newlines:
```mermaid
flowchart LR
    A["`**Phase 1**
    Creates output tables`"]
```

| Feature | `<br/>` tags | Markdown strings |
|---------|-------------|-----------------|
| Mermaid version | All versions | v10.1+ |
| Inline formatting | No | Bold, italic |
| Auto-wrap | No | Yes |

### Where `<br/>` does NOT work

- **Subgraph labels** — use short single-line titles
- **erDiagram** — uses different syntax

## Avoid Unicode in Node Labels

Characters like U+21B3, U+2192, U+00B7 can cause rendering failures in mmdc even
when they display in browser previews. Stick to **ASCII-only text** in node labels.

---

# Quick Reference

## Variant Tuples

| Variant | Flags | Best For |
|---------|-------|----------|
| `dark_transparent_png` | `-e png -t dark -b transparent` | Dark UIs, slides (default) |
| `default_white_png` | `-e png -t default -b white` | README, light docs, print |
| `dark_transparent_svg` | `-e svg -t dark -b transparent` | Scalable dark docs |
| `default_white_svg` | `-e svg -t default -b white` | Scalable light docs |

## Exit Codes

| Tool | 0 | 1 | 2 |
|------|---|---|---|
| `@jpeakai/remark-lint-slopstopper` | No findings | Findings remain, or a plugin failed to load | Usage error (bad flag / missing file) |
| `color_contrast.ts` | All pairs pass WCAG AA (>=4.5:1) | Any pair fails | Usage error |
| `render_mermaid.sh` | Every variant rendered **and verified** as a real PNG | Render failure (stderr carries `class` / `evidence` / `remedy`) or usage error | — |
| `mmdc` | All rendered | Render failure (see stderr) | — |

## Render failure classes

`NPM_CACHE_PERMISSION` · `BROWSER_MISSING` · `SANDBOX_DENIED` ·
`NETWORK_UNREACHABLE` · `DIAGRAM_SYNTAX` · `UNKNOWN` — only `DIAGRAM_SYNTAX`
means the diagram is at fault. See `resources/render_troubleshooting.md`.

## Resources

| File | Content |
|------|---------|
| `resources/document-types/README.md` | How to pick a document type; the invariants every type shares; how to add one |
| `resources/document-types/pr-review.md` | PR review companion: a visual diff of a change, section by section |
| `resources/document-types/plan.md` | Implementation plan: proposed changes, laid out before the code exists |
| `resources/document-types/educational.md` | Educational / illustrative guide: concept beats, monotonic build, shared palette, one-pager contract |
| `resources/gfm_beta_diagrams.md` | Why `-beta` types fail on GFM hosts; render-to-PNG/SVG with sibling `.mmd` pattern; non-beta alternatives |
| `resources/color_theming.md` | Profile selection, categorical families, five shades, compound boundaries and renderer constraints |
| `resources/color_palette_recipes.md` | Semantic category assignments using the selected profile |
| `resources/color_host_themed_renderers.md` | Host-forced text, resolved surfaces and visual verification limits |
| `resources/contrast_tooling.md` | Contrast profiles and rules of `@jpeakai/remark-lint-slopstopper`, and the full CLI surface of the ad-hoc pair calculator |
| `resources/render_troubleshooting.md` | Render failure triage: signature → class → remedy, artifact verification, escalation, when to stop |
| `resources/diagram_organization.md` | Lens naming, dual-density approach, README sync |
| `resources/layout_algorithms.md` | `layout` + `look` config for dagre / elk / tidy-tree / cose-bilkent, ELK tuning keys, per-diagram-type support |
| `resources/pattern_render_markdown.md` | Full render-from-markdown documentation |
| `resources/examples/` | Sample `.mmd` files and rendered PNG output (includes layout comparison gallery) |
| `resources/iconify/` | Iconify icon-pack reference (subdirectory — see files below) |
| `resources/iconify/iconify_setup.md` | Iconify icon pack setup guide |
| `resources/iconify/iconify_logos.md` | Available Iconify logo icons |
| `resources/iconify/iconify_mdi.md` | Available Material Design icons |
| `resources/iconify/iconify_cloud.md` | Cloud-provider icon catalogue |
| `resources/iconify/iconify_saas.md` | SaaS / product icon catalogue |
| `scripts/render_mermaid.sh` | Render both default variants for a markdown file; also `--doctor` (probe the host), `--verify` (is this a real PNG?), `--classify` (stderr → failure class) |
| `scripts/color_contrast.ts` | WCAG + APCA contrast calculator for arbitrary CSS color pairs (ad-hoc / stdin batch) |
| `scripts/Makefile` | `make fix` + `make ci` SDLC loop plus `cli-demo` target showing the lint and the pair calculator |
