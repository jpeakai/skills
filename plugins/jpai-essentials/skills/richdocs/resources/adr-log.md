# richdocs — ADR log

The decision log for the richdocs skill. This is the **child** of
[`../CLAUDE.md`](../CLAUDE.md) (the maintainer guide) — it was split out to keep that
file under the 500-line invariant (`.claude/rules/claude_skills/index.md`). Read it
before changing anything: each entry carries a **Lens**, a forward-looking rule to
apply to the next related decision.

This file holds ADR-014 onwards, newest first. The founding records, ADR-001 to
ADR-013, are in [`adr-log-foundations.md`](adr-log-foundations.md).


### ADR-024 — Every diagram opens full screen and zooms deep

- **Status:** accepted (replaces the click-to-expand lightbox in `viewer.js`)
- **Context:** only pictures could be expanded, with no zoom, and never a
  Cytoscape.js graph. A plain wheel could not zoom anything, so a complex diagram
  stayed unreadable. The showcase had no full-screen view at all.
- **Decision:** `viewer-zoom.js` (styles in `viewer-zoom.css`) is inlined by the
  viewer and the showcase. An SVG or image opens in a modal on click; a graph opens
  from its own "Full screen" button, because a click inside a graph drags nodes.
  In the modal the wheel zooms about the cursor, up to 40 times the fitted view, and
  a drag pans. An SVG zooms through its `viewBox`, so it stays vector-sharp; a graph
  is a second, fully interactive Cytoscape.js copy built from the first one's
  elements and style. In the page, only Ctrl or Cmd + wheel (a trackpad pinch
  arrives as exactly this) zooms a diagram in place, and never wider than its fit.
- **Consequences:** a plain wheel always scrolls the page. The graph renderer
  exposes its instance and style on its element (`__rdCy`, `__rdCyStyle`). The maths
  and the modal are tested in happy-dom; cursor tracking and the graph copy are
  checked in a real browser.
- **Lens:** a long document must never trap the reader inside a diagram. A new
  diagram kind opens full screen and zooms by the same rules, through this module.

### ADR-023 — One categorical palette; a category is a slot

- **Status:** accepted (supersedes the `categoryColours` half of ADR-004)
- **Context:** "chart series" and "category colours" were two names and two
  copies of one idea (`categoryColours` was a reordered subset of `series`, or
  unrelated AWS hues), a repeated source of confusion.
- **Decision:** a brand has ONE categorical palette, `canvas.plotly.<mode>.series`.
  It colours chart series and every diagram category (Cytoscape.js compounds,
  Mermaid subgraphs, draw.io icons, embedding topics). A category takes the next
  slot in a declared order (else first appearance), never cycles, and gets no
  colour past the last slot. `categoryColours` is deleted, and `themecheck.py`
  fails any pack that ships it. Helpers live in `viewer-cytoscape.js`.
- **Consequences:** categories follow brand and mode, and pass the series gate.
- **Lens:** a new encoding of "which kind of thing" takes palette slots. Never add
  a second name-to-colour map.

### ADR-022 — The sidebar folds, the article folds, and the showcase shares both

- **Status:** accepted (extends ADR-021)
- **Context:** a hand-patched companion added a sidebar that collapses to a rail,
  contents branches that fold per level, and article sections that fold in place.
  Regeneration would erase them (ADR-001); the showcase had no navigation.
- **Decision:** `viewer-toc.js` builds all three; styles live in `viewer-toc.css`.
  The fold button sits beside its heading, never inside it. The lone top heading
  does not fold, and navigating to a heading unfolds everything around it. A
  folded body stays in the layout (`height: 0`, `visibility: hidden`), so a
  diagram re-rendered while folded still measures a real width. The showcase
  inlines both files and calls `rdInitToc` with a `header` and `selector`.
- **Consequences:** one module drives both pages, so they cannot drift.
- **Lens:** another page passes options to `rdInitToc`, never forks it. Anything
  a fold hides must stay measurable.

### ADR-021 — A heading sidebar is navigation, not rung 4

