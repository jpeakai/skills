---
type: Architecture Decision
title: Keep agent instructions canonical in AGENTS.md
description: One instruction source shared by agent harnesses
tags: [documentation]
status: accepted
accepted_on: 2026-10-26
provenance: Explicit maintainer requirements for repository agent files, skill overviews and documentation conventions.
enforced_in:
  - AGENTS.md
  - CLAUDE.md
  - skills/*/AGENTS.md
  - skills/*/CLAUDE.md
generated: { by: human:maintainer, at: 2026-10-26T00:00:00Z }
---

<!-- GENERATED from ADR-0001 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

Maintainers use multiple agent harnesses and existing skill-local instructions must remain available.

#### We prefer

canonical AGENTS.md files with CLAUDE.md import siblings over separate harness-specific instruction bodies

#### Because

one maintained instruction body avoids harness drift while retaining existing scoped guidance

#### Unless

a vendored snapshot has an upstream-owned file layout; refresh that snapshot through its documented procedure

## Consequences

### Pros

- Agent harnesses share the same authored instructions.
- Existing skill decision arguments retain their wording.

### Cons

- Each canonical instruction file needs a small import sibling.
