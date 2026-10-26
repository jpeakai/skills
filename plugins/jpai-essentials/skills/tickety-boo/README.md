# tickety-boo

Handle tickets, work in progress and finished-work cleanup using the repository's own `TICKETING.md`.
The repository supplies the system, commands, naming rules and completion policy.
The skill identifies missing conventions rather than inventing them.

## Use it

```text
/tickety-boo create <issue description>
/tickety-boo wip
/tickety-boo cleanup
```

- `create` checks for duplicates before filing.
- `wip` gathers the current user's issues, PRs, branches and worktrees, then considers backlog work when none is active.
- `cleanup` prepares a plan and asks once before closing tickets or removing branches and worktrees.

## Repository-led workflow

```mermaid
flowchart LR
    R["User request"]:::input --> C["Read TICKETING.md"]:::rule
    C --> A["Apply documented workflow"]:::process
    A --> T["Create or match ticket"]:::output
    A --> W["Report current work"]:::output
    A --> P["Plan and confirm cleanup"]:::output
    classDef input fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef process fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef output fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef rule fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
```

Every route uses local conventions and the documented current-user identity.

<details>
<summary>Complete routing and stopping conditions</summary>

```mermaid
flowchart LR
    R["Read root or docs/TICKETING.md"]:::input --> E{"Present and sufficient?"}:::process
    E -->|no| S["Report missing conventions"]:::rule
    E -->|yes| I["Identify current user"]:::process
    I --> C{"Requested command"}:::process
    C -->|create| D["Deduplicate issue"]:::process
    D --> T["Match existing or create ticket"]:::output
    C -->|wip| W["Gather issues, PRs, branches and worktrees"]:::process
    W --> B["Report active work or ready backlog"]:::output
    C -->|cleanup| F["Compare finished work with remote default branch"]:::process
    F --> P["Prepare policy-based cleanup plan"]:::process
    P --> A["Ask once for approval"]:::rule
    A -->|approved| X["Close or remove without force"]:::output
    classDef input fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef process fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef output fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef rule fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
```

</details>

## Requirements and boundaries

- A root `TICKETING.md` or `docs/TICKETING.md` is required.
- Conflicting identity sources stop the workflow until resolved.
- A missing documented step is reported before dependent work proceeds.
- Cleanup uses the remote default branch as evidence and never forces removal.

## Reference

- [Operating instructions](SKILL.md)
- [Ticketing convention checklist](resources/TICKETING-guidelines.md)