- **Status:** accepted (refines ADR-002)
- **Context:** long companions had no navigation, so readers scrolled end to
  end. A sidebar patched into one generated page worked, but regeneration
  erased it, because the HTML is never the source (ADR-001). ADR-002 had
  filed every sidebar under rung 4 (a standalone SPA), which left no home for
  the simplest kind: an index of the document's own headings.
- **Decision:** the viewer builds a collapsible sidebar from the rendered `h1`
  to `h4` headings whenever a document has three or more. It lives in
  `assets/viewer-toc.js`, hoisted before `viewer.js` like the other
  renderers, and runs once after the markdown is parsed and before any
  fenced block is upgraded. Anchors are GitHub-style slugs, unique in
  document order (`setup`, `setup-1`), and never reuse an id already on the
  page. Selecting an entry scrolls to the heading, records the fragment, marks
  the entry `aria-current` and moves focus to the heading. The wide layout
  remembers collapsed or open in `localStorage` (`richdocs-toc`). Below 72rem
  the sidebar becomes a drawer that always opens closed, takes focus when
  opened, and closes on Escape, on an outside tap, or on a choice. The article
  keeps its 52rem column, and print hides the sidebar. Fewer than three
  headings leaves the page exactly as before.
- **Consequences:** the sidebar is derived, never authored, so ADR-001 holds:
  it is rebuilt on every render, in both output modes. Its behaviour is
  tested in happy-dom through `bun test` (`scripts/viewer_toc.test.ts`),
  which makes bun and happy-dom test-time dependencies of this skill's gate.
  The shipped scripts stay stdlib Python. What needs a layout engine (which
  heading is under the header) cannot be asserted without faking geometry, so
  it is checked in a real browser instead, per the extension checklist.
- **Lens:** rung 4 is **routing and views**: state the markdown does not hold.
  A feature derived wholly from the rendered document, and rebuilt on every
  render, belongs in the companion. Ask "could the markdown alone regenerate
  this?" If yes, it is not rung 4.

### ADR-020 — A vendored copy carries no `SKILL.md`

- **Status:** accepted (refines ADR-007)
- **Context:** the packs failed marketplace validation. A harness registers
  every `SKILL.md` beneath a plugin as a skill, so the vendored
  `mermaidjs-diagrams/SKILL.md` declared the name `mermaidjs-diagrams` a second
  time and the whole `jpai-essentials` plugin was rejected as a duplicate.
  Vendoring was correct, keeping upstream's filename was not.
- **Decision:** on the way in, upstream's `SKILL.md` is renamed to
  `<name>.md` — here `vendor/mermaidjs-diagrams/mermaidjs-diagrams.md`. Every
  relative link that resolved to it is repointed, in the copy and in the
  richdocs surfaces that cite it, and so is every mention left in the copy's
  own runtime surfaces (`resources/**`) — a run must not be told to open a file
  that is not there. Its provenance documents (`README.md`, `CLAUDE.md`) keep
  upstream's wording, because they are addressed to whoever edits upstream,
  where the file really is `SKILL.md`.
- **Consequences:** the copy is no longer byte-identical to upstream, so the
  refresh is rsync plus a scripted rename rather than rsync alone.
  `uv run scripts/validate_plugins.py` asserts no `SKILL.md` survives below a
  composed skill's root, so a refresh that forgets the rename fails in CI
  instead of at the marketplace.
- **Lens:** a directory a harness scans holds exactly one registrable
  entrypoint. Anything copied in for self-containment gets its entrypoint
  demoted to a plain document, because self-containment must not cost the
  right to be installed.

### ADR-019 — Output report is worktree-aware and prints absolute paths

- **Status:** accepted
- **Context:** docs are generated across a multi-worktree checkout; the source `.md`
  frequently sits in a different worktree than the process cwd. The old
  `wrote <path>` line was relative, so it only cmd+clicked open when the editor root
  matched cwd — in another worktree it did not resolve. The output also carried no
  worktree/branch context, so cross-worktree docs in flight had no concise shared name.
