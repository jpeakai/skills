# richdocs — ADR log: the foundations

The founding records of the richdocs skill: ADR-001 to ADR-013, in the order they
were first written down. They moved here, unedited, when
[`adr-log.md`](adr-log.md) reached the 500-line limit
(`.claude/rules/claude_skills/index.md`). Later records refine or supersede some of
them, and say so in their Status line. Read both files before changing anything.

### ADR-001 — Companion, not replacement

- **Status:** accepted
- **Context:** discovery docs must stay readable on GitHub and reviewable as plain
  diffs; earlier attempts replaced markdown with HTML apps that rotted.
- **Decision:** the `.md` is canonical and committed; HTML is generated into
  gitignored `tmp/richdocs/` and regenerated at will. Fenced rich blocks
  degrade on GitHub to visible JSON code blocks.
- **Consequences:** no committed HTML to drift; sharing uses `--inline`.
- **Lens:** when a feature tempts you to add authoring state to the HTML side, put it
  in the markdown or a data `.json` instead — the HTML must always be regenerable.

### ADR-002 — Packaged scripts here; teaching patterns stay in the `cli` skill

- **Status:** partially superseded by ADR-007 — the *scope* decision stands
  (richdocs ships packaged tools; rung-4 SPA builds are out of scope), but
  the lateral links from runtime surfaces to the `cli` skill were removed;
  richdocs surfaces no longer reference sibling skills. Refined by ADR-021:
  a sidebar indexing the document's own headings is not rung 4.
- **Decision:** `richdocs` ships runnable, generic tools; its resources cover only
  what's new (stencil pack, block contract, serving, recipes). A doc that outgrows the
  companion (routing, sidebar, views) graduates to a full SPA build — see the fidelity
  ladder in `discovery-docs.md`.
- **Lens:** before adding a feature to `md2html.py`'s template, ask "is this rung 4?"
  — if yes, it belongs in a standalone SPA project, not here.

### ADR-003 — Vendored stencil zip, loaded in memory

- **Status:** accepted
- **Context:** the tfs `diagrams` module proved the draw.io extraction; the
  user wants the icon library on-hand without depending on the tools-tfs
  repo. GitHub renders SVG; icons work in markdown *and* HTML.
- **Decision:** copy `stencils.json.zip` + `NOTICE` into `assets/`;
  `stencil.py` unzips in memory (`io.BytesIO`, `functools.cache`), located
  relative to `__file__`. The extractor script is *not* vendored — refresh
  procedure documented in `stencil-library.md`.
- **Consequences:** ~3.4 MB in the repo (accepted); no runtime coupling to
  tools-tfs; re-extraction requires the source repo.
- **Lens:** when the pack needs new shapes, re-vendor the whole zip from the
  source extractor — never hand-edit entries or unzip into the repo.

### ADR-013 — If a brand ships a ramp, the schema must hold it and the gate must check it

- **Status:** accepted (extends ADR-012)
- **Context:** the showcase "did not reflect the true colour palette" because it
  could not — `canvas.plotly.<mode>` held only `series`, so **five sixths** of a
  documented data-viz system (muted, sequential, diverging ×2, status) had nowhere
  to live. The palette was not wrong, it was *absent*, and nothing failed because
  nothing was looking.
- **Decision:** the schema now carries `muted`, `sequential`, `diverging`
  (`good`/`zero`/`bad`), optional `divergingAlt`, and a top-level `status`
  (`colours` + `labels`). `themecheck.py` gates every one of them:
  sequential must be **monotone in OKLab lightness** with ΔL ≥ 0.06 (else the steps
  cannot be ranked); the diverging **poles must separate by ΔE ≥ 12 under simulated
  deuteranopia**; the midpoint must be **achromatic** (a hue at zero reads as a
  value); status colours must clear AA **and carry a label** (colour never alone);
  adjacent categorical slots must clear the CVD relief floor.
- **Consequences:** **green↔red diverging is now structurally impossible to ship** —
  its poles collapse to ΔE ≈ 1–3 and the gate rejects them. The gate found a real
  defect on its first run: V2's categorical slots 4/5 separated by only ΔE 7.7; the
  order was re-optimised to 13.8. V2 ships **no** `divergingAlt`, because no
  green-adjacent hue survives against its pink (scan: hue 160 → ΔE 1.8; only ≥220,
  which is blue, clears 12) — the honest answer was to omit it, not invent one.
