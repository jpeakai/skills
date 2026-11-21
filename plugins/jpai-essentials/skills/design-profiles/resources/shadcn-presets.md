# Generate a profile from a shadcn preset

Use one preset code to resolve a theme and its fonts, expand its chart palette, and export a reusable design profile.
The JavaScript adapter uses the public [shadcn APIs](https://ui.shadcn.com/docs/registry/api-reference#shadcnpreset).
The import subpath is `shadcn/preset`, singular.

## Generate CSS and design tokens

Run from the repository root with Node.js or Bun installed:

```bash
bun install --cwd skills/design-profiles/scripts --frozen-lockfile
bun skills/design-profiles/scripts/shadcn.mjs b5cR4pgAc --name demo
```

The command writes a saved seed, editable IR, theme CSS, and DTCG tokens under `.design-profiles/demo/`.
Omit `--name` to use `preset-CODE`.
Installed skills use their own installation path in place of `skills/design-profiles`.

| Option | Behaviour |
|---|---|
| `--format both` | Export CSS and DTCG tokens; this is the default. |
| `--format css` | Export CSS, retaining the seed and IR for rebuilds. |
| `--format tokens` | Export DTCG tokens, retaining the seed and IR for rebuilds. |
| `--store DIR` | Use another shared profile store. |

Consumers that resolve shared profiles require the DTCG output.

The adapter rejects an existing profile with a different seed.
Use another name when resolving a changed preset.
For the same saved snapshot, regeneration preserves stated IR edits.
Editing a generated DTCG file does not change the IR or CSS.

## Resolve the complete design

The short code identifies option indexes, not CSS values or font files.
`shadcn/preset` decodes it; `shadcn/registry` resolves the theme and font registry items.
The adapter requests design data without installing application components.
Framework, component base, RTL, and monorepo settings are outside the preset code.

Each mode's supplied colors, alpha values, fonts, and radius remain stated inputs.
The profile stores original colors under `color.shadcn`, font stacks under `font.family`, and a typed `dimension.radius` token.
Semantic roles map those inputs onto the existing rendering surfaces.

Chrome variables that share a shadcn name use a `profile-` prefix in CSS, preserving the original shadcn value.
Every profile supplies the complete shadcn variable contract in both `:root` and `.dark`, including profiles created without a preset.
The compatibility target is the theme-variable block, not framework-specific Tailwind imports or directives.
Applications can retain their existing Tailwind token bridge as described in [shadcn theming](https://ui.shadcn.com/docs/theming).
The DTCG mode extension also carries the preset selection and `fontStylesheets` URLs.
Its `chartContrast` report records adjacent categorical and sequential contrast ratios for each mode using the sRGB hex fallbacks.

CSS imports the body and heading fonts from their Fontsource CDN stylesheets.
An inherited heading uses the body family.
Font files remain remote; bundle them separately for offline viewing.

### Fallback mappings for profiles without a preset

Mappings are curated under `surface.shadcn`, so CSS build only serialises them and lineage records their sources.
An imported `color.shadcn.<name>` takes precedence when available.

| Shadcn variables | Profile source |
| --- | --- |
| `background`, `foreground` | Page surface and text |
| `card`, `popover`, their foregrounds | Raised surface and text |
| `primary`, `primary-foreground` | Brand fill and inverse text |
| `secondary`, `secondary-foreground` | Selected fill and selected text |
| `muted`, `muted-foreground` | Sunken surface and subtle text |
| `accent`, `accent-foreground` | Hovered selected fill and selected text |
| `destructive`, `destructive-foreground` | Danger role and the better black/white foreground |
| `border` | Alpha border composited onto the page |
| `input`, `ring` | Bold border and focused border |
| `chart-1` through `chart-5` | Default five-shade sequential palette |
| `sidebar`, `sidebar-foreground` | Sunken surface and text |
| `sidebar-primary`, `sidebar-primary-foreground` | Brand fill and inverse text |
| `sidebar-accent`, `sidebar-accent-foreground` | Selected fill and selected text |
| `sidebar-border`, `sidebar-ring` | Border composited onto the sidebar, and focused border |
| `radius` | Typed `dimension.radius` |
| `font-sans`, `font-heading`, `font-mono` | Body, display and monospace families |

Each role exports once, under its shadcn name.
`--accent` is shadcn's hover and selection tint, never the brand fill; the brand fill is `--primary`.
Roles shadcn lacks export under their own extension names:

| Extension | Profile role | Meaning |
| --- | --- | --- |
| `link` | `color.link` | Brand-coloured text that is readable on the page |
| `faint-foreground` | `color.text.subtlest` | Text quieter than `muted-foreground` |
| `primary-subtle` | `color.background.brand.subtlest` | A faint brand tint behind content |
| `border-strong` | `color.border.bold` | A border that must stay visible, such as a diagram edge |
| `selected` | `color.background.selected` | The fill of a selected item |

Saved profiles that use the older `surface.css` names (`page`, `raised`, `accent`, `on-accent` and others) migrate when curated, keeping stated edits.
Font and radius projections carry explicit DTCG types rather than inheriting the surface group's color type.
The IR-to-surfaces lineage includes a `surface.shadcn` group, with dependencies for colors, charts, fonts and radius.

## Expand chart colors into ten palettes

Chart expansion uses each mode's original `chart-1` through `chart-5`, independently of the primary theme color.
For seed coordinates `(L₀, C₀, h₀)`, the golden angle is `g = 360 / φ²`, where `φ = (1 + √5) / 2`.
The ten categorical roots use `hᵢ = (h₀ + i × g) mod 360`, for `i = 0…9`.

Each original shade supplies its difference from the first shade:

```text
ΔLⱼ = Lⱼ − L₀
ΔCⱼ = Cⱼ − C₀
Δhⱼ = shortest signed angular difference from h₀ to hⱼ

Lᵢⱼ = L₀ + ΔLⱼ
Cᵢⱼ = max(0, C₀ + ΔCⱼ)
hᵢⱼ = (h₀ + i × g + Δhⱼ) mod 360
```

Reduce chroma when necessary to fit sRGB, preserving lightness and hue.
This offset transfer is the profile generator's rule; shadcn supplies the source values, not this expansion algorithm.
Equal hues across modes produce identical palettes only when the source coordinates also match.
Hue separation does not imply a WCAG contrast threshold or color-vision guarantee.
An achromatic chart seed remains achromatic; a hue rotation cannot create chroma from grey.

| Output | Tokens |
|---|---|
| Ten categorical roots | `color.chart.categorical.01` through `.10`; CSS `--categorical-01` through `--categorical-10`. |
| Ten five-shade ramps | `color.chart.palettes.<hue>.<shade>`; CSS `--palette-<hue>-<shade>`. |
| Default sequential ramp | `color.chart.sequential.1` through `.5`, aliasing the first expanded palette. |
| Original shadcn ramp | `color.shadcn.chart-1` through `color.shadcn.chart-5`; CSS `--chart-1` through `--chart-5`. |

Hue indexes are zero-padded `01` through `10`; shade indexes remain `1` through `5`.
Rebuilding older preset profiles updates hue names and aliases while preserving stated edits.
Use `data-chart-palette="03"` on a chart container to select the third expanded ramp through its familiar `--chart-1` to `--chart-5` variables.
Use categorical tokens to identify unordered groups and sequential tokens to encode ordered magnitude.

### Hue and accent profiles

Profiles without a preset also default to ten roots and five shades per root.
Each mode starts from its own brand fill; rotate hue by the golden angle while retaining lightness and reducing chroma only to fit sRGB.
The default root preserves the brand accent, including a yellow-first categorical scheme when the brand fill is yellow.

With no imported ramp, use this relative recipe, measured from the reference five-shade ramp:

| Shade | Lightness multiplier | Chroma multiplier | Hue offset |
| --- | --- | --- | --- |
| 1 | `1` | `1` | `0°` |
| 2 | `0.704 / 0.855` | `0.140 / 0.138` | `1.432°` |
| 3 | `0.600 / 0.855` | `0.118 / 0.138` | `3.633°` |
| 4 | `0.511 / 0.855` | `0.096 / 0.138` | `5.320°` |
| 5 | `0.437 / 0.855` | `0.078 / 0.138` | `7.145°` |

For each categorical root `(Lᵢ, Cᵢ, hᵢ)`, multiply lightness and chroma by the shade's factors, add its hue offset, then reduce chroma if required to fit sRGB.
Scaling lightness keeps the sequence within range even for a dark root.
This is a fallback profile recipe, not an upstream shadcn derivation.
Imported presets continue to use their own absolute per-mode offsets instead.
Both paths preserve complete OKLCH coordinates, report adjacent contrast, and export the same palette selectors.
Older unpadded hue names migrate on rebuild; surplus imputed slots retire, while stated edits remain held.

## Rebuild without the registry

After the first import, edit `ir.json` and rebuild from the saved snapshot:

```bash
node skills/design-profiles/scripts/profiles.mjs all demo
```

Curation preserves stated edits and computes rendering surfaces before build.
Build serialises existing IR values into both output formats without registry access or runtime color generation.
Existing hue, accent, and example seed commands remain available without JavaScript dependencies.
