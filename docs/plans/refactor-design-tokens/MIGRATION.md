# Migration

Paths are relative to `skills/`.

**Status:** done, M0 to M6. The table below is the state the plan started from.

## Where things stood

| Consumer | Reads today |
|---|---|
| `richdocs` | its own `design-tokens.json` schema (`themes.{light,dark}`, `canvas.{cytoscape,plotly,deckgl}`, `categoryColours`, `status`, `fonts`, `defaultTheme`, `waivers`); lookup in `scripts/md2html.py` `theme_search_dirs`, `load_theme`, `resolve_brand`: `tmp/richdocs/theme/` then `resources/themes/` |
| `mermaidjs-diagrams` | no tokens: palettes are prose (`resources/color_theming.md`, `color_palette_recipes.md`); contrast via `@jpeakai/mermaidjs-lint` with host `--profile`; `scripts/render_mermaid.sh` passes mmdc's `-t`/`-b` only |
| `richdocs/vendor/mermaidjs-diagrams/` | a copy of upstream |

`prototype/pipeline.py` already produces seed → IR → per-mode DTCG plus a projection onto richdocs'
current schema (`project_richdocs()`). That projection is the stand-in this plan retires.

## Sequence

| # | Step | Depends on |
|---|---|---|
| M0 | Create `skills/design-profiles/` and add it to `plugins/composition.yaml` | — |
| M1 | Surface expansion into the IR | M0 |
| M2 | Promote the prototype to the real tool and store | M0 |
| M3 | Ship richdocs' built-in brands' exact-accent seeds as examples | M2 |
| M4 | `richdocs` reads a profile first, else its built-ins | M1, M2 |
| M5 | `mermaidjs-diagrams` reads a profile first, else its palettes; re-vendor into richdocs | M1, M2 |
| M6 | Retire the prototype's projection | M4, M5 |

### M0: the skill

`skills/design-profiles/` with `SKILL.md`, a `CLAUDE.md` maintainer guide, and `scripts/`. Register it
in `plugins/composition.yaml` under `jpai-essentials` and run `uv run scripts/sync_plugins.py`.

### M1: surface expansion

Move every surface from `project_richdocs()` into curation as IR groups (CURATION stage 6), so the
DTCG carries them and no skill computes one. The lineage Sankey's second stage then reads IR → DTCG.

### M2: the real tool and store

- Promote `curate_profile()`, `score_contrast()` and the build into `design-profiles/scripts/`,
  keeping the `argparse` subcommands. Drop the `hue-` prototype profiles.
- Build writes **one** resolver document per DT-DTCG-1, replacing the prototype's three
  `dtcg/*.json` files. Validate the output against the 2025.10 resolver schema in a test.
- Store: `.design-profiles/<name>/{seed.json, ir.json, design-tokens.json}`.
- One resolver for the five-tier cascade (DT-LOC-1) and `.default-profile`, plus the DTCG reader.
  Each consumer carries its **own copy**, never an import.

### M3: built-in brands

richdocs' built-in themes stay in richdocs, hand-authored and gated by `themecheck.py`.
`design-profiles` ships their exact-accent seeds (`pipeline.py init-seeds` produces them) as
examples, so any can be curated into a profile.

### M4: richdocs

- Profile lookup runs before `theme_search_dirs`/`load_theme`/`resolve_brand`. With no profile they
  run as today. The output says which was used.
- A profile maps on read onto richdocs' internal keys (`themes`/`canvas`/`status`): a rename with no
  design knowledge, so the viewer JS keeps its schema. `defaultTheme` comes from
  `modifiers.mode.default`.
- `categoryColours` takes the categorical slots in order (DT-CAT-1). `serious` and `critical` both
  read `color.text.danger`; the glyph distinguishes them.
- Fonts: a profile carries `font.family.{display,body,mono}` as DTCG `fontFamily` tokens plus an
  optional web-font stylesheet URL.
- `themecheck.py` never runs on a profile. Existing tests stay; new tests cover profile-first lookup
  and the mapping (`test_md2html.py`, `test_themecheck.py`, `test_showcase.py`).

### M5: mermaidjs-diagrams

- `render_mermaid.sh` passes the profile's `surface.mermaid` `themeVariables` as an mmdc config.
- Contrast linting gains `--design-profile <name>`, taking grounds from the profile's surfaces.
  `--profile` keeps meaning the host (GitHub, MkDocs); its hard-coded grounds remain the fallback.
- `color_theming.md` points at profiles; the prose palettes become examples, with per-role hue
  families replaced by sequential categorical slots (DT-CAT-1).
- Re-vendor wholesale into `richdocs/vendor/mermaidjs-diagrams/`.

### M6: retire the projection

Delete `project_richdocs()`; M4's on-read mapping replaces it.
