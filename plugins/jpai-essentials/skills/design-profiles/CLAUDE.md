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
| `scripts/profiles.py` | curation (seed → IR), contrast scoring, build (IR → DTCG), lineage, the live-generator entry point `generate()`, and the CLI |
| `scripts/profile_resolver.py` | the five-tier cascade, `.default-profile`, and the DTCG reader. **Copied byte-for-byte** into every consumer |
| `scripts/schemas/2025.10/resolver.json` | the DTCG resolver schema, a self-contained bundle, vendored for the build's validation test |
| `resources/examples/<brand>/seed.json` | richdocs' built-in brands as exact-accent seeds, with their fonts |

## Invariants

- **Curation is additive.** It imputes what is absent and never overwrites a stated
  value (DT-BUILD-1, DT-PROV-1). A role it does not know is kept.
- **Build has no design knowledge.** It serialises, aliases unedited surface keys to
  their role, and fails on an incomplete IR. Nothing is computed at load.
- **Every surface is in the IR.** A new rendering surface is a new block in
  `Curator.surfaces()`, never a computation in a consumer.
- **Scripts are stdlib-only** (Tier B). `jsonschema` is a test-time dependency only.
- **The resolver copies stay identical.** `tests/test_design_profile_copies.py` at the
  repo root fails when `richdocs/scripts/profile_resolver.py` drifts from this one,
  and checks the TypeScript port in `mermaidjs-diagrams` reads the same tokens.

## Changing the resolver

1. Edit `scripts/profile_resolver.py` here and run the gate.
2. Copy it over `skills/richdocs/scripts/profile_resolver.py`.
3. Port the change to `skills/mermaidjs-diagrams/scripts/design_profile.ts`, then
   re-vendor mermaidjs-diagrams into richdocs per its ADR-007.
4. Run `make ci` at the repo root.

## Changing the examples

The seeds state each richdocs brand's exact light and dark accents
(`exact_oklch`), its default mode, fonts and web-font stylesheet. When a richdocs
brand changes its accent, regenerate its seed with `init <brand> --accent` and copy
the font keys across. The repo-root test asserts every seed round-trips to its
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
