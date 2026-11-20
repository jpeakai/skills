---
type: Architecture Decision
title: Resolve skill locations through a harness-independent SKILLS_ROOT placeholder
description: Agent skill instructions resolve their installation path without assuming a harness directory
tags: [skills, portability]
status: accepted
accepted_on: 2026-11-20
provenance: Maintainer requirement that agent skills work across Claude, Codex and Kiro.
enforced_in:
  - skills/richdocs/SKILL.md
  - skills/richdocs/README.md
  - skills/richdocs/AGENTS.md
generated: { by: human:maintainer, at: 2026-11-20T00:00:00Z }
---

<!-- GENERATED from ADR-0009 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

Claude, Codex and Kiro can install the same skill in different locations, including plugin caches and directories outside the target repository.

#### We prefer

{SKILLS_ROOT} in agent skill instructions, resolved from the active harness supplied skill location or the installed SKILL.md path, over literal .claude/, .codex/, .kiro/ or .agents/ directory assumptions

#### Because

commands can locate the installed skill consistently while retaining the target repository as their working directory

#### Unless

a shared cross-harness installation contract supplies another portable resource-location mechanism

## Consequences

### Pros

- SKILLS_ROOT denotes the absolute parent directory of the installed skill directory.
- Agents verify the skill path, substitute the placeholder before execution and quote paths containing spaces.
- Runtime instructions and maintained examples share one portable path convention.
- Richdocs adopts the convention immediately and the remaining skills are tracked separately.

### Cons

- Agents must resolve the installation location before executing commands.
- Accepted historical decision arguments and upstream-owned vendor snapshots retain their original text until supersession or an upstream refresh.
