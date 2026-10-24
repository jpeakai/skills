# ADR-0005: Counts are taken nightly

| Field | Value |
|---|---|
| **Status** | Accepted, 2026-04-20 |
| **Provenance** | Daytime counts that raced the picking floor |
| **Relates to** | - |
| **Enforced in** | the count scheduler |

## Decision

#### Given

picking runs from open to close

#### We prefer

counting after close, over counting during trading hours

#### Because

a count taken while stock moves is out of date before it finishes

#### Unless

a site trades around the clock

## Consequences

### Pros

- A count describes one moment.

### Cons

- Discrepancies surface a day late.
