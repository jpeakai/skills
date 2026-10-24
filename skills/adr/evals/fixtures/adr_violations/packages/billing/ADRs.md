# Decisions

Decisions scoped to the billing package.

## ADR-1: invoices are immutable once sent

| Field | Value |
|---|---|
| **Status** | Accepted, 2026-02-01 |
| **Relates to** | - |

### Decision

##### Given

a sent invoice has left the system

##### We prefer

issuing a credit note, over editing a sent invoice

##### Because

the customer's copy and ours must always agree

##### Unless

never; this one is unconditional

### Consequences

- Corrections take two documents.
