---
type: Architecture Decision
title: Ship the cloud setup script inside the ccw-setup skill and release it under ccw/ tags
description: Machine setup is downloaded from an immutable tag, and per-session state is applied by a skill
tags: [cloud, release]
status: proposed
accepted_on: 2026-11-15
provenance: Maintainer requirement in issue 40 to add a jpai-ccw plugin carrying the cloud setup script and a ccw-setup skill, for both a developer and an admin cloud environment, invoked by hand rather than by a hook.
enforced_in:
  - skills/ccw-setup/scripts/cloud-setup.sh
  - skills/ccw-setup/scripts/cloud-setup-stub.sh
  - skills/ccw-setup/scripts/ccw_check.py
  - plugins/composition.yaml
generated: { by: human:maintainer, at: 2026-11-15T00:00:00Z }
---

<!-- GENERATED from ADR-0005 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Decision

### The lens

#### Given

A cloud environment's setup script runs once per cached snapshot, cannot read the environment's saved variables, and is pasted by hand into each environment's settings, while a raw branch URL can serve a stale copy for minutes.

#### We prefer

cloud-setup.sh inside the ccw-setup skill, downloaded by a per-environment stub from a ccw/vX.Y.Z tag matching the jpai-ccw version, with every per-session value applied by the skill's check script, over a top-level scripts/ path, a branch download, or a SessionStart hook

#### Because

the setup script versions with the plugin it installs, an immutable tag makes each environment's run reproducible, and a session-side check is the only place saved variables such as an admin external ID can be read

#### Unless

the setup script gains access to saved variables, or plugin hooks are confirmed to fire in cloud sessions and the maintainer wants the check to run unprompted

## Consequences

### Pros

- Developer and admin environments share one script and differ only in their stub's exported values.
- The version check names the exact setup script change a lagging environment needs.

### Cons

- The skill must be invoked each session, because no hook runs it.
- The script's download path is a contract, so moving the skill breaks every pinned stub.
