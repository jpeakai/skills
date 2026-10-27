# agnostic

Makes documentation reusable by replacing project, client and company details with generic names and examples.
Use it when writing public documentation, removing branding or checking for leaked names.

## Quickstart

```text
/agnostic
```

Apply it to documentation that should be generic.
Source code, tests and product documentation intended to name the real project stay outside its scope.

## Workflow

```mermaid
flowchart LR
    D["Documentation"]:::source --> G["Generalise names<br/>and examples"]:::process
    G --> R["Reusable documentation"]:::output

    classDef source fill:#1e40af,stroke:#93c5fd,color:#ffffff,stroke-width:2px
    classDef process fill:#6d28d9,stroke:#c4b5fd,color:#ffffff,stroke-width:2px
    classDef output fill:#047857,stroke:#6ee7b7,color:#ffffff,stroke-width:2px
```

Replace identifying details while preserving the explanation.

<details>
<summary>Complete workflow: scope, identifying details and generic replacements</summary>

```mermaid
flowchart TD
    D["Documentation task"]:::source --> S{"Should this content<br/>be generic?"}:::process
    S -->|Yes| I["Identify project and<br/>organisation names"]:::process
    S -->|No| K["Keep intended<br/>project references"]:::output
    I --> P["Identify specific paths,<br/>entities and palettes"]:::process
    P --> G["Use generic names,<br/>paths and examples"]:::process
    G --> R["Documentation with<br/>its meaning preserved"]:::output

    classDef source fill:#1e40af,stroke:#93c5fd,color:#ffffff,stroke-width:2px
    classDef process fill:#6d28d9,stroke:#c4b5fd,color:#ffffff,stroke-width:2px
    classDef output fill:#047857,stroke:#6ee7b7,color:#ffffff,stroke-width:2px
```

The intended audience determines whether real names belong in the document.

</details>

## Reference

The complete operating instructions live in [SKILL.md](SKILL.md).
