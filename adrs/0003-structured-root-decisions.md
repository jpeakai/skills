---
type: Architecture Decision
title: Declare standard documentation and render root decisions from YAML
description: Standard documentation dialect with a generated root decision bundle
tags: [documentation]
status: accepted
accepted_on: 2026-10-26
provenance: Explicit maintainer requirements for repository agent files, skill overviews and documentation conventions.
enforced_in:
  - docs/CONVENTIONS.md
  - adrs/record.schema.json
  - adrs/templates/
  - Makefile
generated: { by: human:maintainer, at: 2026-10-26T00:00:00Z }
---

<!-- GENERATED from ADR-0003 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

Repository guidance needs a declared layout and a root decision surface while existing skill logs remain scoped.

#### We prefer

standard documentation conventions and an okf-yaml bundle in adrs/ over an undeclared layout and hand-maintained decision views

#### Because

schema validation and generated views keep root records, their index and their relation graph consistent

#### Unless

the maintainer requests another layout and an explicit migration preserves accepted decision arguments

## Consequences

### Pros

- Root decisions are schema-validated and rendered consistently.
- The root index routes readers to existing scoped decisions.

### Cons

- The root bundle carries a renderer and templates that require maintenance.
