# Glossary

The ubiquitous language for `ledgerly`.
Each term is written in Title Case wherever it is used, to mark it as this glossary's meaning rather than the plain-language one.
When a new domain term enters the code or the conversation, add it here in the same change.
Give it its own H2 and a place in the diagram.

```mermaid
flowchart LR
    LED["Ledger"]:::record
    STM["Statement"]:::info
    REC["Reconciliation"]:::pipeline

    REC -- matches --> STM
    REC -- updates --> LED

    classDef info     fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
    classDef pipeline fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef record   fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
```

## Ledger

The internal record of every expected money movement.

## Reconciliation

Matching each Statement line to one Ledger entry.

## Statement

A bank's export of account movements for one period.
