# Decisions

Each entry gives the rule, the values it fixes, and the **unless** condition under which it stops
applying. Reopen a decision only when its unless holds.

---

## DT-LOC-1: one shared profile store

User-curated profiles live in one store every consumer reads; `{skill_name}` is not in the path.
Lookup cascades on miss:

```text
1  <project>/.design-profiles/<name>/          shared, project-local
2  ~/.design-profiles/<name>/                  shared, user-global
3  <project>/.{codex,claude}/skills/<skill>/resources/profile/<name>/
4  ~/.{codex,claude}/skills/<skill>/resources/profile/<name>/
5  <skill>'s own built-in fallback             always terminates
```

- `.default-profile` (a one-line file in `.design-profiles/`) resolves through the **same** cascade as
  an explicit name. A name that resolves nowhere fails loudly.
- One profile must satisfy both skills, so the schema is a superset; a surface ignores groups it
  does not use.
- **Unless** the two skills' needs diverge so far that one profile cannot serve both.

## DT-PIPE-1: seed → IR → DTCG; only the DTCG is read at runtime

1. Skills read only `design-tokens.json`. Never the seed or the IR.
2. The DTCG is fully regenerable from a valid IR.
3. A valid DTCG carries a value for every permutation. Nothing is computed at load.
4. No WCAG or CVD check runs when loading a DTCG. Editing it is the user's choice.
5. Gates run at curation, which maximises contrast pragmatically.
6. The seed exists so a brand scraped from a website can be extrapolated.
7. The IR and the DTCG are both hand-editable. The IR regenerates the DTCG; the DTCG regenerates nothing.

Override is editing the IR and rebuilding, or editing the DTCG. There is no patch layer.

## DT-BUILD-1: curation bakes every surface into the IR; build only serialises

- `ir.json` is semantically complete: every role, every surface (categorical walk, Cytoscape,
  Plotly, deck.gl, draw.io, Mermaid, CSS), light and dark.
- Build is a pure IR → DTCG transform with no design knowledge.
- `seed.json` is optional. A hand-authored `ir.json` is a valid profile.
- Store layout: `.design-profiles/<name>/{seed.json, ir.json, design-tokens.json}`.
- Curation is **idempotent and additive**: it imputes what is absent and never overwrites a stated
  value, so re-running it adds a new surface to an existing profile safely.
- **Unless** curation stops being additive, which would destroy hand edits.

## DT-CVD-1: CVD safety is a very low priority

Never raise it as an objection to a design choice. It may inform ordering; it never blocks.

## DT-REF-1: neutrals are pure greys, one reference per mode plus offsets, in OKLCH

Chroma 0, hue 0. For an achromatic colour `Y = L³`, so contrast is closed-form. Every parameter is an
optional seed input:

| Parameter | Default | Kind |
|---|---|---|
| `L-dark-bg` | **0.15** | dark reference (`color.surface`) |
| `L-light-bg` | **0.97** | light reference |
| `offset.surface.sunken` | −0.05 | absolute: darker in both modes |
| `offset.surface.raised` | +0.05 | absolute: lighter in both modes (clamps at 1.00) |
| `offset.text.subtle` | +0.65 | toward text: flips with mode |
| `offset.text` | +0.90 | toward text |

- Trap: HSL 5% grey is about OKLCH 0.16. At OKLCH 0.05 the dark surfaces round to `#000000` and
  collapse. Increments transfer between spaces; bases do not.
- **Unless** the target medium is not 8-bit sRGB.

## DT-ROLES-1: role names follow Atlassian's `foundation · property · modifier` grammar

The vocabulary in [`README.md`](README.md) is locked. Emphasis ladder:
`subtlest → subtle → (default) → bold → boldest`.

- DTCG forbids a group holding a value, so bare `color.text` serialises as `color.text.default`.
  Flattened CSS restores the bare name.
- `color.link` aliases the brand hue.
- Applies to the shared profile vocabulary. A consumer's internal fallback schema keeps its keys and
  maps profile roles onto them on read (DT-TOOL-1).
- **Unless** Atlassian drops the ladder; then only the modifier words move.

## DT-ACCENT-1: one required brand hue; the secondary drives interaction state

