---
type: Architecture Decision
title: Organise repository automation as self-contained CLI Tool subprojects
description: Focused Tools own their environments, commands, tests and maintenance instructions
tags: [tooling]
status: proposed
accepted_on: 2026-11-20
provenance: Maintainer requirement for independently curated plugin-ci and harness-ci Tool subprojects.
enforced_in:
  - tools/AGENTS.md
  - tools/plugin-ci/pyproject.toml
  - tools/harness-ci/pyproject.toml
  - Makefile
generated: { by: human:maintainer, at: 2026-11-20T00:00:00Z }
---

<!-- GENERATED from ADR-0008 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

Repository automation covers distinct publication and harness responsibilities with different dependencies and execution risks.

#### We prefer

focused CLI Tool subprojects under tools/ with independent manifests and lockfiles over a loose root scripts directory

#### Because

each responsibility has explicit commands, curated dependencies, local quality gates and clear maintenance ownership

#### Unless

multiple Tools need a shared runtime package whose ownership and dependency contract are recorded separately

## Consequences

### Pros

- Every Tool owns a README, agent instructions, tests and an independently runnable CLI.
- Root orchestration delegates to Tool commands while skill-local helpers remain self-contained.
- Tool gates enforce formatting, lint, strict typing, cognitive complexity and coverage.

### Cons

- Each Tool maintains its own dependency lockfile and quality configuration.
