# jpai-delivery

Review feedback, decisions and ticketing in one plugin.
This plugin ships three skills and no hook.

## Overview

```mermaid
flowchart LR
    P["jpai-delivery"]:::plugin
    P --> R["Review feedback"]:::review
    P --> D["Decisions"]:::decision
    P --> T["Ticketing"]:::ticket
    classDef plugin fill:#334155,stroke:#cbd5e1,color:#ffffff,stroke-width:2px
    classDef review fill:#1e40af,stroke:#93c5fd,color:#ffffff,stroke-width:2px
    classDef decision fill:#6d28d9,stroke:#c4b5fd,color:#ffffff,stroke-width:2px
    classDef ticket fill:#047857,stroke:#6ee7b7,color:#ffffff,stroke-width:2px
```

Choose a skill for the current task; review feedback, decisions and ticketing can be handled independently.

<details>
<summary>Skills and their results</summary>

```mermaid
flowchart LR
    P["jpai-delivery"]:::plugin
    P --> R["snr-pr"]:::review
    R --> F["Filter existing feedback<br/>Fix Signal and improve safeguards"]:::review
    P --> D["concise-decisions"]:::decision
    D --> A["Check existing decisions<br/>Ask one informed question"]:::decision
    P --> T["tickety-boo"]:::ticket
    C["Repository TICKETING.md"]:::plugin --> T
    T --> W["Create tickets<br/>Report work and clean up"]:::ticket
    classDef plugin fill:#334155,stroke:#cbd5e1,color:#ffffff,stroke-width:2px
    classDef review fill:#1e40af,stroke:#93c5fd,color:#ffffff,stroke-width:2px
    classDef decision fill:#6d28d9,stroke:#c4b5fd,color:#ffffff,stroke-width:2px
    classDef ticket fill:#047857,stroke:#6ee7b7,color:#ffffff,stroke-width:2px
```

Each skill follows its own contract; ticketing conventions come from the repository being worked on.

</details>

## Included skills

| Skill | Purpose |
|---|---|
| [snr-pr](skills/snr-pr/README.md) | Filter existing review feedback into Signal and Noise, then improve fixes and review filters. |
| [concise-decisions](skills/concise-decisions/README.md) | Check existing decisions and resolve related ambiguities with one informed question. |
| [tickety-boo](skills/tickety-boo/README.md) | Follow repository conventions for tickets, work in progress and cleanup. |

All three skills are also included in [jpai-essentials](../jpai-essentials/README.md).

## Use and maintenance

Follow the [installation guide](../../README.md#installing) for your agent.
See [plugin maintenance](../README.md#editing) for composition, manifests and generated skill copies.
