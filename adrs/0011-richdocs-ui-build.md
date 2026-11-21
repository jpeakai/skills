---
type: Architecture Decision
title: Build the richdocs pages with a dev-time Vite and shadcn project outside the skill
description: A dev-time UI Build produces the richdocs viewer and showcase as generated assets
tags: [richdocs, ui]
status: proposed
accepted_on: 2026-11-19
provenance: Maintainer requirement for a mini Vite project using shadcn to rebuild the richdocs showcase and base template, kept external to the skill, with bespoke components curated in the jpeakai/ui registry.
enforced_in:
  - web/richdocs-ui/
  - skills/richdocs/assets/viewer.html
  - skills/richdocs/scripts/md2html.py
  - Makefile
generated: { by: human:maintainer, at: 2026-11-19T00:00:00Z }
---

<!-- GENERATED from ADR-0011 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

The richdocs viewer and showcase are hand-written vanilla files assembled by stdlib Python, and the maintainer wants them rebuilt from shadcn components while installed skills stay stdlib-only.

#### We prefer

a Vite, React, Tailwind and shadcn project under web/richdocs-ui/ whose built IIFE bundles ship as generated files in skills/richdocs/assets/ over hand-written assets or a build step inside the skill

#### Because

shadcn components need a bundler, the plugin mirror never copies web/, and the Python generators keep inlining plain text so installed skills gain no toolchain

#### Unless

the skill must rebuild its own assets on an end user's machine, which would move the build inside the skill

## Consequences

### Pros

- The pages are composed from shadcn primitives and registry components, themed by injected variables.
- Installed skills keep their stdlib-only runtime and pinned CDN libraries.

### Cons

- Contributors changing the pages need bun and a rebuild, and committed output can go stale.
- React and the shadcn primitives add about 80 kB gzipped to every page.
