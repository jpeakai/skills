# Slopstopper and contrast tooling

## One mandatory lint command

```bash
bunx @jpeakai/remark-lint-slopstopper SOURCE.md
bunx @jpeakai/remark-lint-slopstopper --json docs/
bunx @jpeakai/remark-lint-slopstopper --mermaid-only SOURCE.md
bunx @jpeakai/remark-lint-slopstopper --preset low-density SOURCE.md
```

The standalone wrapper enables recommended remark-lint rules plus all custom prose and Mermaid policies.
The package root is a recommended remark preset; custom policies live at its `/remark` entry point.
Using the root preset alone does not enable those custom policies.
The CLI already loads them, so no separate remark CLI is needed.

Inputs are Markdown files, directories, quoted globs or standard input.
Wrap a standalone `.mmd` diagram in a Mermaid fence before linting it.
`--mermaid-only` and `--prose-only` retain recommended Markdown structure checks.
`--fix` applies verified prose edits; it does not repair diagrams.
Review edits and fix remaining findings manually.

JSON output is an object with a `files` array; each file contains `path`, `fixes` and `messages`.
Exit 0 is clean, 1 means findings remain, and 2 means an argument, configuration, input or processing error.

## Profile selection

Use the active design profile, otherwise the prebuilt `resources/themes/osakanights/themes.css` and matching tokens.
Read the [theming guide](color_theming.md) before choosing categories, shades, compound fills or sequence colors.

## Canvas configuration

The CLI uses GitHub's light and dark canvases by default.
For a profile-backed companion, install the skill's locked dependencies and emit native remark configuration:

```bash
bun install --cwd .claude/skills/mermaidjs-diagrams/scripts --frozen-lockfile
mkdir -p tmp/diagrams
bun run .claude/skills/mermaidjs-diagrams/scripts/design_profile.ts lint-config --design-profile NAME > tmp/diagrams/lint-config.json
bunx @jpeakai/remark-lint-slopstopper SOURCE.md --config tmp/diagrams/lint-config.json
```

Omit `--design-profile` to use the project default or prebuilt fallback.
The JSON config references the installed plugin and sets `options.canvas.light` and `options.canvas.dark`.
Keep the config local to the current installation because its plugin path is absolute.
The compiler resolves colors from source and configured canvases; external renderer config does not rewrite the source being audited.

Slopstopper 0.1.2 has no `--profile`, `--canvas-light` or `--canvas-dark` flags.
It does not auto-detect MkDocs or certify host-forced foregrounds and border contrast.
Its Mermaid policies check parseability, modeled text contrast and visual complexity.
Unsupported theme CSS or other unmodeled styling is a blocking diagnostic.

## Extra measurements and visual verification

The retained calculator converts supported CSS colors and checks explicit pairs; it is not another diagram linter.

```bash
bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts "#ffffff" "oklch(0.45 0.131 295.044)" --json
bun run .claude/skills/mermaidjs-diagrams/scripts/color_contrast.ts "#36464e" "#1d4ed836" --over "#ffffff"
```

Use profile-resolved values for actual diagrams rather than copying these calculator inputs as a palette.
Verify borders, host overrides, entity-row alternation, sequence groups and label clipping in both rendered modes.
Keep inspection PNGs in ignored scratch storage and publish native Mermaid fences.

See the upstream [CLI reference](https://github.com/jpeakai/remark-lint-slopstopper/blob/main/docs/cli.md) and [rule reference](https://github.com/jpeakai/remark-lint-slopstopper/blob/main/RULES.md).
