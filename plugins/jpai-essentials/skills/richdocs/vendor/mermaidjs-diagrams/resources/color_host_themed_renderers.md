# Host-themed diagram rendering

Use the active design profile or the prebuilt `resources/themes/osakanights/themes.css` fallback.
Follow [profile-driven theming](color_theming.md) for category and shade assignments.

## Host styles can override source styles

Material for MkDocs can control Mermaid label colors through its own CSS variables.
A foreground that reads on a fixed fill in plain Mermaid may become unreadable when a host overrides it.
Inspect the actual host in light and dark modes instead of assuming source `color:` wins.
The chosen theme supplies the palette; the host determines the surfaces and CSS precedence to verify.

## Resolve per-mode styling

Resolve category tints against the visible canvas and check them against their immediate parents.
Choose foregrounds and same-family border shades against the final composited fills.
For an HTML companion, feed the selected mode's tokens to the renderer and rerender Mermaid from its source on mode changes.
A fixed light tint does not reproduce the dark appearance.

GitHub fences cannot query a host CSS variable or select a different hard-coded palette when the host switches.
Keep fixed fills and foregrounds readable together on both canvases.
For deep nesting, use explicit opaque tints or transparent structural groups so fill opacity does not accumulate unchecked.

## Configure the available audit

Slopstopper 0.1.2 audits modeled Mermaid text contrast in both themes.
Its native remark plugin accepts `options.canvas: {light, dark}` for custom canvas colors.
It does not expose the retired `--profile mkdocs-material`, `--canvas-light` or `--canvas-dark` flags.
Canvas configuration does not model a host stylesheet that forces another foreground.
Do not claim a plain Mermaid audit certifies such host overrides or border contrast.

Use [the native CLI configuration](contrast_tooling.md) and inspect the final host rendering in both modes.
For an entity table, inspect the header, alternating rows, dividers and outer boundary without dropping attributes.
For sequences, inspect participant families and every surface occupied by messages, notes and frames.
Use the ad-hoc color converter or pair calculator for explicit foreground/fill and border/fill measurements.
