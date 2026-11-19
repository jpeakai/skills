---
type: Architecture Decision
title: Tag every plugin version automatically on main, named without the jpai- prefix
description: A workflow creates each missing release tag, so no release waits on a person with tag access
tags: [release]
status: proposed
accepted_on: 2026-11-19
provenance: Maintainer requirement in issue 49 after the ccw/v0.1.0 tag from ADR-0005 went missing, with tags named without the jpai- prefix.
enforced_in:
  - .github/workflows/tag-plugin-versions.yml
  - scripts/tag_plugins.py
  - tests/test_tag_plugins.py
generated: { by: human:maintainer, at: 2026-11-19T00:00:00Z }
---

<!-- GENERATED from ADR-0006 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Relates to

- Extends [ADR-0005](0005-cloud-setup-script-in-skill.md) (Automates the ccw/ release tags ADR-0005 pins.)

## Decision

### The lens

#### Given

Plugin versions change in their manifests, the ccw-setup stub downloads from a ccw/ release tag, and agent sessions cannot push tags.

#### We prefer

a workflow on every push to main that tags each plugin version not yet tagged, named the plugin without its jpai- prefix then /vX.Y.Z, over tagging by hand or one repository-wide version tag

#### Because

a version bump that merges is released without a manual step, each plugin versions on its own, and ccw/ tags keep the name ADR-0005's stub already pins

#### Unless

plugins move to a release tool that owns tagging and changelogs, which would replace this workflow

## Consequences

### Pros

- A merged version bump gets its tag within minutes, with nobody holding tag access.
- An existing tag is never moved, so a pinned stub keeps running the same script.

### Cons

- A version that merges without a bump is never tagged, so the setup script release stays behind.
- The first run tags every current version at that commit, not at the commit each version first appeared.
