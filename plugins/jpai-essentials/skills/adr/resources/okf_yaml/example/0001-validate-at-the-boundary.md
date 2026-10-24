---
type: Architecture Decision
title: Validate external payloads at the boundary, not at the point of use
description: Data crossing a trust boundary is validated once, where it enters
tags: [correctness, boundaries]
status: accepted
accepted_on: 2026-08-28
provenance: Two incidents traced to a response field that changed shape upstream and was read as valid at three call sites
enforced_in:
  - the request handler layer
  - the queue consumer
  - the config loader
generated: { by: human:maintainer, at: 2026-08-28T00:00:00Z }
---

<!-- GENERATED from REC-0001 by okf_render.py. Do not edit; edit the .yml and regenerate. -->

## Relates to

- Depended on by [REC-0002](0002-one-error-taxonomy.md) (the error taxonomy assumes payloads are already shaped)

## Decision

### The lens

#### Given

every value crossing a trust boundary is unknown until something checks it

#### We prefer

parsing each payload into a typed value at the boundary it enters, over defensive checks at each point of use

#### Because

one check produces one error naming the real source, while scattered checks disagree about what valid means

#### Unless

the boundary is provably internal and the producer is in the same deployable

## Consequences

### Pros

- A malformed payload fails once, at the edge, naming the offending field.
- Downstream code can treat its inputs as typed without re-checking.

### Cons

- Schemas must be maintained alongside the types they mirror, and the two can drift.
