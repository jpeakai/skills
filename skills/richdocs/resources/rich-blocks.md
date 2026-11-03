# Fenced Rich Blocks & the Design-Tokens Brandpack

The contract for interactive blocks inside a markdown doc rendered by
`md2html.py`, and the token file that brands them.

## Block contract

Standard markdown renders as usual (marked, pinned). Three fence languages
get special treatment; each block's body is either **inline JSON** or a
**data pointer** `{ "data": "relative/path.json" }` fetched at render time
with `cache: no-store` + `?v=<BUILD_ID>`.

### ` ```mermaid `

Rendered by mermaid 11.x. Theme follows the document theme (`default` /
`dark`), re-initialised and re-rendered on every theme flip. The source must
pass `bunx @jpeakai/remark-lint-slopstopper` (parse, complexity and contrast). See the
"Mermaid gate" section in `SKILL.md`.

### ` ```cytoscape `

```json
{
  "elements": [
    { "data": { "id": "api", "label": "API", "parent": "vpc" } },
    { "data": { "id": "db",  "label": "DB" } },
    { "data": { "source": "api", "target": "db", "label": "reads" } }
  ],
  "layout": { "name": "dagre", "rankDir": "LR" },
  "height": 420
}
```

- `elements` follows Cytoscape's element JSON (compound nodes via `parent`).
- `layout` optional; default `dagre` left-to-right. `height` optional px.
- Stylesheet is built from `canvas.cytoscape.<theme>` tokens.
  Compound nodes opt into categorical colours with `data.category`.
  Leaf nodes can request the secondary fill with `data.variant: "alt"`.
  The packaged renderer does not read `data.colour`.
- Node tap → detail is intentionally not in the packaged viewer; when a doc
  needs routing/detail panels, it has outgrown the companion — build it as a
  standalone SPA sub-project (rung 4 of the fidelity ladder in
  `upgrade-recipes.md`).

### ` ```plotly `

```json
{ "data": [ { "type": "scatter", "x": [1,2,3], "y": [4,1,7] } ],
  "layout": { "title": "Cost by month" } }
```

Rendered with `Plotly.react`. The theme's `canvas.plotly.<theme>` tokens set
`paper_bgcolor`, `plot_bgcolor`, font colour, gridlines, and `colorway`
(series palette) — author traces colour-free unless the colour is data.
Prefer `type: "scatter"` over `scattergl` when points must be clickable or
e2e-addressable.

`height` sizes the canvas (default 420), same as the other blocks. Set it on the
payload, **not** in `layout` — the container is what Plotly's responsive mode
measures.

### ` ```deckgl `

3D and geographic scenes (deck.gl, lazy-loaded — it is the heaviest CDN lib, so
a doc that never uses it never pays for it).

```json
{ "view": "orbit", "space": "oklch", "height": 520,
  "gamut": [0.65], "targetChroma": 0.19,
  "layers": [ { "type": "PointCloudLayer", "pointSize": 11,
                "data": [ { "hex": "#7180fe", "label": "series 1" } ] } ] }
```

| Key | Meaning |
|-----|---------|
| `view` | `"orbit"` (3D, default) or `"map"` (geographic; positions are `[lng, lat]`) |
| `space` | orbit only — `"oklch"` (default), `"oklab"`, `"rgb"`. The projection applied to `hex` data |
| `layers[].type` | **any** deck.gl layer name, looked up on the global (`PointCloudLayer`, `ArcLayer`, `GeoJsonLayer`, …) |
| `gamut` | orbit only — draw the sRGB boundary ring at each listed lightness |
| `targetChroma` | orbit only — draw the *requested* chroma as a circle, and spoke every swatch that could not reach it |
| `basemap` | map only — `true` (OSM) or a raster tile URL template; a deck `TileLayer` under the scene |
| `basemapStyle` | map only — a **vector** GL style URL (e.g. CartoDB dark-matter); MapLibre owns the map, deck rides as a `MapboxOverlay`. Preferred over `basemap` (robust tiles) |
| `height` | canvas height in px (default 460) |

**`type` is looked up on deck's global, so every deck.gl layer works with no code
change here.** The block is open by construction; only the colour-space sugar
below is specific.

**The sugar — a datum that carries `hex` needs neither a position nor a colour.**
Both are derived from the colour itself: the datum *is* its own coordinate. That
is what lets a palette be authored as a plain list of hex strings. Supply
`getPosition`/`getColor` explicitly to override.

**Lighting is OFF by default** (`material: false` on every layer). deck.gl's lit
layers shade marks as 3D solids, which *darkens the fill* — a swatch would render
muddier than its own hex, and in a colour-space scene the mark is a colour claim.
Flat/unlit is the only colour-correct default; put `material` on a layer spec to opt
into shaded geometry.

