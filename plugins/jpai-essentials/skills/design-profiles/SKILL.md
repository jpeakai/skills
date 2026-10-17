---
name: design-profiles
description: "Curate a brand design profile once and paint every surface with it: chrome CSS, Cytoscape, Plotly, Mermaid, deck.gl and draw.io, in light and dark. Turns a seed (as little as one brand hue, or a scraped accent hex) into a semantically complete IR, scores every text pairing against WCAG AA, and builds one DTCG 2025.10 design-tokens.json that richdocs and mermaidjs-diagrams read from the shared .design-profiles/ store. Use when asked to create, tune, rebuild or set a default brand profile, theme or design tokens. Stdlib Python, no network."
argument-hint: "[init <name> --hue H | --accent HEX | --example BRAND] | [curate|build|all|status|set-default] [name]"
user-invocable: true
---

# design-profiles: one brand, every surface

A profile is three files in a shared store. Only the last is read at runtime.

```text
.design-profiles/<name>/
  seed.json            optional: a few parameters and one brand hue
  ir.json              every role and every surface, light and dark (hand-editable)
  design-tokens.json   one DTCG 2025.10 resolver document (hand-editable, never regenerates anything)
```

`richdocs` and `mermaidjs-diagrams` look for a profile first and fall back to their
own built-in themes when there is none. They say which they used.

## Route by intent

| The user wants | Run |
|---|---|
| A profile from one brand hue | `init <name> --hue 295`, then `all <name>` |
| A profile from a brand's accent colour (scraped or given) | `init <name> --accent '#5c4295'`, then `all <name>` |
| One of the shipped brands as a starting point | `init <name> --example osakanights`, then `all <name>` |
| To tune a value | edit `ir.json`, then `all <name>` (the edit is held) |
| To change a parameter | edit `seed.json`, then `all <name>` |
| Every consumer to use a profile by default | `set-default <name>` |
| To see what exists and whether it is healthy | `status` |
| The provenance of every value as two Sankeys | `lineage <name>` |

Every command runs from the project root:

```bash
uv run --no-project .claude/skills/design-profiles/scripts/profiles.py <command> [name ...] [--store DIR | --user]
```

Example, a profile from one hue, made the default for every consumer:

```bash
uv run --no-project .claude/skills/design-profiles/scripts/profiles.py init acme --hue 200
uv run --no-project .claude/skills/design-profiles/scripts/profiles.py all acme
uv run --no-project .claude/skills/design-profiles/scripts/profiles.py set-default acme
```

`--store` defaults to `./.design-profiles`; `--user` uses `~/.design-profiles`.

## Commands

| Command | Does |
|---|---|
| `init <name> --hue H` | writes `seed.json` stating only the brand hue (OKLCH degrees) |
| `init <name> --accent HEX` | states the hex's exact OKLCH lightness, chroma and hue |
| `init <name> --example BRAND` | copies a shipped seed: `fernline`, `freshgreens`, `gandalf`, `locomotif`, `osakanights`, `v2ai` |
| `curate [name ...]` | `seed.json` → `ir.json`: imputes what is absent, keeps what is stated, scores contrast |
| `build [name ...]` | `ir.json` → `design-tokens.json`, a pure transform |
| `all [name ...]` | `curate` then `build` |
| `status [name ...]` | the store, the default profile, and each profile's files, contrast verdicts and staleness |
| `set-default <name>` | writes `.design-profiles/.default-profile` |
| `lineage [name ...]` | writes `tmp/design-profiles/<name>/lineage.json` (seed → IR, IR → surfaces) |

`curate` exits non-zero when a default caused a text pairing below AA. That is a
defect in this skill, not in the user's profile: report it.

## The seed

Only `brand.hue` is required. Everything else has a default with a cited source
(`DEFAULTS` in `scripts/profiles.py`). The parameters a scraped brand usually states:

```json
{
  "brand.hue": 295.044, "brand.chroma": 0.131, "brand.lightness": 0.45,
  "brand.dark.hue": 295.159, "brand.dark.chroma": 0.109, "brand.dark.lightness": 0.801,
  "mode.default": "dark",
  "font.body": "'Fira Sans', sans-serif",
  "font.stylesheet": "https://fonts.googleapis.com/css2?family=Fira+Sans"
}
```

Scrape heuristics: `background|bg|surface|canvas` → ground;
`accent|brand|primary|cta|highlight` → brand accent (use `init --accent`).

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

```text
color.surface.sunken            color.text                  color.border
color.surface                   color.text.subtle           color.border.bold
color.surface.raised            color.text.subtlest         color.border.brand
                                color.text.inverse
color.background.brand.bold     color.link                  color.chart.categorical.1…12
color.background.brand.subtlest color.border.selected       color.border.focused
color.background.selected       color.text.selected
color.text.danger / .warning / .success
font.family.display / .body / .mono
```

Surfaces, each baked by curation so no consumer computes one:
`surface.css`, `surface.cytoscape`, `surface.plotly`, `surface.mermaid`
(`themeVariables`), `surface.deckgl`, `surface.drawio`.

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
`scripts/profile_resolver.py`; each consumer carries its own copy.
