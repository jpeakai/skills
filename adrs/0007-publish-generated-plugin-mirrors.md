---
type: Architecture Decision
title: Publish generated plugin mirrors on main before creating release tags
description: Feature PRs carry canonical sources while publication automation commits validated plugin copies
tags: [release]
status: proposed
accepted_on: 2026-11-20
provenance: Maintainer requirement to keep generated plugin updates outside feature PRs.
enforced_in:
  - .github/workflows/tag-plugin-versions.yml
  - tools/plugin-ci/src/plugin_ci/commands/plugin_mirrors.py
  - tools/plugin-ci/tests/test_plugin_mirrors.py
  - Makefile
generated: { by: human:maintainer, at: 2026-11-20T00:00:00Z }
---

<!-- GENERATED from ADR-0007 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Relates to

- Extends [ADR-0006](0006-auto-tag-plugin-versions.md) (Generates and publishes plugin copies before release tags are created.)

## Decision

### The lens

#### Given

Canonical skills and hooks generate tracked plugin copies, and release tags must identify validated installable content.

#### We prefer

read-only generation and validation in feature PRs, followed by a generated-only bot commit on main before tagging

#### Because

reviewers assess canonical changes once, generated copies remain installable real files, and tags include the validated publication output

#### Unless

publication moves to an artifact registry that removes the need for tracked plugin mirrors

## Consequences

### Pros

- Generated skill and hook copies stay out of feature PRs.
- Publication validates the generated tree and tests its contracts before committing or tagging.
- Version bumps remain explicit and existing release tags remain immutable.

### Cons

- Main temporarily contains stale mirrors between a source merge and successful publication.
- Repository rules must allow the workflow token to push generated commits to main.
- A concurrent main update rejects the publication push and requires a fresh workflow run.
