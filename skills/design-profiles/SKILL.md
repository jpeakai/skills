---
name: design-profiles
description: "Generate a shared design profile from one shadcn preset code, a brand hue, or an accent color. Export theme.css with font loading and/or DTCG design-tokens.json, including light and dark modes, ten-by-five chart palettes, and baked rendering surfaces for richdocs and mermaidjs-diagrams. Use to create, tune, rebuild or select design profiles and design tokens. Preset imports require Bun or Node and network access; saved profiles rebuild offline under Node.js or Bun without Python."
argument-hint: "[preset CODE --name NAME --format css|tokens|both] | [init NAME --hue H | --primary HEX | --example BRAND] | [curate|build|all|status|set-default] [NAME]"
user-invocable: true
---

# design-profiles: one brand, every surface

A profile keeps editable inputs and generated outputs in one shared store.

```text
.design-profiles/<name>/
  seed.json            optional: a few parameters and one brand hue
  ir.json              every role and every surface, light and dark (hand-editable)
  design-tokens.json   one DTCG 2025.10 resolver document (hand-editable, never regenerates anything)
  theme.css            portable CSS, including font loading for preset profiles
```

`richdocs` and `mermaidjs-diagrams` look for a profile first and fall back to their
own built-in themes when there is none. They say which they used.

## Route by intent

| The user wants | Run |
|---|---|
| A profile from a shadcn preset code | `bun <skill>/scripts/shadcn.mjs CODE`; see [preset imports](resources/shadcn-presets.md) |
| A profile from one brand hue | `init <name> --hue 295`, then `all <name>` |
| A profile from a brand's primary colour (scraped or given) | `init <name> --primary '#5c4295'`, then `all <name>` |
| One of the shipped brands as a starting point | `init <name> --example osakanights`, then `all <name>` |
| To tune a value | edit `ir.json`, then `all <name>` (the edit is held) |
| To change a parameter | edit `seed.json`, then `all <name>` |
| Every consumer to use a profile by default | `set-default <name>` |
| To see what exists and whether it is healthy | `status` |
| The provenance of every value as two Sankeys | `lineage <name>` |

Every command runs from the project root:

```bash
node .claude/skills/design-profiles/scripts/profiles.mjs <command> [name ...] [--store DIR | --user]
```

Example, a profile from one hue, made the default for every consumer:

```bash
node .claude/skills/design-profiles/scripts/profiles.mjs init acme --hue 200 --radius 8px
node .claude/skills/design-profiles/scripts/profiles.mjs all acme
node .claude/skills/design-profiles/scripts/profiles.mjs set-default acme
```

`--store` defaults to `./.design-profiles`; `--user` uses `~/.design-profiles`.

## Commands

| Command | Does |
|---|---|
| `init <name> --hue H` | writes `seed.json` stating only the brand hue (OKLCH degrees) |
| `init <name> --primary HEX` | states the hex's exact OKLCH lightness, chroma and hue; `--accent` is a deprecated alias |
| `init <name> --example BRAND` | copies a shipped seed: `fernline`, `freshgreens`, `gandalf`, `locomotif`, `osakanights`, `v2ai` |
| `curate [name ...]` | `seed.json` → `ir.json`: imputes what is absent, keeps what is stated, scores contrast |
| `build [name ...]` | `ir.json` → `design-tokens.json` and `theme.css`, a pure transform |
| `all [name ...]` | `curate` then `build` |
| `status [name ...]` | the store, the default profile, and each profile's files, contrast verdicts and staleness |
| `set-default <name>` | writes `.design-profiles/.default-profile` |
| `lineage [name ...]` | writes `tmp/design-profiles/<name>/lineage.json` (seed → IR, IR → surfaces) |

`curate` exits non-zero when a default caused a text pairing below AA. That is a
defect in this skill, not in the user's profile: report it.

## One preset string

Install the adapter's dependencies once, then generate both output formats:

```bash
bun install --cwd .claude/skills/design-profiles/scripts --frozen-lockfile
bun .claude/skills/design-profiles/scripts/shadcn.mjs b5cR4pgAc --name demo
```