- **Lens:** a token schema is a *contract about what can be expressed*. When a brand
  documents something the schema cannot hold, the schema is the bug — and the moment
  a ramp becomes expressible, it becomes renderable, so it must simultaneously become
  **checkable**. Ship the field and the gate in the same change, or you have just
  built a new way to be silently wrong.

### ADR-012 — `accent` has three jobs; a gate checks the pairings CSS actually renders

- **Status:** accepted
- **Context:** the V2 AI theme shipped **contrast-clean and completely off-brand**.
  Its `#FFC000` yellow accent served BOTH text AND fills, but yellow is **1.64:1 on
  white** — legal as a surface, impossible as text. Unable to satisfy that token, the
  pack quietly substituted a cyan V2 does not own, and every check passed. **The gate
  was green because it was measuring the wrong thing.**
- **Decision:** split the accent into three tokens, with fallbacks so older packs
  keep working:
  - `accent` — the **fill** (CTAs, rules, active states). No text-contrast duty.
  - `onAccent` — the text that sits **on** that fill (defaults to `bg`).
  - `link` — the **text-safe** accent for headings and links (defaults to `accent`).
  Geometry joins them (`radius`, `pill`), because "square corners" is a brand rule
  that CSS defaults were silently overriding. Then `themecheck.py` — wired into
  `make ci` — validates **the pairings the CSS actually renders**, each check naming
  the rule it guards. It fails the build; it never "helpfully" adjusts a colour.
- **Consequences:** a brand with no text-safe accent (V2 has none) declares
  `link` = its ink and lets the accent reach text as a **rule** (a yellow underline),
  never as a glyph — which is what the brand does in real life. No invented colours
  remain in the V2 pack: every hex is one V2 actually owns.
- **Lens:** when a design token cannot satisfy every job it is asked to do, the
  token is wrong — **split it**. And a contrast check that does not mirror the CSS
  is theatre: check `onAccent`-on-`accent`, not `fg`-on-`bg`, because the button is
  what the reader has to read.

### ADR-011 — A showcase is a gallery OR a single brand, never a mixture

