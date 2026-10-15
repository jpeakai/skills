# Contrast Tooling Surface

The contrast surface of the two tools this skill uses: the published lint that
gates every diagram, and the ad-hoc pair calculator the skill still ships. The
*mandate* to run the lint lives in `mermaidjs-diagrams.md` ("Required for every diagram");
this file is the reference you open when the recipe there isn't enough. The
conceptual palette rules live in `color_theming.md`.

## Two complementary tools

| Tool | Scope | Use when |
|------|-------|---------|
| [`@jpeakai/mermaidjs-lint`](https://jpeakai.github.io/jpai-mermaidjs-lint/) | Audits every `classDef`/`style` directive inside `.mmd`/`.md` files: text on fill at AA 4.5:1 and border on fill at 3:1, read the way the host renders it | Gating every diagram before it lands in docs |
| `scripts/color_contrast.ts` | Generic WCAG + APCA calculator for any two CSS colours (hex, rgb, oklch, named, etc.), with alpha compositing | Ad-hoc pair checks, e.g. sampling colours from a screenshot or comparing theme tokens |

The lint replaced the skill's own `mermaid_contrast.ts` and
`mermaid_complexity.ts`, which are deprecated. The calculator stays because the
lint scores directives inside diagrams and has no command for an arbitrary pair.

## Contrast rules

| Rule | Fires when | `--fix` |
|------|-----------|---------|
| `contrast-text-below-aa` | Label text is below 4.5:1 against its fill | Yes, when a safe colour exists |
| `contrast-border-below-ui-minimum` | A border is below 3:1 against its fill | No |
| `contrast-directive-unauditable` | A style directive's contrast cannot be audited | No |

Every rule, with a failing and a fixed example, is in the package's
[rules reference](https://jpeakai.github.io/jpai-mermaidjs-lint/).

## Profiles

`--profile auto|github|mkdocs-material` sets how contrast is read. `auto`, the
default, reads `mkdocs-material` when an ancestor directory holds `mkdocs.yml`,
else `github`.

- **github**: the author controls the text, so the declared `fill × color` and
  `fill × stroke` pairs are scored.
- **mkdocs-material**: the host theme forces the label text and ignores
  `color:`, so each fill is scored against the text the host renders, in both
  light and dark.
- **`erDiagram`** fences are scored against every row background an entity
  draws, in both themes. Mermaid paints a `fill` on even attribute rows only, and
  the odd rows keep a theme surface that flips with the reader.

## Invocations

```bash
# Audit every diagram in a directory tree (auto-detects mkdocs vs github)
bunx @jpeakai/mermaidjs-lint docs/
bunx @jpeakai/mermaidjs-lint docs/ --json
npx -y @jpeakai/mermaidjs-lint docs/                 # where bun is not installed

# Force a render context (see mermaidjs-diagrams.md "Required for every diagram")
bunx @jpeakai/mermaidjs-lint docs/ --profile mkdocs-material
bunx @jpeakai/mermaidjs-lint docs/ --profile github

# Apply the fixes the lint can prove safe, then report what remains
bunx @jpeakai/mermaidjs-lint docs/ --fix

# Ad-hoc pair
bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts "#ffffff" "#2563eb"
bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts "rgb(55 65 81)" "oklch(0.98 0 0)" --json

# Translucent fill: --over composites it onto the page bg first (resolve the box)
bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts "#36464e" "#1d4ed836" --over "#ffffff"

# Batch pairs via stdin
echo '[["#fff","#777"],["red","blue"]]' | bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts --stdin --json
```

## Exit semantics

The lint exits `0` with no findings, `1` when findings remain (or a plugin fails
to load), and `2` on usage error. `color_contrast.ts` exits `0` if every pair
passes its threshold, `1` if any pair fails, `2` on usage error. The non-zero
exit makes both drop-in suitable for `make ci`-style gates.

Unlike the renderer, these tools need no browser and no special execution
class. They keep working in the restricted environments described in
`render_troubleshooting.md`; the lint needs registry access the first time
`bunx` or `npx` fetches it. When a render is blocked, the lint is still the
proof that the diagram itself is sound.

## Calculator output fields

Per pair in `color_contrast.ts --json`:

- `ratio` — WCAG 2.x contrast ratio, 1.0 – 21.0, rounded to 2dp
- `rating` — pass tier (`AAA`, `AA`, `AA Large`, or `Fail`)
- `apca_lc` — signed APCA Lightness contrast (-108..+106), rounded to 1dp.
  APCA is the candidate algorithm for the WCAG 3 draft and scores dark-mode
  pairs more accurately than the ratio metric.