- **Decision:** after every render, `main()` prints a `── richdoc output ──` block via
  `output_report()`: slug (the doc stem), worktree dir + branch resolved from the
  **output file's own directory** with `git -C <dir> rev-parse` (never the cwd),
  absolute source and html paths, any extra companion files, and two serve commands
  (`serve.py` no-store + stdlib `python3 -m http.server --directory <abs-dir>`) from
  `serve_commands()`. `git_context()` is read-only and returns `(None, None)` outside a
  git worktree rather than raising. The old `--serve-hint` print branch is subsumed
  (the report always prints serve commands); the flag remains parsed for back-compat.
- **Consequences:** `git` is invoked read-only twice per run; a non-git output dir
  reports `(not a git worktree)` and still prints absolute paths + serve commands. An
  unborn branch (repo with no commit) resolves to `-`; real worktrees have a commit.
- **Lens:** when a tool emits a path a human is meant to act on, resolve it from the
  artefact's own location and print it **absolute** — a relative path silently assumes
  the reader shares your cwd, which across worktrees they do not.

### ADR-018 — A project-local override dir supplies themes; the default brand is a named theme

- **Status:** accepted (user adjudication)
- **Context:** two asks arrived together. (1) A plain `md2html.py DOC.md` rendered with
  the neutral `assets/design-tokens.json`, so the *default* output was unbranded — the
  user wanted the default to be a real theme (`osakanights`). (2) A project needs to
  override or add themes without editing the skill's committed `resources/themes/`
  (which ADR-009 keeps as portable, symlink-free skill files).
- **Decision:** `DEFAULT_THEME = "osakanights"`, applied by a new pure `resolve_brand()`:
  explicit `--theme` wins, else an explicit `--tokens` (the raw escape hatch, no
  `theme.css`), else `DEFAULT_THEME`. `--tokens` default became `None` so "not passed"
  is detectable. Theme lookup now scans **two roots in precedence order** via
  `theme_search_dirs()`: the cwd-relative `PROJECT_THEMES_DIR = tmp/richdocs/theme/`
  (included only when it exists) then the built-in `THEMES_DIR`. `available_themes()`
  and `load_theme()` take an injectable `project_dir` param (default `PROJECT_THEMES_DIR`)
  so tests pass a real `tmp_path` — no monkeypatch, honouring the no-mock rule.
  `showcase.py` imports both functions, so it inherits override-awareness for free.
- **Consequences:** ADR-009 portability is intact — with no override dir the search
  collapses to exactly `[THEMES_DIR]` and the skill is byte-for-byte the built-in set.
  The override dir lives under gitignored `tmp/`, so overrides are project-local and
  uncommitted by design. The `test_themes_are_real_files_not_symlinks` invariant still
  guards `THEMES_DIR` only; the project dir is the *project's* own directory, outside
  the skill's portability contract.
- **Lens:** a *default* is a decision, not a neutral — pick the branded one and make the
  raw path an explicit opt-out, never the silent baseline. When adding a project
  customization point to a self-contained skill, make it an **optional, additive
  override dir** resolved by precedence (project → built-in): present it degrades
  richer, absent it degrades to fully self-contained — never a hard dependency on the
  project dir existing.

### ADR-017 — A map may opt into a real basemap; a page may compute its own data in-browser

Status: Accepted. Context: the showcase geo map "still showed no dark tiles" and the
user wanted the vector dark basemap their reference app uses, plus a way to prove the
DATA→TRANSFORM half of the pipeline (query complex data, feed the result to a block).
Decision, two opt-ins that keep the defaults untouched: (1) a `map`-view deckgl block
gains `basemap` (raster, a deck `TileLayer`) and `basemapStyle` (a **vector GL style** —
MapLibre owns the map + camera, deck rides as a `MapboxOverlay`). Both are free + keyless;
the vector path is preferred because MapLibre's tile pipeline is robust where a hand-rolled
raster layer can silently blank. (2) a page may run **duckdb-wasm** (in-browser OLAP SQL,
CDN ESM, mvp/eh bundle so no COOP/COEP) and drive any block from the result rows. Lens: a
basemap and a data engine are both **environment degradations, never requirement ones** —
default to no-dependency (brand canvas, seeded data), let a caller opt into the heavier,
more capable path explicitly; and when a raster tile layer "works for me" but blanks for a
user, reach for the library whose loader is battle-tested (MapLibre) before hand-tuning tiles.

