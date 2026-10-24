# ADR-0001: Stock counts are integers

| Field | Value |
|---|---|
| **Status** | Superseded by ADR-0003, 2026-03-02 |
| **Provenance** | The first stocktake, where a fractional count could not be reconciled |
| **Relates to** | superseded by [ADR-0003](0003-counts-carry-a-unit.md) |
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