- The seed requires **one** brand hue. The secondary is imputed (brand hue at about 44% of its
  chroma, a seed parameter) and a stated secondary replaces it.
- The secondary drives `color.background.selected{,.hovered}`, `color.border.selected`,
  `color.text.selected`, and `color.border.focused` (an alias of `border.selected`, drawn with a
  `color.surface` gap). Lightness is always solved, so an override never costs contrast.
- It is **never** a categorical colour. The walk pins no slot.

## DT-WALK-1: the categorical walk ships 12 pre-computed slots

`color.chart.categorical.1…12`, golden angle 137.5° from the brand hue. The chroma-binding hue falls
inside the first seven slots, so 12 costs nothing over 7. Shipping 12 makes them available; it says
nothing about how many a document uses.

## DT-WALK-2: walk lightness is solved; chroma is one rule with a ceiling

- Lightness per slot and mode: nearest to the mode's brand accent lightness (`walk.lightness:
  "brand"`, a number overrides) that keeps 3:1 on every ground.
- `chroma(slot) = min(max in-gamut chroma at its L and H, walk.chromaCeiling)`.
  - `"floor"` (default): every slot takes the walk's gamut floor, a uniform walk.
  - `"seed"`: each hue up to the brand's chroma, truer to the brand.
  - a number: an explicit ceiling.
- Brand roles (`background.brand.*`, `border.brand`, `link`) follow the same rule: solved against
  their grounds, a stated value never pushed.

## DT-BORDER-1: `border` is a text tint; `border.bold` is opaque and solved

| Role | Job | Mechanism | Default |
|---|---|---|---|
| `color.border` | decorative divider, WCAG-exempt | the mode's `color.text` at alpha | `alpha.border` 0.14 |
| `color.border.bold` | functional boundary, 3:1 | opaque grey, nearest L reaching 3:1 on **every** ground | search starts at `offset.border.bold` 0.35 toward text |

- Every projection flattens alpha onto its ground: Mermaid 11.4.1 drops 8-digit hex for
  `primaryColor`, and draw.io carries alpha as a separate `opacity` style.
- **Unless** a surface cannot composite alpha; it then needs a baked opaque value per ground.

## DT-CAT-1: categorical classes take sequential categorical slots. Nothing else.

Any class (Storage, Compute, Network, Input, Process …) is assigned `color.chart.categorical.<N>` in
order. The only purpose is visual separation. No `color.diagram.<class>` role, no per-class hue, no
"meaning" analysis. **Never re-ask; unconditional.** Status colours are a separate channel and no
reason to reopen this.

## DT-CONTRAST-1: defaults maximise text contrast; a stated deviation is a choice

| Seed states | A WCAG miss is | Reported as |
|---|---|---|
| only a hue | a defect in the defaults | a failure, fixed in the defaults |
| any parameter that causes the miss | the user's choice | information, **never** a failure |

- Checked: every text role on every ground or fill it can sit on.
- "Maximise" means clearing the target within each role's tier, so `text.subtle` stays distinct
  from `text`. Stated values are never pushed.
- Mermaid contrast linting follows the same severity rule.
- Waiver mechanisms are unnecessary: a stated deviation never fails.

## DT-PROV-1: each IR value records what curation derived; a difference is a hand edit

Per role, per mode, under `$extensions["ai.jpeak.design-profiles"]`: `derived` (the rule's last
output) and `origin` (`imputed` or `stated`). On each run:

| Current value | Curation |
|---|---|
| equals `derived` | rederives it from the seed |
| differs, or is `stated` | marks it `stated`, keeps it, reports what the rule would give |
| absent | imputes it |

A stated value feeds everything derived after it. Delete a value (or its `origin`) to release it.
**Unless** the IR stops being hand-edited.

## DT-TOOL-1: curation is its own skill; consumers prefer its profiles, then fall back

- **`skills/design-profiles/`** is the only producer: seed → IR → DTCG, contrast scoring, lineage,
  live generator. It writes the shared store.
- `richdocs` and `mermaidjs-diagrams` look for a profile first. With none, each keeps its current
  behaviour (richdocs' built-in themes, mermaidjs-diagrams' prose palettes and host grounds) and says
  which it used.
- Consumers know the store and the skill's **name**, never its code. Each carries its own copy of the
  profile resolver and DTCG reader.
- `themecheck.py` keeps gating richdocs' built-in themes and never runs on a profile.
- richdocs' built-in brands stay as its fallback. `design-profiles` ships their exact-accent seeds as
  examples.
- `cli` and other `design-tokens.json` readers are out of scope.
- **Unless** a consumer cannot work without a profile; then delete its fallback.

## DT-DTCG-1: `design-tokens.json` is a DTCG 2025.10 resolver document, both modes inline

- Schema: `https://www.designtokens.org/schemas/2025.10/resolver.json`.
- `modifiers.mode.contexts.{light,dark}` each hold one coherent token tree; `modifiers.mode.default`
  names the default mode; `resolutionOrder: [{"$ref": "#/modifiers/mode"}]`.