`map` view draws **no basemap by default** — the brand canvas *is* the basemap, so no
vendor token is required. Opt into real tiles with `basemap` (raster) or `basemapStyle`
(vector, via MapLibre); both are free and keyless. Supply `initialViewState` to frame it.
The vector path needs MapLibre GL loaded (`cdn.maplibre` + its CSS) before the block renders.

> **Orbit framing gotcha:** deck's `zoom` here is `log2(pixels per world unit)`,
> **not** a map zoom. Every space is normalised to a ~1-unit extent, so a scene
> needs `zoom ≈ 9`; framing it like a map (`zoom: 2`) renders a perfectly correct
> scene the size of a postage stamp. The defaults handle this — override with care.

Theming reads `canvas.deckgl.<theme>` (`background`, `ink`, `text`, `warn`) when
present, and otherwise derives them from tokens every brandpack already ships, so
**no brandpack change is needed to adopt the block**.

### The data pointer (data-driven mode)

```json
{ "data": "graphs/full_graph.json", "height": 520 }
```

The heart of the pattern: generate the JSON from a real source (terraform
plan, dbt manifest, AWS pricing API) with a script, and the *document* never
changes — refresh re-fetches fresh data. Paths are relative to the served
directory. This only works over `http://` (see `serving.md`); in `--inline`
mode a data pointer that can't be resolved renders a loud error block, not a
blank space.

## The brandpack: `design-tokens.json`

One JSON file, copied verbatim into the output dir, fetched at runtime.
Re-brand = edit the copy, refresh. Schema (all keys required):

```json
{
  "fonts": { "body": "…", "mono": "…" },
  "themes": {
    "light": { "bg": "…", "fg": "…", "muted": "…", "accent": "…", "surface": "…", "border": "…" },
    "dark":  { "…same keys…" }
  },
  "canvas": {
    "cytoscape": { "light": { "nodeFill": "…", "nodeLabel": "…", "edge": "…",
                              "compoundBg": "…", "compoundBorder": "…" },
                   "dark": { "…" } },
    "plotly":    { "light": { "paper": "…", "plot": "…", "font": "…", "grid": "…",
                              "series": ["…", "…", "…", "…", "…"] },
                   "dark": { "…" } }
  }
}
```

### Why two palettes (the load-bearing design fact)

**Canvas renderers cannot read CSS custom properties.** So theming is split:

- `themes.*` → CSS variables under `:root[data-theme=…]` — styles the HTML
  chrome (text, tables, code, header).
- `canvas.*` → a parallel JS palette fed directly into Cytoscape stylesheets
  and Plotly layouts.

A theme flip must therefore do **two** things: restamp `data-theme` (chrome
re-themes instantly via CSS) *and* re-feed the canvas palette + re-render
every fenced block. The generated JS does both; if you fork the template,
keep both or dark mode will half-apply — the classic symptom is a dark page
with blinding white charts.

### Showcase diagram colour rules

The original showcase uses the shared Cytoscape renderer and a showcase-specific Mermaid renderer.
Both assign category borders from `canvas.plotly.<mode>.series`, using the same fixed page-wide category order.
Switching brand or mode changes the colour assigned to each slot, while category identity keeps its slot.

| Element | Fill | Border and label |
| --- | --- | --- |
| Cytoscape leaf | `nodeFill`, or `nodeFillAlt` for `variant="alt"` | `nodeBorder`, `nodeLabel` |
| Cytoscape compound without category | `compoundBg` at 0.55 background opacity | Dashed 1px `compoundBorder`, `nodeLabel` |
| Cytoscape compound with category | Opaque category tint | Solid 2px category border, `nodeLabel` |
| Detailed Mermaid subgraph | Same opaque category tint | Solid 2px category border, theme foreground label |
| Mermaid ordinary node | Theme surface | Theme accent border, theme foreground label |

The category tint is calculated per encoded sRGB channel: `round(0.16 × category + 0.84 × pageBackground)`.
This is an opaque premixed colour, not alpha transparency or an OKLCH interpolation.
Nested category groups therefore do not accumulate transparency.
Cytoscape edges use theme edge colours at 0.75 overall opacity; hover raises incident edges to full opacity and the selected colour.
The fill-only opacity of an untagged compound leaves its border and label opaque.
Tinting does not itself guarantee accessible text contrast; validate the resolved foreground and fill.

There are separate background layers.
The page uses `themes.<mode>.bg` through `--rd-bg`; diagram panels use `themes.<mode>.surface` through `--rd-surface`.
The Mermaid SVG and Cytoscape canvas are transparent, revealing that panel.
Category tints nevertheless mix against the **page background**, so their flat fill can differ from the panel underneath.
Mermaid's edge-label background also uses the page background.