- **Status:** accepted
- **Context:** two different jobs were being asked of one artifact: *compare brands*
  (needs every brand in one page, switchable) and *hand someone a brand reference*
  (must contain that brand and nothing else — shipping a client a page with a
  competitor's palette inside it is not acceptable, even if it is not displayed).
- **Decision:** `showcase.py` with no `--theme` emits a **gallery**: every installed
  brand embedded, a brand switcher, and a light/dark toggle; each brand honours its
  own `defaultTheme` on selection. `--theme NAME` emits that brand **alone** — the
  switcher element is removed and no other brand's tokens or CSS are in the file. A
  test asserts the other brand's name does not appear anywhere in the artifact.
- **Consequences:** every brand's `theme.css` must be **scoped** to
  `:root[data-brand="<name>"]` so brands cannot leak in a gallery. `@import` cannot be
  scoped (legal only at the top of a sheet), so imports are hoisted out and emitted
  once. The scoper is a regex — fine for hand-written `theme.css`, not arbitrary CSS.
- **Architecture diagrams** are composed from the vendored stencils and carry their
  own `mxfile` source in the SVG's `content` attribute, so they re-open in
  diagrams.net as **real AWS shapes**, not a flattened picture. A missing stencil id
  fails the build (escalators-not-stairs) rather than rendering an empty box.
- **Lens:** when one artifact is asked to serve two audiences with incompatible
  containment rules, emit two artifacts. Do not hide content and call it isolation.

### ADR-010 — The brandpack is paired with the doc, not with the output directory

- **Status:** accepted
- **Context:** multi-file mode wrote one `design-tokens.json` per output dir, fetched
  by a fixed name — so a second doc rendered with a different `--theme` into the same
  dir **silently overwrote the first doc's brandpack**, and both then loaded the
  survivor's palette. A shared mutable filename in a dir designed to hold many docs
  was the bug.
- **Decision:** the pack is paired with the doc, exactly as the markdown already
  is: `<stem>.md` · `<stem>.html` · **`<stem>.tokens.json`**. The filename travels
  in `#rd-config` as `tokensSource`, so the viewer fetches its own pack.
- **Consequences:** one output dir can now hold any mix of themes. The
  "edit the tokens in the output dir and refresh" loop still works — the file is
  just named after the doc. `--inline` was never affected (tokens are embedded).
- **Lens:** in a directory that holds N of something, nothing may have a fixed
  singular name. If a file is *about* a doc, name it after the doc.

### ADR-009 — Named themes are a directory, and `theme.css` is part of the contract

- **Status:** accepted
- **Context:** a brandpack can *name* a font family but cannot **load** one — the
  first OsakaNights render fell back to system fonts because nothing `@import`ed Fira
  Sans. Nor can it say "headings use the display face" without reinventing CSS as
  tokens. And `--tokens path/to/pack.json` made the caller track where each brand
  lived, which does not scale past one brand.
- **Decision:** a theme is a **directory** at `resources/themes/<name>/` holding
  `design-tokens.json` (required) and `theme.css` (optional). Both are **real
  files inside the skill — never symlinks out to a project.** `.claude/` must stay
  isolated and portable: copy it anywhere and every theme still resolves. A brand
  that also lives in the wider repo is a *deliberate dual copy*; a symlink would
  be a co-dependency. A test asserts no theme file is a symlink. The pack chooses the
  faces (`fonts.display`/`body`/`mono`); `theme.css` only `@import`s the webfiles and
  expresses layout JSON cannot. `--theme NAME` resolves both; `theme.css` is injected
  *after* `viewer.css`, so a brand can override anything. Unknown names crash loudly
  and list the installed set. `--tokens` survives for ad-hoc packs, but a named theme
  supersedes it.
- **Consequences:** brands are now additive — drop in a directory, no code change.
  The token schema stays small (it only holds what canvas renderers need, which
  genuinely cannot read CSS); everything expressible in CSS stays in CSS.
- **Lens:** when a config format starts growing fields that are really just CSS,
  stop — give the brand a stylesheet instead. Tokens exist for the values CSS
  **cannot** reach (the canvas palettes, ADR-004). Everything else belongs in
  `theme.css`.

### ADR-008 — The generator holds no template; `assets/viewer.*` is the page

- **Status:** accepted (supersedes the `FALLBACK_TOKENS` half of ADR-004)
- **Context:** `md2html.py` had grown to 641 lines, **334 (58%) a triple-quoted
  `TEMPLATE`** holding the whole HTML/CSS/JS — no linting, Python-escaped regexes,
  and 241 lines of real logic buried in noise. Separately, `FALLBACK_TOKENS` was a
  55-line hand-copy of `design-tokens.json` guarded by an equality test — and a test
  asserting two things are identical means there should only be one of them.
- **Decision:** split at three seams — `assets/viewer.html` (shell, 44 lines),
  `assets/viewer.css` (chrome, 80), `assets/viewer.js` (renderer, 261).
  `md2html.py` (274) is now purely a generator: read assets, substitute, write.
  **All generation-time values (build id, source, CDN pins, fallback tokens) are
  delivered in one `<script type="application/json" id="rd-config">` block**, so
  `viewer.js` carries **zero placeholders** and is real, lintable JavaScript.
  `viewer.html` is the only file with `{{...}}`. `FALLBACK_TOKENS` is now *read*
  from `design-tokens.json` at import — the duplicate literal is deleted, and the
  hazard is retired rather than policed.
- **Consequences:** the browser behaviour is untestable by the Python suite
  (ADR-006 still bites), so a browser smoke-test of **both** output modes is
  mandatory after any asset edit. Missing/corrupt asset files now crash at import
  — correct (escalators-not-stairs). Two tests enforce the seam:
  `test_viewer_js_has_no_template_placeholders` and
  `test_assembled_html_inlines_the_css_and_js_assets`.
- **Lens:** when a generator starts carrying the artifact it generates, split
  them. Code that is *data to this program but source to another language*
  belongs in a file of that language, where its own tooling can see it. And when
  you find yourself writing a test that asserts two copies are equal, **delete a
  copy** — don't police the duplication, remove it.

### ADR-004 — Two-palette brandpack (chrome CSS vars + canvas JS palette)

- **Status:** accepted; the `FALLBACK_TOKENS` hand-sync hazard is **retired by
  ADR-008** (the fallback is now read from the asset, not re-declared)
- **Context:** proven in the adaf sdag viewer; canvas renderers (cytoscape,
  plotly) cannot read CSS custom properties.
- **Decision:** one `design-tokens.json` carries both palettes; the template
  applies `themes.*` as CSS vars and feeds `canvas.*` into renderers; theme
  flip does both. Data-encoding colours (`categoryColours`, status) are
  brand- and theme-invariant. *(Categories superseded by ADR-023.)*
- **Consequences:** ~~one hand-sync hazard remains~~ — retired by ADR-008.
  `FALLBACK_TOKENS` is now read from `assets/design-tokens.json`, so there is
  only one copy of the default palette.
- **Lens:** any new themable surface gets a token in *one* of the two
  palettes by asking "can CSS reach it?" — never a hardcoded hex in
  `viewer.css` or `viewer.js`. (The sole exception is `.rd-error`, which must
  stay visible when token loading is the thing that failed.)

### ADR-005 — Pinned CDN, lazy canvas loads, no vendoring of JS libs

- **Status:** accepted
- **Context:** vendoring cytoscape/plotly/mermaid (~5 MB+) into every output
  dir was rejected; local viewing has network; offline is announced
  degradation.
- **Decision:** exact-version jsdelivr pins (table in `serving.md`);
  cytoscape/plotly injected only when a doc uses their blocks; fetch failures
  console.error and render visible error blocks.
- **Consequences:** fully-offline viewing is out of scope for v1; revisit
  with a `--vendor` flag if it becomes a real requirement.
- **Lens:** bump a pin deliberately (test all three block types), never by
  floating a major.

### ADR-006 — Evals deferred

- **Status:** accepted (deferred work)
- **Context:** the repo's then-current eval contract (since retired) defined a
  golden/eval harness; building it now would have doubled the initial scope.
- **Decision:** ship v1 with the free deterministic gate only (`make ci`,
  ≥90% coverage). Eval goldens (render a fixture doc headlessly, assert
  blocks render) are the first follow-up.
- **Lens:** when the first regression slips past `ci` (likely a template/JS
  behaviour Python tests can't see), that's the trigger to build the eval
  suite — don't wait for a second.

### ADR-007 — Self-contained: vendor the mermaid toolchain, never reference sibling skills

- **Status:** accepted (user adjudication; partially supersedes ADR-002)
- **Context:** a companion shipped with an unparseable `mindmap` fence
  (quoted labels + `&amp;` entity → 0 nodes); `md2html.py` passes fences
  through verbatim, so the breakage surfaced only in the browser. A mermaid
  parse + contrast gate exists as prior art. The first fix pointed richdocs
  at the sibling skill's scripts; the user overruled it: **richdocs must
  stand on its own — it must not rely on or be aware of sibling skills.**
- **Decision:** vendor a wholesale copy of the mermaid toolchain at
  `vendor/mermaidjs-diagrams/` (scripts, tests, Makefile, resources — same
  vendoring posture as the stencil zip, ADR-003). SKILL.md mandates running
  the *vendored* `mermaid_complexity.ts` + `mermaid_contrast.ts` on the
  source markdown before `md2html.py`; non-zero exit is a blocker. All
  cross-skill links in SKILL.md and `resources/*.md` were removed. The case
  is in `resources/learned/mermaid-syntax-gate.md`.
- **Consequences:** ~1.5 MB duplicated; drift from upstream is accepted and
  managed by re-vendoring (see refresh below). Gate needs `bun` +
  `bun install --cwd vendor/mermaidjs-diagrams/scripts --frozen-lockfile`
  once. Maintainer docs (this file) may name the upstream for provenance;
  runtime surfaces (SKILL.md, resources) must not.
- **Refresh procedure:** re-vendor wholesale — `rsync -a --exclude
  node_modules --exclude '.*cache*'` from the upstream skill dir, then
  `mv SKILL.md mermaidjs-diagrams.md` inside the copy, repoint the links
  upstream wrote to it, and `sed` every remaining mention in `resources/**`.
  Re-run `bun install --frozen-lockfile` and `make -C …/vendor/mermaidjs-diagrams/
  scripts test-cov`. Never cherry-pick individual files.
- **Lens:** when richdocs needs a capability that lives in another skill,
  vendor a wholesale copy into `vendor/` — never link to, invoke, or
  instruct the agent to read a sibling skill's files. Self-containment
  outranks the never-duplicate rule for anything richdocs *operates with*.

