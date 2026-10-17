# Design-token refactor

One design-token architecture shared by `skills/richdocs/` and `skills/mermaidjs-diagrams/`, so a
brand profile is curated once and paints every surface they render: chrome CSS, Cytoscape, Plotly,
Mermaid, deck.gl and draw.io, in light and dark.

**Status:** implemented. M0 to M6 in [`MIGRATION.md`](MIGRATION.md) are done: the
producer is [`skills/design-profiles/`](../../../skills/design-profiles/), and `richdocs`
and `mermaidjs-diagrams` read its profiles first.

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

Three artifacts, two transforms. Gates run at curation, never at load. A stated value is final;
rules only impute what a profile does not state.

## Files

| Path | Holds |
|---|---|
| [`DECISIONS.md`](DECISIONS.md) | The fifteen decisions. **Canonical.** |
| [`CURATION.md`](CURATION.md) | Seed → IR, stage by stage, with defaults |
| [`MIGRATION.md`](MIGRATION.md) | The build sequence, M0 to M6 |
| [`reference/osakanights.design-tokens.json`](reference/osakanights.design-tokens.json) | The target `design-tokens.json` shape (DT-DTCG-1), built from osakanights before surfaces and fonts were added |

The prototype spike was promoted into `skills/design-profiles/scripts/profiles.py` (M2)
and retired with its richdocs projection (M6); it remains in git history. Run the tool
from the repo root:

```bash
uv run --no-project skills/design-profiles/scripts/profiles.py init acme --example osakanights
uv run --no-project skills/design-profiles/scripts/profiles.py all acme
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

## Ground rules

- **Never ask how categorical classes get colour.** Storage, Compute, Input, Process and every other
  class take sequential `color.chart.categorical.<N>` slots, for visual separation only (DT-CAT-1).
- **Source code shows the present, never intent.** A token's purpose is a question for the maintainer.
- **Research design-convention questions first.** The maintainer is an engineer, not a designer.
  Questions about the maintainer's own system and priorities go straight to the maintainer.
- **Ask decisions through `concise-decisions`.** A bare options list with no briefing gets rejected.
- **Measure, don't assert.** Every colour claim needs a computed number behind it.