The showcase has no framework ThemeProvider.
Its controls set `<html data-brand>` and `<html data-theme>`; scoped CSS variables update the page immediately.
`render()` then recreates the Cytoscape instance and reinitialises Mermaid with `theme: "base"`, explicit theme variables and regenerated subgraph styles before rendering fresh SVGs.
The opening brand's `defaultTheme` sets the first mode; a later brand change keeps the current mode (ADR-032).
The ordinary document viewer persists mode in local storage and rerenders its blocks.
A design profile supplies baked Mermaid theme variables on the native `base` theme; legacy explicitly selected brandpacks retain their default/dark behavior.
The default profile comes from prebuilt `themes/osakanights/themes.css` with matching tokens.
Follow the vendored profile-driven theming guide for authored categories, five-shade families, nested boundaries, entity rows and sequence groups.

Panel corners follow `themes.<mode>.radius` through `--rd-radius`.
Profiles supply that value from `dimension.radius`, preserving its unit and zero; older profiles fall back to `12px`.
Cytoscape node corners independently use `canvas.cytoscape.<mode>.roundness`, with compounds adding 2px.
The current profile adapter supplies 8px for graph nodes; Mermaid node shapes retain their own geometry.
Theme radius propagation to diagram shapes is therefore still a separate mapping decision.

#### Tagged compounds and portable Markdown

A Cytoscape node becomes a compound when another node names its ID in `data.parent`.
It is tagged when its own `data.category` field exists, which matches `:parent[category]`.
An absent field selects the untagged styling; an empty or unknown category still matches the tagged selector but falls back to neutral compound colours.
Category tags are explicit and are not inherited by children.

Mermaid's equivalent of a compound is a `subgraph` with an explicit ID.
For portable Markdown, put each group's `style groupId ...` directive inside the Mermaid fence rather than relying on page CSS or a JavaScript provider.
Use an opaque category stroke, a low-alpha eight-digit hex fill, and leave label colour to the host theme.
For example, `style boundary fill:#ffc00029,stroke:#ffc000,stroke-width:2px` gives approximately 16% fill opacity without fading the text or border.
Avoid setting whole-group `opacity`.
This is a portable syntax recipe, not a guarantee of identical rendering or adequate contrast on every host.

For deeper nesting, keep hue tied to category identity, not depth.
The simplest bounded recipe tints only the outer category boundary; inner structural groups use `fill:transparent` and a dashed border, keeping their labels host-controlled.
Reusing a 16% translucent fill at every level compounds: the effective same-colour opacity after `n` layers is `1 - 0.84^n`, reaching about 58% after five layers.
If every level needs a tint and the maximum depth is `D`, a uniform per-level alpha of `1 - (1 - A)^(1/D)` caps the combined same-colour tint at `A`.
Different nested hues also mix, so category borders and labels must retain their meaning independently of fill.
Neither recipe requires increasingly dark opaque bands as nesting grows.

GitHub controls its Mermaid renderer and version; do not depend on repository JavaScript, custom page CSS or access to the reader's mode.
Material for MkDocs integrates its own fonts, colours and theme changes; other MkDocs integrations need their own checks.
For exact profile colours in both modes, generate separate resolved light/dark diagrams or use a renderer you control.
Validate the actual GitHub and MkDocs outputs in both modes, including the deepest group and the contrast of category outlines.
See [GitHub's diagram support](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams), [Mermaid flowchart styling](https://mermaid.js.org/syntax/flowchart.html), and [Material's Mermaid integration](https://squidfunk.github.io/mkdocs-material/reference/diagrams/).

### Rules that keep brandpacks sane

- **One categorical palette (ADR-023).** `canvas.plotly.<mode>.series` is the
  only categorical palette. It colours chart series *and* diagram categories:
  a Cytoscape.js compound's `data.category`, a Mermaid subgraph, a draw.io icon.
  A category takes the next slot in a fixed order (a block's `categories` list,
  else first appearance), never cycles, and gets no colour past the last slot.
  There is no `categoryColours` map; `themecheck.py` rejects a pack that ships one.
  Status colours stay reserved and are never a slot.
- **WCAG AA (≥4.5:1)** for all fg/bg pairs in both themes. The default pack
  is pre-checked; verify any replacement.
- **`FALLBACK_TOKENS`** baked into the generated JS is a fetch-failure safety
  net that console.errors when used. It is not a place to customise.
- **Pre-paint theme bootstrap**: an inline `<head>` script resolves
  `localStorage` → `prefers-color-scheme` → light and stamps `data-theme`
  before first paint. Moving it to the external JS reintroduces the
  light-flash (FOUC).
