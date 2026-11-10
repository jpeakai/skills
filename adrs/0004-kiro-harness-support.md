---
type: Architecture Decision
title: Support Kiro through Agent Plugins manifests and kiro-conf hook wiring
description: Kiro installs packs as powers and takes its hook from workspace configuration
tags: [harness]
status: proposed
accepted_on: 2026-11-11
provenance: Maintainer requirement to support Kiro as a harness for skills, plugins and hooks, with a kiro-setup target matching codex-setup.
enforced_in:
  - plugins/jpai-essentials/plugin.json
  - plugins/jpai-delivery/plugin.json
  - scripts/validate_plugins.py
  - hooks/tool_coach.py
  - kiro-conf/
  - Makefile
generated: { by: human:maintainer, at: 2026-11-11T00:00:00Z }
---

<!-- GENERATED from ADR-0004 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

Kiro installs a directory as a power only when an Agent Plugins plugin.json sits at its root, a power carries skills but no hooks, and a Kiro PreToolUse command denies by exiting non-zero rather than by a JSON decision.

#### We prefer

a third manifest at each pack root plus a harness flag on the shared hook, wired from kiro-conf/, over a separate Kiro pack tree or a forked hook script

#### Because

the existing mirror stays the single source of skills, one hook implementation keeps one set of rules, and the validator keeps all three manifests on one name and version

#### Unless

Kiro powers gain hook support, which would move the wiring from kiro-conf/ into the packs

## Consequences

### Pros

- Both packs install with kiro-cli powers install without a new generated tree.
- The coaching rules stay identical across Claude Code, Codex and Kiro.

### Cons

- Kiro users run make kiro-setup separately to get the hook.
- The hook command assumes Kiro runs it from the workspace root.
