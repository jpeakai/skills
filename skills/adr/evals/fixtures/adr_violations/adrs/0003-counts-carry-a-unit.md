# ADR-0003: Stock counts carry a unit

| Field | Value |
|---|---|
| **Status** | Accepted, 2026-03-02 |
| **Provenance** | Adding bulk goods sold by the kilogram |
| **Relates to** | supersedes [ADR-0001](0001-counts-are-integers.md) |
| **Enforced in** | the stock model |

## Decision

#### Given

some items are sold by weight or length

#### We prefer

a count paired with its unit, over a bare integer count

#### Because

a unit makes a fractional count exact rather than approximate

#### Unless

never; this one is unconditional

## Consequences

### Pros

- Bulk goods fit the same model as whole units, as ADR-0009 planned.

### Cons

- Every count now carries a second field.
