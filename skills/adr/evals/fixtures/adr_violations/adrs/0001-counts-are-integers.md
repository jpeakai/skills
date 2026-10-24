# ADR-0001: Stock counts are integers

| Field | Value |
|---|---|
| **Status** | Accepted, 2026-01-15 |
| **Provenance** | The first stocktake, where a fractional count could not be reconciled |
| **Relates to** | - |
| **Enforced in** | the stock model |

## Decision

#### Given

every item the service tracked was counted in whole units

#### We prefer

storing counts as integers, over storing them as decimals

#### Because

an integer count cannot drift under repeated arithmetic

#### Unless

an item is sold by weight or length

## Consequences

### Pros

- Counts reconcile exactly.

### Cons

- Items sold by weight do not fit.