The default name is `preset-CODE` when `--name` is omitted.
Use `--format css`, `--format tokens`, or the default `--format both`.
The adapter uses `shadcn/preset` (singular) to decode and `shadcn/registry` to resolve CSS values and font metadata.
It installs no application components.
The saved seed includes the resolved snapshot, so later `curate`, `build`, and `all` commands need no network.
Read [preset imports](resources/shadcn-presets.md) for chart formulas, font loading, and output tokens.

## The seed

Hue and accent seeds require only `brand.hue`. Everything else has a default with a cited source
(`DEFAULTS` in `scripts/profiles.mjs`). Scraped inputs usually state brand accents, fonts, and radius.

`radius` states a nonnegative CSS corner radius in `px` or `rem`; `0` preserves square corners.
`radius.dark` optionally overrides the dark mode value.
`init --radius VALUE [--radius-dark VALUE]` writes these inputs to the seed.
All shipped examples state their theme's radius explicitly.
The resolved `dimension.radius` token and CSS `--radius` preserve the value and unit.

```json
{
  "brand.hue": 295.044, "brand.chroma": 0.131, "brand.lightness": 0.45,
  "brand.dark.hue": 295.159, "brand.dark.chroma": 0.109, "brand.dark.lightness": 0.801,
  "mode.default": "dark",
  "radius": "12px",
  "font.body": "'Fira Sans', sans-serif",
  "font.stylesheet": "https://fonts.googleapis.com/css2?family=Fira+Sans"
}
```

Scrape heuristics: `background|bg|surface|canvas` → ground;
`accent|brand|primary|cta|highlight` → brand primary colour (use `init --primary`).

## Rules

- **A stated value is final.** Curation never pushes it to pass contrast. A miss
  that a stated value causes is reported as a `choice`, never a failure.
- **Hand edits are held.** A value in `ir.json` that differs from what the rule
  derived is marked `stated`, kept, and fed into everything derived after it. Delete
  the value (or its `origin`) to release it.
- **Categorical classes take sequential slots.** Storage, Compute, Input and every
  other class take `color.chart.categorical.<N>` in order, for separation only.
  Never ask what colour a class should be.
- **Never compute a colour at load.** Consumers read `design-tokens.json` as is.
- **`themecheck.py` never runs on a profile.** It gates richdocs' built-in themes.

## Role vocabulary

The core tokens below use an Atlassian-style vocabulary and stay the source of truth.
Every surface a consumer reads speaks shadcn instead (DT-NAMES-1, root ADR-0004).

```text
color.surface.sunken            color.text                  color.border
color.surface                   color.text.subtle           color.border.bold
color.surface.raised            color.text.subtlest         color.border.brand
                                color.text.inverse
color.background.brand.bold     color.link                  color.chart.categorical.01…10
color.background.brand.subtlest color.border.selected       color.border.focused
color.background.selected       color.text.selected
color.text.danger / .warning / .success
font.family.display / .body / .mono
color.chart.palettes.01.1…10.5
```

Surfaces, each baked by curation so no consumer computes one:
`surface.css`, `surface.shadcn`, `surface.cytoscape`, `surface.plotly`, `surface.mermaid`
(`themeVariables`), `surface.deckgl`, `surface.drawio`.

`surface.shadcn` maps every profile onto shadcn's background/foreground, action, chart, sidebar, font and radius variables.
Imported preset values win over fallback mappings.
`surface.css` uses shadcn names wherever shadcn has the role (DT-NAMES-1).
Its extensions, which shadcn lacks, export under their own names: `--link`, `--faint-foreground`, `--primary-subtle`, `--border-strong` and `--selected`.
The IR records every projection as an alias or derived value, including typed font and radius aliases for DTCG and lineage.

## Finding a profile

A consumer resolves a name through five tiers, first hit wins:

```text
1  <project>/.design-profiles/<name>/
2  ~/.design-profiles/<name>/
3  <project>/.{codex,claude}/skills/<skill>/resources/profile/<name>/
4  ~/.{codex,claude}/skills/<skill>/resources/profile/<name>/
5  the consumer's own built-in fallback
```

With no name, `.default-profile` names one and it resolves the same way. A name
that resolves nowhere fails loudly. The resolver and reader are
`scripts/profile_resolver.mjs`; each consumer carries a compatible reader, checked against the canonical module.
