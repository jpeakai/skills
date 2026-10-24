# ADR-0002: One warehouse per ledger

| Field | Value |
|---|---|
| **Status** | Accepted, 2026-02-10 |
| **Provenance** | A transfer between two warehouses that was counted twice |
| **Relates to** | - |
| **Enforced in** | the ledger service |

## Decision

#### Given

a transfer touches two warehouses at once

#### We prefer

one ledger per warehouse, over one shared ledger for every site

#### Because

a mismatch is then attributable to exactly one site

#### Unless

never; this one is unconditional

## Consequences

### Pros

- Every discrepancy names its warehouse.

### Cons

- A transfer writes to two ledgers.