- Aliases are mode-agnostic (`{color.border.selected}`), never prefixed.
- `$extensions["ai.jpeak.design-profiles"]` sits on `modifiers.mode`. The resolver schema forbids it
  at the root.
- Reader: pick the context by mode, merge its list, resolve aliases. About 10 lines.
- Target shape: [`reference/osakanights.design-tokens.json`](reference/osakanights.design-tokens.json).
- Rejected: a format document with `light`/`dark` groups (no mode semantics, prefixed aliases).
- **Unless** no DTCG tool ever reads the file and a bare dictionary lookup is all a consumer needs.

## DT-PRESET-1: one shadcn code resolves a complete profile input

Use the public `shadcn/preset` decoder and `shadcn/registry` APIs through an optional JavaScript adapter.
The decoder selects options; registry data supplies actual CSS values and font metadata.
Save that resolved data in the seed so Python curation and rebuilds remain offline.
Preserve supplied colors, alpha, font families, and radius as stated values.

For preset profiles, this specialises DT-ACCENT-1, DT-WALK-1, and DT-WALK-2:

- Chart expansion starts from each mode's original `chart-1`, independently of the primary brand accent.
- Compute ten hue roots with `360 / φ²` golden-angle steps.
- Transfer the resolved five-shade ramp's lightness, chroma, and shortest signed hue offsets to every root.
- Reduce only chroma to fit sRGB; keep lightness and hue.
- Keep original shadcn chart tokens separate from generated categorical and sequential palettes.
- Record contrast without claiming that golden-angle spacing guarantees WCAG or color-vision thresholds.

This expansion is a profile generator rule, not an upstream shadcn derivation.
Hue and accent seeds retain their existing offline rules and twelve-slot walk.
Build remains a pure IR serialisation, with CSS, DTCG, or both as output choices.
CSS carries font loading; DTCG carries font-family tokens and stylesheet URLs.
Consumers read baked values without fetching a preset or generating colors at load.

- **Because** a reusable preset string should supply the whole design, including charts and typography, without repeated manual setup.
- **Unless** the preset format or public APIs stop exposing the theme and font data needed for a complete saved snapshot.

## DT-NUM-1: preset hue indexes use two digits

Generated preset categorical and palette hue indexes use `01` through `10` in IR, DTCG, CSS, selectors, and contrast reports.
Shade indexes remain `1` through `5`, matching the original shadcn chart slots.
Normalising older preset profiles updates names and aliases without discarding stated values.
Legacy hue and accent profile names remain compatible with existing consumers.

- **Because** fixed-width hue indexes preserve lexical ordering and keep ten-palette references consistent.
- **Unless** the maintained palette count exceeds two-digit indexes.

## DT-RUNTIME-1: design-profile scripts are Node.js-compatible ES modules

The producer, canonical resolver, and preset expander are .mjs modules running under Node.js or Bun.
This supersedes DT-PRESET-1's Python runtime wording; the saved-input and offline-build contracts remain.
The network adapter calls the expander directly, with no Python or uv subprocess.
Saved profiles rebuild using Node.js standard APIs and no installed packages.
Keep curation, stated edits, chart numbering, fonts, radius, DTCG and CSS output behavior consistent across runtimes.
Consumer skills remain self-contained under DT-TOOL-1.
Python and TypeScript compatibility readers are checked for resolved-value agreement rather than byte identity.
Bun runs formatting, lint, strict JavaScript type checks, schema tests and coverage gates.

