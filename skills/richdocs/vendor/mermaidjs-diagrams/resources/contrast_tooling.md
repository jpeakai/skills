# Contrast Tooling Surface

The full CLI surface of the two contrast tools — flags, output fields, and the
exit-code contract. The *mandate* to run them lives in `mermaidjs-diagrams.md` ("Required
for every diagram"); this file is the reference you open when the recipe there
isn't enough. The conceptual palette rules live in `color_theming.md`.

## Two complementary tools

| Script | Scope | Use when |
|--------|-------|---------|
| `scripts/mermaid_contrast.ts` | Audits every `classDef`/`style` directive inside `.mmd`/`.md` files — scores `fill × color` (text on fill) at AA ≥ 4.5:1 and `fill × stroke` (border on fill) at AA ≥ 3:1 | Catching low-contrast custom color palettes before they land in docs |
| `scripts/color_contrast.ts` | Generic WCAG + APCA calculator for any two CSS colors (hex, rgb, oklch, named, etc.) | Ad-hoc pair checks — e.g. sampling colors from a screenshot or comparing theme tokens |

Under the `github` profile an `erDiagram` fence is scored differently. Mermaid
paints its `fill` on even attribute rows only, so each label is scored against
the theme's odd row and against the fill composited over the theme's even row,
in both the `default` and `dark` Mermaid themes. Those pairs carry `theme` and
`row` (`odd`/`even`) in `--json` output. A missing `color:` is not a blocking
gap there, because the theme label is scored in its place.

`sequenceDiagram` fences resolve YAML frontmatter and JSON `init` directives
through Mermaid's theme calculation. Both light and dark passes score actor
labels/borders, lifelines, page-backed message labels/arrows, notes, loop labels
and frames, activation boxes, numbering, and `rect` backgrounds when present.
An explicitly pinned theme is kept on both canvases, so `theme: base` cannot
hide a dark-mode failure. Invalid colors and unsupported CSS overrides block
the gate instead of reporting a clean unaudited fence.

Sequence SVGs are transparent. A `themeVariables.background` value does not
paint the host background. Pass `--background-light COLOR` and
`--background-dark COLOR` for a custom host or branded diagram surface. These
flags affect sequence pairs only; other diagram models remain unchanged.
For a Richdocs theme, take these colors from its `themes.light.surface` and
`themes.dark.surface` tokens. Default canvases follow the selected profile.
Sequence JSON pairs have `directive_kind: "themeVariables"`, a variable
selector, source line, and `theme: "light"` or `"dark"`.

Keep `signalColor`, `signalTextColor`, and `loopTextColor` theme-adaptive by
default. An explicit color that reads on a white page can vanish on a dark
surface even when actor and note labels pass. Custom actor text can also change
inherited loop/label colors; the gate resolves those dependencies rather than
assuming unset colors are safe. Inspect both rendered themes after the gate.

## Invocations

```bash
# Audit every diagram in a directory tree (auto-detects mkdocs vs github)
bun run .claude/skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts docs/
bun run .claude/skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts docs/ --summary
bun run .claude/skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts docs/ --quiet     # failures only
bun run .claude/skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts docs/ --json
bun run .claude/skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts docs/ --color    # ANSI colour (default is plain text: the output is usually read by an agent or captured into a log)

# Force a render context (see SKILL.md "Required for every diagram")
bun run .claude/skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts docs/ --profile mkdocs-material
bun run .claude/skills/mermaidjs-diagrams/scripts/mermaid_contrast.ts docs/ --profile github

# Ad-hoc pair
bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts "#ffffff" "#2563eb"
bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts "rgb(55 65 81)" "oklch(0.98 0 0)" --json

# Translucent fill: --over composites it onto the page bg first (resolve the box)
bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts "#36464e" "#1d4ed836" --over "#ffffff"

# Batch pairs via stdin
echo '[["#fff","#777"],["red","blue"]]' | bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts --stdin --json
```

## Exit semantics

Both scripts: `0` if every pair passes its threshold (4.5:1 text, 3:1 border;
advisory border pairs under the `mkdocs-material` profile and in `erDiagram`
fences never fail), `1` if
any pair fails, `2` on usage error. The non-zero exit makes both tools drop-in
suitable for `make ci`-style gates.

Unlike the renderer, these tools need no browser, no package registry, and no
special execution class — they keep working in the restricted environments
described in `render_troubleshooting.md`. When a render is blocked, these gates
are still the proof that the diagram itself is sound.

## Output fields

Per pair in `color_contrast.ts --json`; per directive under `assessment` in
`mermaid_contrast.ts --json`, where the sibling `passes` (and `advisory`, when
set) are the fields that gate the exit code:

- `ratio` — WCAG 2.x contrast ratio, 1.0 – 21.0, rounded to 2dp
- `rating` — pass tier (`AAA`, `AA`, `AA Large`, or `Fail`)
- `apca_lc` — signed APCA Lightness contrast (-108..+106), rounded to 1dp.
  APCA is the candidate algorithm for the WCAG 3 draft and scores dark-mode
  pairs more accurately than the ratio metric.