### ADR-016 — A stated stylistic identity waives a gate via an explicit per-theme waiver

Status: Accepted. Context: OsakaNights' `Ghibli Pastel` series (L0.80/C0.11) is a
defining identity, used identically Day/Night; on the light plot its marks are ~1.7:1,
under the 3:1 mark-contrast rule. The maintainer ruled the palette higher priority than
that gate (three times); marks are always legended and clear CVD adjacency (ΔE 9.3).
Decision: a pack may declare `waivers.seriesContrast` (a required justification string);
`check_series` then skips mark-contrast for the PRIMARY series only, prints a visible
`[note]`, still enforces CVD adjacency, and still checks `seriesAlt` strictly. No waiver
= the strict rule for every other pack. Lens: when a deliberate stated identity conflicts
with a gate, the identity wins — but only via an explicit, self-printing, per-artifact
waiver, never a silent global loosen; waive the negotiable check (contrast, mitigated by
labels), never the non-negotiable one (CVD distinguishability).

### ADR-015 — Authored prose follows a global-audience standard; rendered content stays verbatim

- **Status:** accepted (2026-07)
- **Decision:** `resources/prose-style.md` holds the standard for prose this
  skill **authors** (showcase copy, UI/error strings, this skill's own docs, a
  discovery doc it is explicitly asked to upgrade): no em-dash, Australian
  English, short coherent clauses, ESL/translator readability, inclusive
  language, standardised vocabulary. The user's canonical markdown is the source
  of truth (ADR-001), so faithfully-rendered content is **never** rewritten to
  satisfy a style rule. ESL/translator readability is an evaluable check (proxy
  metrics or a round-trip translation), not an adjective. Detection is
  tooling-agnostic: the file names *what* to find, never *which* command.
- **Consequences:** SKILL.md gained one cross-cutting convention and a resources
  row.
- **Lens:** separate the prose you **author** from the prose you **render**;
  apply the standard to the former, preserve the latter verbatim. When enforcing
  a prose rule, describe the target, not the tool.

### ADR-014 — A 3D block is a *projection*, and a visual claim must carry its own referent

- **Status:** accepted
- **Context:** two needs arrived together. A doc had to explain **why a palette
  documented as "uniform chroma" was not uniform** — a 2D swatch row cannot show it,
  because the answer lives in a 3D space (a colour's chroma ceiling depends on its
  hue *and* its lightness). And the block set was capped at graph (cytoscape) and
  chart (plotly), with no way to render a spatial or geographic argument at all.
- **Decision:** add a ` ```deckgl ` block whose `layers[].type` is looked up on
  deck's global — so **every deck.gl layer works with no code change here**; the
  block is open by construction. The specific part is one idea: **a colour space is
  just a function `rgb -> [x, y, z]`.** Swap the projection and every mark moves;
  the data never changes. That is why one block serves both a gamut study
  (`OrbitView`) and a map (`MapView`) — a layer only ever asks *where does this
  datum live*. A datum carrying `hex` therefore needs **neither position nor
  colour**: it is its own coordinate. `map` view ships **no basemap by default** —
  the brand canvas is the basemap, no vendor key required (opt into real tiles via
  ADR-017's `basemap`/`basemapStyle`).
- **Consequences:** the first render was *correct and told the wrong story* — spokes
  to the gamut ring read as "chroma denied" but actually measured **unused headroom**
  (the clipped colours sat **on** the ring, spoke-less). A hex records what was
  **granted**, not what was **asked for**, so the spec now carries the intent
  (`targetChroma`) and draws **two** rings: the requested circle against sRGB's lumpy
  blob. Clipping is where the circle escapes the blob, and it reads without a caption.
- **Lens:** when a visualisation implies a *shortfall*, check what it is measuring
  the distance **from**. A rendering can only show the values it is given; if the
  claim is "you did not get what you asked for", then **the request is data and must
  be in the spec** — never inferred from the result, which by definition only knows
  the outcome. And when adding a renderer, expose the *library's* type system rather
  than a hand-rolled whitelist; keep your own cleverness to the one transform the
  library lacks.