## DT-RADIUS-1: every seed supports explicit corner radius

Hue and accent seeds accept `radius` as a nonnegative px/rem CSS dimension, including zero.
An optional `radius.dark` overrides dark mode; otherwise both modes share `radius`.
The default is `12px` for inputs that omit it, preserving existing profile chrome.
Every shipped example states the corresponding built-in theme's radius explicitly.
Preset snapshots use the same parser with their registry CSS values.
Curate this input as `dimension.radius`; export it in DTCG and as CSS `--radius`.
Keep stated radius edits across rebuilds, preserving their unit and square corners.
Graph-specific corner geometry remains an independent consumer mapping.

## DT-PRECISION-1: retain complete OKLCH coordinates

Keep full floating-point coordinates through curation, aliases, CSS and DTCG export.
Do not quantise IR coordinates to four decimals: this can change a channel in the stored sRGB fallback.
Surface aliases carry their source coordinates; newly composited opaque colors receive coordinates during curation.
Build continues to serialise curated values and preserves a hex edit when its recorded coordinates are stale.
Round contrast reports for display, not the color data used to render.

## DT-CHART-1: every profile has categorical roots and five-shade palettes

This supersedes DT-PRESET-1's twelve-slot exception and DT-NUM-1's legacy naming exception for hue and accent profiles.
It also supersedes DT-WALK-1 and DT-WALK-2's default twelve slots, rounded angle, equal-chroma floor and per-slot contrast solving.
Default to ten categorical roots numbered `01` through `10`, with exact `360 / φ²` hue steps.
Hue and accent profiles start from each mode's brand fill and preserve its lightness, fitting sRGB by reducing chroma only.
For each root, scale the measured five-shade reference lightness/chroma ratios and apply its hue offsets.
The reference recipe is documented in the preset reference; it is our curation rule, not a formula provided by shadcn.
Preset imports retain their own supplied five-shade ramp and absolute offset transfer under DT-PRESET-1.
Both paths emit `color.chart.palettes.<hue>.<shade>`, default sequential aliases, CSS palette selectors, and adjacent contrast reports.
Explicit walk settings remain supported; preserve stated roots and shades through rebuilds.
Normalise older numeric hue names and aliases; retire surplus imputed chart slots without discarding stated edits.
Golden-angle spacing and shade construction do not guarantee a WCAG or color-vision threshold.

## DT-SHADCN-1: exported CSS is a superset of the shadcn theme-variable contract

Every profile supplies shadcn's background/foreground pairs, actions, borders, inputs, focus rings, five chart slots, sidebar tokens and radius in both modes.
The CSS also retains font loading, expanded chart palettes and profile chrome variables.
Curate the projections under `surface.shadcn`; preserve imported preset values and unknown supplied variables.
Fallback mappings use existing semantic roles, with the default sequential palette supplying `chart-1` through `chart-5`.
Reserve `--accent` for shadcn interaction styling and `--border` for the shadcn border; prefix colliding legacy chrome variables with `profile-`.
Font and radius aliases carry explicit DTCG types, overriding the surface group's inherited color type.
Record projection dependencies so lineage includes the `surface.shadcn` group and traces fonts, radius and chart inputs.
CSS build resolves recorded aliases without inventing design values; older incomplete IR must be curated before CSS export.
The compatibility contract covers theme variables, not framework-specific Tailwind imports or directives.

## DT-CONSUMER-1: consumers ship a compiled profile fallback

This supersedes DT-TOOL-1's independently authored fallback palettes for Mermaid and default Richdocs output.
Resolve a requested or project-default profile first, preserving explicit Richdocs theme and token selections.
Otherwise consume the prebuilt OsakaNights profile under each skill's `resources/themes/osakanights/` directory.
Generate `themes.css` and matching DTCG tokens together through the design-profiles CLI during `make fix`.
Consumers read baked values and delegate curation to design-profiles where available.
Keep runtime readers self-contained and verify prebuilt artifacts against producer output.
Preserve Richdocs' explicit brand themes and original showcase.
