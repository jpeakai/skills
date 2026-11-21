---
type: Architecture Decision
title: Name consumer-facing colour roles with shadcn's vocabulary
description: shadcn names for shared colour roles, named extensions for the rest
tags: [design-system, naming]
status: accepted
accepted_on: 2026-11-03
provenance: Maintainer review of the osaka-shadcn comparison, after a showcase tag used the brand fill as text and the words accent and muted proved to mean different things in shadcn.
enforced_in:
  - skills/design-profiles/scripts/profiles.mjs
  - skills/design-profiles/scripts/shadcn_profile.mjs
  - skills/richdocs/scripts/md2html.py
  - skills/richdocs/scripts/themecheck.py
  - skills/richdocs/assets/
  - skills/mermaidjs-diagrams/resources/themes/osakanights/
generated: { by: human:maintainer, at: 2026-11-03T00:00:00Z }
---

<!-- GENERATED from ADR-0004 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

Design profiles, richdocs and mermaidjs-diagrams used three role vocabularies.
Two words collided with shadcn, which many developers know.
Our accent was shadcn's primary, and our muted was shadcn's muted-foreground.
Design profiles must stay a superset of a shadcn preset.

#### We prefer

shadcn's names wherever shadcn has the role (background, foreground, card, muted, muted-foreground, primary, primary-foreground, border, ring), and named extensions in shadcn's grammar for the roles it lacks (link, faint-foreground, primary-subtle, border-strong, selected), over our own words for the same jobs

#### Because

a word a reader already knows must not carry a different meaning and side effect, and one name per role lets a shadcn preset expand into a profile and back without translation

#### Unless

shadcn renames its theme variables, or a consumer must match a host system whose names conflict with shadcn's

## Consequences

### Pros

- A developer who knows shadcn reads every consumer surface correctly.
- CSS exports each role once, with no prefixed duplicates.
- Saved profiles and brandpacks with old names migrate or fail loudly with a rename table.

### Cons

- The design-profile core tokens keep their Atlassian-style names, so maintainers learn two vocabularies.
- Project-local richdocs themes must rename their keys.
