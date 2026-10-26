---
type: Architecture Decision
title: Give every canonical skill a dual-density human overview
description: Human entry points separate from runtime skill instructions
tags: [documentation]
status: accepted
accepted_on: 2026-10-26
provenance: Explicit maintainer requirements for repository agent files, skill overviews and documentation conventions.
enforced_in:
  - skills/*/README.md
  - Makefile
generated: { by: human:maintainer, at: 2026-10-26T00:00:00Z }
---

<!-- GENERATED from ADR-0002 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

Each skill needs a human overview without forcing readers through its runtime operating manual.

#### We prefer

a concise README with a visible workflow overview and collapsed detailed Mermaid diagram over a single dense diagram

#### Because

readers can choose the amount of workflow detail while agents retain a separate runtime contract

#### Unless

the maintainer explicitly replaces the README or diagram contract for a skill

## Consequences

### Pros

- Every skill has a predictable human entry point.
- Diagram gates check parsing, complexity and contrast.

### Cons

- Workflow changes require keeping both diagram densities current.
