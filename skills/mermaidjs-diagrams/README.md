# mermaidjs-diagrams

Render and maintain Mermaid.JS diagrams with **visual-clarity enforcement**.

## Features

- **Render** `.md` files containing ```` ```mermaid ```` fences to PNG. Two
  variants by default, dark+transparent and default+white, because a diagram
  has to read on a dark host and a light host and one image cannot do both.
  Every artifact is verified as a decodable PNG: a renderer exiting 0 without
  writing an image is a failure, not a pass.
- **Self-triaging renders**: Chromium failures are classified (npm cache,
  missing browser, sandbox denial, network, diagram syntax, or unknown), the
  two mechanically remediable classes are retried once, and only one class
  ever means "edit the diagram."
- **One published lint for every gate (required, not optional)**: every
  diagram MUST derive its palette from `resources/color_theming.md` and pass
  [`@jpeakai/mermaidjs-lint`](https://jpeakai.github.io/jpai-mermaidjs-lint/).
  That one tested package guarantees every label reads in light and dark
  themes, every diagram parses with Mermaid's own parsers, visual complexity
  (node count, visual-complexity score, subgraph depth) is scored against
  cognitive-load thresholds, and extra rules plug in. `SKILL.md` "Why this is
  mandatory" carries the reasoning.
- **Ad-hoc pair checker**: `scripts/color_contrast.ts` scores any two CSS
  colours (hex, rgb, oklch, named), WCAG 2.x plus APCA Lc, and composites a
  translucent fill over a backdrop. The lint has no equivalent, so it stays.
- **Layout engines**: dagre, elk, tidy-tree and cose-bilkent (mindmap only),
  selectable per diagram via YAML frontmatter. `look: classic | handDrawn | neo`.
- **Icon packs**: Iconify (logos, mdi, cloud, saas) for `architecture-beta`;
  Font Awesome for flowcharts.

## How it fits together

```mermaid
flowchart LR
    subgraph author["Authoring"]
        fence["mermaid fence<br/>in .md"]:::ingressPrimary
        mmd[".mmd file"]:::ingressPrimary
    end

    subgraph gates["Mandatory Quality Gates"]
        palette["Palette<br/>from reference"]:::computePrimary
        complexity["mermaidjs-lint complexity<br/>nodes / VCS / depth"]:::computePrimary
        contrast["mermaidjs-lint contrast<br/>WCAG AA, light and dark"]:::computePrimary
    end

    subgraph optional["Optional Tooling"]
        layout["Layout engine<br/>dagre / elk / tidy-tree / cose-bilkent"]:::dataSecondary
        icons["Iconify packs<br/>logos / mdi / cloud / saas"]:::dataSecondary
        render["render_mermaid.sh<br/>PNG variants, verified"]:::dataPrimary
    end

    subgraph refs["Reference Docs"]
        rColor["color_theming.md"]:::infraSecondary
        rLayout["layout_algorithms.md"]:::infraSecondary
        rOrg["diagram_organization.md"]:::infraSecondary
    end

    fence --> palette
    mmd --> palette
    palette --> complexity
    palette --> contrast
    complexity -- pass --> render
    contrast -- pass --> render

    layout -. configures .-> fence
    icons -. enriches .-> fence

    rColor -. informs .-> palette
    rLayout -. informs .-> layout
    rOrg -. structures .-> fence

    classDef ingressPrimary    fill:#2563eb,stroke:#0f172a,color:#fff,stroke-width:2px
    classDef computePrimary    fill:#7c3aed,stroke:#0f172a,color:#fff,stroke-width:2px
    classDef dataPrimary       fill:#0f766e,stroke:#0f172a,color:#fff,stroke-width:2px
    classDef dataSecondary     fill:#99f6e4,stroke:#0f766e,color:#1e293b,stroke-width:1px
    classDef infraSecondary    fill:#cbd5e1,stroke:#334155,color:#1e293b,stroke-width:1px

    classDef sgBlue   fill:#dbeafe,stroke:#1e40af,color:#1e293b
    classDef sgViolet fill:#ede9fe,stroke:#5b21b6,color:#1e293b
    classDef sgTeal   fill:#ccfbf1,stroke:#0f766e,color:#1e293b
    classDef sgSlate  fill:#f1f5f9,stroke:#334155,color:#334155

    class author sgBlue
    class gates sgViolet
    class optional sgTeal
    class refs sgSlate
```

*Mermaid source flows left-to-right through two mandatory gates, structural
complexity and color contrast, both run by `@jpeakai/mermaidjs-lint`, before
rendering. Reference docs (dotted)
supply the rules each stage enforces.*

## Quick start

```bash
bunx @jpeakai/mermaidjs-lint path/to/doc.md                       # the gates: parse, complexity, contrast
bash .claude/skills/mermaidjs-diagrams/scripts/render_mermaid.sh path/to/doc.md
make -C .claude/skills/mermaidjs-diagrams/scripts install-ts      # once: bun deps for color_contrast.ts
make -C .claude/skills/mermaidjs-diagrams/scripts cli-demo
```

See [`SKILL.md`](SKILL.md) for usage, [`resources/`](resources/) for deep dives,
[render triage](resources/render_troubleshooting.md) when a render fails for
reasons that aren't the diagram, and [`scripts/CLAUDE.md`](scripts/CLAUDE.md)
for the maintenance guide.
