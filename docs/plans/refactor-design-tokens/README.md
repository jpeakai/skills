# Design-token refactor

Generate one design profile from a shadcn preset string and share it across rendering surfaces in light and dark.
Resolve its theme and fonts, expand its chart seed into ten five-shade palettes, and export CSS or DTCG tokens.
Hue and accent seeds remain available for offline authoring.

**Status:** the producer and consumers are implemented, including the preset adapter and chart expansion.
The [skill overview](../../../skills/design-profiles/README.md) shows the complete pipeline.
Implementation steps are in [MIGRATION.md](MIGRATION.md).

## Architecture

```text
  seed.json              ir.json                   design-tokens.json (DTCG)
  ─────────              ───────                   ────────────────────────
  OPTIONAL               the root artifact    ──▶   the ONLY file skills
  a few parameters  ──▶  semantically              read at runtime
  + one brand hue        complete: every
                         role, every surface,
                         light + dark
       │                      │                          │
   scrapeable             hand-editable              hand-editable
   from a website         iterate here               fine-tune here
                              │                          │
                     curation script              build script
                     imputes what is absent,      pure transform,
                     maximises WCAG               no design knowledge
```

Preset resolution precedes the seed and IR pipeline.
The saved seed contains resolved theme and font metadata, so curation and build remain offline.
Build writes `theme.css` with font loading and/or `design-tokens.json`.
Gates run at curation, never at load.
A stated value remains final.

## Files

| Path | Holds |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | Scoped decisions and the preset import contract. |
| [`CURATION.md`](CURATION.md) | Seed → IR, stage by stage, with defaults |
| [`MIGRATION.md`](MIGRATION.md) | The build sequence, M0 to M6 |
| [`review/pr25-design-profiles.md`](review/pr25-design-profiles.md) | The PR 25 review companion; [`.html`](review/pr25-design-profiles.html) is its self-contained render |
| [`reference/osakanights.design-tokens.json`](reference/osakanights.design-tokens.json) | The target `design-tokens.json` shape (DT-DTCG-1), built from osakanights before surfaces and fonts were added |

Run the preset workflow from the repository root:

```bash
bun install --cwd skills/design-profiles/scripts --frozen-lockfile
bun skills/design-profiles/scripts/shadcn.mjs b5cR4pgAc --name demo
```

## Role vocabulary (DT-ROLES-1)

```text
color.surface.sunken            color.text                  color.border
color.surface                   color.text.subtle           color.border.bold
color.surface.raised            color.text.subtlest         color.border.brand
                                color.text.inverse
color.background.brand.bold     color.link                  color.chart.categorical.1…12
color.background.brand.subtlest color.border.selected       color.border.focused
color.background.selected       color.text.selected
color.text.danger / .warning / .success
```

`accent` is retired as a role name.

All profiles default to ten categorical roots and `color.chart.palettes.<hue>.<shade>` for fifty expanded colors.
Hue indexes use `01` through `10`; shade indexes use `1` through `5`.
Existing profiles migrate their names and preserve stated edits when rebuilt.
The [preset reference](../../../skills/design-profiles/resources/shadcn-presets.md) defines formulas, outputs, and font loading.

## Ground rules

- **Never ask how categorical classes get colour.** Storage, Compute, Input, Process and every other
  class take sequential `color.chart.categorical.<N>` slots, for visual separation only (DT-CAT-1).
- **Source code shows the present, never intent.** A token's purpose is a question for the maintainer.
- **Research design-convention questions first.** The maintainer is an engineer, not a designer.
  Questions about the maintainer's own system and priorities go straight to the maintainer.
- **Ask decisions through `concise-decisions`.** A bare options list with no briefing gets rejected.
- **Measure, don't assert.** Every colour claim needs a computed number behind it.
