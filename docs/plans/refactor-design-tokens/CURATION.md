# Curation: seed → IR

Turns a few stated parameters into a semantically complete `ir.json`. Every stage is settled;
`skills/design-profiles/scripts/profiles.mjs` implements every stage.

Invariants: curation imputes what is absent and never overwrites what is stated (DT-BUILD-1,
DT-PROV-1). A stated value is final and unconstrained: a brand may choose green for `danger`.

## Stage 0: the seed

Optional. Only the brand hue is required. The full parameter set, each with its default and source,
is `DEFAULTS` in `skills/design-profiles/scripts/profiles.mjs`. A scraped brand usually states `brand.hue`, `brand.chroma`,
`brand.lightness`, plus `brand.dark.*` when its dark accent differs.

A preset seed instead holds the resolved registry snapshot under `preset`.
The JavaScript adapter decodes the string with `shadcn/preset` and resolves colors and fonts through `shadcn/registry`.
`shadcn_profile.mjs` maps these values to stated semantic roles before curation.
Hue and accent seeds state `radius` using the same nonnegative px/rem/zero input.
An optional `radius.dark` overrides dark mode; both emit the typed `dimension.radius` token.
It preserves original alpha and OKLCH coordinates for export.

Scrape heuristics: `background|bg|surface|canvas` → ground; `accent|brand|primary|cta|highlight` →
brand hue.

## Stage 1: neutral ramp (DT-REF-1)

```text
role                     dark L    hex     |  light L    hex
color.surface.sunken       0.10  #030303   |     0.92  #e4e4e4
color.surface              0.15  #0b0b0b   |     0.97  #f5f5f5
color.surface.raised       0.20  #161616   |     1.00  #ffffff   (clamped)
color.text.subtle          0.80  #bebebe   |     0.32  #333333
color.text                 1.00  #ffffff   |     0.07  #010101
```

Every pairing clears AAA. `color.text.subtlest` is the value nearest the ground that still reaches
4.5:1 on every ground (`target.text.subtlest`).

## Stage 2: borders (DT-BORDER-1)

- `color.border`: `color.text` at 0.14 alpha; 1.36 to 1.52:1 across grounds.
- `color.border.bold`: solved for 3:1 on every ground. Hardest ground is `surface.raised` in dark,
  `surface.sunken` in light. Resolves to dark `#636363`, light `#828282`.

## Stage 3: brand roles (DT-ACCENT-1, DT-WALK-2)

Produces `color.background.brand.bold`, `.subtlest`, `color.border.brand`, `color.text.inverse`,
`color.link`, and the selected/focus roles.

- A stated accent lightness is the brand fill verbatim in its mode.
- A hue-only seed takes the hue's in-gamut cusp, then solves lightness so inverse text reaches 7:1
  and the fill 3:1 on every ground.
- `color.link` solves to 4.5:1 and `color.border.brand` to 3:1, from the same accent.
- `color.background.brand.subtlest` is the fill at 16% over the surface, baked, not mixed at render.
- `offset.background.selected` defaults to 0.07 (M3's `secondaryContainer` sits 0.068 L from its
  surface).

## Stage 4: categorical roots and five-shade palettes (DT-CHART-1)

1. Default to ten roots, numbered `01` through `10`, with `360 / φ²` golden-angle hue steps.
2. Hue and accent profiles start from the mode's brand fill, retaining root lightness rather than solving chart marks to 3:1.
3. Reduce chroma only to fit sRGB; keep lightness and hue.
4. Scale the measured five-shade reference recipe to each categorical root, producing fifty palette colors.
5. Alias the default sequential ramp to palette `01`.

Equal hue angles are not equal perceptual steps; separation is uneven by nature.

For preset profiles, DT-PRESET-1 starts from each mode's original `chart-1`.
Each root gets five shades by transferring the source ramp's lightness, chroma, and shortest hue offsets.
Chroma-only gamut mapping fits each derived color to sRGB.
The source `chart-1` through `chart-5` remain separate from these generated palettes.
See the [preset reference](../../../skills/design-profiles/resources/shadcn-presets.md#expand-chart-colors-into-ten-palettes) for the formulas.
The same reference defines the scaled fallback recipe used when no imported five-shade ramp exists.
Chart contrast is reported, not guaranteed by the hue walk.
Retain full OKLCH coordinates in the IR and exports; round contrast reports only.

## Stage 5: status colours

Conventional hues, not walk slots, each solved to 4.5:1 on its ground:

| Role | OKLCH hue |
|---|---|
| `color.text.danger` | 25 |
| `color.text.warning` | 75 |
| `color.text.success` | 148 |
| chroma cap | 0.18 |

## Stage 6: surface expansion (DT-BUILD-1; MIGRATION M1)

Curation writes each surface into the IR as a group; build only serialises.

For preset profiles, the IR also includes font stylesheet URLs, imported shadcn colors, radius, and expanded chart palettes.
Build exports portable CSS and/or DTCG tokens from this complete IR.

| Group | Shape |
|---|---|
| `surface.cytoscape` | `{selector, style}[]`: node fill/border/label, edge, compound, selected |
| `surface.plotly` | layout + `colorway` + ramps |
| `surface.mermaid` | `themeVariables`, a flat hex object, alpha flattened |
| `surface.deckgl` | RGBA arrays |
| `surface.drawio` | container and stencil fill/stroke per shape class |
| `surface.css` | chrome custom properties |
| `surface.shadcn` | complete shadcn theme variables, with typed font and radius aliases |

No prior art exists for this in any charting or diagram library. Mermaid derives its palette from
`primaryColor` by hue rotation (`secondaryColor` at h −120, `tertiaryColor` at −160, `cScale1` =
secondary), so set every `themeVariables` key explicitly.

## Stage 7: scoring, not gating (DT-CONTRAST-1, DT-PROV-1)

`curate` scores every text-on-background pairing per mode against AA and writes the scores to the
IR's top-level `$extensions`. A miss is a `defect` only when both colours are imputed and no stated
parameter drove them; any other miss is a `choice`. `curate` exits non-zero on a defect. Hue-only
seeds every 15° round the wheel score zero defects.
