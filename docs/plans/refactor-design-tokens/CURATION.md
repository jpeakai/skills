# Curation: seed → IR

Turns a few stated parameters into a semantically complete `ir.json`. Every stage is settled;
`prototype/pipeline.py` implements stages 0 to 5 and 7. Stage 6 is MIGRATION M1.

Invariants: curation imputes what is absent and never overwrites what is stated (DT-BUILD-1,
DT-PROV-1). A stated value is final and unconstrained: a brand may choose green for `danger`.

## Stage 0: the seed

Optional. Only the brand hue is required. The full parameter set, each with its default and source,
is `DEFAULTS` in `prototype/pipeline.py`. A scraped brand usually states `brand.hue`, `brand.chroma`,
`brand.lightness`, plus `brand.dark.*` when its dark accent differs.

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

## Stage 4: categorical walk (DT-WALK-1, DT-WALK-2)

1. Slot 1 is the brand hue in OKLCH; each next slot adds 137.5°.
2. Solve lightness per slot and mode for 3:1 on every ground.
3. Chroma is `min(max in-gamut, walk.chromaCeiling)`. Gamut-map by reducing chroma, holding L and H.

Equal hue angles are not equal perceptual steps; separation is uneven by nature.

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

| Group | Shape |
|---|---|
| `surface.cytoscape` | `{selector, style}[]`: node fill/border/label, edge, compound, selected |
| `surface.plotly` | layout + `colorway` + ramps |
| `surface.mermaid` | `themeVariables`, a flat hex object, alpha flattened |
| `surface.deckgl` | RGBA arrays |
| `surface.drawio` | container and stencil fill/stroke per shape class |
| `surface.css` | chrome custom properties |

No prior art exists for this in any charting or diagram library. Mermaid derives its palette from
`primaryColor` by hue rotation (`secondaryColor` at h −120, `tertiaryColor` at −160, `cScale1` =
secondary), so set every `themeVariables` key explicitly.

## Stage 7: scoring, not gating (DT-CONTRAST-1, DT-PROV-1)

`curate` scores every text-on-background pairing per mode against AA and writes the scores to the
IR's top-level `$extensions`. A miss is a `defect` only when both colours are imputed and no stated
parameter drove them; any other miss is a `choice`. `curate` exits non-zero on a defect. Hue-only
seeds every 15° round the wheel score zero defects.
