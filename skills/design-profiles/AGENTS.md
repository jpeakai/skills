# design-profiles: maintainer guide

The only producer of design profiles. `richdocs` and `mermaidjs-diagrams` consume them.
The decisions this skill implements are DT-* in the design-token refactor plan
(`docs/plans/refactor-design-tokens/DECISIONS.md` at the repo root). Read them before
changing a rule. Dev loop:

```bash
make -C skills/design-profiles/scripts fix   # mutate: format + lint-fix
make -C skills/design-profiles/scripts ci    # gate: must exit 0 before handoff
```

## File map

| File | Role |
|------|------|
| `SKILL.md` | agent operating manual: route by intent, commands, rules |
| `scripts/profiles.mjs` | curation (seed → IR), contrast scoring, build (IR → DTCG), lineage, the live-generator entry point `generate()`, and the CLI |
| `scripts/profile_resolver.mjs` | the five-tier cascade, `.default-profile`, and the canonical DTCG reader |
| `scripts/shadcn.mjs` | optional network adapter using public `shadcn/preset` and `shadcn/registry` APIs |
| `scripts/shadcn_profile.mjs` | offline preset curation, ten-by-five chart expansion, and CSS serialisation |
| `scripts/schemas/2025.10/resolver.json` | the DTCG resolver schema, a self-contained bundle, vendored for the build's validation test |
| `resources/examples/<brand>/seed.json` | richdocs' built-in brands as exact-accent seeds, with their fonts |

## Invariants

- **Curation is additive.** It imputes what is absent and never overwrites a stated
  value (DT-BUILD-1, DT-PROV-1). A role it does not know is kept.
- **Build has no design knowledge.** It serialises, aliases unedited surface keys to
  their role, and fails on an incomplete IR. Nothing is computed at load.
- **Keep full color precision.** Store complete OKLCH coordinates in the IR;
  rounding them before export can change an RGB channel and force hex fallback.
- **All profiles have expanded charts.** The default is ten padded categorical
  roots with five shades each; preset imports retain their supplied ramp offsets,
  while other seeds use the scaled five-shade reference recipe.
- **Every surface is in the IR.** A new rendering surface is a new block in
  `Curator.surfaces()`, never a computation in a consumer.
- **CSS exports are shadcn supersets.** `surface.shadcn` records the compatible
  variable projections and their dependencies. Preserve supplied preset values;
  font and radius projections must retain their DTCG types.
- **Runtime modules use Node.js standard APIs** and also run under Bun.
  Only preset resolution imports shadcn and uses the network.
  Saved seeds and IR rebuild offline without Python, `uv`, or installed packages.
  Ajv, Bun and TypeScript are development dependencies for schema tests and gates.
- **Imported preset values stay stated.** Preserve source colors, alpha, font families and radius.
  Expand each mode's chart ramp separately; do not infer charts from the primary brand accent.
  The chart expansion transfers the source ramp's offsets, not an upstream shadcn formula.
- **Example radii stay explicit.** `radius` and optional `radius.dark` use the same
  px/rem/zero parser as preset radii and emit `dimension.radius` plus CSS `--radius`.
- **Consumer readers agree on resolved values.** `tests/test_design_profile_copies.py`
  checks Richdocs' Python compatibility reader and Mermaid's TypeScript reader against
  the canonical JavaScript reader and generated fixture profiles.

## Changing the resolver

1. Edit `scripts/profile_resolver.mjs` here and run the gate.
2. Apply the same behavior to `skills/richdocs/scripts/profile_resolver.py`.
3. Port the change to `skills/mermaidjs-diagrams/scripts/design_profile.ts`, then
   re-vendor mermaidjs-diagrams into richdocs per its ADR-007.
4. Run `make ci` at the repo root.

## Changing the examples

The seeds state each richdocs brand's exact light and dark accents
(`exact_oklch`), its default mode, fonts and web-font stylesheet. When a richdocs
brand changes its accent, regenerate its seed with `init <brand> --accent` and copy
the font and radius keys across. The repo-root test asserts every seed round-trips to its
brand's accent hex.

## Known gotchas

- **Symptom: a profile's dark surfaces are all `#000000`** — a base lightness was
  carried over from HSL. HSL 5% grey is about OKLCH 0.16; bases do not transfer
  between spaces, increments do (DT-REF-1).
- **Symptom: a mermaid diagram shows an off-brand colour** — a `themeVariables` key
  was left out. Mermaid derives missing keys by hue rotation from `primaryColor`, so
  `surface.mermaid` sets every key explicitly.
- **Symptom: a hand edit vanished after `curate`** — it equalled what the rule derived,
  so it was not an edit. Change the seed parameter instead.
