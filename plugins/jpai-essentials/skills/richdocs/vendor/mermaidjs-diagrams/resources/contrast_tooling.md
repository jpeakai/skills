# Contrast Tooling Surface

The contrast surface of the two tools this skill uses: the published lint that
gates every diagram, sequence diagrams included, and the ad-hoc pair
calculator. The *mandate* to run them lives in `mermaidjs-diagrams.md` ("Required for
every diagram"); this file is the reference you open when the recipe there
isn't enough. The conceptual palette rules live in `color_theming.md`.

## Two complementary tools

| Tool | Scope | Use when |
|------|-------|---------|
| [`@jpeakai/mermaidjs-lint`](https://jpeakai.github.io/jpai-mermaidjs-lint/) | Audits every `classDef`/`style` directive inside `.mmd`/`.md` files (text on fill at AA 4.5:1, border on fill at 3:1, read the way the host renders it), and every `sequenceDiagram`'s theme colours in light and dark | Gating every diagram before it lands in docs |
| `scripts/color_contrast.ts` | Generic WCAG + APCA calculator for any two CSS colours (hex, rgb, oklch, named, etc.), with alpha compositing | Ad-hoc pair checks, e.g. sampling colours from a screenshot, comparing theme tokens, or scoring a sequence colour against a host page the lint does not model |

The lint replaced the skill's own complexity and contrast scripts, the
sequence-diagram audit last of all. The calculator stays because the lint
scores colours inside diagrams and has no command for an arbitrary pair.

## Contrast rules

| Rule | Fires when | `--fix` |
|------|-----------|---------|
| `contrast-text-below-aa` | Label text is below 4.5:1 against its background | Yes, when a safe colour exists |
| `contrast-border-below-ui-minimum` | A border, line or arrow is below 3:1 against its background | No |
| `contrast-directive-unauditable` | A directive's or a sequence config's contrast cannot be audited | No |

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

## Sequence diagrams

A `sequenceDiagram` has no style lines; its colours are theme variables. The
lint reads YAML frontmatter and `%%{init}%%` directives with Mermaid's own
parser, resolves every inherited variable with Mermaid's own theme engine, and
scores both themes. Under `github` it scores participant labels and borders,
human actor names and stick figures against the page, lifelines, page-backed
message text and arrows, notes, frame keywords and descriptions, activation
bars, `autonumber` numbers, and messages inside a `rect`. A theme the config
pins applies to both canvases, so `theme: base` cannot hide a dark-mode
failure. Under `mkdocs-material` only lifelines, arrowheads and activation bars
keep the diagram's colours, so only those are scored, as advisory borders.

Sequence SVGs are transparent, and a `themeVariables.background` paints
nothing. Page-backed colours are scored against GitHub's page, `#ffffff` in
light and `#0d1117` in dark. The lint has no flag for another host's page
colours, so on a branded surface score the page-backed variables
(`signalTextColor`, `signalColor`, `loopTextColor`, `actorLineColor`, and
`actorTextColor` for a human `actor`) against each surface with the calculator.

A config the lint cannot model is reported as `contrast-directive-unauditable`,
which blocks like any finding: a `themeCSS` override, a theme other than
`base`, `default`, `dark`, `forest` or `neutral`, or a colour Mermaid cannot
read. Mermaid's own `dark` theme draws note text at 4.49:1, so a note with no
colours set fails in dark; set `noteBkgColor` and `noteTextColor` to one
readable pair.

Keep `signalColor`, `signalTextColor`, and `loopTextColor` theme-adaptive by
default. An explicit colour that reads on a white page can vanish on a dark
surface even when actor and note labels pass. Inspect both rendered themes
after the gate.

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

# Batch pairs via stdin, e.g. sequence message colours on a branded surface
echo '[["#475569","#1a1a1a"],["#475569","#fafafa"]]' | bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts --stdin --json
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
